#!/usr/bin/env python3
"""A13 — which models actually executed the study, and in what proportion per arm.

The pre-registration (§2) required the model to be "identical across arms, fixed
for the whole study". The runner passed --model claude-opus-5 to the session it
launched; it had no control over what that session delegated to via the Task
tool, and both arm prompts instruct the agent to spawn a reviewer. This reads the
per-model `modelUsage` block that was in every result file all along.
"""
import collections, glob, json, os, re
RAW = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
      os.path.abspath(__file__)))), "case01_spectrum_gambit", "ledger", "raw")
spend = collections.Counter(); runs = collections.Counter()
byarm = collections.defaultdict(collections.Counter); n = 0
for f in glob.glob(os.path.join(RAW, "arm*_c2r*_a*_result.json")):
    m = re.search(r"arm([AB])_(bug\d+)_c2r(\d)_a(\d)_result\.json$", f)
    if not m: continue
    d = json.load(open(f))
    if d.get("is_error"): continue
    n += 1
    for model, v in (d.get("modelUsage") or {}).items():
        c = v.get("costUSD") or 0
        spend[model] += c; runs[model] += 1; byarm[m.group(1)][model] += c
tot = sum(spend.values())
print("non-error runs: %d\n" % n)
print("%-22s %-14s %12s %8s" % ("model", "runs containing", "spend", "share"))
for mdl, c in spend.most_common():
    print("%-22s %8d/%-4d %12.2f %7.1f%%" % (mdl, runs[mdl], n, c, 100 * c / tot))
print("\nper-arm mix (the pre-registration required these to match):")
for arm in "AB":
    t = sum(byarm[arm].values())
    print("  arm %s  total $%.2f" % (arm, t))
    for mdl, c in sorted(byarm[arm].items(), key=lambda x: -x[1]):
        print("     %-22s $%8.2f  %5.1f%%" % (mdl, c, 100 * c / t))
# The contribution IS boundable from this same field -- an earlier draft of the
# threats section claimed it was not. Recompute the headline cost ratio using only
# the primary model's spend, i.e. with the subagent model removed entirely.
import collections as _c, math, statistics as st, glob as _g, json as _j, re as _r
from itertools import product as _p
prim = _c.defaultdict(list); allc = _c.defaultdict(list)
for f in _g.glob(os.path.join(RAW, "arm*_c2r*_a*_result.json")):
    m = _r.search(r"arm([AB])_(bug\d+)_c2r(\d)_a(\d)_result\.json$", f)
    if not m: continue
    d = _j.load(open(f))
    if d.get("is_error"): continue
    mu = d.get("modelUsage") or {}
    prim[(m.group(2), m.group(1))].append(float((mu.get("claude-opus-5") or {}).get("costUSD") or 0))
    allc[(m.group(2), m.group(1))].append(float(d["total_cost_usd"]))
BUGS = ["bug%02d" % i for i in range(1, 8)]
def _sign(k, n):
    return sum(math.comb(n, i) for i in range(n+1) if abs(i-n/2) >= abs(k-n/2)) / 2**n
print("\nBOUNDING the mix: headline cost ratio with the subagent model removed")
for name, C in (("all spend (as reported)", allc), ("primary model only", prim)):
    r = [st.mean(C[(b,"B")])/st.mean(C[(b,"A")]) for b in BUGS]
    print("  %-24s median B/A = %.2fx   %d/7 defects dearer   sign p = %.4f"
          % (name, st.median(r), sum(1 for x in r if x > 1), _sign(sum(1 for x in r if x > 1), 7)))
def _cv(c):
    ln = [math.log(x) for x in c if x > 0]
    return st.stdev(ln)/abs(st.mean(ln)) if len(ln) == len(c) else None
def _ep(d):
    n=len(d); o=st.mean(d)
    return sum(1 for s in _p([1,-1],repeat=n) if abs(st.mean([x*y for x,y in zip(s,d)]))>=abs(o)-1e-12)/2**n
dp = [_cv(prim[(b,"A")])-_cv(prim[(b,"B")]) for b in BUGS]
if all(x is not None for x in dp):
    print("  primary-model-only PRIMARY estimator: mean %+.4f  exact p = %.4f" % (st.mean(dp), _ep(dp)))

sec = [m for m in spend if m != "claude-opus-5"]
if sec:
    a = 100 * byarm["A"][sec[0]] / sum(byarm["A"].values())
    b = 100 * byarm["B"][sec[0]] / sum(byarm["B"].values())
    print("\nimbalance in %s share: arm A %.1f%% vs arm B %.1f%%  (%.1f points)" % (sec[0], a, b, abs(a - b)))
