#!/usr/bin/env python3
"""Case 04 — build ledger/runs.json for analyse_case04.py from the
schedule, the scorer outputs, and the per-cell session logs.

Per PREREGISTRATION §7, the cost of infrastructure-dying attempts is
recorded and excluded: cost_usd = sum of step_finish costs of the LAST
(completing) session only, i.e. the final distinct sessionID in the
cell's jsonl."""
import json
import os

LAB = "/media/sf_Projects/fcdd_lab/case04_coq_rust"


def last_session_cost(path):
    last_sid = None
    cost = 0.0
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        sid = ev.get("sessionID")
        if sid:
            if last_sid is None or sid != last_sid:
                last_sid = sid
                cost = 0.0
        if ev.get("type") == "step_finish":
            part = ev.get("part", {})
            if part.get("sessionID") == last_sid and \
                    isinstance(part.get("cost"), (int, float)):
                cost += part["cost"]
    return cost


def main():
    sched = json.load(open(os.path.join(LAB, "ledger", "schedule.json")))
    runs = []
    for c in sched["cells"]:
        tag = c["tag"]
        scored = json.load(open(os.path.join(LAB, "ledger", "scored",
                                             "%s.json" % tag)))
        cost = last_session_cost(os.path.join(LAB, "ledger", "raw",
                                              "%s.jsonl" % tag))
        runs.append({
            "tag": tag,
            "arm": c["arm"],
            "model": c["model"],
            "mu2": scored["primary"]["mu2"],
            "mu1": scored["rules"]["mu1"],
            "cost_usd": round(cost, 4),
            "completion": True,
        })
    out = os.path.join(LAB, "ledger", "runs.json")
    json.dump(runs, open(out, "w"), indent=1)
    print("wrote %s (%d runs)" % (out, len(runs)))
    for r in runs:
        print("%-8s arm%s mu2=%.4f mu1=%.4f cost=$%.3f"
              % (r["tag"], r["arm"], r["mu2"], r["mu1"], r["cost_usd"]))


if __name__ == "__main__":
    main()
