"""
HC-91 chess engine — PURE TWIN of the formal contract (FCDD Beat 2).

Clause-for-clause transcription of ../spec/Contract.lean.  Same names, same
boundary operators, same constants.  This module is SIDE-EFFECT FREE: no
I/O, no clock, no randomness.  Everything impure (driving the emulator,
reading .sna dumps) lives in ../bridge/ (the shell).

NUMERIC DOMAIN (FCDD Beat 2.7).  Python ints are bignums, so the twin's
numeric domain strictly CONTAINS the spec's `Nat`/`Int`.  Byte arithmetic
is made explicit with w8() exactly where the Z80 wraps; nothing else may
wrap.  Evaluation scores are exact integers; the engine's 16-bit registers
are a separate proof obligation (see ../smt/eval_range.py).
"""

# ---------------------------------------------------------------- 1. bytes

def w8(n):            # `add a,r`
    return n % 256

def addB(a, b):
    return w8(a + b)

def bitOp(f, a, b, n=8):
    if n == 0:
        return 0
    return (1 if f(a % 2 == 1, b % 2 == 1) else 0) + 2 * bitOp(f, a // 2, b // 2, n - 1)

def andB(a, b):
    return bitOp(lambda x, y: x and y, a, b)

def orB(a, b):
    return bitOp(lambda x, y: x or y, a, b)

def xorB(a, b):
    return bitOp(lambda x, y: x != y, a, b)

def bit(v, i):
    return (v // (2 ** i)) % 2

def negB(n):
    return w8(256 - n % 256)

# -------------------------------------------------------------- 2. squares

def onBoard(s):       # `and 0x88 ; jp nz`
    return bit(s, 3) == 0 and bit(s, 7) == 0

def sqFile(s):
    return s % 8

def sqRank(s):
    return (s // 16) % 8

def sq64(s):
    return sqRank(s) * 8 + sqFile(s)

def mirrorIdx(s):     # == sq64(s) ^ 0x38
    return (7 - sqRank(s)) * 8 + sqFile(s)

# --------------------------------------------------------------- 3. pieces

EMPTY = 0
WP, WN, WB, WR, WQ, WK = 1, 2, 3, 4, 5, 6
BP, BN, BB, BR, BQ, BK = 9, 10, 11, 12, 13, 14
COLBIT, TYPEMASK = 8, 7

def pcType(p):
    return p % 8

def pcCol(p):
    return bit(p, 3) * 8

WHITE, BLACK = 0, 8

def other(c):
    return BLACK if c == WHITE else WHITE

# ----------------------------------------------------------------- 4. move

SP_NONE, SP_DPUSH, SP_OO, SP_OOO, SP_EP = 0, 1, 2, 3, 4


class Move(tuple):
    """(frm, dst, flag) — hashable and comparable, like the Lean structure."""
    __slots__ = ()

    def __new__(cls, frm, dst, flag):
        return super().__new__(cls, (frm, dst, flag))

    frm = property(lambda self: self[0])
    dst = property(lambda self: self[1])
    flag = property(lambda self: self[2])

    def __repr__(self):
        return "%02x-%02x/%02x" % self


def mkMove(f, d, fl):
    return Move(f, d, fl)

def mvSpecial(m):
    return m.flag % 8

def mvPromo(m):
    return m.flag // 16

promoFlags = [0x50, 0x40, 0x30, 0x20]        # Q, R, B, N

# ----------------------------------------------------- 5. direction tables

knightDirs = [0x21, 0x1F, 0x12, 0x0E, 0xDF, 0xE1, 0xEE, 0xF2]
kingDirs   = [0x01, 0x0F, 0x10, 0x11, 0xFF, 0xF1, 0xF0, 0xEF]
bishopDirs = [0x0F, 0x11, 0xF1, 0xEF]
rookDirs   = [0x01, 0x10, 0xFF, 0xF0]

# ------------------------------------------------------------- 6. position

def emptyBoard():
    return [0] * 128

def bGet(b, s):
    return b[s] if 0 <= s < len(b) else 0

def bSet(b, s, v):
    nb = list(b)
    if 0 <= s < len(nb):
        nb[s] = v
    return nb

def mkBoard(pairs):
    b = emptyBoard()
    for sq, pc in pairs:
        b = bSet(b, sq, pc)
    return b


class Position:
    __slots__ = ("board", "stm", "castling", "ep", "halfmove",
                 "wking", "bking", "moveCount")

    def __init__(self, board, stm, castling, ep, halfmove, wking, bking, moveCount):
        self.board, self.stm, self.castling, self.ep = list(board), stm, castling, ep
        self.halfmove, self.wking, self.bking, self.moveCount = halfmove, wking, bking, moveCount

    def key(self):
        return (tuple(self.board), self.stm, self.castling, self.ep,
                self.halfmove, self.wking, self.bking, self.moveCount)

    def __eq__(self, o):
        return isinstance(o, Position) and self.key() == o.key()

    def __hash__(self):
        return hash(self.key())

    def replace(self, **kw):
        d = dict(board=self.board, stm=self.stm, castling=self.castling, ep=self.ep,
                 halfmove=self.halfmove, wking=self.wking, bking=self.bking,
                 moveCount=self.moveCount)
        d.update(kw)
        return Position(**d)

    def __repr__(self):
        return "Position(stm=%d,cast=%X,ep=%02X,hm=%d,wk=%02X,bk=%02X)" % (
            self.stm, self.castling, self.ep, self.halfmove, self.wking, self.bking)


scanSquares = [s for s in range(0x78) if onBoard(s)]

# ----------------------------------------------------------- 7. isAttacked

def scanHop(b, s, dirs, want):
    return any(onBoard(addB(s, d)) and bGet(b, addB(s, d)) == want for d in dirs)

def pawnAt(b, s, off, want):
    t = addB(s, off)
    return onBoard(t) and bGet(b, t) == want

def slideHit(b, s, dirr, w1, w2):
    cur, fuel = s, 8
    while fuel > 0:
        fuel -= 1
        nxt = addB(cur, dirr)
        if not onBoard(nxt):
            return False
        occ = bGet(b, nxt)
        if occ == 0:
            cur = nxt
            continue
        return occ == w1 or occ == w2
    return False

def scanSlide(b, s, dirs, w1, w2):
    return any(slideHit(b, s, d, w1, w2) for d in dirs)

def isAttacked(b, atk, s):
    """Clause R8 — movegen.inc:510."""
    if scanHop(b, s, knightDirs, addB(atk, WN)):
        return True
    if scanHop(b, s, kingDirs, addB(atk, WK)):
        return True
    if atk == WHITE:
        if pawnAt(b, s, negB(15), WP) or pawnAt(b, s, negB(17), WP):
            return True
    else:
        if pawnAt(b, s, 15, BP) or pawnAt(b, s, 17, BP):
            return True
    if scanSlide(b, s, bishopDirs, addB(atk, WB), addB(atk, WQ)):
        return True
    return scanSlide(b, s, rookDirs, addB(atk, WR), addB(atk, WQ))

def inCheckSide(p, side):
    ks = p.wking if side == WHITE else p.bking
    return isAttacked(p.board, other(side), ks)

# -------------------------------------------------------------- 8. movegen

def addPromos(f, d):
    return [mkMove(f, d, fl) for fl in promoFlags]

def genHops(b, stm, f, dirs):
    """Clause R3 — `gmHop`."""
    out = []
    for dirr in dirs:
        t = addB(f, dirr)
        if not onBoard(t):
            continue
        occ = bGet(b, t)
        if occ == 0:
            out.append(mkMove(f, t, 0))
        elif pcCol(occ) == stm:
            continue
        else:
            out.append(mkMove(f, t, 0))
    return out

def genRay(b, stm, f, dirr):
    """Clause R4 — `gmSlide`."""
    out, cur, fuel = [], f, 8
    while fuel > 0:
        fuel -= 1
        nxt = addB(cur, dirr)
        if not onBoard(nxt):
            return out
        occ = bGet(b, nxt)
        if occ == 0:
            out.append(mkMove(f, nxt, 0))
            cur = nxt
            continue
        if pcCol(occ) == stm:
            return out
        out.append(mkMove(f, nxt, 0))
        return out
    return out

def genSlides(b, stm, f, dirs):
    out = []
    for d in dirs:
        out += genRay(b, stm, f, d)
    return out

def genPawnWhite(b, ep, f):
    """Clause R5/R6 — `gmPawn`."""
    one = addB(f, 16)
    if bGet(b, one) != 0:
        pushes = []
    elif sqRank(f) == 6:
        pushes = addPromos(f, one)
    else:
        pushes = [mkMove(f, one, 0)]
        if sqRank(f) == 1:
            two = addB(f, 32)
            if bGet(b, two) == 0:
                pushes = pushes + [mkMove(f, two, SP_DPUSH)]

    def cap(off):
        t = addB(f, off)
        if not onBoard(t):
            return []
        occ = bGet(b, t)
        if occ == 0:
            return [mkMove(f, t, SP_EP)] if ep == t else []
        if pcCol(occ) == WHITE:
            return []
        if sqRank(f) == 6:
            return addPromos(f, t)
        return [mkMove(f, t, 0)]

    return pushes + cap(15) + cap(17)

def genPawnBlack(b, ep, f):
    one = addB(f, negB(16))
    if bGet(b, one) != 0:
        pushes = []
    elif sqRank(f) == 1:
        pushes = addPromos(f, one)
    else:
        pushes = [mkMove(f, one, 0)]
        if sqRank(f) == 6:
            two = addB(f, negB(32))
            if bGet(b, two) == 0:
                pushes = pushes + [mkMove(f, two, SP_DPUSH)]

    def cap(off):
        t = addB(f, off)
        if not onBoard(t):
            return []
        occ = bGet(b, t)
        if occ == 0:
            return [mkMove(f, t, SP_EP)] if ep == t else []
        if pcCol(occ) == BLACK:
            return []
        if sqRank(f) == 1:
            return addPromos(f, t)
        return [mkMove(f, t, 0)]

    return pushes + cap(negB(15)) + cap(negB(17))

def genCastling(p, f):
    """Clause R7 — `genCastling`.  The engine trusts the rights bits and
    never checks that a rook is on the corner (DIVERGENCE F1)."""
    b = p.board
    if p.stm == WHITE:
        if f != 0x04 or isAttacked(b, BLACK, 0x04):
            return []
        ks = ([mkMove(0x04, 0x06, SP_OO)]
              if (bit(p.castling, 0) == 1 and bGet(b, 0x05) == 0 and bGet(b, 0x06) == 0
                  and not isAttacked(b, BLACK, 0x05) and not isAttacked(b, BLACK, 0x06))
              else [])
        qs = ([mkMove(0x04, 0x02, SP_OOO)]
              if (bit(p.castling, 1) == 1 and bGet(b, 0x03) == 0 and bGet(b, 0x02) == 0
                  and bGet(b, 0x01) == 0
                  and not isAttacked(b, BLACK, 0x03) and not isAttacked(b, BLACK, 0x02))
              else [])
        return ks + qs
    if f != 0x74 or isAttacked(b, WHITE, 0x74):
        return []
    ks = ([mkMove(0x74, 0x76, SP_OO)]
          if (bit(p.castling, 2) == 1 and bGet(b, 0x75) == 0 and bGet(b, 0x76) == 0
              and not isAttacked(b, WHITE, 0x75) and not isAttacked(b, WHITE, 0x76))
          else [])
    qs = ([mkMove(0x74, 0x72, SP_OOO)]
          if (bit(p.castling, 3) == 1 and bGet(b, 0x73) == 0 and bGet(b, 0x72) == 0
              and bGet(b, 0x71) == 0
              and not isAttacked(b, WHITE, 0x73) and not isAttacked(b, WHITE, 0x72))
          else [])
    return ks + qs

def genForSquare(p, f):
    pc = bGet(p.board, f)
    t = pcType(pc)
    if t == WP:
        return (genPawnWhite(p.board, p.ep, f) if p.stm == WHITE
                else genPawnBlack(p.board, p.ep, f))
    if t == WN:
        return genHops(p.board, p.stm, f, knightDirs)
    if t == WK:
        return genCastling(p, f) + genHops(p.board, p.stm, f, kingDirs)
    if t == WB:
        return genSlides(p.board, p.stm, f, bishopDirs)
    if t == WR:
        return genSlides(p.board, p.stm, f, rookDirs)
    return genSlides(p.board, p.stm, f, kingDirs)          # queen

def genMoves(p):
    """Clause R_GEN — pseudo-legal moves, in the ENGINE's generation order."""
    out = []
    for f in scanSquares:
        pc = bGet(p.board, f)
        if pc == 0 or pcCol(pc) != p.stm:
            continue
        out += genForSquare(p, f)
    return out

# --------------------------------------------------------- 9. make / unmake

def clrCastleSq(rights, s):
    if s == 0x00:
        return andB(rights, 0xFD)
    if s == 0x07:
        return andB(rights, 0xFE)
    if s == 0x70:
        return andB(rights, 0xF7)
    if s == 0x77:
        return andB(rights, 0xFB)
    return rights

def capSquare(p, m):
    if mvSpecial(m) == SP_EP:
        return (addB(m.dst, negB(16)) if pcCol(bGet(p.board, m.frm)) == WHITE
                else addB(m.dst, 16))
    return m.dst

def makeMove(p, m):
    """Clause R9 — movegen.inc:693."""
    piece = bGet(p.board, m.frm)
    side = pcCol(piece)
    special = mvSpecial(m)
    promo = mvPromo(m)
    capSq = capSquare(p, m)
    captured = bGet(p.board, capSq)

    b = bSet(p.board, m.frm, 0)
    if special == SP_EP:
        b = bSet(b, capSq, 0)
    placed = orB(side, promo) if promo != 0 else piece
    b = bSet(b, m.dst, placed)
    if special == SP_OO:
        b = (bSet(bSet(b, 0x07, 0), 0x05, WR) if side == WHITE
             else bSet(bSet(b, 0x77, 0), 0x75, BR))
    elif special == SP_OOO:
        b = (bSet(bSet(b, 0x00, 0), 0x03, WR) if side == WHITE
             else bSet(bSet(b, 0x70, 0), 0x73, BR))

    wk = m.dst if (pcType(piece) == WK and side == WHITE) else p.wking
    bk = m.dst if (pcType(piece) == WK and side == BLACK) else p.bking

    if pcType(piece) == WK:
        r0 = andB(p.castling, 0xFC) if side == WHITE else andB(p.castling, 0xF3)
    else:
        r0 = p.castling
    r1 = clrCastleSq(clrCastleSq(r0, m.frm), m.dst)

    if special == SP_DPUSH:
        ep = addB(m.frm, 16) if side == WHITE else addB(m.frm, negB(16))
    else:
        ep = 0xFF

    hm = 0 if (pcType(piece) == WP or captured != 0) else w8(p.halfmove + 1)

    return Position(b, other(p.stm), r1, ep, hm, wk, bk,
                    p.moveCount + 1 if side == BLACK else p.moveCount)


class Undo(tuple):
    __slots__ = ()
    FIELDS = ("frm", "dst", "flag", "piece", "captured", "capSq",
              "castling", "ep", "halfmove", "wking", "bking", "moveCount")

    def __new__(cls, *a):
        return super().__new__(cls, a)


for _i, _f in enumerate(Undo.FIELDS):
    setattr(Undo, _f, property(lambda self, _i=_i: self[_i]))


def undoOf(p, m):
    return Undo(m.frm, m.dst, m.flag, bGet(p.board, m.frm),
                bGet(p.board, capSquare(p, m)), capSquare(p, m),
                p.castling, p.ep, p.halfmove, p.wking, p.bking, p.moveCount)


def unmakeMove(p, u):
    """Clause R10 — movegen.inc:968."""
    side = pcCol(u.piece)
    special = u.flag % 8
    b = bSet(p.board, u.frm, u.piece)
    if u.dst == u.capSq:
        b = bSet(b, u.dst, u.captured)
    else:
        b = bSet(bSet(b, u.dst, 0), u.capSq, u.captured)
    if special == SP_OO:
        b = (bSet(bSet(b, 0x05, 0), 0x07, WR) if side == WHITE
             else bSet(bSet(b, 0x75, 0), 0x77, BR))
    elif special == SP_OOO:
        b = (bSet(bSet(b, 0x03, 0), 0x00, WR) if side == WHITE
             else bSet(bSet(b, 0x73, 0), 0x70, BR))
    return Position(b, other(p.stm), u.castling, u.ep, u.halfmove,
                    u.wking, u.bking, u.moveCount)

# ------------------------------------------------- 10. legality / terminal

def moverInCheck(q):
    return inCheckSide(q, other(q.stm))

def genLegal(p):
    """Clause R11 — movegen.inc:1113."""
    return [m for m in genMoves(p) if not moverInCheck(makeMove(p, m))]

def isInsufficient(b):
    """Clause R13 — the ENGINE's rule (DIVERGENCE F3)."""
    types = [pcType(bGet(b, s)) for s in scanSquares]
    heavy = any(t in (1, 4, 5) for t in types)
    minors = len([t for t in types if t in (2, 3)])
    return (not heavy) and minors < 2

PLAY, WHITE_MATED, BLACK_MATED, STALEMATE, DRAW = 0, 1, 2, 3, 4
STATE_NAMES = {0: "play", 1: "whiteMated", 2: "blackMated", 3: "stalemate", 4: "draw"}


class History(tuple):
    __slots__ = ()

    def __new__(cls, keys, cur):
        return super().__new__(cls, (tuple(keys), cur))

    keys = property(lambda self: self[0])
    cur = property(lambda self: self[1])


def countReps(h):
    return len([k for k in h.keys if k == h.cur])

def updateTerminal(p, h):
    """Clause R12 — movegen.inc:1172.  Precedence is the engine's."""
    if not genLegal(p):
        if inCheckSide(p, p.stm):
            return WHITE_MATED if p.stm == WHITE else BLACK_MATED
        return STALEMATE
    if countReps(h) >= 3:
        return DRAW
    if isInsufficient(p.board):
        return DRAW
    if p.halfmove >= 100:
        return DRAW
    return PLAY

# --------------------------------------------------------------- 11. eval

materialTbl = [0, 100, 320, 330, 500, 900, 0]

pstPawn = [0, 0, 0, 0, 0, 0, 0, 0,
           5, 10, 10, -20, -20, 10, 10, 5,
           5, -5, -10, 0, 0, -10, -5, 5,
           0, 0, 0, 20, 20, 0, 0, 0,
           5, 5, 10, 25, 25, 10, 5, 5,
           10, 10, 20, 30, 30, 20, 10, 10,
           50, 50, 50, 50, 50, 50, 50, 50,
           0, 0, 0, 0, 0, 0, 0, 0]
pstKnight = [-50, -40, -30, -30, -30, -30, -40, -50,
             -40, -20, 0, 5, 5, 0, -20, -40,
             -30, 5, 10, 15, 15, 10, 5, -30,
             -30, 0, 15, 20, 20, 15, 0, -30,
             -30, 5, 15, 20, 20, 15, 5, -30,
             -30, 0, 10, 15, 15, 10, 0, -30,
             -40, -20, 0, 0, 0, 0, -20, -40,
             -50, -40, -30, -30, -30, -30, -40, -50]
pstBishop = [-20, -10, -10, -10, -10, -10, -10, -20,
             -10, 5, 0, 0, 0, 0, 5, -10,
             -10, 10, 10, 10, 10, 10, 10, -10,
             -10, 0, 10, 10, 10, 10, 0, -10,
             -10, 5, 5, 10, 10, 5, 5, -10,
             -10, 0, 5, 10, 10, 5, 0, -10,
             -10, 0, 0, 0, 0, 0, 0, -10,
             -20, -10, -10, -10, -10, -10, -10, -20]
pstRook = [0, 0, 0, 5, 5, 0, 0, 0,
           -5, 0, 0, 0, 0, 0, 0, -5,
           -5, 0, 0, 0, 0, 0, 0, -5,
           -5, 0, 0, 0, 0, 0, 0, -5,
           -5, 0, 0, 0, 0, 0, 0, -5,
           -5, 0, 0, 0, 0, 0, 0, -5,
           5, 10, 10, 10, 10, 10, 10, 5,
           0, 0, 0, 0, 0, 0, 0, 0]
pstQueen = [-20, -10, -10, -5, -5, -10, -10, -20,
            -10, 0, 5, 0, 0, 0, 0, -10,
            -10, 5, 5, 5, 5, 5, 0, -10,
            0, 0, 5, 5, 5, 5, 0, -5,
            -5, 0, 5, 5, 5, 5, 0, -5,
            -10, 0, 5, 5, 5, 5, 0, -10,
            -10, 0, 0, 0, 0, 0, 0, -10,
            -20, -10, -10, -5, -5, -10, -10, -20]
pstKingMG = [-30, -40, -40, -50, -50, -40, -40, -30,
             -30, -40, -40, -50, -50, -40, -40, -30,
             -30, -40, -40, -50, -50, -40, -40, -30,
             -30, -40, -40, -50, -50, -40, -40, -30,
             -20, -30, -30, -40, -40, -30, -30, -20,
             -10, -20, -20, -20, -20, -20, -20, -10,
             20, 20, 0, 0, 0, 0, 20, 20,
             20, 30, 10, 0, 0, 10, 30, 20]
pstKingEG = [-50, -40, -30, -20, -20, -30, -40, -50,
             -30, -20, -10, 0, 0, -10, -20, -30,
             -30, -10, 20, 30, 30, 20, -10, -30,
             -30, -10, 30, 40, 40, 30, -10, -30,
             -30, -10, 30, 40, 40, 30, -10, -30,
             -30, -10, 20, 30, 30, 20, -10, -30,
             -30, -30, 0, 0, 0, 0, -30, -30,
             -50, -30, -30, -30, -30, -30, -30, -50]

PHASE_EG = 8
DOUBLED, ISOLATED, BISHOP_PAIR, PASSED, KSHIELD = 12, 14, 30, 8, 10


def pstFor(t):
    return {1: pstPawn, 2: pstKnight, 3: pstBishop,
            4: pstRook, 5: pstQueen}.get(t, pstKingMG)

def pieceValSigned(pc, sq):
    if pc == 0 or pcType(pc) == 6:
        return 0
    idx = mirrorIdx(sq) if pcCol(pc) == BLACK else sq64(sq)
    v = materialTbl[pcType(pc)] + pstFor(pcType(pc))[idx]
    return -v if pcCol(pc) == BLACK else v

def pstScore(b):
    return sum(pieceValSigned(bGet(b, s), s) for s in scanSquares)

def gamePhase(b):
    acc = 0
    for s in scanSquares:
        t = pcType(bGet(b, s))
        if t in (2, 3):
            acc += 1
        elif t == 4:
            acc += 2
        elif t == 5:
            acc += 4
    return acc

def kingPstSigned(b, pc, sq):
    tbl = pstKingMG if gamePhase(b) >= PHASE_EG else pstKingEG
    idx = mirrorIdx(sq) if pcCol(pc) == BLACK else sq64(sq)
    v = tbl[idx]
    return -v if pcCol(pc) == BLACK else v

def fileCount(b, want, f):
    return len([s for s in scanSquares if bGet(b, s) == want and sqFile(s) == f])

def countPiece(b, want):
    return len([s for s in scanSquares if bGet(b, s) == want])

def shieldMissing(b, ks, pawn):
    dirr = negB(16) if pcCol(pawn) == BLACK else 16
    acc = 0
    for off in (negB(1), 0, 1):
        t = addB(addB(ks, dirr), off)
        if not onBoard(t) or bGet(b, t) != pawn:
            acc += 1
    return acc

def centerDist(s):
    f, r = sqFile(s), sqRank(s)
    return (f - 4 if f >= 4 else 3 - f) + (r - 4 if r >= 4 else 3 - r)

def kingProx(wk, bk):
    df = abs(sqFile(bk) - sqFile(wk))
    dr = abs(sqRank(bk) - sqRank(wk))
    return 7 - max(df, dr)

def passedPawns(b):
    if gamePhase(b) >= 12:
        return 0

    def adj(want, f):
        return ((f == 0 or fileCount(b, want, f - 1) == 0)
                and fileCount(b, want, f) == 0
                and (f == 7 or fileCount(b, want, f + 1) == 0))

    acc = 0
    for s in scanSquares:
        pc = bGet(b, s)
        if pc == WP and adj(BP, sqFile(s)):
            acc += PASSED * sqRank(s)
        elif pc == BP and adj(WP, sqFile(s)):
            acc -= PASSED * (7 - sqRank(s))
    return acc

def matingEval(b, wk, bk):
    def anyOf(col):
        return any(bGet(b, s) != 0 and pcCol(bGet(b, s)) == col and pcType(bGet(b, s)) != 6
                   for s in scanSquares)

    def heavyOf(col):
        return any(bGet(b, s) != 0 and pcCol(bGet(b, s)) == col
                   and pcType(bGet(b, s)) in (4, 5) for s in scanSquares)

    if not anyOf(BLACK):
        return 0 if not heavyOf(WHITE) else centerDist(bk) * 16 + kingProx(wk, bk) * 4
    if not anyOf(WHITE):
        return 0 if not heavyOf(BLACK) else -(centerDist(wk) * 16 + kingProx(wk, bk) * 4)
    return 0

def evalWhite(p):
    """Clause R_EVAL — engine.inc:420, white-relative."""
    b = p.board
    acc = pstScore(b) + kingPstSigned(b, WK, p.wking) + kingPstSigned(b, BK, p.bking)
    acc += BISHOP_PAIR if countPiece(b, WB) >= 2 else 0
    acc -= BISHOP_PAIR if countPiece(b, BB) >= 2 else 0
    for f in range(8):
        wf, bf = fileCount(b, WP, f), fileCount(b, BP, f)

        def hasNb(want):
            return ((f != 0 and fileCount(b, want, f - 1) > 0)
                    or (f != 7 and fileCount(b, want, f + 1) > 0))

        if wf >= 2:
            acc -= DOUBLED
        if wf > 0 and not hasNb(WP):
            acc -= ISOLATED
        if bf >= 2:
            acc += DOUBLED
        if bf > 0 and not hasNb(BP):
            acc += ISOLATED
    acc += passedPawns(b)
    if gamePhase(b) >= 10:
        acc -= shieldMissing(b, p.wking, WP) * KSHIELD
        acc += shieldMissing(b, p.bking, BP) * KSHIELD
    acc += matingEval(b, p.wking, p.bking)
    return acc

def eval_(p):
    return evalWhite(p) if p.stm == WHITE else -evalWhite(p)

# --- colour mirror -------------------------------------------------------

def mirrorSq(s):
    return addB(w8((7 - sqRank(s)) * 16), sqFile(s))

def mirrorPc(pc):
    return 0 if pc == 0 else xorB(pc, 8)

def mirrorBoard(b):
    nb = emptyBoard()
    for s in scanSquares:
        nb = bSet(nb, mirrorSq(s), mirrorPc(bGet(b, s)))
    return nb

def mirrorCastling(c):
    return orB(andB(c * 4, 0x0C), andB(c // 4, 0x03))

def mirrorPos(p):
    return Position(mirrorBoard(p.board), other(p.stm), mirrorCastling(p.castling),
                    0xFF if p.ep == 0xFF else mirrorSq(p.ep), p.halfmove,
                    mirrorSq(p.bking), mirrorSq(p.wking), p.moveCount)

# ------------------------------------------------------------- 12. search

INF, MATE, MAXPLY = 30000, 29000, 15


class GTree(tuple):
    __slots__ = ()

    def __new__(cls, v, cs):
        return super().__new__(cls, (v, tuple(cs)))

    v = property(lambda self: self[0])
    cs = property(lambda self: self[1])


def minimax(t, d):
    if d == 0 or not t.cs:
        return t.v
    return max(-minimax(c, d - 1) for c in t.cs)

def alphaBeta(t, d, a, b):
    """Fail-soft alpha-beta, transcribed from the engine's node loop."""
    if d == 0 or not t.cs:
        return t.v
    best = -INF
    for c in t.cs:
        s = -alphaBeta(c, d - 1, -b, -a)
        if s > best:
            best = s
        if best > a:
            a = best
        if a >= b:
            return best
    return best

# ------------------------------------------------------------ 13. contract

def C1_pseudoLegal(o):
    return o.mv in genMoves(o.pre)

def C2_legal(o):
    return o.mv in genLegal(o.pre)

def C3_makeAgrees(o):
    return makeMove(o.pre, o.mv) == o.post

def C4_unmakeInverts(o):
    return unmakeMove(makeMove(o.pre, o.mv), undoOf(o.pre, o.mv)) == o.pre

def C5_sideAlternates(o):
    return o.post.stm == other(o.pre.stm)

def C6_kingSafe(o):
    return not moverInCheck(o.post)

def C7_rightsMonotone(o):
    return andB(o.post.castling, o.pre.castling) == o.post.castling

def C8_epDiscipline(o):
    if mvSpecial(o.mv) == SP_DPUSH:
        return o.post.ep != 0xFF
    return o.post.ep == 0xFF

def C9_halfmove(o):
    piece = bGet(o.pre.board, o.mv.frm)
    cap = bGet(o.pre.board, capSquare(o.pre, o.mv))
    if pcType(piece) == WP or cap != 0:
        return o.post.halfmove == 0
    return o.post.halfmove == w8(o.pre.halfmove + 1)

def C10_kingSquares(o):
    return (bGet(o.post.board, o.post.wking) == WK
            and bGet(o.post.board, o.post.bking) == BK)

def C11_terminal(o):
    return updateTerminal(o.post, o.hist) == o.state

def C12_pieceCount(o):
    def cnt(b):
        return len([s for s in scanSquares if bGet(b, s) != 0])
    cap = bGet(o.pre.board, capSquare(o.pre, o.mv))
    return cnt(o.post.board) == cnt(o.pre.board) - (1 if cap != 0 else 0)

def C13_kingsUnique(o):
    return countPiece(o.post.board, WK) == 1 and countPiece(o.post.board, BK) == 1

def C14_promotion(o):
    if mvPromo(o.mv) == 0:
        return True
    pc = bGet(o.post.board, o.mv.dst)
    return (pcCol(pc) == pcCol(bGet(o.pre.board, o.mv.frm))
            and 2 <= pcType(pc) <= 5)


CLAUSES = [C1_pseudoLegal, C2_legal, C3_makeAgrees, C4_unmakeInverts,
           C5_sideAlternates, C6_kingSafe, C7_rightsMonotone, C8_epDiscipline,
           C9_halfmove, C10_kingSquares, C11_terminal, C12_pieceCount,
           C13_kingsUnique, C14_promotion]

clauseNames = ["C1_pseudoLegal", "C2_legal", "C3_makeAgrees", "C4_unmakeInverts",
               "C5_sideAlternates", "C6_kingSafe", "C7_rightsMonotone",
               "C8_epDiscipline", "C9_halfmove", "C10_kingSquares", "C11_terminal",
               "C12_pieceCount", "C13_kingsUnique", "C14_promotion"]


class Obs:
    __slots__ = ("pre", "mv", "post", "hist", "state")

    def __init__(self, pre, mv, post, hist, state):
        self.pre, self.mv, self.post, self.hist, self.state = pre, mv, post, hist, state

    def replace(self, **kw):
        d = dict(pre=self.pre, mv=self.mv, post=self.post, hist=self.hist, state=self.state)
        d.update(kw)
        return Obs(**d)


def obsOf(p, m, h):
    q = makeMove(p, m)
    return Obs(p, m, q, h, updateTerminal(q, h))

def clauseVector(o):
    return [bool(c(o)) for c in CLAUSES]

def Conforming(o):
    return all(clauseVector(o))

def failedClauses(o):
    return [i for i, v in enumerate(clauseVector(o)) if not v]

def failedClauseNames(o):
    return [clauseNames[i] for i in failedClauses(o)]

# ---------------------------------------------------------------- 14. perft

def perft(p, d):
    if d == 0:
        return 1
    return sum(perft(makeMove(p, m), d - 1) for m in genLegal(p))

def perftDivide(p, d):
    return {m: perft(makeMove(p, m), d - 1) for m in genLegal(p)}
