#!/usr/bin/env python3
"""Corrected analysis, rebuilt after adversarial review (2026-08-05).

Fixes the three measurement defects the reviewers found:
  1. token totals come from `modelUsage` (includes subagent/reviewer tokens),
     not `usage` (main loop only, which under-counted by 29-99%);
  2. the one imputed cell is priced with the study's OWN pre-registered D3
     rate table rather than a blended rate borrowed from a different cell
     whose denominator was itself truncated (that inflated it ~1.6x);
  3. statistics are reported with intervals, and the estimator is named.

Usage: python3 tools/analyse.py
"""
import glob
import json
import os
import re
import statistics as st
from itertools import combinations

CASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(CASE, "ledger", "raw")

# Pre-registered D3 rates, USD per MTok: in / cache-write / cache-read / out.
# D3 froze Opus 4.8 at 5/10/0.50/25; the model actually used is unpriced there,
# so we price with this table AND report the platform figure, per review C3.
D3 = (5.0, 10.0, 0.50, 25.0)
KEYS = ("inputTokens", "cacheCreationInputTokens",
        "cacheReadInputTokens", "outputTokens")


def cell_tokens_and_cost(arm, bug, tag="v4"):
    """(4-tuple of tokens from modelUsage, platform USD, n_attempts)."""
    tok = [0, 0, 0, 0]
    usd = 0.0
    n = 0
    for p in sorted(glob.glob(os.path.join(RAW, f"arm{arm}_{bug}_{tag}_a*_result.json"))):
        try:
            d = json.load(open(p))
        except Exception:
            continue
        n += 1
        usd += d.get("total_cost_usd") or 0
        for mu in (d.get("modelUsage") or {}).values():
            for i, k in enumerate(KEYS):
                tok[i] += int(mu.get(k) or 0)
    return tok, usd, n


def d3_price(tok):
    return sum(t / 1e6 * r for t, r in zip(tok, D3))


def sign_test_two_sided(n_pos, n):
    """Exact two-sided sign test p-value."""
    from math import comb
    tail = sum(comb(n, k) for k in range(n_pos, n + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def median_ci(vals, conf=0.95):
    """Nonparametric CI for the median from order statistics."""
    from math import comb
    n = len(vals)
    s = sorted(vals)
    best = (s[0], s[-1], 0.0)
    for i in range(n // 2 + 1):
        cov = 1 - 2 * sum(comb(n, k) for k in range(i)) / 2 ** n
        if cov >= conf:
            best = (s[i], s[n - 1 - i], cov)
    return best


BUGS = [f"bug{i:02d}" for i in range(1, 8)]
rows = {}
for bug in BUGS:
    for arm in "AB":
        tok, usd, n = cell_tokens_and_cost(arm, bug)
        if n:
            rows[(arm, bug)] = {"tok": tok, "usd": usd, "n": n,
                                "d3": d3_price(tok), "imputed": False}

# bug03/B: attempt 1 emitted no result record. Recovered token classes come
# from the session transcripts (ledger row acceptance_bug03B_v4).
REC = [325, 358624, 34175067, 132209]
if ("B", "bug03") in rows:
    r = rows[("B", "bug03")]
    r["tok"] = REC
    r["d3"] = d3_price(REC)
    r["usd"] = r["d3"]          # no platform figure exists for the lost attempt
    r["imputed"] = True

print("PER-CELL (v4). tokens = modelUsage incl. subagents; D3 = pre-registered rates\n")
print("%-6s %-4s %10s %10s %9s %5s" % ("bug", "arm", "tokens", "platform $", "D3 $", "att"))
for bug in BUGS:
    for arm in "AB":
        r = rows.get((arm, bug))
        if not r:
            continue
        mark = " *imputed" if r["imputed"] else ""
        print("%-6s %-4s %10.2fM %10.2f %9.2f %5d%s"
              % (bug, arm, sum(r["tok"]) / 1e6, r["usd"], r["d3"], r["n"], mark))

pairs = [b for b in BUGS if ("A", b) in rows and ("B", b) in rows]
print(f"\nMATCHED PAIRS: {len(pairs)} -> {', '.join(pairs)}\n")

for basis, key in (("platform USD", "usd"), ("D3-priced", "d3"),
                   ("raw tokens", None)):
    ratios = []
    for b in pairs:
        a = sum(rows[("A", b)]["tok"]) if key is None else rows[("A", b)][key]
        bb = sum(rows[("B", b)]["tok"]) if key is None else rows[("B", b)][key]
        ratios.append(bb / a)
    lo, hi, cov = median_ci(ratios)
    print("%-12s median %.2fx  range %.2f-%.2f  CI[%.2f,%.2f] @%.0f%%"
          % (basis, st.median(ratios), min(ratios), max(ratios), lo, hi, cov * 100))

n_pos = sum(1 for b in pairs if rows[("B", b)]["usd"] > rows[("A", b)]["usd"])
print("\nFCDD dearer on %d of %d pairs; exact two-sided sign test p = %.3f"
      % (n_pos, len(pairs), sign_test_two_sided(n_pos, len(pairs))))

# dispersion, with and without the cell the reviewers flagged
for label, drop in (("all cells", None), ("excluding bug01", "bug01")):
    out = []
    for arm in "AB":
        v = [rows[(arm, b)]["usd"] for b in BUGS
             if (arm, b) in rows and b != drop]
        out.append("Arm %s spread %.2fx (n=%d)" % (arm, max(v) / min(v), len(v)))
    print("dispersion, %-16s %s" % (label + ":", "   ".join(out)))

gaps = [rows[("B", b)]["usd"] - rows[("A", b)]["usd"] for b in pairs]
print("\nper-pair gap: mean $%.2f, median $%.2f (NOT the difference of medians)"
      % (st.mean(gaps), st.median(gaps)))

# quality: paired differences
Q = {"bug02": (14 / 3, 14 / 3), "bug03": (14 / 3, 12 / 3),
     "bug04": (12 / 3, 14 / 3), "bug06": (12 / 3, 15 / 3)}
d = [b - a for a, b in Q.values()]
m, sd, n = st.mean(d), st.stdev(d), len(d)
half = 3.182 * sd / n ** 0.5          # t(3), 95%
print("quality paired diff (B-A): %s" % ", ".join("%+.2f" % x for x in d))
print("  mean %+.3f, 95%% CI [%+.2f, %+.2f] -> spans zero; no statement warranted"
      % (m, m - half, m + half))
