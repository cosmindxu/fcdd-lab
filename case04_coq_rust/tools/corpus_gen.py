#!/usr/bin/env python3
"""Case 04 — corpus generator (orchestrator-side only; NEVER shipped to arms).

Samples reachable chess positions by random legal playouts from the start
position (python-chess; every move filtered through `board.legal_moves` —
bare `push` does NOT validate legality, see PILOT E7).

Per playout game, with deterministic quotas:
    1 early position   (plies 1..12)
    2 mid positions    (plies 13..40)
    2 late positions   (plies 41..end)
    up to 2 special positions (legal set contains promotion / en-passant /
                               castling) from anywhere, in addition
    if the game terminates: the terminal position and the one ply before
    it, ALWAYS kept (statuses concentrate there)

Excluded by rule (PILOT E8): the ply-0 start position (the oracle's move
buffer is only observable after a completed move). Entries with paths longer
than MAX_PLIES are excluded.

Each entry is (fen = seed, path = moves to play, ply, phase, flags). The
hidden answers (legal set, status) are NOT stored here — the scorer computes
them against the live oracle and seals them separately.
"""
import argparse
import json
import random

import chess

MAX_PLIES = 150
GAME_CAP = 250


def playout(rng, check_bias=0.0):
    """Random legal playout. With probability check_bias per move, the
    move is chosen uniformly among CHECKING moves when any exist (random
    play almost never delivers mate/stalemate, and a rules corpus without
    terminal statuses cannot exercise mate detection)."""
    b = chess.Board()
    path, fenlist = [], []
    while not b.is_game_over() and len(path) < GAME_CAP:
        moves = list(b.legal_moves)
        if check_bias and rng.random() < check_bias:
            checks = [m for m in moves if b.gives_check(m)]
            if checks:
                moves = checks
        mv = rng.choice(moves)
        b.push(mv)
        path.append(mv.uci())
        fenlist.append(b.fen())
    return fenlist, path, b.is_game_over()


def has_special(board):
    for mv in board.legal_moves:
        if mv.promotion or board.is_en_passant(mv) or board.is_castling(mv):
            return True
    return False


def pick(rng, pool):
    return rng.choice(pool) if pool else None


def stalemate_playout(rng):
    """A playout whose mover minimises the opponent's mobility (ties broken
    randomly) — the mechanism by which real games stalemate: trade down,
    then corner the bare king without mating it. Returns the stalemate
    position's (fen, path) or (None, None) if none occurred."""
    b = chess.Board()
    path = []
    while not b.is_game_over() and len(path) < GAME_CAP:
        moves = list(b.legal_moves)
        best, best_n = [], 10 ** 9
        for mv in moves:
            b.push(mv)
            n = b.legal_moves.count()
            b.pop()
            if n < best_n:
                best, best_n = [mv], n
            elif n == best_n:
                best.append(mv)
        mv = rng.choice(best)
        b.push(mv)
        path.append(mv.uci())
        if b.is_stalemate():
            return b.fen(), path
    return None, None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=1200)
    ap.add_argument("--seed", type=int, default=20260807)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-target", type=int, default=12000)
    ap.add_argument("--check-bias", type=float, default=0.5,
                    help="probability per move of choosing among checking "
                         "moves; brings mates/stalemates into random play")
    ap.add_argument("--hunt", type=int, default=300,
                    help="stalemate-hunt stratum size")
    args = ap.parse_args(argv)

    rng = random.Random(args.seed)
    entries, seen = [], set()
    n_games = n_term = 0

    while n_games < args.games and len(entries) < args.n_target:
        n_games += 1
        fenlist, path, over = playout(rng, check_bias=args.check_bias)
        if not path:
            continue
        if over:
            n_term += 1
        early = [i for i in range(1, min(12, len(path)) + 1)]
        mid = [i for i in range(13, min(40, len(path)) + 1)]
        late = [i for i in range(41, len(path) + 1)]
        special = [i for i in range(1, len(path) + 1)
                   if has_special(chess.Board(fenlist[i - 1]))]
        picks = []
        for pool in (early, mid, mid, late, late):
            i = pick(rng, pool)
            if i is not None:
                picks.append((i, "early" if pool is early else
                                 ("mid" if pool is mid else "late"), 0))
        for i in rng.sample(special, min(2, len(special))) if special else []:
            picks.append((i, "special", 1))
        if over:
            picks.append((len(path), "terminal", 2))
            if len(path) > 1:
                picks.append((len(path) - 1, "preTerminal", 2))
        for i, phase, _ in picks:
            fen = fenlist[i - 1]
            if fen in seen or i > MAX_PLIES or i < 1:
                continue
            seen.add(fen)
            entries.append({
                "fen": chess.STARTING_FEN, "path": path[:i], "ply": i,
                "phase": phase, "special": phase == "special",
                "targetFen": fen})
    # stalemate-hunt stratum: mobility-minimising playouts (random play and
    # check-biased play almost never stalemate; a rules corpus without
    # stalemate statuses cannot exercise that branch of updateTerminal).
    n_hunted = 0
    while n_hunted < args.hunt and n_games < args.games + 2000:
        n_games += 1
        fen, path = stalemate_playout(rng)
        if fen is None or not path:
            continue
        if fen in seen or len(path) > MAX_PLIES or len(path) < 2:
            continue
        seen.add(fen)
        entries.append({
            "fen": chess.STARTING_FEN, "path": path, "ply": len(path),
            "phase": "terminal", "special": False, "targetFen": fen})
        parent = path[:-1]
        if len(parent) >= 1:
            pb = chess.Board()
            for m in parent:
                pb.push(chess.Move.from_uci(m))
            pfen = pb.fen()
            if pfen not in seen:
                seen.add(pfen)
                entries.append({
                    "fen": chess.STARTING_FEN, "path": parent,
                    "ply": len(parent), "phase": "preTerminal",
                    "special": False, "targetFen": pfen})
        n_hunted += 1
        if n_hunted % 10 == 0:
            print("  stalemate-hunt: %d found" % n_hunted, flush=True)
    with open(args.out, "w") as f:
        json.dump({"seed": args.seed, "games": n_games,
                   "entries": entries}, f, indent=1)
    phases = {}
    plies = []
    for e in entries:
        phases[e["phase"]] = phases.get(e["phase"], 0) + 1
        plies.append(e["ply"])
    print("games=%d entries=%d terminalGames=%d phases=%s"
          % (n_games, len(entries), n_term, phases))
    print("ply quantiles:", sorted(plies)[len(plies)//4::len(plies)//4][:5])


if __name__ == "__main__":
    main()
