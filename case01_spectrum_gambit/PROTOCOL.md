# PROTOCOL — case01 Spectrum Gambit token-cost study  [DRAFT — not yet frozen]

Status: **DRAFT** pending the operator's answers in §Decisions. When frozen,
this file is committed and its commit hash is the pre-registration mark;
after that, changes require a dated amendment note, never a silent edit.

## Hypothesis under test

H1: For single-bug fixes at an equivalent quality gate, typical dev + code
review costs fewer tokens per bug than FCDD (which pays a large upfront
contract cost), but FCDD's marginal per-bug cost drops once the contract
exists — there may be a crossover at some bug count N.
H0: No reliable difference at this sample size. (Also possible: FCDD wins even
marginally, because the contract localizes faults faster than review rounds.)

We measure; we do not assume. Quality-beyond-bar is recorded so neither method
is strawmanned.

## Arms (operational definitions)

**Arm A — typical dev + review.** Fresh session per bug. Prompt pack: the bug
report + repo access + "fix it; add/adjust tests; then a code-review round by
a reviewer agent; address findings; stop when the gate passes." Reviewer =
same model, fresh context. No formal methods vocabulary in the prompt.

**Arm B — FCDD.** Fresh session per bug, with the `formal-contract-dev` skill
and the step-1 contract available. Prompt pack: the same bug report + "work
per FCDD: locate the violated clause (or extend the contract), fix, prove /
bridge, attack round; stop when the gate passes." Attack reviewers = same
model as Arm A's reviewer.

**Step 1 (Arm B's upfront phase, measured alone).** Express the chess game +
implemented strategies as a formal contract per the FCDD skill's Beat 1
(+ twin/bridge to the depth decided in §Decisions D4).

## Decisions (filled from operator answers — PENDING)

- **D1 Bug surface**: PENDING (Z80 engine `chess.asm` | Rust port vehicle |
  full stack incl. JS chess semantics)
- **D2 Bug-set origin**: PENDING (seeded sealed mutations | organic discovery |
  operator's known-bug list | seeded+organic) — note: issue tracker is empty.
- **D3 Headline token metric**: PENDING (cost-weighted total | output-only |
  no single headline). All four raw counters are logged regardless.
- **D4 Contract depth (step 1)**: PENDING (layered rules-core + strategy
  properties | fully determinized incl. exact eval/search | bug-adjacent
  minimal)
- **D5 Arm model/effort**: default = same model + effort both arms (chosen at
  launch, logged). PENDING confirmation.

## Equivalence gate (per bug, pre-registered before arms run)

1. **Acceptance test(s)** written from the bug's ground truth (seeded key or
   report), runnable headlessly (emulator harness / node tests / devserver).
2. **Regression**: the repo's existing checks stay green (`verify.mjs`,
   `test_movelog.mjs`, `make test` in hc91emu, per D1 scope).
3. **Blinded rubric review**: a grader agent (fresh context, not told which arm
   produced which diff) scores both fixes on correctness risk, clarity,
   test quality. Gate = acceptance + regression pass AND rubric ≥ threshold
   set at freeze time. Rubric ties do NOT block; they're reported.
4. An arm that cannot reach the gate within a per-bug token budget cap
   (set at freeze) is recorded as DNF at the cap — a result, not an exclusion.

## Measurement

- Unit of attribution = session / headless run; lanes per CONTEXT.md.
- `tools/tokencount.py` sums transcript usage (dedup by message id) or
  headless result JSON; rows appended to `ledger/runs.csv`.
- Counted: input, cache-write, cache-read, output per model. Headline per D3.
- The orchestrator's own tokens = lane `meta`, reported but outside both arms.
- Seeding and grading tokens are their own lanes (method-neutral overhead).

## Threats to validity (named up front)

- **n is small**; k=1 per bug per arm initially — replicate before believing
  gaps within noise. Model nondeterminism is real.
- **Operator contamination**: the orchestrator sees both arms' outputs over
  time. Mitigation: scripted prompt packs, sealed keys, blinded grading,
  fresh contexts per unit.
- **Grading bias toward Arm B**: the contract must not be the rubric. Graders
  judge against the pre-registered gate artifacts only; the contract may be
  consulted only after both arms froze their fixes, and any use is logged.
- **Author asymmetry**: the engine was written by Fable; if arms also run on
  Fable, both arms share whatever self-model advantage exists (symmetric).
- **Fable pricing** unknown in the local table → cost-weighted headline needs
  a price entry or falls back to raw counters (see tokencount.py PRICES).

## Report skeleton (end state)

Upfront cost (step 1) · per-bug tokens per arm (table + medians) ·
crossover N = step1 / (perBugA − perBugB) if perBugB < perBugA ·
gate outcomes + DNFs · quality-beyond-bar notes · threats recap.
