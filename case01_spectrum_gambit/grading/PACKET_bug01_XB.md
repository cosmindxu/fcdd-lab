# Blind review packet — bug01

Two independent submissions fixed the SAME reported defect in the same
Z80 codebase. You are not told who wrote them or by what process, and
the two are not necessarily comparable in style. Judge only what is here.

## The reported defect

# bug01 — the engine's evaluation readout is far too optimistic, and it plays for phantom material

**Build under test:** `arms/variants/bug01` — build with `make` (see its
`BUILD.md`). Emulator, drivers and the commands used below: `arms/harness`
(see `HOWTO.md`), 48K machine, `roms/48.rom`.

## Observed

The `Eval` figure on the analysis panel (and the move the engine picks from it)
claims material the engine does not have and cannot get.

Put the engine in an **exactly mirror-symmetric** position — White's army is
Black's reflected in the middle of the board, and Black has the move:

```
5k2/1p6/2n5/3pp3/3PP3/2N5/1P6/5K2 b - - 0 1

  8 . . . . . k . .
  7 . p . . . . . .
  6 . . n . . . . .
  5 . . . p p . . .
  4 . . . P P . . .
  3 . . N . . . . .
  2 . P . . . . . .
  1 . . . . . K . .
    a b c d e f g h      Black to move
```

At level 2 the panel reads `Move d5e4`, **`Eval 108`** — the engine announces a
1.08-pawn advantage for Black in a position that is symmetric by construction.
It plays `d5xe4`, a capture that is immediately recaptured; material after
White's obvious reply is level again, but the engine had already priced the
pawn in.

At level 3 the same position reads `Eval 133`.

The same over-valuation shows up whenever a capture sequence is unfinished at
the search horizon. In

```
5k2/pp6/2p2n2/3P4/4P3/2N5/1P6/5K2 b - - 0 1     (material is level: 3P+N each)
```

the engine reports `Eval 114` at level 2. The exchange it is counting on
(`c6xd5 e4xd5 Nf6xd5 Nc3xd5`) ends with Black a knight down, not a pawn up.

## Repro

```sh
cd arms/harness
make build/hc91emu                       # once

tools/play.py --tap ../variants/bug01/chess.tap \
    --fen '5k2/1p6/2n5/3pp3/3PP3/2N5/1P6/5K2 b - - 0 1' --depth 2
```

The last lines of the output are the decoded state; the panel is in the screen
dump above them:

```
                    Move d5e4
                    Eval 108
lastMove       d5e4
lastScore      108
```

Without the helper script:

```sh
cd arms/harness
tools/chesspos.py tap ../variants/bug01/chess.tap /tmp/bug01.tap \
    --fen '5k2/1p6/2n5/3pp3/3PP3/2N5/1P6/5K2 b - - 0 1'
./build/hc91emu --machine 48k --rom roms/48.rom /tmp/bug01.tap --autoload \
    --turbo --type "l@700" --frames 3800 --text
```

(`l` = the game's own tape-load key, which reads the position block appended to
the tape. Level 3 and above: press the digit *before* `l`, i.e.
`--type "3l@700"`, because the strength keys set both sides' search depth while
a tape load only restores White's.)

The second position:

```sh
tools/play.py --tap ../variants/bug01/chess.tap \
    --fen '5k2/pp6/2p2n2/3P4/4P3/2N5/1P6/5K2 b - - 0 1' --depth 2
```

## Expected

- In the mirror-symmetric position the evaluation must be about **0** at every
  level: whatever is true for one side is true for the other, and the side to
  move has no way to break the symmetry in its favour. A correct build reports
  `Eval 0` at level 2 and plays a waiting move (`f8f7`).
- In the second position a correct build reports a small **negative** score
  (about `-24`), because the capture sequence it can start loses a knight for a
  pawn.
- More generally: a capture that is going to be recaptured must not be scored
  as if it were free. The score the engine prints should be reachable by force
  from the position on the board.

## Also observed

- The built-in self-test (`T`) passes: `PERFT OK - movegen verified`, including
  the incremental key/phase/eval-accumulator check.
- The initial board renders pixel-identical to `initial_golden.png`.
- Obvious captures are still found: with a free queen on d5
  (`rnbqkbnr/pppp1ppp/4p3/3Q4/8/8/PPPP1PPP/RNB1KBNR b - - 0 1`) the engine
  plays `e6xd5` and reports `Eval 953`.
- Legal move generation, castling, en passant, promotion, mate and draw
  detection all behave normally in spot checks.


## Submission X — source changes

```diff
--- a/engine.inc
+++ b/engine.inc
@@ -1435,8 +1435,8 @@
 ; =====================================================================
 quiesce:
         ld a,(searchPly)
-        cp 3
-        jp nc,eval               ; too deep -> static eval
+        cp MAXPLY                ; the per-ply frame bound, NOT a q-depth cap:
+        jp nc,eval               ; out of ply frames -> static eval
         call ptrTtMvFrom         ; no TT move in quiescence
         ld (hl),0xFF
         call eval

```

## Submission X — tests added

```
--- changes to the accompanying verification package (44111 bytes of diff) ---
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/bridge/a check script SUBMISSION/the the check suite
--- BASELINE/bridge/a check script	2026-07-29 22:59:13.374886388 +0200
+++ SUBMISSION/the the check suite	2026-08-02 03:35:05.524013302 +0200
@@ -190,7 +190,7 @@
 #       loop's updateTerminal does.  A forced repetition therefore scores as
 #       whatever the static eval says, not as 0.
 # =====================================================================
-src = open("/media/sf_Projects/HC91_emulator/chess/engine.inc").read()
+src = open("SUBMISSION/variants/bug01/engine.inc").read()
 ok("countReps" not in src, "F11: engine.inc now mentions countReps")
 ok("halfmove" not in src, "F11: engine.inc now mentions halfmove")
 EVID.append("F11 engine.inc (negamax + quiesce) contains no reference to "
Only in SUBMISSION/specification/bridge: a check script
Only in SUBMISSION/specification/bridge: a check script
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/bridge/emu.py SUBMISSION/the the check suite
--- BASELINE/bridge/emu.py	2026-07-29 22:44:14.362471728 +0200
+++ SUBMISSION/the the check suite	2026-08-02 03:35:05.522690693 +0200
@@ -20,8 +20,8 @@
 import subprocess
 import tempfile
 
-EMU = "/media/sf_Projects/HC91_emulator/build/hc91emu"
-ROM = "/media/sf_Projects/HC91_emulator/roms/48.rom"
+EMU = "SUBMISSION/harness/build/hc91emu"
+ROM = "SUBMISSION/harness/roms/48.rom"
 TAP = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "artifacts", "chess.tap")
 
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/bridge/run_all.sh SUBMISSION/the the check suite
--- BASELINE/bridge/run_all.sh	2026-07-29 22:55:43.254474282 +0200
+++ SUBMISSION/the the check suite	2026-08-02 03:59:43.684545991 +0200
@@ -10,6 +10,11 @@
 #   b5  emulator-as-oracle: 9 real games, engine legal lists vs reference implementation
 #   b6  alpha-beta == minimax, widened beyond the kernel's small scope
 #   b7  organic findings pinned as regression probes
+#   b8  clause S6 (quiescence resolves the horizon): witnesses, guard-mutation
+#       coverage, algorithm-vs-quantifier brute force, and the source/binary
+#       pin of `cp MAXPLY` — added by incident bug01
+#   b9  S6 through the REAL engine on the BUILD UNDER TEST: a symmetric
+#       position may not be scored as if it owned material
 #   s1-s3  SMT tier (z3): int16 no-overflow, memory layout, dead aspiration
 #
 # Stale bytecode is cleared first so a cached .pyc cannot mask a red gate.
@@ -44,13 +49,15 @@
 run b5 $PY "$HERE/a check script"
 run b6 $PY "$HERE/a check script"
 run b7 $PY "$HERE/a check script"
+run b8 $PY "$HERE/a check script"
+run b9 $PY "$HERE/a check script"
 run s1 "$VPY" "$HERE/../smt/s1_eval_range.py"
 run s2 "$VPY" "$HERE/../smt/s2_addresses.py"
 run s3 "$VPY" "$HERE/../smt/s3_aspiration.py"
 
 echo "==============================================="
 if [ $fail -eq 0 ]; then
-  echo "GATE: GREEN (11/11 layers)"
+  echo "GATE: GREEN (13/13 layers)"
 else
   echo "GATE: RED — ${RED[*]}"
 fi
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/DECISIONS.md SUBMISSION/specification/DECISIONS.md
--- BASELINE/DECISIONS.md	2026-07-29 23:03:27.291429317 +0200
+++ SUBMISSION/specification/DECISIONS.md	2026-08-02 05:05:15.745866542 +0200
@@ -224,7 +224,7 @@
 ### D-GATE-1 — The gate is judged by exit code, and clears its own caches
 
 `bridge/run_all.sh` deletes `__pycache__` and the stale `spec/specification.olean`
-before running, then judges each of the 11 layers by **exit status only** and
+before running, then judges each of the 13 layers by **exit status only** and
 prints the red ones by name. Tail-matching was rejected: a layer that prints
 "0 failures" and exits 1 (e.g. an exception after the summary line) would pass
 a tail check.
@@ -250,3 +250,130 @@
   scope** entirely. They are inputs to the position, not rules of the game;
   F1 and F6 both note that they are the paths by which an out-of-specification
   position could reach the engine.
+
+---
+
+## Incident bug01 (fix session) — appended
+
+### D-BUG01-1 — The reported fault violated NO existing clause, so the specification was extended first
+
+**The fault.** `engine.inc:1438`, head of `quiesce`: `cp 3` where the engine ships
+`cp MAXPLY`. The quiescence ply guard is the per-ply FRAME bound of §16.7, not a
+search-depth cap; at 3 it leaves one ply of quiescence at `aiDepth` 2 and none at
+all from `aiDepth` 3, so a capture standing at the horizon is scored as free.
+
+**Chosen.** Extend the specification before calling the fix done — new clause **S6
+`quiesceResolves`** (spec §12.5, reference implementation §12.5, bridge `b8`/`b9`), with the incident
+encoded as theorems (§16.6b) per the method law 6.
+
+**Why it was necessary rather than optional.** `C1`..`C14` constrain moves and
+positions; `S1`/`S2` the returned move and the ply budget; `S3` the STATIC eval;
+`S4` alpha-beta on abstract trees. None constrains the VALUE a leaf hands back.
+`b8` asserts this explicitly (`M_old_spec_identifier`): replaying the
+engine's own `d5xe4` from the incident position fails no clause. A fix without a
+clause would have left the next horizon regression equally invisible.
+
+**Rejected — "the score must be reachable by force from the position on the
+board", as stated in the bug report.** That is the honest informal property, but
+as a specification clause it is a soundness claim about the whole heuristic search
+(TT, null move, LMR, reverse futility), which D4 already declines to make and
+which no finite bridge could sample meaningfully. S6 states the part that is both
+true and checkable: the leaf value equals the value of a RESOLVED position.
+
+**Rejected — pinning the reported numbers (108 → 0, 114 → −24) as the test.**
+Failure mode: it pins two positions, not the fault's class; any other horizon
+truncation would sail through. `b9` therefore leads with a symmetry FAMILY whose
+premise is verified in the reference implementation, and `b8` pins the guard in the assembled image.
+
+**Assumptions.** (i) The pristine tape shipped in `artifacts/chess.tap` is the
+correct reference — discharged by the rebuilt tape being byte-identical to it,
+not assumed. (ii) `aiDepth ∈ 1..5` (assumption 6 of `SUMMARY.md`), which is what
+makes "≥ 10 plies of quiescence at every legal level" a total statement.
+
+---
+
+### D-BUG01-2 — S6 is modelled over abstract capture trees, at the same tier as S4
+
+**Chosen.** `QTree` + `qsearch`/`qminimax`, mirroring the existing
+`GTree` + `alphaBeta`/`minimax`. The spec models the quiescence ALGORITHM, not
+chess move generation, and says so in the section header.
+
+**Rejected — modelling quiescence over real `Position`s using the reference implementation's
+`genMoves`.** It would be a stronger statement, but the kernel proofs are `rfl`
+on decidable Booleans and a chess-level quiescence would not reduce inside any
+reasonable time or memory; the alternative is `native_decide`, ruled out by D1.
+The wide sweeps live in the reference implementation at a labelled lower claim level instead — same
+split D5 already made for alpha-beta.
+
+**Residual, named:** S6 is not bridged value-for-value to the Z80 quiescence,
+because the engine does not expose intermediate quiescence scores. `b9` bridges
+it by pinning the engine's EXACT score on a set of tempo-neutral symmetric
+probes, and `b8`'s P sub-layer pins the guard byte in the shipped image.
+
+**Superseded framing, kept for the record (D-BUG01-5).**  `b9` originally
+asserted a CLASS property — "a mirror-symmetric position may not be scored as
+if it owned material" (`abs(score) < 100`) — justified by S3 + S6.  Two
+review rounds refuted it, in two stages, both by execution
+against a build byte-identical to the pristine reference:
+
+* symmetry alone does not force the SEARCH value to 0 (S3 is about the STATIC
+  evaluator), because the side to move gets a free tempo: with mutually
+  en-prise pieces the mover simply takes first;
+* adding a QUIET premise (resolved quiescence value 0) does not rescue it
+  either, because quiescence follows captures and a knight FORK is a quiet
+  move.  No capture-based predicate can imply the conclusion.
+
+**Chosen instead:** assert only what is sound — the exact per-position score
+pins — and keep three NEGATIVE CONTROLS in the layer whose engine scores
+(500 / 865 / 140, all correct) assert that `abs(score) < 100` is FALSE there.
+The refutation is thus executable rather than a comment, and re-introducing
+the class property turns the layer red.  **Rejected — weakening the bound to
+`abs(score) < 1000` or similar:** it would keep the false framing, pass
+vacuously, and leave the badge mismatched to the detector (law 3).
+
+---
+
+### D-BUG01-3 — The optimistic-direction claim was DROPPED after execution falsified it
+
+**Intended.** A fail-direction property in the spirit of the method law 1: a truncated
+quiescence over-values, never under-values — which is what the bug report
+describes ("far too optimistic").
+
+**Falsified.** Enumerating chains of 0..5 captures over {−320, −100, 0, 100, 320}
+and budgets 0..7 (31,248 cases) found **918 under-valued** cases alongside 1,348
+over-valued ones. With no quiescence at all a node simply returns its static eval,
+which misses the mover's OWN winning capture as readily as the opponent's reply.
+
+**Chosen instead.** State it as an explicit NON-CLAIM (`T27f`..`T27i`), in the
+spirit of the existing `T21d_narrow_window_diverges`: one and the same tree,
+`chainOf [−320, 100]` under a root capture, is under-valued at budget 0 and
+over-valued at budget 1. So S6 is an EQUALITY to the resolved score, never a
+one-sided bound. The general property that does hold — and that is proved instead
+— is the FIXPOINT (`T27e`): once the budget covers the capture depth, more budget
+changes nothing.  **Enumerated, not general**: 81 trees × 3 budgets in the
+kernel, 3,906 × 3 in `b8`.  The general lemma `bud ≥ capDepth t → qsearch =
+qminimax` is not proved, and S6 deliberately carries no `capDepth ≤ bud` side
+condition — so S6 is genuinely false for a tree needing deeper resolution than
+the frame budget affords (first reachable at capture depth ≥ 14; the gate's
+domains top out at 6).  That is an honest limitation of a 15-ply frame budget,
+and stating it as a precondition would have hidden it.
+
+**Why this is in the ledger:** the wrong claim was plausible, matched the reported
+symptom, and would have shipped had it not been executed first.
+
+---
+
+### D-BUG01-4 — b9 drives the BUILD UNDER TEST; the older layers still do not
+
+**Chosen.** `a check script` boots `variants/bug01/chess.tap`, and `b8`'s P
+sub-layer reads `variants/bug01/chess.bin` and `engine.inc`. A regression pin
+aimed at a different binary from the one that ships would be worthless (the method
+law 4, verify-where-it-runs).
+
+**Not changed, and recorded as a residual:** `bridge/emu.py` still points at
+`specification/artifacts/chess.tap`, so `b4`/`b5`/`b7` test the pristine artifact.
+That is harmless while the two are byte-identical (they are, and `b8`'s
+`P_tap_contains_the_built_image` plus `b9` cover the gap), but it is a standing
+version-drift risk in the package. Re-pointing the whole shell is a change to
+layers this incident did not touch, so it is named here rather than done under a
+bug fix.
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/organic_findings.md SUBMISSION/specification/organic_findings.md
--- BASELINE/organic_findings.md	2026-07-29 23:00:29.200185253 +0200
+++ SUBMISSION/specification/organic_findings.md	2026-08-02 05:52:21.043956278 +0200
@@ -1,7 +1,7 @@
 # Organic findings — HC-91 chess engine
 
 Real defects and FIDE divergences found in the **pristine** engine
-(`/media/sf_Projects/HC91_emulator/chess/`, 7,343 lines) while building the
+(`EXTERNAL_PATH_REMOVED`, 7,343 lines) while building the
 formal specification.  These are the *organic bonus lane* of case01: none of them
 is a seeded fault, and none was hinted at by anything outside the source.
 
@@ -261,3 +261,72 @@
 * **16-bit evaluation arithmetic** cannot overflow: worst case |eval| ≤ 11,465
   against a 32,767 limit, with the aspiration, reverse-futility and
   window-negation arithmetic all inside range.
+
+---
+
+## F12 — the spec and the reference implementation misdescribe `matingEval`: a Z80 register clobber
+
+**Severity: MED (pure-specification-only — it makes the specification wrong, not the engine
+worse). Claim level: CONFIRMED (source read + 32/32 emulator measurements).**
+Found by the round-3 review of the bug01 fix; **pre-existing**, unrelated
+to that fix (the fixed tape is byte-identical to the pristine reference).
+
+`spec/the specification` §`matingEval` and `reference implementation/reference implementation.py:matingEval` both define
+
+    matingEval = centerDist(bking) * 16  +  kingProx(wking, bking) * 4
+
+citing `engine.inc:634`.  The shipped engine computes something else.  `matingEval`
+(engine.inc:643-657) saves the first term in `C`:
+
+    ld a,(bking) / call centerDist / add a,a x4   ; A = centerDist*16
+    ld c,a                                        ; saved in C
+    call kingProx                                 ; <-- clobbers C
+    add a,a / add a,a                             ; A = kingProx*4
+    add a,c                                       ; + whatever C now holds
+
+but `kingProx` (engine.inc:714-746) contains
+
+    kpF:    ld c,a                   ; |file diff|
+
+so by the time `add a,c` runs, `C` holds `|file(wking) - file(bking)|`, not
+`centerDist*16`.  The engine therefore computes
+
+    kingProx * 4  +  |file diff|          (range 0..35)
+
+instead of the intended `centerDist*16 + kingProx*4` (range 0..124).  The
+"drive the lone 
```

## Submission Y — source changes

```diff
--- a/chess.asm
+++ b/chess.asm
@@ -184,6 +184,8 @@
 moveLogN equ 0xE15D      ; plies recorded in the full move history (cap 255)
 blackDepth equ 0xE15E    ; Black's search depth (odds / handicap play)
 effDepth equ 0xE15F      ; effective depth for the side currently moving
+qRootPly equ 0xE1A7      ; ply the current quiescence search started at
+                         ; (free RAM: saveBuf is 0xE160..0xE1A6, moveLog 0xE200)
 moveLog  equ 0xE200      ; full game move history: 2 bytes/ply (from,to)
 saveBuf  equ 0xE160      ; game-save buffer: 64 board + side/cas/ep + extras
 SAVELEN  equ 71          ; 64 + side + castle + ep + halfmove + moveCount(2) + depth
@@ -226,7 +228,19 @@
 MV_REC  equ 4
 INF     equ 30000
 MATE    equ 29000
-MAXPLY  equ 15
+MAXPLY  equ 15           ; hard per-ply frame limit: the move buffer
+                         ; (0x6000+ply*512) and undo slot (0xD000+ply*16) are
+                         ; sized for plies 0..15.  Only the arrays quiescence
+                         ; uses go that deep: negamax's origAlphaArr wraps and
+                         ; nbFromArr/nbToArr alias each other above ply 7, so
+                         ; negamax must stay <= ply 7 (it never passes 5).
+QDEPTH  equ 4            ; quiescence budget: plies below the ply it started at
+QHORIZ  equ 6            ; ...but never stop before this ABSOLUTE ply.  What
+                         ; decides whether an exchange resolves is the total
+                         ; horizon (level + budget); at level 1 a plain budget
+                         ; leaves it one ply short, so the shallowest searches
+                         ; get the extra ply.  Level 2+ already reach 6 at the
+                         ; end of the budget, so they are unaffected.
 ASPW    equ 40           ; aspiration-window half-width (centipawns)
 
 ; flag byte: bits0-2 special, bits4-7 promo type

--- a/engine.inc
+++ b/engine.inc
@@ -1014,7 +1014,13 @@
 ; =====================================================================
 negamax:
         or a
-        jp z,quiesce
+        jp nz,nmHasDepth
+        ; depth 0 -> the leaf quiescence search starts here.  Record the ply
+        ; so quiesce can bound itself RELATIVE to its entry (see quiesce).
+        ld a,(searchPly)
+        ld (qRootPly),a
+        jp quiesce
+nmHasDepth:
         ld b,a
         call ptrDepth
         ld (hl),b
@@ -1434,9 +1440,38 @@
 ;  the position before evaluating (kills the horizon effect).
 ; =====================================================================
 quiesce:
+        ; Two independent limits, and they are NOT the same thing (bug01 was
+        ; caused by using one literal for both):
+        ;  1. MAXPLY is the hard *frame* limit — beyond it the per-ply move
+        ;     buffer (0x6000+ply*512) would run into the program image.
+        ;  2. QDEPTH is the quiescence *budget*, counted from the ply the
+        ;     leaf search started at, so it does not grow with the level.
+        ;     It must be big enough to play out an exchange to the end: a
+        ;     capture whose recapture falls outside it is scored as if it
+        ;     were free, which is exactly the bug (a budget of 1 made the
+        ;     engine claim a phantom pawn in a symmetric position).
         ld a,(searchPly)
-        cp 3
-        jp nc,eval               ; too deep -> static eval
+        cp MAXPLY
+        jp nc,eval               ; out of per-ply frames -> static eval
+        ; budget = max(QDEPTH, QHORIZ - effDepth): what decides whether an
+        ; exchange resolves is the TOTAL horizon (level + budget), so the
+        ; shallowest level gets the extra ply it would otherwise be short.
+        ; effDepth is the level, not the iterative-deepening iteration, so
+        ; levels 2..5 keep exactly QDEPTH — including their throwaway depth-1
+        ; iteration, whose score is only a PV/aspiration hint.
+        ld a,QHORIZ
+        ld hl,effDepth
+        sub (hl)
+        cp QDEPTH
+        jr nc,qLim
+        ld a,QDEPTH
+qLim:
+        ld b,a                   ; B = this search's quiescence budget
+        ld a,(searchPly)
+        ld hl,qRootPly
+        sub (hl)                 ; A = plies spent in this quiescence search
+        cp b
+        jp nc,eval               ; budget spent -> static eval
         call ptrTtMvFrom         ; no TT move in quiescence
         ld (hl),0xFF
         call eval
@@ -1521,7 +1556,7 @@
         ld h,0xE0
         ld a,(hl)
         or a
-        jr nz,qIsCap
+        jr nz,qIsCap             ; every capture is searched — see below
         ld a,(mvFlag)
         and 7
         cp SP_EP
@@ -1529,6 +1564,16 @@
         ld a,(mvFlag)
         and 0xF0
         jp z,qLoop               ; quiet, non-promotion -> skip
+        ; Under-promotions are skipped: they never decide a quiescence score,
+        ; and generating four promotions per promoting pawn per ply is what
+        ; makes a pawn-heavy position unbounded.  Captures, by contrast, are
+        ; ALL searched.  Filtering them by the SEE-lite ordering test was
+        ; tried and reverted: it declines a capture whose target looks
+        ; defended, and when that defender cannot actually recapture (it is
+        ; pinned) the *recapture* is the move that gets skipped — so the
+        ; original capture scores as free and bug01 comes straight back.
+        cp 0x50                  ; queen promotion? (promoFlags Q,R,B,N)
+        jp nz,qLoop
 qIsCap:
         call makeMove
         call moverInCheck

```

## Submission Y — tests added

```
--- eval_check.py (8686 bytes) ---
#!/usr/bin/env python3
"""eval_check.py — quiescence / horizon regression check.

The engine's printed `Eval` must be a score it can actually reach by force
from the position on the board.  That only holds if the leaf quiescence
search is allowed to resolve a capture sequence to the end: a capture that is
going to be recaptured must not be scored as if it were free.

This is the check that bug01 failed.  `quiesce` bailed out to a static eval
once the *absolute* `searchPly` reached 3, instead of at the per-ply frame
limit `MAXPLY` (15).  At level 2 that let quiescence play the capture but not
the recapture; at level 3 and above it disabled quiescence altogether.  The
engine then announced material it did not have and played for it.

Each case runs the real tape in the harness emulator (~0.5 s) and asserts on
the decoded game state, so it fails for the user-visible symptom, not for an
implementation detail.  `observed_before` records what the broken build
printed, so it is obvious what each case is guarding.

    ./eval_check.py                       # uses ../../harness and ./chess.tap
    ./eval_check.py --harness ../../harness --tap chess.tap
"""

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# Mirror-symmetric: White's army is Black's reflected in the middle of the
# board, and Black has the move.  Whatever is true for one side is true for
# the other and the side to move cannot break the symmetry in its favour, so
# the score must be ~0 at every level and the engine must not grab d5xe4.
SYM = '5k2/1p6/2n5/3pp3/3PP3/2N5/1P6/5K2 b - - 0 1'

# Material is level (3P+N each).  The capture sequence Black can start,
# c6xd5 e4xd5 Nf6xd5 Nc3xd5, ends with Black a knight down for a pawn — it
# needs four plies of quiescence to see that, so a build whose quiescence
# stops after one capture prices in a free pawn instead.
LOSING_EXCHANGE = '5k2/pp6/2p2n2/3P4/4P3/2N5/1P6/5K2 b - - 0 1'

# Fully symmetric and completely quiet: no capture exists for either side, so
# quiescence has nothing to resolve.  Guards the trivial direction — a build
# that scores this as anything but 0 has an asymmetric evaluation, which
# would be a different fault wearing the same symptom.
QUIET_SYM = '4k3/pppppppp/8/8/8/8/PPPPPPPP/4K3 b - - 0 1'

# Sanity in the other direction: a genuinely free queen must still be taken
# and still be worth ~9 pawns.  A "fix" that made the engine blind to
# captures, or that clamped the score, would pass everything above and fail
# here.
FREE_QUEEN = 'rnbqkbnr/pppp1ppp/4p3/3Q4/8/8/PPPP1PPP/RNB1KBNR b - - 0 1'

# Positions that make an unbounded capture search explode.  A quiescence
# search must be bounded RELATIVE to the ply it starts at; capping it by the
# absolute ply instead lets it grow with the level and these never finish.
# The assertion is "the engine finished its move inside the frame budget" — a
# search that has to be waited out is a broken search even if the move it
# eventually returns is good.
SICILIAN = 'r2q1rk1/1b1nbppp/p2ppn2/1p4B1/3NPP2/2N2Q2/PPP3PP/2KR1B1R b - - 0 1'
PROMO_STORM = '4k3/PPP2PPP/8/8/8/8/ppp2ppp/4K3 b - - 0 1'

# Dense capture melee: every pawn and knight is en prise to something, so the
# capture ladders are long and it is the sharpest test of whether the engine
# stops resolving too early.  Mirror-symmetric, but note that does NOT make it
# equal — the copycat refutation breaks as soon as a capture comes with check
# (…Nc6xe5, Nc3xe4, …Ne5xf3+ is not mirrorable).  Its true worth, by an
# exhaustive unbounded material quiescence (stand-pat + all captures, engine
# piece values, computed offline with python-chess), is **+100 for Black**.
# The assertion is therefore an UPPER bound: the engine may under-claim (a
# bounded quiescence truncates a long ladder) but must not claim more than is
# reachable by force.  The broken build printed 340 here; a build whose
# quiescence budget is one ply short prints 313 at level 1.
SYM_MELEE = '4k3/1ppppp2/2nnnn2/3PPP2/3ppp2/2NNNN2/1PPPPP2/4K3 b - - 0 1'
SYM_MELEE_ORACLE = 100

# A capture whose recapture comes from a piece that only *looks* like it
# cannot afford to recapture: Ne7 is pinned by Re1 against Ke8, so a filter
# that trusts "is the target defended?" skips White's Bg2xd5 and prices
# Black's Nf6xd5 as free.  The engine must decline Nxd5 (it loses a knight
# for a pawn) and score the position around -278, not -145.
PINNED_DEFENDER = '4k3/4n2p/5n2/3P4/8/8/6BP/4R2K b - - 0 1'

# name, fen, depth, expected move (None = don't care), score low, score high,
# frames allowed after the load, what the broken build printed.
# Every case also requires that the engine actually completed a move: without
# that, a case with no expected move passes vacuously on a build so slow that
# it never moves, reading back a stale score from an earlier iteration.
CASES = [
    ('symmetric level 2', SYM, 2, 'f8f7', 0, 0, 900, 'd5e4 / 108'),
    ('symmetric level 3', SYM, 3, None, -40, 40, 900, 'd5e4 / 133'),
    # level 4 happened to come out f8f7 / 20 on the broken build — it is kept
    # as a stability guard (the score must stay bounded as depth grows), not
    # as a reproducer of bug01.
    ('symmetric level 4', SYM, 4, None, -40, 40, 1800, 'f8f7 / 20 — did not fail'),
    ('losing exchange level 2', LOSING_EXCHANGE, 2, 'c6d5', -60, 0, 900, 'c6d5 / 114'),
    ('quiet symmetric level 2', QUIET_SYM, 2, None, 0, 0, 900, '0 (already OK)'),
    ('free queen level 2', FREE_QUEEN, 2, 'e6d5', 800, 1100, 900, 'e6d5 / 953'),
    # cost guards: an unbounded quiescence takes minutes here, or never returns
    ('sicilian finishes', SICILIAN, 2, None, -400, 400, 4000, '4690 frames'),
    ('promotion storm finishes', PROMO_STORM, 2, None, -3000, 3000, 6000, 'never finished'),
    # cost AND over-claiming in one position.  Upper bound = the exhaustive
    # material-quiescence value + a positional allowance; the lower bound is
    # loose because truncating a long ladder under-claims, which is safe.
    # Level 1 matters as much as the rest: the capture horizon is
    # (level + budget), so the shallowest search is where it collapses first.
    ('symmetric melee level 1', SYM_MELEE, 1, None, -150, SYM_MELEE_ORACLE + 100, 8000, '340; 313 with a short budget'),
    ('symmetric melee level 2', SYM_MELEE, 2, None, -150, SYM_MELEE_ORACLE + 100, 8000, '340, never finished'),
    ('symmetric melee level 3', SYM_MELEE, 3, None, -150, SYM_MELEE_ORACLE + 100, 8000, '340, never finished'),
    ('pinned defender level 1', PINNED_DEFENDER, 1, 'e8d7', -400, -200, 900, 'n/a'),
]


def run(play, tap, fen, depth, machine, tail):
    cmd = [sys.executable, play, '--tap', tap, '--fen', fen,
           '--depth', str(depth), '--machine', machine,
           '--tail', str(tail), '--quiet', '--json']
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError('%s failed:\n%s' % (' '.join(cmd), r.stderr))
    return json.loads(r.stdout)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--harness', default=os.path.join(HERE, '..', '..', 'harness'))
    ap.add_argument('--tap', default=os.path.join(HERE, 'chess.tap'))
    ap.add_argument('--machine', default='48k')
    a = ap.parse_args(argv)

    play = os.path.join(a.harness, 'tools', 'play.py')
    emu = os.path.join(a.harness, 'build', 'hc91emu')
    for p in (play, emu, a.tap):
        if not os.path.exists(p):
            sys.stderr.write('eval_check: missing %s\n' % p)
            return 2

    bad = 0
    for name, fen, depth, move, lo, hi, tail, before in CASES:
        st = run(play, a.tap, fen, depth, a.machine, tail)
        got_move, got_score = st['lastMove'], st['lastScore']
        why = []
        if got_move == '-':
            why.append('engine never completed a move in %d frames' % tail)
        if move is not None and got_move != move:
            why.append('move %s, want %s' % (got_move, move))
        if not lo <= got_score <= hi:
            why.append('score %d, want %d..%d' % (got_score, lo, hi))
        if why:
            bad += 1
            print('chess: FAIL - %s: %s   (broken build printed %s)'
                  % (name, '; '.join(why), before))
        else:
            print('chess: %s OK (%s / %d)' % (name, got_move, got_score))

    if bad:
        print('chess: FAIL - %d quiescence/horizon case(s) failed' % bad)
        return 1
    print('chess: quiescence horizon OK (%d cases)' % len(CASES))
    return 0


if __name__ == '__main__':
    sys.exit(main())

```
