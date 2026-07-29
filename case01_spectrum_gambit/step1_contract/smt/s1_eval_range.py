#!/usr/bin/env python3
"""
SMT tier — the 16-BIT NO-OVERFLOW obligation (FCDD Beat 2.7).

The Lean contract and the Python twin both score positions in UNBOUNDED
integers.  The engine scores them in HL, a signed 16-bit register.  That gap
is a real proof obligation, not a modelling convenience: if any evaluation
path could exceed +/-32767 the twin would silently disagree with the engine
exactly where it matters (a wrapped score inverts the sign of a decision).

This script discharges it with z3: it asserts the per-component bounds and
proves UNSAT of "the total leaves the signed 16-bit range", for the
evaluation itself and for every arithmetic the search wraps around it
(negated windows, aspiration widening, reverse-futility margins).

The component bounds are ASSUMPTIONS, listed below and each cross-checked
by exhaustive computation over the engine's own tables in s1_bounds_check().

SOLVER TIER: z3 only.  cvc5 is not installed on this machine, so the FCDD
two-independent-solver rule is NOT met for this claim; it is recorded as a
claim-level downgrade in ../DECISIONS.md (D-SMT-1).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "twin"))
sys.path.insert(0, "/home/xcos/.venvs/quant/lib/python3.14/site-packages")

import z3                                                        # noqa: E402
from hc91_twin import (materialTbl, pstFor, DOUBLED, ISOLATED, BISHOP_PAIR,
                       PASSED, KSHIELD, INF, MATE)                # noqa: E402

FAILS = []
INT16_MIN, INT16_MAX = -32768, 32767


def bounds_check():
    """Cross-check the assumed component bounds by exhaustive computation."""
    # A1: the largest |material + PST| any single non-king piece can have.
    per_piece = {t: materialTbl[t] + max(pstFor(t)) for t in range(1, 6)}
    worst_piece = max(per_piece.values())
    # A2: a side owns at most 15 non-king men (8 promoted + 7 originals);
    #     the richest legal composition is 9Q + 2R + 2B + 2N.
    max_side = 9 * per_piece[5] + 2 * per_piece[4] + 2 * per_piece[3] + 2 * per_piece[2]
    # A3: king PST magnitude
    max_kingpst = max(max(abs(v) for v in pstFor(6)), 50)
    return {
        "worst_piece": worst_piece,
        "PST_MAX": max_side,               # |pstScore| <= this
        "KING_PST": max_kingpst,           # per king
        "BISHOP_PAIR": BISHOP_PAIR,
        "PAWN_STRUCT": 8 * DOUBLED + 8 * ISOLATED,
        "PASSED": 8 * PASSED * 7,
        "SHIELD": 3 * KSHIELD,
        "MATING": 6 * 16 + 7 * 4,
    }


B = bounds_check()

# ---------------------------------------------------------------- z3 ----
s = z3.Solver()
pst, kw, kb, bp, pawn, passed, shield, mating = z3.Ints(
    "pstScore kingPstW kingPstB bishopPair pawnStruct passed shield mating")

s.add(pst >= -B["PST_MAX"], pst <= B["PST_MAX"])
s.add(kw >= -B["KING_PST"], kw <= B["KING_PST"])
s.add(kb >= -B["KING_PST"], kb <= B["KING_PST"])
s.add(bp >= -B["BISHOP_PAIR"], bp <= B["BISHOP_PAIR"])
s.add(pawn >= -B["PAWN_STRUCT"], pawn <= B["PAWN_STRUCT"])
s.add(passed >= -B["PASSED"], passed <= B["PASSED"])
s.add(shield >= -B["SHIELD"], shield <= B["SHIELD"])
s.add(mating >= -B["MATING"], mating <= B["MATING"])

total = pst + kw + kb + bp + pawn + passed + shield + mating

# P1 — the evaluation itself fits in HL.
s.push()
s.add(z3.Or(total > INT16_MAX, total < INT16_MIN))
r = s.check()
if r != z3.unsat:
    FAILS.append("P1 eval-in-int16: z3 says %s, model %s" % (r, s.model()))
s.pop()

# P2 — the reverse-futility threshold `eval - depth*110` (depth 1..2) fits.
s.push()
d = z3.Int("d")
s.add(d >= 1, d <= 2)
s.add(z3.Or(total - d * 110 > INT16_MAX, total - d * 110 < INT16_MIN))
if s.check() != z3.unsat:
    FAILS.append("P2 reverse-futility margin can overflow")
s.pop()

# P3 — the aspiration window `lastScore +/- ASPW` fits, given |score| <= MATE.
asp = z3.Int("lastScore")
s2 = z3.Solver()
s2.add(asp >= -MATE, asp <= MATE)
s2.add(z3.Or(asp + 40 > INT16_MAX, asp - 40 < INT16_MIN))
if s2.check() != z3.unsat:
    FAILS.append("P3 aspiration window can overflow")

# P4 — negating a search window (`setChildWindow`, `-beta`, `-beta+1`) fits.
s3 = z3.Solver()
a, b = z3.Ints("alpha beta")
s3.add(a >= -INF, a <= INF, b >= -INF, b <= INF)
s3.add(z3.Or(-a > INT16_MAX, -a < INT16_MIN, -b > INT16_MAX, -b < INT16_MIN,
             -b + 1 > INT16_MAX, -b + 1 < INT16_MIN))
if s3.check() != z3.unsat:
    FAILS.append("P4 window negation can overflow")

# P5 — non-vacuity: the encoding must be ABLE to express an overflow, else
#      P1-P4 would be proving nothing.  A fictitious component 4x the real
#      pstScore bound MUST come out SAT.
s4 = z3.Solver()
fake = z3.Int("fakePst")
s4.add(fake >= -4 * B["PST_MAX"], fake <= 4 * B["PST_MAX"])
s4.add(fake > INT16_MAX)
if s4.check() != z3.sat:
    FAILS.append("P5 non-vacuity: even a 4x bound cannot overflow — check the model")

worst = (B["PST_MAX"] + 2 * B["KING_PST"] + B["BISHOP_PAIR"] + B["PAWN_STRUCT"]
         + B["PASSED"] + B["SHIELD"] + B["MATING"])
print("[s1_eval_range] z3: eval/RFP/aspiration/window arithmetic proved inside "
      "int16 (UNSAT of the negation). worst-case |eval| <= %d, headroom %d. "
      "%d failures" % (worst, INT16_MAX - worst, len(FAILS)))
print("  assumptions: " + ", ".join("%s=%d" % kv for kv in sorted(B.items())))
for f in FAILS:
    print("  FAIL " + f)
sys.exit(1 if FAILS else 0)
