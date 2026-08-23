# Blind review packet — bug05_r1

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

# bug05 — a rook reappears on a1 out of nowhere once the rook that started there has moved away

**Build under test:** `arms/variants/bug05` — build with `make` (see its
`BUILD.md`). Emulator, drivers and the commands used below: `arms/harness`
(see `HOWTO.md`), 48K machine, `roms/48.rom`.

## Observed

**A white rook materialises on a1.** Start from White Ra1 + Ke1 with queenside
castling still available and the black king on e8:

```
4k3/8/8/8/8/8/8/R3K3 w Q - 0 1
```

Move the rook `Ra1-a2` — fine, the board is correct and `Matl` still reads `5`.
Now let Black play any move at all (`Ke8-e7`). As soon as that move is made the
board becomes

```
8/4k3/8/8/8/8/R7/R3K3 w - - 2 2

  2 R . . . . . . .      the rook that moved, on a2
  1 R . . . K . . . ... and a SECOND rook, back on a1
```

`Matl` jumps from `5` to `10`. Nobody castled, nobody promoted, and no white
move was made between the two screens — the extra rook simply appears while the
opponent moves. It is a real piece: it can be moved and captured afterwards.

**Castling long is also still offered.** Continuing from that position, e1 → c1
is accepted even though the original a1 rook is standing on a2: the king lands
on c1, a rook lands on d1, and White ends up with two rooks
(`8/4k3/8/8/8/8/R7/2KR4`, `Matl 10`).

**And the kingside right is lost instead.** From
`4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1`, play `Ra1-a2`, `Ke8-e7`, then try `e1-g1`:
the move is rejected as `Illegal move` although the h1 rook has never moved.

The h1/a8/h8 corners behave correctly; everything above is specific to a1.

## Repro

```sh
cd arms/harness
make build/hc91emu                       # once

# 1. the phantom rook — two moves is enough
tools/play.py --tap ../variants/bug05/chess.tap \
    --fen '4k3/8/8/8/8/8/8/R3K3 w Q - 0 1' --moves 'a1a2,e8e7' --two-player
```

```
fen            8/4k3/8/8/8/8/R7/R3K3 w - - 2 2    <-- rooks on a1 AND a2
material       1000                               <-- must still be 500
```

```sh
# ... and after only the first move it is still correct, so the extra rook
#     arrives with Black's reply
tools/play.py --tap ../variants/bug05/chess.tap \
    --fen '4k3/8/8/8/8/8/8/R3K3 w Q - 0 1' --moves a1a2 --two-player
#   fen 4k3/8/8/8/8/8/R7/4K3 b - - 1 1     material 500        (correct)

# 2. castling long accepted with the rook long gone
tools/play.py --tap ../variants/bug05/chess.tap \
    --fen '4k3/8/8/8/8/8/8/R3K3 w Q - 0 1' --moves 'a1a2,e8e7,e1c1' --two-player
#   fen 8/4k3/8/8/8/8/R7/2KR4 b - - 3 2    material 1000    moveLog a1a2 e8e7 e1c1

# 3. the kingside right is revoked by a1 traffic
tools/play.py --tap ../variants/bug05/chess.tap \
    --fen '4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1' --moves 'a1a2,e8e7,e1g1' --two-player
#   moveLog a1a2 e8e7                      (e1g1 was refused; it must be legal)

# controls, all correct on this build:
tools/play.py --tap ../variants/bug05/chess.tap \
    --fen '4k3/8/8/8/8/8/8/R3K3 w Q - 0 1' --moves e1c1 --two-player
#   O-O-O with the rook still home: legal, material 500
tools/play.py --tap ../variants/bug05/chess.tap \
    --fen '4k3/8/8/8/8/8/8/4K2R w K - 0 1' --moves 'h1h2,e8e7,e1g1' --two-player
#   h1 rook leaves -> O-O correctly refused
```

`--two-player` presses `V` so both sides are driven by `--moves` and the engine
never interferes; the FEN's castling field is honoured because the game's own
tape-load restores it. Without the helper script:

```sh
cd arms/harness
tools/chesspos.py tap ../variants/bug05/chess.tap /tmp/bug05.tap \
    --fen '4k3/8/8/8/8/8/8/R3K3 w Q - 0 1'
./build/hc91emu --machine 48k --rom roms/48.rom /tmp/bug05.tap --autoload \
    --turbo --type "vl@700" \
    --type "$(tools/chesspos.py keys --cursor e2 a1a2)@820" \
    --type "$(tools/chesspos.py keys --cursor a2 e8e7)@1220" \
    --frames 2400 --text --save-sna /tmp/bug05.sna
tools/chesspos.py board /tmp/bug05.sna
```

(one `--type` per move, a few hundred frames apart: the game repaints the whole
screen between moves and keystrokes that arrive during the repaint are dropped.
`--cursor` is where the cursor was left by the previous move.)

```
```

## Expected

- No piece may ever appear on the board that was not put there by a move. After
  `Ra1-a2` and Black's reply the position must be
  `8/4k3/8/8/8/8/R7/4K3 w - - 2 2`, with `Matl 5`.
- Moving (or losing) the a1 rook must revoke White's **queenside** castling
  right and nothing else, so `e1-c1` in repro 2 must be refused as illegal and
  the move log must stop at `a1a2 e8e7`.
- Moving the a1 rook must **not** touch the kingside right: `e1-g1` in repro 3
  must be accepted, ending as `5RK1` on the first rank.
- Castling must never change the material on the board.
- The other three corners must keep behaving as they already do.

## Also observed

- The built-in self-test (`T`) does **not** pass on this build:

  ```
  perft 1  20         OK
  perft 2  400        OK
  perft 3  8902       OK
  perft 4  197281     OK
  kiwipete d3  97739    BAD
  enpassant d4 43238    OK
  promotion d3 62379    OK
  incr key/phase/pst    OK
  PERFT BAD - movegen error
  ```

  (the canonical count for Kiwipete at depth 3 is 97862; that position starts
  with both sides holding all four castling rights.)
- The initial board renders pixel-identical to `initial_golden.png`.
- A king move still revokes both of its own rights.
- En passant, promotion, check/mate/stalemate detection, the draw rules and the
  engine's search all behave normally in spot checks.


## Submission X — source changes

```diff
--- a/movegen.inc
+++ b/movegen.inc
@@ -939,26 +939,28 @@
         call keyUpdate
         ret
 
+; clrCastleSq(A=square, B=rights) — a move from or to a corner square kills
+; the right that corner owns.  Bits: 0=WK(h1) 1=WQ(a1) 2=BK(h8) 3=BQ(a8).
 clrCastleSq:
-        cp 0x00
+        cp 0x00 ; a1 -> white queenside (bit1)
         jr nz,cc1
         ld a,b
-        and 0xFE
+        and 0xFD
         ld b,a
         ret
-cc1:    cp 0x07
+cc1:    cp 0x07 ; h1 -> white kingside (bit0)
         jr nz,cc2
         ld a,b
         and 0xFE
         ld b,a
         ret
-cc2:    cp 0x70
+cc2:    cp 0x70 ; a8 -> black queenside (bit3)
         jr nz,cc3
         ld a,b
         and 0xF7
         ld b,a
         ret
-cc3:    cp 0x77
+cc3:    cp 0x77 ; h8 -> black kingside (bit2)
         ret nz
         ld a,b
         and 0xFB

```

## Submission Y — source changes

```diff
--- a/movegen.inc
+++ b/movegen.inc
@@ -939,26 +939,28 @@
         call keyUpdate
         ret
 
+; --- a rook leaving or being captured on a corner kills THAT corner's right.
+; rights bits: 0 WK (h1), 1 WQ (a1), 2 BK (h8), 3 BQ (a8) - see chess.asm.
 clrCastleSq:
-        cp 0x00
+        cp 0x00 ; a1 -> clear WQ (bit1)
         jr nz,cc1
         ld a,b
-        and 0xFE
+        and 0xFD
         ld b,a
         ret
-cc1:    cp 0x07
+cc1:    cp 0x07 ; h1 -> clear WK (bit0)
         jr nz,cc2
         ld a,b
         and 0xFE
         ld b,a
         ret
-cc2:    cp 0x70
+cc2:    cp 0x70 ; a8 -> clear BQ (bit3)
         jr nz,cc3
         ld a,b
         and 0xF7
         ld b,a
         ret
-cc3:    cp 0x77
+cc3:    cp 0x77 ; h8 -> clear BK (bit2)
         ret nz
         ld a,b
         and 0xFB

```
