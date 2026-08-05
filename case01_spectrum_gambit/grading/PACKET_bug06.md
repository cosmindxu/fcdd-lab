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
@@ -231,6 +231,7 @@
         ld a,(ttStage+7)
         ld (ttTo),a
         ; usable for a cutoff only if entry depth >= current depth
+        ; (CF=1 <=> entDepth < curDepth -> the entry is too shallow to trust)
         ld a,(ttEntDepth)
         ld hl,ttCurDepth
         cp (hl)
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

## Submission X — tests added

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

## Submission Y — source changes

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
-        jr c,ttNoCut
+        cp (hl)                  ; CF=1 <=> entDepth < curDepth
+        jr c,ttNoCut             ; shallower entry -> not usable, search on
         ld a,(ttEntFlag)
         or a
         jr z,ttExact

```

## Submission Y — tests added

```
(no new test files)
```
