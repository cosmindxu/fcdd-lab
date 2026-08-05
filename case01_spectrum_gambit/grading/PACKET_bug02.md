# Blind review packet — bug02

Two independent submissions fixed the SAME reported defect in the same
Z80 codebase. You are not told who wrote them or by what process, and
the two are not necessarily comparable in style. Judge only what is here.

## The reported defect

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


## Submission X — source changes

```diff
--- a/movegen.inc
+++ b/movegen.inc
@@ -903,11 +903,11 @@
         ld a,0xFF
         ld (epSquare),a
 mkHalf:
-        ld a,(mkPiece)
+        ld a,(mkPiece)           ; mover; "and 7" folds BP..BK onto WP..WK
         and 7
-        cp WP
+        cp WP                    ; a pawn move resets the fifty-move clock
         jr z,mkHm0
-        ld a,(mkCaptured)
+        ld a,(mkCaptured)        ; ...and so does any capture (incl. en passant)
         or a
         jr nz,mkHm0
         ld a,(halfmove)

```

## Submission X — tests added

```
--- test_fifty_move.py (7462 bytes) ---
#!/usr/bin/env python3
"""test_fifty_move.py — regression test for the fifty-move (halfmove) clock.

Drives the built chess.tap headlessly through the harness emulator from a set
of hand-made positions and checks the halfmove clock after each move.

The rule under test (movegen.inc, label `mkHalf` in `makeMove`):

    a PAWN move or a CAPTURE resets the clock to 0;
    everything else increments it;
    the game is drawn once the clock reaches 100.

The bug this was written for: `mkHalf` compared the mover against `WN`
(knight) instead of `WP` (pawn), so pawn moves incremented the clock and
knight moves reset it -> spurious "Draw (50-move)".

Usage:
    ./test_fifty_move.py                       # tests ./chess.tap
    ./test_fifty_move.py --tap /tmp/other.tap  # tests another build
    ./test_fifty_move.py -v                    # show every case

Exit status 0 if every case passes.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, '..', '..', 'harness'))
# Guess the harness next door; PYTHONPATH still wins, which is how the
# Makefile honours a HARNESS= override.
sys.path.append(os.path.join(HARNESS, 'tools'))
import chesspos                                          # noqa: E402

# name, start FEN, moves, expected halfmove, expected game state, expected
# board placement (FEN field 1) after the moves.
CASES = [
    # --- the reported symptom -------------------------------------------
    ('pawn push resets the clock',
     '4k3/8/8/8/8/8/PR6/4K3 w - - 98 60', 'a2a3', 0, 'play',
     '4k3/8/8/8/8/P7/1R6/4K3'),
    ('pawn push then a quiet move: 1, and the game is still running',
     '4k3/8/8/8/8/8/PR6/4K3 w - - 98 60', 'a2a3,e8e7', 1, 'play',
     '8/4k3/8/8/8/P7/1R6/4K3'),
    ('knight move increments the clock (it must NOT reset it)',
     '4k3/8/8/8/8/8/1R6/N3K3 w - - 40 60', 'a1b3', 41, 'play',
     '4k3/8/8/8/8/1N6/1R6/4K3'),

    # --- the draw must still fire when it is genuinely due ---------------
    ('99 + one quiet move = 100 = Draw (50-move)',
     '4k3/8/8/8/8/8/1R6/4K3 w - - 99 60', 'b2b3', 100, 'draw',
     '4k3/8/8/8/8/1R6/8/4K3'),
    ('98 + one quiet move = 99: not a draw yet (boundary)',
     '4k3/8/8/8/8/8/1R6/4K3 w - - 98 60', 'b2b3', 99, 'play',
     '4k3/8/8/8/8/1R6/8/4K3'),

    # --- every other way a pawn can move --------------------------------
    ('double pawn push resets the clock',
     '4k3/8/8/8/8/8/PR6/4K3 w - - 50 60', 'a2a4', 0, 'play',
     '4k3/8/8/8/P7/8/1R6/4K3'),
    ('pawn capture resets the clock',
     '4k3/8/8/8/8/1p6/P7/R3K3 w - - 40 60', 'a2b3', 0, 'play',
     '4k3/8/8/8/8/1P6/8/R3K3'),
    ('en-passant capture resets the clock',
     '4k3/1p6/8/P7/8/8/1R6/4K3 b - - 40 60', 'b7b5,a5b6', 0, 'play',
     '4k3/8/1P6/8/8/8/1R6/4K3'),
    ('promotion resets the clock',
     '4k3/P7/8/8/8/8/1R6/4K3 w - - 40 60', 'a7a8q', 0, 'play',
     'Q3k3/8/8/8/8/8/1R6/4K3'),
    ('black pawn move resets the clock (piece code 9, not 1)',
     '4k3/p7/8/8/8/8/1R6/4K3 b - - 60 60', 'a7a6', 0, 'play',
     '4k3/8/p7/8/8/8/1R6/4K3'),

    # --- captures by non-pawns still reset ------------------------------
    ('rook takes rook resets the clock',
     '4k3/8/8/8/8/8/1r6/1R2K3 w - - 40 60', 'b1b2', 0, 'play',
     '4k3/8/8/8/8/8/1R6/4K3'),

    # --- everything else increments -------------------------------------
    ('black knight move increments (piece code 10, not 2)',
     '4k3/8/n7/8/8/8/1R6/4K3 b - - 60 60', 'a6b4', 61, 'play',
     '4k3/8/8/8/1n6/8/1R6/4K3'),
    ('king move increments',
     '4k3/8/8/8/8/8/1R6/4K3 w - - 40 60', 'e1e2', 41, 'play',
     '4k3/8/8/8/8/8/1R2K3/8'),
    ('queen move increments',
     '4k3/8/8/8/8/8/8/3QK3 w - - 40 60', 'd1d4', 41, 'play',
     '4k3/8/8/8/3Q4/8/8/4K3'),
    ('castling increments (the king is the mover, nothing is captured)',
     '4k3/8/8/8/8/8/8/4K2R w K - 40 60', 'e1g1', 41, 'play',
     '4k3/8/8/8/8/8/8/5RK1'),
]


def run_case(emu, rom, rom_tap, fen, moves, tmpdir, idx,
             load_frame=700, wait=120, gap=900, tail=900, depth=2):
    """Boot rom_tap, load `fen` through the game's own tape load, play `moves`,
    return the decoded state dict.  Mirrors tools/play.py --two-player."""
    tap = os.path.join(tmpdir, 'pos%d.tap' % idx)
    blk = chesspos.tap_data_block(chesspos.fen_to_block(fen, depth))
    with open(tap, 'wb') as f:
        f.write(open(rom_tap, 'rb').read() + blk)
    sna = os.path.join(tmpdir, 'final%d.sna' % idx)

    cmd = [emu, '--machine', '48k', '--rom', rom, tap,
           '--autoload', '--turbo', '--save-sna', sna]
    frame = load_frame
    cmd += ['--type', 'vl@%d' % frame]        # V = two-player, L = load position
    frame += wait
    cursor = 'e2'
    for mv in [m for m in moves.replace(',', ' ').split() if m]:
        cmd += ['--type', '%sx@%d' % (chesspos.move_keys([mv], cursor), frame)]
        cursor = mv[2:4]
        frame += gap
    cmd += ['--frames', str(frame + tail)]

    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError('emulator failed (%d): %s' % (r.returncode, r.stderr))
    return chesspos.state_dict(chesspos.sna_ram(sna))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tap', default=os.path.join(HERE, 'chess.tap'))
    ap.add_argument('--emu', default=os.path.join(HARNESS, 'build', 'hc91emu'))
    ap.add_argument('--rom', default=os.path.join(HARNESS, 'roms', '48.rom'))
    ap.add_argument('-v', '--verbose', action='store_true')
    a = ap.parse_args(argv)

    for path in (a.tap, a.emu, a.rom):
        if not os.path.exists(path):
            sys.stderr.write('missing: %s\n' % path)
            return 2

    tmpdir = tempfile.mkdtemp(prefix='fifty.')
    failures = []
    for i, (name, fen, moves, want_hm, want_state, want_place) in enumerate(CASES):
        st = run_case(a.emu, a.rom, a.tap, fen, moves, tmpdir, i)
        got_place = st['fen'].split()[0]
        bad = []
        # placement first: it proves the move was actually played, so a
        # halfmove mismatch can never be blamed on a lost keystroke.
        if got_place != want_place:
            bad.append('board %s != %s' % (got_place, want_place))
        if st['halfmove'] != want_hm:
            bad.append('halfmove %d != %d' % (st['halfmove'], want_hm))
        if st['gameStateName'] != want_state:
            bad.append('state %s != %s' % (st['gameStateName'], want_state))
        if bad:
            failures.append((name, fen, moves, bad))
            print('FAIL  %s' % name)
            print('        %s  moves=%s' % (fen, moves))
            for b in bad:
                print('        %s' % b)
        elif a.verbose:
            print('ok    %s (halfmove %d, %s)' % (name, st['halfmove'], st['gameStateName']))

    if failures:
        # keep the tapes and snapshots of a failing run so they can be examined
        print('fifty-move: FAIL - %d/%d cases (artefacts kept in %s)'
              % (len(failures), len(CASES), tmpdir))
        return 1
    shutil.rmtree(tmpdir, ignore_errors=True)
    print('fifty-move: %d/%d OK (pawn/capture reset, everything else '
          'increments, draw at 100)' % (len(CASES), len(CASES)))
    return 0


if __name__ == '__main__':
    sys.exit(main())

```

## Submission Y — source changes

```diff
--- a/movegen.inc
+++ b/movegen.inc
@@ -903,6 +903,9 @@
         ld a,0xFF
         ld (epSquare),a
 mkHalf:
+        ; fifty-move clock (contract C9): reset to 0 on a PAWN move or a
+        ; capture, increment on everything else.  `and 7` strips the colour
+        ; bit, so WP covers black pawns too.
         ld a,(mkPiece)
         and 7
         cp WP

```

## Submission Y — tests added

```
(no new test files)
```
