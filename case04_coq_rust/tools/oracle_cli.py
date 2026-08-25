#!/usr/bin/env python3
"""Case 04 — oracle CLI. The ONLY access either arm has to the reference engine.

Mechanics (each validated empirically on 2026-08-24, see PILOT.md):

  * Direct FEN injection (tape loader) NEVER populates the ply-0 move buffer
    and never computes terminal status in two-player mode. The engine runs
    updateTerminal only after a COMPLETED MOVE.
  * Therefore legal/status are observed by REPLAY: a path of moves is played
    (two-player mode, fixed frame schedule) and the behaviour is read at the
    final position. The engine's own final FEN must equal the python-chess FEN
    of the same path — byte for byte on the board fields — or the probe is
    UNJUDGEABLE. This check is also the corpus-hygiene rule (C16).
  * Promotions: the engine prompts "Q=Queen R B N" (hardware rows 0xFBFE /
    0x7FFE) and the piece key must arrive in its OWN frame slot, after the
    move's ENTER has settled; the move itself may be typed in the shared slot.
  * Chosen moves (choose): normal-mode injection of a Black-to-move position;
    the engine thinks at the level typed before the load and moves; the move
    is read from the move log tail. Deterministic across repeated runs at
    levels 1-3 (tested).

Query budget (PREREGISTRATION §3 / constraint C14): every probe is counted
per --run-id and refused past --cap. --internal (orchestrator/scorer only)
bypasses the cap and must never be reachable from a run workspace.

Move identity used by scoring: (from, to, promo) with promo decoded from the
flag byte: flag>>4 in 2..5 = N,B,R,Q (twin: promoFlags 0x20,0x30,0x40,0x50);
flag%8 is 0 quiet, 1 double-push, 2 O-O, 3 O-O-O, 4 en-passant — the special
kinds do not change move identity.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
CASE01 = os.path.join(os.path.dirname(LAB), "case01_spectrum_gambit")
HARNESS = os.path.join(CASE01, "arms", "harness")
EMU = os.path.join(HARNESS, "build", "hc91emu")
ROM = os.path.join(HARNESS, "roms", "48.rom")
TAP = os.path.join(CASE01, "sealed", "seedkit", "pristine", "chess.tap")

# Fixed frame schedule — deterministic by construction (case02 charlib).
# GAP=900 is the charlib-validated key-safe margin; smaller GAPs drop
# keystrokes on slower positions (measured: 250 dropped keys at 23-55
# moves, 150 desynced at move 7). 900 burns ~1,044 engine-frames per move
# against INITCLK=15000 (5:00 per side), so a single run dies by flag-fall
# at ~28 plies. Deep paths are therefore replayed in CHUNKS of at most
# CHUNK_PLIES moves, each chunk continuing from the previous chunk's .sna
# with the clocks patched back to 15000: full RAM (including the engine's
# repetition history) survives the boundary, only the clock resets.
# Promotion moves and their piece key stay inside one chunk (the prompt is
# transient).
LOAD_FRAME = 700
WAIT = 200
GAP = 900
TAIL_LEGAL = 1500
TAIL_CHOOSE = 6000
CHUNK_PLIES = 20
A_WCLOCK = 0xE147
A_BCLOCK = 0xE149
INITCLK = 15000

DEFAULT_CAP = 5000
DEFAULT_LEVEL = 1

A_MOVEBUF = 0x6000
A_GENCOUNT = 0xE0A0
A_GAMESTATE = 0xE088
A_MOVELOG = 0xE200
A_MOVELOGN = 0xE15D

STATE_NAME = {0: "play", 1: "white-mated", 2: "black-mated",
              3: "stalemate", 4: "draw", 5: "flag-fall"}
PROMO_PIECE = {2: "n", 3: "b", 4: "r", 5: "q"}


class Snapshot:
    """A 48K .sna: 27-byte header then RAM 0x4000..0xFFFF."""

    def __init__(self, path):
        with open(path, "rb") as f:
            self.raw = f.read()
        if len(self.raw) < 27 + 49152:
            raise ValueError("short .sna: %d bytes" % len(self.raw))

    def byte(self, a):
        return self.raw[27 + (a - 0x4000)]

    def word(self, a):
        return self.byte(a) | (self.byte(a + 1) << 8)


def sqname(s):
    return chr(ord("a") + s % 16) + str(s // 16 + 1)


def decode_move(frm, to, flag):
    return sqname(frm) + sqname(to) + PROMO_PIECE.get(flag >> 4, "")


def read_legal(sn):
    n = sn.byte(A_GENCOUNT)
    moves = []
    for i in range(n):
        frm = sn.byte(A_MOVEBUF + 4 * i)
        to = sn.byte(A_MOVEBUF + 4 * i + 1)
        flag = sn.byte(A_MOVEBUF + 4 * i + 2)
        if not (frm < 128 and frm % 16 < 8 and to < 128 and to % 16 < 8):
            raise RuntimeError("move buffer garbage: %02x->%02x f=%02x"
                               % (frm, to, flag))
        moves.append({"move": decode_move(frm, to, flag),
                      "from": frm, "to": to, "flag": flag,
                      "special": flag % 8, "promo": flag >> 4})
    return n, moves


def chesspos():
    tools = os.path.join(HARNESS, "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    import chesspos
    return chesspos


def patch_clocks(sna_path):
    """Set both clock words back to INITCLK so the next chunk starts with
    a full 5:00 per side. .sna: 27-byte header then RAM 0x4000..0xFFFF."""
    data = bytearray(open(sna_path, "rb").read())
    for a in (A_WCLOCK, A_BCLOCK):
        off = 27 + (a - 0x4000)
        data[off] = INITCLK & 0xFF
        data[off + 1] = (INITCLK >> 8) & 0xFF
    open(sna_path, "wb").write(bytes(data))


def chunk_path(path):
    """Split a move path into segments of <= CHUNK_PLIES moves. A promotion
    move and its piece key must stay in the same chunk, so the cut lands
    after a non-promotion move (at worst the chunk grows by one)."""
    segs, cur = [], []
    for mv in path:
        cur.append(mv)
        if len(cur) >= CHUNK_PLIES and len(mv) != 5:
            segs.append(cur)
            cur = []
    if cur:
        segs.append(cur)
    return segs


def run_segment(boot, moves, save_sna, cursor="e2", load_keys=None):
    """One emulator run: boot `boot` (.tap or .sna), type the schedule,
    snapshot to save_sna. Returns the final cursor square. Raises loudly on
    failure."""
    cp = chesspos()
    cmd = [EMU, "--machine", "48k", "--rom", ROM, boot,
           "--turbo", "--save-sna", save_sna]
    if load_keys:                          # tap boot: autoload + position
        cmd += ["--autoload"]
        cmd += ["--type", "%s@%d" % (load_keys, LOAD_FRAME)]
    frame = LOAD_FRAME + (WAIT if load_keys else WAIT)
    for mv in moves:
        promo = mv[4] if len(mv) == 5 else None
        keys = cp.move_keys([mv[:4]], cursor)
        cmd += ["--type", "%sx@%d" % (keys, frame)]
        cursor = mv[2:4]
        frame += GAP
        if promo:                           # promo key needs its OWN slot
            cmd += ["--type", "%s@%d" % (promo, frame)]
            frame += GAP
    cmd += ["--frames", str(frame + TAIL_LEGAL)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    if r.returncode != 0:
        raise RuntimeError("hc91emu exit %d: %s"
                           % (r.returncode, r.stderr[-500:]))
    if not os.path.isfile(save_sna):
        raise RuntimeError("no snapshot written")
    return cursor


def replay(fen, path):
    """Play `path` from `fen` (two-player mode, fixed schedule, chunked
    through .sna with clock resets); return the decoded state at the final
    position. Raises on any failure (judgability must be loud)."""
    cp = chesspos()
    payload = cp.fen_to_block(fen, 2)
    tapdata = open(TAP, "rb").read() + cp.tap_data_block(payload)
    tmp = tempfile.mkdtemp(prefix="c04oracle.")
    try:
        tap = os.path.join(tmp, "run.tap")
        with open(tap, "wb") as f:
            f.write(tapdata)
        segs = chunk_path(path)
        boot = tap
        load_keys = "vl"
        cursor = "e2"
        sna = None
        for i, seg in enumerate(segs):
            sna = os.path.join(tmp, "chunk%d.sna" % i)
            cursor = run_segment(boot, seg, sna, cursor=cursor,
                                 load_keys=load_keys if i == 0 else None)
            if i < len(segs) - 1:
                patch_clocks(sna)          # next chunk gets a fresh clock
                boot = sna
                load_keys = None
        st = cp.state_dict(cp.sna_ram(sna))
        sn = Snapshot(sna)
        if st["moveLogN"] != len(path):
            raise RuntimeError("path did not land: expected %d moves, got %d "
                               "(%r)" % (len(path), st["moveLogN"],
                                         st["moveLog"]))
        return st, sn
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def choose(fen, level):
    """Normal-mode injection of a Black-to-move position; engine thinks and
    moves; return (state_dict, chosen_move or None)."""
    cp = chesspos()
    payload = cp.fen_to_block(fen, level)
    tapdata = open(TAP, "rb").read() + cp.tap_data_block(payload)
    tmp = tempfile.mkdtemp(prefix="c04oracle.")
    try:
        tap = os.path.join(tmp, "run.tap")
        sna = os.path.join(tmp, "final.sna")
        with open(tap, "wb") as f:
            f.write(tapdata)
        keys = (str(level) if level != 2 else "") + "l"
        cmd = [EMU, "--machine", "48k", "--rom", ROM, tap,
               "--autoload", "--turbo", "--save-sna", sna,
               "--type", "%s@%d" % (keys, LOAD_FRAME),
               "--frames", str(LOAD_FRAME + WAIT + GAP + TAIL_CHOOSE)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        if r.returncode != 0:
            raise RuntimeError("hc91emu exit %d: %s"
                               % (r.returncode, r.stderr[-500:]))
        if not os.path.isfile(sna):
            raise RuntimeError("no snapshot written")
        st = cp.state_dict(cp.sna_ram(sna))
        sn = Snapshot(sna)
        nlog = sn.byte(A_MOVELOGN)
        mv = None
        if nlog > 0:
            frm = sn.byte(A_MOVELOG + 2 * (nlog - 1))
            to = sn.byte(A_MOVELOG + 2 * (nlog - 1) + 1)
            mv = sqname(frm) + sqname(to)
        return st, sn, mv
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def auto_path(target_fen, max_plies=14, max_nodes=300000, seed=20260807):
    """BFS from the start position to `target_fen` (python-chess). Orchestrator
    convenience only: arms may always supply their own --path."""
    import chess
    import random
    board = chess.Board()
    if board.fen() == target_fen:
        return []
    rng = random.Random(seed)
    frontier = [([], board.fen())]
    seen = {board.fen()}
    nodes = 0
    while frontier and nodes < max_nodes:
        path, fen = frontier.pop(0)
        b = chess.Board(fen)
        if len(path) >= max_plies:
            continue
        moves = list(b.legal_moves)
        rng.shuffle(moves)
        for mv in moves:
            nodes += 1
            b.push(mv)
            nf = b.fen()
            if nf == target_fen:
                return path + [mv.uci()]
            if nf not in seen:
                seen.add(nf)
                frontier.append((path + [mv.uci()], nf))
            b.pop()
    raise RuntimeError("no path found within %d plies/%d nodes; "
                       "supply --path" % (max_plies, max_nodes))


def board_part(fen):
    # board + side + castling only. The ep field is EXCLUDED from the
    # judicability check: the engine leaves a stale ep square where
    # python-chess clears it (measured on smoke corpus entries, PILOT
    # 2026-08-24) — that staleness is engine behaviour the clone must
    # replicate, not an injection failure. The legal list still carries
    # whatever ep semantics the engine actually implements.
    return " ".join(fen.split()[:3])


def expect_final_fen(fen, path):
    """python-chess replay of (fen, path) -> final FEN, or loud error.
    The full move string is used (promotion letters are part of the UCI
    encoding; stripping them makes pawns-to-the-last-rank unparseable)."""
    import chess
    b = chess.Board(fen)
    for mv in path or []:
        m = chess.Move.from_uci(mv)
        if m not in b.legal_moves:
            raise RuntimeError("path move %s illegal per python-chess" % mv)
        b.push(m)
    return b.fen()


def probe_legal(fen, path, auto):
    if isinstance(path, str):
        path = path.split(",") if path else []
    if not path and auto:
        path = auto_path(fen)
    expected = expect_final_fen(fen, path)
    st, sn = replay(fen, path or [])
    n, moves = read_legal(sn)
    out = {"layer": "legal", "fen": fen, "path": path,
           "genCount": n, "legal": [m["move"] for m in moves],
           "status": STATE_NAME.get(st.get("gameState"), "?"),
           "gameState": st.get("gameState"),
           "reachedFen": st.get("fen")}
    if board_part(st["fen"]) != board_part(expected):
        raise RuntimeError("replay landed on %s, expected %s"
                           % (st["fen"], expected))
    return out


def probe_status(fen, path, auto):
    return probe_legal(fen, path, auto)


def probe_choose(fen, level):
    st, sn, mv = choose(fen, level)
    return {"layer": "choose", "fen": fen, "level": level,
            "move": mv, "gameState": STATE_NAME.get(st.get("gameState"), "?"),
            "moveLogN": sn.byte(A_MOVELOGN)}


def budget_path(run_id, state_dir):
    return os.path.join(state_dir, "oracle_budget_%s.json" % run_id)


def load_budget(path):
    if os.path.isfile(path):
        return json.load(open(path))
    return {"run_id": None, "count": 0, "probes": []}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", default=os.environ.get("ORACLE_RUN_ID"),
                    help="defaults to $ORACLE_RUN_ID (set by the runner)")
    ap.add_argument("--state-dir", default=os.path.join(LAB, "ledger"))
    ap.add_argument("--cap", type=int, default=DEFAULT_CAP)
    ap.add_argument("--internal", action="store_true",
                    help="orchestrator/scorer use ONLY; bypasses the cap")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("legal", "status"):
        p = sub.add_parser(name)
        p.add_argument("--fen", required=True)
        p.add_argument("--path", default=None)
        p.add_argument("--auto", action="store_true")
    p = sub.add_parser("choose")
    p.add_argument("--fen", required=True)
    p.add_argument("--level", type=int, default=DEFAULT_LEVEL)
    args = ap.parse_args(argv)
    if not args.run_id:
        print(json.dumps({"error": "no --run-id and ORACLE_RUN_ID unset"}))
        return 2

    path = budget_path(args.run_id, args.state_dir)
    budget = load_budget(path)
    if not args.internal and budget["count"] >= args.cap:
        print(json.dumps({"error": "query cap exhausted",
                          "count": budget["count"], "cap": args.cap}))
        return 2
    try:
        if args.cmd in ("legal", "status"):
            out = probe_legal(args.fen, args.path, args.auto)
        else:
            out = probe_choose(args.fen, args.level)
    except Exception as e:
        out = {"error": "UNJUDGEABLE: %s" % e, "fen": args.fen,
               "layer": args.cmd}
    if not args.internal:
        budget["count"] += 1
        budget["run_id"] = args.run_id
        budget["probes"].append({"layer": args.cmd, "fen": args.fen,
                                 "level": getattr(args, "level", None),
                                 "path": getattr(args, "path", None),
                                 "error": out.get("error")})
        os.makedirs(os.path.dirname(path), exist_ok=True)
        json.dump(budget, open(path, "w"), indent=1)
    print(json.dumps(out))
    return 0 if "error" not in out else 1


if __name__ == "__main__":
    sys.exit(main())
