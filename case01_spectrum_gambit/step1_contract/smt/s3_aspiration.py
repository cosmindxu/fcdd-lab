#!/usr/bin/env python3
"""
SMT tier — FINDING F4: the aspiration window is DEAD CODE.

`aiMove` (engine.inc:2118-2177) narrows the root window to
[lastScore-40, lastScore+40] for every iterative-deepening iteration >= 2,
then decides whether to re-search with a full window by reading alpha/beta
back OUT OF THE PER-PLY ARRAYS after the search:

    call negamax                  ; HL = score, and negamax has MUTATED
    ld (lastScore),hl             ; alphaArr[0] along the way
    ...
    call ptrAlpha                 ; BC = alphaArr[0]  <-- the MUTATED alpha
    ld de,(lastScore)
    call cmpDEgtBC                ; score > alpha ?
    jr nc,aspWiden                ; no -> widen and search AGAIN

The root node raises alphaArr[0] to the best score whenever it improves
(`nmTryA`), so at exit alpha >= score on every path that reaches the move
loop; and the three early-exit paths return a value that is >= beta > alpha,
which fails the SECOND test instead.  Either way `aspWiden` is taken.

Consequence: every iterative-deepening iteration from depth 2 upwards runs
the search TWICE, and the aspiration window never prunes anything.  It is a
performance defect, not a correctness one — and, as documented in
../organic_findings.md, it also MASKS a latent root hazard (a root-level
reverse-futility or null-move cutoff would otherwise return without ever
setting `bestFrom`).

Below, the four exit paths of `negamax` at searchPly 0 are modelled and z3 is
asked to find ANY execution in which the aspiration re-search is skipped.
UNSAT = the window is unconditionally dead.

SOLVER TIER: z3 only (see D-SMT-1).  The model is an EXTRACTION of the
control flow by hand — that extraction is the assumption this proof rests on;
the code excerpts it was taken from are quoted in organic_findings.md F4.
"""
import sys

sys.path.insert(0, "/home/xcos/.venvs/quant/lib/python3.14/site-packages")
import z3                                                        # noqa: E402

FAILS = []
INF, ASPW = 30000, 40

lastScore, best, evalv, margin = z3.Ints("lastScore best eval margin")
a0, b0 = z3.Ints("alpha0 beta0")

base = [
    lastScore >= -29000, lastScore <= 29000,
    a0 == lastScore - ASPW,                 # aspGo: alpha = lastScore - W
    b0 == lastScore + ASPW,                 # beta  = lastScore + W
    best >= -INF, best <= INF,
]

# The four ways negamax can return at searchPly 0, as (score, alphaAtExit):
#   P_loop  — the move loop ran; alphaArr[0] = max(a0, best)   (nmTryA)
#   P_rfut  — reverse futility fired: score = eval, eval-margin >= beta, alpha
#             untouched                                       (engine.inc:1078)
#   P_null  — null move fired: score = beta, alpha untouched   (engine.inc:1153)
# The no-legal-move exit is handled separately below (it is unreachable).
def widened(score, alpha, beta):
    """aiMove's decision: TRUE when the full-window re-search is performed."""
    inside = z3.And(score > alpha, beta > score)
    return z3.Not(inside)


CASES = {
    "loop":  (best, z3.If(best > a0, best, a0), b0, []),
    "rfut":  (evalv, a0, b0, [margin >= 110, margin <= 220,
                              evalv - margin >= b0,
                              evalv >= -13000, evalv <= 13000]),
    "null":  (b0, a0, b0, []),
}

# The FOURTH exit (`nmDone` with legalArr == 0: the root has no legal move) is
# deliberately NOT in CASES.  z3 confirms it CAN keep the narrow window — and
# it is unreachable from `aiMove`, because `updateTerminal` (movegen.inc:1172)
# sets gameState != 0 in exactly that situation and `mainLoop` then never
# calls aiMove at all.  Recording it explicitly rather than quietly dropping it.
_s = z3.Solver()
_mate = z3.Int("mateScore")
_s.add(base + [z3.Or(_mate == 0, _mate == -29000)])
_s.add(z3.Not(widened(_mate, a0, b0)))
NOMOVE_KEEPS = (_s.check() == z3.sat)
if not NOMOVE_KEEPS:
    FAILS.append("the no-legal-move exit was expected to be able to keep the "
                 "window; the model may be wrong")

for name, (score, alpha, beta, extra) in CASES.items():
    s = z3.Solver()
    s.add(base + extra)
    s.add(z3.Not(widened(score, alpha, beta)))       # try to SKIP the re-search
    r = s.check()
    if r != z3.unsat:
        FAILS.append("path %s can keep the narrow window: %s" % (name, s.model()))

# Non-vacuity: a HYPOTHETICAL engine that saved the original alpha (as
# `origAlphaArr` already does per ply!) WOULD sometimes keep the window.  If
# even that is UNSAT, the model is broken rather than the engine.
s = z3.Solver()
s.add(base)
s.add(z3.Not(widened(best, a0, b0)))                 # alpha = the ORIGINAL alpha
if s.check() != z3.sat:
    FAILS.append("non-vacuity: even with the original alpha the window is dead — "
                 "the model does not distinguish the two engines")

print("[s3_aspiration] z3: all %d REACHABLE root exit paths of negamax force the "
      "aspiration re-search (UNSAT of 'window kept'); the unreachable "
      "no-legal-move exit %s keep it (excluded with its reachability argument); "
      "a variant reading the ORIGINAL alpha does not widen (SAT), so the result "
      "is not vacuous. %d failures"
      % (len(CASES), "CAN" if NOMOVE_KEEPS else "cannot", len(FAILS)))
for f in FAILS:
    print("  FAIL " + f)
sys.exit(1 if FAILS else 0)
