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
