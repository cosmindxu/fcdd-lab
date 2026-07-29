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
