# Adversarial review — the four lenses, reviewer contract, convergence

Fan out FOUR independent reviewers (one per lens), in parallel, each on a distinct lens. Never one
generalist — the value is that no single reviewer holds all four framings at once. Route to your
strongest / most-independent reviewer (a different model than the author, or a different person /
team). Each prompt is a template: substitute the target files, the tool names, and the domain.

## Shared reviewer contract (put in every prompt)

- Repo/target is READ-ONLY (or a copy); probe scripts ONLY under a scratchpad; never touch live
  config/secrets — read them, don't write them.
- **Prove findings by EXECUTION.** A finding is CONFIRMED only if you ran it; otherwise mark it a
  hypothesis. Speculation without a repro is not a finding.
- For every attack that fails, write one line: "attacked, no defect found" — **padding a report
  with weak findings is itself a review defect.**
- Rank: HIGH (a reachable safety hole / a will-not-run / a materially false doc claim) / MED
  (proof-strength, over-tightness, fragility, overclaim) / LOW (hygiene). Give a concrete
  reproducing input or exact file:line per finding.
- End with a one-line verdict on the target's fitness.

## Lens A — SPEC ADEQUACY (the contract itself)

The dangerous direction is UNDER-specification. Attack:
1. **Bad cases that CONFORM.** Construct legitimate-looking traces that violate real intent yet
   satisfy every clause. Systematically: is each lane that can cause harm actually constrained? (a
   money/action lane with no timing or precondition clause is the classic hole). Is any clause
   vacuous under the witnesses that "prove" satisfiability?
2. **Good cases that VIOLATE** (alarm fatigue): legitimate operations the spec flags — schedule
   shifts (DST, half-days), diagnostics, allowed compositions the spec over-forbids.
3. **Vacuity / tautology hunt.** Which theorems are real, which are eta-projections of one clause?
   Are the satisfiability witnesses non-degenerate (do any exercise the guards/quantifiers, or are
   all premises False)? Verify the claimed axiom profile by running the kernel.
4. **Constants vs reality.** Do the spec's pinned constants match the actual schedule/config/units?
   A spec judging a fictional system is worse than none.
5. **Theorem-claim audit.** Does the incident theorem pin the ACTUAL incident or just any member of
   a class? Do same-value booleans secretly weaken a temporal ("A precedes B") doctrine?

## Lens B — TWIN FIDELITY (spec ↔ implementation)

1. **Clause-by-clause diff.** Field count vs clause count; quantifier structure; boundary operators
   (≤ vs <); scoping; premise/conclusion direction; default values (does an unset field read in a
   direction that differs from the formal total function?).
2. **Assault any clever algorithm.** An O(n) scan replacing a nested quantifier, a cache, a
   memoized check: enumerate ALL small inputs (e.g. 2^8 × 2^8) plus adversarial patterns (boundary
   coincidences, empty, full, interleaved, reversed) against a DIRECT transcription of the formal
   quantifier. Any mismatch is HIGH.
3. **Edge semantics.** Out-of-domain values (indices past the modeled range, negatives, NaN/inf);
   totality of the formal object vs finiteness of the implementation.
4. **Bridge blind spots.** For EVERY clause, can you construct a violating input the bridge would
   catch? Enumerate clauses with no negative test — those are dead code waiting to happen.
5. **Witness transcription.** Diff the implementation's witness copies against the kernel witnesses
   field by field.

## Lens C — SHELL TRUTHFULNESS ("can the shell lie?")

False-NEGATIVES first (the dangerous direction):
1. **Circular evidence.** Is observable X derived mostly FROM observable Y such that the clause
   relating them is nearly unfalsifiable at runtime? Quantify the INDEPENDENT evidence (how many
   samples, from where, and does that source fail under the same conditions as the thing it's
   supposed to catch?).
2. **Structurally-unfalsifiable clauses.** Which checks set both sides of their implication from
   the SAME record (attempt-adjacency)? Census them: which are acceptable-and-documented vs which
   make a monitoring claim hollow. A safety clause that can only fire on an evaluator bug, never on
   a world state, is decorative — say so.
3. **Parsing / tz / classification fragility.** Timezone (naive vs aware, UTC vs local — demonstrate
   any minute shift); a mis-parsed timestamp silently dropping all events of a kind; classification
   off by a stale/edge config value → the day judged against the wrong clause set.
4. **False-POSITIVES** (alarm fatigue): the same fragilities firing the other way; conservative
   syntheses that over-trigger (a single-episode assumption on multi-episode data).
5. **Robustness.** Corrupt/truncated inputs, empty files, a size cap silently dropping the relevant
   window, missing files, a failing subprocess. Does a mere record-append failure flip the exit
   code and spam alerts?

## Lens D — INTEGRATION + DOCS ("will it run, do the docs tell the truth?")

1. **The wiring, token by token.** Will the scheduled job actually run from its real cwd/env?
   (extract the EXACT payload, run it from `$HOME`). Does a fallback branch double-execute or
   spam? Compare against neighboring working lines.
2. **Exit-code / alert contract.** What EXACTLY happens on the first run and on a benign day?
3. **Package truth.** Extract the artifact; grep for secrets (expect 0, independently of the
   builder's own claim); confirm the new files ship and run from install paths.
4. **Doc-claims audit, line by line.** Every "derives X", "monitors Y", "validated on Z": does the
   shipped code do it? Re-run the validation claims. Count the things the docs count.
5. **Lifecycle gaps.** Session-mortal schedulers, unrotated ledgers, ordering hazards between
   stacked jobs.

## After the fan-out (the author's job)

- **Ground-truth every load-bearing finding by execution** before accepting AND before rejecting —
  reviewers are also verified by two-independent-checks (their claim + your re-run).
- Fix at the correct layer (spec / twin / shell / wiring / docs), never by special-casing a test.
- **Re-review the fixes** — a focused pass; material changes to a safety verdict get one more.
- **Convergence is PER-SURFACE, not global.** Within a FIXED review surface, reachability decreases
  round over round (reachable → pure-contract-only → hygiene) — stop when a round yields only
  residuals you NAME in writing (trigger + why accepted + roadmap fix). But **widening the surface
  legitimately re-opens reachable findings**: a new lens, a bigger diff, or the shipped-vs-staged
  artifact is a new surface — reset the expectation and expect reachable finds again. (In the arc a
  narrow "GO" was followed by a full-code review that found new reachable arming blockers, and one
  deployment bug recurred five times — so "strictly decreasing globally" is false; per-surface is the
  honest criterion.) Update the decision log and the falsifiability tiering after each surface closes.
