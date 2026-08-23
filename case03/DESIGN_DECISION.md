# Case 03 — design selected: PORTGUARD

**2026-08-23.** Five designs were generated from deliberately different starting
angles and each scored by three independent judges on five axes. Scores are the
mean of the lens-scores each design received.

| design | can fail | oracle safety | measurability | feasibility | answers the claim | total |
|---|---|---|---|---|---|---|
| **PORTGUARD** (no seeding, differential oracle) | 4.7 | **5.0** | 4.7 | 3.3 | 4.3 | **22.0** |
| The Escape Rate | 4.7 | 3.7 | 4.3 | 3.0 | 4.3 | 20.0 |
| silent_repair | 3.7 | 3.7 | 4.3 | 3.3 | 4.3 | 19.3 |
| Silent Failure (contract-converts) | 3.7 | 3.0 | 4.7 | 2.7 | 3.7 | 18.0 |
| Silent Failure (search-behaviour) | 4.3 | 3.7 | 3.3 | 2.7 | 3.3 | 17.3 |

## Why PORTGUARD

**It makes A17 unrepresentable rather than guarded against.** Nothing is seeded,
so there is no pristine version, no sealed answer, and no artefact whose
accidental shipment hands one arm the solution. Difficulty is *generated* by a
frozen grammar, not injected.

**Cross-arm byte parity replaces the argument case02 lost.** Both workspaces are
bit-identical except `PROMPT.md`, asserted per cell. Case02's failure was
shipping two *different* packages and then arguing about their relative value
until round three found one of them contained the answer. Parity turns that
argument into an equality test. A judge put the consequence precisely: any leak
that survives is now necessarily *symmetric*, so it degrades the benchmark
visibly instead of inverting the confound silently.

**It tests the claim the method is actually sold on.** Cases 01 and 02 answered a
question nobody disputes — formal methods cost more — on a benchmark where both
arms scored 100%. PORTGUARD asks whether the premium buys fewer wrong-but-
plausible programs, on a pre-trade risk gate with fail-direction requirements
under degraded input, which is the FCDD skill's own stated home ground.

**The outcome has real variance and no judge in the loop.** Defect mass
μ = |{s : impl(s) ≠ oracle(s)}| / 3,136,000, enumerated exhaustively at
~50k states/s — 63 s per submission, 75 minutes for all 72. No sampling, no
fuzzer luck, no LLM grading.

**Case02's fatal condition is pre-registered with a name.** If the pooled CORRECT
rate leaves [0.10, 0.90] the study is declared **UNINFORMATIVE — a benchmark
failure, not a null on FCDD**. Case02 discovered its ceiling in the post-mortem;
case03 declares it in advance with a verdict attached.

**A co-primary gate closes the obvious gaming path.** FCDD could drive silent
failure to zero by refusing to ship, so H1 is supported only if Arm B's CORRECT
rate is also non-inferior to Arm A's within 10 points. "Converts silent failures
into loud ones" must be distinguished from "converts working programs into
non-working ones".

## What the losing designs contributed, and what killed them

The recurring fatal pattern is worth recording, because it is A17 wearing a
different coat: **three of the five designs shipped Arm B a runnable twin or
reference implementation of the same semantics the sealed oracle implements.**
That is the same leak one level up — semantic rather than byte-level — and two
judges found it independently. Grafted from the losers: the Escape Rate's
self-certification predicate, and silent_repair's admission assertions that make
difficulty a checked precondition rather than a hope.

## What this costs

**Comparability with cases 01 and 02.** Those measured repair; this measures
forward synthesis. The cost premium is no longer the same quantity and a null
here does not transfer backwards. The programme loses its longitudinal spine.
Judged worth paying, because the shared benchmark was the thing that made cases
01 and 02 unable to answer anything.

**A circularity risk the design names against itself.** A spec assembled by a
grammar from randomised clauses with a randomised precedence order manufactures
exactly the pedantic clause-interaction difficulty formalisation is best at. If
FCDD wins here, the honest reading may be "FCDD wins on machine-generated clause
interactions". That belongs in the abstract, not the threats section.

## Superseded from CONSTRAINTS.md

C1's mechanism changes. `tools/workspace_manifest_guard.py` was built against a
seeded design and remains useful as a backstop, but the primary control is now
`tools/parity_assert.py`: an equality test between the two arms' workspaces. It
is strictly stronger, because it needs no judgement about what a file is worth.
