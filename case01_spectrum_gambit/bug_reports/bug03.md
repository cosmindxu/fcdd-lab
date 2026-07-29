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
