#!/usr/bin/env python3
"""Did a cell actually RUN its review/attack round?

A9/A10 bound how long review may iterate, but nothing verified it happened at
Reviewer effort varies enormously between cells that all "passed": bug01/A ran
1 reviewer, bug07/A 2, bug07/B 5, bug05/B 8, bug02/A 14. Cost per cell is
therefore substantially a function of HOW MUCH REVIEW HAPPENED, not of the
method alone — which is exactly what prompt v4's bounded termination rule is
meant to equalise. Cells still in flight legitimately show 0.

This checks each cell's own transcript for reviewer subagent invocations, which
is the only evidence the arm cannot self-report away.

NOTE: the subagent tool is named "Agent" in these transcripts (an earlier
version of this script grepped for "Task" and reported a false zero for every
cell — verify the detector before trusting a null result).

Usage: python3 tools/verify_review.py [v3|v4|all]
Exit 1 if any completed cell reviewed zero times.
"""
import glob
import json
import os
import re
import sys

PROJ = os.path.expanduser("~/.claude/projects")


def rounds_for(ws_slug):
    """(task_invocations, transcript_count) for a workspace slug."""
    d = os.path.join(PROJ, "-home-xcos-fcdd-arms-" + ws_slug)
    files = glob.glob(os.path.join(d, "*.jsonl"))
    n = 0
    for f in files:
        try:
            with open(f, errors="replace") as fh:
                for line in fh:
                    n += line.count('"name":"Agent"') + line.count('"name":"Task"')
        except OSError:
            pass
    return n, len(files)


def main():
    want = (sys.argv[1] if len(sys.argv) > 1 else "all").lower()
    rows, bad = [], 0
    for ws in sorted(glob.glob(os.path.expanduser("~/fcdd_arms/bug*_arm*_v[34]"))):
        base = os.path.basename(ws)
        m = re.match(r"(bug\d\d)_arm([AB])_(v[34])$", base)
        if not m:
            continue
        bug, arm, ver = m.groups()
        if want not in ("all", ver):
            continue
        slug = base.replace("_", "-")
        n, tcount = rounds_for(slug)
        fix = os.path.join(ws, "FIX_NOTES.md")
        placeholder = False
        if os.path.exists(fix):
            txt = open(fix, errors="replace").read()
            placeholder = "filled in after the review" in txt
        status = "OK" if n > 0 else "NO-REVIEW"
        if n == 0:
            bad += 1
        rows.append((f"arm{arm}", bug, ver, n, tcount,
                     "placeholder" if placeholder else "", status))

    w = "{:<5} {:<7} {:<4} {:>9} {:>6}  {:<12} {}"
    print(w.format("arm", "bug", "ver", "reviewers", "trans", "fixnotes", "verdict"))
    for r in rows:
        print(w.format(*r))
    if bad:
        print(f"\n{bad} cell(s) completed WITHOUT spawning a reviewer — their cost is "
              f"fix-only and NOT comparable with reviewed cells.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
