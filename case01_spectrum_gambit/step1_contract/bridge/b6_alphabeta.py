#!/usr/bin/env python3
"""
BRIDGE layer 6 — ALPHA-BETA == MINIMAX (clause S4), widened.

The Lean kernel proves the equivalence exhaustively for all 3^4 = 81 complete
binary trees of depth 2 with leaf scores in {-1,0,1} (`T21`).  This layer
widens the same statement in the twin:

  * ALL 3^8 = 6561 complete binary trees of depth 3
  * 20,000 pseudo-random trees with branching 1..4, depth 1..4 and scores
    in -400..400 (a realistic centipawn range)

and pins the two NON-claims the contract deliberately makes:

  N1  a NARROW window does NOT return the minimax value (fail-soft bounds),
      which is why the engine's aspiration window / TT / null move / LMR /
      reverse futility layers are NOT claimed to preserve minimax;
  N2  alpha-beta visits strictly fewer leaves than minimax on some tree —
      i.e. the pruning is real, so N1 is not vacuous.
"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "twin"))

from hc91_twin import GTree, minimax, alphaBeta, INF              # noqa: F403

FAILS = []
LEAF = [-1, 0, 1]


def build(code, depth):
    if depth == 0:
        return GTree(LEAF[code % 3], [])
    half = 3 ** (2 ** (depth - 1))
    return GTree(0, [build(code % half, depth - 1), build(code // half, depth - 1)])


# --- exhaustive depth 3 ---------------------------------------------------
bad = [c for c in range(6561)
       if alphaBeta(build(c, 3), 3, -INF, INF) != minimax(build(c, 3), 3)]
if bad:
    FAILS.append("full-window mismatch at depth-3 codes %r" % bad[:5])

vals = {minimax(build(c, 3), 3) for c in range(6561)}
if len(vals) < 2:
    FAILS.append("depth-3 family is vacuous: every tree scores %r" % vals)

# --- randomised, realistic score range ------------------------------------
rnd = random.Random(20260729)


def rnd_tree(depth):
    if depth == 0:
        return GTree(rnd.randrange(-400, 401), [])
    return GTree(rnd.randrange(-400, 401),
                 [rnd_tree(depth - 1) for _ in range(rnd.randint(1, 4))])


NR = 20000
rbad = 0
for _ in range(NR):
    d = rnd.randint(1, 4)
    t = rnd_tree(d)
    if alphaBeta(t, d, -INF, INF) != minimax(t, d):
        rbad += 1
if rbad:
    FAILS.append("%d/%d random trees disagree under a FULL window" % (rbad, NR))

# --- N1: a narrow window is NOT the minimax value -------------------------
narrow = [c for c in range(6561)
          if alphaBeta(build(c, 3), 3, 0, 1) != minimax(build(c, 3), 3)]
if not narrow:
    FAILS.append("N1 vacuous: no narrow-window divergence found — the "
                 "contract's non-claim about aspiration/TT would be unmotivated")

# --- N2: the pruning is real ---------------------------------------------
LEAVES = [0]


def counting_ab(t, d, a, b):
    if d == 0 or not t.cs:
        LEAVES[0] += 1
        return t.v
    best = -INF
    for c in t.cs:
        s = -counting_ab(c, d - 1, -b, -a)
        best = max(best, s)
        a = max(a, best)
        if a >= b:
            return best
    return best


def counting_mm(t, d):
    if d == 0 or not t.cs:
        LEAVES[0] += 1
        return t.v
    return max(-counting_mm(c, d - 1) for c in t.cs)


pruned = 0
for c in range(6561):
    t = build(c, 3)
    LEAVES[0] = 0
    counting_ab(t, 3, -INF, INF)
    nab = LEAVES[0]
    LEAVES[0] = 0
    counting_mm(t, 3)
    if nab < LEAVES[0]:
        pruned += 1
if pruned == 0:
    FAILS.append("N2: alpha-beta never pruned — the reference is not alpha-beta")

print("[b6_alphabeta] 6561 exhaustive depth-3 trees + %d random trees agree with "
      "minimax under a full window; %d/6561 diverge under a narrow window; "
      "alpha-beta prunes on %d/6561; %d failures"
      % (NR, len(narrow), pruned, len(FAILS)))
for f in FAILS:
    print("  FAIL " + f)
sys.exit(1 if FAILS else 0)
