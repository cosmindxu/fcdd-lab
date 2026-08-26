#!/usr/bin/env python3
"""Case 04 — review round 1 evidence emitter (C10). Reproduces the
findings' numbers from the deposited artifacts:

  F1  the shared symlink and its creator (first ln -sfn seen per cell)
  F2  per-cell content-reads of sealed source + direct hc91emu runs
  F3  exact code matches between engine.inc and armB_s2's eval.rs
  F4  pairwise choose-identity clusters on a 60-position sample

Output is appended to ledger/review_evidence.txt."""
import glob
import hashlib
import json
import os
import random
import re
import subprocess

LAB = "/media/sf_Projects/fcdd_lab/case04_coq_rust"
RAW = os.path.join(LAB, "ledger", "raw")
BASE = os.path.expanduser("~/fcdd_c04_scored")
CASE01 = os.path.join(os.path.dirname(LAB), "case01_spectrum_gambit")
PRISTINE = os.path.join(CASE01, "sealed", "seedkit", "pristine")

BINS = {
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

READ_PAT = re.compile(
    r"(cat|sed|head|tail|cp|grep|diff|md5sum)\s+[^\n]*"
    r"(chess\.asm|engine\.inc|pieces\.inc|movegen\.inc|perft\.inc|tt\.inc"
    r"|zobrist\.inc|chess\.tap|chess\.bin|seedkit|bookgen\.py)")
EMU_PAT = re.compile(r"hc91emu(?!\.)")


def tool_commands(tag):
    out = []
    path = os.path.join(RAW, "%s.jsonl" % tag)
    if not os.path.isfile(path):
        return out
    for line in open(path, errors="replace"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        p = d.get("part", {})
        if d.get("type") != "tool_use":
            continue
        inp = p.get("state", {}).get("input", {})
        cmd = inp.get("command") or ""
        if cmd:
            out.append(cmd)
    return out


def main():
    lines = ["# review_evidence — emitted %s" % __import__("time").ctime()]

    # F1: symlink creator
    lines.append("\n## F1 symlink creation")
    for tag in ["armA_r1", "armA_r2", "armA_r3", "armA_r4", "armA_r5",
                "armB_r1", "armB_r2", "armB_r3", "armB_r4", "armB_r5",
                "armB_s1", "armB_s2", "armB_s3"]:
        for cmd in tool_commands(tag):
            if "ln -s" in cmd and "case01_spectrum_gambit" in cmd:
                lines.append("- %s: %s" % (tag, cmd[:140]))
                break

    # F2: per-cell reads
    lines.append("\n## F2 per-cell source content-reads / direct emulator runs")
    for tag in BINS:
        reads = emu = 0
        for cmd in tool_commands(tag):
            if READ_PAT.search(cmd):
                reads += 1
            if EMU_PAT.search(cmd) and "harness" in cmd:
                emu += 1
        lines.append("- %-8s content-reads=%2d  direct-hc91emu=%2d" % (tag, reads, emu))

    # F3: code matches engine.inc vs armB_s2 eval.rs
    lines.append("\n## F3 engine.inc vs armB_s2 eval.rs")
    inc = open(os.path.join(PRISTINE, "engine.inc")).read()
    s2eval = open(os.path.join(BASE, "armB_s2_build", "armB", "skeleton",
                               "src", "eval.rs")).read()
    for probe in ["0,100,320,330,500,900,0",
                  "5, 10, 10,-20,-20, 10, 10,  5"]:
        in_inc = probe.replace(" ", "") in inc.replace(" ", "")
        s2 = probe.replace(" ", "") in s2eval.replace(" ", "")
        lines.append("- '%s': in engine.inc=%s, in s2 eval.rs=%s" % (probe, in_inc, s2))

    # F4: pairwise choose identity on 60-sample
    lines.append("\n## F4 pairwise choose identity (60 positions, seed 20260807)")
    sealed = json.load(open(os.path.join(LAB, "ledger", "sealed", "answers.json")))
    random.seed(20260807)
    sample = random.sample(sealed["policy"], 60)
    moves = {}
    for tag, rel in BINS.items():
        binp = os.path.join(BASE, rel)
        ms = []
        for p in sample:
            r = subprocess.run([binp, "choose", "--fen", p["fen"]],
                               capture_output=True, text=True, timeout=60)
            ms.append(r.stdout.strip().lower())
        moves[tag] = ms
    for a in BINS:
        for b in BINS:
            if a >= b:
                continue
            ag = sum(1 for x, y in zip(moves[a], moves[b]) if x == y)
            if ag >= 55:
                lines.append("- %s==%s: %d/60" % (a, b, ag))

    # F5-degenerate: choose == first legal move frequency
    lines.append("\n## F5-degenerate choose==firstLegal /60")
    for tag, rel in BINS.items():
        binp = os.path.join(BASE, rel)
        n = agree = 0
        for p in sample:
            leg = subprocess.run([binp, "legal", "--fen", p["fen"]],
                                 capture_output=True, text=True, timeout=60)
            ch = subprocess.run([binp, "choose", "--fen", p["fen"]],
                                capture_output=True, text=True, timeout=60)
            lm = [x.strip().lower() for x in leg.stdout.splitlines()
                  if len(x.strip()) in (4, 5)]
            if lm and ch.stdout.strip().lower() == lm[0]:
                n += 1
            if ch.stdout.strip().lower() == p["move"]:
                agree += 1
        lines.append("- %-8s firstLegal=%d/60 engineAgree=%d/60" % (tag, n, agree))

    out = "\n".join(lines) + "\n"
    with open(os.path.join(LAB, "ledger", "review_evidence.txt"), "a") as f:
        f.write(out)
    print(out)


if __name__ == "__main__":
    main()
