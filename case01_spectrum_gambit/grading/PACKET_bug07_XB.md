# Blind review packet — bug07

Two independent submissions fixed the SAME reported defect in the same
Z80 codebase. You are not told who wrote them or by what process, and
the two are not necessarily comparable in style. Judge only what is here.

## The reported defect

# bug07 — checkmate is announced as "Stalemate - draw"

**Build under test:** `arms/variants/bug07` — build with `make` (see its
`BUILD.md`). Emulator, drivers and the commands used below: `arms/harness`
(see `HOWTO.md`), 48K machine, `roms/48.rom`.

## Observed

Every checkmate ends the game as a draw. Deliver mate and the status line reads

```
Stalemate - draw        SPC=new
```

and the recorded result is a stalemate, not a win.

From White Ra1 + Ke6 against the black king on e8:

```
4k3/8/4K3/8/8/8/8/R7 w - - 0 1
```

`Ra1-a8` is mate — the black king is in check on the eighth rank and has no
legal reply. The game does stop, but it stops as `Stalemate - draw`.

The same happens when the engine delivers the mate: from
`r7/8/8/8/8/4k3/8/4K3 b - - 0 1` it correctly finds `Ra8-a1#`, and the game
again ends `Stalemate - draw` instead of `Checkmate! Black wins`. Queen mates
behave the same way (`7k/8/6K1/8/8/8/8/5Q2 w - - 0 1`, `Qf1-f8#`).

Genuine stalemates are still reported as stalemates, and an ordinary check with
legal replies available still leaves the game running, so the only visible
difference is that wins are recorded as draws.

## Repro

```sh
cd arms/harness
make build/hc91emu                       # once

tools/play.py --tap ../variants/bug07/chess.tap \
    --fen '4k3/8/4K3/8/8/8/8/R7 w - - 0 1' --moves a1a8
```

The last screen row and the decoded state show it:

```
Stalemate - draw        SPC=new
gameStateName  stalemate
fen            R3k3/8/4K3/8/8/8/8/8 b - - 1 1
```

```sh
# the engine's own mate
tools/play.py --tap ../variants/bug07/chess.tap \
    --fen 'r7/8/8/8/8/4k3/8/4K3 b - - 0 1' --depth 2
#   lastMove a8a1     gameStateName stalemate      (must be white-mated)

# a queen mate
tools/play.py --tap ../variants/bug07/chess.tap \
    --fen '7k/8/6K1/8/8/8/8/5Q2 w - - 0 1' --moves f1f8
#   gameStateName stalemate                        (must be black-mated)

# controls, both correct on this build:
tools/play.py --tap ../variants/bug07/chess.tap \
    --fen 'k7/8/8/8/8/8/1Q6/4K3 w - - 0 1' --moves b2b6
#   a real stalemate: gameStateName stalemate      (correct)
tools/play.py --tap ../variants/bug07/chess.tap \
    --fen '4k3/8/8/8/8/8/8/R3K3 w - - 0 1' --moves a1a8 --two-player
#   a check with replies available: gameStateName play   (correct)
```

Without the helper script:

```sh
cd arms/harness
tools/chesspos.py tap ../variants/bug07/chess.tap /tmp/bug07.tap \
    --fen '4k3/8/4K3/8/8/8/8/R7 w - - 0 1'
./build/hc91emu --machine 48k --rom roms/48.rom /tmp/bug07.tap --autoload \
    --turbo --type "l@700" \
    --type "$(tools/chesspos.py keys --cursor e2 a1a8)@820" \
    --frames 2000 --text
```

## Expected

- `Ra1-a8` in the first position must end the game with
  `Checkmate! White wins` (recorded state: black is mated).
- `Ra8-a1` in the second must end it with `Checkmate! Black wins`
  (recorded state: white is mated).
- `Qf1-f8` in the third must end it as a checkmate for White.
- A position with no legal moves and the side to move **not** in check must stay
  a stalemate draw, and a check with legal replies must not end the game at all.

## Also observed

- The built-in self-test (`T`) passes: `PERFT OK - movegen verified`, including
  the incremental key/phase/eval-accumulator check. In particular the legal-move
  count in the mated positions is genuinely zero — the game correctly notices
  that the side to move has run out of moves; it just files the result under the
  wrong heading.
- The initial board renders pixel-identical to `initial_golden.png`.
- The engine's search is unaffected: it still finds and plays forced mates, and
  its `Eval` readout shows the mate scores.
- Castling, en passant, promotion, the fifty-move rule, repetition and
  insufficient-material draws all behave normally in spot checks.


## Submission X — source changes

```diff
--- a/movegen.inc
+++ b/movegen.inc
@@ -1176,8 +1176,12 @@
         ld a,(genCount)
         or a
         jr nz,utHas
+        ; No legal moves: mate iff the SIDE TO MOVE is in check.  It must be
+        ; inCheckSide(sideToMove) — NOT moverInCheck, which tests
+        ; sideToMove XOR 8 (the side that just moved) and is therefore always
+        ; 0 here after a legal move, filing every mate as a stalemate.
         ld a,(sideToMove)
-        call moverInCheck
+        call inCheckSide
         or a
         jr z,utStale
         ld a,(sideToMove)

```

## Submission X — tests added

```
--- changes to the accompanying verification package (43959 bytes of diff) ---
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/bridge/a check script SUBMISSION/the the check suite
--- BASELINE/bridge/a check script	2026-07-29 22:35:40.234282768 +0200
+++ SUBMISSION/the the check suite	2026-08-05 16:47:15.704722657 +0200
@@ -130,6 +130,36 @@
 base = obsOf(startPos, mkMove(0x14, 0x34, SP_DPUSH), h0)
 chk("T25_base_conforms", failedClauses(base), [])
 
+# --- §16.9  INCIDENT bug07 — "checkmate announced as Stalemate - draw" ----
+# Mirrors of the kernel theorems T26a..T26l.  A regression of the fault must
+# break these, on the reference implementation side, without any emulator.
+chk("W11a_mate_matches_FEN", bug07RookMate, bug07RookMateFEN)
+chk("T26a_rook_mate", updateTerminal(bug07RookMate, h0), BLACK_MATED)
+chk("T26b_queen_mate", updateTerminal(bug07QueenMate, h0), BLACK_MATED)
+chk("T26c_engine_mate", updateTerminal(bug07EngineMate, h0), WHITE_MATED)
+chk("T26d_mates_are_real",
+    all(not genLegal(p) and inCheckSide(p, p.stm) for p in BUG07_MATES), True)
+chk("T26e_incident_reproduced",
+    [updateTerminalBug07(p, h0) for p in BUG07_MATES], [STALEMATE] * 3)
+chk("T26f_mechanism", any(moverInCheck(p) for p in BUG07_MATES), False)
+chk("T26g_rules_differ",
+    all(updateTerminal(p, h0) != updateTerminalBug07(p, h0)
+        for p in BUG07_MATES), True)
+chk("T26h_controls_agree",
+    all(updateTerminal(p, h0) == updateTerminalBug07(p, h0)
+        for p in BUG07_CONTROLS + [startPos, kiwiPos]), True)
+chk("T26i_stale_control_is_stalemate",
+    updateTerminal(bug07StaleControl, h0), STALEMATE)
+chk("T26j_check_control_still_plays",
+    (updateTerminal(bug07CheckControl, h0),
+     inCheckSide(bug07CheckControl, bug07CheckControl.stm),
+     genLegal(bug07CheckControl) != []), (PLAY, True, True))
+mateObs = obsOf(bug07RookPre, mkMove(0x00, 0x70, 0), h0)
+chk("T26k_mate_step_conforms", failedClauses(mateObs), [])
+chk("T26l_fault_trips_C11_exactly",
+    failedClauses(mateObs.replace(state=updateTerminalBug07(bug07RookMate, h0))),
+    [10])
+
 print("[b1_witnesses] %d checks, %d failures" % (N, len(FAILS)))
 for f in FAILS:
     print("  FAIL " + f)
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/bridge/a check script SUBMISSION/the the check suite
--- BASELINE/bridge/a check script	2026-07-29 22:38:58.133777757 +0200
+++ SUBMISSION/the the check suite	2026-08-05 16:47:50.107601674 +0200
@@ -303,6 +303,16 @@
 
 seed("mate/stalemate-swapped", *_swap(T, "updateTerminal", _ut_bad2))
 
+# B6a — INCIDENT bug07, seeded as itself: the mate guard consults
+# `moverInCheck` (the side that just MOVED) instead of
+# `inCheckSide(p, p.stm)`.  Distinct from B6 — this is not an inversion but a
+# CONSTANTLY-FALSE guard, so genuine stalemates and checks stay correct and
+# only wins are misfiled, which is exactly why it shipped unnoticed.  Seeding
+# it here also proves the reference implementation's `updateTerminalBug07` test object really
+# differs from the specified rule (non-vacuity of §16.9).
+seed("bug07-moverInCheck-guard",
+     *_swap(T, "updateTerminal", T.updateTerminalBug07))
+
 # B7 — e.p. capture removes the wrong pawn (dst+16 instead of dst-16).
 _orig_cs = T.capSquare
 
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/bridge/a check script SUBMISSION/the the check suite
--- BASELINE/bridge/a check script	2026-07-29 22:44:54.050437666 +0200
+++ SUBMISSION/the the check suite	2026-08-05 17:23:28.470429448 +0200
@@ -175,6 +175,7 @@
 
 print("[b5_emulator_oracle] %d emulator runs, %d checks, %d failures"
       % (SAMPLES, CHECKS, len(FAILS)))
+print("  tape: %s" % emu.tap_provenance())
 for f in FAILS:
     print("  FAIL " + f)
 sys.exit(1 if FAILS else 0)
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/bridge/a check script SUBMISSION/the the check suite
--- BASELINE/bridge/a check script	2026-07-29 22:59:13.374886388 +0200
+++ SUBMISSION/the the check suite	2026-08-05 16:34:15.541110199 +0200
@@ -190,7 +190,7 @@
 #       loop's updateTerminal does.  A forced repetition therefore scores as
 #       whatever the static eval says, not as 0.
 # =====================================================================
-src = open("/media/sf_Projects/HC91_emulator/chess/engine.inc").read()
+src = open("SUBMISSION/variants/bug07/engine.inc").read()
 ok("countReps" not in src, "F11: engine.inc now mentions countReps")
 ok("halfmove" not in src, "F11: engine.inc now mentions halfmove")
 EVID.append("F11 engine.inc (negamax + quiesce) contains no reference to "
Only in SUBMISSION/specification/bridge: a check script
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/bridge/emu.py SUBMISSION/the the check suite
--- BASELINE/bridge/emu.py	2026-07-29 22:44:14.362471728 +0200
+++ SUBMISSION/the the check suite	2026-08-05 17:27:16.149866699 +0200
@@ -18,12 +18,25 @@
 """
 import os
 import subprocess
+import sys
 import tempfile
 
-EMU = "/media/sf_Projects/HC91_emulator/build/hc91emu"
-ROM = "/media/sf_Projects/HC91_emulator/roms/48.rom"
-TAP = os.path.join(os.path.dirname(os.path.abspath(__file__)),
-                   "..", "artifacts", "chess.tap")
+# Everything the shell touches is derived from this file's own location, so
+# the package stays inside its workspace and cannot follow a path out of it.
+_HERE = os.path.dirname(os.path.abspath(__file__))
+WORKSPACE = os.path.normpath(os.path.join(_HERE, "..", ".."))
+HARNESS = os.path.join(WORKSPACE, "harness")
+
+EMU = os.path.join(HARNESS, "build", "hc91emu")
+ROM = os.path.join(HARNESS, "roms", "48.rom")
+# VERIFY WHERE IT RUNS (the method Law 4).  This MUST be the tape the variant's
+# `make` produces, never a frozen copy under artifacts/ — a stale artifact
+# makes every emulator layer structurally blind to a regression in the build
+# under test (that is exactly how the bug07 mate/stalemate fault reached a
+# GREEN gate).  Overridable with $HC91_TAP for A/B runs; the default is the
+# build under test.
+TAP = os.environ.get(
+    "HC91_TAP", os.path.join(WORKSPACE, "variants", "bug07", "chess.tap"))
 
 # --- provenance: chess.asm equates -------------------------------------
 A_BOARD      = 0xE000   # board    equ 0xE000   (128 bytes, 0x88 indexed)
@@ -47,6 +60,26 @@
 A_AIDEPTH    = 0xE08A   # aiDepth
 
 
+def tap_provenance():
+    """Which tape this run actually booted, and its md5.
+
+    Printed by the emulator layers so a green result carries the identity of
+    the binary it was green ABOUT.  Without this, `$HC91_TAP` can silently
+    aim the whole emulator tier at a tape that is not the build under test —
+    which is the exact failure mode D-BUG07-1 exists to close.
+    """
+    import hashlib
+    path = os.path.abspath(TAP)
+    try:
+        with open(path, "rb") as f:
+            digest = hashlib.md5(f.read()).hexdigest()
+    except OSError as e:
+        return "%s (UNREADABLE: %s)" % (path, e)
+    tag = ("  [OVERRIDDEN via $HC91_TAP — NOT necessarily the build under test]"
+           if os.environ.get("HC91_TAP") else "")
+    return "%s  md5=%s%s" % (path, digest, tag)
+
+
 class Snapshot:
     """A 48K .sna: 27-byte header then RAM 0x4000..0xFFFF."""
 
@@ -67,7 +100,7 @@
         return list(self.raw[off:off + n])
 
 
-def run(frames, types=(), sna=None, extra=()):
+def run(frames, types=(), sna=None, extra=(), tap=None):
     """Boot chess.tap, apply scheduled key events, snapshot.
 
     Returns (screen_text, Snapshot|None).  Raises on emulator failure —
@@ -77,7 +110,7 @@
            "--frames", str(frames), "--text", "--save-sna", tmp]
     for s, f in types:
         cmd += ["--type", "%s@%d" % (s, f)]
-    cmd += list(extra) + [os.path.abspath(TAP)]
+    cmd += list(extra) + [os.path.abspath(tap or TAP)]
     r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
     if r.returncode != 0:
         raise RuntimeError("hc91emu exit %d: %s" % (r.returncode, r.stderr[:400]))
@@ -147,6 +180,49 @@
 MOVE_GAP = 150
 
 
+# --- arbitrary start positions -----------------------------------------
+# The game's own save/load block (`G`/`L`) is a plain ROM data block, so any
+# position can be injected by appending one hand-built block to the tape under
+# test and pressing `L` after boot — no patching of engine or emulator.  The
+# block builder is the harness's own `chesspos.fen_to_block`, INSIDE this
+# workspace (harness/tools); nothing outside it is read.
+sys.path.insert(0, os.path.join(HARNESS, "tools"))
+import chesspos                                                  # noqa: E402
+
+
+def pos_tap(fen, depth=2):
+    """TAP-under-test + one appended position block.  Returns the path."""
+    out = tempfile.mktemp(suffix=".tap")
+    with open(out, "wb") as f:
+        f.write(open(os.path.abspath(TAP), "rb").read())
+        f.write(chesspos.tap_data_block(chesspos.fen_to_block(fen, depth)))
+    return out
+
+
+def run_fen(fen, moves=(), depth=2, two_player=False,
+            load_frame=700, wait=120, gap=900, tail=900):
+    """Boot the tape under test, LOAD `fen`, play `moves`, snapshot.
+
+    Mirrors harness/tools/play.py's schedule, which is the schedule the bug
+    report used.  `moves` are algebraic ("a1a8", "c7c8q").  Returns
+    (screen_text, Snapshot).  Ordering rules that must not be reordered:
+    the strength digit and `V` are pressed BEFORE `L`, because a tape load
+    only restores White's depth and a loaded Black-to-move position goes
+    straight to the engine.
+    """
+    tap = pos_tap(fen, depth)
+    pre = ("" if depth == 2 else str(depth)) + ("v" if two_player else "") + "l"
+    types, frame = [(pre, load_frame)], load_frame + wait
+    cursor = "e2"
+    for mv in moves:
+        # a trailing 'x' is unbound in the game: harmless padding that keeps a
+        # final ENTER from being eaten by shell/argv trimming (HOWTO caveat).
+        types.append((chesspos.move_keys([mv], cursor) + "x", frame))
+        cursor = mv[2:4]
+        frame += gap
+    return run(frame + tail, types, extra=("--turbo",), tap=tap)
+
+
 def script(moves, start_frame=1000, prefix="", gap=MOVE_GAP):
     """Build --type options for a whole scripted game.
 
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/bridge/run_all.sh SUBMISSION/the the check suite
--- BASELINE/bridge/run_all.sh	2026-07-29 22:55:43.254474282 +0200
+++ SUBMISSION/the the check suite	2026-08-05 16:48:00.575452656 +0200
@@ -10,6 +10,8 @@
 #   b5  emulator-as-oracle: 9 real games, engine legal lists vs reference implementation
 #   b6  alpha-beta == minimax, widened beyond the kernel's small scope
 #   b7  organic findings pinned as regression probes
+#   b8  terminal-verdict oracle (a specification clause) from arbitrary FEN positions:
+#       the mate/stalemate class of INCIDENT bug07, against the real engine
 #   s1-s3  SMT tier (z3): int16 no-overflow, memory layout, dead aspiration
 #
 # Stale bytecode is cleared first so a cached .pyc cannot mask a red gate.
@@ -44,13 +46,14 @@
 run b5 $PY "$HERE/a check script"
 run b6 $PY "$HERE/a check script"
 run b7 $PY "$HERE/a check script"
+run b8 $PY "$HERE/a check script"
 run s1 "$VPY" "$HERE/../smt/s1_eval_range.py"
 run s2 "$VPY" "$HERE/../smt/s2_addresses.py"
 run s3 "$VPY" "$HERE/../smt/s3_aspiration.py"
 
 echo "==============================================="
 if [ $fail -eq 0 ]; then
-  echo "GATE: GREEN (11/11 layers)"
+  echo "GATE: GREEN (12/12 layers)"
 else
   echo "GATE: RED — ${RED[*]}"
 fi
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/DECISIONS.md SUBMISSION/specification/DECISIONS.md
--- BASELINE/DECISIONS.md	2026-07-29 23:03:27.291429317 +0200
+++ SUBMISSION/specification/DECISIONS.md	2026-08-05 17:22:47.593203202 +0200
@@ -224,7 +224,7 @@
 ### D-GATE-1 — The gate is judged by exit code, and clears its own caches
 
 `bridge/run_all.sh` deletes `__pycache__` and the stale `spec/specification.olean`
-before running, then judges each of the 11 layers by **exit status only** and
+before running, then judges each of the 12 layers by **exit status only** and
 prints the red ones by name. Tail-matching was rejected: a layer that prints
 "0 failures" and exits 1 (e.g. an exception after the summary line) would pass
 a tail check.
@@ -250,3 +250,56 @@
   scope** entirely. They are inputs to the position, not rules of the game;
   F1 and F6 both note that they are the paths by which an out-of-specification
   position could reach the engine.
+
+---
+
+### D-BUG07-1 — The emulator layers test the BUILD UNDER TEST, not a frozen artifact
+
+**Chosen.** `bridge/emu.py` boots `variants/bug07/chess.tap` — the tape the
+variant's `make` produces — overridable with `$HC91_TAP` for A/B runs.
+
+**Rejected — the previous `artifacts/chess.tap`.** That frozen copy is how the
+bug07 fault reached a GREEN gate: b4/b5 ran the *pristine* engine and were
+structurally blind to any regression in the build under test. b5 already
+contained a fool's-mate witness that would have caught the fault on the first
+run; it was pointed at the wrong binary. This is the method Law 4 (verify where it
+runs) applied to the bridge's own shell.
+
+**Assumption:** `variants/bug07/make` is byte-reproducible, so the tape the
+gate boots is the tape the sources describe. Checked: rebuilding from a clean
+copy of the sources reproduces the committed `chess.tap` md5 exactly, and
+reverting the one-line fix reproduces the *original* shipped tape md5 exactly.
+
+**Residual:** `artifacts/chess.tap` is still the pristine engine's tape. It is
+now historical evidence, not the gate's input. `artifacts/perft_full.txt` HAS
+been regenerated from the fixed build (`b4 --emu`, 2026-08-05) and came out
+**byte-identical** to the pristine engine's transcript — which is itself
+evidence that the fix does not touch move generation. `b4` without `--emu`
+still 
```

## Submission Y — source changes

```diff
--- a/movegen.inc
+++ b/movegen.inc
@@ -1177,7 +1177,7 @@
         or a
         jr nz,utHas
         ld a,(sideToMove)
-        call moverInCheck
+        call inCheckSide         ; the side with no moves: in check = mate
         or a
         jr z,utStale
         ld a,(sideToMove)

```

## Submission Y — tests added

```
--- test_terminal.py (6280 bytes) ---
#!/usr/bin/env python3
"""test_terminal.py — regression test for updateTerminal's game-over verdict.

Drives the harness (`../../harness/tools/play.py`) through positions whose
outcome is forced, and checks BOTH things the user sees:

  * the recorded state   (`gameState` / `gameStateName` from the snapshot)
  * the status line      (the message row of the screen)

Regression guarded (bug07): with no legal moves, `updateTerminal` asked
`moverInCheck` — which ignores its argument and tests the side that just
MOVED — instead of `inCheckSide(sideToMove)`.  The mover is never in check
after their own move, so every checkmate was filed as "Stalemate - draw".
Cases 1-4 below fail on that build; cases 5-6 keep the genuine draw / live
check verdicts honest, so a "call it mate whenever there are no moves"
non-fix fails too.

Both mating directions are covered (white mated and black mated), and case 4
reaches the mate through the engine's own search rather than a typed move.

    ./test_terminal.py                     # uses ./chess.tap
    ./test_terminal.py --tap /path/chess.tap --harness /path/harness

Exit status is 0 only if every case passes.
"""

import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# name, play.py args, expected gameStateName, required status-line substring
# (None = none required), forbidden status-line substrings.
#
# The status line only persists once the game is over: a live game repaints it
# to "Your move" when the next turn starts (chess.asm, mainLoop), so the check
# control asserts the absence of a game-over banner instead.
GAME_OVER_BANNERS = ['Checkmate', 'Stalemate', 'Draw', 'SPC=new']

CASES = [
    ("rook mate, black mated",
     ['--fen', '4k3/8/4K3/8/8/8/8/R7 w - - 0 1', '--moves', 'a1a8', '--two-player'],
     'black-mated', 'Checkmate! White wins', ['Stalemate']),

    ("queen mate, black mated",
     ['--fen', '7k/8/6K1/8/8/8/8/5Q2 w - - 0 1', '--moves', 'f1f8', '--two-player'],
     'black-mated', 'Checkmate! White wins', ['Stalemate']),

    ("rook mate, white mated",
     ['--fen', 'r7/8/8/8/8/4k3/8/4K3 b - - 0 1', '--moves', 'a8a1', '--two-player'],
     'white-mated', 'Checkmate! Black wins', ['Stalemate']),

    ("engine delivers mate, white mated",
     ['--fen', 'r7/8/8/8/8/4k3/8/4K3 b - - 0 1', '--depth', '2'],
     'white-mated', 'Checkmate! Black wins', ['Stalemate']),

    # ordering: the no-legal-moves branch must be reached before the draw
    # claims below it, so a mate that is also the 100th halfmove is a mate.
    ("mate beats the 50-move claim",
     ['--fen', '4k3/8/4K3/8/8/8/8/R7 w - - 99 1', '--moves', 'a1a8', '--two-player'],
     'black-mated', 'Checkmate! White wins', ['Draw', 'Stalemate']),

    ("control: genuine stalemate stays a draw",
     ['--fen', 'k7/8/8/8/8/8/1Q6/4K3 w - - 0 1', '--moves', 'b2b6', '--two-player'],
     'stalemate', 'Stalemate - draw', ['Checkmate']),

    ("control: check with legal replies keeps playing",
     ['--fen', '4k3/8/8/8/8/8/8/R3K3 w - - 0 1', '--moves', 'a1a8', '--two-player'],
     'play', None, GAME_OVER_BANNERS),
]

# the engine-driven case must also have played the mating move it is named for
EXPECT_LAST_MOVE = {"engine delivers mate, white mated": "a8a1"}


def run_case(play, tap, args):
    """Run one play.py session -> (state dict, list of screen rows)."""
    r = subprocess.run([sys.executable, play, '--tap', tap] + args,
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("play.py failed (%d):\n%s%s" % (r.returncode, r.stdout, r.stderr))
    state, screen, in_screen = {}, [], False
    for line in r.stdout.splitlines():
        if line.startswith('=== SCREEN'):
            in_screen = True
            continue
        if line.startswith('=== END'):
            in_screen = False
            continue
        if in_screen:
            screen.append(line)
        else:
            m = re.match(r'^(\w+)\s+(.*)$', line)
            if m:
                state[m.group(1)] = m.group(2).strip()
    if 'gameStateName' not in state:
        raise RuntimeError("no state decoded from play.py output:\n" + r.stdout)
    return state, screen


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tap', default=os.path.join(HERE, 'chess.tap'))
    ap.add_argument('--harness', default=os.path.normpath(os.path.join(HERE, '..', '..', 'harness')))
    a = ap.parse_args(argv)

    play = os.path.join(a.harness, 'tools', 'play.py')
    for p in (a.tap, play):
        if not os.path.exists(p):
            sys.stderr.write("test_terminal: missing %s\n" % p)
            return 2

    failures = 0
    for name, args, want_state, want_msg, forbid in CASES:
        try:
            state, screen = run_case(play, a.tap, args)
        except RuntimeError as e:
            print("chess: FAIL - %s: %s" % (name, e))
            failures += 1
            continue

        shown = [row.strip() for row in screen if row.strip()]
        problems = []
        if state['gameStateName'] != want_state:
            problems.append("gameState %s, want %s" % (state['gameStateName'], want_state))
        if want_msg and not any(want_msg in row for row in screen):
            problems.append("status line lacks %r (screen: %r)" % (want_msg, shown[-3:]))
        for bad in forbid:
            if any(bad in row for row in screen):
                problems.append("status line shows %r (screen: %r)" % (bad, shown[-3:]))
        want_move = EXPECT_LAST_MOVE.get(name)
        if want_move and state.get('lastMove') != want_move:
            problems.append("lastMove %s, want %s" % (state.get('lastMove'), want_move))

        if problems:
            print("chess: FAIL - %s: %s" % (name, "; ".join(problems)))
            failures += 1
        else:
            print("chess: %s OK (%s)" % (name, want_state))

    if failures:
        print("chess: FAIL - %d/%d terminal-state case(s) wrong" % (failures, len(CASES)))
        return 1
    print("chess: checkmate/stalemate verdicts OK (%d cases)" % len(CASES))
    return 0


if __name__ == '__main__':
    sys.exit(main())

```
