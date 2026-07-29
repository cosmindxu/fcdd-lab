#!/usr/bin/env python3
"""
BRIDGE layer 3 — SPEC vs TWIN, brute force over generated positions.

The Lean contract and the Python twin are INDEPENDENT transcriptions of the
same assembly.  This layer runs both over the same pseudo-random corpus of
small positions and demands byte-identical digests:

    genMoves (ordered, with flags) | genLegal (ordered) | in-check |
    evalWhite | gamePhase | isInsufficient | updateTerminal | make/unmake
    round-trip | perft 1

The corpus is deterministic (seeded), so a failure is reproducible.

SCOPE / PRECONDITION.  The generator never places a pawn on rank 1 or rank 8.
That is not laziness: `gmPawn` computes `from+16` with NO 0x88 test, so for a
white pawn on rank 8 the ENGINE reads board[0x80] = `sideToMove` and can WRITE
there.  Spec and twin both model board[0x80] as 0, so they would agree with
each other and BOTH differ from the engine.  Including such positions would
therefore test an agreement that means nothing.  See organic_findings.md F6.
"""
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "twin"))

from hc91_twin import *                                          # noqa: F403

SPEC = os.path.join(HERE, "..", "spec")
LEAN = os.path.expanduser("~/.elan/bin/lean")
N = int(os.environ.get("B3_N", "300"))
SEED = int(os.environ.get("B3_SEED", "20260729"))

PIECES = [WP, WN, WB, WR, WQ, BP, BN, BB, BR, BQ]


def gen_positions(n, seed):
    rnd = random.Random(seed)
    out = []
    while len(out) < n:
        b = emptyBoard()
        free = list(scanSquares)
        rnd.shuffle(free)
        wk, bk = free.pop(), free.pop()
        if abs(sqFile(wk) - sqFile(bk)) <= 1 and abs(sqRank(wk) - sqRank(bk)) <= 1:
            continue                                # kings adjacent: unreachable
        b = bSet(bSet(b, wk, WK), bk, BK)
        for _ in range(rnd.randint(0, 10)):
            if not free:
                break
            sq = free.pop()
            pc = rnd.choice(PIECES)
            if pcType(pc) == WP and sqRank(sq) in (0, 7):
                continue                            # precondition, see docstring
            b = bSet(b, sq, pc)
        stm = rnd.choice([WHITE, BLACK])
        cast = 0
        if wk == 0x04:
            if bGet(b, 0x07) == WR:
                cast |= 1
            if bGet(b, 0x00) == WR:
                cast |= 2
        if bk == 0x74:
            if bGet(b, 0x77) == BR:
                cast |= 4
            if bGet(b, 0x70) == BR:
                cast |= 8
        if rnd.random() < 0.35:
            ep = rnd.randrange(0x50, 0x58) if stm == WHITE else rnd.randrange(0x20, 0x28)
        else:
            ep = 0xFF
        out.append(Position(b, stm, cast, ep, rnd.randrange(0, 101),
                            wk, bk, rnd.randrange(1, 80)))
    return out


def move_str(m):
    return "%d,%d,%d" % (m.frm, m.dst, m.flag)


def digest(p):
    gm, gl = genMoves(p), genLegal(p)
    rt = all(unmakeMove(makeMove(p, m), undoOf(p, m)) == p for m in gl)
    return "|".join([
        " ".join(move_str(m) for m in gm),
        " ".join(move_str(m) for m in gl),
        str(1 if inCheckSide(p, p.stm) else 0),
        str(evalWhite(p)),
        str(gamePhase(p.board)),
        str(1 if isInsufficient(p.board) else 0),
        str(updateTerminal(p, History([], 0))),
        str(1 if rt else 0),
        str(perft(p, 1)),
    ])


def lean_literal(p):
    pairs = ", ".join("(%d,%d)" % (s, bGet(p.board, s))
                      for s in scanSquares if bGet(p.board, s) != 0)
    return ("{ board := mkBoard [%s], stm := %d, castling := %d, ep := %d, "
            "halfmove := %d, wking := %d, bking := %d, moveCount := %d }"
            % (pairs, p.stm, p.castling, p.ep, p.halfmove, p.wking, p.bking,
               p.moveCount))


LEAN_PRELUDE = r'''import Contract
open HC91

def moveStr (m : Move) : String :=
  toString m.frm ++ "," ++ toString m.dst ++ "," ++ toString m.flag

def stateNum : GameState → Nat
  | GameState.play => 0
  | GameState.whiteMated => 1
  | GameState.blackMated => 2
  | GameState.stalemate => 3
  | GameState.draw => 4

def digest (p : Position) : String :=
  let gm := genMoves p
  let gl := genLegal p
  String.intercalate "|"
    [ String.intercalate " " (gm.map moveStr),
      String.intercalate " " (gl.map moveStr),
      toString (if inCheckSide p p.stm then 1 else 0),
      toString (evalWhite p),
      toString (gamePhase p.board),
      toString (if isInsufficient p.board then 1 else 0),
      toString (stateNum (updateTerminal p { keys := [], cur := 0 })),
      toString (if gl.all (fun m => unmakeMove (makeMove p m) (undoOf p m) == p)
                then 1 else 0),
      toString (perft p 1) ]

def go : Nat → List Position → IO Unit
  | _, [] => pure ()
  | i, p :: ps => do
      IO.println (toString i ++ "#" ++ digest p)
      go (i + 1) ps
'''


def main():
    positions = gen_positions(N, SEED)
    src = [LEAN_PRELUDE, "def corpus : List Position := ["]
    src.append(",\n".join("  " + lean_literal(p) for p in positions))
    src.append("]\n\n#eval go 0 corpus\n")
    gen = os.path.join(SPEC, "B3Gen.lean")
    with open(gen, "w") as f:
        f.write("\n".join(src))

    olean = os.path.join(SPEC, "Contract.olean")
    if not os.path.exists(olean):
        print("[b3] building Contract.olean ...")
        r = subprocess.run([LEAN, "-o", olean, os.path.join(SPEC, "Contract.lean")],
                           capture_output=True, text=True, cwd=SPEC)
        if r.returncode != 0:
            print("[b3] FAIL: spec did not compile\n" + r.stdout[-2000:] + r.stderr[-2000:])
            return 1

    env = dict(os.environ, LEAN_PATH=os.path.abspath(SPEC))
    r = subprocess.run([LEAN, gen], capture_output=True, text=True, env=env, cwd=SPEC)
    if r.returncode != 0:
        print("[b3] FAIL: generated Lean file did not run\n"
              + r.stdout[-2000:] + r.stderr[-2000:])
        return 1
    lean_lines = [l for l in r.stdout.splitlines() if "#" in l]
    if len(lean_lines) != N:
        print("[b3] FAIL: Lean emitted %d digests, expected %d" % (len(lean_lines), N))
        return 1

    fails = []
    for line in lean_lines:
        idx, _, lean_d = line.partition("#")
        i = int(idx)
        twin_d = digest(positions[i])
        if twin_d != lean_d:
            parts = ["genMoves", "genLegal", "inCheck", "evalWhite", "gamePhase",
                     "isInsufficient", "updateTerminal", "unmakeRoundTrip", "perft1"]
            lp, tp = lean_d.split("|"), twin_d.split("|")
            which = [parts[k] for k in range(len(parts))
                     if k >= len(lp) or k >= len(tp) or lp[k] != tp[k]]
            fails.append("pos %d differs in %s\n    spec: %s\n    twin: %s"
                         % (i, which, lean_d[:300], twin_d[:300]))

    tot_moves = sum(len(genMoves(p)) for p in positions)
    tot_legal = sum(len(genLegal(p)) for p in positions)
    print("[b3_spec_twin_brute] %d positions (seed %d), %d pseudo-legal / %d legal "
          "moves compared across 9 observables, %d failures"
          % (N, SEED, tot_moves, tot_legal, len(fails)))
    for f in fails[:10]:
        print("  FAIL " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
