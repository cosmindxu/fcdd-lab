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
SEEDED = os.path.join(CASE, "arms", "variants")   # the buggy tree each arm received
STEP1 = os.path.join(CASE, "step1_contract")      # Arm B's contract baseline
OUT = os.path.join(CASE, "grading")

SRC = ["chess.asm", "movegen.inc", "engine.inc", "tt.inc",
       "zobrist.inc", "perft.inc"]

# Tells that would identify the FCDD arm. Order matters (longest first).
SCRUB = [
    # PATH scrubs MUST come first: diff -ru embeds absolute paths that name the
    # arm ("bug02_armB_v4"), the lab ("fcdd_arms") and the baseline. Adding the
    # verification-package diff without these leaked the mapping outright.
    (r"/home/[A-Za-z0-9_]+/fcdd_arms/bug\d\d_arm[AB]_v\d+", "SUBMISSION"),
    (r"[A-Za-z0-9_./-]*step1_contract", "BASELINE"),
    (r"[A-Za-z0-9_./-]*fcdd_lab[A-Za-z0-9_./-]*", "PROJECT"),
    (r"(?i)fcdd_arms", "workspace"),
    (r"(?i)\bbug\d\d_arm[AB]_v\d+\b", "SUBMISSION"),
    (r"(?i)\barm[AB]\b", "the submission"),
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
    # leaks found in the first build: "contract C9", bare "contract", "clause",
    # "spec of record", "conformance", file names under contract/
    (r"(?i)\bcontract\s+C\d+\b", "a specification rule"),
    (r"(?i)\bclause\s+C\d+\b", "a specification rule"),
    (r"(?i)\bC\d+_[a-zA-Z_]+", "a specification rule"),
    (r"(?i)\bspec of record\b", "the specification"),
    (r"(?i)\bconformance suite\b", "the check suite"),
    (r"(?i)\bthe contract\b", "the specification"),
    (r"(?i)\bcontract\b", "specification"),
    (r"(?i)\bcontracted\b", "specified"),
    (r"(?i)contract[_-][a-z_]+", "spec_identifier"),
    (r"(?i)[a-z_]+[_-]contract\b", "spec_identifier"),
    (r"(?i)\bcontracts\b", "specifies"),
    (r"(?i)\bhc91_twin\b", "reference implementation"),
    (r"(?i)\bb\d_[a-z_]+\.py\b", "a check script"),
]


def scrub(text):
    for pat, rep in SCRUB:
        text = re.sub(pat, rep, text)
    return text


def diff_for(ws, bug):
    """Unified diff of the engine sources against the SEEDED tree the arm was given.

    Baseline correctness matters: diffing against `pristine` shows the fix as
    EMPTY (a correct minimal fix restores pristine exactly), which is how the
    first packet build presented every submission as comment-only changes.
    """
    out = []
    src = os.path.join(ws, "variants", bug)
    for f in SRC:
        a, b = os.path.join(SEEDED, bug, f), os.path.join(src, f)
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
    # Verification artifacts also live OUTSIDE variants/ for some submissions
    # (a conformance/spec package). Omitting them scored one submission as
    # having shipped no tests at all, which was false and arm-specific.
    ext = os.path.join(ws, "contract")
    if os.path.isdir(ext):
        d = subprocess.run(["diff", "-ru", "-x", "*.olean", "-x", "__pycache__",
                            "-x", "*.png", "-x", "*.sna", "-x", "*.tap",
                            STEP1, ext], capture_output=True, text=True).stdout
        if d.strip():
            parts.append("--- changes to the accompanying verification package "
                         f"({len(d)} bytes of diff) ---\n" + d[:20000])
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
        ws = {"A": wsA, "B": wsB}
        for order_tag, (first, second) in (("XA", ("A", "B")), ("XB", ("B", "A"))):
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
            open(os.path.join(OUT, f"PACKET_{bug}_{order_tag}.md"), "w").write("\n".join(packet))
            json.dump({"bug": bug, "order": order_tag, "X": first, "Y": second},
                      open(os.path.join(OUT, f"KEY_{bug}_{order_tag}.json"), "w"))
            made += 1
            print(f"{bug} [{order_tag}]: packet written (X={first}, Y={second})")
    print(f"\n{made} packet(s) in {OUT}")
    print("KEY_*.json must NOT be shown to graders.")


if __name__ == "__main__":
    main()
