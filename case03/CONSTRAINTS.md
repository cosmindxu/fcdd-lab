# Case 03 — constraints inherited from cases 01 and 02

**Read this before designing anything.** Every item below is a defect that
actually occurred, not a hypothetical. Each names the amendment that records it.
The design is not free to trade these away; it is free to choose *how* it meets
them.

## The disqualifying one

**C1 — no arm may hold the answer, and the check is code.** Case02's treated arm
was shipped `contract/artifacts/chess.tap`, bit-identical to the sealed answer
key, in 28 of 28 workspaces; the control was deliberately denied it on the stated
grounds that holding it would be "a strictly stronger oracle than the contract
Arm B holds" (A17). One `cmp -l` localised any seeded fault. This inverted the
confound the study existed to neutralise and it survived three review rounds,
because the check was a person's diligence and not a program.

*Mechanism, built and retro-tested:* `tools/workspace_manifest_guard.py` runs at
workspace-build time and exits non-zero unless every shipped file is declared in
the arm's manifest with its hash, no undeclared file is present, no file
hash-matches sealed material outside an explicit `intentionally_shared` list, and
no file sits within 64 bytes of a sealed binary. Retro-tested against the real
case02 workspaces: it flags `contract/artifacts/chess.tap` in the treated arm and
passes the control arm clean. **A run that fails the guard does not launch.**

## The one that made case02 unable to answer anything

**C2 — the benchmark must be able to produce failures.** All 56 case02 runs, in
both arms, produced a byte-identical correct program. A benchmark on which both
arms score 100% can discriminate on cost and on nothing else. FCDD's actual claim
is that it prevents **silent** failure — a repair that looks right, passes the
obvious checks, and is wrong. Neither prior case tested that. Case03's faults
must admit plausible-but-wrong repairs, and the acceptance oracle that
distinguishes them must be hidden from both arms and mechanical.

## Measurement discipline

**C3 — model identity must be verified, not assumed (A13).** A second model ran
inside 51 of 56 case02 cells because Task-tool subagents did not inherit the
parent's `--model`, and its share differed by arm (35.5% vs 25.7%). The runner
must pin the model for subagents too, and a per-run check must assert from the
recorded `modelUsage` that only the intended model appears. Mismatch aborts the
cell.

**C4 — the primary estimator must be invariance-checked before freezing (A14).**
Case02's `CV_log = sd(ln c)/|mean(ln c)|` is not scale-invariant: its verdict
moved from *p* = 0.1094 to 0.0469 between dollars and cents, and it was biased
toward the hypothesis because the dearer arm carries a larger denominator. Any
candidate estimator must be tested under every transformation its units admit —
scaling *and* change of measure, since dollars and tokens are not proportional —
before the pre-registration is frozen.

**C5 — dry-run the analysis script against a real completed cell before freezing
(A7, A8).** Case02's frozen script shipped with two defects: it never tested
`is_error`, so an interrupted attempt would have entered a cell as a fifth
observation, and its input path pointed at a directory that does not exist.
Freezing a script before the data exists means freezing one that has never seen
real input.

**C6 — log schedule discontinuities automatically (A6, A16).** Case02 had two:
a nine-day host reboot and an 88.6-hour usage-limit suspension. The second was
found by a reviewer reading `drive.log`, not by the experimenters. The driver
must detect and record any gap beyond a threshold, and the sensitivity analysis
must select cells by identity, never by list position (A18).

## Blinding, if the design grades anything

**C7 — the artefact category is the treatment label (A10).** All 28 case02 arm B
workspaces carried a `contract/` package; no arm A workspace did. No vocabulary
scrubbing disguises a Lean file as a pytest script. Anything graded blind must be
an object both arms produce in the same form.

**C8 — the blinding audit must cover the scrubber's own output (A16).** Case02's
audit certified 0-vs-0 while the substituted phrase "the design note" leaked in 3
of 28 packets, because the term list was written before the replacement
vocabulary was chosen. A scrubber's output vocabulary is part of its attack
surface.

**C9 — the grader must not be the model under study (A11).** Case02 graded
`claude-opus-5`'s output with `claude-opus-5` after the intended alternative hit
a quota.

## Reporting

**C10 — every reported number must be emitted by a deposited script.** Three
review rounds found figures in the manuscript with no deposited source, including
one (15,295 bytes) that was simply invented.

**C11 — the amendment log is append-only and the paper must cite all of it.**
Case02 accumulated eighteen amendments across three adversarial review rounds
that verified 43, then 47, then 72 findings. Round three found the worst defect.
Budget for at least two review rounds *before* believing any result.

## What the prior cases established, so case03 need not re-litigate it

* FCDD costs more: 7/7 defects in case01, 7/7 in case02, median 2.26× (2.75× on
  primary-model spend). This is the only finding that has replicated.
* FCDD did not make repair cost more predictable on easy single-byte faults; the
  point estimate ran against the hypothesis in every unit and statistic tried.
* On such faults both methods converge on the identical program — but case02
  could not say whether that reflects the methods, because the treated arm held
  the answer (C1).
