# Adjudication protocol — the third party

The adjudicator assigns every severity and decides every match. Arms report
findings; **no arm grades its own or the other's work.**

## Identity, pinned

- **Opus**, model string recorded in the freeze commit and verified per
  adjudication run from recorded usage (C3).
- **Transcript-blind:** sees the scrubbed tree, the probes, and the finding
  statements. Never sees which arm produced a finding, either arm's reasoning,
  round counts, or costs.
- Findings are presented **shuffled and arm-stripped**, in one pool.

## Confirmation — a finding is real

A finding is CONFIRMED iff its deposited probe, run on the scrubbed tree,
demonstrates the stated wrong behaviour. Prose without a runnable probe is
recorded as UNCONFIRMED and is not a finding for any outcome.

## Severity — BLOCKING is mechanical

**BLOCKING** iff the confirmed demonstration shows a **wrong verdict, or a wrong
money-path action, reachable via a named caller** in the unit's declared surface.
"Reachable via a named caller" means the adjudicator can state the call path; a
defect only reachable by inputs the callers cannot produce is **NON-BLOCKING —
unreachable**, recorded, not counted.

Everything else is NON-BLOCKING. There is no middle tier: the primary counts
BLOCKING only, so a tier that invites judgement would decide the study.

## Matching — the probe-transfer test

Two confirmed findings **match** iff the adjudicator determines that **one fix
location resolves both probes**. This replaces "same behaviour at the same site",
which mis-scored a shared root cause probed via two different callers.

- Adjudicator states the fix location for each; same location ⇒ match.
- If it cannot decide, the pair is recorded **DISPUTED** and reported as such —
  never silently merged, never silently split.

## Residual absorption — the specificity criterion

A CONV finding is absorbed by a BUDGET **named residual** (and scored
*found-unconfirmed*, not *missed*) **only if the residual names the specific
trigger condition the probe demonstrates.**

- Sufficient: *"boundary handling in `stale()` at age == limit is unverified"*.
- Insufficient: *"anything in module X's boundary handling"* — a residual broad
  enough to absorb an unknown finding absorbs nothing.
- Judgement calls go to DISPUTED, which is reported, not resolved silently.

## Outputs

Per finding: `confirmed | unconfirmed`, `blocking | non-blocking | unreachable`,
match-group id, `absorbed-by-residual | not`, and the stated fix location. Every
DISPUTED item appears in the report with both readings.
