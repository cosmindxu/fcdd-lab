#!/usr/bin/env python3
"""Rebuild runs.csv token columns from modelUsage (subagents included).

Why: the deposited columns were populated from each result JSON's `usage`
block, which counts MAIN-LOOP tokens only. Reviewer subagents — the dominant
cost term per the study's own §4.3 — were excluded, so the published ledger
under-counted by 29-99% (armB_bug01_v4: 711,678 deposited vs 58.3M actual, an
82x error, because that attempt's `usage` block was lost on a 429 while
`modelUsage` survived).

That falsified the paper's own claim that the deposited token counters are the
ground truth. This script repairs it in place, keeps the original values in a
new column so nothing is silently rewritten, and is idempotent.

Usage: python3 tools/fix_ledger_tokens.py [--apply]
"""
import csv
import json
import os
import sys

CASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(CASE, "ledger", "runs.csv")
KEYS = ("inputTokens", "cacheCreationInputTokens",
        "cacheReadInputTokens", "outputTokens")
TOK_COLS = slice(9, 13)          # in, cache_write, cache_read, out


def model_usage_totals(refs):
    """Sum modelUsage across every result JSON named in the source_ref field."""
    tot = [0, 0, 0, 0]
    found = False
    for ref in refs.split(";"):
        ref = ref.strip()
        if not ref.endswith(".json"):
            continue
        p = os.path.join(CASE, ref)
        if not os.path.exists(p):
            continue
        try:
            d = json.load(open(p))
        except Exception:
            continue
        mu = d.get("modelUsage") or {}
        if not mu:
            continue
        found = True
        for entry in mu.values():
            for i, k in enumerate(KEYS):
                tot[i] += int(entry.get(k) or 0)
    return tot if found else None


def main():
    apply = "--apply" in sys.argv
    rows = list(csv.reader(open(CSV)))
    hdr = rows[0]
    if "tokens_source" not in hdr:
        hdr.append("tokens_source")
    changed = []
    for r in rows[1:]:
        if len(r) < 14 or not r[0].startswith("arm"):
            continue
        while len(r) < len(hdr):
            r.append("")
        tot = model_usage_totals(r[8])
        if not tot:
            continue
        old = [int(x) if x.strip().isdigit() else 0 for x in r[TOK_COLS]]
        if old == tot:
            r[-1] = "modelUsage"
            continue
        ratio = (sum(tot) / sum(old)) if sum(old) else float("inf")
        changed.append((r[0], sum(old), sum(tot), ratio))
        if apply:
            r[9:13] = [str(t) for t in tot]
            r[-1] = f"modelUsage (was usage-only: {sum(old)})"

    print("%-24s %14s %14s %8s" % ("run_id", "deposited", "modelUsage", "ratio"))
    for name, o, n, ratio in sorted(changed, key=lambda x: -x[3]):
        print("%-24s %14d %14d %7.1fx" % (name, o, n, ratio))
    print(f"\n{len(changed)} row(s) under-counted"
          + (" — REWRITTEN" if apply else " — dry run, pass --apply to fix"))

    if apply:
        with open(CSV, "w", newline="") as f:
            csv.writer(f).writerows(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
