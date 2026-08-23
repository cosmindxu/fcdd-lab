# Blind review packet — bug06_r2

Two independent submissions repaired the SAME reported defect in the
same Z80 assembly codebase. You are not told who wrote them or by what
process. Judge only the source changes shown below.

## How to judge

Score each submission 1-5 on each axis, then say which you would merge.

- **correctness_risk** (1 = high risk it is wrong or incomplete, 5 = clearly
  correct and complete for the reported defect). Does the change actually
  address the reported behaviour? Could it break something else?
- **minimality** (1 = sprawling, changes far more than the defect requires,
  5 = tightly scoped to the fault). A larger change is not automatically
  worse -- judge whether the extra scope is warranted.
- **clarity** (1 = opaque, 5 = a reviewer can see why it is right).

Judge ONLY the assembly source changes shown. Both submissions were produced
under time and tooling conditions you are not told about. Do not speculate
about who wrote them or by what process; if you find yourself forming a theory
about the authors, say so in `blinding_note` and score the code regardless.


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
--- a/tt.inc
+++ b/tt.inc
@@ -234,7 +234,7 @@
         ld a,(ttEntDepth)
         ld hl,ttCurDepth
         cp (hl)
-        jr z,ttNoCut
+        jr c,ttNoCut ; entDepth < curDepth -> too shallow, no cut
         ld a,(ttEntFlag)
         or a
         jr z,ttExact

```

## Submission Y — source changes

```diff
--- a/tt.inc
+++ b/tt.inc
@@ -233,8 +233,8 @@ ; usable for a cutoff only if entry depth >= current depth
         ld a,(ttEntDepth)
         ld hl,ttCurDepth
-        cp (hl)
-        jr z,ttNoCut
+        cp (hl) ; CF=1 iff entDepth < curDepth
+        jr c,ttNoCut ; shallower entry: its score is not deep enough
         ld a,(ttEntFlag)
         or a
         jr z,ttExact

```
