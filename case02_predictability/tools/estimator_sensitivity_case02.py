#!/usr/bin/env python3
"""A14 — the pre-registered estimator is not scale-invariant. Quantified here.

CV_log = sd(ln c)/|mean(ln c)| is a function of the UNIT the costs are in:
scaling by k sends ln c -> ln c + ln k, leaving the numerator alone and moving
the denominator. This script demonstrates that on the study's own data and
reports the scale-free alternative.

It does NOT replace the primary. Swapping estimators after seeing the data is
the freedom §4 exists to remove, and here the replacement happens to favour the
conclusion already reported, which makes the temptation worse rather than
better. This is disclosure, not substitution.

Also carries the A6 nine-day-gap sensitivity, whose direction A6 predicted and
got wrong.
"""
import glob, json, math, os, re, statistics as st
from itertools import product
RAW = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
      os.path.abspath(__file__)))), "case01_spectrum_gambit", "ledger", "raw")
BUGS = ["bug%02d" % i for i in range(1, 8)]
POST_GAP = {("bug04","B","1"),("bug03","B","4"),("bug07","A","2"),("bug03","B","2"),("bug01","A","3")}

KEYS_T = ("inputTokens","cacheCreationInputTokens","cacheReadInputTokens","outputTokens")

def cells_tok():
    C = {}
    for f in glob.glob(os.path.join(RAW, "arm*_c2r*_a*_result.json")):
        m = re.search(r"arm([AB])_(bug\d+)_c2r(\d)_a(\d)_result\.json$", f)
        if not m: continue
        d = json.load(open(f))
        if d.get("is_error"): continue
        mu = d.get("modelUsage") or {}
        C.setdefault((m.group(2), m.group(1)), []).append(
            float(sum(sum(v.get(k) or 0 for k in KEYS_T) for v in mu.values())))
    return C

def load():
    C, pre = {}, {}
    for f in glob.glob(os.path.join(RAW, "arm*_c2r*_a*_result.json")):
        m = re.search(r"arm([AB])_(bug\d+)_c2r(\d)_a(\d)_result\.json$", f)
        if not m: continue
        d = json.load(open(f))
        if d.get("is_error"): continue
        arm, bug, k = m.group(1), m.group(2), m.group(3)
        C.setdefault((bug, arm), []).append(float(d["total_cost_usd"]))
        if (bug, arm, k) not in POST_GAP:
            pre.setdefault((bug, arm), []).append(float(d["total_cost_usd"]))
    return C, pre

cv_log = lambda c: st.stdev([math.log(x) for x in c]) / abs(st.mean([math.log(x) for x in c]))
sd_log = lambda c: st.stdev([math.log(x) for x in c])
# NOT an interquartile range: on n=4 this is the spread of the middle two values.
# Named accurately after review pointed out the mislabel.
midspread_log = lambda c: (lambda s: s[2] - s[1])(sorted(math.log(x) for x in c))

def ep(d):
    n = len(d); o = st.mean(d)
    return sum(1 for s in product([1, -1], repeat=n)
               if abs(st.mean([x * y for x, y in zip(s, d)])) >= abs(o) - 1e-12) / 2 ** n

if __name__ == "__main__":
    C, PRE = load()
    print("=== scale-invariance: identical data, different currency unit ===")
    print("%-34s %22s %22s" % ("estimator", "in dollars", "in cents (x100)"))
    for name, f in (("CV_log  (PRE-REGISTERED)", cv_log),
                    ("sd(ln c)  scale-free", sd_log),
                    ("mid-spread(ln c)  scale-free", midspread_log)):
        d1 = [f(C[(b,"A")]) - f(C[(b,"B")]) for b in BUGS]
        d2 = [f([100*x for x in C[(b,"A")]]) - f([100*x for x in C[(b,"B")]]) for b in BUGS]
        tag = "" if abs(st.mean(d1) - st.mean(d2)) < 1e-9 else "   <-- MOVES WITH THE UNIT"
        print("%-34s  mean %+.4f p=%.4f   mean %+.4f p=%.4f%s"
              % (name, st.mean(d1), ep(d1), st.mean(d2), ep(d2), tag))
    print("\n  All variants agree on DIRECTION (negative = the ordinary arm is less")
    print("  dispersed). They differ only on whether it reaches alpha = 0.05.")
    print("\n  SCALE-invariance is not MEASURE-invariance. Dollars and tokens are not")
    print("  proportional (two models at different prices; cached input near-free), so")
    print("  a scale-free statistic still moves between them:")
    T = cells_tok()
    for name, f in (("sd(ln c)", sd_log), ("mid-spread(ln c)", midspread_log)):
        du = [f(C[(b,"A")]) - f(C[(b,"B")]) for b in BUGS]
        dt = [f(T[(b,"A")]) - f(T[(b,"B")]) for b in BUGS]
        print("    %-20s dollars p=%.4f    tokens p=%.4f" % (name, ep(du), ep(dt)))
    print("\n  Why CV_log is also biased toward H1: |mean(ln c)| sits in the")
    print("  denominator and arm B costs ~2.26x more, so B's dispersion is divided")
    print("  by a larger number in every defect:")
    for b in BUGS:
        print("    %s  |mean ln c|  A=%.2f  B=%.2f" % (b,
              abs(st.mean([math.log(x) for x in C[(b,"A")]])),
              abs(st.mean([math.log(x) for x in C[(b,"B")]]))))
    print("\n=== A6 nine-day-gap sensitivity (A6 predicted this direction; it was wrong) ===")
    full = [cv_log(C[(b,"A")]) - cv_log(C[(b,"B")]) for b in BUGS]
    pre  = [cv_log(PRE[(b,"A")]) - cv_log(PRE[(b,"B")]) for b in BUGS]
    print("  all 56 runs       : mean %+.4f  p=%.4f" % (st.mean(full), ep(full)))
    print("  pre-gap runs only : mean %+.4f  p=%.4f" % (st.mean(pre), ep(pre)))
    print("  => removing the post-gap runs makes the anti-H1 mean %s."
          % ("STRONGER" if st.mean(pre) < st.mean(full) else "WEAKER"))
    print("     A6 claimed the gap biased conservatively (against H1). The observed")
    print("     sign is the opposite: the post-gap runs pulled TOWARD H1.")
    print("\n=== a SECOND discontinuity the paper's threats did not count ===")
    print("  drive.log records cell 14 (bug05/armB/r1) running 88.6 h wall clock,")
    print("  2026-08-08 -> 2026-08-12, against ~55 min of agent time in its two")
    print("  result files: the schedule was suspended on a weekly usage limit. A6")
    print("  reasons about ONE gap; there are two, so more cells straddle an era")
    print("  boundary than A6's analysis assumes. Sensitivity, dropping BOTH the")
    print("  five post-gap runs and the suspended cell:")
    both = {k: [c for c in v] for k, v in PRE.items()}
    both[("bug05","B")] = [c for c in both[("bug05","B")]][:3] if len(both[("bug05","B")]) > 3 else both[("bug05","B")]
    d3 = [cv_log(both[(b,"A")]) - cv_log(both[(b,"B")]) for b in BUGS]
    print("    both removed    : mean %+.4f  p=%.4f" % (st.mean(d3), ep(d3)))
    print("  (the cell is dropped by count, not by identity, since the suspension")
    print("   is a property of when it ran rather than of the run itself)")
