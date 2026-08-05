# Blind review packet — bug05

Two independent submissions fixed the SAME reported defect in the same
Z80 codebase. You are not told who wrote them or by what process, and
the two are not necessarily comparable in style. Judge only what is here.

## The reported defect

# bug05 — a rook reappears on a1 out of nowhere once the rook that started there has moved away

**Build under test:** `arms/variants/bug05` — build with `make` (see its
`BUILD.md`). Emulator, drivers and the commands used below: `arms/harness`
(see `HOWTO.md`), 48K machine, `roms/48.rom`.

## Observed

**A white rook materialises on a1.** Start from White Ra1 + Ke1 with queenside
castling still available and the black king on e8:

```
4k3/8/8/8/8/8/8/R3K3 w Q - 0 1
```

Move the rook `Ra1-a2` — fine, the board is correct and `Matl` still reads `5`.
Now let Black play any move at all (`Ke8-e7`). As soon as that move is made the
board becomes

```
8/4k3/8/8/8/8/R7/R3K3 w - - 2 2

  2 R . . . . . . .      the rook that moved, on a2
  1 R . . . K . . .      ... and a SECOND rook, back on a1
```

`Matl` jumps from `5` to `10`. Nobody castled, nobody promoted, and no white
move was made between the two screens — the extra rook simply appears while the
opponent moves. It is a real piece: it can be moved and captured afterwards.

**Castling long is also still offered.** Continuing from that position, e1 → c1
is accepted even though the original a1 rook is standing on a2: the king lands
on c1, a rook lands on d1, and White ends up with two rooks
(`8/4k3/8/8/8/8/R7/2KR4`, `Matl 10`).

**And the kingside right is lost instead.** From
`4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1`, play `Ra1-a2`, `Ke8-e7`, then try `e1-g1`:
the move is rejected as `Illegal move` although the h1 rook has never moved.

The h1/a8/h8 corners behave correctly; everything above is specific to a1.

## Repro

```sh
cd arms/harness
make build/hc91emu                       # once

# 1. the phantom rook — two moves is enough
tools/play.py --tap ../variants/bug05/chess.tap \
    --fen '4k3/8/8/8/8/8/8/R3K3 w Q - 0 1' --moves 'a1a2,e8e7' --two-player
```

```
fen            8/4k3/8/8/8/8/R7/R3K3 w - - 2 2    <-- rooks on a1 AND a2
material       1000                               <-- must still be 500
```

```sh
# ... and after only the first move it is still correct, so the extra rook
#     arrives with Black's reply
tools/play.py --tap ../variants/bug05/chess.tap \
    --fen '4k3/8/8/8/8/8/8/R3K3 w Q - 0 1' --moves a1a2 --two-player
#   fen 4k3/8/8/8/8/8/R7/4K3 b - - 1 1     material 500        (correct)

# 2. castling long accepted with the rook long gone
tools/play.py --tap ../variants/bug05/chess.tap \
    --fen '4k3/8/8/8/8/8/8/R3K3 w Q - 0 1' --moves 'a1a2,e8e7,e1c1' --two-player
#   fen 8/4k3/8/8/8/8/R7/2KR4 b - - 3 2    material 1000    moveLog a1a2 e8e7 e1c1

# 3. the kingside right is revoked by a1 traffic
tools/play.py --tap ../variants/bug05/chess.tap \
    --fen '4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1' --moves 'a1a2,e8e7,e1g1' --two-player
#   moveLog a1a2 e8e7                      (e1g1 was refused; it must be legal)

# controls, all correct on this build:
tools/play.py --tap ../variants/bug05/chess.tap \
    --fen '4k3/8/8/8/8/8/8/R3K3 w Q - 0 1' --moves e1c1 --two-player
#   O-O-O with the rook still home: legal, material 500
tools/play.py --tap ../variants/bug05/chess.tap \
    --fen '4k3/8/8/8/8/8/8/4K2R w K - 0 1' --moves 'h1h2,e8e7,e1g1' --two-player
#   h1 rook leaves -> O-O correctly refused
```

`--two-player` presses `V` so both sides are driven by `--moves` and the engine
never interferes; the FEN's castling field is honoured because the game's own
tape-load restores it. Without the helper script:

```sh
cd arms/harness
tools/chesspos.py tap ../variants/bug05/chess.tap /tmp/bug05.tap \
    --fen '4k3/8/8/8/8/8/8/R3K3 w Q - 0 1'
./build/hc91emu --machine 48k --rom roms/48.rom /tmp/bug05.tap --autoload \
    --turbo --type "vl@700" \
    --type "$(tools/chesspos.py keys --cursor e2 a1a2)@820" \
    --type "$(tools/chesspos.py keys --cursor a2 e8e7)@1220" \
    --frames 2400 --text --save-sna /tmp/bug05.sna
tools/chesspos.py board /tmp/bug05.sna
```

(one `--type` per move, a few hundred frames apart: the game repaints the whole
screen between moves and keystrokes that arrive during the repaint are dropped.
`--cursor` is where the cursor was left by the previous move.)

```
```

## Expected

- No piece may ever appear on the board that was not put there by a move. After
  `Ra1-a2` and Black's reply the position must be
  `8/4k3/8/8/8/8/R7/4K3 w - - 2 2`, with `Matl 5`.
- Moving (or losing) the a1 rook must revoke White's **queenside** castling
  right and nothing else, so `e1-c1` in repro 2 must be refused as illegal and
  the move log must stop at `a1a2 e8e7`.
- Moving the a1 rook must **not** touch the kingside right: `e1-g1` in repro 3
  must be accepted, ending as `5RK1` on the first rank.
- Castling must never change the material on the board.
- The other three corners must keep behaving as they already do.

## Also observed

- The built-in self-test (`T`) does **not** pass on this build:

  ```
  perft 1  20         OK
  perft 2  400        OK
  perft 3  8902       OK
  perft 4  197281     OK
  kiwipete d3  97739    BAD
  enpassant d4 43238    OK
  promotion d3 62379    OK
  incr key/phase/pst    OK
  PERFT BAD - movegen error
  ```

  (the canonical count for Kiwipete at depth 3 is 97862; that position starts
  with both sides holding all four castling rights.)
- The initial board renders pixel-identical to `initial_golden.png`.
- A king move still revokes both of its own rights.
- En passant, promotion, check/mate/stalemate detection, the draw rules and the
  engine's search all behave normally in spot checks.


## Submission X — source changes

```diff
--- a/movegen.inc
+++ b/movegen.inc
@@ -939,26 +939,28 @@
         call keyUpdate
         ret
 
+; A rook leaving or being captured on a corner revokes exactly THAT corner's
+; right.  castling bits (chess.asm): bit0 WK(h1) bit1 WQ(a1) bit2 BK(h8) bit3 BQ(a8).
 clrCastleSq:
-        cp 0x00
+        cp 0x00                  ; a1 -> white queenside
         jr nz,cc1
         ld a,b
-        and 0xFE
+        and 0xFD
         ld b,a
         ret
-cc1:    cp 0x07
+cc1:    cp 0x07                  ; h1 -> white kingside
         jr nz,cc2
         ld a,b
         and 0xFE
         ld b,a
         ret
-cc2:    cp 0x70
+cc2:    cp 0x70                  ; a8 -> black queenside
         jr nz,cc3
         ld a,b
         and 0xF7
         ld b,a
         ret
-cc3:    cp 0x77
+cc3:    cp 0x77                  ; h8 -> black kingside
         ret nz
         ld a,b
         and 0xFB

```

## Submission X — tests added

```
--- changes to the accompanying verification package (63783 bytes of diff) ---
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/artifacts/perft_full.txt SUBMISSION/specification/artifacts/perft_full.txt
--- BASELINE/artifacts/perft_full.txt	2026-07-29 22:17:48.023897750 +0200
+++ SUBMISSION/specification/artifacts/perft_full.txt	2026-08-05 18:57:46.196533292 +0200
@@ -24,3 +24,5 @@
                                 
                                 
 === END ===
+
+; hc91 tape md5 783b72ba018897b1311a7af0295ab041
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/bridge/a check script SUBMISSION/the the check suite
--- BASELINE/bridge/a check script	2026-07-29 22:35:40.234282768 +0200
+++ SUBMISSION/the the check suite	2026-08-05 17:48:25.673063151 +0200
@@ -130,6 +130,55 @@
 base = obsOf(startPos, mkMove(0x14, 0x34, SP_DPUSH), h0)
 chk("T25_base_conforms", failedClauses(base), [])
 
+baseRook = obsOf(castlePos, mkMove(0x00, 0x01, 0), h0)
+chk("T25a_baseRook_conforms", failedClauses(baseRook), [])
+chk("T25b_baseRook_rights", baseRook.post.castling, 0x0D)
+chk("T24k_C15", 14 in failedClauses(
+    baseRook.replace(post=baseRook.post.replace(castling=0x0E))), True)
+chk("T24l_C15_kept", 14 in failedClauses(
+    baseRook.replace(post=baseRook.post.replace(castling=0x0F))), True)
+
+# --- §16.10  INCIDENT bug05 — the phantom rook on a1 ----------------------
+# Every theorem of the specification §16.10, re-checked in the shipped reference implementation.
+bug05Mv = mkMove(0x00, 0x10, 0)                       # Ra1-a2
+bug05Reply = mkMove(0x74, 0x64, 0)                    # Ke8-e7
+
+chk("T26_a1_clears_WQ", makeMove(bug05Pos, bug05Mv).castling, 0)
+chk("T26a_a1_spares_WK", makeMove(bug05KQPos, bug05Mv).castling, 1)
+chk("T26b_h1_spares_WQ", makeMove(bug05KQPos, mkMove(0x07, 0x17, 0)).castling, 2)
+chk("T26c_a8_clears_BQ",
+    makeMove(kiwiPos.replace(stm=BLACK), mkMove(0x70, 0x71, 0)).castling, 0x07)
+chk("T26d_h8_clears_BK",
+    makeMove(kiwiPos.replace(stm=BLACK), mkMove(0x77, 0x76, 0)).castling, 0x0B)
+
+_after = makeMove(makeMove(bug05Pos, bug05Mv), bug05Reply)
+chk("T26e_no_OOO_after_a1", mkMove(0x04, 0x02, SP_OOO) in genLegal(_after), False)
+chk("T26f_OO_survives_a1",
+    mkMove(0x04, 0x06, SP_OO) in
+    genLegal(makeMove(makeMove(bug05KQPos, bug05Mv), bug05Reply)), True)
+chk("T26g_no_material_from_nowhere",
+    len([s for s in scanSquares if bGet(_after.board, s) != 0]), 3)
+chk("T26h_incident_conforms", Conforming(obsOf(bug05Pos, bug05Mv, h0)), True)
+chk("T26i_reply_conforms",
+    Conforming(obsOf(makeMove(bug05Pos, bug05Mv), bug05Reply, h0)), True)
+
+bug05Obs = obsOf(bug05Pos, bug05Mv, h0)
+bug05KQObs = obsOf(bug05KQPos, bug05Mv, h0)
+chk("T27_kept_right_fails_C3_C15",
+    failedClauses(bug05Obs.replace(post=bug05Obs.post.replace(castling=0x02))),
+    [2, 14])
+chk("T27a_phantom_rook_fails_C3_C12_C15",
+    failedClauses(bug05Obs.replace(post=bug05Obs.post.replace(
+        castling=0x02, board=bSet(bug05Obs.post.board, 0x00, WR)))),
+    [2, 11, 14])
+# C7 alone could NEVER have caught bug05: 0x02 is a subset of 0x03.
+chk("T27b_wrong_bit_is_monotone",
+    a specification rule(bug05KQObs.replace(
+        post=bug05KQObs.post.replace(castling=0x02))), True)
+chk("T27c_wrong_bit_fails_C15",
+    failedClauses(bug05KQObs.replace(post=bug05KQObs.post.replace(castling=0x02))),
+    [2, 14])
+
 print("[b1_witnesses] %d checks, %d failures" % (N, len(FAILS)))
 for f in FAILS:
     print("  FAIL " + f)
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/bridge/a check script SUBMISSION/the the check suite
--- BASELINE/bridge/a check script	2026-07-29 22:38:58.133777757 +0200
+++ SUBMISSION/the the check suite	2026-08-05 17:50:03.904517050 +0200
@@ -80,10 +80,11 @@
     base.replace(post=base.post.replace(stm=WHITE)),
     ["a specification rule", "a specification rule"])
 
-# C7 — castling rights INVENTED (bitwise non-monotone).
+# C7 — castling rights INVENTED (bitwise non-monotone).  C15 fires too:
+# 0xFF is both outside the 4-bit field and the wrong bit map.
 mut("C7/invented-rights",
     base.replace(post=base.post.replace(castling=0xFF)),
-    ["a specification rule", "a specification rule"])
+    ["a specification rule", "a specification rule", "a specification rule"])
 
 # C8 — e.p. target dropped after a double push.
 mut("C8/lost-ep-target",
@@ -133,8 +134,34 @@
     _pro.replace(post=_pro.post.replace(board=bSet(_pro.post.board, 0x71, WK))),
     ["a specification rule", "a specification rule", "a specification rule"])
 
+# C15 — the WRONG castling right revoked (incident bug05).  This is the
+# mutation C7 cannot see: after Ra1-b1 out of castlePos the conforming byte
+# is 0x0D, and the engine produced 0x0E — still a SUBSET of 0x0F, so
+# a specification rule is satisfied.  Only C15 fires (plus C3).
+_rook = obsOf(castlePos, mkMove(0x00, 0x01, 0), h0)
+mut("C15/wrong-right-revoked",
+    _rook.replace(post=_rook.post.replace(castling=0x0E)),
+    ["a specification rule", "a specification rule"])
+
+# C15 — the right KEPT although the rook left its corner (the other half of
+# bug05: this is what let genCastling offer O-O-O with no rook on a1).
+mut("C15/right-kept-after-rook-left",
+    _rook.replace(post=_rook.post.replace(castling=0x0F)),
+    ["a specification rule", "a specification rule"])
+
+# C15 — junk outside the 4-bit field.  C7 accepts it whenever pre also had
+# the bits; C15 does not.
+mut("C15/junk-high-nibble",
+    _rook.replace(post=_rook.post.replace(castling=0x8D)),
+    ["a specification rule", "a specification rule", "a specification rule"])
+
 # ------------------------------------------- Part B: implementation ------
 
+# Counted, not hard-coded: a new Part A mutation must not silently make the
+# printed split wrong (doc-count drift is a recorded failure mode).
+NOBS = NMUT
+
+
 def probe():
     """A compact battery over the whole rules core, called through the MODULE
     object so a seeded fault anywhere in the call graph is visible.  Any
@@ -157,8 +184,13 @@
     sig.append(T.mkMove(0x44, 0x53, T.SP_EP) in T.genLegal(epPos))
     # the e.p. capture must remove the pawn on d5 (0x43), not something else
     sig.append(tuple(T.makeMove(epPos, T.mkMove(0x44, 0x53, T.SP_EP)).board))
-    # a rook leaving a1 must clear the white queenside right
+    # each corner must revoke EXACTLY its own right (incident bug05):
+    # a1->WQ (0x0D), h1->WK (0x0E), a8->BQ (0x07), h8->BK (0x0B)
     sig.append(T.makeMove(castlePos, T.mkMove(0x00, 0x01, 0)).castling)
+    sig.append(T.makeMove(castlePos, T.mkMove(0x07, 0x06, 0)).castling)
+    _cb = castlePos.replace(stm=T.BLACK)
+    sig.append(T.makeMove(_cb, T.mkMove(0x70, 0x71, 0)).castling)
+    sig.append(T.makeMove(_cb, T.mkMove(0x77, 0x76, 0)).castling)
     # a promotion must place a piece of the MOVER's colour
     sig.append(T.bGet(T.makeMove(promoPos, T.mkMove(0x61, 0x71, 0x50)).board, 0x71))
     sig.append(len([m for m in T.genLegal(promoPos) if T.mvPromo(m) != 0]))
@@ -345,6 +377,42 @@
 _orig_cc = T.clrCastleSq
 seed("rights-never-cleared", *_swap(T, "clrCastleSq", lambda r, s: r))
 
+
+# B10a — INCIDENT bug05, seeded verbatim: `clrCastleSq` masks 0xFE for a1
+# where it must mask 0xFD, i.e. the a1 rook revokes the KINGSIDE right.
+# This is the one-operand fault that was found in movegen.inc:942.
+def _cc_bug05(rights, s):
+    if s == 0x00:
+        return T.andB(rights, 0xFE)            # <- was 0xFD
+    return _orig_cc(rights, s)
+
+
+seed("bug05/a1-clears-WK", *_swap(T, "clrCastleSq", _cc_bug05))
+
+# ... and the same fault must be visible AT THE CLAUSE LEVEL, naming C15.
+# A probe-signature change alone would only say "something moved"; the point
+# of C15 is that a regression of bug05 is reported with the right name.
+NMUT += 1
+COVERED.add("a specification rule")
+T.clrCastleSq = _cc_bug05
+try:
+    # The engine's own post-position under the fault, judged by the CLAUSES
+    # (which are computed from the untouched rightSurvives restatement).
+    _pre = bug05KQPos
+    _mv = T.mkMove(0x00, 0x10, 0)                      # Ra1-a2
+    _buggy_post = T.makeMove(_pre, _mv)
+    _o = T.Obs(_pre, _mv, _buggy_post, h0, T.updateTerminal(_buggy_post, h0))
+    _got = set(n for i, n in enumerate(clauseNames) if not T.CLAUSES[i](_o))
+    _rights = _buggy_post.castling
+finally:
+    T.clrCastleSq = _orig_cc
+if _rights != 0x02:
+    FAILS.append("B/bug05 seeding did not reproduce the reported byte "
+                 "(got 0x%02X, the harness observed 0x02)" % _rights)
+if _got != {"a specification rule"}:
+    FAILS.append("B/bug05-a1-clears-WK        tripped %s, expected "
+                 "['a specification rule']" % (sorted(_got) or ["NOTHING"]))
+
 # B11 — C4's ONLY possible negative test: break unmake and check that the
 # clause itself (not merely the probe signature) goes red.
 def _um_bad(p, u):
@@ -371,7 +439,7 @@
 
 print("[b2_mutations] %d mutations (%d observation + %d implementation), "
       "%d/%d clauses negatively tested, %d failures"
-      % (NMUT, 16, NMUT - 16, len(COVERED), len(clauseNames), len(FAILS)))
+      % (NMUT, NOBS, NMUT - NOBS, len(COVERED), len(clauseNames), len(FAILS)))
 for f in FAILS:
     print("  FAIL " + f)
 sys.exit(1 if FAILS else 0)
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/bridge/a check script SUBMISSION/the the check suite
--- BASELINE/bridge/a check script	2026-07-29 22:47:27.641510760 +0200
+++ SUBMISSION/the the check suite	2026-08-05 17:51:07.155547849 +0200
@@ -8,7 +8,8 @@
 
     genMoves (ordered, with flags) | genLegal (ordered) | in-check |
     evalWhite | gamePhase | isInsufficient | updateTerminal | make/unmake
-    round-trip | perft 1
+    round-trip | perft 1 | the castling byte after every legal move | C15's
+    verdict on every legal move
 
 The corpus is deterministic (seeded), so a failure is reproducible.
 
@@ -94,6 +95,12 @@
         str(updateTerminal(p, History([], 0))),
         str(1 if rt else 0),
         str(perft(p, 1)),
+        # observable 10 (added by incident bug05): the castling byte AFTER
+        # every legal move, and C15's independent verdict on it.  A
+        # corner->bit slip in either transcription shows up here.
+        " ".join(str(makeMove(p, m).castling) for m in gl),
+        " ".join("1" if a specification rule(obsOf(p, m, History([], 0))) else "0"
+                 for m in gl),
     ])
 
 
@@ -132,7 +139,12 @@
       toString (stateNum (updateTerminal p { keys := [], cur := 0 })),
       toString (if gl.all (fun m => unmakeMove (makeMove p m) (undoOf p m) == p)
                 then 1 else 0),
-      toString (perft p 1) ]
+      toString (perft p 1),
+      String.intercalate " " (gl.map (fun m => toString (makeMove p m).castling)),
+      String.intercalate " "
+        (gl.map (fun m =>
+          if a specification rule (obsOf p m { keys := [], cur := 0 })
+          then "1" else "0")) ]
 
 def go : Nat → List Position → IO Unit
   | _, [] => pure ()
@@ -178,7 +190,8 @@
         twin_d = digest(positions[i])
         if twin_d != lean_d:
             parts = ["genMoves", "genLegal", "inCheck", "evalWhite", "gamePhase",
-                     "isInsufficient", "updateTerminal", "unmakeRoundTrip", "perft1"]
+                     "isInsufficient", "updateTerminal", "unmakeRoundTrip", "perft1",
+                     "rightsAfter", "C15"]
             lp, tp = lean_d.split("|"), twin_d.split("|")
             which = [parts[k] for k in range(len(parts))
                      if k >= len(lp) or k >= len(tp) or lp[k] != tp[k]]
@@ -188,7 +201,7 @@
     tot_moves = sum(len(genMoves(p)) for p in positions)
     tot_legal = sum(len(genLegal(p)) for p in positions)
     print("[b3_spec_twin_brute] %d positions (seed %d), %d pseudo-legal / %d legal "
-          "moves compared across 9 observables, %d failures"
+          "moves compared across 11 observables, %d failures"
           % (N, SEED, tot_moves, tot_legal, len(fails)))
     for f in fails[:10]:
         print("  FAIL " + f)
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/bridge/a check script SUBMISSION/the the check suite
--- BASELINE/bridge/a check script	2026-07-29 22:49:05.888097955 +0200
+++ SUBMISSION/the the check suite	2026-08-05 17:58:10.507308155 +0200
@@ -20,8 +20,14 @@
 (recorded as a bridge blind spot in SUMMARY.md; layer b5 closes part of it by
 comparing the move LISTS themselves).
 
-`--emu` re-runs the engine (about 2.5 min); without it, the recorded
-artifacts/perft_full.txt transcript from the pre-registered run is parsed.
+EVIDENCE FRESHNESS (changed by incident bug05, 2026-08-05).  This layer used
+to replay a PRE-RECORDED `artifacts/perft_full.txt` by default, and the
+recording was never tied to the binary under test.  A live `T` on the bug05
+build prints `kiwipete d3  97739  BAD` — the engine's own self-test names the
+fault — but the recorded transcript said OK, so the gate stayed green.  The
+engine is therefore RUN, live, by default.  `--recorded` still replays the
+transcript, but only if the transcript's stamped tape hash matches the tape
+under test; a stale transcript is a LOUD failure, never a quiet pass.
 """
 import os
 import re
@@ -31,21 +37,34 @@
 sys.path.insert(0, HERE)
 sys.path.insert(0, os.path.join(HERE, "..", "reference implementation"))
 
-from reference implementation import perft                                      # noqa: F403
-from positions import ENGINE_PERFT                               # noqa: F403
+import emu                                                       # noqa: E402
+from reference implementation import perft                                      # noqa: F403,E402
+from positions import ENGINE_PERFT                               # noqa: F403,E402
 
 TRANSCRIPT = os.path.join(HERE, "..", "artifacts", "perft_full.txt")
+STAMP = "; hc91 tape md5 "
 
 
 def engine_screen(
```

## Submission Y — source changes

```diff
--- a/movegen.inc
+++ b/movegen.inc
@@ -939,26 +939,29 @@
         call keyUpdate
         ret
 
+; clrCastleSq(A=square) — a rook corner was vacated or captured, so drop the
+; right that belongs to it.  B holds the rights (bit0 WK, bit1 WQ, bit2 BK,
+; bit3 BQ — see chess.asm); each corner clears exactly its own bit.
 clrCastleSq:
-        cp 0x00
+        cp 0x00                 ; a1 -> white queenside
         jr nz,cc1
         ld a,b
-        and 0xFE
+        and 0xFD
         ld b,a
         ret
-cc1:    cp 0x07
+cc1:    cp 0x07                 ; h1 -> white kingside
         jr nz,cc2
         ld a,b
         and 0xFE
         ld b,a
         ret
-cc2:    cp 0x70
+cc2:    cp 0x70                 ; a8 -> black queenside
         jr nz,cc3
         ld a,b
         and 0xF7
         ld b,a
         ret
-cc3:    cp 0x77
+cc3:    cp 0x77                 ; h8 -> black kingside
         ret nz
         ld a,b
         and 0xFB

```

## Submission Y — tests added

```
--- test_castling_rights.py (4829 bytes) ---
#!/usr/bin/env python3
"""test_castling_rights.py — regression test for the castling-rights masks.

Guards the bug where `clrCastleSq` (movegen.inc) cleared the wrong rights bit
for the a1 corner: moving the a1 rook revoked White's *kingside* right and left
the *queenside* right standing.  A stale queenside right with a1 empty made
genCastling emit O-O-O anyway, and the legal-move filter's make/unmake of that
move wrote a rook back onto a1 (umOOO restores the rook unconditionally) — a
piece appearing on the board that no move put there.

Each case drives the game headlessly through the harness with `--two-player`,
so the engine never moves and every move in the list is ours.  A move the game
refuses simply does not appear in `moveLog`, which is how "must be illegal" is
asserted.

    ./test_castling_rights.py                 # uses ./chess.tap and ../../harness
    HARNESS=/path/to/harness ./test_castling_rights.py
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.environ.get('HARNESS') or os.path.join(HERE, '..', '..', 'harness')
PLAY = os.path.join(HARNESS, 'tools', 'play.py')
TAP = os.environ.get('TAP') or os.path.join(HERE, 'chess.tap')

# name, start FEN, moves, expected {field: value}
CASES = [
    # --- the reported bug -------------------------------------------------
    ("a1 rook leaves: no phantom rook, Q right revoked",
     '4k3/8/8/8/8/8/8/R3K3 w Q - 0 1', 'a1a2,e8e7',
     {'fen': '8/4k3/8/8/8/8/R7/4K3 w - - 2 2', 'material': 500,
      'castling': 0, 'moveLog': 'a1a2 e8e7'}),

    ("a1 rook leaves: O-O-O must then be illegal",
     '4k3/8/8/8/8/8/8/R3K3 w Q - 0 1', 'a1a2,e8e7,e1c1',
     {'fen': '8/4k3/8/8/8/8/R7/4K3 w - - 2 2', 'material': 500,
      'moveLog': 'a1a2 e8e7'}),

    ("a1 rook leaves: the kingside right must survive",
     '4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1', 'a1a2,e8e7,e1g1',
     {'fen': '8/4k3/8/8/8/8/R7/5RK1 b - - 3 2', 'material': 1000,
      'moveLog': 'a1a2 e8e7 e1g1'}),

    ("a1 rook captured: Q right revoked, board not rewritten",
     '4k3/8/8/8/8/8/1b6/R3K3 b Q - 0 1', 'b2a1,e1c1',
     {'fen': '4k3/8/8/8/8/8/8/b3K3 w - - 0 2', 'material': -330,
      'castling': 0, 'moveLog': 'b2a1'}),

    # --- the mirror: h1 traffic must not touch the queenside right --------
    ("h1 rook leaves: the queenside right must survive",
     '4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1', 'h1h2,e8e7,e1c1',
     {'fen': '8/4k3/8/8/8/8/7R/2KR4 b - - 3 2', 'material': 1000,
      'moveLog': 'h1h2 e8e7 e1c1'}),

    # --- the black corners, same shape ------------------------------------
    ("a8 rook leaves: the black kingside right must survive",
     'r3k2r/8/8/8/8/8/8/4K3 b kq - 0 1', 'a8a7,e1e2,e8g8',
     {'fen': '5rk1/r7/8/8/8/8/4K3/8 w - - 3 3', 'material': -1000,
      'moveLog': 'a8a7 e1e2 e8g8'}),

    ("h8 rook leaves: the black queenside right must survive",
     'r3k2r/8/8/8/8/8/8/4K3 b kq - 0 1', 'h8h7,e1e2,e8c8',
     {'fen': '2kr4/7r/8/8/8/8/4K3/8 w - - 3 3', 'material': -1000,
      'moveLog': 'h8h7 e1e2 e8c8'}),

    # --- controls: castling still works, and never changes material -------
    ("control: O-O-O with the rook still home",
     '4k3/8/8/8/8/8/8/R3K3 w Q - 0 1', 'e1c1',
     {'fen': '4k3/8/8/8/8/8/8/2KR4 b - - 1 1', 'material': 500,
      'moveLog': 'e1c1'}),

    ("control: h1 rook leaves -> O-O illegal",
     '4k3/8/8/8/8/8/8/4K2R w K - 0 1', 'h1h2,e8e7,e1g1',
     {'fen': '8/4k3/8/8/8/8/7R/4K3 w - - 2 2', 'material': 500,
      'castling': 0, 'moveLog': 'h1h2 e8e7'}),
]


def run(fen, moves):
    cmd = [sys.executable, PLAY, '--tap', TAP, '--fen', fen,
           '--moves', moves, '--two-player', '--json']
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError('play.py failed:\n' + r.stderr)
    return json.loads(r.stdout)


def main():
    if not os.path.exists(PLAY):
        sys.stderr.write('test_castling_rights: no harness at %s\n' % HARNESS)
        return 2
    if not os.path.exists(TAP):
        sys.stderr.write('test_castling_rights: no tape at %s (run make)\n' % TAP)
        return 2

    bad = 0
    for name, fen, moves, want in CASES:
        st = run(fen, moves)
        diffs = ['%s: got %r want %r' % (k, st.get(k), v)
                 for k, v in want.items() if st.get(k) != v]
        if diffs:
            bad += 1
            print('FAIL  %s' % name)
            print('      %s  moves %s' % (fen, moves))
            for d in diffs:
                print('      %s' % d)
        else:
            print('ok    %s' % name)

    if bad:
        print('chess: FAIL - %d/%d castling-rights case(s) wrong' % (bad, len(CASES)))
        return 1
    print('chess: castling rights OK (%d cases)' % len(CASES))
    return 0


if __name__ == '__main__':
    sys.exit(main())

```
