# Case 04 — descriptive reading (NOT a verdict)

Status: descriptive observations from the scored data, after the
constraint-violation close-out (PREREG amendment A-2026-08-26,
ledger/review_round1.md). Nothing in this file is a causal claim. All
numbers are emitted by deposited scripts (C10): `ledger/runs.json`,
`tools/analyse_case04.py`, `tools/review_evidence.py`.

## The pattern the data shows

1. **Direction as hypothesized, at a weak sample.** Arm A policy
   disagreement μ₂ = {0.088, 0.078, 0.078, 0.010, 0.088}, mean 0.0684;
   Arm B (pro) μ₂ = {0.088, 0.119, 0.231, 0.302, 0.183}, mean 0.1845.
   Every armA run is ≤ every armB-pro run — strictly below all but one
   (a tie at 0.088). Bootstrap CI on the mean difference excludes zero;
   exact permutation p = 0.1181 (α = 0.05 not met; k = 5/5 pro runs).

2. **Variance reduction is the more robust signal.** sd(μ₂): armA
   0.033 vs armB-pro 0.086 vs armB-flash 0.269. Arm A clusters in a
   narrow *good* band; direct development spreads across the whole
   range (0.000–0.503). This clustering is not explained by source
   access alone: within armB, two cells that both read the leaked
   engine source scored 0.088 (r4, 67 reads) and 0.231 (r2, 10 reads)
   — the spread persists among readers — while armA cells converged
   whether they read much (r1, 32 reads → 0.088) or little (r2, 4
   reads → 0.078). The pattern is consistent with the FCDD mechanism:
   a formal target anchors independent attempts onto the
   spec-faithful implementation.

3. **No measurable cost penalty.** H2: median cost ratio B/A = 1.10,
   exact p = 0.93. Completion 100% both arms.

4. **The cheap-model sweep repeats the pattern.** The flash cells
   (s1–s3: 0.503, 0.088, 0.000) show the same wide spread — weakly
   consistent with the spread being a property of direct development
   rather than of the primary model.

5. **The rules layer says nothing.** μ₁ = 0 for 12 of 13 runs (0.111
   for armB_r3) — the layer the calibration already declared
   uninformative at this budget, including for the cells with zero
   detectable source access.

## Why this is only a pointer

The leak (F1–F3) confounds the comparison in the observed direction:
armA cells were on average heavier readers of the sealed engine source,
and the two best runs are proven transcriptions of leaked constants.
The arm-level difference therefore admits an explanation — differential
source access — that has nothing to do with the treatment. The
observations above are the pattern the data would be consistent with
under the hypothesis; they are not evidence for it.

## The falsifiable takeaway for a future clean run

If the prevention claim is real, the observable effect in this task is
**anchoring/variance reduction more than raw quality**: formal
expression should compress the per-run spread of behavioural
disagreement, not just shift its mean. That is a testable,
pre-registerable hypothesis: sd(μ₂) as a co-primary outcome, with the
information-symmetry controls fixed (REPORT.md §8, local manuscript).
