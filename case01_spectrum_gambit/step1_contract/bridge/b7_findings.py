#!/usr/bin/env python3
"""
BRIDGE layer 7 — FINDINGS AS REGRESSION THEOREMS (FCDD law 6).

Every organic finding in ../organic_findings.md that can be demonstrated by
EXECUTION is pinned here.  The assertions encode the CURRENT (divergent)
behaviour, so this layer goes RED the day someone fixes the engine — which is
the point: a finding that nothing watches is a finding that silently comes back.

Each probe prints its evidence and its claim level.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "twin"))

import emu
from hc91_twin import *                                          # noqa: F403
from positions import startPos                                   # noqa: F403

FAILS, EVID = [], []


def ok(cond, msg):
    if not cond:
        FAILS.append(msg)


# =====================================================================
# F5 — the repetition key history (gameKeys, 0x5B00) runs INTO the ZX
#      ROM system variables from ply 128, and lands exactly on FRAMES
#      (the 50 Hz clock the game itself reads) at ply 188.
# =====================================================================
GAMEKEYS, CAP = 0x5B00, 250
last = GAMEKEYS + 2 * (CAP - 1) + 1
SYSVAR_LO, SYSVAR_HI = 0x5C00, 0x5CB5           # ZX Spectrum 48K system vars
FRAMES = 0x5C78

ok(last == 0x5CF3, "gameKeys end address changed: %04X" % last)
first_bad_ply = (SYSVAR_LO - GAMEKEYS) // 2
frames_ply = (FRAMES - GAMEKEYS) // 2
ok(first_bad_ply == 128, "sysvar overlap ply changed: %d" % first_bad_ply)
ok(frames_ply == 188, "FRAMES ply changed: %d" % frames_ply)

# ... and that region is LIVE: the game runs with `im 1` + `ei` (chess.asm:243-7)
# so the ROM interrupt handler ticks FRAMES and rewrites KSTATE every frame.
_, sn1 = emu.run(1400)
_, sn2 = emu.run(2600)
# a run with keys held, so the ROM keyboard scan writes KSTATE / LAST-K
_, sn3 = emu.run(1310, [("Q", 1300)])
f1, f2 = sn1.word(FRAMES), sn2.word(FRAMES)
k1, k3 = sn1.block(0x5C00, 12), sn3.block(0x5C00, 12)
ok(f1 != f2, "FRAMES did not advance (%d vs %d) — ROM ISR not live?" % (f1, f2))
ok(k1 != k3, "KSTATE/LAST-K unchanged while a key was held — ROM scan not live?")
kdiff = [(0x5C00 + i, k1[i], k3[i]) for i in range(12) if k1[i] != k3[i]]
EVID.append("F5  gameKeys 0x%04X..0x%04X overlaps the ZX system variables "
            "0x%04X..0x%04X from ply %d; FRAMES (0x%04X, the clock the game "
            "itself reads) is entry %d.  That region is LIVE under the engine's "
            "own `im 1; ei`: FRAMES %d -> %d across two runs, and the ROM "
            "keyboard scan rewrites %s when a key is held.  [CONFIRMED]"
            % (GAMEKEYS, last, SYSVAR_LO, SYSVAR_HI, first_bad_ply, FRAMES,
               frames_ply, f1, f2,
               ", ".join("0x%04X:%d->%d" % t for t in kdiff) or "(nothing)"))

# =====================================================================
# F10 — the Zobrist key is 16 BITS.  Using the ENGINE'S OWN random tables
#       (read out of RAM), distinct positions inside a single 3-ply game
#       tree already collide in the hundreds.  A collision in the game
#       history is a FALSE threefold draw; a collision inside the search
#       is a transposition-table score read from the wrong position.
# =====================================================================
Z_PIECE, Z_CASTLE, Z_EP, Z_SIDE = 0xD540, 0xDB40, 0xDB60, 0xDB70


def zob_tables(sn):
    return (
        [sn.word(Z_PIECE + 2 * i) for i in range(12 * 64)],
        [sn.word(Z_CASTLE + 2 * i) for i in range(16)],
        [sn.word(Z_EP + 2 * i) for i in range(8)],
        sn.word(Z_SIDE),
    )


ZP, ZC, ZE, ZS = zob_tables(sn1)
ok(len(set(ZP)) > 700, "zobrist piece table looks unseeded: %d distinct "
   "values in %d entries" % (len(set(ZP)), len(ZP)))


def computeKey(p):
    """zobrist.inc:107 `computeKey`, byte for byte."""
    k = 0
    for s in scanSquares:
        pc = bGet(p.board, s)
        if pc == 0:
            continue
        idx = (6 if pcCol(pc) == BLACK else 0) + pcType(pc) - 1
        k ^= ZP[idx * 64 + sq64(s)]
    if p.stm != 0:
        k ^= ZS
    k ^= ZC[p.castling]
    if p.ep != 0xFF:
        k ^= ZE[p.ep % 8]
    return k


# the engine's own key for the start position must match
_, snb = emu.run(1400)
st = emu.read_state(snb)
ok(computeKey(startPos) == st["hashKey"],
   "twin computeKey %04X != engine hashKey %04X" % (computeKey(startPos), st["hashKey"]))

seen = {}
collisions = []
frontier = [startPos]
for _ in range(3):
    nxt = []
    for p in frontier:
        for m in genLegal(p):
            nxt.append(makeMove(p, m))
    frontier = nxt
    for p in frontier:
        k = computeKey(p)
        sig = p.key()
        if k in seen and seen[k] != sig:
            collisions.append(k)
        else:
            seen[k] = sig
ok(len(collisions) > 0,
   "no 16-bit Zobrist collision found in a 3-ply tree — finding F10 needs review")
EVID.append("F10 16-bit Zobrist: %d distinct positions in the 3-ply tree from the "
            "start position produce %d COLLIDING keys using the engine's own "
            "seeded tables (%.1f%% of positions).  [CONFIRMED]"
            % (len(seen) + len(collisions), len(collisions),
               100.0 * len(collisions) / max(1, len(seen) + len(collisions))))

# =====================================================================
# F2 — the e.p. target is set after EVERY double push, even when no enemy
#      pawn can take.  Two positions that differ only in an UNUSABLE e.p.
#      target therefore hash differently, so a repetition that FIDE counts
#      is invisible to the engine.
# =====================================================================
p_ep = Position(mkBoard([(0x04, WK), (0x74, BK), (0x34, WP), (0x60, BP)]),
                BLACK, 0, 0x24, 0, 0x04, 0x74, 5)
p_no = p_ep.replace(ep=0xFF)
ok(computeKey(p_ep) != computeKey(p_no),
   "F2: keys agree — the e.p. square is apparently not hashed")
ok(not any(mvSpecial(m) == SP_EP for m in genLegal(p_ep)),
   "F2: an e.p. capture exists, so the target was in fact usable")
EVID.append("F2  e.p. target set with no possible capture: same board, keys "
            "%04X vs %04X -> two FIDE-identical positions hash differently, so "
            "the repetition counter misses them.  [CONFIRMED]"
            % (computeKey(p_ep), computeKey(p_no)))

# =====================================================================
# F1 — castling trusts the rights bits and never looks for a rook.  Given
#      rights without a rook the engine CREATES one and DELETES whatever
#      stands on the corner.
# =====================================================================
# a black KNIGHT on h1: it attacks f2/g3 only, so e1/f1/g1 stay safe and the
# castling guards all pass — but there is no white rook to castle with.
p_norook = Position(mkBoard([(0x04, WK), (0x74, BK), (0x07, BN)]),
                    WHITE, 0x01, 0xFF, 0, 0x04, 0x74, 5)
oo = mkMove(0x04, 0x06, SP_OO)
ok(oo in genMoves(p_norook), "F1: O-O not generated without a rook")
after = makeMove(p_norook, oo)
ok(bGet(after.board, 0x05) == WR, "F1: no rook conjured on f1")
ok(bGet(after.board, 0x07) == 0, "F1: the black knight on h1 was not deleted")
EVID.append("F1  castling with the right held but NO rook: O-O is generated, a "
            "white rook appears on f1 and the black knight on h1 is deleted.  "
            "Reachable only through a corrupted tape load (the setup editor "
            "zeroes rights), so: pure-contract-only.  [CONFIRMED in the model]")

# =====================================================================
# F3 — FIDE calls K+B vs K+B with SAME-COLOURED bishops a dead position;
#      the engine counts minors across both sides and needs < 2.
# =====================================================================
same_col = Position(mkBoard([(0x00, WK), (0x77, BK), (0x11, WB), (0x33, BB)]),
                    WHITE, 0, 0xFF, 3, 0x00, 0x77, 60)
ok(not isInsufficient(same_col.board), "F3: engine already draws KBvKB")
ok(sqRank(0x11) % 2 == sqRank(0x33) % 2 and sqFile(0x11) % 2 == sqFile(0x33) % 2,
   "F3: the two bishops are not on the same colour")
EVID.append("F3  K+B vs K+B, both bishops on dark squares: FIDE 5.2.2 dead "
            "position, engine says isInsufficient = False and plays on.  "
            "[CONFIRMED in the model]")

# =====================================================================
# F11 — the SEARCH has no repetition or fifty-move awareness: only the game
#       loop's updateTerminal does.  A forced repetition therefore scores as
#       whatever the static eval says, not as 0.
# =====================================================================
src = open("/media/sf_Projects/HC91_emulator/chess/engine.inc").read()
ok("countReps" not in src, "F11: engine.inc now mentions countReps")
ok("halfmove" not in src, "F11: engine.inc now mentions halfmove")
EVID.append("F11 engine.inc (negamax + quiesce) contains no reference to "
            "countReps or halfmove: the search cannot see a draw by repetition "
            "or by the fifty-move rule.  [CONFIRMED by absence in source]")

print("[b7_findings] %d pinned findings re-demonstrated, %d failures" % (len(EVID), len(FAILS)))
for e in EVID:
    print("  * " + e)
for f in FAILS:
    print("  FAIL " + f)
print("  NOTE: these assertions pin CURRENT engine behaviour.  Fixing the engine "
      "will turn this layer RED — update it together with the fix.")
sys.exit(1 if FAILS else 0)
