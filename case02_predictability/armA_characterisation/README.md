# Characterisation-test suite — HC-91 ZX-CHESS engine

**57 cases, ~1,520 recorded observations, ~65 seconds, one exit code.**

```sh
./characterise.py --tap /path/to/your/chess.tap
```

Exit 0 = every recorded observation still matches. Exit 1 = at least one
differs, and the difference is printed. Exit 2 = the harness could not run.

---

## 1. What this is, and what green means

Every expected value in `expected.json` was **recorded by running the pristine
build**. Nothing in this suite encodes an opinion about what chess rules
require, what the engine ought to do, or where its bugs are. It is a
photograph, not a judgement.

So a green run means exactly this:

> At the 57 scripted observation points below, this build behaves
> byte-for-byte as the pristine build behaved.

It does **not** mean the build is correct. The pristine engine has known
defects, and this suite pins them in place along with everything else. If you
deliberately fix one, some cases will go red; that is the suite doing its job,
and the right response is to look at the diff and decide, not to re-record.

Read §4 before you trust a green run. It is the honest half of this document.

---

## 2. How it observes

The engine is a ZX Spectrum tape running inside `hc91emu`. From outside it has
exactly four channels, and every assertion here is built from them:

| # | Channel | How |
|---|---|---|
| 1 | keystrokes in | `--type` / `--keys` |
| 2 | the 24×32 screen out | `--text` OCR — **piece glyphs render as `?`**, the right-hand text panel and the status line are readable |
| 3 | a 48K memory image out | `--save-sna`, decoded with the harness's `tools/chesspos.py` |
| 4 | whatever the game itself SAVEs to tape | `--save-tape`, which captures the game's own 71-byte position block |

From those, each case records some of:

* **Position state** — `fen`, `side`, `castling`, `ep`, `halfmove`,
  `moveCount`, `wking`, `bking`, `gamePhase`, and `board128`: the raw hex of
  the whole 128-byte `0x88` board region at `0xE000`, **including the 64
  off-board bytes**, so that a write that lands beside the board is visible.
* **The engine's own legal-move list** — `genCount` plus `moveList`: the 4-byte
  records the engine leaves in its ply-0 buffer at `0x6000`, **in generation
  order, with each move's flag byte** (observed on pristine: `0` normal,
  `1` double push, `2` O-O, `3` O-O-O, and the values the engine uses for e.p.
  and for each promotion piece). This is the sharpest instrument here: a
  movegen change that adds, drops, reorders or re-flags a single move shows up
  as a text diff.
* **Terminal classification** — `gameState` / `gameStateName`, and the status
  message the game prints.
* **Search output** — `lastMove`, `lastScore`, and the panel's `Eval`.
* **The engine's material readout** — `panel.Matl`, which the engine computes
  from its own piece-value table.
* **Game bookkeeping** — `moveLog`, `moveLogN`, `aiDepth`, `blackDepth`,
  `twoPlayer`, `cursor`, `selSq`.
* **The save block** — `savedBlock` (the exact bytes the game wrote to tape)
  and `rt_*` (the state after those bytes were loaded straight back in).
* **The screen** — `screen`, the whole final screen normalised: `?` glyph bytes
  deleted, the two chess clocks masked, blank lines dropped.

One field is *not* an engine readout: `material` is computed in Python by the
harness from the board bytes. It is redundant with `board128` and is kept only
because it makes a diff easier to read. `panel.Matl` is the engine's own
figure; that one is a real observation.

### The illegal-nudge idiom

The engine only materialises its legal-move list when it has to decide
something. A bare tape load leaves the list empty, and so does picking up an
enemy piece or an empty square — the game rejects those before generating.
Attempting an **illegal move with one's own piece** does force generation and
leaves the position untouched. So every movegen case ends with one such
attempt, always as its last action, and the attempt is itself a test: the
status must read `Illegal move` and the position must be unchanged.

---

## 3. What it covers

| Group | Cases | What is pinned |
|---|---|---|
| `perft` | 2 | The engine's own built-in self-test (key `T`): perft 1–4 from the start position, Kiwipete d3, an e.p. torture position d4, a promotion position d3, and its incremental Zobrist-key / game-phase / PST accumulator re-checked against a recomputation. ~410,000 leaf nodes of movegen + make/unmake for one keystroke. Run on both the 48K and the 128K build. |
| `movegen` | 15 | Full ordered legal-move lists with flags at: start (both colours), Kiwipete (both colours, both machines), an e.p. torture position, a position with a live e.p. target, a promotion position (both colours), castling free / blocked by a covered transit square / with no rights, a pinned-and-in-check position, K+R vs K, and an illegal-move refusal. |
| `moves` | 16 | Both castlings (and take-back of one), an e.p. capture, all four promotion pieces, a promotion left un-chosen, castling-rights loss on a rook move, fifty-move clock ticking and its reset by a pawn move and by a capture, take-back, and a 30-ply Ruy Lopez. |
| `terminal` | 7 | Checkmate both ways, stalemate, insufficient material, the fifty-move boundary, threefold repetition, and the fact that giving check is *not* terminal and (on pristine) is *not* announced. |
| `search` | 9 | The engine's chosen move and score at depths 1, 2 and 3 from the start position, on both machines; a mate in one; an open middlegame position; an undefended rook; and two lopsided positions whose scores expose the pawn and knight values. |
| `material` | 5 | The engine's `Matl` readout with the imbalance multiplied up, one case per piece type, so that a change of a few centipawns in one entry of the value table moves the displayed figure. |
| `saveload` | 3 | The game's own save (`G`) captured off the tape port byte for byte, then fed straight back into its own load (`L`): a position with rights, e.p. target and clocks set; a played game; and a castled position. |

---

## 4. What this suite does **NOT** cover

Read this before you trust a green run.

1. **Only these 57 positions.** This is characterisation, not verification. A
   change that alters behaviour in a position no case visits passes green. The
   suite detects *deviation at recorded points*; it cannot detect deviation
   anywhere else. This is the single biggest limitation and no amount of extra
   cases removes it in kind.
2. **Static evaluation is barely visible.** The engine never displays its
   evaluation function — only the *search* score and the material figure. The
   `material` group pins the piece-value table and the `search` group pins the
   score at nine positions; **piece-square tables, mobility, king safety, pawn
   structure and every other evaluation term are essentially unpinned.** A
   change to them will be caught only if it happens to move one of nine
   recorded scores.
3. **Search internals are not pinned at all.** No case observes the
   transposition table, null-move pruning, late-move reductions, the
   aspiration window, move ordering or node counts. Only the move the search
   returned and the score it reported. Two searches that arrive at the same
   move by completely different routes are indistinguishable here.
4. **Deep search is deliberately not pinned.** Recorded depths are 1–3. The
   engine allocates itself roughly 1/32 of its remaining clock per move, so at
   higher depths a *functionally identical* build with a different cycle count
   could stop at a different node and answer differently. Pinning depth 4–5
   would have manufactured false failures. Depths 1–3 were shown to be
   converged, not truncated (§5).
5. **No long game.** The longest case is 30 plies. Each side has a 5:00 clock
   (15,000 frames) and a scripted move costs frames, so a two-player game much
   past ~35 plies flag-falls inside the emulator. Anything that only goes wrong
   deep into a game — repetition-history growth, undo-stack depth, move-log
   overflow — is out of reach of this suite by construction.
6. **The clocks and flag-fall are not pinned.** They are wall-frame quantities;
   they are masked out of the screen and never asserted. `gameState = 5`
   (flag-fall) is never exercised.
7. **The Zobrist key is not asserted** — see §6.
8. **The position editor (`S`) is not exercised**, and neither is the K+R vs K
   demo (`E`), the board flip (`F`), the two look modes (`C`/`W`), or `N`
   beyond what a new game does implicitly. Positions are injected through the
   game's own tape-load instead, which is a different code path from the
   editor.
9. **The opening book is not exercised as such.** If the engine consults one,
   these cases sample it only incidentally through the `search` group.
10. **Nothing is asserted about the 128K build beyond three cases** (perft,
    one movegen position, one search position). The 128K build uses spare RAM
    banks the 48K build does not have; that machinery is essentially unpinned.
11. **Sound, timing, colour, attributes and the graphical rendering of the
    board are invisible.** The OCR reads characters; the piece glyphs are
    graphics and come out as `?`. A change that draws the wrong piece on the
    right square would be caught only through the memory image, not the screen.
12. **The recorded search scores assume the Zobrist/RNG seeding is unchanged.**
    The engine's Zobrist tables are filled from a PRNG at boot. That seeding
    proved insensitive to every timing perturbation available (§5), but a
    repair whose code changes what feeds the seed could move the transposition
    table's behaviour and the repetition history, and the `search` and
    `tm_threefold` cases would go red with no rules change behind it. Evidence
    that this is not a live hazard for ordinary edits: two single-byte code
    mutants left 55/57 and 56/57 cases green. Evidence it has *not* been ruled
    out: no mutant here changed the code's length.
13. **It cannot tell a regression from an improvement.** If you fix a real
    defect, cases go red. The suite has no way to know which you did.

---

## 5. How the baseline was made, and how it was verified

**Source of truth.** Every value was recorded from
`case01_spectrum_gambit/step1_contract/artifacts/chess.tap` — the pristine
tape. It was recorded black-box, by execution. (The pristine *assembly source*
was not available: the upstream working tree has moved on to a different build
whose code block differs from the pristine tape from byte 12 onward, so it was
used only as a symbol map for workspace addresses, and every address used here
was then confirmed by execution — the board region read back the FEN that was
injected into it, and `genCount`/`moveBuf` read back 20 at the start position
and 48 at Kiwipete.)

**Recorded more than once, under different schedules.** Re-running an identical
command against a deterministic emulator proves nothing, so the baseline is the
**intersection of three recordings under different scheduling profiles**:

| Profile | load frame | wait | gap per move | tail |
|---|---|---|---|---|
| A | 700 | 120 | 900 | 900 |
| B | 780 | 200 | 1050 | 1150 |
| C (search group) | 700 | 300 | 3000 | 2000 |

A field reaches `expected.json` only if **every** recording that covers its
case agrees on it; `--build-baseline` drops the rest and says so. Profile C
gives the engine over three times as long per move: since it agrees with A, the
recorded search results are converged rather than time-truncated. The clock
masking is validated by the same mechanism — A and B run for different numbers
of frames, so an unmasked clock would disagree and be dropped.

Result: **0 fields disagreed across profiles.** The only drops were the 55
`hashKey` fields removed by policy (§6).

**Boot timing was probed separately.** `--play-at 320 / 400 / 512 / 700` and
total frame counts of 1000 / 1500 / 2000 all yield an identical Zobrist key and
RNG state, so the seeding is not frame-counter-dependent in this build.

**Green on pristine, repeatedly.** Three full runs, including one from a
different working directory: 57 ok, 0 failed, 0 errors, exit 0.

**It was checked that it can actually fail.** Four single-byte mutants were
built directly in the pristine tape (locating the tables by their own byte
patterns, and repairing the tape checksum), plus one whole different build of
the engine:

| Mutant | Cases red / 57 |
|---|---|
| knight move delta `0x21 → 0x22` | 16 |
| king orthogonal delta `0x01 → 0x02` | 18 |
| pawn value `100 → 120` | 2 |
| bishop value `330 → 316` | 1 |
| a different, later build of the engine entirely | 44 |

`mutate.py` in this directory reproduces all four, and records how the target
tables were located: by searching the binary for byte patterns that any
`0x88`-board engine must contain (the knight deltas, the orthogonal king
deltas, the little-endian piece values), chosen from first principles about how
such engines are written.

The pawn-value mutant is the reason the `material` and the two lopsided
`search` cases exist: **an earlier version of this suite passed that mutant
49/49.** The value table was invisible until cases were added whose recorded
numbers depend on it. Treat that as the calibration of how much of §4.2 is
still open: the same blind spot certainly remains for the evaluation terms that
have no readout at all.

The mutants also say something about **false** failures, which matter as much:
the pawn-value and bishop-value mutants are code-byte changes, and 55 of 57 and
56 of 57 unrelated cases stayed green. Single-byte changes to the program do
not cascade into spurious failures elsewhere in the suite. The honest caveat is
that none of these mutants changed the code's *length*, and that could not be
tested without the pristine source (§5, first paragraph).

---

## 6. Fields deliberately not asserted

* **`hashKey`** — the engine's 16-bit Zobrist key. Its tables are filled at
  boot from a PRNG, so the key is a property of one build's boot rather than of
  the chess. It proved stable here across every scheduling and boot-timing
  perturbation available, but it is an internal hash, not behaviour, and a
  repair that shifts code layout could move it without changing a single move.
  Asserting it would buy nothing and could cost a false alarm. Excluded in
  code, in `POLICY_EXCLUDE`, with this reason attached.
* **The two chess clocks** — masked out of `screen`, never asserted.
* Anything else that disagreed between profiles — nothing did, but the
  mechanism is in place and reports what it drops.

---

## 7. Re-recording

```sh
./characterise.py --tap PRISTINE.tap --record recA.json --profile A
./characterise.py --tap PRISTINE.tap --record recB.json --profile B
./characterise.py --build-baseline recA.json recB.json     # -> expected.json
```

> **Do not re-record against a build you are repairing.** `expected.json`
> derives its entire value from the fact that it came from the pristine tape.
> Re-recording against anything else silently redefines "correct" as "whatever
> my current build does", and every green run afterwards is worthless.
> `--record` takes an output path of its own, so it cannot touch
> `expected.json` unless you name it explicitly, and `--build-baseline` refuses
> to emit a baseline containing a case that only one recording covers.

Other flags: `--filter GROUP_OR_NAME`, `--verbose` (print the recorded values
of passing cases), `--keep` (keep the temp `.sna`/`.tap` artefacts),
`--harness DIR` / `--emu` / `--rom` if the harness is not in its usual place.

---

## 8. Files

| File | What |
|---|---|
| `characterise.py` | the runner, the recorder, and the baseline builder |
| `cases.py` | the 57 cases — positions, move scripts, what each is for |
| `expected.json` | the recorded pristine observations |
| `mutate.py` | the single-byte tape mutator used to show the suite can fail |
| `README.md` | this |

Requires `python3` (stdlib only) and the case01 harness — `build/hc91emu`
(prebuilt and committed) and `roms/48.rom`. Nothing outside this directory is
written to; temporary tapes and snapshots go to a `tempfile` directory and are
deleted.
