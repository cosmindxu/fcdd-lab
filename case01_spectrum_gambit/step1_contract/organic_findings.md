# Organic findings — HC-91 chess engine

Real defects and FIDE divergences found in the **pristine** engine
(`/media/sf_Projects/HC91_emulator/chess/`, 7,343 lines) while building the
formal contract.  These are the *organic bonus lane* of case01: none of them
is a seeded fault, and none was hinted at by anything outside the source.

Nothing here is "silently normalised": the Lean contract and the Python twin
specify **the engine's actual rule**, and each divergence is flagged with an
inline `DIVERGENCE Fn` marker at the corresponding clause.

Severity uses the FCDD map: **HIGH ≈ reachable in normal play**,
**MED ≈ pure-contract-only or fragility**, **LOW ≈ hygiene / documentation**.
Every finding carries the evidence that establishes it; the executable ones
are pinned as regression probes in `bridge/b7_findings.py`, which goes RED if
the engine is fixed without updating it.

---

## F5 — the repetition history overwrites the ZX ROM system variables (HIGH)

`gameKeys equ 0x5B00` (chess.asm:212) holds up to **250** 16-bit position keys
(`recordGameKey`, movegen.inc:1289), i.e. `0x5B00 .. 0x5CF3`.  The ZX Spectrum
48K **system variable area is `0x5C00 .. 0x5CB5`**, and the engine deliberately
keeps the ROM interrupt handler alive (`im 1` + `ei`, chess.asm:243-247) so it
can read the 50 Hz frame counter for its chess clock.

* from **ply 128** (`(0x5C00-0x5B00)/2`) every recorded key lands on a live
  system variable, and the ROM's per-frame keyboard scan writes back over it;
* at **ply 188** the key is written *directly onto* `FRAMES` (`0x5C78`), the
  very counter `clkStartTurn`/`clkCommit` use — so recording that position's
  key **corrupts the game clock**, and the next interrupt corrupts the key.

Consequences in a normal long game (188 plies = move 94, entirely ordinary):
threefold-repetition detection silently degrades from ply 128, and both
players' clocks jump at ply 188.

**Evidence — CONFIRMED.**  Arithmetic proved by z3 as a *reachability*
(`smt/s2_addresses.py` A5: z3 finds ply 128 as the first offender and ply 188
for `FRAMES`, it is not told them).  The region is shown to be live by
execution: two snapshots have `FRAMES` 1317 → 2517, and holding a key rewrites
`0x5C04/05/07/08` (`bridge/b7_findings.py` F5).

**Fix sketch:** `gameKeys` needs 500 bytes somewhere the ROM does not own —
e.g. below `moveLog` at `0xE400`, or cap the history at 128 plies and say so.

---

## F10 — the Zobrist key is 16 bits: collisions are routine (HIGH)

`hashKey` is two bytes (chess.asm:124) and the transposition table stores that
same 16-bit value as its verification key (tt.inc:284-308), so a TT "hit"
means nothing more than a 16-bit agreement.  The same key is the sole identity
used for threefold repetition (`countReps`, movegen.inc:1383).

Reading the engine's **own** PRNG-seeded Zobrist tables out of RAM
(`zobPiece` 0xD540) and hashing the 8,652 distinct positions of the 3-ply tree
from the start position yields **1,576 colliding keys — 18.2 %**.  A single
search at level 5 visits far more nodes than that.

Consequences: (a) the TT can return a score computed for a *different*
position (a wrong move, or a wrong mate claim); (b) `countReps` can reach 3 on
three *different* positions and declare a draw that never happened.

**Evidence — CONFIRMED by execution** (`bridge/b7_findings.py` F10), using the
engine's real tables, and cross-validated by the twin reproducing the engine's
`hashKey` for the start position exactly.

**Fix sketch:** 32-bit keys, or keep 16-bit indexing but store a wider
verification word in the TT entry and compare full position identity in
`countReps`.

---

## F4 — the aspiration window is dead code; every deepening iteration searches twice (MED)

`aiMove` (engine.inc:2118-2177) sets the root window to
`[lastScore-40, lastScore+40]` for every iterative-deepening iteration ≥ 2, and
then decides whether to re-search by reading `alphaArr[0]` back **after** the
search:

```asm
        call negamax          ; HL = score  (and negamax MUTATED alphaArr[0])
        ld (lastScore),hl
        ...
        call ptrAlpha         ; BC = alphaArr[0]   <-- the mutated alpha
        ld de,(lastScore)
        call cmpDEgtBC        ; score > alpha ?
        jr nc,aspWiden        ; no -> full-window re-search
```

The root raises `alphaArr[0]` to the best score whenever it improves
(`nmTryA`, engine.inc:1356-1360), so at exit `alpha ≥ score` and `score > alpha`
is **never** true.  The two early-exit paths (reverse futility, null move)
return a value `≥ beta`, which fails the *second* half of the window test
instead.  Either way the full-window re-search always runs.

**Evidence — SOLVER-PROVED over an extracted control-flow model**
(`smt/s3_aspiration.py`): z3 shows UNSAT of "the narrow window is kept" on all
three reachable root exits, and SAT for a hypothetical engine that read the
*original* alpha (the per-ply `origAlphaArr` the TT code already maintains), so
the result is not vacuous.  The extraction is the assumption; the exact
instructions it was taken from are quoted above.

**Note — two bugs cancelling.** This defect currently *masks* a latent one: a
root reverse-futility (engine.inc:1078) or null-move (engine.inc:1153) cutoff
returns **without ever setting `bestFrom`**, and those can only fire once the
window is narrow, i.e. on iterations ≥ 2.  Because the re-search with
`[-INF, INF]` always follows, `bestFrom` is always repaired.  *Fixing the
aspiration window without also guarding the root against those two cutoffs
would expose an engine that plays no move.*  (The engine's author already met
this class of bug once — engine.inc:1026-1031 suppresses TT cutoffs at the
root for exactly this reason, with a comment saying so.)

---

## F6 — a pawn on the back rank indexes outside the board array (MED)

`gmPawn` computes the one-ahead square as `genFrom + 16` with **no 0x88 test**
(movegen.inc:337-343); `gmPawnBlack` likewise uses `genFrom - 16`
(movegen.inc:424-429).  `board equ 0xE000` is 128 bytes, and `sideToMove` sits
immediately after it at `0xE080`.

* a **white pawn on rank 8** reads `board[0x80]` = `sideToMove`; if that byte
  is 0 the engine generates a "push" to square `0x80`, and `makeMove` then
  **writes the pawn into `sideToMove`**;
* worse, `unmakeMove` restores `board[0x80] = 0` and *then* does
  `ld a,(sideToMove) / xor 8`, so the side to move comes back **flipped**;
* a **black pawn on rank 1** reads/writes `0xE0F0..0xE0F7`
  (`pvTo`, `twoPlayer`, `aidIter`, `wpFile`).

Normal play cannot produce such a pawn (promotion always replaces it), and the
setup editor zeroes castling but *can* place one, so this is reachable through
the editor and through a hand-made tape load.

**Evidence — CONFIRMED by source reading**, not by execution: demonstrating it
end-to-end needs ~25 scripted editor keystrokes, which was cut for effort.
Recorded honestly at that claim level.  The contract makes the exclusion
explicit: `spec/Contract.lean` §8 marks precondition `P_PAWN_RANK`, and
`bridge/b3_spec_twin_brute.py` refuses to generate such positions *and says
why* — spec and twin would agree with each other and both differ from the
engine, so testing there would prove nothing.

---

## F11 — the search cannot see a draw (MED)

`negamax` and `quiesce` (engine.inc) contain **no reference to `countReps` or
`halfmove`**; only the game loop's `updateTerminal` knows about repetition and
the fifty-move rule.  A forced repetition therefore scores as whatever the
static evaluation says, so the engine will happily walk into a drawn
repetition believing it is winning — and, in a won position, will not avoid
one.

**Evidence — CONFIRMED by absence in the source**, asserted mechanically in
`bridge/b7_findings.py` F11 so that adding either call turns the probe red.

---

## F2 — the e.p. target is set after every double push (LOW, FIDE divergence)

`makeMove` sets `epSquare` on **every** double push (movegen.inc:890-904) and
`computeKey` hashes it (zobrist.inc:132-133), whereas the modern FEN/FIDE
convention records the target only when a capture is actually available.

Consequence: two positions FIDE calls identical hash differently, so a genuine
threefold repetition can be **missed**.  (Note the direction: this one loses
draws, F10 invents them.)

**Evidence — CONFIRMED** (`bridge/b7_findings.py` F2): the same board with and
without an unusable e.p. target hashes to `D259` vs `5144`, with no e.p.
capture available in either.

The contract specifies the engine's rule; the divergence is flagged, not
normalised.

---

## F1 — castling trusts the rights bits and never looks for a rook (MED, pure-contract-only)

`genCastling` (movegen.inc:105-239) checks the rights bit, the empty path and
the attacked squares, but never that a rook is on the corner.  `makeMove` then
*writes* a rook onto f1/d1 (or f8/d8) and *zeroes* the corner square.

Given rights without a rook — reachable only through a corrupted or
hand-crafted tape load, since `setupEditor` zeroes castling (chess.asm:1470)
and `clrCastleSq` keeps rights honest in play — the engine **conjures a rook
and deletes whatever stood on h1**.

**Evidence — CONFIRMED in the model** (`bridge/b7_findings.py` F1): a black
knight on h1 with `castling = 1` yields O-O, a white rook on f1 and an empty
h1.  Classified pure-contract-only because the live input paths cannot reach
it.

---

## F3 — K+B vs K+B with same-coloured bishops is not called a draw (LOW, FIDE divergence)

`isInsufficient` (movegen.inc:1243) requires no pawn/rook/queen **and fewer
than two minors counted across both sides**.  FIDE 5.2.2 also calls
K+B vs K+B with both bishops on the same colour a dead position; the engine
plays on.  The divergence is *conservative* (it never claims a draw that FIDE
would refuse), so it is a LOW-severity rule gap, not a safety issue.

**Evidence — CONFIRMED in the model** (`bridge/b7_findings.py` F3).

---

## F7 — the fifty-move clock is a byte with no saturation (LOW)

`halfmove` is one byte and `makeMove` does a plain `inc a` (movegen.inc:913).
It would wrap 255 → 0.  Unreachable in normal play because `updateTerminal`
ends the game at 100, but `finalizePosition` (perft.inc:424) resets it to 0
when a position is set up, and the search never inspects it (see F11) — so the
byte only survives because two other things happen to bound it.

**Evidence — source reading.**  Hygiene: the invariant "halfmove ≤ 100" is
maintained by a *different* function than the one that increments it.

---

## F8 — `validateHumanMove`'s comment contradicts its code (LOW, documentation)

chess.asm:1721 says "Auto-queens promotions", but `maybeForceQueen`
(chess.asm:1760) calls `promptPromo`, which **blocks until the human presses
Q/R/B/N**.  The behaviour is the better one; the comment is stale.

---

## F9 — the engine declares draws instead of offering a claim (LOW, FIDE divergence)

`updateTerminal` ends the game automatically on threefold repetition and on
the fifty-move clock (movegen.inc:1203-1229).  FIDE makes both a *claim* by a
player (only 75 moves / fivefold are automatic).  Deliberate simplification for
an 8-bit UI; recorded so the contract's `updateTerminal` is not mistaken for
the FIDE rule.

---

## Not findings (attacked, no defect found)

Recorded so the clean areas are visible, per the FCDD reviewer contract:

* **make/unmake** round-trips exactly on every legal move of every witness
  position, on all five special-move classes, and across 410,082 engine perft
  nodes — including the incremental Zobrist key, game phase and PST score,
  which the engine self-checks inside perft (`checkKey`, perft.inc:87).
* **Castling legality** (rights, empty path, king not in / through / into
  check) matches the twin on every generated and played position; the
  through-check guard is exercised in both directions.
* **En passant** target, capture square, and the removal of the *correct*
  pawn agree with the twin, in the kernel, in 300 generated positions, in a
  scripted real game, and over the engine's 43,238-node e.p. perft.
* **Evaluation antisymmetry** holds exactly under the colour mirror on every
  witness — the two sides are scored by the same code path with the mirrored
  index, and no term leaks a colour.
* **Ply bounds**: the per-ply move buffers and undo records fit their pages
  for ply ≤ 15 and would *not* fit at ply 16 — the `MAXPLY` cap in `quiesce`
  is load-bearing and correct, and the eight per-ply arrays on page 0xD4 are
  pairwise disjoint (28 z3 proofs).
* **16-bit evaluation arithmetic** cannot overflow: worst case |eval| ≤ 11,465
  against a 32,767 limit, with the aspiration, reverse-futility and
  window-negation arithmetic all inside range.
