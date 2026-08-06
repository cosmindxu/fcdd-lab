#!/usr/bin/env python3
"""Predictability / quality analysis for the two-goal reframe (2026-08-06).

Companion to tools/analyse.py (which owns the cost headline). This script
re-derives every number the paper quotes for Goal 1 (predictability and
unfounded-change reduction), so no figure in the manuscript rests on prose:

  1. bug01 replication: per-run costs summed across attempts from the raw
     result JSONs (v4 instrument only, per amendment A10 v3/v4 cost
     non-comparability), solution mode per run taken from the ledger's
     acceptance rows (pristine binary = minimal fix, differs = redesign);
  2. within-defect dispersion (the only replicated cell) and its honest
     statistics: spread, CV, Fisher exact on strategy-by-arm, and the
     attainable-significance floor for 3-vs-3 designs;
  3. across-defect dispersion with and without bug01;
  4. the counterbalanced quality round, recomputed from the deposited
     VERDICT_*/KEY_* files: axis means, per-pair preference, order
     consistency, position split, and the paired composite CI;
  5. the review-effort ANCOVA of paper section 4.3, re-derived. NOTE: this
     CORRECTS the regression published in draft v4 of the article
     (4.13 + 21.35*ArmB + 7.13*rev, R^2 0.826, attenuation 30.34->21.35),
     which does not reproduce from the deposited table. The corrected fit
     is printed below; the direction of the conclusion is unchanged and in
     fact strengthened (reviewers-alone R^2 exceeds arm-alone R^2).

Usage: python3 tools/analyse_predictability.py
"""
import csv
import glob
import json
import os
import re
import statistics as st
from math import comb

CASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(CASE, "ledger", "raw")
LEDGER = os.path.join(CASE, "ledger", "runs.csv")
GRADING = os.path.join(CASE, "grading")


# ---------------------------------------------------------------- bug01 runs
def bug01_runs():
    """{(arm, tag): platform USD summed across attempts} for v4 runs."""
    out = {}
    for p in sorted(glob.glob(os.path.join(RAW, "arm?_bug01_v4*_result.json"))):
        m = re.search(r"arm([AB])_bug01_(v4(?:r\d)?)_a\d_result\.json", p)
        if not m:
            continue
        arm, tag = m.groups()
        out.setdefault((arm, tag), 0.0)
        out[(arm, tag)] += json.load(open(p)).get("total_cost_usd") or 0.0
    return out


def bug01_modes():
    """{(arm, tag): 'minimal'|'redesign'} from the ledger acceptance rows.

    pristine binary => minimal one-byte fix; 'binary DIFFERS' => redesign.
    Source rows: acceptance_bug01{A,B}_v4*, notes column.
    """
    modes = {}
    for row in csv.DictReader(open(LEDGER)):
        rid = row["run_id"]
        m = re.match(r"(?:acceptance_bug01|arm)([AB])(?:_bug01)?_(v4(?:r\d)?)$",
                     rid)
        if not m:
            continue
        arm, tag = m.groups()
        # classify on the FIRST binary-status phrase only: later sentences in
        # some notes recap the OTHER arm's history and would misclassify.
        # one ledger row (armA_bug01_v4r2) carries unquoted commas in notes,
        # which DictReader spills into the overflow key: rejoin before matching
        note = row["notes"] + " " + " ".join(row.get(None) or [])
        hit = re.search(r"binary\s+(PRISTINE|DIFFERS)|(PRISTINE|DIFFERS)\s+binary",
                        note, re.I)
        if not hit:
            continue
        word = (hit.group(1) or hit.group(2)).upper()
        modes[(arm, tag)] = "minimal" if word == "PRISTINE" else "redesign"
    # bug01/A v4 (the original cell): its acceptance row does not restate the
    # binary status; the v4r3 row records the four-run A history explicitly
    # ("minimal 8.66/11.78 pristine vs redesign 44.27/41.35 differs").
    modes.setdefault(("A", "v4"), "redesign")
    return modes


def fisher_two_sided(a, b, c, d):
    """Exact two-sided Fisher for [[a,b],[c,d]] (sum of tables <= P(obs))."""
    r1, r2, c1 = a + b, c + d, a + c
    n = r1 + r2

    def p(x):
        return comb(r1, x) * comb(r2, c1 - x) / comb(n, c1)

    po = p(a)
    return sum(p(x) for x in range(max(0, c1 - r2), min(r1, c1) + 1)
               if p(x) <= po + 1e-12)


# -------------------------------------------------------------------- report
runs = bug01_runs()
modes = bug01_modes()
print("== bug01 replication (v4 instrument; attempts summed per run) ==")
for (arm, tag), usd in sorted(runs.items()):
    print("  arm%s %-5s $%7.2f  %s" % (arm, tag, usd, modes.get((arm, tag), "?")))
A = [usd for (a, t), usd in sorted(runs.items()) if a == "A"]
B = [usd for (a, t), usd in sorted(runs.items()) if a == "B"]
for name, v in (("A", A), ("B", B)):
    print("  arm%s n=%d spread %.2fx  sample CV %.2f" %
          (name, len(v), max(v) / min(v), st.stdev(v) / st.mean(v)))
am = [modes[(("A"), t)] for (a, t) in sorted(runs) if a == "A"]
bm = [modes[(("B"), t)] for (a, t) in sorted(runs) if a == "B"]
a_min, a_red = am.count("minimal"), am.count("redesign")
b_min, b_red = bm.count("minimal"), bm.count("redesign")
p_v4 = fisher_two_sided(a_min, a_red, b_min, b_red)
print("  strategy table v4: A %d minimal / %d redesign; B %d / %d"
      % (a_min, a_red, b_min, b_red))
print("  Fisher exact two-sided p = %.3f  (incl. the v3 strategy row "
      "2/2 vs 3/0: p = %.3f)" % (p_v4, fisher_two_sided(2, 2, 3, 0)))
print("  attainable-significance floor, any 3-vs-3 permutation test: "
      "min two-sided p = %.2f" % (2 / comb(6, 3)))
print("  => no dispersion statistic at this k can reach 0.05; the "
      "contrast is a directional observation, not a tested claim")

# solution-matched ratios (both arms produced the byte-identical minimal fix)
a_minimal = [usd for (a, t), usd in runs.items()
             if a == "A" and modes.get((a, t)) == "minimal"]
if len(a_minimal) == 1:
    print("  solution-matched ratios (each B run / the one A minimal run "
          "$%.2f): %s" % (a_minimal[0],
                          ", ".join("%.2fx" % (x / a_minimal[0]) for x in sorted(B))))
    print("  (quoted individually: a denominator of one is not an estimator)")

# ------------------------------------------------- across-defect dispersion
print("\n== across-defect dispersion (7 v4 cells; platform USD, bug03/B "
      "imputed per analyse.py) ==")
AV = [44.27, 7.32, 11.96, 11.30, 8.88, 16.44, 7.11]
BV = [49.63, 50.37, 23.98, 55.40, 31.05, 48.69, 24.19]
for nm, v in (("A", AV), ("B", BV)):
    w = v[1:]  # drop bug01
    print("  arm%s all: spread %.2fx CV %.2f | excl bug01: spread %.2fx CV %.2f"
          % (nm, max(v) / min(v), st.stdev(v) / st.mean(v),
             max(w) / min(w), st.stdev(w) / st.mean(w)))

# --------------------------------------------- counterbalanced quality round
print("\n== counterbalanced quality round (14 verdicts, 7 pairs x 2 orders) ==")
axes = ("correctness_risk", "clarity", "test_quality")
scores = {a: {ax: [] for ax in axes} for a in "AB"}
scores_ex = {a: {ax: [] for ax in axes} for a in "AB"}
prefs, pos, comp = {}, [], {}
for vf in sorted(glob.glob(os.path.join(GRADING, "VERDICT_bug0?_X?.json"))):
    d = json.load(open(vf))
    k = json.load(open(vf.replace("VERDICT", "KEY")))
    for lab in "XY":
        arm = k[lab]
        for ax in axes:
            scores[arm][ax].append(d[lab][ax])
            if d["bug"] != "bug01":
                scores_ex[arm][ax].append(d[lab][ax])
        comp.setdefault((d["bug"], arm), []).extend(d[lab][ax] for ax in axes)
    w = d["which_is_better_overall"]
    prefs.setdefault(d["bug"], []).append(k[w])
    pos.append("first" if w == "X" else "second")
for arm in "AB":
    print("  arm%s all7  %s  composite %.2f" %
          (arm, "  ".join("%s %.2f" % (ax, st.mean(v))
                          for ax, v in scores[arm].items()),
           st.mean([st.mean(v) for v in scores[arm].values()])))
    print("  arm%s ex01  %s  composite %.2f" %
          (arm, "  ".join("%s %.2f" % (ax, st.mean(v))
                          for ax, v in scores_ex[arm].items()),
           st.mean([st.mean(v) for v in scores_ex[arm].values()])))
consistent = sum(1 for p in prefs.values() if len(set(p)) == 1)
fav_b = sum(1 for p in prefs.values() if set(p) == {"B"})
print("  order-consistent pairs: %d/7; FCDD favoured on %d/7; position "
      "preference %d first / %d second"
      % (consistent, fav_b, pos.count("first"), pos.count("second")))
bugs = sorted({b for b, _ in comp})
diffs = [st.mean(comp[(b, "B")]) - st.mean(comp[(b, "A")]) for b in bugs]
m, sd, n = st.mean(diffs), st.stdev(diffs), len(diffs)
half = 2.447 * sd / n ** 0.5  # t(6), 95%
print("  paired composite diff (B-A) per pair: %s"
      % ", ".join("%+.2f" % x for x in diffs))
print("  mean %+.3f, 95%% CI [%+.2f, %+.2f] -> spans zero; no quality claim"
      % (m, m - half, m + half))

# ------------------------------------------------- estimator sensitivity
print("\n== estimator sensitivity for the cost ratio (platform USD, "
      "corrected imputation) ==")
ratios = [b / a for a, b in zip(AV, BV)]
print("  median-of-ratios %.2fx | ratio-of-medians %.2fx (medians %.2f/%.2f)"
      " | ratio-of-totals %.2fx"
      % (st.median(ratios), st.median(BV) / st.median(AV),
         st.median(BV), st.median(AV), sum(BV) / sum(AV)))
print("  NOTE: draft v4 published 3.40 / 3.50 / 2.83. The 3.50 does not "
      "reproduce under any reconstruction we found; the 2.83 matches the "
      "SUPERSEDED $45.76 imputation for bug03/B. Corrected values above.")

# -------------------------------------------- contract-extension mechanism
print("\n== contract extension vs cost (Arm B v4 cells; theorem counts "
      "re-derived 2026-08-06 by `grep -cE '^theorem ' Contract.lean` in each "
      "workspace vs the 95-theorem baseline) ==")
EXT = {"bug01": 29, "bug02": 16, "bug03": 35, "bug04": 33, "bug05": 18,
       "bug06": 29, "bug07": 12}
BCOST = {"bug01": 49.63, "bug02": 50.37, "bug03": 23.98, "bug04": 55.40,
         "bug05": 31.05, "bug06": 48.69, "bug07": 24.19}
bugs7 = sorted(EXT)


def rank(vals):
    s = sorted(vals)
    return [sum(i + 1 for i, x in enumerate(s) if x == v) / s.count(v)
            for v in vals]


re_, rc_ = rank([EXT[b] for b in bugs7]), rank([BCOST[b] for b in bugs7])
d2 = sum((a - b) ** 2 for a, b in zip(re_, rc_))
n7 = len(bugs7)
print("  every cell extended the contract: %s" %
      ", ".join("%s +%d" % (b, EXT[b]) for b in bugs7))
print("  Spearman rho (theorems added vs cell cost) = %.3f -> raw extension "
      "count does NOT predict cost" % (1 - 6 * d2 / (n7 * (n7 * n7 - 1))))
se = ["bug01", "bug04", "bug06"]   # search/eval-layer faults, outside C1-C14
rl = ["bug02", "bug03", "bug05", "bug07"]
print("  fault layer: search/eval median $%.2f (n=3) vs rule-layer $%.2f "
      "(n=4) -> a mechanism, not a tested effect"
      % (st.median([BCOST[b] for b in se]), st.median([BCOST[b] for b in rl])))
print("  NOTE: draft v4's grouping ('four cells needing new properties "
      "$49.16 vs $24.19') could not be re-derived from the deposited "
      "artefacts and is replaced by the two statements above.")

# --------------------------------------------------- review-effort ANCOVA
print("\n== review-effort ANCOVA, corrected (13 v4 cells with a deposited "
      "platform cost; reviewer counts = deposited table) ==")
cells = [("A", 44.27, 3), ("A", 7.32, 2), ("A", 11.96, 1), ("A", 11.30, 1),
         ("A", 8.88, 1), ("A", 16.44, 2), ("A", 7.11, 1),
         ("B", 49.63, 3), ("B", 50.37, 4), ("B", 55.40, 5), ("B", 31.05, 1),
         ("B", 48.69, 3), ("B", 24.19, 1)]


def ols(rows, cols):
    """Tiny OLS via normal equations (cols = list of feature functions)."""
    X = [[f(r) for f in cols] for r in rows]
    y = [r[1] for r in rows]
    k = len(cols)
    # normal equations X'X b = X'y, solved by Gaussian elimination
    xtx = [[sum(X[i][p] * X[i][q] for i in range(len(rows))) for q in range(k)]
           for p in range(k)]
    xty = [sum(X[i][p] * y[i] for i in range(len(rows))) for p in range(k)]
    for p in range(k):
        piv = xtx[p][p]
        for q in range(p, k):
            xtx[p][q] /= piv
        xty[p] /= piv
        for r2 in range(k):
            if r2 != p and xtx[r2][p]:
                f = xtx[r2][p]
                for q in range(p, k):
                    xtx[r2][q] -= f * xtx[p][q]
                xty[r2] -= f * xty[p]
    b = xty
    yhat = [sum(bb * X[i][j] for j, bb in enumerate(b)) for i in range(len(rows))]
    ybar = sum(y) / len(y)
    r2v = 1 - sum((yi - yh) ** 2 for yi, yh in zip(y, yhat)) / \
        sum((yi - ybar) ** 2 for yi in y)
    return b, r2v


one = lambda r: 1.0
armB = lambda r: 1.0 if r[0] == "B" else 0.0
rev = lambda r: float(r[2])
b3, r2_full = ols(cells, [one, armB, rev])
b2a, r2_arm = ols(cells, [one, armB])
b2r, r2_rev = ols(cells, [one, rev])
print("  cost = %.2f + %.2f*ArmB + %.2f*reviewers   R^2 = %.3f"
      % (b3[0], b3[1], b3[2], r2_full))
print("  arm alone: gap $%.2f, R^2 = %.3f | reviewers alone: R^2 = %.3f"
      % (b2a[1], r2_arm, r2_rev))
print("  attenuation: $%.2f -> $%.2f (%.0f%% of the raw arm gap moves to "
      "reviewer count)" % (b2a[1], b3[1], 100 * (1 - b3[1] / b2a[1])))
mean_a = st.mean([r[2] for r in cells if r[0] == "A"])
mean_b = st.mean([r[2] for r in cells if r[0] == "B"])
print("  mean reviewer invocations: A %.2f, B %.2f (%.1fx)"
      % (mean_a, mean_b, mean_b / mean_a))
