#!/usr/bin/env python3
"""
BRIDGE layer 2 — MUTATION COVERAGE (DeMillo-Lipton-Sayward).

Part A — OBSERVATION mutations.  Single-field edits of a conforming
observation must trip EXACTLY the expected clause set.  The expected sets
below are the OBSERVED, ground-truthed ones, not guesses; the interesting
ones are annotated with WHY the neighbouring clauses do or do not fire.

  Note on C11: `C11_terminal` RECOMPUTES `updateTerminal(post, hist)` from
  the mutated post, so mutating the post cannot trip it — only mutating the
  reported `state` can.  That is a real clause-independence fact, recorded
  here rather than papered over.

  Note on C4: `C4_unmakeInverts` is computed entirely from `pre` and `mv`,
  so NO observation mutation can falsify it.  It is an internal-consistency
  clause (FCDD falsifiability tier 4) whose only negative test is an
  IMPLEMENTATION mutation — Part B.

Part B — IMPLEMENTATION mutations.  Seeded single-line faults in the twin
must be caught by the bridge's own checks.  A fault that survives every
layer is a coverage hole, and fails this script.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "twin"))

import hc91_twin as T
from hc91_twin import *                                          # noqa: F403
from positions import *                                          # noqa: F403

h0 = History([7], 7)
# KB vs KB: exactly TWO minors, so the engine's `minors < 2` boundary and a
# mutated `<= 2` disagree.  Needed to give B4 anything to bite on.
twoMinorPos = Position(mkBoard([(0x00, WK), (0x77, BK), (0x33, WB), (0x35, BB)]),
                       WHITE, 0, 0xFF, 3, 0x00, 0x77, 60)
# A BLACK promotion — needed so that "drop the colour bit" is observable
# (for a white promotion `orB(0, promo) == promo`, so the fault is a no-op).
bPromoPos = mirrorPos(promoPos)
base = obsOf(startPos, mkMove(0x14, 0x34, SP_DPUSH), h0)
FAILS, COVERED = [], set()
NMUT = 0

assert failedClauses(base) == [], "baseline must conform"


def mut(name, obs, expect_names):
    global NMUT
    NMUT += 1
    got = set(failedClauseNames(obs))
    want = set(expect_names)
    COVERED.update(want)
    if got != want:
        FAILS.append("A/%-28s tripped %s, expected %s"
                     % (name, sorted(got) or ["NOTHING"], sorted(want)))


# ------------------------------------------------- Part A: observations ---

# C1 — a shape no piece can produce (a pawn "sliding" e2->e7).  C8 also
# fires because the post still carries the double-push e.p. target while the
# substituted move is not a double push; C12 because e7 held a black pawn.
mut("C1/illegal-shape",
    base.replace(mv=mkMove(0x14, 0x64, 0)),
    ["C1_pseudoLegal", "C2_legal", "C3_makeAgrees", "C8_epDiscipline",
     "C12_pieceCount"])

# C2 + C6 — pseudo-legal but leaves the mover's own king in check.  The
# CLEAN pair: nothing else fires.
mut("C2+C6/self-check",
    obsOf(pinPos, mkMove(0x14, 0x35, 0), h0),
    ["C2_legal", "C6_kingSafe"])

# C3 + C10 — post-position tampered in a field make() owns.
mut("C3+C10/tampered-wking",
    base.replace(post=base.post.replace(wking=0x00)),
    ["C3_makeAgrees", "C10_kingSquares"])

# C5 — the side to move did not alternate.
mut("C5/stuck-side",
    base.replace(post=base.post.replace(stm=WHITE)),
    ["C3_makeAgrees", "C5_sideAlternates"])

# C7 — castling rights INVENTED (bitwise non-monotone).
mut("C7/invented-rights",
    base.replace(post=base.post.replace(castling=0xFF)),
    ["C3_makeAgrees", "C7_rightsMonotone"])

# C8 — e.p. target dropped after a double push.
mut("C8/lost-ep-target",
    base.replace(post=base.post.replace(ep=0xFF)),
    ["C3_makeAgrees", "C8_epDiscipline"])

# C8 — e.p. target invented after a quiet move.
_quiet = obsOf(startPos, mkMove(0x06, 0x25, 0), h0)
mut("C8/invented-ep-target",
    _quiet.replace(post=_quiet.post.replace(ep=0x34)),
    ["C3_makeAgrees", "C8_epDiscipline"])

# C9 — the fifty-move clock not reset by a pawn move.
mut("C9/clock-not-reset",
    base.replace(post=base.post.replace(halfmove=1)),
    ["C3_makeAgrees", "C9_halfmove"])

# C10 + C12 + C13 — a king vanished from the board.
mut("C10+C13/king-vanished",
    base.replace(post=base.post.replace(board=bSet(base.post.board, 0x74, 0))),
    ["C3_makeAgrees", "C10_kingSquares", "C12_pieceCount", "C13_kingsUnique"])

# C11 — the terminal verdict misreported (the ONLY way to trip C11).
mut("C11/wrong-verdict", base.replace(state=DRAW), ["C11_terminal"])
mut("C11/mate-called-play",
    Obs(startPos, mkMove(0x14, 0x34, SP_DPUSH), matePos, h0, PLAY),
    ["C3_makeAgrees", "C5_sideAlternates", "C8_epDiscipline", "C11_terminal"])

# C12 — a piece materialised from nowhere.
mut("C12/piece-from-nowhere",
    base.replace(post=base.post.replace(board=bSet(base.post.board, 0x40, WQ))),
    ["C3_makeAgrees", "C12_pieceCount"])

# C13 — a second white king.
mut("C13/two-kings",
    base.replace(post=base.post.replace(board=bSet(base.post.board, 0x40, WK))),
    ["C3_makeAgrees", "C12_pieceCount", "C13_kingsUnique"])

# C14 — promotion produced the WRONG colour.
_pro = obsOf(promoPos, mkMove(0x61, 0x71, 0x50), h0)
mut("C14/promoted-wrong-colour",
    _pro.replace(post=_pro.post.replace(board=bSet(_pro.post.board, 0x71, BQ))),
    ["C3_makeAgrees", "C14_promotion"])

# C14 — promotion produced a KING (type outside 2..5).
mut("C14/promoted-to-king",
    _pro.replace(post=_pro.post.replace(board=bSet(_pro.post.board, 0x71, WK))),
    ["C3_makeAgrees", "C13_kingsUnique", "C14_promotion"])

# ------------------------------------------- Part B: implementation ------

def probe():
    """A compact battery over the whole rules core, called through the MODULE
    object so a seeded fault anywhere in the call graph is visible.  Any
    seeded fault must change this signature (or raise)."""
    sig = []
    sig.append(len(T.genLegal(startPos)))
    sig.append(T.perft(startPos, 3))
    sig.append(T.perft(kiwiPos, 2))
    sig.append(T.perft(epPos, 3))                      # e.p. exercised in depth
    sig.append(T.perft(castlePos, 3))                  # rights changes exercised
    sig.append(T.perft(promoPos, 2))                   # promotions exercised
    sig.append(T.updateTerminal(matePos, h0))
    sig.append(T.updateTerminal(stalematePos, h0))
    sig.append(T.updateTerminal(insufficientPos, h0))
    sig.append(T.updateTerminal(twoMinorPos, h0))      # the <2 / <=2 boundary
    sig.append(T.updateTerminal(fiftyPos, h0))
    sig.append(T.updateTerminal(fiftyPos.replace(halfmove=99), h0))
    sig.append(T.mkMove(0x04, 0x06, T.SP_OO) in T.genLegal(castlePos))
    sig.append(T.mkMove(0x04, 0x06, T.SP_OO) in T.genLegal(castleBlockedPos))
    sig.append(T.mkMove(0x44, 0x53, T.SP_EP) in T.genLegal(epPos))
    # the e.p. capture must remove the pawn on d5 (0x43), not something else
    sig.append(tuple(T.makeMove(epPos, T.mkMove(0x44, 0x53, T.SP_EP)).board))
    # a rook leaving a1 must clear the white queenside right
    sig.append(T.makeMove(castlePos, T.mkMove(0x00, 0x01, 0)).castling)
    # a promotion must place a piece of the MOVER's colour
    sig.append(T.bGet(T.makeMove(promoPos, T.mkMove(0x61, 0x71, 0x50)).board, 0x71))
    sig.append(len([m for m in T.genLegal(promoPos) if T.mvPromo(m) != 0]))
    # ... and a BLACK promotion must keep the colour bit
    sig.append(T.bGet(T.makeMove(bPromoPos, T.mkMove(0x11, 0x01, 0x50)).board, 0x01))
    sig.append(T.perft(bPromoPos, 2))
    sig.append(all(T.unmakeMove(T.makeMove(p, m), T.undoOf(p, m)) == p
                   for p in (startPos, castlePos, promoPos, epPos, kiwiPos)
                   for m in T.genLegal(p)))
    sig.append(T.evalWhite(T.mirrorPos(kiwiPos)) == -T.evalWhite(kiwiPos))
    sig.append(T.evalWhite(kiwiPos))
    sig.append(T.Conforming(T.obsOf(castlePos, T.mkMove(0x04, 0x06, T.SP_OO), h0)))
    return tuple(sig)


GOLDEN = probe()


def seed(name, patch, restore):
    """Apply a one-line fault, assert `probe()` notices, then restore."""
    global NMUT
    NMUT += 1
    patch()
    try:
        caught = probe() != GOLDEN
    except Exception:
        caught = True                      # a crash is a caught fault
    finally:
        restore()
    if probe() != GOLDEN:
        FAILS.append("B/%s: restore FAILED (harness bug)" % name)
    if not caught:
        FAILS.append("B/%-28s SURVIVED every check — coverage hole" % name)


def _swap(obj, attr, value):
    old = getattr(obj, attr)
    return (lambda: setattr(obj, attr, value)), (lambda: setattr(obj, attr, old))


# B1 — a wrong knight offset (classic off-by-one in a direction table).
_bad = list(T.knightDirs); _bad[0] = 0x22
seed("knightDirs[0]=0x22", *_swap(T, "knightDirs", _bad))

# B2 — pawn double-push allowed from any rank.
_orig_gpw = T.genPawnWhite


def _gpw_bad(b, ep, f):
    one = T.addB(f, 16)
    if T.bGet(b, one) != 0:
        pushes = []
    elif T.sqRank(f) == 6:
        pushes = T.addPromos(f, one)
    else:
        pushes = [T.mkMove(f, one, 0)]
        two = T.addB(f, 32)                       # <- rank test removed
        if T.bGet(b, two) == 0:
            pushes = pushes + [T.mkMove(f, two, T.SP_DPUSH)]

    def cap(off):
        t = T.addB(f, off)
        if not T.onBoard(t):
            return []
        occ = T.bGet(b, t)
        if occ == 0:
            return [T.mkMove(f, t, T.SP_EP)] if ep == t else []
        if T.pcCol(occ) == T.WHITE:
            return []
        if T.sqRank(f) == 6:
            return T.addPromos(f, t)
        return [T.mkMove(f, t, 0)]
    return pushes + cap(15) + cap(17)


seed("dpush-from-any-rank", *_swap(T, "genPawnWhite", _gpw_bad))

# B3 — castling no longer checks the transit square for attack.
_orig_gc = T.genCastling


def _gc_bad(p, f):
    b = p.board
    if p.stm == T.WHITE:
        if f != 0x04 or T.isAttacked(b, T.BLACK, 0x04):
            return []
        ks = ([T.mkMove(0x04, 0x06, T.SP_OO)]
              if (T.bit(p.castling, 0) == 1 and T.bGet(b, 0x05) == 0
                  and T.bGet(b, 0x06) == 0) else [])          # <- attack test gone
        qs = ([T.mkMove(0x04, 0x02, T.SP_OOO)]
              if (T.bit(p.castling, 1) == 1 and T.bGet(b, 0x03) == 0
                  and T.bGet(b, 0x02) == 0 and T.bGet(b, 0x01) == 0
                  and not T.isAttacked(b, T.BLACK, 0x03)
                  and not T.isAttacked(b, T.BLACK, 0x02)) else [])
        return ks + qs
    return _orig_gc(p, f)


seed("castle-through-check-ok", *_swap(T, "genCastling", _gc_bad))

# B4 — insufficient-material boundary loosened (< 2 becomes <= 2).
_orig_ii = T.isInsufficient


def _ii_bad(b):
    types = [T.pcType(T.bGet(b, s)) for s in T.scanSquares]
    heavy = any(t in (1, 4, 5) for t in types)
    minors = len([t for t in types if t in (2, 3)])
    return (not heavy) and minors <= 2                         # <- boundary flipped


seed("insufficient-<=2", *_swap(T, "isInsufficient", _ii_bad))

# B5 — the fifty-move boundary off by one (>= 100 becomes > 100).
_orig_ut = T.updateTerminal


def _ut_bad(p, h):
    if not T.genLegal(p):
        if T.inCheckSide(p, p.stm):
            return T.WHITE_MATED if p.stm == T.WHITE else T.BLACK_MATED
        return T.STALEMATE
    if T.countReps(h) >= 3:
        return T.DRAW
    if T.isInsufficient(p.board):
        return T.DRAW
    if p.halfmove > 100:                                       # <- was >=
        return T.DRAW
    return T.PLAY


seed("fifty->100-not->=100", *_swap(T, "updateTerminal", _ut_bad))

# B6 — mate and stalemate swapped (the classic check/no-check inversion).
def _ut_bad2(p, h):
    if not T.genLegal(p):
        if not T.inCheckSide(p, p.stm):                        # <- inverted
            return T.WHITE_MATED if p.stm == T.WHITE else T.BLACK_MATED
        return T.STALEMATE
    return _orig_ut(p, h)


seed("mate/stalemate-swapped", *_swap(T, "updateTerminal", _ut_bad2))

# B7 — e.p. capture removes the wrong pawn (dst+16 instead of dst-16).
_orig_cs = T.capSquare


def _cs_bad(p, m):
    if T.mvSpecial(m) == T.SP_EP:
        return T.addB(m.dst, 16)                               # <- colour ignored
    return m.dst


seed("ep-wrong-capture-square", *_swap(T, "capSquare", _cs_bad))

# B8 — promotion places the opponent's piece (colour bit dropped).
_orig_mm = T.makeMove


def _mm_bad(p, m):
    q = _orig_mm(p, m)
    if T.mvPromo(m) != 0:
        q = q.replace(board=T.bSet(q.board, m.dst, T.mvPromo(m)))   # always white
    return q


seed("promo-drops-colour-bit", *_swap(T, "makeMove", _mm_bad))

# B9 — eval loses its colour symmetry (bishop pair scored for both sides).
_orig_ev = T.evalWhite


def _ev_bad(p):
    v = _orig_ev(p)
    if T.countPiece(p.board, T.BB) >= 2:
        v += 2 * T.BISHOP_PAIR                                 # <- sign error
    return v


seed("eval-bishop-pair-sign", *_swap(T, "evalWhite", _ev_bad))

# B10 — castling rights not cleared when a rook leaves its corner.
_orig_cc = T.clrCastleSq
seed("rights-never-cleared", *_swap(T, "clrCastleSq", lambda r, s: r))

# B11 — C4's ONLY possible negative test: break unmake and check that the
# clause itself (not merely the probe signature) goes red.
def _um_bad(p, u):
    q = _orig_um(p, u)
    return q.replace(castling=T.andB(q.castling, 0xF0))   # <- loses white rights


_orig_um = T.unmakeMove
NMUT += 1
COVERED.add("C4_unmakeInverts")
T.unmakeMove = _um_bad
try:
    _o = T.obsOf(castlePos, T.mkMove(0x00, 0x01, 0), h0)
    _got = set(n for i, n in enumerate(clauseNames) if not T.CLAUSES[i](_o))
finally:
    T.unmakeMove = _orig_um
if _got != {"C4_unmakeInverts"}:
    FAILS.append("B/unmake-loses-rights        tripped %s, expected ['C4_unmakeInverts']"
                 % (sorted(_got) or ["NOTHING"]))

missing = [c for c in clauseNames if c not in COVERED]
if missing:
    FAILS.append("clauses with NO negative test: %s" % missing)

print("[b2_mutations] %d mutations (%d observation + %d implementation), "
      "%d/%d clauses negatively tested, %d failures"
      % (NMUT, 16, NMUT - 16, len(COVERED), len(clauseNames), len(FAILS)))
for f in FAILS:
    print("  FAIL " + f)
sys.exit(1 if FAILS else 0)
