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
sec = [m for m in spend if m != "claude-opus-5"]
if sec:
    a = 100 * byarm["A"][sec[0]] / sum(byarm["A"].values())
    b = 100 * byarm["B"][sec[0]] / sum(byarm["B"].values())
    print("\nimbalance in %s share: arm A %.1f%% vs arm B %.1f%%  (%.1f points)" % (sec[0], a, b, abs(a - b)))
