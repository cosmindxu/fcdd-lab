#!/usr/bin/env python3
"""Enumerate case 07's review units: verdict / money-path modules only.

Round 2 M3: BLOCKING ("wrong verdict or money-path action") is undecidable for
indicator code that emits numbers and takes no action, so the unit list is
restricted to modules that DECIDE or ACT. Selection is by declared signal, not
by reading the code, so it is reproducible.

Strata: HARDENED = named in the skill's references/case_study.md (FCDD was
distilled from this codebase's own arc, so those modules were already attacked);
UNHARDENED = the rest.
"""
import os, re, json, sys

SRC = "/media/sf_Projects/ikbr_tools/ikbr_tools"
SCRIPTS = "/media/sf_Projects/ikbr_tools/scripts"
CASE_STUDY = "/media/sf_Projects/fcdd_lab/skills/formal-contract-dev-current/references/case_study.md"

# a unit DECIDES or ACTS if it emits a verdict or places/cancels an order
DECIDES = re.compile(r"\b(verdict|SAFE|DANGER|UNKNOWN|halt|latch|kill.?switch|"
                     r"breach|guard|block_trade|allow_trade)\b")
ACTS = re.compile(r"\b(placeOrder|place_order|cancelOrder|cancel_order|"
                  r"submit_order|reqGlobalCancel|liquidat)\b")
MIN_LINES = 200


def main():
    cs = open(CASE_STUDY).read()
    units = []
    for root in (SRC, SCRIPTS):
        if not os.path.isdir(root):
            continue
        for f in sorted(os.listdir(root)):
            if not f.endswith(".py") or f.startswith("test_"):
                continue
            p = os.path.join(root, f)
            src = open(p, errors="ignore").read()
            n = src.count("\n")
            if n < MIN_LINES:
                continue
            # strip comments/docstrings: a token inside prose is not a decision
            code = re.sub(r'(?s)""".*?"""|\'\'\'.*?\'\'\'', "", src)
            code = re.sub(r"(?m)#.*$", "", code)
            dtok = {m.group(0).lower() for m in DECIDES.finditer(code)}
            a = bool(ACTS.search(code))
            # a unit qualifies only if it ACTS, or DECIDES on >=3 distinct tokens
            if not (a or len(dtok) >= 3):
                continue
            d = bool(dtok)
            stem = f[:-3]
            units.append({
                "unit": os.path.relpath(p, "/media/sf_Projects/ikbr_tools"),
                "lines": n,
                "signal": (f"decides:{len(dtok)}" if d else "") + ("+acts" if a else ""),
                "stratum": "HARDENED" if re.search(re.escape(stem), cs) else "UNHARDENED",
            })
    units.sort(key=lambda u: (u["stratum"], -u["lines"]))
    json.dump(units, open(os.path.join(os.path.dirname(__file__), "..", "ledger", "units.json"), "w"), indent=1)
    print(f"{'unit':<44}{'lines':>7}  {'signal':<14}stratum")
    print("-" * 82)
    for u in units:
        print(f"{u['unit']:<44}{u['lines']:>7}  {u['signal']:<14}{u['stratum']}")
    from collections import Counter
    print("\n", dict(Counter(u["stratum"] for u in units)), f"| {len(units)} units")
    print("Selection order (pre-registered): descending lines within stratum, alternating strata.")


if __name__ == "__main__":
    main()
