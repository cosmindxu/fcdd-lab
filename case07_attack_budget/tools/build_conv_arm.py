#!/usr/bin/env python3
"""Build the CONV arm's skill pack from the BUDGET (current) skill.

The delta is derived from the frozen->current DIFF, not from grep: the pattern
`law 12` misses "laws 3 and 12" and "12 was bought by measurement", both real
sites (method/ATTACK_BUDGET_DIAGNOSIS.md, rollout note). Every hunk of that diff
is classified below, so the site list is exhaustive by construction.

CONV = current skill with the law-12 stopping-rule complex reverted, and
NOTHING else changed. Everything the current skill gained that is not the
stopping rule (the §0 narrowing objective, laws 13/14 and their Beat-1 sites,
the FCDD-T/X variant block, #16.5's turnstile) is KEPT in both arms — reverting
any of it would add an undeclared second treatment.
"""
import os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, "..", ".."))
CUR = os.path.join(LAB, "skills", "formal-contract-dev-current")
FRZ = os.path.join(LAB, "skills", "formal-contract-dev")
OUT = os.path.abspath(os.path.join(HERE, "..", "arms"))

# hunk classification of diff(frozen, current) — see PREREGISTRATION §3
CLASSIFY = {
    1: ("REVERT-PARTIAL", "frontmatter: the declared-budget clause only"),
    2: ("KEEP", "§0 narrowing objective (law 14) — not the stopping rule"),
    3: ("KEEP", "Beat 1 entry obligation (law 13)"),
    4: ("KEEP", "Beat 1 input totality (law 14)"),
    5: ("KEEP", "FCDD-T / FCDD-X variant block"),
    6: ("REVERT", "Beat 4 title"),
    7: ("REVERT", "#15.5 — the declared-budget rule"),
    8: ("KEEP", "#16.5 solver/reviewer turnstile — postdates frozen, NOT the stopping rule"),
    9: ("REVERT-PARTIAL", "§4 laws header: the law-12 evidence clause only"),
    10: ("REVERT-PARTIAL", "laws block: law 12 out; laws 13/14 stay, their law-12 refs neutralised"),
    11: ("KEEP", "§5 'what IS owned' (law 13)"),
}

EDITS = [
    # (description, needle, replacement) — applied to the CURRENT text
    ("frontmatter budget clause -> convergence",
     "against a DECLARED BUDGET — coverage is the stop condition, not convergence",
     "iterate per-surface to convergence"),
    ("Beat 4 title",
     "### Beat 4 — ATTACK: adversarial review against a declared budget",
     "### Beat 4 — ATTACK: adversarial review to convergence"),
    ("laws header: drop law-12 evidence clause",
     "; **12 was bought by measurement, not incident** — case02, 56 runs", ""),
    ("law 13 ref: laws 3 and 12 -> law 3",
     "which laws 3 and 12 both forbid", "which law 3 forbids"),
    ("#16 back-reference to the removed #15.5 block",
     "**re-review the fixes** (a focused pass,\n    inside the declared budget of #15.5).",
     "**re-review the fixes** (a focused pass)."),
    ("law 13 ref: law 12's 56 runs -> generic",
     "weaker evidence\n    than law 12's 56 runs, and it should be cited that way",
     "weaker evidence\n    than a 56-run measurement, and it should be cited that way"),
]


def cut_block(text, start_marker, end_marker, what):
    i = text.index(start_marker)
    j = text.index(end_marker, i)
    return text[:i] + text[j:]


def main():
    cur = open(os.path.join(CUR, "SKILL.md")).read()
    frz = open(os.path.join(FRZ, "SKILL.md")).read()
    conv = cur
    applied = []

    for what, needle, repl in EDITS:
        if needle not in conv:
            sys.exit("FAIL: site not found -> %s" % what)
        conv = conv.replace(needle, repl, 1)
        applied.append(what)

    # #15.5 block: from its number to the next numbered item (16.)
    conv = cut_block(conv, "15.5 **DECLARE THE ATTACK BUDGET", "\n16. **Ground-truth", "#15.5")
    applied.append("#15.5 block removed")

    # law 12 block: from its number to law 13's number
    conv = cut_block(conv, "12. **No unbounded loop in the method.", "\n13. **Every clause declares", "law 12")
    applied.append("law 12 removed")

    # Beat 4 #16: restore the frozen convergence criterion verbatim
    m_cur = re.search(r"\*\*The criterion is #15\.5's.*?quoted separately\.", conv, re.S)
    m_frz = re.search(r"So the criterion is: within an.*?evidence the surface grew\.", frz, re.S)
    if not (m_cur and m_frz):
        sys.exit("FAIL: #16 criterion block not locatable")
    conv = conv[:m_cur.start()] + m_frz.group(0) + conv[m_cur.end():]
    applied.append("#16 criterion restored to frozen text")

    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, "SKILL_CONV.md"), "w").write(conv)
    # the CONV reference pack keeps the frozen convergence block
    open(os.path.join(OUT, "lenses_CONV.md"), "w").write(open(os.path.join(FRZ, "references", "lenses.md")).read())

    d = subprocess.run(["diff", "-u", os.path.join(OUT, "SKILL_CONV.md"), os.path.join(CUR, "SKILL.md")],
                       capture_output=True, text=True).stdout
    open(os.path.join(OUT, "DELTA.diff"), "w").write(d)

    print("CONV pack built. Edits applied:")
    for a in applied:
        print("  -", a)
    print("\nresidual stopping-rule language in CONV (must be convergence-only):")
    for ln, t in enumerate(conv.split("\n"), 1):
        if re.search(r"declared budget|law 12|stop on coverage", t, re.I):
            print("  ! line %d: %s" % (ln, t.strip()[:88]))
    print("\ndelta vs BUDGET: %d added / %d removed lines"
          % (sum(1 for l in d.split("\n") if l.startswith("+") and not l.startswith("+++")),
             sum(1 for l in d.split("\n") if l.startswith("-") and not l.startswith("---"))))


if __name__ == "__main__":
    main()
