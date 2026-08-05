# Blind review packet — bug03

Two independent submissions fixed the SAME reported defect in the same
Z80 codebase. You are not told who wrote them or by what process, and
the two are not necessarily comparable in style. Judge only what is here.

## The reported defect

# bug03 — promoting to a rook gives a queen, and promoting to a knight gives a bishop

**Build under test:** `arms/variants/bug03` — build with `make` (see its
`BUILD.md`). Emulator, drivers and the commands used below: `arms/harness`
(see `HOWTO.md`), 48K machine, `roms/48.rom`.

## Observed

The promotion chooser prompts as documented (`Q`/`R`/`B`/`N`), accepts the key,
and then puts the **wrong piece** on the board for two of the four choices:

| chosen at the prompt | piece that appears | material on the board |
|----------------------|--------------------|-----------------------|
| Q                    | queen (correct)    | 900                   |
| **R**                | **queen**          | **900** (should be 500) |
| B                    | bishop (correct)   | 330                   |
| **N**                | **bishop**         | **330** (should be 320) |

Both colours are affected. It is not a display problem: the promoted piece
behaves as the wrong piece from then on, and the `Matl` readout and the board
memory agree that it *is* the wrong piece.

With a white pawn on a7 and the a8 square empty, promoting and pressing `R`
leaves the board as

```
Q3k3/8/8/8/8/8/8/4K3 b - - 0 1        (expected R3k3/8/8/8/8/8/8/4K3)
```

The engine's own promotions look right only because it prefers a queen anyway.

## Repro

```sh
cd arms/harness
make build/hc91emu                       # once

# promote a7-a8 and press R at the prompt
tools/play.py --tap ../variants/bug03/chess.tap \
    --fen '4k3/P7/8/8/8/8/8/4K3 w - - 0 1' --moves a7a8r --two-player
```

```
fen            Q3k3/8/8/8/8/8/8/4K3 b - - 0 1     <-- a queen, not a rook
material       900                                <-- must be 500
```

```sh
# ... and N at the prompt
tools/play.py --tap ../variants/bug03/chess.tap \
    --fen '4k3/P7/8/8/8/8/8/4K3 w - - 0 1' --moves a7a8n --two-player
#   fen  B3k3/...   material 330      <-- a bishop, not a knight (320)

# a black pawn promoting on a1, choosing R
tools/play.py --tap ../variants/bug03/chess.tap \
    --fen '4k3/8/8/8/8/8/p7/4K3 b - - 0 1' --moves a2a1r --two-player
#   material -900                     <-- must be -500

# controls: Q and B give the right piece
tools/play.py --tap ../variants/bug03/chess.tap \
    --fen '4k3/P7/8/8/8/8/8/4K3 w - - 0 1' --moves a7a8q --two-player   # 900 ok
tools/play.py --tap ../variants/bug03/chess.tap \
    --fen '4k3/P7/8/8/8/8/8/4K3 w - - 0 1' --moves a7a8b --two-player   # 330 ok
```

In `--moves`, a fifth character is the key pressed at the promotion prompt
(`a7a8r` = play a7-a8, press `R`). `--two-player` presses `V` first so the
engine never moves. Without the helper script the keystrokes are: `v`, `l`
(load the position block appended to the tape), cursor keys to a7, `ENTER`,
cursor keys to a8, `ENTER`, then `r`:

```sh
cd arms/harness
tools/chesspos.py tap ../variants/bug03/chess.tap /tmp/bug03.tap \
    --fen '4k3/P7/8/8/8/8/8/4K3 w - - 0 1'
./build/hc91emu --machine 48k --rom roms/48.rom /tmp/bug03.tap --autoload \
    --turbo --type "vl@700" \
    --type "$(tools/chesspos.py keys --cursor e2 a7a8r)@820" \
    --frames 2200 --text --save-sna /tmp/bug03.sna
tools/chesspos.py board /tmp/bug03.sna
```

## Expected

The piece chosen at the prompt is the piece that appears — a rook for `R`
(material 500 for White, -500 for Black) and a knight for `N` (320 / -320) —
for both colours, whether the promotion is a plain push or a capture on the
last rank.

## Also observed

- The built-in self-test (`T`) does **not** pass on this build:

  ```
  perft 1  20         OK
  perft 2  400        OK
  perft 3  8902       OK
  perft 4  197281     OK
  kiwipete d3  97862    OK
  enpassant d4 43238    OK
  promotion d3 62603    BAD
  incr key/phase/pst    BAD
  PERFT BAD - movegen error
  ```

  (the canonical count for that position at depth 3 is 62379).
- The initial board renders pixel-identical to `initial_golden.png`.
- Castling, en passant, check/mate/stalemate detection, the draw rules and the
  engine's search all behave normally in spot checks.


## Submission X — source changes

```diff
--- a/movegen.inc
+++ b/movegen.inc
@@ -798,9 +798,9 @@
         or a
         jr z,mkNoProm
         ld b,a
-        ld a,(mkPiece)
-        or b
-        jr mkPut
+        ld a,(mkSide)            ; COLOUR BIT ONLY — never (mkPiece): the pawn
+        or b                     ; is WP=1/BP=9, so OR-ing the whole piece
+        jr mkPut                 ; leaves type bit 0 set and turns R->Q, N->B
 mkNoProm:
         ld a,(mkPiece)
 mkPut:

```

## Submission X — tests added

```
--- changes to the accompanying verification package (52662 bytes of diff) ---
Only in SUBMISSION/specification/artifacts: perft_full.tapmd5
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/bridge/a check script SUBMISSION/the the check suite
--- BASELINE/bridge/a check script	2026-07-29 22:35:40.234282768 +0200
+++ SUBMISSION/the the check suite	2026-08-05 02:08:45.671541379 +0200
@@ -70,6 +70,25 @@
 for nm, fl in (("Q", 0x50), ("R", 0x40), ("B", 0x30), ("N", 0x20)):
     chk("T11_promo_" + nm, mkMove(0x61, 0x71, fl) in genLegal(promoPos), True)
 
+# T11e..T11r — GENERATING all four flags is not the same as HONOURING them.
+# bug03 generated the four records correctly and placed the wrong piece for
+# two of them, so every check above was true on the broken build.
+chk("T18_bPromo_is_the_mirror", bPromoPos == mirrorPos(promoPos), True)
+for nm, fl, ty in (("Q", 0x50, WQ), ("R", 0x40, WR), ("B", 0x30, WB), ("N", 0x20, WN)):
+    chk("T11_places_" + nm,
+        bGet(makeMove(promoPos, mkMove(0x61, 0x71, fl)).board, 0x71), ty)
+    chk("T11_cap_places_" + nm,
+        bGet(makeMove(promoPos, mkMove(0x61, 0x70, fl)).board, 0x70), ty)
+for nm, fl, ty in (("Q", 0x50, BQ), ("R", 0x40, BR), ("B", 0x30, BB), ("N", 0x20, BN)):
+    chk("T11_black_places_" + nm,
+        bGet(makeMove(bPromoPos, mkMove(0x11, 0x01, fl)).board, 0x01), ty)
+chk("T11q_R_ne_Q",
+    makeMove(promoPos, mkMove(0x61, 0x71, 0x40))
+    == makeMove(promoPos, mkMove(0x61, 0x71, 0x50)), False)
+chk("T11r_N_ne_B",
+    makeMove(promoPos, mkMove(0x61, 0x71, 0x20))
+    == makeMove(promoPos, mkMove(0x61, 0x71, 0x30)), False)
+
 # --- §16.3  make/unmake involution ---------------------------------------
 def roundTrips(p, m):
     return unmakeMove(makeMove(p, m), undoOf(p, m)) == p
@@ -130,6 +149,70 @@
 base = obsOf(startPos, mkMove(0x14, 0x34, SP_DPUSH), h0)
 chk("T25_base_conforms", failedClauses(base), [])
 
+
+# --- §16.8b  bug03 encoded as a regression witness (the method Law 6) -----------
+# `makeMove` built the promoted piece as `mkPiece | promoType` instead of
+# `mkSide | promoType`, so the pawn's own type bit 0 survived.
+def bug03Post(p, m):
+    q = makeMove(p, m)
+    return q.replace(board=bSet(q.board, m.dst,
+                                orB(bGet(p.board, m.frm), mvPromo(m))))
+
+
+def bug03Obs(p, m, h):
+    q = bug03Post(p, m)
+    return Obs(p, m, q, h, updateTerminal(q, h))
+
+
+chk("T26a_bug03_R_gives_Q",
+    bGet(bug03Post(promoPos, mkMove(0x61, 0x71, 0x40)).board, 0x71), WQ)
+chk("T26b_bug03_N_gives_B",
+    bGet(bug03Post(promoPos, mkMove(0x61, 0x71, 0x20)).board, 0x71), WB)
+chk("T26c_bug03_black_R_gives_Q",
+    bGet(bug03Post(bPromoPos, mkMove(0x11, 0x01, 0x40)).board, 0x01), BQ)
+chk("T26d_bug03_black_N_gives_B",
+    bGet(bug03Post(bPromoPos, mkMove(0x11, 0x01, 0x20)).board, 0x01), BB)
+# why it hid: Q and B are bit-for-bit unaffected
+chk("T26e_bug03_Q_unaffected",
+    bug03Post(promoPos, mkMove(0x61, 0x71, 0x50))
+    == makeMove(promoPos, mkMove(0x61, 0x71, 0x50)), True)
+chk("T26f_bug03_B_unaffected",
+    bug03Post(promoPos, mkMove(0x61, 0x71, 0x30))
+    == makeMove(promoPos, mkMove(0x61, 0x71, 0x30)), True)
+# THE REGRESSION CHECK: the incident trace fails EXACTLY C3 and C14
+for nm, p, frm, dst, fl in (("R", promoPos, 0x61, 0x71, 0x40),
+                            ("N", promoPos, 0x61, 0x71, 0x20),
+                            ("capR", promoPos, 0x61, 0x70, 0x40),
+                            ("blackR", bPromoPos, 0x11, 0x01, 0x40),
+                            ("blackN", bPromoPos, 0x11, 0x01, 0x20)):
+    chk("T26g_bug03_%s_fails_C3_C14" % nm,
+        failedClauses(bug03Obs(p, mkMove(frm, dst, fl), h0)), [2, 13])
+
+
+# The clause as it stood BEFORE bug03 — kept here to prove the strengthening
+# is load-bearing rather than decorative.
+def a specification rule03(o):
+    if mvPromo(o.mv) == 0:
+        return True
+    pc = bGet(o.post.board, o.mv.dst)
+    return (pcCol(pc) == pcCol(bGet(o.pre.board, o.mv.frm))
+            and 2 <= pcType(pc) <= 5)
+
+
+_inc = bug03Obs(promoPos, mkMove(0x61, 0x71, 0x40), h0)
+chk("T26l_old_clause_missed_it", a specification rule03(_inc), True)
+chk("T26m_new_clause_catches_it", a specification rule(_inc), False)
+chk("T26n_old_clause_missed_black",
+    a specification rule03(bug03Obs(bPromoPos, mkMove(0x11, 0x01, 0x20), h0)), True)
+# ... and it did not over-forbid: every honest promotion still conforms
+for nm, p, frm, dst in (("push", promoPos, 0x61, 0x71),
+                        ("cap", promoPos, 0x61, 0x70),
+                        ("black-push", bPromoPos, 0x11, 0x01),
+                        ("black-cap", bPromoPos, 0x11, 0x00)):
+    chk("T26o_correct_%s_conform" % nm,
+        all(Conforming(obsOf(p, mkMove(frm, dst, fl), h0))
+            for fl in (0x50, 0x40, 0x30, 0x20)), True)
+
 print("[b1_witnesses] %d checks, %d failures" % (N, len(FAILS)))
 for f in FAILS:
     print("  FAIL " + f)
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/bridge/a check script SUBMISSION/the the check suite
--- BASELINE/bridge/a check script	2026-07-29 22:38:58.133777757 +0200
+++ SUBMISSION/the the check suite	2026-08-05 02:10:12.639071305 +0200
@@ -39,13 +39,15 @@
 base = obsOf(startPos, mkMove(0x14, 0x34, SP_DPUSH), h0)
 FAILS, COVERED = [], set()
 NMUT = 0
+NOBS = 0            # Part A count, derived — never a hard-coded literal
 
 assert failedClauses(base) == [], "baseline must conform"
 
 
 def mut(name, obs, expect_names):
-    global NMUT
+    global NMUT, NOBS
     NMUT += 1
+    NOBS += 1
     got = set(failedClauseNames(obs))
     want = set(expect_names)
     COVERED.update(want)
@@ -133,6 +135,19 @@
     _pro.replace(post=_pro.post.replace(board=bSet(_pro.post.board, 0x71, WK))),
     ["a specification rule", "a specification rule", "a specification rule"])
 
+# C14 — promotion produced the WRONG TYPE, right colour, still inside 2..5:
+# bug03 exactly (chose R, got a queen).  Before C14 was strengthened this
+# tripped ONLY the catch-all C3 — the promotion clause could not name it.
+_proR = obsOf(promoPos, mkMove(0x61, 0x71, 0x40), h0)          # R chosen
+mut("C14/promoted-wrong-type-R",
+    _proR.replace(post=_proR.post.replace(board=bSet(_proR.post.board, 0x71, WQ))),
+    ["a specification rule", "a specification rule"])
+# ... and N -> B, the other half of the reported table, for BLACK.
+_bproN = obsOf(bPromoPos, mkMove(0x11, 0x01, 0x20), h0)        # N chosen
+mut("C14/promoted-wrong-type-N-black",
+    _bproN.replace(post=_bproN.post.replace(board=bSet(_bproN.post.board, 0x01, BB))),
+    ["a specification rule", "a specification rule"])
+
 # ------------------------------------------- Part B: implementation ------
 
 def probe():
@@ -165,6 +180,19 @@
     # ... and a BLACK promotion must keep the colour bit
     sig.append(T.bGet(T.makeMove(bPromoPos, T.mkMove(0x11, 0x01, 0x50)).board, 0x01))
     sig.append(T.perft(bPromoPos, 2))
+    # ... and it must place the piece the flag ASKED for, for ALL FOUR types,
+    # push and capture, both colours.  Sampling only the QUEEN left bug03
+    # invisible to this battery: R->Q and N->B change no perft count at
+    # depth 2 here (a rook and a queen on b8 both check g8 along rank 8),
+    # so a queen-only probe is a coverage hole, not a shortcut.
+    for _fl in (0x50, 0x40, 0x30, 0x20):
+        sig.append(T.bGet(T.makeMove(promoPos, T.mkMove(0x61, 0x71, _fl)).board, 0x71))
+        sig.append(T.bGet(T.makeMove(promoPos, T.mkMove(0x61, 0x70, _fl)).board, 0x70))
+        sig.append(T.bGet(T.makeMove(bPromoPos, T.mkMove(0x11, 0x01, _fl)).board, 0x01))
+        sig.append(T.bGet(T.makeMove(bPromoPos, T.mkMove(0x11, 0x00, _fl)).board, 0x00))
+        # ... and the specification itself must accept each of them
+        sig.append(T.Conforming(T.obsOf(promoPos, T.mkMove(0x61, 0x71, _fl), h0)))
+        sig.append(T.Conforming(T.obsOf(bPromoPos, T.mkMove(0x11, 0x01, _fl), h0)))
     sig.append(all(T.unmakeMove(T.makeMove(p, m), T.undoOf(p, m)) == p
                    for p in (startPos, castlePos, promoPos, epPos, kiwiPos)
                    for m in T.genLegal(p)))
@@ -328,6 +356,20 @@
 
 seed("promo-drops-colour-bit", *_swap(T, "makeMove", _mm_bad))
 
+# B8b — bug03 ITSELF, transcribed into the reference implementation: the promoted piece is built
+# by OR-ing the promotion type into the whole PAWN (WP=1 / BP=9) instead of
+# into the colour bit, so type bit 0 survives and R->Q, N->B.  This is the
+# seeded fault whose survival would mean the bug could come back unnoticed.
+def _mm_bug03(p, m):
+    q = _orig_mm(p, m)
+    if T.mvPromo(m) != 0:
+        q = q.replace(board=T.bSet(q.board, m.dst,
+                                   T.orB(T.bGet(p.board, m.frm), T.mvPromo(m))))
+    return q
+
+
+seed("promo-ORs-the-pawn(bug03)", *_swap(T, "makeMove", _mm_bug03))
+
 # B9 — eval loses its colour symmetry (bishop pair scored for both sides).
 _orig_ev = T.evalWhite
 
@@ -371,7 +413,7 @@
 
 print("[b2_mutations] %d mutations (%d observation + %d implementation), "
       "%d/%d clauses negatively tested, %d failures"
-      % (NMUT, 16, NMUT - 16, len(COVERED), len(clauseNames), len(FAILS)))
+      % (NMUT, NOBS, NMUT - NOBS, len(COVERED), len(clauseNames), len(FAILS)))
 for f in FAILS:
     print("  FAIL " + f)
 sys.exit(1 if FAILS else 0)
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/bridge/a check script SUBMISSION/the the check suite
--- BASELINE/bridge/a check script	2026-07-29 22:49:05.888097955 +0200
+++ SUBMISSION/the the check suite	2026-08-05 02:13:34.983392320 +0200
@@ -20,9 +20,15 @@
 (recorded as a bridge blind spot in SUMMARY.md; layer b5 closes part of it by
 comparing the move LISTS themselves).
 
-`--emu` re-runs the engine (about 2.5 min); without it, the recorded
-artifacts/perft_full.txt transcript from the pre-registered run is parsed.
+`--emu` re-runs the engine (about 2.5 min) and re-records the transcript;
+`run_all.sh` passes it, so THE GATE always exercises the live build.  Without
+it the recorded artifacts/perft_full.txt is parsed instead — and that path is
+now guarded: the transcript is stamped with the md5 of the tape it came from,
+and a stamp that does not match the build under test is a LOUD failure, not a
+quiet pass.  (bug03 shipped a broken tape past a green gate partly because
+this layer read a transcript recorded from a different binary.)
 """
+import hashlib
 import os
 import re
 import sys
@@ -31,19 +37,39 @@
 sys.path.insert(0, HERE)
 sys.path.insert(0, os.path.join(HERE, "..", "reference implementation"))
 
+import emu                                                       # noqa: E402
 from reference implementation import perft                                      # noqa: F403
 from positions import ENGINE_PERFT                               # noqa: F403
 
 TRANSCRIPT = os.path.join(HERE, "..", "artifacts", "perft_full.txt")
+STAMP = os.path.join(HERE, "..", "artifacts", "perft_full.tapmd5")
+
+STALE = []
+
+
+def tap_md5():
+    with open(os.path.abspath(emu.TAP), "rb") as f:
+        return hashlib.md5(f.read()).hexdigest()
 
 
 def engine_screen():
     if "--emu" in sys.argv:
-        import emu
         txt, _ = emu.run(900000, [("T", 900)])
         with open(TRANSCRIPT, "w") as f:
             f.write(txt)
+        with open(STAMP, "w") as f:
+            f.write("%s  %s\n" % (tap_md5(), os.path.abspath(emu.TAP)))
         return txt
+    # recorded path: PROVE the transcript belongs to the build under test
+    want = tap_md5()
+    got = None
+    if os.path.exists(STAMP):
+        with open(STAMP) as f:
+            got = f.read().split()[0]
+    if got != want:
+        STALE.append("recorded transcript is stale: it was produced from tape "
+                     "md5 %s, the build under test is %s — re-run with --emu"
+                     % (got, want))
     with open(TRANSCRIPT) as f:
         return f.read()
 
@@ -69,7 +95,7 @@
 
 txt = engine_screen()
 got, bad = parse(txt)
-fails = list("engine reported BAD: " + b for b in bad)
+fails = list(STALE) + list("engine reported BAD: " + b for b in bad)
 
 if "PERFT OK" not in txt:
     fails.append("engine did not print its own PERFT OK verdict "
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/bridge/a check script SUBMISSION/the the check suite
--- BASELINE/bridge/a check script	2026-07-29 22:59:13.374886388 +0200
+++ SUBMISSION/the the check suite	2026-08-05 02:14:22.451737613 +0200
@@ -190,7 +190,10 @@
 #       loop's updateTerminal does.  A forced repetition therefore scores as
 #       whatever the static eval says, not as 0.
 # =====================================================================
-src = open("/media/sf_Projects/HC91_emulator/chess/engine.inc").read()
+# The SOURCE of the build under test, resolved relative to this package so it
+# tracks emu.TAP rather than a hard-coded absolute path.
+SRCDIR = os.path.join(HERE, "..", "..", "variants", "bug03")
+src = open(os.path.join(SRCDIR, "engine.inc")).read()
 ok("countReps" not in src, "F11: engine.inc now mentions countReps")
 ok("halfmove" not in src, "F11: engine.inc now mentions halfmove")
 EVID.append("F11 engine.inc (negamax + quiesce) contains no reference to "
Only in SUBMISSION/specification/bridge: a check script
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/bridge/emu.py SUBMISSION/the the check suite
--- BASELINE/bridge/emu.py	2026-07-29 22:44:14.362471728 +0200
+++ SUBMISSION/the the check suite	2026-08-05 01:56:46.182916701 +0200
@@ -20,10 +20,23 @@
 import subprocess
 import tempfile
 
-EMU = "/media/sf_Projects/HC91_emulator/build/hc91emu"
-ROM = "/media/sf_Projects/HC91_emulator/roms/48.rom"
-TAP = os.path.join(os.path.dirname(os.path.abspath(__file__)),
-                   "..", "artifacts", "chess.tap")
+_HERE = os.path.dirname(os.path.abspath(__file__))
+_WS = os.path.join(_HERE, "..", "..")
```

## Submission Y — source changes

```diff
--- a/movegen.inc
+++ b/movegen.inc
@@ -797,10 +797,11 @@
         ld a,(mkPromo)
         or a
         jr z,mkNoProm
-        ld b,a
+        ld b,a                   ; B = promoted type (2=N 3=B 4=R 5=Q)
         ld a,(mkPiece)
-        or b
-        jr mkPut
+        and COLBIT               ; colour only: the moving pawn's type bits
+        or b                     ; must not leak in (P|R would read as Q,
+        jr mkPut                 ; P|N as B).  Same form as keyUpdate/pstDelta.
 mkNoProm:
         ld a,(mkPiece)
 mkPut:

```

## Submission Y — tests added

```
--- test_promotion.py (6411 bytes) ---
#!/usr/bin/env python3
"""test_promotion.py — regression test for the promotion piece chooser.

The piece the player picks at the `Promote: Q=Queen R B N` prompt must be the
piece that actually lands on the last rank — for both colours, for a plain
push and for a capture, and it must then *behave* as that piece.

This is the test for bug03: `makeMove` built the promoted piece as
`movingPiece OR promoType` instead of `colourBit OR promoType`, so the pawn's
own type bit (bit0 of WP=1 / BP=9) leaked in and turned R(4) into 5=Q and
N(2) into 3=B.  Q(5) and B(3) already have bit0 set and so looked fine, which
is why only two of the four choices were visibly broken.

Each case boots the build under test in the harness emulator, loads a position
through the game's own tape-load, plays the move with the promotion key, and
reads the resulting board straight out of the 48K memory image.

    ./test_promotion.py                          # ./chess.tap on 48k
    ./test_promotion.py --machine 48k,hc128
    ./test_promotion.py --tap /tmp/other/chess.tap

Exit status 0 iff every case passes.
"""

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# material scores the engine reports, white-positive
QUEEN, ROOK, BISHOP, KNIGHT, PAWN = 900, 500, 330, 320, 100

WPUSH = '4k3/P7/8/8/8/8/8/4K3 w - - 0 1'      # white pawn a7, a8 empty
BPUSH = '4k3/8/8/8/8/8/p7/4K3 b - - 0 1'      # black pawn a2, a1 empty
WCAP = 'r3k3/1P6/8/8/8/8/8/4K3 w - - 0 1'     # white b7 takes the rook on a8
BCAP = '4k3/8/8/8/8/8/1p6/R3K3 b - - 0 1'     # black b2 takes the rook on a1
# a7/h7 pawns with the black king off the 8th rank and off the a-file, so a
# promotion on a8 gives no check and the follow-up moves are playable.
BEHAVE = '8/P6p/4k3/8/8/8/8/4K3 w - - 0 1'

# name, start fen, moves, expected board placement, expected material,
# expected side to move at the end
CASES = [
    # --- plain push, White: the four choices must give the four pieces -----
    ('white push =Q', WPUSH, 'a7a8q', 'Q3k3/8/8/8/8/8/8/4K3', QUEEN, 'black'),
    ('white push =R', WPUSH, 'a7a8r', 'R3k3/8/8/8/8/8/8/4K3', ROOK, 'black'),
    ('white push =B', WPUSH, 'a7a8b', 'B3k3/8/8/8/8/8/8/4K3', BISHOP, 'black'),
    ('white push =N', WPUSH, 'a7a8n', 'N3k3/8/8/8/8/8/8/4K3', KNIGHT, 'black'),
    # --- plain push, Black -------------------------------------------------
    ('black push =Q', BPUSH, 'a2a1q', '4k3/8/8/8/8/8/8/q3K3', -QUEEN, 'white'),
    ('black push =R', BPUSH, 'a2a1r', '4k3/8/8/8/8/8/8/r3K3', -ROOK, 'white'),
    ('black push =B', BPUSH, 'a2a1b', '4k3/8/8/8/8/8/8/b3K3', -BISHOP, 'white'),
    ('black push =N', BPUSH, 'a2a1n', '4k3/8/8/8/8/8/8/n3K3', -KNIGHT, 'white'),
    # --- capture on the last rank, White (the black rook on a8 is taken) ---
    ('white capture =Q', WCAP, 'b7a8q', 'Q3k3/8/8/8/8/8/8/4K3', QUEEN, 'black'),
    ('white capture =R', WCAP, 'b7a8r', 'R3k3/8/8/8/8/8/8/4K3', ROOK, 'black'),
    ('white capture =B', WCAP, 'b7a8b', 'B3k3/8/8/8/8/8/8/4K3', BISHOP, 'black'),
    ('white capture =N', WCAP, 'b7a8n', 'N3k3/8/8/8/8/8/8/4K3', KNIGHT, 'black'),
    # --- capture on the last rank, Black -----------------------------------
    ('black capture =Q', BCAP, 'b2a1q', '4k3/8/8/8/8/8/8/q3K3', -QUEEN, 'white'),
    ('black capture =R', BCAP, 'b2a1r', '4k3/8/8/8/8/8/8/r3K3', -ROOK, 'white'),
    ('black capture =B', BCAP, 'b2a1b', '4k3/8/8/8/8/8/8/b3K3', -BISHOP, 'white'),
    ('black capture =N', BCAP, 'b2a1n', '4k3/8/8/8/8/8/8/n3K3', -KNIGHT, 'white'),
    # --- and it must *behave* as the chosen piece afterwards ---------------
    # =N then Na8-b6: a knight move no bishop can make, so this fails if the
    # buggy build put a bishop on a8.
    ('=N then Nb6 (not a bishop)', BEHAVE, 'a7a8n,h7h6,a8b6',
     '8/8/1N2k2p/8/8/8/8/4K3', KNIGHT - PAWN, 'black'),
    # =R then Ra8-h1: a clear diagonal only a queen could use, so the move
    # must be refused and White must still be to move.  Fails if the buggy
    # build put a queen on a8.
    ('=R then Rh1 refused (not a queen)', BEHAVE, 'a7a8r,h7h6,a8h1',
     'R7/8/4k2p/8/8/8/8/4K3', ROOK - PAWN, 'white'),
]


def run(play, tap, machine, fen, moves):
    cmd = [sys.executable, play, '--tap', tap, '--fen', fen, '--moves', moves,
           '--two-player', '--machine', machine, '--json']
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError('play.py failed: %s\n%s' % (' '.join(cmd), out.stderr))
    return json.loads(out.stdout)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tap', default=os.path.join(HERE, 'chess.tap'),
                    help='the build under test (default: chess.tap next door)')
    ap.add_argument('--harness', default=os.path.join(HERE, '..', '..', 'harness'),
                    help='harness directory holding tools/play.py')
    ap.add_argument('--machine', default='48k',
                    help='comma-separated machines to run, e.g. "48k,hc128"')
    args = ap.parse_args(argv)

    play = os.path.join(args.harness, 'tools', 'play.py')
    for path in (args.tap, play):
        if not os.path.exists(path):
            sys.exit('test_promotion: missing %s' % path)

    failures = []
    total = 0
    for machine in [m.strip() for m in args.machine.split(',') if m.strip()]:
        for name, fen, moves, board, material, side in CASES:
            total += 1
            st = run(play, args.tap, machine, fen, moves)
            got = (st['fen'].split()[0], st['material'], st['side'])
            want = (board, material, side)
            if got != want:
                failures.append('  %s [%s] %s\n      want board=%s material=%d %s\n'
                                '      got  board=%s material=%d %s'
                                % (machine, name, moves, want[0], want[1], want[2],
                                   got[0], got[1], got[2]))

    if failures:
        print('chess: FAIL - promotion chooser puts the wrong piece on the board')
        print('\n'.join(failures))
        return 1
    print('chess: promotion chooser OK (%d cases: Q/R/B/N, both colours, '
          'push + capture, and the piece behaves as chosen)' % total)
    return 0


if __name__ == '__main__':
    sys.exit(main())

```
