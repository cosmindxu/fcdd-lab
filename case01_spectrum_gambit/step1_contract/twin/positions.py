"""
Witness positions shared by the spec, the twin and the bridge.

The `W*` positions are the exact ones the Lean contract proves theorems
about (../spec/Contract.lean §15).  The `ENGINE_*` positions are the
engine's OWN perft test boards, transcribed from perft.inc:437-471 in
`setupBoard` layout (64 bytes rank-major a1..h8, then side, castling, ep)
and expanded through the same `finalizePosition` rules.
"""

from hc91_twin import (Position, mkBoard, scanSquares, bGet, bSet, WHITE, BLACK,
                       WP, WN, WB, WR, WQ, WK, BP, BN, BB, BR, BQ, BK)

# ------------------------------------------------ Lean witnesses (§15) ----

startBoard = mkBoard([
    (0x00, WR), (0x01, WN), (0x02, WB), (0x03, WQ), (0x04, WK), (0x05, WB),
    (0x06, WN), (0x07, WR),
    (0x10, WP), (0x11, WP), (0x12, WP), (0x13, WP), (0x14, WP), (0x15, WP),
    (0x16, WP), (0x17, WP),
    (0x60, BP), (0x61, BP), (0x62, BP), (0x63, BP), (0x64, BP), (0x65, BP),
    (0x66, BP), (0x67, BP),
    (0x70, BR), (0x71, BN), (0x72, BB), (0x73, BQ), (0x74, BK), (0x75, BB),
    (0x76, BN), (0x77, BR)])

startPos = Position(startBoard, WHITE, 0x0F, 0xFF, 0, 0x04, 0x74, 1)

matePos = Position(mkBoard([
    (0x00, WR), (0x01, WN), (0x02, WB), (0x03, WQ), (0x04, WK), (0x05, WB),
    (0x06, WN), (0x07, WR),
    (0x10, WP), (0x11, WP), (0x12, WP), (0x13, WP), (0x14, WP), (0x25, WP),
    (0x36, WP), (0x17, WP),
    (0x60, BP), (0x61, BP), (0x62, BP), (0x63, BP), (0x44, BP), (0x65, BP),
    (0x66, BP), (0x67, BP),
    (0x70, BR), (0x71, BN), (0x72, BB), (0x37, BQ), (0x74, BK), (0x75, BB),
    (0x76, BN), (0x77, BR)]), WHITE, 0x0F, 0xFF, 0, 0x04, 0x74, 3)

stalematePos = Position(mkBoard([(0x70, BK), (0x62, WK), (0x51, WQ)]),
                        BLACK, 0, 0xFF, 0, 0x62, 0x70, 40)

insufficientPos = Position(mkBoard([(0x00, WK), (0x77, BK), (0x33, WN)]),
                           WHITE, 0, 0xFF, 3, 0x00, 0x77, 60)

castlePos = Position(mkBoard([
    (0x00, WR), (0x04, WK), (0x07, WR), (0x70, BR), (0x74, BK), (0x77, BR),
    (0x10, WP), (0x17, WP), (0x60, BP), (0x67, BP)]),
    WHITE, 0x0F, 0xFF, 5, 0x04, 0x74, 20)

epPos = Position(mkBoard([(0x04, WK), (0x74, BK), (0x44, WP), (0x43, BP)]),
                 WHITE, 0, 0x53, 0, 0x04, 0x74, 12)

promoPos = Position(mkBoard([(0x04, WK), (0x76, BK), (0x61, WP), (0x70, BR)]),
                    WHITE, 0, 0xFF, 0, 0x04, 0x76, 30)

fiftyPos = Position(mkBoard([(0x00, WK), (0x77, BK), (0x33, WR)]),
                    WHITE, 0, 0xFF, 100, 0x00, 0x77, 60)

kiwiPos = Position(mkBoard([
    (0x00, WR), (0x04, WK), (0x07, WR), (0x10, WP), (0x11, WP), (0x12, WP),
    (0x13, WB), (0x14, WB), (0x15, WP), (0x16, WP), (0x17, WP), (0x22, WN),
    (0x25, WQ), (0x27, BP), (0x31, BP), (0x34, WP), (0x43, WP), (0x44, WN),
    (0x50, BB), (0x51, BN), (0x54, BP), (0x55, BN), (0x56, BP), (0x60, BP),
    (0x62, BP), (0x63, BP), (0x64, BQ), (0x65, BP), (0x66, BB), (0x70, BR),
    (0x74, BK), (0x77, BR)]), WHITE, 0x0F, 0xFF, 0, 0x04, 0x74, 1)

pinPos = Position(mkBoard([(0x04, WK), (0x14, WN), (0x74, BK), (0x44, BR)]),
                  WHITE, 0, 0xFF, 0, 0x04, 0x74, 9)

castleBlockedPos = castlePos.replace(
    board=bSet(bSet(castlePos.board, 0x75, BR), 0x65, 0))

LEAN_WITNESSES = {
    "startPos": startPos, "matePos": matePos, "stalematePos": stalematePos,
    "insufficientPos": insufficientPos, "castlePos": castlePos, "epPos": epPos,
    "promoPos": promoPos, "fiftyPos": fiftyPos, "kiwiPos": kiwiPos,
    "pinPos": pinPos, "castleBlockedPos": castleBlockedPos,
}

# ------------------------- the ENGINE's own perft boards (perft.inc) ------


def from_setup_board(rows, side, castling, ep):
    """`setupBoard` + `finalizePosition` — perft.inc:360-433."""
    b = [0] * 128
    for r, row in enumerate(rows):
        for f, pc in enumerate(row):
            b[r * 16 + f] = pc
    wk = bk = 0xFF
    for s in scanSquares:
        if b[s] == WK:
            wk = s
        elif b[s] == BK:
            bk = s
    return Position(b, side, castling, ep, 0, wk, bk, 1)


_ = 0
# Kiwipete: r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq -
ENGINE_KIWI = from_setup_board([
    [WR, _, _, _, WK, _, _, WR],
    [WP, WP, WP, WB, WB, WP, WP, WP],
    [_, _, WN, _, _, WQ, _, BP],
    [_, BP, _, _, WP, _, _, _],
    [_, _, _, WP, WN, _, _, _],
    [BB, BN, _, _, BP, BN, BP, _],
    [BP, _, BP, BP, BQ, BP, BB, _],
    [BR, _, _, _, BK, _, _, BR]], 0, 0x0F, 0xFF)

# Position 3: 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - -
ENGINE_EP3 = from_setup_board([
    [_, _, _, _, _, _, _, _],
    [_, _, _, _, WP, _, WP, _],
    [_, _, _, _, _, _, _, _],
    [_, WR, _, _, _, BP, _, BK],
    [WK, WP, _, _, _, _, _, BR],
    [_, _, _, BP, _, _, _, _],
    [_, _, BP, _, _, _, _, _],
    [_, _, _, _, _, _, _, _]], 0, 0, 0xFF)

# Position 5: rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ -
ENGINE_PROMO = from_setup_board([
    [WR, WN, WB, WQ, WK, _, _, WR],
    [WP, WP, WP, _, WN, BN, WP, WP],
    [_, _, _, _, _, _, _, _],
    [_, _, WB, _, _, _, _, _],
    [_, _, _, _, _, _, _, _],
    [_, _, BP, _, _, _, _, _],
    [BP, BP, _, WP, BB, BP, BP, BP],
    [BR, BN, BB, BQ, _, BK, _, BR]], 0, 0x03, 0xFF)

# The numbers the RUNNING ENGINE printed (artifacts/perft_full.txt), which
# are also its hard-coded expectations in perft.inc.
ENGINE_PERFT = [
    ("start",     startPos,      1, 20),
    ("start",     startPos,      2, 400),
    ("start",     startPos,      3, 8902),
    ("start",     startPos,      4, 197281),
    ("kiwipete",  ENGINE_KIWI,   3, 97862),
    ("enpassant", ENGINE_EP3,    4, 43238),
    ("promotion", ENGINE_PROMO,  3, 62379),
]
