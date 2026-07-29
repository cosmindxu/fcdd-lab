#!/usr/bin/env python3
"""
BRIDGE layer 5 — THE EMULATOR AS ORACLE (FCDD Beat 3.75, validate on reality).

The real Z80 engine runs inside hc91emu; after every move `afterMove` calls
`updateTerminal`, which leaves the FULL LEGAL MOVE LIST for the side to move
in the ply-0 buffer at 0x6000 with its count in `genCount` (0xE0A0).  A .sna
dump therefore hands us the engine's own answer to "what are the legal moves
here?", computed by 7,343 lines of assembly, which we compare against the
twin move for move, IN ORDER, WITH FLAGS.

Three checks per sampled game:
  E1  engine position  == twin replay of the engine's own move log
  E2  engine legal list == twin genLegal (exact sequence, incl. flags)
  E3  engine gameState  == twin updateTerminal (fed the engine's OWN
      16-bit key history, since the Zobrist function is not modelled)

Plus the strategy property:
  S1  every move the ENGINE chose is legal in the twin's model

FAIL DIRECTION: a run whose screen never reaches "Your move" is reported
UNJUDGEABLE and fails the script.  A broken harness must never read as a
clean pass.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "twin"))

import emu
from hc91_twin import *                                          # noqa: F403
from positions import startPos                                   # noqa: F403

FAILS, CHECKS, SAMPLES = [], 0, 0

# A run is JUDGEABLE only if the engine parked in `humanMove` (status "Your
# move" / "Check!") or reached a terminal screen.  Anything else — a lost
# key, a hung search, a promotion prompt — is reported UNJUDGEABLE and fails.
# It is never silently read as conformance.
JUDGEABLE = ("your move", "check!", "checkmate!", "stalemate", "draw")


def judgeable(txt):
    return any(s in txt.lower() for s in JUDGEABLE)


def chk(name, got, want):
    global CHECKS
    CHECKS += 1
    if got != want:
        FAILS.append("%-28s\n      got  %r\n      want %r" % (name, got, want))


def eng_pos(st):
    return Position(st["board"], st["stm"], st["castling"], st["ep"],
                    st["halfmove"], st["wking"], st["bking"], st["moveCount"])


def replay(moves):
    """Replay (frm,dst) pairs through the twin, resolving the flag from the
    twin's own legal list (the engine's moveLog stores no flag)."""
    p = startPos
    played = []
    for frm, dst in moves:
        cand = [m for m in genLegal(p) if m.frm == frm and m.dst == dst]
        if not cand:
            return None, played, "no legal twin move %02x-%02x" % (frm, dst)
        if len(cand) > 1:
            # only promotions are ambiguous; the engine auto-queens (chess.asm
            # `maybeForceQueen`) when the human does not answer the prompt
            cand = [m for m in cand if mvPromo(m) == 5] or cand[:1]
        p = makeMove(p, cand[0])
        played.append(cand[0])
    return p, played, None


# ---------------------------------------------------------------- games ---
# 0x88 squares.  Two-player mode ('V') removes the engine's thinking delay,
# so a whole game can be typed at a fixed cadence.
GAMES = {
    # Italian game with BOTH castlings and a bishop pin
    "italian": [(0x14, 0x34), (0x64, 0x44), (0x06, 0x25), (0x71, 0x52),
                (0x05, 0x32), (0x75, 0x42), (0x04, 0x06), (0x76, 0x55),
                (0x13, 0x23), (0x63, 0x53), (0x02, 0x46), (0x72, 0x36),
                (0x01, 0x22), (0x74, 0x76)],
    # en passant: 1.e4 a6 2.e5 d5 3.exd6 e.p.
    "enpassant": [(0x14, 0x34), (0x60, 0x50), (0x34, 0x44), (0x63, 0x43),
                  (0x44, 0x53)],
    # queenside castling for both sides
    "queenside": [(0x13, 0x33), (0x63, 0x43), (0x02, 0x46), (0x72, 0x36),
                  (0x01, 0x22), (0x71, 0x52), (0x03, 0x13), (0x73, 0x63),
                  (0x04, 0x02), (0x74, 0x72)],
    # fool's mate — terminates in gameState 1 (white mated)
    "foolsmate": [(0x15, 0x25), (0x64, 0x44), (0x16, 0x36), (0x73, 0x37)],
    # Ruy Lopez exchange: captures (halfmove reset) + castling (rights loss)
    "exchange": [(0x14, 0x34), (0x64, 0x44), (0x06, 0x25), (0x71, 0x52),
                 (0x05, 0x41), (0x60, 0x50), (0x41, 0x52), (0x61, 0x52),
                 (0x04, 0x06), (0x63, 0x53)],
}

for name, moves in GAMES.items():
    types, endf = emu.script(moves, start_frame=1000, prefix="V")
    txt, sn = emu.run(endf + 400, types)
    if not judgeable(txt):
        FAILS.append("%s: UNJUDGEABLE — no settled status line on screen" % name)
        continue
    st = emu.read_state(sn)
    SAMPLES += 1

    # the engine must have accepted every scripted move
    chk("%s/moveLogN" % name, st["moveLog"], [tuple(m) for m in moves])

    tp, played, err = replay(st["moveLog"])
    if err:
        FAILS.append("%s: twin could not replay engine log — %s" % (name, err))
        continue

    # E1 — position agreement, field by field
    ep = eng_pos(st)
    chk("%s/E1 board" % name, tp.board, ep.board)
    chk("%s/E1 stm" % name, tp.stm, ep.stm)
    chk("%s/E1 castling" % name, tp.castling, ep.castling)
    chk("%s/E1 ep" % name, tp.ep, ep.ep)
    chk("%s/E1 halfmove" % name, tp.halfmove, ep.halfmove)
    chk("%s/E1 kings" % name, (tp.wking, tp.bking), (ep.wking, ep.bking))
    chk("%s/E1 moveCount" % name, tp.moveCount, ep.moveCount)

    # E2 — the legal list, exact sequence with flags
    chk("%s/E2 legal-list" % name,
        [(m.frm, m.dst, m.flag) for m in genLegal(tp)], st["legal"])

    # E3 — terminal verdict, using the ENGINE's own key history
    hist = History(st["gameKeys"], st["hashKey"])
    chk("%s/E3 gameState" % name, updateTerminal(tp, hist), st["gameState"])

# --------------------------------------------- S1: the engine's own moves --
# Normal mode (engine plays Black at aiDepth 2).  Every reply it chooses must
# be legal in the twin.  Spaced widely enough for the search to finish.
OPENINGS = [[(0x14, 0x34)], [(0x13, 0x33)], [(0x06, 0x25)],
            [(0x14, 0x34), (0x06, 0x25)]]

for i, moves in enumerate(OPENINGS):
    types, f = [], 1000
    cur = 0x14
    for frm, dst in moves:
        keys, cur = emu.move_keys(cur, frm, dst)
        types.append((keys, f))
        f += emu.CHAR_FRAMES * len(keys) + 2500        # let the engine think
    txt, sn = emu.run(f + 2500, types)
    if not judgeable(txt):
        FAILS.append("S1/%d: UNJUDGEABLE — engine never returned the move" % i)
        continue
    st = emu.read_state(sn)
    SAMPLES += 1
    log = st["moveLog"]
    if len(log) < 2 * len(moves):
        FAILS.append("S1/%d: engine did not reply (log=%r)" % (i, log))
        continue
    p = startPos
    for ply, (frm, dst) in enumerate(log):
        legal = genLegal(p)
        cand = [m for m in legal if m.frm == frm and m.dst == dst]
        CHECKS += 1
        if not cand:
            FAILS.append("S1/%d ply %d: engine played %02x-%02x, NOT legal in twin"
                         % (i, ply, frm, dst))
            break
        p = makeMove(p, cand[0])
    else:
        chk("S1/%d final board" % i, p.board, st["board"])
        chk("S1/%d legal-list" % i,
            [(m.frm, m.dst, m.flag) for m in genLegal(p)], st["legal"])
        CHECKS += 1
        if not genLegal(p) and st["gameState"] == 0:
            FAILS.append("S1/%d: twin says no moves but engine says 'play'" % i)

print("[b5_emulator_oracle] %d emulator runs, %d checks, %d failures"
      % (SAMPLES, CHECKS, len(FAILS)))
for f in FAILS:
    print("  FAIL " + f)
sys.exit(1 if FAILS else 0)
