#!/usr/bin/env python3
"""Case02 §5 quality — blinded grading packets, with case01 §4.5's defects fixed.

§4.5 found case01's blinding did not occur: signature terms ran 0 (ordinary) vs
37 (FCDD) in one packet, so "every grader could identify the treatment with
certainty", and the rubric's test-quality axis "mechanically rewards shipping
more verification material — which is FCDD's definition".

Scrubbing harder cannot fix that. The artefact CATEGORY is the label: all 28
arm B workspaces carry a contract/ package (spec + twin + bridge + smt); no arm
A workspace does, its tests being loose scripts inside variants/. No vocabulary
substitution hides a Lean specification.

So this builder grades THE SOURCE REPAIR ONLY — the diff to the seven engine
sources — where both arms emit the same kind of object and blinding is
achievable. Verification packages are excluded from the blinded tier entirely,
and the test-quality axis is dropped with them. What is lost is reported, not
hidden: see AMENDMENTS A10.

Carried forward from case01, which had to learn each the hard way:
  * diff against the SEEDED tree, never pristine (a correct minimal repair
    restores pristine, so a pristine diff shows the fix as empty);
  * scrub absolute paths FIRST, since they embed arm names;
  * keys are written separately and never shown to graders.

Counterbalancing is deterministic and balanced WITHIN every defect: run indices
1,3 present arm A as Submission X; 2,4 present arm B as X. So each defect
contributes two packets each way and order cannot align with arm.

Usage: python3 tools/make_packets_case02.py
"""
import json, os, re, subprocess

C2   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASE1= os.path.join(os.path.dirname(C2), "case01_spectrum_gambit")
WORK = os.path.expanduser("~/fcdd_arms")
SEEDED = os.path.join(CASE1, "arms", "variants")
OUT  = os.path.join(C2, "grading")
SRC  = ["chess.asm", "movegen.inc", "engine.inc", "tt.inc", "zobrist.inc", "perft.inc", "pieces.inc"]
BUGS = ["bug%02d" % i for i in range(1, 8)]

SCRUB = [
    (r"/home/[A-Za-z0-9_]+/fcdd_arms/[A-Za-z0-9_]+", "SUBMISSION"),
    (r"[A-Za-z0-9_./-]*step1_contract", "BASELINE"),
    (r"[A-Za-z0-9_./-]*fcdd_lab[A-Za-z0-9_./-]*", "PROJECT"),
    (r"(?i)fcdd_arms", "workspace"),
    (r"(?i)\bbug\d\d_arm[AB]_c2r\d\b", "SUBMISSION"),
    (r"(?i)\barm ?[AB]\b", "the submission"),
    (r"(?i)\bformal[- ]contract[- ]driven development\b", "the development method"),
    (r"(?i)\bFCDD\b", "the method"),
    (r"(?i)\bformal-contract-dev\b", "the method"),
    # Replacement vocabulary is deliberately ARM-NEUTRAL. The first build used
    # "specification"/"a specification rule", which are themselves signature
    # terms: scrubbing INTRODUCED the tell it was removing, and the collision of
    # two rules produced the visibly-censored phrase "specification a
    # specification rule". Both arms could plausibly cite a design note.
    (r"(?i)\bContract\.lean\b", "the design note"),
    (r"(?i)\bcontract/(spec|twin|bridge|smt)/[A-Za-z0-9_./]*", "the design note"),
    (r"(?i)\b(clause|contract|spec|specification) ?[CS]\d+\b", "the design note"),
    (r"(?i)\bC\d+_[a-zA-Z_]+", "the design note"),
    (r"(?i)\bkernel-checked\b", "reviewed"),
    (r"(?i)\bmachine-checked\b", "reviewed"),
    (r"(?i)\bLean ?4?\b", "the design note"),
    (r"(?i)\bspec of record\b", "the design note"),
    (r"(?i)\bconformance suite\b", "the check suite"),
    (r"(?i)\bconformance\b", "check"),
    (r"(?i)\bthe contract\b", "the design note"),
    (r"(?i)\bcontracts?\b", "design note"),
    (r"(?i)\bspecifications?\b", "design note"),
    (r"(?i)\btwin\b", "reference build"),
    (r"(?i)\bbridge layer\b", "check"),
    (r"(?i)\bb\d_[a-z_]+\.py\b", "a check script"),
    (r"(?i)\battack round\b", "review round"),
    (r"(?i)\badversarial review(er)?\b", "review"),
]
# Collapse artefacts left by overlapping rules. A visibly mangled phrase is
# itself a tell -- it says "this text was censored", which only the treated arm
# would trigger.
COLLAPSE = [
    (r"(?i)\b(the |a )?design note(,? )?(the |a )?design note\b", "the design note"),
    (r"(?i)\bdesign note rule\b", "design note"),
    (r"(?i)\b(the design note){2,}", "the design note"),
    (r"\s{2,}(?=[.,;)])", " "),
]
def scrub(t):
    for pat, rep in SCRUB: t = re.sub(pat, rep, t)
    for pat, rep in COLLAPSE: t = re.sub(pat, rep, t)
    return t

def source_diff(ws, bug):
    """Unified diff of the engine sources vs the SEEDED tree the arm received."""
    out = []
    src = os.path.join(ws, "variants", bug)
    for f in SRC:
        a, b = os.path.join(SEEDED, bug, f), os.path.join(src, f)
        if not (os.path.exists(a) and os.path.exists(b)): continue
        d = subprocess.run(["diff", "-u", "--label", "a/"+f, "--label", "b/"+f, a, b],
                           capture_output=True, text=True).stdout
        if d.strip(): out.append(d)
    return "\n".join(out) or "(no changes to the engine sources)"

RUBRIC = """## How to judge

Score each submission 1-5 on each axis, then say which you would merge.

- **correctness_risk** (1 = high risk it is wrong or incomplete, 5 = clearly
  correct and complete for the reported defect). Does the change actually
  address the reported behaviour? Could it break something else?
- **minimality** (1 = sprawling, changes far more than the defect requires,
  5 = tightly scoped to the fault). A larger change is not automatically
  worse -- judge whether the extra scope is warranted.
- **clarity** (1 = opaque, 5 = a reviewer can see why it is right).

Judge ONLY the assembly source changes shown. Both submissions were produced
under time and tooling conditions you are not told about. Do not speculate
about who wrote them or by what process; if you find yourself forming a theory
about the authors, say so in `blinding_note` and score the code regardless.
"""

def main():
    os.makedirs(OUT, exist_ok=True); made = 0
    for bug in BUGS:
        for k in (1, 2, 3, 4):
            wsA = os.path.join(WORK, "%s_armA_c2r%d" % (bug, k))
            wsB = os.path.join(WORK, "%s_armB_c2r%d" % (bug, k))
            if not (os.path.isdir(wsA) and os.path.isdir(wsB)):
                print("SKIP %s r%d (missing workspace)" % (bug, k)); continue
            first, second = ("A", "B") if k in (1, 3) else ("B", "A")
            ws = {"A": wsA, "B": wsB}
            pid = "%s_r%d" % (bug, k)
            packet = [
                "# Blind review packet — %s" % pid, "",
                "Two independent submissions repaired the SAME reported defect in the",
                "same Z80 assembly codebase. You are not told who wrote them or by what",
                "process. Judge only the source changes shown below.", "",
                RUBRIC, "",
                "## The reported defect", "",
                scrub(open(os.path.join(CASE1, "bug_reports", bug + ".md"), errors="replace").read()),
                "",
            ]
            for label, arm in (("X", first), ("Y", second)):
                packet += ["## Submission %s — source changes" % label, "",
                           "```diff", scrub(source_diff(ws[arm], bug)), "```", ""]
            open(os.path.join(OUT, "PACKET_%s.md" % pid), "w").write("\n".join(packet))
            json.dump({"pair": pid, "bug": bug, "run": k, "X": first, "Y": second},
                      open(os.path.join(OUT, "KEY_%s.json" % pid), "w"))
            made += 1
    print("%d packets in %s" % (made, OUT))
    print("KEY_*.json must NOT be shown to graders.")

if __name__ == "__main__":
    main()
