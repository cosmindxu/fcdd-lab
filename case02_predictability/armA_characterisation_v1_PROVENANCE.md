# Provenance and disclosures — for the study operator

**This file is addressed to the operator of case02, not to an Arm A run, and
it deliberately lives OUTSIDE `armA_characterisation/` so that copying that
directory wholesale into an Arm A workspace cannot carry it along.** It names
the pristine build's path and hash, the sealed material, and the study's
asymmetries — none of which an Arm A run may see. `armA_characterisation/` is
the shippable packet; its `README.md` is the Arm-A-facing document and is
written to be safe to hand over as-is.

## What this artefact is

Arm A's cost-matched counterpart to Arm B's formal contract, per
`PREREGISTRATION.md` §3: a characterisation-test suite derived from the
pristine engine, built once, before any repair run, and given to every Arm A
run exactly as the contract is given to every Arm B run.

## Source of truth

The oracle is `case01_spectrum_gambit/step1_contract/artifacts/chess.tap` — the
pristine build the contract author produced in step 1.

Its sha256 is `33ed86b2cdec18ab3147376903739882210581f303321882141770dd6ba978b4`,
which is **bit-identical** to the entry for `sealed/seedkit/pristine/chess.tap`
in `case01_spectrum_gambit/ledger/sealed_manifest.sha256`. The baseline is
therefore the same build the variants were seeded from. The manifest lives in
`ledger/`, not `sealed/`, so this was checked without opening the seal.

Nothing under `arms/variants/` or `sealed/` was read, listed for content, built
or run. The current working tree at `/media/sf_Projects/HC91_emulator/chess/`
was **not** used as a source: its sources have moved on since case01 (revived
aspiration window, negamax draw detection, 24-bit Zobrist keys, transposition
table changes), so it is not pristine. It was used once, as a black box, only
to confirm that the runner reports differences against an unfamiliar build
gracefully.

The pristine `.tap` itself is deliberately **not** shipped with the suite. Only
observable values (FENs, game states, move logs, scores, perft counts) are
recorded. Shipping the binary would let an Arm A run diff it against the
variant and localise the fault instantly, which would be a strictly stronger
oracle than the contract Arm B holds.

## Disclosure 1 — the author saw the seeding prompt

While locating the pristine snapshot I read
`case01_spectrum_gambit/prompts/seeding_prompt.md`, which names the seven fault
*classes* the seeding agent was told to use. **Arm B's contract author never saw
that list.** This is an asymmetry in the opposite direction from the one case02
exists to remove, and it must be stated in the paper.

Mitigation, and why it is probably small:

- The coverage checklist was taken from two sources that predate and are
  independent of that prompt: the contract's own clause map C1–C14 plus S1–S4
  (`step1_contract/SUMMARY.md`, which the task instructed me to read), and the
  areas named in my own task statement (move generation, search at fixed depth,
  evaluation of known positions, perft, terminal detection, save/load).
- Those two sources already cover the same ground. The seeding classes —
  movegen/legality, promotion, mate/stalemate, search/TT, quiescence, eval,
  draw accounting — are the obvious partition of a chess engine, and are what
  the contract's fourteen clauses are about.
- No test was aimed at a specific fault, because no fault is known to me. The
  suite has no idea which variant contains what.

The residual risk is one of *emphasis*: knowing the classes exist may have made
me weight, say, draw accounting more heavily than a blind author would have.
`term/`, `clock/` and the draw goldens are where that would show.

## Disclosure 2 — the tier boundary was set with the engine's answers in view

Tier-1 expectations were written before running the engine, and 55 of the first
60 matched on the first attempt. Of the five that did not:

- four were **my errors** (`move/promote_white_b`, `move/promote_white_n`,
  `clock/reset_on_capture`, `clock/increment_on_quiet`) — I had overlooked that
  the resulting positions were K+B/K+N vs K, i.e. dead. The engine was right;
  the expectations were corrected and two of the positions were given a spare
  pawn so that they test the clock and not the material rule;
- one was a **real engine characteristic**: `Z` restores the position but does
  not truncate the move log. The rule was narrowed to the position (which is
  what a take-back must restore) and the log behaviour was recorded as a
  tier-2 golden with a note.

That last move — narrowing a rule after seeing the engine disagree with it — is
the one place where the engine's behaviour influenced where the tier boundary
sits. It is recorded in `cases.py` at the case itself.

## Cost

I cannot observe my own token spend from inside the session; the operator
measures it from the transcript the way step 1's $21.75 was measured. My own
estimate is in the delivery report. Emulator time is free in token terms: the
whole suite is ~25 s of wall clock and ~500 emulator runs were used during
development.

## Ways this is not a fair counterpart to the contract

Stated plainly because the paper has to say something either way.

1. **It is weaker where the contract is strongest.** The contract carries 95
   kernel-checked theorems with an empty axiom profile and an exhaustive
   410,082-node perft comparison against a *second implementation*. This suite
   has no second implementation at all: its movegen evidence is the engine
   checking itself against published counts. On movement generation the
   contract is a genuinely stronger oracle.

2. **It is stronger where the contract is weakest.** The contract's own
   residuals name evaluation as "the largest un-bridged surface" and make no
   claim about the transposition table, move ordering or null-move safety. This
   suite records 61 real search outputs from the running engine at four depths
   and on two machine configurations, which does constrain those paths — not by
   proving anything about them, but by pinning what they produce.

3. **It localises differently.** A contract violation names a clause. A red
   test here names a position and a field, which is more concrete but less
   diagnostic: it says *where* behaviour differs, not *which property* broke.

4. **Half of it is not falsifiable as "wrong".** 66 of the 132 cases are
   goldens, and a golden diff is not a defect. An Arm A run that changes the
   search will see red tier-2 cases that it is correct to accept. The contract
   has no equivalent category — every clause is a claim. This may make the
   artefact *less* decision-forcing than the contract, and it is the most
   likely way the two arms' artefacts differ in effect on run cost.

5. **Its coverage was chosen by one author with no adversarial review.** Beat 4
   was not run for the contract either, so on this axis the two are matched —
   but neither is clean.

6. **It cannot express a property, only an instance.** "Evaluation is
   antisymmetric" is a clause in the contract. Here it is not expressible: the
   engine only ever searches for Black, so no colour-mirrored pair of
   observations exists that would test it. Several contract clauses (C3
   `makeAgrees`, C4 `unmakeInverts`, C12 `pieceCount`, C13 `kingsUnique`) are
   similarly quantified statements with no direct analogue in a test suite;
   they appear here only as their consequences on particular positions.
