#!/usr/bin/env python3
"""Build BLINDED grading packets — gate item 3 of the frozen protocol.

For each bug with two completed v4 cells, writes a packet containing both
arms' work with every arm-identifying marker removed, presented as
"Submission X" and "Submission Y". Which arm is X alternates by bug parity
(even bug number -> X=A, odd -> X=B) so a grader cannot learn the mapping
from one packet and apply it to the next.

Blinding is the load-bearing part, so it is deliberately aggressive: file
names, contract paths, FCDD vocabulary and skill references are the obvious
tells. Anything not scrubbable is dropped rather than shipped.

The true mapping is written to grading/KEY_<bug>.json, which the grader agents
never see; the orchestrator only reads it after verdicts are in.

Usage: python3 tools/make_grading_packets.py
"""
import glob
import json
import os
import re
import shutil
import subprocess

CASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.expanduser("~/fcdd_arms")
PRISTINE = os.path.join(CASE, "sealed", "seedkit", "pristine")
OUT = os.path.join(CASE, "grading")

SRC = ["chess.asm", "movegen.inc", "engine.inc", "tt.inc",
       "zobrist.inc", "perft.inc"]

# Tells that would identify the FCDD arm. Order matters (longest first).
SCRUB = [
    (r"(?i)\bformal[- ]contract[- ]driven development\b", "the development method"),
    (r"(?i)\bFCDD\b", "the method"),
    (r"(?i)\bformal-contract-dev\b", "the method"),
    (r"(?i)\bContract\.lean\b", "the specification"),
    (r"(?i)\bcontract/spec/[A-Za-z0-9_./]*", "the specification"),
    (r"(?i)\bcontract/twin/[A-Za-z0-9_./]*", "the reference implementation"),
    (r"(?i)\bcontract/bridge/[A-Za-z0-9_./]*", "the conformance suite"),
    (r"(?i)\bcontract/smt/[A-Za-z0-9_./]*", "the solver checks"),
    (r"(?i)\battack round\b", "review round"),
    (r"(?i)\badversarial review(er)?\b", "review"),
    (r"(?i)\bbeat [0-9.]+\b", "stage"),
    (r"(?i)\bkernel-checked\b", "machine-checked"),
    (r"(?i)\bLean 4?\b", "the specification language"),
    (r"(?i)\bclause C[0-9]+\b", "a specification clause"),
    (r"(?i)\btwin\b", "reference implementation"),
    (r"(?i)\bbridge layer\b", "conformance check"),
    (r"(?i)\barm ?[AB]\b", "the submission"),
]


def scrub(text):
    for pat, rep in SCRUB:
        text = re.sub(pat, rep, text)
    return text


def diff_for(ws, bug):
    """Unified diff of the engine sources against pristine."""
    out = []
    src = os.path.join(ws, "variants", bug)
    for f in SRC:
        a, b = os.path.join(PRISTINE, f), os.path.join(src, f)
        if not (os.path.exists(a) and os.path.exists(b)):
            continue
        d = subprocess.run(["diff", "-u", "--label", f"a/{f}", "--label", f"b/{f}", a, b],
                           capture_output=True, text=True).stdout
        if d.strip():
            out.append(d)
    return "\n".join(out) or "(no changes to the engine sources)"


def tests_for(ws, bug):
    """Any test files the submission added, listed and inlined (truncated)."""
    src = os.path.join(ws, "variants", bug)
    base = {f for f in os.listdir(PRISTINE)}
    parts = []
    for f in sorted(os.listdir(src)):
        if f in base or not re.search(r"(test|check).*\.(py|sh|mjs)$", f, re.I):
            continue
        p = os.path.join(src, f)
        try:
            body = open(p, errors="replace").read()
        except OSError:
            continue
        parts.append(f"--- {f} ({len(body)} bytes) ---\n{body[:12000]}")
    return "\n\n".join(parts) or "(no new test files)"


def main():
    os.makedirs(OUT, exist_ok=True)
    made = 0
    for n in range(1, 8):
        bug = f"bug{n:02d}"
        wsA = os.path.join(WORK, f"{bug}_armA_v4")
        wsB = os.path.join(WORK, f"{bug}_armB_v4")
        if not (os.path.isdir(wsA) and os.path.isdir(wsB)):
            continue
        # only grade cells that COMPLETED — an in-flight workspace holds a
        # partial fix and would be judged as if it were the arm's final answer
        done = True
        for arm in ("A", "B"):
            res = glob.glob(os.path.join(CASE, "ledger", "raw",
                                         f"arm{arm}_{bug}_v4_a*_result.json"))
            ok = False
            for r in res:
                try:
                    ok = ok or not json.load(open(r)).get("is_error")
                except Exception:
                    pass
            done = done and ok
        if not done:
            print(f"{bug}: SKIPPED — a cell is still in flight")
            continue
        # alternate which arm is presented first, by bug parity
        first, second = ("A", "B") if n % 2 == 0 else ("B", "A")
        ws = {"A": wsA, "B": wsB}
        packet = [
            f"# Blind review packet — {bug}",
            "",
            "Two independent submissions fixed the SAME reported defect in the same",
            "Z80 codebase. You are not told who wrote them or by what process, and",
            "the two are not necessarily comparable in style. Judge only what is here.",
            "",
            "## The reported defect", "",
            scrub(open(os.path.join(CASE, "bug_reports", f"{bug}.md"),
                       errors="replace").read()),
            "",
        ]
        for label, arm in (("X", first), ("Y", second)):
            packet += [
                f"## Submission {label} — source changes", "",
                "```diff", scrub(diff_for(ws[arm], bug)), "```", "",
                f"## Submission {label} — tests added", "",
                "```", scrub(tests_for(ws[arm], bug))[:14000], "```", "",
            ]
        open(os.path.join(OUT, f"PACKET_{bug}.md"), "w").write("\n".join(packet))
        json.dump({"bug": bug, "X": first, "Y": second},
                  open(os.path.join(OUT, f"KEY_{bug}.json"), "w"))
        made += 1
        print(f"{bug}: packet written (X={first}, Y={second}) — key sealed")
    print(f"\n{made} packet(s) in {OUT}")
    print("KEY_*.json must NOT be shown to graders.")


if __name__ == "__main__":
    main()
