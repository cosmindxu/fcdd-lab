# PROTOCOL — case01 Spectrum Gambit token-cost study  [FROZEN v1.0 — 2026-07-29]

Status: **FROZEN v1.0** (operator answered the four design questions
2026-07-29; the commit adding this line is the pre-registration mark).
Changes after freeze require a dated amendment note here, never a silent
edit. Numeric freeze constants (§Gate, §Decisions) may be amended pre-run
the same way.

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

## Decisions (operator, 2026-07-29)

- **D1 Bug surface = the Z80 engine** (`hc91emu/chess/chess.asm`, 2,268 L,
  lives in `/media/sf_Projects/HC91_emulator/chess/`). Fixes are written in
  Z80 asm; behavior is exercised through the hc91emu emulator headlessly
  (and the spectrum-gambit WASM harness where useful). The JS/backend layers
  are OUT of headline scope — anything found there goes to the bonus lane.
- **D2 Bug set = seeded core + organic bonus.** **N = 7** seeded single-fault
  variants of `chess.asm`, one bug per variant, classes spanning:
  movegen/legality (castling rights / through-check, en passant, promotion),
  check/mate/stalemate detection, search (TT key/depth bound, quiescence),
  eval (sign/symmetry), draw accounting (50-move / repetition). The seeding
  lane (an independent agent, its own token lane) must: inject the fault,
  **verify it manifests** via the emulator (a reproducible symptom line),
  write a **symptom-level bug report** (no location or cause hints), deliver
  each variant as a tree **without git history**, and write the answer key
  (locations + patches + intended class) to `sealed/answer_key.json` — the
  ledger records only its sha256; the orchestrator never reads the key or
  the seeded diffs until grading. Real bugs an arm (or step 1) uncovers in
  the pristine engine are logged in the **organic bonus lane**, outside the
  headline A/B. Contamination controls: arms run **offline** (no web tools),
  are forbidden to fetch the public repos, and receive the variant tarball
  as "the current dev state".
- **D3 Metric = cost-weighted USD total** over all four counters, per-model
  prices at the 1-hour cache-write rate; raw counters always reported
  alongside. Frozen prices (USD/MTok, in / cache-wr(1h) / cache-rd / out):
  **Fable 5 = 10 / 20 / 1 / 50; Opus 4.8 = 5 / 10 / 0.50 / 25** (Opus
  4.5–4.8 share the rate). Fast-mode, batch, and US-1.1x multipliers are out
  of scope (not used). Opus 5 unpriced → raw-only if it ever appears.
- **D4 Contract depth = layered.** Step 1 produces: a kernel spec of the
  full rule set **as the engine implements it** (movegen, legality,
  check/mate/stalemate, castling/EP/promotion, the draw rules actually
  present) + the strategy layer as PROPERTIES (always-returns-a-legal-move,
  search termination within budget, eval symmetry where intended, alpha-beta
  ≡ minimax at small depth via the twin), per FCDD Beats 1–3 with the
  emulator as execution oracle for conformance sampling. **Honesty rule:**
  where the 8-bit engine deliberately diverges from FIDE (e.g. promotion
  choice, threefold tracking), the contract records the engine's actual rule
  and FLAGS the divergence as a finding (organic lane) — it does not
  silently normalize the spec to FIDE.
- **D5 Arms config (default, operator may veto): same model + same effort
  for both arms; launch default = Fable 5 / effort high.** Logged per run.

## Equivalence gate (per bug, pre-registered before arms run)

1. **Acceptance test(s)** written from the bug's ground truth (seeded key or
   report), runnable headlessly (emulator harness / node tests / devserver).
2. **Regression**: the repo's existing checks stay green (`verify.mjs`,
   `test_movelog.mjs`, `make test` in hc91emu, per D1 scope).
3. **Blinded rubric review**: a grader agent (fresh context, not told which arm
   produced which diff; label order alternates deterministically by bug
   parity) scores both fixes 1–5 on three axes — correctness risk, clarity /
   maintainability, test quality. **Gate threshold: no axis below 3.**
   Rubric ties do NOT block; they're reported.
4. **Per-bug per-arm budget cap: $40 cost-weighted.** An arm that cannot
   reach the gate within the cap is recorded as **DNF at cap** — a result,
   not an exclusion.
5. Replication rule: k=1 first pass; any bug where the arms' cost gap is
   < 30% of the larger cost is re-run (k=2–3) before a winner is claimed.

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
- **Prices are a dated snapshot** (2026-07-29, third-party pricing pages; the
  session runs on a subscription, not metered API). The $-headline is a
  list-price-weighted USAGE index, not an actual bill — raw counters remain
  the ground truth if prices move.

## Amendments

- **2026-07-29 A1 (factual correction, pre-run):** D1 understated the engine.
  The source is `chess.asm` (2,268 L) **plus six includes** — `engine.inc`
  (2,489), `movegen.inc` (1,403), `perft.inc` (578), `tt.inc` (309),
  `zobrist.inc` (230), `pieces.inc` (66) — **7,343 lines total**, built by
  `chess/Makefile` (pasmo → `../tools/zxtap.py` → `chess.tap`). No decision
  changes; seeded faults may live in any of these files; the engine's own
  perft facility is fair game for bridges.
- **2026-07-29 A3 (operator directive, pre-run):** ALL measured runs in this
  case (step 1, seeding, both arms, grading) use **the Opus model at effort
  max**, superseding D5's "Fable 5 / high" default (operator instruction
  during the first launch attempt; a ~2-minute Fable step-1 launch was killed
  before it wrote anything — killed runs emit no result JSON, so its small
  cost is unrecorded; noted in TOKEN_LEDGER). Same-model-both-arms parity
  unchanged. Opus 4.8 is priced in the table, so the D3 cost headline stays
  fully computable. Launch-mechanics note: orchestrator-side launch commands
  are subject to the interactive auto-mode classifier (two blocks occurred —
  meta lane only, before any measured run started); measured lanes run
  headless with an explicit `--allowedTools` grant, so no classifier sits
  inside their loop — **measured lanes are unpolluted**.
- **2026-07-29 A2 (verification note, pre-run):** lane isolation verified
  empirically — a fresh `claude --model fable --effort high -p` run with cwd
  inside the case folder reports NONE for visible CLAUDE.md / user-memory
  context (`ledger/raw/smoke_isolation.json`; $0.34, meta lane). `--effort`
  exists headless, so D5 is fully applicable; the CLI's own
  `total_cost_usd` is recorded alongside tokencount's computation.

## Report skeleton (end state)

Upfront cost (step 1) · per-bug tokens per arm (table + medians) ·
crossover N = step1 / (perBugA − perBugB) if perBugB < perBugA ·
gate outcomes + DNFs · quality-beyond-bar notes · threats recap.
