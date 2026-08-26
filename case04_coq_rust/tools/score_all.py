#!/usr/bin/env python3
"""Case 04 — run the scorer on all 13 scheduled cells' binaries in
parallel (one process per cell), writing ledger/scored/<tag>.json."""
import json
import os
import subprocess
import sys
import time

LAB = "/media/sf_Projects/fcdd_lab/case04_coq_rust"
SCORED = os.path.join(LAB, "ledger", "scored")
SEALED = os.path.join(LAB, "ledger", "sealed", "answers.json")
BASE = os.path.expanduser("~/fcdd_c04_scored")

BINARIES = {
    "armA_r1": "armA_r1_build/armA/target/release/chess_clone",
    "armA_r2": "armA_r2_build/armA/target/release/chess_clone",
    "armA_r3": "armA_r3_build/armA/target/release/chess_clone",
    "armA_r4": "armA_r4_build/armA/skeleton/target/release/chess_clone",
    "armA_r5": "armA_r5_build/armA/target/release/chess_clone",
    "armB_r1": "armB_r1_build/armB/skeleton/target/release/chess_clone",
    "armB_r2": "armB_r2_build/armB/skeleton/target/release/chess_clone",
    "armB_r3": "armB_r3_build/armB/skeleton/target/debug/chess_clone",
    "armB_r4": "armB_r4_build/armB/target/release/chess_clone",
    "armB_r5": "armB_r5_build/armB/target/release/chess_clone",
    "armB_s1": "armB_s1_build/armB/target/release/chess_clone",
    "armB_s2": "armB_s2_build/armB/skeleton/target/debug/chess_clone",
    "armB_s3": "armB_s3_build/armB/target/release/chess_clone",
}


def main():
    os.makedirs(SCORED, exist_ok=True)
    procs = {}
    for tag, rel in BINARIES.items():
        binary = os.path.join(BASE, rel)
        if not os.path.isfile(binary):
            print("MISSING BINARY: %s (%s)" % (tag, binary), flush=True)
            continue
        out = os.path.join(SCORED, "%s.json" % tag)
        procs[tag] = (subprocess.Popen(
            [sys.executable, os.path.join(LAB, "tools", "score_case04.py"),
             "--binary", binary, "--sealed", SEALED, "--out", out],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True),
            out)
    print("launched %d scorers" % len(procs), flush=True)
    done = set()
    while len(done) < len(procs):
        for tag, (p, out) in list(procs.items()):
            if tag in done:
                continue
            rc = p.poll()
            if rc is not None:
                done.add(tag)
                print("%s DONE rc=%d -> %s" % (tag, rc, out), flush=True)
            elif os.path.isfile(out):
                try:
                    r = json.load(open(out))
                    print("PROGRESS %s mu2=%s rules_mu1=%s"
                          % (tag, r["primary"]["mu2"],
                             r["rules"]["mu1"]), flush=True)
                except (ValueError, KeyError):
                    pass
        time.sleep(30)
    print("all scorers done", flush=True)


if __name__ == "__main__":
    main()
