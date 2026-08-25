#!/usr/bin/env python3
"""Case 04 — D9 MODEL REFEREE. Ground truth = the formal model
(case01's Contract.lean via its executable twin hc91_twin.py), NOT the
Z80 engine. For each corpus entry (seed FEN + path) the referee replays
the path through the twin and records:

    legal   twin genLegal move list (uci strings, promotion letter incl.)
    status  twin updateTerminal, with the twin's own 16-bit key history
            (the same convention the engine uses: keys after each ply,
            current key as `cur`)

The zobrist tables for computeKey are read once from the engine's RAM
(booted once, deterministic: the engine seeds them from its code image).

Gate: --gate-perft refuses to emit answers unless the twin passes the
canonical perft battery (startpos d1-3, kiwipete d3, positions 3-6 d1-3).
Checkpointed: --resume skips entries already in the output file.

The cross-check against the engine's own answers (and the resulting
bug-inventory + sealed answer set) lives in crosscheck_referee.py.
"""
import argparse
import json
import multiprocessing as mp
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
CASE01 = os.path.join(os.path.dirname(LAB), "case01_spectrum_gambit")
TWIN = os.path.join(CASE01, "step1_contract", "twin")
sys.path.insert(0, TWIN)
sys.path.insert(0, HERE)

from hc91_twin import *                                    # noqa: E402,F403
import oracle_cli as oc                                    # noqa: E402

import chess                                              # noqa: E402

PROMO_LETTER = {5: "q", 4: "r", 3: "b", 2: "n"}
TWIN_STATE = {0: "play", 1: "white-mated", 2: "black-mated",
              3: "stalemate", 4: "draw"}

# --- zobrist tables (engine RAM, one boot) -------------------------------

_Z = {}


def load_tables():
    global _Z
    if _Z:
        return _Z
    tmp = tempfile.mkdtemp(prefix="c04ref.")
    try:
        sna = os.path.join(tmp, "t.sna")
        cmd = [oc.EMU, "--machine", "48k", "--rom", oc.ROM, oc.TAP,
               "--autoload", "--turbo", "--save-sna", sna,
               "--frames", "3000"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            raise RuntimeError("table boot failed: %s" % r.stderr[-300:])
        sn = oc.Snapshot(sna)
        ZP = [sn.word(0xD540 + 2 * i) for i in range(12 * 64)]
        ZC = [sn.word(0xDB40 + 2 * i) for i in range(16)]
        ZE = [sn.word(0xDB60 + 2 * i) for i in range(8)]
        ZS = sn.word(0xDB70)
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    _Z = dict(ZP=ZP, ZC=ZC, ZE=ZE, ZS=ZS)
    return _Z


def compute_key(p):
    t = load_tables()
    k = 0
    for s in scanSquares:
        pc = bGet(p.board, s)
        if pc == 0:
            continue
        idx = (6 if pcCol(pc) == BLACK else 0) + pcType(pc) - 1
        k ^= t["ZP"][idx * 64 + sq64(s)]
    if p.stm != 0:
        k ^= t["ZS"]
    k ^= t["ZC"][p.castling]
    if p.ep != 0xFF:
        k ^= t["ZE"][p.ep % 8]
    return k


# --- FEN adapter ---------------------------------------------------------

def fen_to_position(fen):
    b = chess.Board(fen)
    board = emptyBoard()
    for sq in chess.SQUARES:
        p = b.piece_at(sq)
        if p is None:
            continue
        idx = (sq >> 3) * 16 + (sq & 7)
        code = {chess.PAWN: 1, chess.KNIGHT: 2, chess.BISHOP: 3,
                chess.ROOK: 4, chess.QUEEN: 5, chess.KING: 6}[p.piece_type]
        board[idx] = code if p.color == chess.WHITE else code + 8
    stm = 0 if b.turn == chess.WHITE else 8
    cast = (1 if b.has_kingside_castling_rights(chess.WHITE) else 0) | \
           (2 if b.has_queenside_castling_rights(chess.WHITE) else 0) | \
           (4 if b.has_kingside_castling_rights(chess.BLACK) else 0) | \
           (8 if b.has_queenside_castling_rights(chess.BLACK) else 0)
    ep = (0xFF if b.ep_square is None
          else (b.ep_square >> 3) * 16 + (b.ep_square & 7))
    wk = board.index(6)
    bk = board.index(14)
    return Position(board, stm, cast, ep, b.halfmove_clock, wk, bk,
                    b.fullmove_number)


def uci_of(m):
    return oc.sqname(m.frm) + oc.sqname(m.dst) + PROMO_LETTER.get(mvPromo(m), "")


def find_move(p, uci):
    f = uci[:2]
    d = uci[2:4]
    want_promo = uci[4] if len(uci) == 5 else ""
    for m in genLegal(p):
        if oc.sqname(m.frm) == f and oc.sqname(m.dst) == d and \
                PROMO_LETTER.get(mvPromo(m), "") == want_promo:
            return m
    raise RuntimeError("twin: %s not legal from %r" % (uci, p))


def referee(e):
    """Replay one corpus entry through the MODEL. Returns the recorded
    answer dict, or None on any failure (recorded as unjudgeable)."""
    try:
        p = fen_to_position(e["fen"])
        keys = []
        for uci in e["path"]:
            m = find_move(p, uci)
            p = makeMove(p, m)
            keys.append(compute_key(p))
        legal = sorted(uci_of(m) for m in genLegal(p))
        cur = compute_key(p)
        hist = History(keys, cur)
        status = TWIN_STATE[updateTerminal(p, hist)]
        rep_draw = status == "draw" and countReps(hist) >= 3
        return {"fen": e["targetFen"], "path": e["path"], "ply": e["ply"],
                "phase": e.get("phase"), "legal": legal, "status": status,
                "repDraw": rep_draw}
    except Exception as ex:
        return {"fen": e["targetFen"], "path": e["path"], "ply": e["ply"],
                "phase": e.get("phase"), "kind": "unj",
                "detail": str(ex)[:200]}


# --- perft gate ----------------------------------------------------------

PERFT_CASES = [
    (chess.STARTING_FEN, {1: 20, 2: 400, 3: 8902}),
    ("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
     {1: 48, 2: 2039, 3: 97862}),
    ("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", {1: 14, 2: 191, 3: 2812}),
    ("r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
     {1: 6, 2: 264, 3: 9467}),
    ("rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
     {1: 44, 2: 1486, 3: 62379}),
    ("r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10",
     {1: 46, 2: 2079, 3: 89890}),
]


def perft(p, depth):
    if depth == 0:
        return 1
    return sum(perft(makeMove(p, m), depth - 1) for m in genLegal(p))


def gate_perft():
    for fen, want in PERFT_CASES:
        p = fen_to_position(fen)
        for d in (1, 2, 3):
            got = perft(p, d)
            if got != want[d]:
                raise SystemExit("REFEREE PERFT GATE FAILED: %s d%d = %d "
                                 "(want %d) — refusing to emit answers"
                                 % (fen.split()[0][:16], d, got, want[d]))
    print("referee perft gate: PASSED (standard battery)", flush=True)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("corpus")
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--out", required=True)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args(argv)

    gate_perft()
    data = json.load(open(args.corpus))
    entries = data["entries"]
    done = {}
    if args.resume and os.path.isfile(args.out):
        for line in open(args.out):
            if line.strip():
                try:
                    r = json.loads(line)
                    done[r["fen"]] = r
                except Exception:
                    pass
    todo = [e for e in entries if e["targetFen"] not in done]
    print("referee: %d entries, %d todo" % (len(entries), len(todo)),
          flush=True)
    with mp.Pool(args.jobs) as pool:
        for i, r in enumerate(pool.imap_unordered(referee, todo)):
            with open(args.out, "a") as f:
                f.write(json.dumps(r) + "\n")
            if (i + 1) % 500 == 0:
                print("  referee: %d/%d" % (i + 1, len(todo)), flush=True)
    print("referee pass done -> %s" % args.out)


if __name__ == "__main__":
    main()
