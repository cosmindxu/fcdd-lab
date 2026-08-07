# Characterisation suite for the ZX-Spectrum chess engine

This suite pins down **what the program actually does**, so that you can tell
whether a change you made preserved the behaviour you did not mean to touch.

It was written by reading and running a known-good build of this program — not
the one in your workspace. Everything it asserts or records came from that
build. It is an oracle for *existing behaviour*, and nothing more: it is not a
specification, it was not written by the program's author, and it does not
know what the program was supposed to do.

**132 cases, about 25 seconds.** No network, no dependencies beyond `python3`
and the emulator in `harness/`.

---

## Running it

```sh
./run.py --tap ../variants/bugNN/chess.tap        # a build you already made
./run.py --variant ../variants/bugNN              # runs `make` first
./run.py --tier 1 --tap ...                       # rules only, ~20 s
./run.py --only movegen,terminal --tap ...        # one or more groups
./run.py --tap ... -v                             # list every case, not just failures
./run.py --tap ... --json results.json            # machine-readable results
```

`--harness DIR` (or `$HC91_HARNESS`) if the emulator is not found automatically;
it looks for the directory holding `build/hc91emu` and `tools/chesspos.py`.

### Exit codes — read these before you interpret a run

| code | meaning |
|---|---|
| **0** | everything matched |
| **1** | a **TIER 1 (RULE)** case failed |
| **2** | only **TIER 2 (GOLDEN)** cases differ |
| **3** | the suite could not run (no harness, no build, emulator crash) |

---

## The two tiers, and what a red case means

This distinction is the whole point of the suite. Ignoring it will waste your
time.

### Tier 1 — RULES (66 cases)

Expectations written from the **rules of chess** and from the program's own
documented interface, *independently of what this engine does*. Every tier-1
case carries the rule it rests on, and `run.py` prints that rule when the case
fails:

```
FAIL   move/castle_through_check   O-O refused when the transit square f1 is attacked
       rule: The king may not pass through an attacked square; a rook on
       f8 covers f1 and forbids O-O.
```

A red tier-1 case means the build is **wrong**, in a way that does not depend
on anyone's opinion. There is no legitimate reason for one to be red.

The expectations were written before the reference build was run. Where the
first draft disagreed with it, the disagreement was resolved by re-deriving the
chess — which found four mistakes in the draft and none in the engine. Where
the engine genuinely makes a defensible choice that FIDE leaves open, the case
was **demoted to tier 2** rather than asserted (see `term/fifty_move_boundary`,
`term/threefold`, `ui/takeback_movelog`).

### Tier 2 — GOLDENS (66 cases)

Values **recorded from the reference build** and stored in `golden.json`. They
are what the program did, not what chess requires. A red tier-2 case says:

> this build no longer behaves the way the reference build behaved here.

That is **information, not a verdict**. If you deliberately changed the search,
the evaluation or a draw rule, the goldens in that area *should* change, and a
diff there is evidence your change took effect. A diff somewhere you did not
expect is worth understanding before you stop.

A worked example, from a build with real (intended) search improvements: all 66
rules stayed green and 3 of the 66 goldens moved. That is the shape a healthy
change makes.

**Do not run `--record` to make red goldens go green.** `--record` overwrites
the baseline, which destroys the only record of what the program used to do.

---

## What is covered

| group | n | what it pins |
|---|---:|---|
| `perft` | 1 | the engine's own perft + incremental-state self-test (`T`): four boards over seven position/depth pairs, 410,082 nodes, against published counts — `perft(startpos)` = 20/400/8902/197281 at depths 1–4, Kiwipete d3 = 97862, the standard e.p. position d4 = 43238, the standard promotion position d3 = 62379 |
| `load` | 11 | loading a position is the identity: board, side, castling rights, e.p. target, halfmove clock, move number, over 11 positions |
| `movegen` | 27 | all four castlings; castling refused when blocked, when the transit square is attacked, while in check, and when the rights bit is gone; rights lost by king and by rook moves; the e.p. target set by a double push, captured, and expiring one ply later; promotion to Q/R/B/N, for both colours, and by capture; a pinned piece along and off its line; a king refusing an attacked square; a move that fails to answer a check |
| `clock` | 3 | the fifty-move counter resets on a pawn move and on a capture, and increments otherwise |
| `terminal` | 8 | fool's mate → *white-mated*; a back-rank mate → *black-mated*; a queen stalemate → *stalemate* (not mate, not draw); K vs K and K+B vs K → *draw*; 98 halfmoves is not yet a draw; **recorded**: the exact halfmove boundary, and threefold repetition |
| `save` | 3 | the engine's own `G` (save to tape) followed by `L` (load) reproduces the state exactly — after castling, after a double push (e.p. target survives), and with a high halfmove clock. Self-checking: no baseline involved |
| `ui` | 9 | `Z` restores the position after a take-back; `N` restores the initial array; the level keys 1/3/4/5 set the search depth; **recorded**: what `Z` leaves in the move log, what `Z` does after an engine reply, and the position the `E` demo loads |
| `search` | 61 | 17 positions × depths 1–3 (plus depth 4 on four of them): the move the engine chose, the score it reported, and the position that resulted. Openings, an in-check position, a capture-rich position (quiescence), material imbalances, pawn/rook/bishop endgames, a promotion race, an available knight fork, a closed middlegame. 6 of these are tier-1: the engine must answer with exactly one move |
| `search128` | 3 | the same at depth 3 on the **128 KB machine**, whose transposition table lives in a banked RAM page — a different code path |
| `game` | 6 | three short scripted games (8–10 plies) where the engine answers every move, so make/unmake, the transposition table and the incremental accumulators are carried across plies rather than reset. Tier 1: the engine answers every legal move |

Fields deliberately **not** compared: `hashKey` (the Zobrist tables are seeded
from the code image, so any change in code size moves every key — it is not a
behavioural observable) and the on-screen clocks (they measure how many frames
the search burned, i.e. code speed, not correctness).

---

## What is NOT covered — read this before trusting a green run

A green run is evidence, not proof. This suite is a **sample of behaviour**,
taken through the only interface the program offers: keystrokes in, screen and
memory snapshot out.

1. **There is no independent move generator here.** Move generation is pinned
   by the engine checking *itself* against hard-coded perft counts, plus 27
   hand-written legality cases. A generation fault that leaves all five
   self-test positions' node counts intact and misses all 27 cases will pass
   unnoticed. Nothing in this suite compares full move lists against a second
   implementation.

2. **Static evaluation is not observable at all.** The program displays the
   *search* score, never the static evaluation. Every "evaluation" case here is
   really "the search at depth *d* returned this number". An evaluation change
   that the search smooths over is invisible.

3. **The transposition table, move ordering, null-move pruning, late-move
   reductions and the internals of quiescence are unobserved.** Only their
   effect on the chosen move and the reported score is recorded. A table that
   returns wrong entries but happens not to change the top-level choice on
   these 17 positions will pass.

4. **Check detection has no direct observable.** The status line does not say
   "check". Check is pinned only indirectly, through move legality and through
   mate/stalemate classification.

5. **No long games.** Each side has a five-minute clock and the harness must be
   given a frame budget per move; beyond roughly ten plies a scripted game
   stops being reproducible — eight-move lines were tried and lost moves at
   every frame budget. Anything that only goes wrong deep in a long game, or in
   a long repetition history, is outside this suite entirely.

6. **Everything except the perft self-test is a sample.** 17 search positions,
   3 short games, 11 loaded positions. Nothing here is exhaustive.

7. **Two machine configurations, unevenly.** 48 KB for everything, 128 KB for
   three search cases only.

8. **Positions are injected through the game's own save/load block**, so the
   `load` group is on the critical path of almost every other case. A fault in
   the loader would light up many groups at once and could easily be mistaken
   for a fault in what they were meant to test. If `load` is red, fix that
   reading first.

9. **Timing, not chess, can turn a case red.** The engine-move cases assume the
   engine finishes inside the frame budget. A build that is substantially
   slower may lose a keystroke; that shows up as a `moveLogN` mismatch. If you
   see one, check whether the move was made at all before concluding anything
   about the chess.

10. **Not covered at all**: the position editor (`S`), the flip and look keys
    (`F`, `C`, `W`), sound, screen rendering and the piece graphics, tape
    loading edge cases, and what the five strength levels mean beyond setting
    the depth byte.

11. **The suite does not know what is correct beyond the rules it states.** The
    program has documented divergences from FIDE, and one of them is recorded
    here as a golden rather than judged. If the behaviour you are looking at is
    a golden, this suite has no opinion on whether it is right.

---

## Files

| file | what it is |
|---|---|
| `run.py` | the runner. `--record` rewrites the baseline (see the warning above) |
| `cases.py` | the 132 cases, as data. Tier-1 expectations and their rules live here |
| `charlib.py` | the emulator driver: a fixed keystroke schedule, and the state read back from a snapshot |
| `golden.json` | the recorded tier-2 baseline |

Adding a case is editing `cases.py`. A tier-1 case needs an `expect` block and
a `rule` sentence that justifies it without reference to this engine; a tier-2
case needs neither — run `./run.py --tier 2 --record --only <your case>` on a
build you trust.

Every golden was captured twice and the two runs had to agree before it was
written, so a value that is not reproducible never became an expectation.
