# Blind review packet — bug04_r2

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

# bug04 — the engine leaves free pieces on the board and thinks it is winning when it is lost

**Build under test:** `arms/variants/bug04` — build with `make` (see its
`BUILD.md`). Emulator, drivers and the commands used below: `arms/harness`
(see `HOWTO.md`), 48K machine, `roms/48.rom`.

## Observed

The engine will not take material, and the sign of the score it prints is
inverted with respect to who is actually winning.

**1. It declines a free queen.** Give Black (the engine) a pawn capture of an
undefended white queen:

```
rnbqkbnr/pppp1ppp/4p3/3Q4/8/8/PPPP1PPP/RNB1KBNR b - - 0 1
```

At level 2 it plays `c7c6` and reports `Eval -90`; the queen is still on d5. At
level 3 it plays `g7g6`. It never plays `e6xd5`.

**2. It declines a free rook.** In `4k3/8/8/8/8/1n6/8/R3K3 b - - 0 1` the black
knight on b3 can take the undefended rook on a1. The engine plays `b3a5`
instead and the rook survives; the `Matl` readout goes to `+1` (White ahead)
where it should have gone to `-3`.

**3. Its score has the wrong sign.** In `4k3/8/8/8/8/8/8/QQ2K3 b - - 0 1` —
Black is a bare king against two queens — the engine reports

```
Eval 1766
```

i.e. it believes *it* is nearly eighteen pawns to the good while being
hopelessly lost. `Matl` on the same screen correctly reads `18` in White's
favour, so the two figures on the panel contradict each other.

Played out from the opening, the effect is that the engine gives pieces away
and does not take what is offered. The first few moves look normal because they
come out of the opening book.

## Repro

```sh
cd arms/harness
make build/hc91emu                       # once

tools/play.py --tap ../variants/bug04/chess.tap \
    --fen 'rnbqkbnr/pppp1ppp/4p3/3Q4/8/8/PPPP1PPP/RNB1KBNR b - - 0 1' --depth 2
#   lastMove c7c6      lastScore -90     material -100   (queen still on d5)

tools/play.py --tap ../variants/bug04/chess.tap \
    --fen '4k3/8/8/8/8/1n6/8/R3K3 b - - 0 1' --depth 2
#   lastMove b3a5      material 180

tools/play.py --tap ../variants/bug04/chess.tap \
    --fen '4k3/8/8/8/8/8/8/QQ2K3 b - - 0 1' --depth 2
#   lastScore 1766
```

Without the helper script:

```sh
cd arms/harness
tools/chesspos.py tap ../variants/bug04/chess.tap /tmp/bug04.tap \
    --fen 'rnbqkbnr/pppp1ppp/4p3/3Q4/8/8/PPPP1PPP/RNB1KBNR b - - 0 1'
./build/hc91emu --machine 48k --rom roms/48.rom /tmp/bug04.tap --autoload \
    --turbo --type "l@700" --frames 3200 --text
```

(the position has Black to move, so the engine moves as soon as it is loaded;
for level 3 and up press the digit before `l`, e.g. `--type "3l@700"`.)

## Expected

- `e6xd5` in position 1, with the engine's score jumping to about `+950` and
  `Matl` to `-10` (Black a queen up). A correct build plays it at every level.
- `b3xa1` in position 2, leaving `Matl` at `-3`.
- A deeply **negative** score in position 3 (a correct build reports about
  `-1786`), agreeing in sign with the `Matl` figure next to it.
- In general: more of your own material must score better for you, not worse,
  and the printed evaluation must agree in sign with who is ahead.

## Also observed

- The built-in self-test (`T`) passes: `PERFT OK - movegen verified`, including
  the incremental key/phase/eval-accumulator check.
- The initial board renders pixel-identical to `initial_golden.png`.
- Move legality is fine: the captures it declines are legal and can be played
  by hand in two-player mode (`V`); castling, en passant, promotion, mate,
  stalemate and the draw rules all behave normally in spot checks.
- Mate is still found when it is forced: from `r7/8/8/8/8/4k3/8/4K3 b - - 0 1`
  the engine plays `a8a1` and the game correctly ends `Checkmate! Black wins`.


## Submission X — source changes

```diff
--- a/engine.inc
+++ b/engine.inc
@@ -182,12 +182,12 @@
         ld de,(matVal)
         add hl,de
         ld a,b
-        and 8
-        ret nz
+        and 8 ; COLBIT: Z = white piece, NZ = black piece
+        ret z ; white scores POSITIVE (white-relative)
         ex de,hl
         ld hl,0
         or a
-        sbc hl,de
+        sbc hl,de ; black is negated
         ret
 pvsZero:
         ld hl,0

```

## Submission Y — source changes

```diff
--- a/engine.inc
+++ b/engine.inc
@@ -182,9 +182,9 @@
         ld de,(matVal)
         add hl,de
         ld a,b
-        and 8
-        ret nz
-        ex de,hl
+        and 8 ; colour bit: 0 = white
+        ret z ; white -> positive (white-relative)
+        ex de,hl ; black -> negate
         ld hl,0
         or a
         sbc hl,de

```
