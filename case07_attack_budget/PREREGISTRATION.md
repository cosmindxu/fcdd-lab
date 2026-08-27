# CASE 07 — is the ATTACK budget safe? (pre-registration, DRAFT)

**Deliberately short.** Five cases taught that long designs written before the
subject is qualified get abandoned; this one is ~100 lines and gets one review
and a pilot before anything else is written.

## 1. What is being tested, and why this one

`method/ATTACK_BUDGET_DIAGNOSIS.md` measured, from case 02's 56 runs, that FCDD's
ATTACK beat ran **1–18 rounds** on repeats of the same defect, that round count
correlated **r = +0.72** with cost and explained about half its variance, and that
runs with ≥ 6 rounds cost **$48.33** against **$28.42** for runs with ≤ 2 — while
**all 56 runs produced a byte-identical artefact**, so no extra round changed
anything. The fix — stop on *coverage*, budget *convergence* — shipped as **law
12** and is live in the method today.

**It shipped on a measured diagnosis with a predicted benefit. Nobody has tested
whether the bounded rule is safe.** That is the question here, and it is the only
study in this programme that tests a claim the method actually makes: the skill's
own §5 says its value is *late*, in adversarial review.

**H1.** Bounded ATTACK (law 12) misses no CONFIRMED BLOCKING finding that
unbounded ATTACK finds, at materially lower cost.

**Falsified by:** any confirmed blocking finding that the bounded arm misses and
the unbounded arm reports. One is enough — law 12 would then be unsafe as written
and must be amended or reverted.

## 2. Why it is decidable, and informative either way

**There is no oracle and nothing to steal.** The comparison is between the two
arms' *outputs*, not against a hidden truth: run both on the same artefact and
diff the finding sets. The leak class that voided cases 04–06 cannot exist here.

**Both outcomes are results.** If the arms find the same set, law 12 is confirmed
and the programme has its first tested improvement to the method. If the bounded
arm misses blocking findings, law 12 is refuted and gets reverted. Neither
outcome is a null-by-benchmark.

## 3. Arms — identical except the stopping rule

Both run FCDD's ATTACK beat, same lenses, same model, same artefact.

- **CONV** — iterate to convergence (the pre-law-12 rule, quoted verbatim from
  the frozen skill).
- **BUDGET** — law 12: declare the surface set **S**; one mandatory pass, every
  lens against every surface, in parallel; at most one scoped remediation round;
  hard stop at two.

Neither cell is told what the study measures. (Case 06's round 1 caught the
method text naming its own study and stating its endpoint; the cell-facing text
is checked for that before any run.)

## 4. Subject: `ikbr_tools`, which is the method's declared domain

Money paths, live guards, risk watchers, kill switches — *"anything load-bearing
whose silent failure beats its loud one"*, in the skill's own words. **The first
time this programme has tested FCDD inside its stated scope.**

**Variant pinned: FCDD-T** (transcription twin + bridge) — the variant the
subject codebase actually uses and the one cases 01/02 measured. The ATTACK beat
is shared by both variants, so H1's conclusion transfers to FCDD-X only to the
extent Beat 4 is variant-independent; that limit goes in the report.

Review units are whole modules, ~1,100–3,300 lines. Selection is **stratified by
prior hardening**, pre-registered before any run, because FCDD was distilled from
this codebase's own R18 arc: modules named in `references/case_study.md`
(riskwatch/R18 composite, ops-monitor) are the **hardened** stratum; the rest are
**unhardened**. Reporting is per stratum — an already-attacked module is a
different test from a fresh one.

## 5. Outcomes

| | Measure |
|---|---|
| **Primary** | confirmed blocking findings reported by CONV and **missed** by BUDGET, per unit |
| Secondary | cost ratio BUDGET : CONV, on both COMPLETING and CONSUMED accounting |
| Secondary | rounds executed per arm, and the spread across repeats |
| Secondary | total confirmed findings per arm, by severity |
| Descriptive | findings unique to BUDGET (the bounded pass is parallel, so it may find *more*, not less) |

**A finding counts only if CONFIRMED BY EXECUTION** — a failing test, an executed
counterexample, a demonstrated trace. That is the skill's own standard
("verify-by-execution, ground-truth every finding yourself") and it makes the
outcome mechanical rather than a judgement about plausibility.

**Confirmation is done by a third party**, never by either arm, so no arm grades
its own findings.

## 6. Controls carried from five cases

- Cells isolated from each other, disjoint workspaces (C23 — case 04's cells read
  each other's work).
- Model pinned and verified per run from recorded usage, subagents included (C3).
- **Dual cost accounting**, COMPLETING *and* CONSUMED, with a mechanical
  infrastructure-death classifier; the headline is named before the first run
  (case 04: the choice moved an answer from 0.88× to 1.33×).
- Every reported number emitted by a deposited script (C10).
- Amendments append-only; ≥ 2 adversarial review rounds before believing any
  result (C11).
- No optional stopping; the analysis script dry-runs against a real pilot cell
  before freezing (C5).

## 7. Pilot, and the gate that stops this cheaply

**k = 2 per arm on 2 units.** The gate: the units must yield **≥ 1 confirmed
finding**, or there is nothing for the arms to differ about and the corpus is the
finding. Pilot cells are excluded from inference.

The pilot also fixes what this document deliberately leaves open: k, n, the
per-cell timeout and attempt cap, and the schedule ceiling — measured, not
asserted. (Case 05 stated "k = 3" and "k = 10–20" ten lines apart; nothing here
states a number the pilot has not produced.)

## 8. Status

**DRAFT.** Not frozen. Owed before any scored run: one adversarial review round,
then the pilot, then the numbers this document leaves blank.
