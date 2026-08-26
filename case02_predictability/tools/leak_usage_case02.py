#!/usr/bin/env python3
"""Case 02 — did the treated arm USE the answer key it was shipped? (A17)

A17 established that every Arm B workspace contained the pristine binary,
bit-identical to the sealed answer key, and asserted that Arm B localised faults
"by a byte comparison against the answer". It cited no evidence for the usage
half. This script supplies what can be measured.

Scope and limits, stated up front: the only per-run text deposited is the
agent's closing `result` summary, not its full transcript. A run could use `cmp`
without saying so, or name the path incidentally. These counts are therefore a
LOWER BOUND on mention and weak evidence on use. They are reported because
A17's claim currently rests on nothing at all.
"""
import glob, json, os, re

RAW = os.path.join(os.path.dirname(__file__), "..", "..",
                   "case01_spectrum_gambit", "ledger", "raw")
LEAK = re.compile(r"(contract/)?artifacts/[^\s\"']*\.tap", re.I)
CMPISH = re.compile(r"\bcmp\b|\bdiff\b|xxd|hexdump|byte[- ]compar|sha256sum[^\n]*tap", re.I)


def main():
    rows = []
    for f in sorted(glob.glob(os.path.join(RAW, "*result*.json"))):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        r = d.get("result") if isinstance(d, dict) else None
        if not isinstance(r, str):
            continue
        b = os.path.basename(f)
        arm = "B" if "armB" in b else ("A" if "armA" in b else None)
        if not arm:
            continue
        named = bool(LEAK.search(r))
        rows.append((b, arm, named, named and bool(CMPISH.search(r))))

    out = ["CASE 02 — use of the shipped answer key (A17 follow-up)",
           "Lower bound: counts closing summaries only, not full transcripts.\n",
           f"{'arm':<5}{'runs':>6}{'named artifacts/*.tap':>24}{'+ byte-compare verb':>22}",
           "-" * 57]
    for arm in ("A", "B"):
        sub = [x for x in rows if x[1] == arm]
        out.append(f"{arm:<5}{len(sub):>6}{sum(x[2] for x in sub):>24}{sum(x[3] for x in sub):>22}")
    out.append("\nArm A was never shipped the artefact; its zero is the control.")
    out.append("\nruns naming it:")
    for b, arm, named, c in rows:
        if named:
            out.append(f"  arm{arm}  {b}{'   [byte-compare verb present]' if c else ''}")
    txt = "\n".join(out)
    print(txt)
    open(os.path.join(os.path.dirname(__file__), "..", "ledger",
                      "LEAK_USAGE.txt"), "w").write(txt + "\n")


if __name__ == "__main__":
    main()
