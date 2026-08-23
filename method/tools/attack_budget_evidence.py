#!/usr/bin/env python3
"""Evidence for ATTACK_BUDGET_DIAGNOSIS.md — recomputed from case02's deposits.

Round counts are lexical (mentions of "round N" / "attack round" / "review round"
in each run's FIX_NOTES.md). That is a proxy, not an instrumented counter: the
runs were never instrumented to emit a round count, which is itself a finding —
see the diagnosis's validation section. The proxy is applied identically to both
arms, so the ARM CONTRAST is fair even where the absolute counts are noisy.
"""
import glob, json, os, re, statistics as st
# method/tools/x.py -> method/tools -> method -> fcdd_lab. Three levels.
# (An earlier version was one short: the same defect case02 recorded as A8.)
LAB = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(LAB, "case01_spectrum_gambit", "ledger", "raw")
W   = os.path.expanduser("~/fcdd_arms")
BUGS = ["bug%02d" % i for i in range(1, 8)]
ROUND = re.compile(r'round\s*[1-9#]|attack round|review round', re.I)

def cost(arm, bug, k):
    for x in glob.glob(os.path.join(RAW, "arm%s_%s_c2r%d_a*_result.json" % (arm, bug, k))):
        d = json.load(open(x))
        if not d.get("is_error"): return float(d["total_cost_usd"])
    return None

def rounds(arm, bug, k):
    p = os.path.join(W, "%s_arm%s_c2r%d" % (bug, arm, k), "FIX_NOTES.md")
    if not os.path.exists(p): return None
    return len(ROUND.findall(open(p, errors="replace").read()))

def pearson(pts):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    mx, my = st.mean(xs), st.mean(ys)
    den = (sum((x-mx)**2 for x in xs) * sum((y-my)**2 for y in ys)) ** 0.5
    return sum((x-mx)*(y-my) for x, y in pts) / den if den else 0.0

print("%-4s %-22s %-8s %-16s %s" % ("arm","rounds min..max,med","spread","r(rounds,cost)","median within-cell cost spread"))
for arm in "AB":
    pts, spreads = [], []
    for b in BUGS:
        cs = []
        for k in (1, 2, 3, 4):
            c, r = cost(arm, b, k), rounds(arm, b, k)
            if c is not None:
                cs.append(c)
                if r is not None: pts.append((r, c))
        if cs: spreads.append(max(cs) / min(cs))
    xs = [p[0] for p in pts]
    print("%-4s %-22s %-8s %-16.3f %.2fx"
          % (arm, "%d..%d, %.0f" % (min(xs), max(xs), st.median(xs)),
             "%.0fx" % (max(xs) / max(1, min(xs))), pearson(pts), st.median(spreads)))

print("\nwhat the extra rounds bought:")
for lo, hi, lbl in ((6, 99, ">=6 rounds"), (0, 2, "<=2 rounds")):
    sel = [(rounds("B", b, k), cost("B", b, k)) for b in BUGS for k in (1, 2, 3, 4)]
    sel = [(r, c) for r, c in sel if r is not None and c is not None and lo <= r <= hi]
    print("  arm B %-11s n=%2d  mean cost $%.2f" % (lbl, len(sel), st.mean([c for _, c in sel])))
print("  all 56 runs produced a binary byte-identical to pristine (case02 A12),")
print("  so no extra round changed any artefact.")
