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
    disputed_units = {f["unit"] for f in adj if f.get("disputed")}
    # round 3 B6: a NAMED residual is unconfirmed by definition — law 12 produces
    # exactly these — so it is read from its own channel, not through eligible().
    for f in adj:
        if (f["arm"] == "BUDGET" and f.get("absorbed_by_residual")
                and f["in_surface"] and not f["rediscovery"]):
            bud_absorbed[f["unit"]].add(f["match_group"])
    for f in adj:
        # round 3 B5: a null match_group cannot be reasoned about — two distinct
        # findings would collapse into one, and cross-arm nulls would cancel.
        if f["match_group"] is None:
            sys.exit("REFUSED: finding with null match_group in %s — adjudicator must group it"
                     % f["unit"])
        if not eligible(f):
            continue
        g = f["match_group"]
        if f["arm"] == "CONV" and f["severity"] == "blocking":
            conv_block[f["unit"]].add(g)
        # round 3 B5: the subtrahend must be BLOCKING-only. A BUDGET finding graded
        # non-blocking or unreachable previously cancelled a CONV blocking finding.
        if f["arm"] == "BUDGET" and f["severity"] == "blocking":
            bud_any[f["unit"]].add(g)

    out.append("\nPRIMARY — CONV confirmed-blocking, in-surface, missed by BUDGET")
    out.append(f"{'unit':<40}{'CONV blk':>9}{'missed':>8}{'found-unconf':>14}  status")
    out.append("-" * 82)
    total_b = total_missed = 0
    decidable_units = 0
    # round 3 M5: only a unit with >=1 CONV confirmed blocking finding can exhibit
    # a miss; including others inflates n and falsely tightens the bound.
    for unit in sorted(conv_block):
        if unit in censored_units:
            out.append(f"{unit:<40}{'—':>9}{'—':>8}{'—':>14}  NOT DECIDABLE (CONV censored)")
            continue
        decidable_units += 1
        b = conv_block[unit]
        missed = b - bud_any[unit] - bud_absorbed[unit]
        unconf = b & bud_absorbed[unit]
        if unit in disputed_units:      # B5: never silently merged
            out.append(f"{unit:<40}{len(b):>9}{'—':>8}{'—':>14}  NOT DECIDABLE (disputed match)")
            decidable_units -= 1
            continue
        total_b += len(b); total_missed += len(missed)
        status = ("MISS — H1 FALSIFIED on this unit" if missed
                  else "SAFE (rests on residual absorption)" if unconf else "SAFE")
        out.append(f"{unit:<40}{len(b):>9}{len(missed):>8}{len(unconf):>14}  {status}")

    out.append(f"\n  totals: b = {total_b} confirmed blocking (CONV), missed = {total_missed}, "
               f"over {decidable_units} decidable units")
    # round 3 B4: a verdict from zero evidence is a vacuous SAFE — the wrong fail
    # direction under law 1. The §7 gate lives here, not only in prose.
    if total_b < 1 or decidable_units < 1:
        out.append("  VERDICT: NOT DECIDABLE — NO VERDICT. The corpus produced no confirmed")
        out.append("           blocking finding in CONV (or no decidable unit), so H1 was")
        out.append("           never put at risk. This is a corpus result, not a safety result.")
    elif total_missed:
        out.append("  VERDICT: the two-round default MISSED a confirmed blocking finding — H1 falsified.")
    else:
        # rule of three over UNITS (the clustering unit), not findings — round 2 B4
        bound = min(1.0, 3.0 / decidable_units)
        out.append(f"  VERDICT: no miss. Rule-of-three over units: ≤ {bound:.0%} of units may harbour "
                   f"a miss (95%), n = {decidable_units} units.")
        if bound >= 0.20:
            out.append("  ** the bound is no tighter than the 20% ceiling round 2 rejected as an")
            out.append("     unargued safety number — the QUANTITATIVE claim is NOT made. **")
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
    over = [r for r in runs if r["arm"] == "BUDGET" and r["rounds"] > r.get("declared_budget", 2)]
    under = [r for r in runs if r["arm"] == "BUDGET" and r["rounds"] < 1]
    if not [r for r in runs if r["arm"] == "BUDGET"]:
        out.append("  ** no BUDGET runs — delivered-treatment check cannot be computed **")
    elif over or under:
        out.append(f"  ** DELIVERED-TREATMENT CHECK FAILED: {len(over)} cell(s) over their declared "
                   f"budget, {len(under)} under the mandatory pass **")
    else:
        out.append("  delivered-treatment check: every BUDGET cell within its declared budget — OK")

    disputed = [f for f in adj if f.get("disputed")]
    out.append(f"\nDISPUTED (reported, never silently resolved): {len(disputed)}")
    txt = "\n".join(out)
    print(txt)
    if not dry:
        open(os.path.join(HERE, "..", "ledger", "RESULT.txt"), "w").write(txt + "\n")


if __name__ == "__main__":
    main()
