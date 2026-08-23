# Where FCDD's unpredictability lives, and the one change that addresses it

**2026-08-23.** Derived from case02's 56 runs. Every figure below is recomputed
from the deposited result files and the run workspaces; the script is
`tools/attack_budget_evidence.py`.

## The finding

Case02 tested whether FCDD makes repair cost more predictable and found it does
not — the point estimate ran the other way. This locates *why*.

| arm | review rounds per run | spread | *r*(rounds, cost) | median within-cell cost spread |
|---|---|---|---|---|
| A — ordinary dev + review | 1–3, median 2 | 3× | −0.21 | **1.30×** |
| B — FCDD | 1–**18**, median 3 | **18×** | **+0.72** | **1.75×** |

Round count explains roughly **half** of Arm B's cost variance (r² ≈ 0.52) and
none of Arm A's. Arm A's review is bounded by construction; FCDD's ATTACK beat is
not.

## What the extra rounds bought

Nothing measurable.

| | mean cost | artefact |
|---|---|---|
| runs with ≥ 6 round-mentions (n = 9) | **$48.33** | identical to pristine |
| runs with ≤ 2 round-mentions (n = 12) | **$28.42** | identical to pristine |

All 56 runs in both arms produced a byte-identical, correct binary (case02 A12).
So on this benchmark **every additional attack round in every long run found
nothing that changed the artefact**, at a 1.7× cost premium and with the round
count itself varying 18-fold.

## Why the beat behaves this way — it is doing what it says

Beat 4's termination rule is not sloppy; it is deliberately open. From the skill:

> Convergence is **per review-surface, not global**: … within an unchanged
> surface, severity trends down and a round yields only accepted residuals; when
> you WIDEN the surface … reset and expect reachable finds again. **A late-round
> reachable find is not a failure of convergence — it is evidence the surface
> grew.**

That reasoning is sound about *surfaces* and is exactly the variance generator.
The rule conflates two properties that should be separated:

1. **Coverage** — have all four lenses been applied to the declared surface?
   Bounded, checkable, costs a known amount.
2. **Convergence** — has iteration stopped producing findings? Unbounded,
   judgement-based, costs whatever it costs.

FCDD currently stops on (2). Case01 §4.2 already reported the consequence under
the title *"Unbounded review has no fixed point."* Case02 priced it.

## The change: stop on coverage, budget convergence

Replace *iterate-to-convergence* with a **declared adversarial budget**.

- Declare the surface set **S** before the beat starts.
- **Mandatory pass:** for each surface, all four lenses, **one round, in
  parallel**. Cost = |S| × 4 agents. Known before you start.
- **Remediation:** if any finding is CONFIRMED blocking, exactly **one** further
  round, scoped to the affected surface, re-verifying only that finding.
- **Hard stop at two rounds.** Residuals are named in writing and shipped, which
  the method already requires.
- **Widening the surface starts a NEW attack with its own declared budget.** It
  is not a continuation, and its price is quoted separately.

The mandatory pass preserves the property that actually catches defects —
**four independent lenses**, the diversity argument — and removes the iteration,
which on this benchmark caught nothing. Cost becomes a constant the operator can
quote in advance rather than a random variable with an 18× range.

## What this trades, stated honestly

**The evidence is from a benchmark where nothing failed.** All 56 runs succeeded,
so "extra rounds found nothing" is measured on faults that were easy enough that
one round sufficed. On work hard enough to produce real failures, later rounds
may well earn their cost. This change therefore makes the budget **explicit and
operator-set**, not small: an operator who believes their surface needs six
rounds declares six and pays a known price. What is removed is the *agent's*
discretion to keep going, which is where the variance came from.

**It cannot be validated by case02's data alone.** Case02 shows the cost of
unboundedness and shows it bought nothing *there*. It cannot show what bounding
would lose elsewhere. The honest status of this change is: a diagnosis with
strong evidence, and a fix whose benefit is predicted rather than demonstrated.

## How to validate it cheaply

Not another 56-run study. Two steps:

1. **Retrospective, free.** Re-read the 28 Arm B `FIX_NOTES.md`. For each run,
   ask whether any finding accepted after round 2 changed the shipped artefact.
   Case02 already answers this globally (no artefact differs), but a per-finding
   pass would show whether any *contract* clause survived only because of a late
   round.
2. **Prospective, small.** A single defect, k = 6 runs under bounded ATTACK
   against the 4 existing unbounded runs of the same defect. Compare the spread,
   not the mean. Roughly $180 — an eighth of case02 — and it measures the
   quantity the change is supposed to move.
