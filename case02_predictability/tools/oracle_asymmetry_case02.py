#!/usr/bin/env python3
"""A17 — what each arm was actually SHIPPED, and whether it contained the answer.

The design's central control was to spend case01's oracle confound symmetrically:
Arm B holds a pristine-derived contract, so Arm A is given a pristine-derived
characterisation suite. This checks what the workspace builder actually copied.
"""
import hashlib, os, re, subprocess
LAB  = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SEAL = os.path.join(LAB, "case01_spectrum_gambit", "sealed", "seedkit", "pristine")
WORK = os.path.expanduser("~/fcdd_arms")
BUGS = ["bug%02d" % i for i in range(1, 8)]
sha  = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()

ptap = sha(os.path.join(SEAL, "chess.tap"))
print("sealed pristine chess.tap sha256 : %s\n" % ptap)

for arm in "AB":
    shipped = used = diffed = 0
    for bug in BUGS:
        for k in (1, 2, 3, 4):
            ws = os.path.join(WORK, "%s_arm%s_c2r%d" % (bug, arm, k))
            if not os.path.isdir(ws): continue
            # INPUTS only: anything outside variants/, which holds the arm's own output
            hit = False
            for root, _, files in os.walk(ws):
                if "/variants/" in root + "/": continue
                for f in files:
                    if f.endswith((".tap", ".sna")):
                        try:
                            if sha(os.path.join(root, f)) == ptap: hit = True
                        except OSError: pass
            shipped += hit
            fn = os.path.join(ws, "FIX_NOTES.md")
            if os.path.exists(fn):
                t = open(fn, errors="replace").read()
                if "artifacts/" in t: used += 1
                if re.search(r"cmp -l|differ in exactly|byte offset|file offset", t): diffed += 1
    print("arm %s: shipped the pristine binary as an INPUT in %2d/28 workspaces" % (arm, shipped))
    print("        FIX_NOTES referencing the shipped artefacts : %2d/28" % used)
    print("        FIX_NOTES recording a byte-level comparison : %2d/28" % diffed)

print("\nWhat Arm B's package contains beyond spec/twin/bridge/smt:")
d = os.path.join(LAB, "case01_spectrum_gambit", "step1_contract", "artifacts")
for f in sorted(os.listdir(d)):
    p = os.path.join(d, f)
    mark = "  <-- BIT-IDENTICAL TO SEALED PRISTINE" if os.path.isfile(p) and sha(p) == ptap else ""
    print("  %-18s %8d bytes%s" % (f, os.path.getsize(p), mark))
