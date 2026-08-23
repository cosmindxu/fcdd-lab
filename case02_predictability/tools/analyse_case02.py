#!/usr/bin/env python3
"""Case02 primary analysis — FROZEN before the first run (see PREREGISTRATION.md §4).

Primary: two-sided EXACT permutation test, paired across defects, on the
per-defect difference in CV of log cost. 2^7 = 128 assignments, enumerated.
No estimator choice is left open at analysis time; that freedom is what this
file exists to remove.
"""
import glob, json, os, statistics as st
from itertools import product

CASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# The runner is case01's run_resilient.sh, which HARDCODES its output directory,
# so every case02 result file is written to case01's ledger — not this case's.
# As frozen, RAW pointed at a directory that does not exist and the script found
# zero runs. Defect + fix recorded as AMENDMENTS A8.
RAW = os.path.join(os.path.dirname(CASE), "case01_spectrum_gambit", "ledger", "raw")
BUGS = ["bug%02d" % i for i in range(1, 8)]
KEYS = ("inputTokens", "cacheCreationInputTokens", "cacheReadInputTokens", "outputTokens")

def cell_costs(bug, arm):
    """USD per run for one (defect, arm) cell, from modelUsage (incl. subagents)."""
    out = []
    for p in sorted(glob.glob(os.path.join(RAW, "arm%s_%s_c2r*_result.json" % (arm, bug)))):
        try: d = json.load(open(p))
        except Exception: continue
        # PREREGISTRATION §6: a run killed by infrastructure has its partial cost
        # "recorded and excluded". run_resilient writes one result file PER ATTEMPT,
        # so without this test the interrupted first attempt of bug05/armB/r1 enters
        # that cell as a fifth observation. Defect + fix recorded as AMENDMENTS A7.
        if d.get("is_error"): continue
        c = d.get("total_cost_usd")
        if c: out.append(float(c))
    return out

def cv_log(costs):
    if len(costs) < 2: return None
    ln = [__import__("math").log(c) for c in costs]
    m = st.mean(ln)
    return st.stdev(ln) / abs(m) if m else None

def exact_paired_permutation(diffs):
    """Two-sided exact p: enumerate all 2^n sign flips of the paired differences."""
    n = len(diffs); obs = st.mean(diffs)
    hits = sum(1 for signs in product([1, -1], repeat=n)
               if abs(st.mean([s * d for s, d in zip(signs, diffs)])) >= abs(obs) - 1e-12)
    return hits / 2 ** n

if __name__ == "__main__":
    rows, diffs = [], []
    for b in BUGS:
        a, bb = cell_costs(b, "A"), cell_costs(b, "B")
        ca, cb = cv_log(a), cv_log(bb)
        rows.append((b, len(a), len(bb), ca, cb))
        if ca is not None and cb is not None: diffs.append(ca - cb)
    print("%-7s %3s %3s %9s %9s" % ("defect", "nA", "nB", "CV_log A", "CV_log B"))
    for b, na, nb, ca, cb in rows:
        print("%-7s %3d %3d %9s %9s" % (b, na, nb,
              "%.4f" % ca if ca is not None else "-", "%.4f" % cb if cb is not None else "-"))
    if len(diffs) < 2:
        print("\nnot enough complete defects yet (need >=2, have %d)" % len(diffs)); raise SystemExit
    p = exact_paired_permutation(diffs)
    print("\npaired defects: %d   mean CV difference (A-B): %+.4f" % (len(diffs), st.mean(diffs)))
    print("exact two-sided permutation p = %.4f   (floor at n=%d is %.4f)"
          % (p, len(diffs), 2 / 2 ** len(diffs)))
    print("verdict:", "H1 SUPPORTED" if p < 0.05 and st.mean(diffs) > 0
          else "H1 NOT SUPPORTED at alpha=0.05")
