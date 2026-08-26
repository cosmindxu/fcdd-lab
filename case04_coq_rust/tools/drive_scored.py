#!/usr/bin/env python3
"""Case 04 — scored-phase driver. Launches schedule cells as systemd
units, at most --jobs cells concurrently (with a hard cap of 1 armA cell —
Rocq/MetaRocq extraction peaks ~32 GB, so two concurrent armA cells OOM the
61 GB host). A cell is SETTLED iff its last drive.log line is a COMPLETE
verdict; anything else (GAVE UP, a fresh attempt, a silent OOM-kill) leaves
it pending and it is relaunched. This replaces the earlier forward-idx loop,
which silently dropped cells that died without a verdict."""
import argparse
import json
import os
import re
import subprocess
import sys
import time

LAB = "/media/sf_Projects/fcdd_lab/case04_coq_rust"
RAW = os.path.join(LAB, "ledger", "raw")
BASE = os.path.expanduser("~/fcdd_c04_scored")
SEALED = os.path.join(LAB, "ledger", "sealed", "answers.json")
CELL_SH = os.path.join(LAB, "tools", "cell_unit.sh")
TAG_RE = re.compile(r"\b(arm[AB]_(?:r\d+|s\d+))\b")


def unit_name(tag):
    return "c04-cell-%s" % tag.replace("_", "-")


def launch(cell):
    tag = cell["tag"]
    build = os.path.join(BASE, tag + "_build")
    r = subprocess.run([sys.executable, os.path.join(LAB, "tools",
                                                      "build_workspace.py"),
                        build, "--ledger", os.path.join(LAB, "ledger")],
                       capture_output=True, text=True)
    if r.returncode != 0:
        with open(os.path.join(RAW, "drive.log"), "a") as f:
            f.write("%s %s WORKSPACE BUILD FAILED: %s\n"
                    % (time.strftime("%c"), tag, r.stderr[-200:]))
        return False
    arm = "armA" if cell["arm"] == "A" else "armB"
    ws = os.path.join(build, arm)
    out = os.path.join(RAW, "%s.jsonl" % tag)
    cmd = ["systemd-run", "--user", "--unit", unit_name(tag), "--collect",
           "bash", CELL_SH, tag, cell["model"], ws, out]
    subprocess.run(cmd, capture_output=True)
    return True


def active(tag):
    r = subprocess.run(["systemctl", "--user", "is-active", unit_name(tag)],
                       capture_output=True, text=True)
    return r.returncode == 0


def settled_map():
    """tag -> True iff the last drive.log line for that tag is COMPLETE.
    A later 'attempt'/'GAVE UP' line (re-run after infra death / outage)
    flips it back to pending."""
    state = {}
    path = os.path.join(RAW, "drive.log")
    if not os.path.isfile(path):
        return state
    for line in open(path):
        m = TAG_RE.search(line)
        if not m:
            continue
        tag = m.group(1)
        if "COMPLETE" in line or "GAVE UP" in line:
            state[tag] = True
        elif "attempt" in line:
            state[tag] = False
    return state


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("schedule")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--arm-a-jobs", type=int, default=1)
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args(argv)

    if not os.path.isfile(SEALED):
        print("GATE: sealed answers.json does not exist — refusing to run "
              "the scored schedule against an unsealed corpus.")
        return 2

    sched = json.load(open(args.schedule))
    cells = sched["cells"]
    dlog = os.path.join(RAW, "drive.log")
    with open(dlog, "a") as f:
        f.write("%s DRIVER START (jobs=%d, armA_jobs=%d, %s)\n"
                % (time.strftime("%c"), args.jobs, args.arm_a_jobs,
                   "DRY" if args.dry else "real"))

    settled = settled_map()
    settled_tags = {c["tag"] for c in cells if settled.get(c["tag"])}
    print("settled: %d, pending: %d, jobs: %d%s"
          % (len(settled_tags),
             len([c for c in cells if c["tag"] not in settled_tags]),
             args.jobs, " (DRY)" if args.dry else ""))

    while True:
        settled = settled_map()
        running = [c for c in cells if active(c["tag"])]
        running_tags = {c["tag"] for c in running}
        n_armA = sum(1 for c in running if c["arm"] == "A")

        to_launch = []
        for c in cells:
            if c["tag"] in settled_tags or c["tag"] in running_tags:
                continue
            if not settled.get(c["tag"], False):
                if len(running) + len(to_launch) >= args.jobs:
                    continue
                if c["arm"] == "A" and \
                        n_armA + sum(1 for x in to_launch if x["arm"] == "A") \
                        >= args.arm_a_jobs:
                    continue
                to_launch.append(c)

        for c in to_launch:
            if args.dry:
                subprocess.run(["bash", CELL_SH, c["tag"], c["model"],
                                os.path.join(BASE, c["tag"] + "_build",
                                             "armA" if c["arm"] == "A" else "armB"),
                                os.path.join(RAW, "%s.jsonl" % c["tag"]),
                                "--dry"])
            else:
                launch(c)
        if to_launch:
            print("launched: %s" % ", ".join(c["tag"] for c in to_launch),
                  flush=True)

        if all(settled.get(c["tag"]) for c in cells):
            print("all cells settled; drive.log tail:")
            with open(dlog) as f:
                print("".join(f.readlines()[-20:]))
            return 0

        time.sleep(60)


if __name__ == "__main__":
    main()
