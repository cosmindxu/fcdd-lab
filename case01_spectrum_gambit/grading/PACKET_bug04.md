# Blind review packet — bug04

Two independent submissions fixed the SAME reported defect in the same
Z80 codebase. You are not told who wrote them or by what process, and
the two are not necessarily comparable in style. Judge only what is here.

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
@@ -183,8 +183,8 @@
         add hl,de
         ld a,b
         and 8
-        ret z
-        ex de,hl
+        ret z                   ; white piece: already white-positive
+        ex de,hl                ; black piece: negate
         ld hl,0
         or a
         sbc hl,de

```

## Submission X — tests added

```
--- eval_sign_test.py (5513 bytes) ---
#!/usr/bin/env python3
"""eval_sign_test.py — the evaluation must agree in sign with who is ahead.

Regression test for bug04: `pieceValSigned` returned the material+PST term
*black*-positive while every other eval term (king PST, pawn structure, king
safety, mating drive) and the `Matl` readout were white-positive.  The whole
material+PST component therefore entered the search with the wrong sign, so the
engine preferred *losing* material: it declined free pieces, gave its own away,
and printed an `Eval` that contradicted the `Matl` next to it.

Neither the golden screenshot nor the built-in perft/`T` self-test can see this
— the self-test only checks that the incremental `pstScore` matches a rebuild
from scratch, and a flipped sign is flipped consistently in both.  So this test
drives real searches through the harness and asserts on the move chosen and on
the sign of the reported score.

The engine always plays Black in these runs, so:
  * `lastScore` is the engine's own score: positive = the engine is winning.
  * `material` is white-positive: negative = Black (the engine) is ahead.
Those two must always have OPPOSITE signs.

Usage:
    ./eval_sign_test.py                       # needs ../../harness
    ./eval_sign_test.py -v                    # list every check, not just failures
    HARNESS=/path/to/harness TAP=/path/to/chess.tap ./eval_sign_test.py
Exit status 0 on success, 1 on any failed check.  Run by `make test`.
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.environ.get('HARNESS', os.path.join(HERE, '..', '..', 'harness'))
PLAY = os.path.join(HARNESS, 'tools', 'play.py')
TAP = os.environ.get('TAP', os.path.join(HERE, 'chess.tap'))

# Positions from the bug report, plus the colour-mirror of the third one.
FREE_QUEEN = 'rnbqkbnr/pppp1ppp/4p3/3Q4/8/8/PPPP1PPP/RNB1KBNR b - - 0 1'
FREE_ROOK = '4k3/8/8/8/8/1n6/8/R3K3 b - - 0 1'
LOST = '4k3/8/8/8/8/8/8/QQ2K3 b - - 0 1'      # engine (Black) is a bare king
WON = 'qq2k3/8/8/8/8/8/8/4K3 b - - 0 1'       # mirror: the engine has the queens

VERBOSE = '-v' in sys.argv[1:] or '--verbose' in sys.argv[1:]
failures = []


def run(fen, depth):
    """One headless search from `fen` at `depth`; returns the decoded state."""
    cmd = [sys.executable, PLAY, '--tap', TAP, '--fen', fen,
           '--depth', str(depth), '--json']
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit('harness run failed (%d):\n%s' % (r.returncode, r.stderr))
    return json.loads(r.stdout)


def check(name, ok, detail):
    if not ok:
        failures.append(name)
    if VERBOSE or not ok:
        print('%-4s %-36s %s' % ('ok' if ok else 'FAIL', name, detail))


def check_sign_agreement(name, st):
    """lastScore (engine-relative) and material (white-relative) must disagree
    in sign — the engine plays Black, so it cannot be ahead and behind at once."""
    score, matl = st['lastScore'], st['material']
    ok = (score > 0) == (matl < 0)
    check(name, ok, 'Eval %+d vs Matl %+d' % (score, matl))


def main():
    # 1. A free queen must be taken — at every level, per the bug report.
    for depth in (1, 2, 3, 4, 5):
        st = run(FREE_QUEEN, depth)
        # Guard: '-' means no engine move was recorded inside the harness's
        # frame budget, which would make the checks below meaningless.
        check('engine moved at all (level %d)' % depth,
              st['lastMove'] != '-',
              'lastMove %s' % st['lastMove'])
        check('free queen taken (level %d)' % depth,
              st['lastMove'] == 'e6d5' and st['material'] == -1000,
              'played %s, Matl %+d, Eval %+d'
              % (st['lastMove'], st['material'], st['lastScore']))
        # A queen up, the engine's own score must be clearly positive.
        check('queen-up score positive (level %d)' % depth,
              st['lastScore'] > 500,
              'Eval %+d' % st['lastScore'])
        check_sign_agreement('queen-up signs agree (level %d)' % depth, st)

    # 2. A free rook must be taken.
    st = run(FREE_ROOK, 2)
    check('free rook taken',
          st['lastMove'] == 'b3a1' and st['material'] == -320,
          'played %s, Matl %+d' % (st['lastMove'], st['material']))

    # 3. Bare king against two queens: the engine must know it is lost.
    st = run(LOST, 2)
    check('hopeless position scores negative',
          st['lastScore'] < -1000 and st['material'] > 1000,
          'Eval %+d, Matl %+d' % (st['lastScore'], st['material']))
    check_sign_agreement('hopeless position signs agree', st)

    # 4. The colour mirror must flip the score, not repeat it.  This is what
    #    separates "the sign is inverted" from "the sign is right": a build
    #    with pieceValSigned flipped passes neither 3 nor 4, and a build that
    #    ignored material entirely would fail both.
    st = run(WON, 2)
    check('winning position scores positive',
          st['lastScore'] > 1000 and st['material'] < -1000,
          'Eval %+d, Matl %+d' % (st['lastScore'], st['material']))
    check_sign_agreement('winning position signs agree', st)

    if failures:
        print('chess: FAIL - eval sign/material regression (%d): %s'
              % (len(failures), ', '.join(failures)))
        return 1
    print('chess: eval sign + material greed OK '
          '(free queen at levels 1-5, free rook, lost/won score signs)')
    return 0


if __name__ == '__main__':
    sys.exit(main())

```

## Submission Y — source changes

```diff
--- a/engine.inc
+++ b/engine.inc
@@ -128,6 +128,14 @@
 
 ; pieceValSigned(B=piece, C=square) -> HL = signed white-relative value
 ; (material + piece-square), 0 for a king or empty square.
+;
+; WHITE-RELATIVE means: a white piece contributes a POSITIVE value and a
+; black piece a NEGATIVE one (contract clause S6a, spec/the specification
+; §16.10).  The colour test at the tail must therefore be `ret z` (bit 3
+; clear = white = return the magnitude as-is); `ret nz` there inverts the
+; whole material term of pstScore/eval and makes the engine play to LOSE
+; material.  Cf. `kingPstSigned` below and `materialBalance` in chess.asm,
+; which use the same convention.
 pieceValSigned:
         ld a,b
         or a
@@ -183,11 +191,11 @@
         add hl,de
         ld a,b
         and 8
-        ret z
+        ret z                    ; white: +magnitude (white-relative)
         ex de,hl
         ld hl,0
         or a
-        sbc hl,de
+        sbc hl,de                ; black: -magnitude
         ret
 pvsZero:
         ld hl,0

```

## Submission Y — tests added

```
(no new test files)
```
