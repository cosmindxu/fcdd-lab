#!/usr/bin/env python3
"""Case 07 analysis — every reported number comes from here (C10).

Input: ledger/adjudicated.json, written by the third party (tools/adjudicate.md),
one record per finding:
  {unit, arm: CONV|BUDGET, confirmed: bool, severity: blocking|non-blocking|
   unreachable, match_group: id|null, absorbed_by_residual: bool,
   in_surface: bool, rediscovery: bool, disputed: bool}
plus ledger/runs.json: {unit, arm, repeat, rounds, cost_consumed, cost_completing,
   censored: bool}

Run with --dry-run to execute against tools/fixture_adjudicated.json — C5 requires
a dry-run before freeze; the dry-run against a REAL pilot cell is still owed.
"""
import json, os, sys, statistics as st
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))


def load(dry):
    if dry:
        a = json.load(open(os.path.join(HERE, "fixture_adjudicated.json")))
        r = json.load(open(os.path.join(HERE, "fixture_runs.json")))
    else:
        a = json.load(open(os.path.join(HERE, "..", "ledger", "adjudicated.json")))
        r = json.load(open(os.path.join(HERE, "..", "ledger", "runs.json")))
    return a, r


def main():
    dry = "--dry-run" in sys.argv
    adj, runs = load(dry)
    out = ["CASE 07 — bounded vs unbounded ATTACK" + ("  [DRY RUN — fixture data]" if dry else "")]

    # units rendered NOT DECIDABLE by a censored CONV cell (fail-direction, r3)
    censored_units = {r["unit"] for r in runs if r["arm"] == "CONV" and r.get("censored")}

    # eligible findings: confirmed, in-surface, not a rediscovery
    def eligible(f):
        return f["confirmed"] and f["in_surface"] and not f["rediscovery"]

    conv_block = defaultdict(set)   # unit -> match_groups
    bud_any = defaultdict(set)
    bud_absorbed = defaultdict(set)
    for f in adj:
        if not eligible(f):
            continue
        g = f["match_group"]
        if f["arm"] == "CONV" and f["severity"] == "blocking":
            conv_block[f["unit"]].add(g)
        if f["arm"] == "BUDGET":
            bud_any[f["unit"]].add(g)
            if f.get("absorbed_by_residual"):
                bud_absorbed[f["unit"]].add(g)

    out.append("\nPRIMARY — CONV confirmed-blocking, in-surface, missed by BUDGET")
    out.append(f"{'unit':<40}{'CONV blk':>9}{'missed':>8}{'found-unconf':>14}  status")
    out.append("-" * 82)
    total_b = total_missed = 0
    decidable_units = 0
    for unit in sorted(set(list(conv_block) + list(bud_any))):
        if unit in censored_units:
            out.append(f"{unit:<40}{'—':>9}{'—':>8}{'—':>14}  NOT DECIDABLE (CONV censored)")
            continue
        decidable_units += 1
        b = conv_block[unit]
        missed = b - bud_any[unit] - bud_absorbed[unit]
        unconf = b & bud_absorbed[unit]
        total_b += len(b); total_missed += len(missed)
        status = "SAFE" if not missed else "MISS — H1 FALSIFIED on this unit"
        out.append(f"{unit:<40}{len(b):>9}{len(missed):>8}{len(unconf):>14}  {status}")

    out.append(f"\n  totals: b = {total_b} confirmed blocking (CONV), missed = {total_missed}, "
               f"over {decidable_units} decidable units")
    if total_missed:
        out.append("  VERDICT: the two-round default MISSED a confirmed blocking finding — H1 falsified.")
    else:
        # rule of three over UNITS (the clustering unit), not findings — round 2 B4
        bound = 3.0 / decidable_units if decidable_units else float("nan")
        out.append(f"  VERDICT: no miss. Rule-of-three over units: ≤ {bound:.0%} of units may harbour "
                   f"a miss (95%), n = {decidable_units} units.")
        out.append("  NOTE: the bound is per UNIT because misses cluster by unit and round-depth;")
        out.append("        a per-finding bound would assume an independence the structure violates.")

    out.append("\nCOST — headline CONSUMED, median per unit")
    per = defaultdict(lambda: defaultdict(list))
    for r in runs:
        if r.get("censored"):
            continue
        per[r["arm"]]["consumed"].append(r["cost_consumed"])
        per[r["arm"]]["completing"].append(r["cost_completing"])
        per[r["arm"]]["rounds"].append(r["rounds"])
    for acct in ("consumed", "completing"):
        c, b_ = per["CONV"][acct], per["BUDGET"][acct]
        if c and b_:
            ratio = st.median(b_) / st.median(c)
            tag = "  <- HEADLINE" if acct == "consumed" else ""
            out.append(f"  {acct:<11} CONV {st.median(c):8.2f}   BUDGET {st.median(b_):8.2f}   "
                       f"ratio {ratio:.2f}{tag}")
    for arm in ("CONV", "BUDGET"):
        rd = per[arm]["rounds"]
        if rd:
            out.append(f"  rounds {arm:<7} min {min(rd)}  median {st.median(rd)}  max {max(rd)}  "
                       f"spread {max(rd)/max(min(rd),1):.0f}x")
    bud_rounds = per["BUDGET"]["rounds"]
    if bud_rounds and max(bud_rounds) > 2:
        out.append("  ** DELIVERED-TREATMENT CHECK FAILED: a BUDGET cell exceeded its declared budget **")
    elif bud_rounds:
        out.append("  delivered-treatment check: every BUDGET cell within its declared budget — OK")

    disputed = [f for f in adj if f.get("disputed")]
    out.append(f"\nDISPUTED (reported, never silently resolved): {len(disputed)}")
    txt = "\n".join(out)
    print(txt)
    if not dry:
        open(os.path.join(HERE, "..", "ledger", "RESULT.txt"), "w").write(txt + "\n")


if __name__ == "__main__":
    main()
