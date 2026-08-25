# Case 04 — design decision record: Coq→Rust extraction vs direct Rust

**2026-08-24, operator decisions taken interactively.** This file records what was
decided, what was rejected, and why. The protocol candidate lives in
`PREREGISTRATION.md` and is **not frozen** — it freezes only after the pilot
gates in its §9 pass, per constraint C5.

## The claim under test

Cases 01 and 02 measured **repair**: a fault was injected, then fixed. The
operator's criticism, accepted: that design cannot see FCDD's actual claim,
which is **prevention** — a target expressed formally *before* coding should
produce fewer defects in the first place. Case 04 is therefore a **forward
synthesis** experiment, not a bug-injection one:

> Build the same chess engine anew, in Rust, once via a formal expression of
> the target (Rocq model, mechanically extracted to Rust) and once by direct
> development, and count behavioral divergences from the reference engine.

Keeping the same target semantics (the Spectrum Gambit Z80 engine) preserves
longitudinal continuity with cases 01/02 while changing what is measured.

## Decisions

**D1 — Arm A is Coq→Rust, not OCaml→Rust.** The initial proposal said "OCaml
with automatically generated code"; corrected by the operator: the formal
expression language is **Rocq/Coq**, and the generator is the AU-COBRA
extraction plugin (`rocq-rust-extraction` 0.2.1, MetaRocq 1.5.1, Rocq 9.1.1 —
verified installed in the `coq-switch` opam switch on this host, source at
`~/src/coq-rust-extraction`, public on GitHub). This is a stronger operationalisation
of the hypothesis than OCaml: the expression medium is a proof assistant, and
the code generation is a real mechanical extractor, not a convention.

**D2 — Information symmetry is achieved by equality, not denial (capped
symmetric oracle queries).** Case02's fatal A17 was asymmetric access to the
answer. Case 04 ships **both** arms the same oracle CLI against the pristine
Z80 engine (FEN injection via the case02 characterisation-suite machinery) with
a hard, mechanically enforced per-run query cap. The cap keeps information
scarce so the task is *generalisation from limited observations* — exactly the
regime where a prior formal expression is claimed to help. Unlimited access was
rejected: at the measured ~5 positions/s, mass transcription probing is feasible
and would push both arms to the ceiling (C2). A fixed shipped corpus with no
live access was rejected: corpus curation becomes an attackable design
judgement, and the scenario is thinner than any real cloning task.

**D3 — Scored behaviour: rules layer primary, policy layer secondary.**
Layer 1 (RULES): legal move set + terminal status per injected position —
well-defined, achievable, discriminating. Layer 2 (POLICY): chosen move at fixed
engine settings — reported separately, because exact search/eval cloning may be
near-impossible at budget and would saturate both arms. UI/screen behaviour is
out of scope. Oracle self-consistency per layer is a pilot gate (P1); any
behaviour the oracle does not reproduce on itself is excluded before scoring.

**D4 — New case04, pilot first.** Case03/PORTGUARD remains selected on its own
track (its grammar-generated semantics has no reference implementation at all —
a different answer to A17). Case04 runs a pilot phase (oracle determinism,
throughput, extraction spike, one excluded pilot run per arm for cost
calibration), and only then freezes the pre-registration, the corpus, and the
analysis script. Target scale k=5 per arm (10 runs; exact two-group permutation
floor 2/C(10,5) = 0.0079), adjusted to pilot-measured cost; k=4 (floor 0.0286)
is the fallback.

**D5 — Deliverable parity: both arms ship a Rust crate with the same API.**
Same artefact category, same probe CLI contract — the scorer cannot tell the
arms apart mechanically (C7 satisfied at the level that matters: the scored
behaviour). Named residual: extracted Rust *looks* generated, so blinded source
grading carries a style-leak risk; the blinding audit + manipulation check of
case02 are pre-registered for that tier, and if the audit fails the tier is
reported as unblinded rather than trusted.

**D6 — the case01 Lean contract is a symmetric shared reference; the
Lean→Rocq import tool is rejected.** The operator proposed reusing the case01
contract (`step1_contract/spec/Contract.lean`: 1,271 lines, Lean 4 core only,
no sorry/native_decide, 95 kernel-proved theorems, empty axiom profile) via
`rocq-community/rocq-lean-import`. Investigated and rejected as the Arm A
mechanism:

1. The tool is an experimental alpha, self-described as "useful to compare how
   Lean and Rocq work but probably not much beyond that".
2. It needs `lean4export` export files — a third experimental toolchain step.
3. **It breaks extraction by design** — Prop→SProp, custom recursors
   (`_indl`/`_recl`), README verbatim: "this translation breaks extraction".
   Arm A's path ends in MetaRocq typed erasure → Rust, which needs clean
   computational content.
4. Importing a pre-translated contract would also be an artefact shipped to
   Arm A only — the case01/02 confound wearing a new coat.

What IS adopted: **both workspaces ship `reference/Contract.lean`,
byte-identical, asserted by the parity check.** It is the formal description
of the engine's rules plus the S1–S4 strategy clauses. Both arms may read it
identically: Arm A uses it as the formal source for the Rocq executable model
(its own transcription work, hash-locked); Arm B uses it as reference
documentation while writing Rust directly. The pristine-derived-artefact
confound is spent symmetrically by equality (the case03 principle), and the
query cap remains the budget for everything the contract does NOT pin down —
eval weights, PST tables, move ordering, TT behaviour, i.e. the policy layer.

The honest consequence for the claim: the arm difference is now purely
*process* — formal expression + mechanical extraction versus direct coding —
over identical information. That is a stronger, cleaner test of the
hypothesis, not a weaker one.

**D7 — exploratory Arm B model sweep (deepseek), pre-registered as secondary.**
Operator decision 2026-08-24, REVISED same day: the control arm is
additionally run on **`deepseek/deepseek-v4-flash`** (k = 3, via the
opencode CLI — the only deepseek runner on this machine). The sweep is
reported in its own section, not part of H1. The schedule includes the
sweep cells in the same randomised order.

**D8 — primary model: deepseek-v4-pro for BOTH arms (claude exits the
design).** Operator decision 2026-08-24: Arm A runs on
`deepseek/deepseek-v4-pro`; by C3 the primary Arm B matches on the same
model — any other split would re-inherit case02's A13 model-mix confound.
Consequences recorded: (1) the completed claude-opus-5 Arm B calibration
($53.41, 50/50 smoke) is retained as a cross-model data point, excluded
from inference; (2) the claude credit-restart watcher was killed — the
claude calibration of Arm A is abandoned; (3) P4 calibration re-runs on
deepseek-v4-pro for both arms; (4) the scored-phase runner becomes
`opencode run` (claude CLI no longer used); the C3 model-pin check is
adapted to opencode's session accounting at P5.

**D10 — prior-art reference: Acher's agentic chess engines; referee validated by perft.**
Operator direction 2026-08-25: explored
`blog.mathieuacher.com/FromScratchChessEnginesPolyglot/` as a starting page.
Two repositories cloned orchestrator-side ONLY (never shipped to arms):
`acherm/agentic-chessengine-rocq-cc` (ChessRocq — a complete 1,167-line pure
Rocq engine: Types/Board/Attacks/MoveGen/Eval/Search, bitboards on Uint63,
legal movegen + mate/stalemate, extracted to OCaml, built by Claude Code)
and `acherm/agentic-chessengine-lean-codex` (a Lean 4 engine with perft
executable + UCI). Consequences recorded:
(1) **Feasibility datum**: an agent of the arms' class produced a complete
Rocq chess rules+search engine in 1,167 lines — Arm A's task is comfortably
inside the envelope; (2) **our spike's design stands**: ChessRocq extracts
Uint63→OCaml int63; our Rust plugin path uses Z→i64 remaps (validated in the
spike) — the architecture (module separation, flag encoding) is the reusable
lesson, not the representation; (3) **referee validation**: the D9 model
referee (the case01 twin) was re-run through the canonical perft battery —
startpos d1–3, Kiwipete d3, positions 3–6 d1–3 — all match the standard
numbers, on top of case01 b4's exhaustive twin-vs-engine perft cross-check
(410,082 leaves); the seal job now gates on this battery before deciding any
answer. Contamination note: the arms are offline (no web tools) and these
repos are not shipped; model-training priors about them are a symmetric
residual, as for every public chess engine.

**D9 — ground truth is the MODEL, not the engine.** Operator decision
2026-08-25: "correct" is defined by what the formal model describes, not
by what the imperfect Z80 engine does (case01's own contract step found 10
organic engine bugs, 2 HIGH — a clone faithful to the engine would be
scored for reproducing bugs). Mechanics, all decided by the operator:
(1) the referee is the case01 contract evaluated through its executable
twin; (2) the engine demotes to a cross-check — positions where model and
engine disagree are excluded from scoring and reported as the engine-bug
inventory (a deliverable); positions where they agree get answers that are
both model-derived and empirically confirmed; engine-unjudgeable positions
take the model's answer; (3) the policy layer leaves the primary — the
model specifies search properties, not the concrete evaluation, so
"correct chosen move" is undefined; chosen-move-vs-engine survives only as
a clearly labelled exploratory secondary; (4) the arms keep capped engine
probing as a debugging aid. The model's provenance caveat is stated in the
pre-registration: the contract was transcribed from the engine, so it is
cleaner but implementation-derived; its fidelity to intent is bounded by
case01's bridge sampling, not by proof. Referee validation: canonical
perft battery (startpos d1-3, Kiwipete d3, positions 3-6) passed 2026-08-25
on top of case01 b4's 410,082-leaf twin-vs-engine cross-check; the battery
is now a gate inside the sealing job.

**D11 — the shared formal spec is WITHDRAWN (D6 reversed); the gate fired.**
Operator decision 2026-08-25, after the calibration crates scored against
the model referee: both arms at μ₁ = 0 (two threefold-repetition status
divergences each, which are a FEN-only-interface impossibility — a
scoring-spec bug fixed by flagging repetition draws and skipping their
status). The pre-registered uninformativeness gate fired decisively:
shipping the kernel-checked contract to BOTH arms reduced the rules layer
to near-free transcription and left no variance to measure. The study
therefore returns to the hypothesis's actual shape: **neither arm receives
a formal specification.** Both get the natural-language task, the smoke
set, and the capped probing budget; Arm A's treatment is doing the formal
expression itself (its Rocq model is its own discovery work), Arm B goes
direct. Ground truth stays model-decided (D9 — the referee is
orchestrator-side only). Consequences: calibration re-runs (cheap: ~$5
total so far); informativeness re-checked before any scored run; the
threefold-repetition status exclusion is part of the seal.

**D12 — POLICY BECOMES THE PRIMARY.** Operator decision 2026-08-25,
after D11's contract-free calibration ALSO scored μ₁ = 0 for both arms
(53 vs 237 probes; the probe→differential-test→self-review loop converges
to perfect rules at this model's capability — the benchmark's rules layer
cannot discriminate, formally expressed or not). The primary outcome is
now **policy agreement**: the submission's `choose` vs the ENGINE'S own
level-1 moves on the 2,000-position policy subset. Ground truth for the
policy is the engine's play — the only coherent meaning of "which move
should a clone of THIS engine play"; the user's correctness principle is
untouched because the RULES remain model-decided (D9) as the co-requisite
gate. Reverse-engineering the engine's evaluation + search from probes is
genuinely hard, so variance should return. Consequences: scorer and
analysis reworked (primary μ₂); sealed answers carry the policy section;
PROMPTs rewritten to make `choose` the scored outcome; one further
calibration pair (policy task) runs before the freeze to set the μ₂
uninformativeness thresholds.

## What this design inherits mechanically

- `case03/tools/parity_assert.py` — cross-arm workspace byte parity except
  `PROMPT.md` (the primary A17 control).
- `case03/tools/workspace_manifest_guard.py` — manifest + sealed-hash backstop;
  the hidden scoring corpus is registered as sealed material.
- Case02's runner lessons: model pinned for subagents with per-run `modelUsage`
  assertion (C3), automatic schedule-gap logging (C6), analysis frozen only
  after a dry-run against a real completed cell (C5), estimator invariance
  checked before freezing (C4 — dispersion statistic here is `sd(ln cost)`,
  scale-free by construction; the primary outcome μ is a proportion).

## The honest scope of any result

The oracle is *a specific program's* behaviour, quirks included (case01
documented this engine's divergences from FIDE). The claim tested is therefore:
**formal expression reduces behavioural divergence when cloning a reference** —
which generalises to specification-conformance tasks, not to green-field
specification writing. A null here does not transfer back to repair (case02's
domain), and case02's null does not transfer forward to here.
