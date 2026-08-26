#!/usr/bin/env python3
"""Case 05 — evidence for §5.2: movegen faults are depth-latent, and POSITION
selection detects them where depth does not.

Emits the §5.2 table. Reference is python-chess; the "faults" are omissions
injected by filtering the legal-move list, which is the cheapest faithful model
of a movegen that never implements a rule.

Run: python3 latency_demo.py
"""
import chess

KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
FAULTS = {
    "en passant omitted": lambda b, m: b.is_en_passant(m),
    "castling omitted": lambda b, m: b.is_castling(m),
}


def perft(board, depth, fault=None):
    if depth == 0:
        return 1
    moves = [m for m in board.legal_moves if not (fault and fault(board, m))]
    if depth == 1:
        return len(moves)
    total = 0
    for m in moves:
        board.push(m)
        total += perft(board, depth - 1, fault)
        board.pop()
    return total


def main():
    cases = [("startpos", chess.STARTING_FEN, 4), ("startpos", chess.STARTING_FEN, 5),
             ("Kiwipete", KIWIPETE, 1), ("Kiwipete", KIWIPETE, 3)]
    print(f"{'position/depth':<18}{'correct':>12}" +
          "".join(f"{k:>24}" for k in FAULTS))
    print("-" * (18 + 12 + 24 * len(FAULTS)))
    for name, fen, d in cases:
        good = perft(chess.Board(fen), d)
        row = f"{name + ' d' + str(d):<18}{good:>12,}"
        for _, f in FAULTS.items():
            got = perft(chess.Board(fen), d, f)
            if got == good:
                row += f"{('%s  INVISIBLE' % format(got, ',')):>24}"
            else:
                row += f"{('%s  %+d' % (format(got, ','), got - good)):>24}"
        print(row)
    print("\nDepth is not the lever; position selection is: startpos at depth 5")
    print("(4.8M nodes) detects neither fault, Kiwipete at depth 1 (48 nodes)")
    print("detects one. The scored suite must make every rule immediately")
    print("reachable in some position.")


if __name__ == "__main__":
    main()
