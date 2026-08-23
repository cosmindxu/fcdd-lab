#!/usr/bin/env python3
"""Case02 §5 secondary H2 — minimal vs redesign, classified mechanically.

PREREGISTRATION §5: "each fix classified mechanically as *minimal* or
*redesign* by binary diff against pristine (zero marginal cost, no judgement).
Reported as a 2x2 with an exact Fisher test."

§5 fixes the METHOD (binary diff vs pristine) but not a threshold, so the
literal reading is implemented as PRIMARY and two judgement-free variants are
reported alongside it as labelled sensitivities. No LLM classifies anything
here: that is the point of "no judgement".

  PRIMARY (literal)  minimal  <=> all seven program source files are
                                  byte-identical to pristine.
  S1 (comment-blind) minimal  <=> identical after dropping blank lines and
                                  whole-line ';' assembly comments.
  S2 (seeded-line)   minimal  <=> the only non-comment lines differing from
                                  pristine are the seeded fault's own line
                                  (from the sealed answer key).

Fisher's exact test is computed exactly from hypergeometric point
probabilities; runs are the unit, as §5 specifies.
"""
import json, math, os, sys
from difflib import SequenceMatcher
from collections import Counter

LAB = "/media/sf_Projects/fcdd_lab"
PRIS = os.path.join(LAB, "case01_spectrum_gambit/sealed/seedkit/pristine")
KEY = json.load(open(os.path.join(LAB, "case01_spectrum_gambit/sealed/answer_key.json")))
WORK = os.path.expanduser("~/fcdd_arms")
SRC = ["chess.asm", "movegen.inc", "engine.inc", "perft.inc", "tt.inc", "zobrist.inc", "pieces.inc"]
BUGS = ["bug%02d" % i for i in range(1, 8)]
SEED = {b["id"]: b for b in KEY["bugs"]}

def lines(p):
    try: return open(p, encoding="utf-8", errors="replace").read().splitlines()
    except FileNotFoundError: return None

def strip_comments(ls):
    """Drop blank lines and whole-line ';' comments. Purely lexical."""
    out = []
    for l in ls:
        s = l.strip()
        if not s or s.startswith(";"): continue
        out.append(s)
    return out

def classify(ws, bug):
    """Return (primary, s1, s2) each in {'minimal','redesign'}, plus detail."""
    vd = os.path.join(ws, "variants", bug)
    k = SEED[bug]; seeded_file = k["file"]
    # The seeded line as it reads in PRISTINE: the '-' side of the key's own hunk
    # ('+' is the injected fault). A minimal fix touches this line and nothing else.
    pris_line = None
    for dl in k["diff"].splitlines():
        if dl.startswith("-") and not dl.startswith("---"):
            pris_line = dl[1:].strip(); break
    assert pris_line, "no pristine line recoverable from the key hunk for " + bug

    exact_same = True; nocomment_same = True; missing = []
    off_seed_edits = 0     # non-comment edit hunks NOT confined to the seeded line
    n_hunks = 0
    for f in SRC:
        a, b = lines(os.path.join(PRIS, f)), lines(os.path.join(vd, f))
        if b is None:
            missing.append(f); exact_same = nocomment_same = False; off_seed_edits += 1; continue
        if a != b: exact_same = False
        sa, sb = strip_comments(a), strip_comments(b)
        if sa == sb: continue
        nocomment_same = False
        # Align the two non-comment line sequences. EVERY non-equal opcode counts,
        # so insertions are caught as well as deletions -- the previous version
        # only looked for pristine lines that had gone missing.
        for tag, i1, i2, j1, j2 in SequenceMatcher(None, sa, sb, autojunk=False).get_opcodes():
            if tag == "equal": continue
            n_hunks += 1
            confined = (f == seeded_file and tag == "replace"
                        and (i2 - i1) == 1 and (j2 - j1) == 1
                        and sa[i1] == pris_line)
            if not confined: off_seed_edits += 1
    s2_minimal = (off_seed_edits == 0)
    return (("minimal" if exact_same else "redesign"),
            ("minimal" if nocomment_same else "redesign"),
            ("minimal" if s2_minimal else "redesign"),
            dict(missing=missing, hunks=n_hunks, off_seed=off_seed_edits))

def fisher_exact_2x2(a, b, c, d):
    """Two-sided Fisher exact p by summing tables no more probable than observed."""
    n = a + b + c + d
    r1, r2, c1 = a + b, c + d, a + c
    def prob(x):
        y, z, w = r1 - x, c1 - x, r2 - (c1 - x)
        if min(y, z, w) < 0: return 0.0
        return (math.comb(r1, x) * math.comb(r2, z)) / math.comb(n, c1)
    p0 = prob(a)
    return min(1.0, sum(prob(x) for x in range(0, min(r1, c1) + 1) if prob(x) <= p0 + 1e-12))

if __name__ == "__main__":
    rows = []
    for bug in BUGS:
        for arm in "AB":
            for k in (1, 2, 3, 4):
                ws = os.path.join(WORK, "%s_arm%s_c2r%d" % (bug, arm, k))
                if not os.path.isdir(ws): print("MISSING WORKSPACE", ws); continue
                p, s1, s2, det = classify(ws, bug)
                rows.append((bug, arm, k, p, s1, s2, det))
    print("runs classified: %d / 56\n" % len(rows))

    for label, idx in (("PRIMARY (literal byte-identity)", 3),
                       ("S1 (comment/whitespace-blind)", 4),
                       ("S2 (seeded line only)", 5)):
        A = Counter(r[idx] for r in rows if r[1] == "A")
        B = Counter(r[idx] for r in rows if r[1] == "B")
        a, b = A["minimal"], A["redesign"]
        c, d = B["minimal"], B["redesign"]
        p = fisher_exact_2x2(a, b, c, d)
        print("%s" % label)
        print("            minimal  redesign")
        print("  arm A     %7d  %8d" % (a, b))
        print("  arm B     %7d  %8d" % (c, d))
        print("  Fisher exact two-sided p = %.4f\n" % p)

    print("--- per-defect breakdown (S2), for the record ---")
    print("%-7s %-28s %s" % ("defect", "armA (r1..r4)", "armB (r1..r4)"))
    for bug in BUGS:
        ga = [r[5][0] for r in rows if r[0] == bug and r[1] == "A"]
        gb = [r[5][0] for r in rows if r[0] == bug and r[1] == "B"]
        print("%-7s %-28s %s" % (bug, " ".join(ga), " ".join(gb)))
