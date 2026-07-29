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
