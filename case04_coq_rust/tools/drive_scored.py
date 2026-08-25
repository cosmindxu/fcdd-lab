#!/usr/bin/env python3
"""Case 04 — scored-phase driver. Launches schedule cells as systemd
units, at most --jobs cells concurrently. Waits for all to settle, then
prints the drive.log summary. Freeze prerequisite: the sealed answers
must exist (checking here is the driver's own gate)."""
import argparse
import json
import os
import subprocess
import sys
import time

LAB = "/media/sf_Projects/fcdd_lab/case04_coq_rust"
RAW = os.path.join(LAB, "ledger", "raw")
BASE = os.path.expanduser("~/fcdd_c04_scored")
SEALED = os.path.join(LAB, "ledger", "sealed", "answers.json")
CELL_SH = os.path.join(LAB, "tools", "cell_unit.sh")


def unit_name(tag):
    return "c04-cell-%s" % tag.replace("_", "-")


def launch(cell):
    tag = cell["tag"]
    ws = os.path.join(BASE, tag)
    subprocess.run([sys.executable, os.path.join(LAB, "tools",
                                                 "build_workspace.py"),
                    ws, "--ledger", os.path.join(LAB, "ledger")],
                   capture_output=True)
    out = os.path.join(RAW, "%s.jsonl" % tag)
    cmd = ["systemd-run", "--user", "--unit", unit_name(tag), "--collect",
           "bash", CELL_SH, tag, cell["model"], ws, out]
    subprocess.run(cmd, capture_output=True)


def active(tag):
    r = subprocess.run(["systemctl", "--user", "is-active", unit_name(tag)],
                       capture_output=True, text=True)
    return r.stdout.strip() == "active"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("schedule")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args(argv)

    if not os.path.isfile(SEALED):
        print("GATE: sealed answers.json does not exist — refusing to run "
              "the scored schedule against an unsealed corpus.")
        return 2

    sched = json.load(open(args.schedule))
    cells = sched["cells"]
    print("cells: %d, jobs: %d%s" % (len(cells), args.jobs,
                                     " (DRY)" if args.dry else ""))
    idx = 0
    while idx < len(cells) or any(active(c["tag"]) for c in cells):
        running = [c for c in cells if active(c["tag"])]
        while idx < len(cells) and len(running) < args.jobs:
            c = cells[idx]
            if args.dry:
                subprocess.run(["bash", CELL_SH, c["tag"], c["model"],
                                os.path.join(BASE, c["tag"]),
                                os.path.join(RAW, "%s.jsonl" % c["tag"]),
                                "--dry"])
            else:
                launch(c)
            idx += 1
            running = [c for c in cells if active(c["tag"])]
        time.sleep(60)
    print("all cells settled; drive.log tail:")
    with open(os.path.join(RAW, "drive.log")) as f:
        print("".join(f.readlines()[-20:]))


if __name__ == "__main__":
    main()
