# Blind review packet — bug02

Two independent submissions fixed the SAME reported defect in the same
Z80 codebase. You are not told who wrote them or by what process, and
the two are not necessarily comparable in style. Judge only what is here.

## The reported defect

# bug02 — the game is declared a 50-move draw two moves after a pawn was pushed

**Build under test:** `arms/variants/bug02` — build with `make` (see its
`BUILD.md`). Emulator, drivers and the commands used below: `arms/harness`
(see `HOWTO.md`), 48K machine, `roms/48.rom`.

## Observed

A pawn move does not reset the fifty-move counter, so a game that is nowhere
near a fifty-move draw is declared drawn.

Load a position whose fifty-move counter already stands at 98 half-moves and
push a pawn. The counter goes to **99** instead of back to 0. One more quiet
move and the game ends with the status line

```
Draw (50-move)          SPC=new
```

even though a pawn was pushed two plies earlier.

Conversely, a plain **knight** move *does* reset the counter: from a position
with the counter at 40, `Na1-b3` leaves it at **0**.

Captures reset the counter correctly.

## Repro

```sh
cd arms/harness
make build/hc91emu                       # once

# 1. counter at 98, push a2-a3, read the counter back out of memory
tools/play.py --tap ../variants/bug02/chess.tap \
    --fen '4k3/8/8/8/8/8/PR6/4K3 w - - 98 60' --moves a2a3 --two-player
```

```
halfmove       99            <-- must be 0 after a pawn move
```

```sh
# 2. one more quiet move -> the game is over
tools/play.py --tap ../variants/bug02/chess.tap \
    --fen '4k3/8/8/8/8/8/PR6/4K3 w - - 98 60' --moves 'a2a3,e8e7' --two-player
```

```
Draw (50-move)          SPC=new
gameStateName  draw
halfmove       100
```

```sh
# 3. a knight move wrongly resets it: counter 40 -> 0
tools/play.py --tap ../variants/bug02/chess.tap \
    --fen '4k3/8/8/8/8/8/1R6/N3K3 w - - 40 60' --moves a1b3 --two-player
```

```
halfmove       0             <-- must be 41
```

`--two-player` presses `V` so the engine never moves and both sides are driven
by `--moves`; the FEN's halfmove-clock field is honoured because the game's own
tape-load restores it. Without the helper script:

```sh
cd arms/harness
tools/chesspos.py tap ../variants/bug02/chess.tap /tmp/bug02.tap \
    --fen '4k3/8/8/8/8/8/PR6/4K3 w - - 98 60'
./build/hc91emu --machine 48k --rom roms/48.rom /tmp/bug02.tap --autoload \
    --turbo --type "vl@700" \
    --type "$(tools/chesspos.py keys --cursor e2 a2a3)@820" \
    --frames 2000 --text --save-sna /tmp/bug02.sna
tools/chesspos.py board /tmp/bug02.sna         # halfmove is in there
```

## Expected

The fifty-move counter must be reset to 0 by a pawn move or a capture, and
incremented by everything else, so that:

- position 1 above shows `halfmove 0` after `a2-a3`, and `halfmove 1` after the
  following king move, with the game still running (`Your move`);
- position 3 shows `halfmove 41` after `Na1-b3`;
- the draw still fires when the counter genuinely reaches 100 half-moves — from
  `4k3/8/8/8/8/8/1R6/4K3 w - - 99 60`, one quiet rook move must end the game
  with `Draw (50-move)`.

## Also observed

- The built-in self-test (`T`) passes: `PERFT OK - movegen verified`.
- The initial board renders pixel-identical to `initial_golden.png`.
- Checkmate, stalemate, repetition and insufficient-material draws are reported
  correctly in spot checks; castling, en passant and promotion look normal; the
  engine plays sensibly.
- The counter shown by the FEN in `tools/chesspos.py board` is the game's own
  halfmove clock, so it can be watched directly move by move.


## Submission X — source changes

```diff
--- a/movegen.inc
+++ b/movegen.inc
@@ -903,9 +903,12 @@
         ld a,0xFF
         ld (epSquare),a
 mkHalf:
+        ; fifty-move clock (a specification rule): reset to 0 on a PAWN move or a
+        ; capture, increment on everything else.  `and 7` strips the colour
+        ; bit, so WP covers black pawns too.
         ld a,(mkPiece)
         and 7
-        cp WN
+        cp WP
         jr z,mkHm0
         ld a,(mkCaptured)
         or a

```

## Submission X — tests added

```
--- changes to the accompanying verification package (81386 bytes of diff) ---
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/bridge/a check script SUBMISSION/the the check suite
--- BASELINE/bridge/a check script	2026-07-29 22:35:40.234282768 +0200
+++ SUBMISSION/the the check suite	2026-08-02 08:09:36.253018726 +0200
@@ -130,6 +130,108 @@
 base = obsOf(startPos, mkMove(0x14, 0x34, SP_DPUSH), h0)
 chk("T25_base_conforms", failedClauses(base), [])
 
+# --- §16.8b  C9 as a QUANTIFIED rule over every piece type ----------------
+chk("T26a_clock_rule_all_moves",
+    all((makeMove(clockPos, m).halfmove == 0)
+        == (pcType(bGet(clockPos.board, m.frm)) == WP
+            or bGet(clockPos.board, capSquare(clockPos, m)) != 0)
+        for m in genLegal(clockPos)), True)
+chk("T26b_resets", len([m for m in genLegal(clockPos)
+                        if makeMove(clockPos, m).halfmove == 0]), 5)
+chk("T26b_increments", len([m for m in genLegal(clockPos)
+                            if makeMove(clockPos, m).halfmove == 41]), 35)
+chk("T26b_move_count", len(genLegal(clockPos)), 40)
+chk("T26c_all_piece_types_move",
+    sorted({pcType(bGet(clockPos.board, m.frm)) for m in genLegal(clockPos)}),
+    [WP, WN, WB, WR, WQ, WK])
+chk("T26d_pawn_quiet", makeMove(clockPos, mkMove(0x10, 0x20, 0)).halfmove, 0)
+chk("T26d_pawn_capture", makeMove(clockPos, mkMove(0x10, 0x21, 0)).halfmove, 0)
+chk("T26d_rook_capture", makeMove(clockPos, mkMove(0x07, 0x77, 0)).halfmove, 0)
+chk("T26d_knight_quiet", makeMove(clockPos, mkMove(0x01, 0x22, 0)).halfmove, 41)
+chk("T26d_castling", makeMove(clockPos, mkMove(0x04, 0x06, SP_OO)).halfmove, 41)
+
+chk("T26e_capture_rule_all_moves",
+    all((makeMove(clockCapPos, m).halfmove == 0)
+        == (pcType(bGet(clockCapPos.board, m.frm)) == WP
+            or bGet(clockCapPos.board, capSquare(clockCapPos, m)) != 0)
+        for m in genLegal(clockCapPos)), True)
+chk("T26f_captured_types",
+    sorted({pcType(bGet(clockCapPos.board, capSquare(clockCapPos, m)))
+            for m in genLegal(clockCapPos)
+            if bGet(clockCapPos.board, capSquare(clockCapPos, m)) != 0}),
+    [WP, WN, WB, WR, WQ])
+chk("T26f_nonpawn_takes_pawn",
+    any(pcType(bGet(clockCapPos.board, m.frm)) != WP
+        and pcType(bGet(clockCapPos.board, capSquare(clockCapPos, m))) == WP
+        and bGet(clockCapPos.board, capSquare(clockCapPos, m)) != 0
+        for m in genLegal(clockCapPos)), True)
+chk("T26f_pawn_takes_nonpawn",
+    any(pcType(bGet(clockCapPos.board, m.frm)) == WP
+        and bGet(clockCapPos.board, capSquare(clockCapPos, m)) != 0
+        for m in genLegal(clockCapPos)), True)
+chk("T26f_cap_resets", len([m for m in genLegal(clockCapPos)
+                            if makeMove(clockCapPos, m).halfmove == 0]), 8)
+chk("T26f_cap_increments", len([m for m in genLegal(clockCapPos)
+                                if makeMove(clockCapPos, m).halfmove == 41]), 13)
+chk("T26f_cap_move_count", len(genLegal(clockCapPos)), 21)
+
+# §16.8b — the captured-COLOUR axis (W13) and the byte wrap (T26g)
+chk("T26h_capture_rule_mirrored",
+    all((makeMove(clockCapBlackPos, m).halfmove == 0)
+        == (pcType(bGet(clockCapBlackPos.board, m.frm)) == WP
+            or bGet(clockCapBlackPos.board, capSquare(clockCapBlackPos, m)) != 0)
+        for m in genLegal(clockCapBlackPos)), True)
+chk("T26i_mover_is_black", clockCapBlackPos.stm, BLACK)
+chk("T26i_captured_types",
+    sorted({pcType(bGet(clockCapBlackPos.board, capSquare(clockCapBlackPos, m)))
+            for m in genLegal(clockCapBlackPos)
+            if bGet(clockCapBlackPos.board, capSquare(clockCapBlackPos, m)) != 0}),
+    [WP, WN, WB, WR, WQ])
+chk("T26i_captured_are_white",
+    sorted({pcCol(bGet(clockCapBlackPos.board, capSquare(clockCapBlackPos, m)))
+            for m in genLegal(clockCapBlackPos)
+            if bGet(clockCapBlackPos.board, capSquare(clockCapBlackPos, m)) != 0}),
+    [WHITE])
+chk("T26i_cap_resets", len([m for m in genLegal(clockCapBlackPos)
+                            if makeMove(clockCapBlackPos, m).halfmove == 0]), 8)
+chk("T26i_cap_increments", len([m for m in genLegal(clockCapBlackPos)
+                                if makeMove(clockCapBlackPos, m).halfmove == 41]), 13)
+chk("T26i_cap_move_count", len(genLegal(clockCapBlackPos)), 21)
+
+# T26g — the byte wrap: at 255 an increment also lands on 0 (divergence F7),
+# so T26a/T26e/T26h are statements about pre-clocks < 255.
+chk("T26g_wrap_increment",
+    makeMove(clockPos.replace(halfmove=255), mkMove(0x01, 0x22, 0)).halfmove, 0)
+chk("T26g_no_wrap_at_254",
+    makeMove(clockPos.replace(halfmove=254), mkMove(0x01, 0x22, 0)).halfmove, 255)
+chk("T26g_wrap_reset",
+    makeMove(clockPos.replace(halfmove=255), mkMove(0x10, 0x20, 0)).halfmove, 0)
+
+# --- §16.8c  the bug02 incident (the method law 6) ------------------------------
+_b02 = makeMove(bug02Pos, mkMove(0x10, 0x20, 0))
+chk("T27a_bug02_pawn_resets", _b02.halfmove, 0)
+chk("T27a_bug02_still_play", updateTerminal(_b02, h0), PLAY)
+_b02b = makeMove(_b02, mkMove(0x74, 0x64, 0))
+chk("T27b_bug02_next_ply", _b02b.halfmove, 1)
+chk("T27b_bug02_next_play", updateTerminal(_b02b, h0), PLAY)
+_o99 = obsOf(bug02Pos, mkMove(0x10, 0x20, 0), h0)
+chk("T27c_bug02_trace_fails_C3_C9",
+    failedClauses(_o99.replace(post=_o99.post.replace(halfmove=99))), [2, 8])
+chk("T27d_bug02_knight_increments",
+    makeMove(bug02KnightPos, mkMove(0x00, 0x21, 0)).halfmove, 41)
+_on = obsOf(bug02KnightPos, mkMove(0x00, 0x21, 0), h0)
+chk("T27e_bug02_knight_trace_fails_C3_C9",
+    failedClauses(_on.replace(post=_on.post.replace(halfmove=0))), [2, 8])
+_b50 = makeMove(bug02FiftyPos, mkMove(0x11, 0x21, 0))
+chk("T27f_bug02_draw_clock", _b50.halfmove, 100)
+chk("T27f_bug02_draw_fires", updateTerminal(_b50, h0), DRAW)
+chk("T27f_bug02_draw_is_the_clock", isInsufficient(_b50.board), False)
+chk("T27g_bug02_dpush_resets",
+    makeMove(bug02Pos, mkMove(0x10, 0x30, SP_DPUSH)).halfmove, 0)
+chk("T27g_bug02_pawn_at_99_no_draw",
+    updateTerminal(makeMove(bug02Pos.replace(halfmove=99), mkMove(0x10, 0x20, 0)),
+                   h0), PLAY)
+
 print("[b1_witnesses] %d checks, %d failures" % (N, len(FAILS)))
 for f in FAILS:
     print("  FAIL " + f)
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/bridge/a check script SUBMISSION/the the check suite
--- BASELINE/bridge/a check script	2026-07-29 22:38:58.133777757 +0200
+++ SUBMISSION/the the check suite	2026-08-02 08:09:36.264346356 +0200
@@ -39,13 +39,15 @@
 base = obsOf(startPos, mkMove(0x14, 0x34, SP_DPUSH), h0)
 FAILS, COVERED = [], set()
 NMUT = 0
+NOBS = 0          # Part A (observation) mutations; the rest are Part B
 
 assert failedClauses(base) == [], "baseline must conform"
 
 
 def mut(name, obs, expect_names):
-    global NMUT
+    global NMUT, NOBS
     NMUT += 1
+    NOBS += 1
     got = set(failedClauseNames(obs))
     want = set(expect_names)
     COVERED.update(want)
@@ -101,6 +103,18 @@
     base.replace(post=base.post.replace(halfmove=1)),
     ["a specification rule", "a specification rule"])
 
+# C9 — the bug02 incident, both halves.  A pawn move that leaves the clock
+# at pre+1, and a KNIGHT move that zeroes it: the two directions of the
+# piece-type confusion that shipped in variants/bug02.
+_b02 = obsOf(bug02Pos, mkMove(0x10, 0x20, 0), h0)          # a2-a3, clock 98
+mut("C9/bug02-pawn-not-reset",
+    _b02.replace(post=_b02.post.replace(halfmove=99)),
+    ["a specification rule", "a specification rule"])
+_b02n = obsOf(bug02KnightPos, mkMove(0x00, 0x21, 0), h0)   # Na1-b3, clock 40
+mut("C9/bug02-knight-resets",
+    _b02n.replace(post=_b02n.post.replace(halfmove=0)),
+    ["a specification rule", "a specification rule"])
+
 # C10 + C12 + C13 — a king vanished from the board.
 mut("C10+C13/king-vanished",
     base.replace(post=base.post.replace(board=bSet(base.post.board, 0x74, 0))),
@@ -152,6 +166,29 @@
     sig.append(T.updateTerminal(twoMinorPos, h0))      # the <2 / <=2 boundary
     sig.append(T.updateTerminal(fiftyPos, h0))
     sig.append(T.updateTerminal(fiftyPos.replace(halfmove=99), h0))
+    # the fifty-move CLOCK itself, over every legal move of a position where
+    # all six piece types move and both reset disjuncts are live.  Without
+    # this the bug02 fault (reset selected by the wrong piece type) survives
+    # every other observable in this battery — perft, terminal states and
+    # make/unmake are all clock-blind.
+    sig.append(tuple(T.makeMove(clockPos, m).halfmove for m in T.genLegal(clockPos)))
+    # ... and over a position whose captures range over every CAPTURABLE type
+    # (`mkHalf:` tests two pieces; clockPos only quantifies over the mover —
+    # an review built a "captured PAWN does not reset" engine that
+    # passed everything keyed on clockPos alone).
+    sig.append(tuple(T.makeMove(clockCapPos, m).halfmove
+                     for m in T.genLegal(clockCapPos)))
+    # ... and its MIRROR, so the captured man's COLOUR is observed too
+    # (round 2 of the attack built a "captured WHITE man does not reset"
+    # engine that passed everything keyed on White-to-move witnesses).
+    sig.append(tuple(T.makeMove(clockCapBlackPos, m).halfmove
+                     for m in T.genLegal(clockCapBlackPos)))
+    # the byte wrap at 255 (divergence F7)
+    sig.append(T.makeMove(clockPos.replace(halfmove=255),
+                          T.mkMove(0x01, 0x22, 0)).halfmove)
+    sig.append(T.makeMove(bug02Pos, T.mkMove(0x10, 0x20, 0)).halfmove)
+    sig.append(T.updateTerminal(
+        T.makeMove(bug02FiftyPos, T.mkMove(0x11, 0x21, 0)), h0))
     sig.append(T.mkMove(0x04, 0x06, T.SP_OO) in T.genLegal(castlePos))
     sig.append(T.mkMove(0x04, 0x06, T.SP_OO) in T.genLegal(castleBlockedPos))
     sig.append(T.mkMove(0x44, 0x53, T.SP_EP) in T.genLegal(epPos))
@@ -345,6 +382,56 @@
 _orig_cc = T.clrCastleSq
 seed("rights-never-cleared", *_swap(T, "clrCastleSq", lambda r, s: r))
 
+# B12 — THE bug02 FAULT, seeded in the reference implementation: the fifty-move clock is reset by
+# the wrong piece type (WN instead of WP), exactly as movegen.inc `mkHalf:`
+# did.  Before this layer grew a clock observable the fault SURVIVED the
+# whole battery — that hole is what let bug02 ship.
+_orig_mm12 = T.makeMove
+
+
+def _mm_bug02(p, m):
+    q = _orig_mm12(p, m)
+    cap = T.bGet(p.board, T.capSquare(p, m))
+    hm = 0 if (T.pcType(T.bGet(p.board, m.frm)) == T.WN     # <- WP became WN
+               or cap != 0) else T.w8(p.halfmove + 1)
+    return q.replace(halfmove=hm)
+
+
+seed("clock-reset-on-KNIGHT(bug02)", *_swap(T, "makeMove", _mm_bug02))
+
+# B13 — the neighbouring fault: the clock is never reset at all.
+def _mm_noreset(p, m):
+    return _orig_mm12(p, m).replace(halfmove=T.w8(p.halfmove + 1))
+
+
+seed("clock-never-reset", *_swap(T, "makeMove", _mm_noreset))
+
+
+# B14 — the fault the review round found unpinned: the clock is reset by every
+# capture EXCEPT a captured pawn (the second piece test in `mkHalf:`).
+def _mm_cappawn(p, m):
+    q = _orig_mm12(p, m)
+    cap = T.bGet(p.board, T.capSquare(p, m))
+    reset = (T.pcType(T.bGet(p.board, m.frm)) == T.WP
+             or (cap != 0 and T.pcType(cap) != T.WP))     # <- pawn captures lost
+    return q.replace(halfmove=0 if reset else T.w8(p.halfmove + 1))
+
+
+seed("captured-PAWN-does-not-reset", *_swap(T, "makeMove", _mm_cappawn))
+
+
+# B15 — the axis the SECOND review round found unpinned: the captured man's
+# COLOUR (`mkHalf:` reads `mkCaptured` as a whole byte).
+def _mm_capwhite(p, m):
+    q = _orig_mm12(p, m)
+    cap = T.bGet(p.board, T.capSquare(p, m))
+    reset = (T.pcType(T.bGet(p.board, m.frm)) == T.WP
+             or (cap != 0 and T.pcCol(cap) == T.BLACK))    # <- white captures lost
+    return q.replace(halfmove=0 if reset else T.w8(p.halfmove + 1))
+
+
+seed("captured-WHITE-does-not-reset", *_swap(T, "makeMove", _mm_capwhite))
+
 # B11 — C4's ONLY possible negative test: break unmake and check that the
 # clause itself (not merely the probe signature) goes red.
 def _um_bad(p, u):
@@ -371,7 +458,7 @@
 
 print("[b2_mutations] %d mutations (%d observation + %d implementation), "
       "%d/%d clauses negatively tested, %d failures"
-      % (NMUT, 16, NMUT - 16, len(COVERED), len(clauseNames), len(FAILS)))
+      % (NMUT, NOBS, NMUT - NOBS, len(COVERED), len(clauseNames), len(FAILS)))
 for f in FAILS:
     print("  FAIL " + f)
 sys.exit(1 if FAILS else 0)
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/bridge/a check script SUBMISSION/the the check suite
--- BASELINE/bridge/a check script	2026-07-29 22:47:27.641510760 +0200
+++ SUBMISSION/the the check suite	2026-08-05 01:43:03.595673408 +0200
@@ -8,7 +8,7 @@
 
     genMoves (ordered, with flags) | genLegal (ordered) | in-check |
     evalWhite | gamePhase | isInsufficient | updateTerminal | make/unmake
-    round-trip | perft 1
+    round-trip | perft 1 | the post-move fifty-move CLOCK of every legal move
 
 The corpus is deterministic (seeded), so a failure is reproducible.
 
@@ -77,6 +77,21 @@
     return out
 
 
+# Clock-boundary positions are PINNED rather than sampled.  Widening the
+# generator's own range to 0..255 was tried and rejected: it resamples the
+# whole corpus (promotions 48 -> 24, one of the corpus's 3 mates lost, PLAY
+# 261 -> 103, because ~60% of positions become unconditional fifty-move draws
+# that shadow the other updateTerminal branches) AND leaves
+# the 255 wrap to the luck of the seed (0 hits on some seeds).  Appending a
+# fixed set keeps the original sample and makes the boundary structural.
+WRAP_CLOCKS = (255, 255, 254, 254, 100, 100, 99, 99)
+
+
+def wrap_positions(positions):
+    live = [p for p in positions if genLegal(p)]
+    return [live[i].replace(halfmove=hm) for i, hm in enumerate(WRAP_CLOCKS)]
+
+
 def move_str(m):
     return "%d,%d,%d" % (m.frm, m.dst, m.flag)
 
@@ -94,6 +109,11 @@
         str(updateTe
```

## Submission Y — source changes

```diff
--- a/movegen.inc
+++ b/movegen.inc
@@ -903,11 +903,11 @@
         ld a,0xFF
         ld (epSquare),a
 mkHalf:
-        ld a,(mkPiece)
+        ld a,(mkPiece)           ; mover; "and 7" folds BP..BK onto WP..WK
         and 7
-        cp WN
+        cp WP                    ; a pawn move resets the fifty-move clock
         jr z,mkHm0
-        ld a,(mkCaptured)
+        ld a,(mkCaptured)        ; ...and so does any capture (incl. en passant)
         or a
         jr nz,mkHm0
         ld a,(halfmove)

```

## Submission Y — tests added

```
--- test_fifty_move.py (7462 bytes) ---
#!/usr/bin/env python3
"""test_fifty_move.py — regression test for the fifty-move (halfmove) clock.

Drives the built chess.tap headlessly through the harness emulator from a set
of hand-made positions and checks the halfmove clock after each move.

The rule under test (movegen.inc, label `mkHalf` in `makeMove`):

    a PAWN move or a CAPTURE resets the clock to 0;
    everything else increments it;
    the game is drawn once the clock reaches 100.

The bug this was written for: `mkHalf` compared the mover against `WN`
(knight) instead of `WP` (pawn), so pawn moves incremented the clock and
knight moves reset it -> spurious "Draw (50-move)".

Usage:
    ./test_fifty_move.py                       # tests ./chess.tap
    ./test_fifty_move.py --tap /tmp/other.tap  # tests another build
    ./test_fifty_move.py -v                    # show every case

Exit status 0 if every case passes.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, '..', '..', 'harness'))
# Guess the harness next door; PYTHONPATH still wins, which is how the
# Makefile honours a HARNESS= override.
sys.path.append(os.path.join(HARNESS, 'tools'))
import chesspos                                          # noqa: E402

# name, start FEN, moves, expected halfmove, expected game state, expected
# board placement (FEN field 1) after the moves.
CASES = [
    # --- the reported symptom -------------------------------------------
    ('pawn push resets the clock',
     '4k3/8/8/8/8/8/PR6/4K3 w - - 98 60', 'a2a3', 0, 'play',
     '4k3/8/8/8/8/P7/1R6/4K3'),
    ('pawn push then a quiet move: 1, and the game is still running',
     '4k3/8/8/8/8/8/PR6/4K3 w - - 98 60', 'a2a3,e8e7', 1, 'play',
     '8/4k3/8/8/8/P7/1R6/4K3'),
    ('knight move increments the clock (it must NOT reset it)',
     '4k3/8/8/8/8/8/1R6/N3K3 w - - 40 60', 'a1b3', 41, 'play',
     '4k3/8/8/8/8/1N6/1R6/4K3'),

    # --- the draw must still fire when it is genuinely due ---------------
    ('99 + one quiet move = 100 = Draw (50-move)',
     '4k3/8/8/8/8/8/1R6/4K3 w - - 99 60', 'b2b3', 100, 'draw',
     '4k3/8/8/8/8/1R6/8/4K3'),
    ('98 + one quiet move = 99: not a draw yet (boundary)',
     '4k3/8/8/8/8/8/1R6/4K3 w - - 98 60', 'b2b3', 99, 'play',
     '4k3/8/8/8/8/1R6/8/4K3'),

    # --- every other way a pawn can move --------------------------------
    ('double pawn push resets the clock',
     '4k3/8/8/8/8/8/PR6/4K3 w - - 50 60', 'a2a4', 0, 'play',
     '4k3/8/8/8/P7/8/1R6/4K3'),
    ('pawn capture resets the clock',
     '4k3/8/8/8/8/1p6/P7/R3K3 w - - 40 60', 'a2b3', 0, 'play',
     '4k3/8/8/8/8/1P6/8/R3K3'),
    ('en-passant capture resets the clock',
     '4k3/1p6/8/P7/8/8/1R6/4K3 b - - 40 60', 'b7b5,a5b6', 0, 'play',
     '4k3/8/1P6/8/8/8/1R6/4K3'),
    ('promotion resets the clock',
     '4k3/P7/8/8/8/8/1R6/4K3 w - - 40 60', 'a7a8q', 0, 'play',
     'Q3k3/8/8/8/8/8/1R6/4K3'),
    ('black pawn move resets the clock (piece code 9, not 1)',
     '4k3/p7/8/8/8/8/1R6/4K3 b - - 60 60', 'a7a6', 0, 'play',
     '4k3/8/p7/8/8/8/1R6/4K3'),

    # --- captures by non-pawns still reset ------------------------------
    ('rook takes rook resets the clock',
     '4k3/8/8/8/8/8/1r6/1R2K3 w - - 40 60', 'b1b2', 0, 'play',
     '4k3/8/8/8/8/8/1R6/4K3'),

    # --- everything else increments -------------------------------------
    ('black knight move increments (piece code 10, not 2)',
     '4k3/8/n7/8/8/8/1R6/4K3 b - - 60 60', 'a6b4', 61, 'play',
     '4k3/8/8/8/1n6/8/1R6/4K3'),
    ('king move increments',
     '4k3/8/8/8/8/8/1R6/4K3 w - - 40 60', 'e1e2', 41, 'play',
     '4k3/8/8/8/8/8/1R2K3/8'),
    ('queen move increments',
     '4k3/8/8/8/8/8/8/3QK3 w - - 40 60', 'd1d4', 41, 'play',
     '4k3/8/8/8/3Q4/8/8/4K3'),
    ('castling increments (the king is the mover, nothing is captured)',
     '4k3/8/8/8/8/8/8/4K2R w K - 40 60', 'e1g1', 41, 'play',
     '4k3/8/8/8/8/8/8/5RK1'),
]


def run_case(emu, rom, rom_tap, fen, moves, tmpdir, idx,
             load_frame=700, wait=120, gap=900, tail=900, depth=2):
    """Boot rom_tap, load `fen` through the game's own tape load, play `moves`,
    return the decoded state dict.  Mirrors tools/play.py --two-player."""
    tap = os.path.join(tmpdir, 'pos%d.tap' % idx)
    blk = chesspos.tap_data_block(chesspos.fen_to_block(fen, depth))
    with open(tap, 'wb') as f:
        f.write(open(rom_tap, 'rb').read() + blk)
    sna = os.path.join(tmpdir, 'final%d.sna' % idx)

    cmd = [emu, '--machine', '48k', '--rom', rom, tap,
           '--autoload', '--turbo', '--save-sna', sna]
    frame = load_frame
    cmd += ['--type', 'vl@%d' % frame]        # V = two-player, L = load position
    frame += wait
    cursor = 'e2'
    for mv in [m for m in moves.replace(',', ' ').split() if m]:
        cmd += ['--type', '%sx@%d' % (chesspos.move_keys([mv], cursor), frame)]
        cursor = mv[2:4]
        frame += gap
    cmd += ['--frames', str(frame + tail)]

    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError('emulator failed (%d): %s' % (r.returncode, r.stderr))
    return chesspos.state_dict(chesspos.sna_ram(sna))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tap', default=os.path.join(HERE, 'chess.tap'))
    ap.add_argument('--emu', default=os.path.join(HARNESS, 'build', 'hc91emu'))
    ap.add_argument('--rom', default=os.path.join(HARNESS, 'roms', '48.rom'))
    ap.add_argument('-v', '--verbose', action='store_true')
    a = ap.parse_args(argv)

    for path in (a.tap, a.emu, a.rom):
        if not os.path.exists(path):
            sys.stderr.write('missing: %s\n' % path)
            return 2

    tmpdir = tempfile.mkdtemp(prefix='fifty.')
    failures = []
    for i, (name, fen, moves, want_hm, want_state, want_place) in enumerate(CASES):
        st = run_case(a.emu, a.rom, a.tap, fen, moves, tmpdir, i)
        got_place = st['fen'].split()[0]
        bad = []
        # placement first: it proves the move was actually played, so a
        # halfmove mismatch can never be blamed on a lost keystroke.
        if got_place != want_place:
            bad.append('board %s != %s' % (got_place, want_place))
        if st['halfmove'] != want_hm:
            bad.append('halfmove %d != %d' % (st['halfmove'], want_hm))
        if st['gameStateName'] != want_state:
            bad.append('state %s != %s' % (st['gameStateName'], want_state))
        if bad:
            failures.append((name, fen, moves, bad))
            print('FAIL  %s' % name)
            print('        %s  moves=%s' % (fen, moves))
            for b in bad:
                print('        %s' % b)
        elif a.verbose:
            print('ok    %s (halfmove %d, %s)' % (name, st['halfmove'], st['gameStateName']))

    if failures:
        # keep the tapes and snapshots of a failing run so they can be examined
        print('fifty-move: FAIL - %d/%d cases (artefacts kept in %s)'
              % (len(failures), len(CASES), tmpdir))
        return 1
    shutil.rmtree(tmpdir, ignore_errors=True)
    print('fifty-move: %d/%d OK (pawn/capture reset, everything else '
          'increments, draw at 100)' % (len(CASES), len(CASES)))
    return 0


if __name__ == '__main__':
    sys.exit(main())

```
