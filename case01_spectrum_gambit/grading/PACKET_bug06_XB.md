# Blind review packet — bug06

Two independent submissions fixed the SAME reported defect in the same
Z80 codebase. You are not told who wrote them or by what process, and
the two are not necessarily comparable in style. Judge only what is here.

## The reported defect

# bug06 — the strength setting does nothing: levels 3, 4 and 5 return the level-2 answer

**Build under test:** `arms/variants/bug06` — build with `make` (see its
`BUILD.md`). Emulator, drivers and the commands used below: `arms/harness`
(see `HOWTO.md`), 48K machine, `roms/48.rom`.

## Observed

Raising the engine's level has no effect on what it plays or on the score it
reports. The panel dutifully shows `Level 5`, the search runs, and the answer is
bit-for-bit the level-2 answer.

Position (Black, i.e. the engine, to move):

```
5k2/1p6/2n5/3pp3/3PP3/2N5/1P6/5K2 b - - 0 1
```

| level | `Move` | `Eval` |
|-------|--------|--------|
| 2     | f8f7   | 0      |
| 3     | f8f7   | 0      |
| 4     | f8f7   | 0      |
| 5     | f8f7   | 0      |

The same in a middlegame position
(`r3k2r/pp3ppp/2n1b3/3q4/3P4/2N1B3/PP3PPP/R2QK2R b KQkq - 0 1`): level 2 gives
`d5g2` / `Eval 47` and so do levels 3, 4 and 5 — identical move, identical
score.

It is not that the engine is refusing to think: the higher levels visibly take
longer (the clock on the panel is charged for it) and then return the shallow
result anyway. The effect is the same on the 128K machine (`--machine hc128`),
where the table lives in the spare RAM banks.

## Repro

```sh
cd arms/harness
make build/hc91emu                       # once

for L in 2 3 4 5; do
  echo "level $L"
  tools/play.py --tap ../variants/bug06/chess.tap \
      --fen '5k2/1p6/2n5/3pp3/3PP3/2N5/1P6/5K2 b - - 0 1' --depth $L --quiet
done
```

```
level 2 ... lastMove f8f7   lastScore 0
level 3 ... lastMove f8f7   lastScore 0
level 4 ... lastMove f8f7   lastScore 0
level 5 ... lastMove f8f7   lastScore 0
```

```sh
# middlegame position, level 2 vs level 5
tools/play.py --tap ../variants/bug06/chess.tap \
    --fen 'r3k2r/pp3ppp/2n1b3/3q4/3P4/2N1B3/PP3PPP/R2QK2R b KQkq - 0 1' --depth 2
tools/play.py --tap ../variants/bug06/chess.tap \
    --fen 'r3k2r/pp3ppp/2n1b3/3q4/3P4/2N1B3/PP3PPP/R2QK2R b KQkq - 0 1' --depth 5
#   both: lastMove d5g2   lastScore 47

# 128K machine, same story
tools/play.py --tap ../variants/bug06/chess.tap --machine hc128 \
    --fen '5k2/1p6/2n5/3pp3/3PP3/2N5/1P6/5K2 b - - 0 1' --depth 5
```

Without the helper script (note the digit goes **before** `l`: the strength keys
set both sides' search depth, while a tape load only restores White's):

```sh
cd arms/harness
tools/chesspos.py tap ../variants/bug06/chess.tap /tmp/bug06.tap \
    --fen '5k2/1p6/2n5/3pp3/3PP3/2N5/1P6/5K2 b - - 0 1' --depth 5
./build/hc91emu --machine 48k --rom roms/48.rom /tmp/bug06.tap --autoload \
    --turbo --type "5l@700" --frames 4500 --text
```

## Expected

Each level must search deeper than the one below it, so the move and/or the
score must change as the level rises. On a correct build the same position gives

| level | `Move` | `Eval` |
|-------|--------|--------|
| 2     | f8f7   | 0      |
| 3     | d5e4   | 30     |
| 4     | d5e4   | 30     |
| 5     | d5e4   | 30     |

and the middlegame position goes from `d5g2` / `47` at level 2 to `d5g2` / `77`
at level 5. The 48K and 128K builds must agree with each other.

## Also observed

- The built-in self-test (`T`) passes: `PERFT OK - movegen verified`, including
  the incremental key/phase/eval-accumulator check.
- The initial board renders pixel-identical to `initial_golden.png`.
- What the engine does play is not nonsense: it takes a free queen
  (`rnbqkbnr/pppp1ppp/4p3/3Q4/8/8/PPPP1PPP/RNB1KBNR b - - 0 1` → `e6xd5`), and
  it finds a mate in one (`r7/8/8/8/8/4k3/8/4K3 b - - 0 1` → `a8a1`,
  `Checkmate! Black wins`). It just never plays better than level 2.
- Move legality, castling, en passant, promotion, mate/stalemate detection and
  the draw rules all behave normally in spot checks.


## Submission X — source changes

```diff
--- a/chess.asm
+++ b/chess.asm
@@ -1406,6 +1406,12 @@
         ld (moveCount),hl
         ld a,(saveBuf+70)
         ld (aiDepth),a
+        ld (blackDepth),a       ; the save block carries ONE strength byte —
+                                ; restore it for BOTH sides, exactly as the
+                                ; 1..5 keys and newGame set it.  Restoring
+                                ; only aiDepth left the engine (Black) at the
+                                ; new-game default 2 while the panel showed
+                                ; the loaded level: "Level 5", depth-2 play.
         ld a,0xFF
         ld (selSq),a
         ld sp,0xFFF0           ; clean stack, return to the main loop

--- a/tt.inc
+++ b/tt.inc
@@ -4,7 +4,8 @@
 ;  flag: 0 exact, 1 lower bound (>=beta), 2 upper bound (<=alpha).
 ;  depth 0 marks an empty slot.
 ;
-;  48K: 8 KB / 1024 buckets at 0x6000, addressed directly.
+;  48K: 4 KB / 512 buckets at TT_BASE = 0xC000, addressed directly
+;  (ttAddr masks the key with 0x01FF; ttClear wipes 0x1000 bytes).
 ;  128K (is128=1): 64 KB / 8192 buckets across the four spare 16K RAM
 ;  banks (1,3,4,6) paged through 0x7FFD into the 0xC000 window.  Each
 ;  access stages the 8-byte entry to/from ttStage (non-pageable RAM) with
@@ -233,8 +234,8 @@
         ; usable for a cutoff only if entry depth >= current depth
         ld a,(ttEntDepth)
         ld hl,ttCurDepth
-        cp (hl)
-        jr z,ttNoCut
+        cp (hl)                  ; CF=1 <=> entDepth < curDepth
+        jr c,ttNoCut             ; shallower entry -> not usable, search on
         ld a,(ttEntFlag)
         or a
         jr z,ttExact

```

## Submission X — tests added

```
--- changes to the accompanying verification package (61632 bytes of diff) ---
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/bridge/a check script SUBMISSION/the the check suite
--- BASELINE/bridge/a check script	2026-07-29 22:59:13.374886388 +0200
+++ SUBMISSION/the the check suite	2026-08-01 17:02:36.975151331 +0200
@@ -190,7 +190,7 @@
 #       loop's updateTerminal does.  A forced repetition therefore scores as
 #       whatever the static eval says, not as 0.
 # =====================================================================
-src = open("/media/sf_Projects/HC91_emulator/chess/engine.inc").read()
+src = open("SUBMISSION/variants/bug06/engine.inc").read()
 ok("countReps" not in src, "F11: engine.inc now mentions countReps")
 ok("halfmove" not in src, "F11: engine.inc now mentions halfmove")
 EVID.append("F11 engine.inc (negamax + quiesce) contains no reference to "
Only in SUBMISSION/specification/bridge: a check script
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/bridge/emu.py SUBMISSION/the the check suite
--- BASELINE/bridge/emu.py	2026-07-29 22:44:14.362471728 +0200
+++ SUBMISSION/the the check suite	2026-08-01 17:15:19.990777272 +0200
@@ -20,10 +20,22 @@
 import subprocess
 import tempfile
 
-EMU = "/media/sf_Projects/HC91_emulator/build/hc91emu"
-ROM = "/media/sf_Projects/HC91_emulator/roms/48.rom"
-TAP = os.path.join(os.path.dirname(os.path.abspath(__file__)),
-                   "..", "artifacts", "chess.tap")
+_HERE = os.path.dirname(os.path.abspath(__file__))
+_WS = os.path.normpath(os.path.join(_HERE, "..", ".."))
+
+EMU = os.path.join(_WS, "harness", "build", "hc91emu")
+ROM = os.path.join(_WS, "harness", "roms", "48.rom")
+
+# Verify where it RUNS (the method law 4).  The tape under test is the one the
+# VARIANT's Makefile builds, not the pinned copy in ../artifacts: a fault
+# re-injected into variants/bug06 must turn this gate red.  ../artifacts is
+# only the fallback (and the historical reference the fixed build reproduces
+# byte for byte).  HC91_TAP overrides both.
+_BUILT = os.path.join(_WS, "variants", "bug06", "chess.tap")
+_PINNED = os.path.join(_HERE, "..", "artifacts", "chess.tap")
+TAP = os.environ.get("HC91_TAP") or (_BUILT if os.path.exists(_BUILT) else _PINNED)
+TAP_PROVENANCE = ("variants/bug06 build" if os.path.abspath(TAP) == os.path.abspath(_BUILT)
+                  else os.path.abspath(TAP))
 
 # --- provenance: chess.asm equates -------------------------------------
 A_BOARD      = 0xE000   # board    equ 0xE000   (128 bytes, 0x88 indexed)
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/bridge/run_all.sh SUBMISSION/the the check suite
--- BASELINE/bridge/run_all.sh	2026-07-29 22:55:43.254474282 +0200
+++ SUBMISSION/the the check suite	2026-08-01 18:24:13.569669045 +0200
@@ -10,6 +10,11 @@
 #   b5  emulator-as-oracle: 9 real games, engine legal lists vs reference implementation
 #   b6  alpha-beta == minimax, widened beyond the kernel's small scope
 #   b7  organic findings pinned as regression probes
+#   b8  TT depth sufficiency (S6), strength effectiveness (S7), strength
+#       application (S8) and search-within-level (S9):
+#       kernel witnesses, widened tree families, guard mutations, the Z80
+#       guard pinned in tt.inc, and 17 real engine runs over all three level
+#       doors (strength keypress, save-block load, opening book)
 #   s1-s3  SMT tier (z3): int16 no-overflow, memory layout, dead aspiration
 #
 # Stale bytecode is cleared first so a cached .pyc cannot mask a red gate.
@@ -44,13 +49,14 @@
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
+++ SUBMISSION/specification/DECISIONS.md	2026-08-01 21:30:47.875078582 +0200
@@ -224,7 +224,7 @@
 ### D-GATE-1 — The gate is judged by exit code, and clears its own caches
 
 `bridge/run_all.sh` deletes `__pycache__` and the stale `spec/specification.olean`
-before running, then judges each of the 11 layers by **exit status only** and
+before running, then judges each of the 12 layers by **exit status only** and
 prints the red ones by name. Tail-matching was rejected: a layer that prints
 "0 failures" and exits 1 (e.g. an exception after the summary line) would pass
 a tail check.
@@ -250,3 +250,202 @@
   scope** entirely. They are inputs to the position, not rules of the game;
   F1 and F6 both note that they are the paths by which an out-of-specification
   position could reach the engine.
+
+---
+
+### D-BUG06-1 — The strength setting is specified as TWO clauses, not one
+
+**Context.** bug06: `tt.inc ttProbe` shipped `jr z,ttNoCut` (0x28) where the
+sound guard is `jr c,ttNoCut` (0x38). `cp (hl)` sets CF iff
+`entDepth < curDepth`, so the shipped test refused a cutoff only on an EXACT
+depth match and admitted every SHALLOWER entry. The existing specification could
+not see it: C1..C14 constrain the moves and the state (all still correct), and
+D4 deliberately declines to claim that the TT preserves the minimax value
+(T21d), so S1..S4 were satisfied too.
+
+**Chosen.** Two new clauses.
+* **S6 `ttDepthSufficient`** — the mechanism: a TT cutoff is only ever taken
+  from an entry at least as deep as the node it answers. Cheap, decidable,
+  and pinned to the Z80 flag semantics (`T26a`: `!cpCarry` ≡ `curDepth ≤
+  entDepth` over all reachable depth pairs).
+* **S7 `levelEffective`** — the user-visible consequence: observations of the
+  same position at different levels are not all the same answer.
+
+**Rejected — S6 alone.** It is unobservable from outside the engine: the
+emulator can read `aiDepth`, the move and the score, but not a probe. A
+specification whose only new clause needs a tracing build would have left the
+shipped tape unbridged; S7 is what layer b8 part E can actually falsify.
+
+**Rejected — S7 alone.** "Some level differs from some other" is satisfiable
+by an engine that is merely *noisy* across levels; it names no mechanism, so a
+violation would not point at a line of code. S6 is what makes the finding
+vocabulary specific.
+
+**Rejected — claiming `TT-with-a-sound-guard ⇒ minimax`.** False in general
+(a fail-soft entry is a bound, not a value) and it would re-open D4's
+deliberate non-claim. The model (`nmTT`/`idSearch`/`idValue`) claims only what
+it can: with the sound guard level D reports the depth-D value *in this model*,
+and with bug06's guard every level ≥ 2 reports the depth-2 value (`T27c`) —
+the incident itself, as a theorem (the method law 6).
+
+**Assumptions.** (i) The `nmTT` model abstracts away windows, null move, LMR,
+reverse futility and quiescence; the mechanism it keeps is probe/cut/store,
+the root's no-cut rule, and one table across iterations. (ii) The model is a
+TREE, so no two nodes share a key — under the sound guard the table therefore
+never cuts *there*, and the sound guard's own cutoffs are exercised at the
+clause level (`T28a`/`T28b`) and exhaustively by `T28g` instead.
+**Recorded residual:** S6 forbids an *unsound* guard, not an *over-conservative*
+one — `jr nz` (cut only on an exact depth match) is sound, loses pruning, and
+is deliberately NOT flagged (b8 part C asserts this, so the detector's noise
+floor is visible rather than assumed).
+
+---
+
+### D-BUG06-2 — The bridge tests the BUILD, not the pinned artifact
+
+**Chosen.** `bridge/emu.py` now boots `variants/bug06/chess.tap` — the tape the
+variant's own `Makefile` produces — falling back to `specification/artifacts/chess.tap`
+only if it is absent (`HC91_TAP` overrides both).
+
+**Rejected — keep booting `specification/artifacts/chess.tap`.** Concrete failure
+mode, observed: with the fault present in `variants/bug06/tt.inc`, the whole
+11-layer gate was GREEN, because every emulator layer was running a *different*
+tape. Verify where it runs (the method law 4). With ONLY the `tt.inc` fix applied the
+two were byte-identical (md5 783b72ba018897b1311a7af0295ab041) — recorded
+evidence that the injected fault was exactly one byte, 0x38 → 0x28. They are
+**no longer** identical: D-BUG06-4 adds a 3-byte instruction to the load path,
+so the build under test is now `2eba0494682c9a4ddcb2068ffb6edadd`.
+
+---
+
+### D-BUG06-3 — `make` did not depend on the file that was edited
+
+`variants/bug06/Makefile` listed `SRC = chess.asm movegen.inc engine.inc
+pieces.inc`, omitting the three other `include`s (`perft.inc`, `zobrist.inc`,
+`tt.inc`). Editing `tt.inc` therefore produced *no rebuild* and a silently
+stale `chess.bin`. Fixed by listing every included file. Rejected alternative —
+"always `make clean` first": it hides the defect rather than removing it, and
+the next reader gets the same silent staleness.
+
+---
+
+### D-BUG06-4 — S8 `levelApplied`: the level set reaches the side that moves
+
+> **SUPERSEDED IN PART by D-BUG06-5.**  This entry was written with the badge
+> "the level *searched*".  Adversarial round 2 showed that is more than S8
+> decides — `effDepth` is the bound `aiMove` loads, not the depth it reaches.
+> The entry is kept verbatim below (append-only; supersede, never delete); read
+> D-BUG06-5 for the corrected clause statement.  The heading above is the only
+> line amended, so that a reader scanning headings is not misled.
+
+**Context.** The Beat-4 adversarial round produced a BLOCKING finding: the
+shipped, already-fixed build still reproduced the bug report's table through
+the game's own save/load door. `chess.asm`'s load path restored `aiDepth`
+only; `blackDepth` — the field `aiMove` reads when the engine is Black — kept
+the new-game default 2, while the panel prints `aiDepth`. Measured:
+`aiDepth=5 blackDepth=2 effDepth=2 -> f8f7 0` at every saved level.
+
+**Chosen — fix the engine AND add a third clause.**
+* Engine: `ld (blackDepth),a` after `ld (aiDepth),a` in the load path. The save
+  block carries exactly one strength byte (`SAVELEN`); restoring it to one side
+  only was the defect.
+* specification: **S8 `levelApplied`** — `effDepth == cfgSelected(c) && effDepth ==
+  aiDepth`, i.e. the depth actually searched is the depth configured for the
+  side to move *and* the depth the panel shows.  *(Superseded: "actually
+  searched" is wrong — see D-BUG06-5.)*
+
+**Rejected — record it as a known S7 violation and scope the clause to "the
+keypress path".** That is the cheaper option and it preserves byte-identity
+with `specification/artifacts/chess.tap`. Rejected because the residual it would
+leave is the reported bug: a user who saves at level 5 and reloads gets a
+level-2 engine and a panel that says 5. A specification whose clause the shipped
+artifact violates on a reachable path is not a specification; and the the method rule for
+a false-looking finding on a real case — fix it in spec, reference implementation or shell, never
+by special-casing the test — applies a fortiori to a TRUE one.
+**Accepted cost:** the tape is no longer byte-identical to the pristine
+artifact (`2eba0494682c9a4ddcb2068ffb6edadd`, 13,519 code bytes vs 13,516);
+the byte-identity evidence about the *injected* fault is preserved in writing
+(FIX_NOTES §3) rather than in the artifact.
+
+**Rejected — extend S7 instead of adding S8.** S7 is a property of a SET of
+observations ("the answers are not all equal"); S8 is a property of ONE
+observation ("what you searched is what you were told to"). Folding them would
+have produced a clause with two quantifier shapes and no clean negative test.
+Keeping them apart also buys the discriminating power that closed the
+reviewer's proven coverage hole: a silent level cap at 3 satisfies S7 and fails
+S8 (kernel theorem T30f), and before S8 existed that mutant passed the entire
+gate.
+
+**Assumption.** S8's inputs are read from the engine's own memory —
+`aiDepth` 0xE08A, `blackDepth` 0xE15E, `effDepth` 0xE15F, `sideToMove` 0xE080
+(the mover is `stm ^ 8`, since the engine's move has already flipped it).
+Falsifiability tier: MONITORED — `effDepth` is written by `aiMove` and the
+expected value comes from the level the harness asked for, so the two sides of
+the clause have independent sources.
+
+---
+
+### D-BUG06-5 — S9 and the `searched` guard: what `effDepth` does and does not say
+
+**Context.** Adversarial round 2 produced two blocking findings against the S8
+introduced in D-BUG06-4, both confirmed by execution.
+
+1. **S8's badge overclaimed.** `effDepth` (0xE15F) is the bound `aiMove`
+   *loads*, not the depth the loop *reaches*. `aidIter` (0xE0F4) is the depth
+   reached, and on both bug-report positions it is **3** at levels 3, 4 and 5 —
+   `clkBudgetExceeded` (engine.inc:2187-2194, budget = remaining clock / 32)
+   stops the deepening. So the level-4 and level-5 golden rows were pinning
+   "level ≥ 3", and a cap applied *inside* the loop passed the entire gate and
+   `make test`.
+2. **S8 false-alarmed on the opening book.** `aiMove` does `call tryBook /
+   ret c` **before** `ld (effDepth),a`, so a book reply leaves `effDepth`
+   stale — 0 on a cold boot. Measured after 1.e4 at level 5:
+   `LevelCfg(aiDepth=5, blackDepth=5, stm=8, effDepth=0)` ⇒ `S8 = False` on the
+   most ordinary path in the program.
+
+**Chosen.**
+* **S8 restated to what it decides** — the configured level reached the side
+  that moves and matches the panel — with the "the level the engine SEARCHES"
+  wording removed from the spec, the reference impl
```

## Submission Y — source changes

```diff
--- a/engine.inc
+++ b/engine.inc
@@ -1425,6 +1425,15 @@
 ttfEx:
         xor a                    ; exact
 ttfStore:
+        ; ttCurDepth is a single global, and every child's ttProbe overwrote it
+        ; with the child's depth on the way down.  Restamp it from this node's
+        ; own per-ply depth, or the entry goes into the table labelled with a
+        ; subtree's depth and the probe's depth test above is meaningless.
+        ld c,a                   ; save the bound flag
+        call ptrDepth
+        ld a,(hl)
+        ld (ttCurDepth),a
+        ld a,c
         call ttStore
         ld hl,(bestScoreTmp)
         ret

--- a/tt.inc
+++ b/tt.inc
@@ -4,7 +4,7 @@
 ;  flag: 0 exact, 1 lower bound (>=beta), 2 upper bound (<=alpha).
 ;  depth 0 marks an empty slot.
 ;
-;  48K: 8 KB / 1024 buckets at 0x6000, addressed directly.
+;  48K: 4 KB / 512 buckets at TT_BASE (0xC000), addressed directly.
 ;  128K (is128=1): 64 KB / 8192 buckets across the four spare 16K RAM
 ;  banks (1,3,4,6) paged through 0x7FFD into the 0xC000 window.  Each
 ;  access stages the 8-byte entry to/from ttStage (non-pageable RAM) with
@@ -231,10 +231,11 @@
         ld a,(ttStage+7)
         ld (ttTo),a
         ; usable for a cutoff only if entry depth >= current depth
+        ; (CF=1 <=> entDepth < curDepth -> the entry is too shallow to trust)
         ld a,(ttEntDepth)
         ld hl,ttCurDepth
         cp (hl)
-        jr z,ttNoCut
+        jr c,ttNoCut
         ld a,(ttEntFlag)
         or a
         jr z,ttExact
@@ -279,7 +280,9 @@
         ret
 
 ; ttStore(score in (nmScore-ish)) — write the node result.
-; Inputs: (ttCurDepth)=depth, (bestScoreTmp)=score, A=flag,
+; Inputs: (ttCurDepth)=depth — the caller must restamp it from the node's own
+;         per-ply depth, since the children's probes have overwritten it,
+;         (bestScoreTmp)=score, A=flag,
 ;         (nbFromArr[ply])/(nbToArr[ply]) = best move.
 ttStore:
         ld (ttEntFlag),a

```

## Submission Y — tests added

```
--- level_test.py (10443 bytes) ---
#!/usr/bin/env python3
"""level_test.py — regression test for the engine strength setting (levels 1-5).

Bug06 symptom: raising the level changed the panel and the time charged to the
clock, but levels 3, 4 and 5 returned the level-2 move and the level-2 score
bit for bit.  Cause: the transposition-table probe (`tt.inc`, ttProbe) used the
wrong condition on its depth test, so it rejected the one case that is safe
(entry depth == current depth) and accepted every entry that is too shallow.

Four assertions, three of them over a positions x levels x machines matrix:

  1. GOLDEN     every cell must produce exactly the documented move and score.
  2. DISTINCT   named level pairs must NOT produce the same answer.  This is
                the bug's signature stated without reference to the golden
                numbers, so it survives an eval re-baseline.
  3. AGREEMENT  the 48K (direct TT) and 128K (banked TT) builds must agree in
                every cell.
  4. TT-STAMP   white-box: after a depth-3 search the transposition table must
                hold entries stamped with more than one depth.  ttStore takes
                the depth from the global ttCurDepth, which every child probe
                overwrites on the way down, so it is easy to regress into
                stamping every entry with the frontier depth — which would
                make the probe's depth test (the thing this bug was about)
                gate on a constant.  Not observable in the move/score matrix.

On the two positions quoted in the bug report the answer stops changing above
level 3 *on a correct build too* — the engine paces itself by the clock
(`clkBudgetExceeded` in chess.asm stops iterative deepening once the move's
time budget is gone), and in those positions iteration 4 never starts.  That is
why the report's own "expected" table has L3 = L4 = L5.  So a third, sparse
position is included: it is cheap enough that all five iterations run, and its
answer changes at *every* level.  Without it the L4 and L5 rows would be
vacuous — a build that hard-wired levels 4 and 5 back to level 3 would pass.

    ./level_test.py                          # tests ./chess.tap
    ./level_test.py --tap /tmp/other.tap     # tests some other build
    ./level_test.py --machines 48k           # skip the (slower) 128K half

Deterministic: identical arguments give an identical run.  Exit status 0 iff
every check passed.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_HARNESS = os.path.normpath(os.path.join(HERE, '..', '..', 'harness'))
DEFAULT_TAP = os.path.join(HERE, 'chess.tap')

# name -> (FEN, {level: (move, score)}, [level pairs that must differ])
#
# 'endgame' and 'middlegame' are the two positions from the bug report; their
# L2 and L3..L5 rows are the values the report says a correct build produces.
# 'pawn-endgame' is sparse enough for the clock to afford all five iterations,
# so it pins levels 4 and 5 down as well.  All other cells were measured on the
# fixed build and agree between 48K and 128K.
POSITIONS = {
    'endgame': (
        '5k2/1p6/2n5/3pp3/3PP3/2N5/1P6/5K2 b - - 0 1',
        {1: ('f8f7', 20), 2: ('f8f7', 0), 3: ('d5e4', 30),
         4: ('d5e4', 30), 5: ('d5e4', 30)},
        [(2, 3)],
    ),
    'middlegame': (
        'r3k2r/pp3ppp/2n1b3/3q4/3P4/2N1B3/PP3PPP/R2QK2R b KQkq - 0 1',
        {1: ('d5g2', 37), 2: ('d5g2', 47), 3: ('d5g2', 77),
         4: ('d5g2', 77), 5: ('d5g2', 77)},
        [(2, 3)],
    ),
    'pawn-endgame': (
        '8/6k1/8/8/8/8/1P6/6K1 b - - 0 1',
        {1: ('g7f6', -44), 2: ('g7f6', -74), 3: ('g7f6', -54),
         4: ('g7g6', -64), 5: ('g7g6', -94)},
        [(1, 2), (2, 3), (3, 4), (4, 5)],
    ),
}

# Frames left for the engine after the position is loaded.  Must comfortably
# cover the deepest search, otherwise the snapshot catches the engine still
# thinking (lastMove '-') and the run is inconclusive, not a pass.
DEFAULT_TAIL = 8000


def probe(harness, tap, machine, fen, depth, tail, sna=None):
    """Load `fen` at `depth` on `machine`, let the engine reply, read it back."""
    cmd = [sys.executable, os.path.join(harness, 'tools', 'play.py'),
           '--tap', os.path.abspath(tap), '--fen', fen, '--depth', str(depth),
           '--machine', machine, '--tail', str(tail), '--json']
    if sna:
        cmd += ['--sna', os.path.abspath(sna)]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=harness)
    if r.returncode != 0:
        raise SystemExit('level_test: play.py failed (%d)\n%s' % (r.returncode, r.stderr))
    return json.loads(r.stdout)


def tt_base():
    """TT_BASE from chess.asm, so this check follows the source, not a guess."""
    asm = os.path.join(HERE, 'chess.asm')
    if not os.path.exists(asm):
        return None
    m = re.search(r'^TT_BASE\s+equ\s+(0x[0-9A-Fa-f]+)', open(asm).read(), re.M)
    return int(m.group(1), 16) if m else None


def tt_depth_histogram(sna_path, base):
    """Depths stamped on the live entries of the 48K table (4 KB, 8 bytes/entry).

    A depth of 0 marks an empty slot (tt.inc), so those are skipped.
    """
    ram = open(sna_path, 'rb').read()[27:]          # .sna: 27-byte header, then 0x4000..
    hist = {}
    for off in range(0, 0x1000, 8):
        d = ram[base - 0x4000 + off + 4]
        if d:
            hist[d] = hist.get(d, 0) + 1
    return hist


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tap', default=DEFAULT_TAP, help='the build under test')
    ap.add_argument('--harness', default=DEFAULT_HARNESS)
    ap.add_argument('--machines', default='48k,hc128',
                    help='comma separated: 48k, hc128 (default both)')
    ap.add_argument('--tail', type=int, default=DEFAULT_TAIL,
                    help='frames the engine gets to reply (default %d)' % DEFAULT_TAIL)
    ap.add_argument('-v', '--verbose', action='store_true')
    a = ap.parse_args(argv)

    # play.py runs with cwd=harness, so resolve --harness before that cd.
    harness = os.path.abspath(a.harness)
    machines = [m for m in a.machines.replace(',', ' ').split() if m]
    fails = []
    got = {}                                # (machine, position, level) -> (move, score)

    # --- 1. GOLDEN -------------------------------------------------------
    for machine in machines:
        for name in sorted(POSITIONS):
            fen, table, _ = POSITIONS[name]
            for level in sorted(table):
                st = probe(harness, a.tap, machine, fen, level, a.tail)
                move, score = st['lastMove'], st['lastScore']
                got[(machine, name, level)] = (move, score)
                where = '%s %s L%d' % (machine, name, level)
                if a.verbose:
                    print('  %-26s %s %d' % (where, move, score))
                if move == '-':
                    fails.append('%s: the engine had not moved yet '
                                 '(inconclusive - raise --tail)' % where)
                    continue
                if st['gameStateName'] != 'play':
                    fails.append('%s: game state is %r, expected \'play\''
                                 % (where, st['gameStateName']))
                want = table[level]
                if (move, score) != want:
                    fails.append('%s: got %s/%d, expected %s/%d'
                                 % (where, move, score, want[0], want[1]))

    # --- 2. DISTINCT -----------------------------------------------------
    # The bug's signature: a level that silently returns a shallower level's
    # answer.  Asserted independently of the golden numbers above.
    for machine in machines:
        for name in sorted(POSITIONS):
            for lo, hi in POSITIONS[name][2]:
                x, y = got.get((machine, name, lo)), got.get((machine, name, hi))
                if x is None or y is None:
                    continue
                if x == y:
                    fails.append('%s %s: level %d returns the level-%d answer '
                                 '(%s/%d) - the level setting is not deepening '
                                 'the search' % (machine, name, hi, lo, x[0], x[1]))

    # --- 3. AGREEMENT ----------------------------------------------------
    if '48k' in machines and 'hc128' in machines:
        for name in sorted(POSITIONS):
            for level in sorted(POSITIONS[name][1]):
                x, y = got.get(('48k', name, level)), got.get(('hc128', name, level))
                if x != y:
                    fails.append('%s L%d: 48K says %s but 128K says %s'
                                 % (name, level, x, y))

    # --- 4. TT-STAMP (48K only: the 128K entries live in banked RAM) -----
    if '48k' in machines:
        base = tt_base()
        if base is None:
            fails.append('tt-stamp: could not read TT_BASE from chess.asm')
        else:
            sna = os.path.join(tempfile.mkdtemp(prefix='leveltest.'), 'tt.sna')
            fen = POSITIONS['endgame'][0]
            probe(harness, a.tap, '48k', fen, 3, a.tail, sna=sna)
            hist = tt_depth_histogram(sna, base)
            if a.verbose:
                print('  %-26s %s' % ('48k tt depth histogram', dict(sorted(hist.items()))))
            if not hist:
                fails.append('tt-stamp: the transposition table is empty after a '
                             'depth-3 search')
            elif max(hist) < 2:
                fails.append('tt-stamp: after a depth-3 search every one of the %d '
                             'live TT entries is stamped depth %d - ttStore is '
                             'recording a child\'s depth, so the probe\'s depth '
                             'test gates on a constant'
                             % (sum(hist.values()), max(hist)))

    if fails:
        print('chess: FAIL - engine level ladder')
        for f in fails:
            print('   %s' % f)
        return 1
    pairs = sum(len(POSITIONS[n][2]) for n in POSITIONS) * len(machines)
    print('chess: level ladder OK (%d positions x levels 1-5 on %s; %d level '
          'steps each change the answer; TT depth-stamped)'
          % (len(POSITIONS), '/'.join(machines), pairs))
    return 0


if __name__ == '__main__':
    sys.exit(main())

```
