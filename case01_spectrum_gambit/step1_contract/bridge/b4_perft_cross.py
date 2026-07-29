#!/usr/bin/env python3
"""
BRIDGE layer 4 — PERFT CROSS-CHECK against the RUNNING Z80 ENGINE.

perft is the standard whole-of-movegen conformance instrument: it counts the
leaves of the legal move tree, so every make/unmake, every castling right,
every e.p. target and every promotion on the way is exercised.  The engine
ships its own perft (perft.inc) and prints the counts on screen; this layer
runs it inside hc91emu, parses the SCREEN, and demands that the twin
reproduce every number.

Three positions come from the engine's own suite:
  kiwipete   d3 — castling + pins on both sides
  enpassant  d4 — the classic e.p. torture position
  promotion  d3 — under-promotion and promotion-with-check

Claim level for this layer: EXHAUSTIVELY-CHECKED over 410,082 leaf nodes of
the real engine's legal-move tree.  It is NOT a refinement proof: perft
compares COUNTS, so two compensating errors on the same subtree would cancel
(recorded as a bridge blind spot in SUMMARY.md; layer b5 closes part of it by
comparing the move LISTS themselves).

`--emu` re-runs the engine (about 2.5 min); without it, the recorded
artifacts/perft_full.txt transcript from the pre-registered run is parsed.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "twin"))

from hc91_twin import perft                                      # noqa: F403
from positions import ENGINE_PERFT                               # noqa: F403

TRANSCRIPT = os.path.join(HERE, "..", "artifacts", "perft_full.txt")


def engine_screen():
    if "--emu" in sys.argv:
        import emu
        txt, _ = emu.run(900000, [("T", 900)])
        with open(TRANSCRIPT, "w") as f:
            f.write(txt)
        return txt
    with open(TRANSCRIPT) as f:
        return f.read()


def parse(txt):
    """Screen -> {(label, depth): count}.  Only lines the engine itself
    marked OK are accepted; a BAD line is a LOUD failure, never ignored."""
    got, bad = {}, []
    for line in txt.splitlines():
        m = re.match(r"\s*perft (\d)\s+(\d+)\s+(OK|BAD)", line)
        if m:
            got[("start", int(m.group(1)))] = int(m.group(2))
            if m.group(3) != "OK":
                bad.append(line.strip())
            continue
        m = re.match(r"\s*(kiwipete|enpassant|promotion) d(\d)\s+(\d+)\s+(OK|BAD)", line)
        if m:
            got[(m.group(1), int(m.group(2)))] = int(m.group(3))
            if m.group(4) != "OK":
                bad.append(line.strip())
    return got, bad


txt = engine_screen()
got, bad = parse(txt)
fails = list("engine reported BAD: " + b for b in bad)

if "PERFT OK" not in txt:
    fails.append("engine did not print its own PERFT OK verdict "
                 "(run is UNJUDGEABLE, not a pass)")

total = 0
for label, pos, depth, expected in ENGINE_PERFT:
    key = (label, depth)
    if key not in got:
        fails.append("%s d%d: engine printed no count" % (label, depth))
        continue
    engine_n = got[key]
    twin_n = perft(pos, depth)
    total += twin_n
    if engine_n != expected:
        fails.append("%s d%d: engine printed %d, pinned expectation %d"
                     % (label, depth, engine_n, expected))
    if twin_n != engine_n:
        fails.append("%s d%d: TWIN %d != ENGINE %d" % (label, depth, twin_n, engine_n))

print("[b4_perft_cross] %d positions, %d leaf nodes cross-checked twin-vs-engine, "
      "%d failures" % (len(ENGINE_PERFT), total, len(fails)))
for f in fails:
    print("  FAIL " + f)
sys.exit(1 if fails else 0)
