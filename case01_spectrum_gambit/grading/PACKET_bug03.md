# Blind review packet — bug03

Two independent submissions fixed the SAME reported defect in the same
Z80 codebase. You are not told who wrote them or by what process, and
the two are not necessarily comparable in style. Judge only what is here.

## The reported defect

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


## Submission X — source changes

```diff
--- a/movegen.inc
+++ b/movegen.inc
@@ -798,9 +798,9 @@
         or a
         jr z,mkNoProm
         ld b,a
-        ld a,(mkSide)
-        or b
-        jr mkPut
+        ld a,(mkSide)            ; COLOUR BIT ONLY — never (mkPiece): the pawn
+        or b                     ; is WP=1/BP=9, so OR-ing the whole piece
+        jr mkPut                 ; leaves type bit 0 set and turns R->Q, N->B
 mkNoProm:
         ld a,(mkPiece)
 mkPut:

```

## Submission X — tests added

```
(no new test files)
```

## Submission Y — source changes

```diff
--- a/movegen.inc
+++ b/movegen.inc
@@ -797,10 +797,11 @@
         ld a,(mkPromo)
         or a
         jr z,mkNoProm
-        ld b,a
-        ld a,(mkSide)
-        or b
-        jr mkPut
+        ld b,a                   ; B = promoted type (2=N 3=B 4=R 5=Q)
+        ld a,(mkPiece)
+        and COLBIT               ; colour only: the moving pawn's type bits
+        or b                     ; must not leak in (P|R would read as Q,
+        jr mkPut                 ; P|N as B).  Same form as keyUpdate/pstDelta.
 mkNoProm:
         ld a,(mkPiece)
 mkPut:

```

## Submission Y — tests added

```
--- test_promotion.py (6411 bytes) ---
#!/usr/bin/env python3
"""test_promotion.py — regression test for the promotion piece chooser.

The piece the player picks at the `Promote: Q=Queen R B N` prompt must be the
piece that actually lands on the last rank — for both colours, for a plain
push and for a capture, and it must then *behave* as that piece.

This is the test for bug03: `makeMove` built the promoted piece as
`movingPiece OR promoType` instead of `colourBit OR promoType`, so the pawn's
own type bit (bit0 of WP=1 / BP=9) leaked in and turned R(4) into 5=Q and
N(2) into 3=B.  Q(5) and B(3) already have bit0 set and so looked fine, which
is why only two of the four choices were visibly broken.

Each case boots the build under test in the harness emulator, loads a position
through the game's own tape-load, plays the move with the promotion key, and
reads the resulting board straight out of the 48K memory image.

    ./test_promotion.py                          # ./chess.tap on 48k
    ./test_promotion.py --machine 48k,hc128
    ./test_promotion.py --tap /tmp/other/chess.tap

Exit status 0 iff every case passes.
"""

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# material scores the engine reports, white-positive
QUEEN, ROOK, BISHOP, KNIGHT, PAWN = 900, 500, 330, 320, 100

WPUSH = '4k3/P7/8/8/8/8/8/4K3 w - - 0 1'      # white pawn a7, a8 empty
BPUSH = '4k3/8/8/8/8/8/p7/4K3 b - - 0 1'      # black pawn a2, a1 empty
WCAP = 'r3k3/1P6/8/8/8/8/8/4K3 w - - 0 1'     # white b7 takes the rook on a8
BCAP = '4k3/8/8/8/8/8/1p6/R3K3 b - - 0 1'     # black b2 takes the rook on a1
# a7/h7 pawns with the black king off the 8th rank and off the a-file, so a
# promotion on a8 gives no check and the follow-up moves are playable.
BEHAVE = '8/P6p/4k3/8/8/8/8/4K3 w - - 0 1'

# name, start fen, moves, expected board placement, expected material,
# expected side to move at the end
CASES = [
    # --- plain push, White: the four choices must give the four pieces -----
    ('white push =Q', WPUSH, 'a7a8q', 'Q3k3/8/8/8/8/8/8/4K3', QUEEN, 'black'),
    ('white push =R', WPUSH, 'a7a8r', 'R3k3/8/8/8/8/8/8/4K3', ROOK, 'black'),
    ('white push =B', WPUSH, 'a7a8b', 'B3k3/8/8/8/8/8/8/4K3', BISHOP, 'black'),
    ('white push =N', WPUSH, 'a7a8n', 'N3k3/8/8/8/8/8/8/4K3', KNIGHT, 'black'),
    # --- plain push, Black -------------------------------------------------
    ('black push =Q', BPUSH, 'a2a1q', '4k3/8/8/8/8/8/8/q3K3', -QUEEN, 'white'),
    ('black push =R', BPUSH, 'a2a1r', '4k3/8/8/8/8/8/8/r3K3', -ROOK, 'white'),
    ('black push =B', BPUSH, 'a2a1b', '4k3/8/8/8/8/8/8/b3K3', -BISHOP, 'white'),
    ('black push =N', BPUSH, 'a2a1n', '4k3/8/8/8/8/8/8/n3K3', -KNIGHT, 'white'),
    # --- capture on the last rank, White (the black rook on a8 is taken) ---
    ('white capture =Q', WCAP, 'b7a8q', 'Q3k3/8/8/8/8/8/8/4K3', QUEEN, 'black'),
    ('white capture =R', WCAP, 'b7a8r', 'R3k3/8/8/8/8/8/8/4K3', ROOK, 'black'),
    ('white capture =B', WCAP, 'b7a8b', 'B3k3/8/8/8/8/8/8/4K3', BISHOP, 'black'),
    ('white capture =N', WCAP, 'b7a8n', 'N3k3/8/8/8/8/8/8/4K3', KNIGHT, 'black'),
    # --- capture on the last rank, Black -----------------------------------
    ('black capture =Q', BCAP, 'b2a1q', '4k3/8/8/8/8/8/8/q3K3', -QUEEN, 'white'),
    ('black capture =R', BCAP, 'b2a1r', '4k3/8/8/8/8/8/8/r3K3', -ROOK, 'white'),
    ('black capture =B', BCAP, 'b2a1b', '4k3/8/8/8/8/8/8/b3K3', -BISHOP, 'white'),
    ('black capture =N', BCAP, 'b2a1n', '4k3/8/8/8/8/8/8/n3K3', -KNIGHT, 'white'),
    # --- and it must *behave* as the chosen piece afterwards ---------------
    # =N then Na8-b6: a knight move no bishop can make, so this fails if the
    # buggy build put a bishop on a8.
    ('=N then Nb6 (not a bishop)', BEHAVE, 'a7a8n,h7h6,a8b6',
     '8/8/1N2k2p/8/8/8/8/4K3', KNIGHT - PAWN, 'black'),
    # =R then Ra8-h1: a clear diagonal only a queen could use, so the move
    # must be refused and White must still be to move.  Fails if the buggy
    # build put a queen on a8.
    ('=R then Rh1 refused (not a queen)', BEHAVE, 'a7a8r,h7h6,a8h1',
     'R7/8/4k2p/8/8/8/8/4K3', ROOK - PAWN, 'white'),
]


def run(play, tap, machine, fen, moves):
    cmd = [sys.executable, play, '--tap', tap, '--fen', fen, '--moves', moves,
           '--two-player', '--machine', machine, '--json']
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError('play.py failed: %s\n%s' % (' '.join(cmd), out.stderr))
    return json.loads(out.stdout)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tap', default=os.path.join(HERE, 'chess.tap'),
                    help='the build under test (default: chess.tap next door)')
    ap.add_argument('--harness', default=os.path.join(HERE, '..', '..', 'harness'),
                    help='harness directory holding tools/play.py')
    ap.add_argument('--machine', default='48k',
                    help='comma-separated machines to run, e.g. "48k,hc128"')
    args = ap.parse_args(argv)

    play = os.path.join(args.harness, 'tools', 'play.py')
    for path in (args.tap, play):
        if not os.path.exists(path):
            sys.exit('test_promotion: missing %s' % path)

    failures = []
    total = 0
    for machine in [m.strip() for m in args.machine.split(',') if m.strip()]:
        for name, fen, moves, board, material, side in CASES:
            total += 1
            st = run(play, args.tap, machine, fen, moves)
            got = (st['fen'].split()[0], st['material'], st['side'])
            want = (board, material, side)
            if got != want:
                failures.append('  %s [%s] %s\n      want board=%s material=%d %s\n'
                                '      got  board=%s material=%d %s'
                                % (machine, name, moves, want[0], want[1], want[2],
                                   got[0], got[1], got[2]))

    if failures:
        print('chess: FAIL - promotion chooser puts the wrong piece on the board')
        print('\n'.join(failures))
        return 1
    print('chess: promotion chooser OK (%d cases: Q/R/B/N, both colours, '
          'push + capture, and the piece behaves as chosen)' % total)
    return 0


if __name__ == '__main__':
    sys.exit(main())

```
