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
-        ret nz
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
+; black piece a NEGATIVE one (specification clause S6a, spec/the specification
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
-        ret nz
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
--- changes to the accompanying verification package (77949 bytes of diff) ---
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/bridge/a check script SUBMISSION/the the check suite
--- BASELINE/bridge/a check script	2026-07-29 22:35:40.234282768 +0200
+++ SUBMISSION/the the check suite	2026-08-05 06:54:41.350143790 +0200
@@ -118,6 +118,117 @@
 chk("T20a_start_balanced", evalWhite(startPos), 0)
 chk("T20b_stm_relative", eval_(kiwiPos.replace(stm=BLACK)), -eval_(kiwiPos))
 
+# --- §16.10  clause S6: EVALUATION ORIENTATION ---------------------------
+# The kernel proves S6a over all 640 (piece, square) pairs and S6b/S6c
+# small-scope (4 squares / 1 square).  The reference implementation WIDENS S6b and S6c to every
+# empty square of the two-kings board, and re-checks every §16.10 theorem.
+
+chk("T26a_S6a_domain_640", len(S6aDomain()), 640)
+chk("T26b_S6a_oriented",
+    all(S6a_oriented(pieceValSigned, pc, s) for pc, s in S6aDomain()), True)
+chk("T26c_S6a_mutant_fails_everywhere",
+    any(S6a_oriented(pieceValSignedMut, pc, s) for pc, s in S6aDomain()), False)
+chk("T26d_king_is_zero", pieceValSigned(WK, 0x04), 0)
+chk("T26e_empty_is_zero", pieceValSigned(0, 0x33), 0)
+
+_kb = kingsOnlyPos.board
+_empty = [s for s in scanSquares if bGet(_kb, s) == 0]
+chk("S6_carrier_62_empty", len(_empty), 62)
+# ... and the carrier's kings really do cancel, so any sign that appears in
+# S6b/S6c comes from the added material and nothing else.
+chk("S6_carrier_is_zero", evalWhite(kingsOnlyPos), 0)
+
+chk("T27a_S6b_place_moves_pstScore(620)",
+    all(S6b_placeMoves(_kb, pc, s) for pc in nonKingPieces for s in _empty), True)
+chk("T27b_S6b_mutant_fails_everywhere(620)",
+    any(S6b_placeMoves(_kb, pc, s, pstScoreMut)
+        for pc in nonKingPieces for s in _empty), False)
+
+_fam = [kingsOnlyPos.replace(board=bSet(_kb, s, pc))
+        for pc in nonKingPieces for s in _empty]
+chk("S6c_family_620", len(_fam), 620)
+chk("T27d_S6c_sign_agrees(620)",
+    all(S6c_signAgrees(evalWhite, p) for p in _fam), True)
+chk("T27e_S6c_mutant_fails_everywhere(620)",
+    any(S6c_signAgrees(evalWhiteMut, p) for p in _fam), False)
+chk("T27f_S6c_has_white_up",
+    any(matBalance(p.board) > 0 for p in _fam), True)
+chk("T27g_S6c_has_black_up",
+    any(matBalance(p.board) < 0 for p in _fam), True)
+
+# S6d — the three reported incidents (the method Law 6).
+_cap1, _quiet1 = mkMove(0x54, 0x43, 0), mkMove(0x62, 0x52, 0)
+_cap2, _quiet2 = mkMove(0x21, 0x00, 0), mkMove(0x21, 0x40, 0)
+# the moves must really be legal, or the incident theorems are vacuous
+chk("S6d_cap1_legal", _cap1 in genLegal(bug04Pos1), True)
+chk("S6d_quiet1_legal", _quiet1 in genLegal(bug04Pos1), True)
+chk("S6d_cap2_legal", _cap2 in genLegal(bug04Pos2), True)
+chk("S6d_quiet2_legal", _quiet2 in genLegal(bug04Pos2), True)
+
+chk("T28a_incident1_capture_much_better",
+    evalWhite(makeMove(bug04Pos1, _cap1)) + 800
+    <= evalWhite(makeMove(bug04Pos1, _quiet1)), True)
+chk("T28b_incident1_mutant_prefers_quiet",
+    evalWhiteMut(makeMove(bug04Pos1, _quiet1))
+    < evalWhiteMut(makeMove(bug04Pos1, _cap1)), True)
+chk("T28c_incident2_capture_much_better",
+    evalWhite(makeMove(bug04Pos2, _cap2)) + 400
+    <= evalWhite(makeMove(bug04Pos2, _quiet2)), True)
+chk("T28d_incident2_mutant_prefers_quiet",
+    evalWhiteMut(makeMove(bug04Pos2, _quiet2))
+    < evalWhiteMut(makeMove(bug04Pos2, _cap2)), True)
+chk("T28e_incident3_matl_white_ahead", matBalance(bug04Pos3.board) > 0, True)
+chk("T28f_incident3_eval_agrees", evalWhite(bug04Pos3) > 0, True)
+chk("T28g_incident3_stm_is_losing", eval_(bug04Pos3) < 0, True)
+chk("T28h_incident3_decisive", evalWhite(bug04Pos3) >= 1000, True)
+chk("T28i_incident3_mutant_inverts",
+    matBalance(bug04Pos3.board) > 0 and evalWhiteMut(bug04Pos3) < 0, True)
+
+# S6 is INDEPENDENT of S3 — the fault preserves antisymmetry, which is
+# exactly why T19a..T19e could not see it.
+chk("T29_mutant_still_antisymmetric",
+    evalWhiteMut(mirrorPos(kiwiPos)), -evalWhiteMut(kiwiPos))
+chk("T29a_mutant_still_start_balanced", evalWhiteMut(startPos), 0)
+
+# --- §16.11  clause S6e: the KING piece-square term's orientation --------
+# The kernel proves S6e over 8 king pairs; the reference implementation runs ALL 3,612
+# non-adjacent pairs.  Ground truth is pstKingEG read directly, never
+# kingPstSigned (that would be circular under the mutation being caught).
+
+_kp = S6eDomain()
+_kpnz = [(w, b) for w, b in _kp if kingTblAdvantage(w, b) != 0]
+chk("S6e_domain_3612", len(_kp), 3612)
+chk("S6e_non_degenerate_3004", len(_kpnz), 3004)
+chk("T30a_S6e_king_oriented(3612)",
+    all(S6e_kingOriented(evalWhite, w, b) for w, b in _kp), True)
+chk("T30b_S6e_family_non_degenerate",
+    all(kingTblAdvantage(w, b) != 0 for w, b in
+        [(0x33, 0x70), (0x34, 0x77), (0x44, 0x07), (0x43, 0x00),
+         (0x00, 0x44), (0x07, 0x43), (0x70, 0x34), (0x77, 0x33)]), True)
+chk("T30c_S6e_kmutant_fails_everywhere(3004)",
+    any(S6e_kingOriented(evalWhiteKMut, w, b) for w, b in _kpnz), False)
+
+# ... and the sibling fault really is invisible to everything else — stated
+# on a carrier whose kings are NOT a mirror pair.  On a mirror pair the two
+# kingPstSigned terms cancel and `evalWhiteKMut` is pointwise EQUAL to
+# `evalWhite`, so the claim would collapse to `f = f` (review round 2, N3).
+_kmc = kmutCarrier
+chk("T30d_kmutant_really_bites", evalWhiteKMut(_kmc) != evalWhite(_kmc), True)
+chk("T30e_carrier_is_material_dominated", matBalance(_kmc.board) > 0, True)
+chk("T30f_kmutant_passes_S6c_where_it_bites",
+    S6c_signAgrees(evalWhiteKMut, _kmc), True)
+_kg = kingGeomPos(0x33, 0x70)
+chk("T30g_kmutant_still_antisymmetric",
+    evalWhiteKMut(mirrorPos(_kg)), -evalWhiteKMut(_kg))
+chk("T30h_kmutant_bites_there_too", evalWhiteKMut(_kg) != evalWhite(_kg), True)
+chk("T30i_kmutant_leaves_pstScore_alone",
+    all(S6a_oriented(pieceValSigned, pc, s) for pc, s in S6aDomain()), True)
+# The degeneracy itself, recorded so it cannot be re-introduced silently:
+# on the S6c family every member has mirror-pair kings, so the k-mutant IS
+# the identity there and a claim stated on that family proves nothing.
+chk("S6e_mirror_pair_family_is_degenerate_for_kmut",
+    [p for p in _fam if evalWhiteKMut(p) != evalWhite(p)], [])
+
 # --- §16.7  ply bound ----------------------------------------------------
 chk("T22_movebuf_in_range",
     all(0x6000 + ply * 512 + 511 <= 0x7FFF for ply in range(MAXPLY + 1)), True)
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/bridge/a check script SUBMISSION/the the check suite
--- BASELINE/bridge/a check script	2026-07-29 22:59:13.374886388 +0200
+++ SUBMISSION/the the check suite	2026-08-05 04:37:43.898405883 +0200
@@ -190,7 +190,9 @@
 #       loop's updateTerminal does.  A forced repetition therefore scores as
 #       whatever the static eval says, not as 0.
 # =====================================================================
-src = open("/media/sf_Projects/HC91_emulator/chess/engine.inc").read()
+# Relative to the shell's own VARIANT_DIR, not an absolute path: a copy of
+# this workspace must assert against ITS OWN source, not this one's.
+src = open(os.path.join(emu.VARIANT_DIR, "engine.inc")).read()
 ok("countReps" not in src, "F11: engine.inc now mentions countReps")
 ok("halfmove" not in src, "F11: engine.inc now mentions halfmove")
 EVID.append("F11 engine.inc (negamax + quiesce) contains no reference to "
Only in SUBMISSION/specification/bridge: a check script
diff -ru -x '*.olean' -x __pycache__ -x '*.png' -x '*.sna' -x '*.tap' BASELINE/bridge/emu.py SUBMISSION/the the check suite
--- BASELINE/bridge/emu.py	2026-07-29 22:44:14.362471728 +0200
+++ SUBMISSION/the the check suite	2026-08-05 06:55:13.603860454 +0200
@@ -20,10 +20,19 @@
 import subprocess
 import tempfile
 
-EMU = "/media/sf_Projects/HC91_emulator/build/hc91emu"
-ROM = "/media/sf_Projects/HC91_emulator/roms/48.rom"
-TAP = os.path.join(os.path.dirname(os.path.abspath(__file__)),
-                   "..", "artifacts", "chess.tap")
+HERE = os.path.dirname(os.path.abspath(__file__))
+WS = os.path.normpath(os.path.join(HERE, "..", ".."))       # workspace root
+
+EMU = os.path.join(WS, "harness", "build", "hc91emu")
+ROM = os.path.join(WS, "harness", "roms", "48.rom")
+# THE BUILD UNDER TEST.  Law 4 (verify claims where they RUN): the bridge
+# judges the tape the variant's `make` produces, not a snapshot of it that
+# can silently go stale.  `HC91_TAP` overrides it, which is how a reviewer
+# points the whole suite at a seeded-fault tape; nothing in the shipped
+# gate sets it.
+TAP = os.environ.get("HC91_TAP",
+                     os.path.join(WS, "variants", "bug04", "chess.tap"))
+VARIANT_DIR = os.path.join(WS, "variants", "bug04")
 
 # --- provenance: chess.asm equates -------------------------------------
 A_BOARD      = 0xE000   # board    equ 0xE000   (128 bytes, 0x88 indexed)
@@ -44,7 +53,17 @@
 A_HASHKEY    = 0xE10C   # hashKey (2 bytes, 16-bit Zobrist)
 A_HAVELAST   = 0xE124   # haveLast (1 once the engine has moved)
 A_LASTFROM   = 0xE122   # lastFrom / lastTo
-A_AIDEPTH    = 0xE08A   # aiDepth
+A_AIDEPTH    = 0xE08A   # aiDepth    — WHITE's search depth
+A_BLACKDEPTH = 0xE15E   # blackDepth — BLACK's, i.e. the ENGINE's
+A_LASTSCORE  = 0xE120   # lastScore (2 bytes, signed) — the panel's `Eval`,
+                        #   from the ENGINE's point of view
+A_PSTSCORE   = 0xE13D   # pstScore  (2 bytes, signed) — "incremental
+                        #   material+PST, non-king, white-rel"; seeded by
+                        #   computePstScore from finalizePosition
+A_GAMEPHASE  = 0xE107   # gamePhase (1 byte), seeded by computePhase
+A_MATBALTMP  = 0xE134   # matBalTmp (2 bytes, signed) — where the ENGINE's
+                        #   OWN materialBalance (chess.asm:988) leaves the
+                        #   `Matl` figure on every panel redraw (chess.asm:956)
 
 
 class Snapshot:
@@ -66,24 +85,119 @@
         off = 27 + (a - 0x4000)
         return list(self.raw[off:off + n])
 
+    def sword(self, a):
+        """A SIGNED 16-bit word — the engine's scores are two's complement."""
+        v = self.word(a)
+        return v - 0x10000 if v >= 0x8000 else v
+
+
+# One scratch directory per PROCESS, removed at exit.  Previously every
+# run leaked a `mkdtemp` and a `mktemp` .sna into a RAM-backed /tmp — one
+# b8 run leaked ~8 MB.
+_SCRATCH = None
+_scratch_n = 0
+
+
+def scratch(suffix=""):
+    global _SCRATCH, _scratch_n
+    if _SCRATCH is None:
+        import atexit
+        import shutil
+        _SCRATCH = tempfile.mkdtemp(prefix="hc91bridge.")
+        atexit.register(shutil.rmtree, _SCRATCH, True)
+    _scratch_n += 1
+    return os.path.join(_SCRATCH, "t%05d%s" % (_scratch_n, suffix))
+
 
-def run(frames, types=(), sna=None, extra=()):
+def run(frames, types=(), sna=None, extra=(), tap=None):
     """Boot chess.tap, apply scheduled key events, snapshot.
 
     Returns (screen_text, Snapshot|None).  Raises on emulator failure —
     a broken harness must be LOUD."""
-    tmp = sna or tempfile.mktemp(suffix=".sna")
+    tmp = sna or scratch(".sna")
     cmd = [EMU, "--machine", "48k", "--rom", ROM, "--autoload",
            "--frames", str(frames), "--text", "--save-sna", tmp]
     for s, f in types:
         cmd += ["--type", "%s@%d" % (s, f)]
-    cmd += list(extra) + [os.path.abspath(TAP)]
+    cmd += list(extra) + [os.path.abspath(tap or TAP)]
     r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
     if r.returncode != 0:
         raise RuntimeError("hc91emu exit %d: %s" % (r.returncode, r.stderr[:400]))
     return r.stdout, Snapshot(tmp)
 
 
+# --- loading an ARBITRARY position into the running engine ---------------
+# The game's own save/load block (`G`/`L`) is a plain ROM data block, so a
+# position is injected by appending one hand-built block to the tape and
+# pressing L — no patch to the engine and none to the emulator.  The builder
+# is the harness's `chesspos.py`; the reference implementation builds the SAME position from the
+# SAME FEN string through `positions.from_fen`, independently, so a
+# transcription slip on either side shows up as a DISAGREEMENT.
+
+_chesspos = None
+
+
+def _cp():
+    global _chesspos
+    if _chesspos is None:
+        import sys
+        sys.path.insert(0, os.path.join(WS, "harness", "tools"))
+        import chesspos
+        _chesspos = chesspos
+    return _chesspos
+
+
+def run_fen(fen, depth=2, move=False, frames=None, tap=None):
+    """Load `fen` into the engine and snapshot.
+
+    move=False presses `V` (two-player) BEFORE `L`, so the engine never
+    moves and the snapshot holds the position exactly as loaded — that is
+    what makes the static-eval observables (pstScore, gamePhase, matBalTmp)
+    readable.  move=True lets the engine reply, which needs `fen` to have
+    Black to move (the engine plays Black).
+
+    The depth digit must precede `L`: a tape load only restores White's
+    level (harness/HOWTO.md §Caveats).
+    """
+    tapfile = os.path.abspath(tap or TAP)
+    blk = _cp().tap_data_block(_cp().fen_to_block(fen, depth))
+    path = scratch(".tap")
+    with open(path, "wb") as f:
+        f.write(open(tapfile, "rb").read() + blk)
+    keys = ("%d" % depth) + ("" if move else "v") + "l"
+    return run(frames or (1400 if not move else 2400),
+               types=[(keys, 700)], tap=path)
+
+
+def read_eval_state(sn):
+    """The engine's OWN evaluation observables, with provenance.
+
+    Falsifiability tier: MONITORED.  `pstScore` is computed by the Z80 from
+    its own tables and `matBalTmp` by a SEPARATE Z80 routine
+    (`materialBalance`); the reference implementation derives both from the FEN independently.
+    A disagreement is a real finding, not a format regression.
+    """
+    return {
+        "board": sn.block(A_BOARD, 128),
+        "stm": sn.byte(A_STM),
+        "wking": sn.byte(A_WKING),
+        "
```
