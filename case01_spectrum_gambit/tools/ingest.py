#!/usr/bin/env python3
"""Ingest finished arm runs into ledger/runs.csv (idempotent).

Scans ledger/raw/arm{A,B}_bugNN_v3_a*_result.json, groups attempts per
arm x bug, and appends ONE row per cell summing the attempts' costs and
tokens (A9: a run's attempts are one measurement). Rows already present
(matched by run_id) are skipped, so this is safe to re-run at any time.

Usage: python3 tools/ingest.py [--commit-note "..."]
"""
import glob
import json
import os
import re
import sys

CASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(CASE, "ledger", "raw")
CSV = os.path.join(CASE, "ledger", "runs.csv")
KEYS = ("input_tokens", "cache_creation_input_tokens",
        "cache_read_input_tokens", "output_tokens")


def load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def main():
    existing = open(CSV).read() if os.path.exists(CSV) else ""
    cells = {}
    pat = re.compile(r"arm([AB])_(bug\d\d)_v(3|4)_a(\d+)_result\.json$")
    for p in sorted(glob.glob(os.path.join(RAW, "arm*_v[34]_a*_result.json"))):
        m = pat.search(os.path.basename(p))
        if not m:
            continue
        arm, bug, ver, att = m.group(1), m.group(2), m.group(3), int(m.group(4))
        d = load(p)
        if not d:
            continue
        c = cells.setdefault((arm, bug, ver), {"tok": [0, 0, 0, 0], "usd": 0.0,
                                          "turns": 0, "att": 0, "ok": False,
                                          "models": set(), "files": []})
        for mu in (d.get("modelUsage") or {}):
            c["models"].add(mu)
        u = d.get("usage") or {}
        for i, k in enumerate(KEYS):
            c["tok"][i] += int(u.get(k) or 0)
        c["usd"] += float(d.get("total_cost_usd") or 0)
        c["turns"] += int(d.get("num_turns") or 0)
        c["att"] = max(c["att"], att)
        c["ok"] = c["ok"] or not d.get("is_error")
        c["files"].append(os.path.relpath(p, CASE))

    new = []
    for (arm, bug, ver), c in sorted(cells.items()):
        run_id = f"arm{arm}_{bug}_v{ver}"
        if re.search(rf"^{run_id},", existing, re.M):
            continue
        if not c["ok"]:
            continue                      # still running / not yet complete
        models = "+".join(sorted(c["models"])) or "?"
        gate = f"gate-selfreported-v{ver}"
        note = (f"VALID(v{ver}) {c['att']} attempt(s) summed; "
                f"cli_usd={c['usd']:.2f}; turns={c['turns']}; "
                f"prompt v{ver}; A9 resilient runner")
        row = [run_id, "2026-07-31", f"arm{arm}:{bug}", arm, "fix", bug,
               models, "max", ";".join(c["files"])]
        row += [str(t) for t in c["tok"]]
        row += ["", gate, note]
        new.append(",".join(row))

    if new:
        with open(CSV, "a") as f:
            f.write("\n".join(new) + "\n")
    print(f"ingested {len(new)} new cell(s)")
    for r in new:
        print("  " + r[:120])
    pending = [f"arm{a}:{b}(v{v})" for (a, b, v), c in sorted(cells.items()) if not c["ok"]]
    if pending:
        print("in progress / incomplete: " + ", ".join(pending))
    return 0


if __name__ == "__main__":
    sys.exit(main())
