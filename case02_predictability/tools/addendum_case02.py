#!/usr/bin/env python3
"""Case02 pre-registered reporting that analyse_case02.py omitted.

PREREGISTRATION §4 requires, regardless of outcome: the seven per-defect CV
pairs, the observed difference, the exact p, AND a bootstrap CI on the median
difference. The frozen script printed the first three. This adds the fourth,
plus a recomputation of the exact p from the definition. NOTE, after review: this
is NOT an independent implementation. It imports analyse_case02.py by path and
reuses its cost extractor and its cv_log, so it re-derives only the PERMUTATION
ENUMERATION independently. A defect in the cost selection or in the estimator
would be reproduced identically by both. The agreement it reports is therefore a
check on the enumeration alone, and the §5 cost-level sign test.

Nothing here alters the primary analysis. Run after analyse_case02.py.
"""
import importlib.util, math, os, random, statistics as st
from itertools import product

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("a2", os.path.join(HERE, "analyse_case02.py"))
A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)

cells = {(b, arm): A.cell_costs(b, arm) for b in A.BUGS for arm in "AB"}
assert all(len(v) == 4 for v in cells.values()), "every cell must hold exactly 4 runs"

diffs = [A.cv_log(cells[(b, "A")]) - A.cv_log(cells[(b, "B")]) for b in A.BUGS]

# --- independent exact permutation p (sign enumeration, written from the
#     definition rather than reusing the frozen implementation) -------------
def exact_p_independent(d):
    n = len(d); obs = sum(d) / n
    ge = 0
    for bits in range(2 ** n):
        m = sum((d[i] if (bits >> i) & 1 else -d[i]) for i in range(n)) / n
        if abs(m) >= abs(obs) - 1e-12: ge += 1
    return ge / 2 ** n

# Deposit the per-defect difference column and the study totals. The article's
# §5.1 table and §3 totals had no deposited source until review pointed it out;
# the frozen script emits CV_log per arm but not their difference.
print("=== per-defect CV_log difference (A - B), the §5.1 table's last column ===")
for b, d in zip(A.BUGS, [A.cv_log(cells[(x,"A")]) - A.cv_log(cells[(x,"B")]) for x in A.BUGS]):
    print("  %-7s %+0.4f" % (b, d))
_tot = sum(sum(v) for v in cells.values())
_a = sum(sum(cells[(b,"A")]) for b in A.BUGS); _b = sum(sum(cells[(b,"B")]) for b in A.BUGS)
print("\nstudy totals: $%.2f  (arm A $%.2f, arm B $%.2f)  over %d runs\n"
      % (_tot, _a, _b, sum(len(v) for v in cells.values())))

p_ind = exact_p_independent(diffs)
p_frozen = A.exact_paired_permutation(diffs)
print("exact p  (frozen impl)              : %.4f" % p_frozen)
print("exact p  (enumeration re-derived)   : %.4f" % p_ind)
print("agree                               :", abs(p_ind - p_frozen) < 1e-12)
print("NB: shares cost extraction + estimator with the frozen script; this checks")
print("    the permutation enumeration only, not the upstream pipeline.")

# --- bootstrap CI on the MEDIAN difference (§4) ---------------------------
rng = random.Random(20260807)          # the pre-registration's seed
B = 100000
meds = []
for _ in range(B):
    s = [diffs[rng.randrange(7)] for _ in range(7)]
    meds.append(st.median(s))
meds.sort()
lo, hi = meds[int(0.025 * B)], meds[int(0.975 * B)]
print("\nobserved median difference (A-B): %+.4f" % st.median(diffs))
print("bootstrap 95%% CI (B=%d, seed 20260807): [%+.4f, %+.4f]" % (B, lo, hi))
print("CI spans zero:", lo <= 0 <= hi)

# --- §5 secondary: cost LEVEL, matched-pair ratio + sign test -------------
print("\n--- secondary (§5): cost level, not dispersion ---")
ratios, signs = [], []
for b in A.BUGS:
    ma, mb = st.mean(cells[(b, "A")]), st.mean(cells[(b, "B")])
    ratios.append(mb / ma); signs.append(1 if mb > ma else -1)
    print("  %s  meanA=$%7.2f  meanB=$%7.2f  B/A=%.2fx" % (b, ma, mb, mb / ma))
k = sum(1 for s in signs if s > 0); n = len(signs)
p_sign = sum(math.comb(n, i) for i in range(n + 1)
             if abs(i - n / 2) >= abs(k - n / 2)) / 2 ** n
print("  median B/A ratio: %.2fx   sign test: %d/%d defects cost more under B, two-sided p = %.4f"
      % (st.median(ratios), k, n, p_sign))

# --- sensitivity, POST-HOC and NOT the headline (§7 forbids outlier removal) ---
print("\n--- POST-HOC sensitivity (NOT a pre-registered analysis) ---")
print("A7 recorded, before this ran, that bug05 armB holds one resumed-completion")
print("cost and that this would inflate its CV. Leave-one-defect-out:")
for i, b in enumerate(A.BUGS):
    d2 = diffs[:i] + diffs[i + 1:]
    print("  drop %s -> mean diff %+.4f, exact p = %.4f" % (b, sum(d2) / 6, exact_p_independent(d2)))
