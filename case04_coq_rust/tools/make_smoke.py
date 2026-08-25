#!/usr/bin/env python3
"""Case 04 — public smoke set: 50 SHALLOW positions (paths <= 8 plies) with
oracle answers, disjoint from the hidden corpus (own seed). Both arms get
this for harness wiring."""
import json
import multiprocessing as mp
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))
from corpus_gen import playout  # noqa: E402
from twin_referee import referee  # noqa: E402

import random  # noqa: E402
import chess  # noqa: E402


def build(seed, n=50):
    rng = random.Random(seed)
    entries, seen = [], set()
    while len(entries) < n:
        fenlist, path, _ = playout(rng)
        if not path:
            continue
        for i in range(1, min(8, len(path)) + 1):
            if fenlist[i - 1] in seen:
                continue
            seen.add(fenlist[i - 1])
            entries.append({"fen": chess.STARTING_FEN, "path": path[:i],
                            "ply": i, "targetFen": fenlist[i - 1]})
            if len(entries) >= n:
                break
    return entries


def check(e):
    r = referee(e)
    if r is None or r.get("kind") == "unj":
        return None
    return {"fen": r["fen"], "path": r["path"],
            "legal": r["legal"], "status": r["status"]}


def main():
    entries = build(20260810, 50)
    out = [r for r in (check(e) for e in entries) if r is not None]
    print("smoke set: %d/%d referee-answered" % (len(out), len(entries)))
    dest = os.path.join(os.path.dirname(HERE), "workspace", "smoke")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "smoke.json"), "w") as f:
        json.dump(out, f, indent=1)
    with open(os.path.join(dest, "README.md"), "w") as f:
        f.write("# Public smoke set\n\n50 positions with oracle answers for "
                "harness wiring. Disjoint from the hidden corpus. Answers "
                "reveal nothing the oracle would not sell for a few probes.\n")


if __name__ == "__main__":
    main()
