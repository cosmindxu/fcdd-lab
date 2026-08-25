# Case 04 — pre-registration (DRAFT, pilot-gated): does formal expression + mechanical extraction reduce behavioural divergence?

**STATUS: DRAFT — NOT FROZEN.** Nothing here is executable until the pilot
gates in §9 pass and this file is committed with the frozen schedule, the
sealed corpus hash, and the pinned toolchain filled in. Every draft value is
marked `(pilot)` and every finalisation step is enumerated. Departures after
freeze are recorded as dated, append-only amendments, as case02's A1–A18 were.

## 1. Hypotheses

**H1 (primary, D12).** Building the chess engine through a formal
expression in Rocq mechanically extracted to Rust (Arm A) yields a *lower*
policy disagreement mass μ₂ — the submission's `choose` diverges from the
engine's own level-1 play on fewer policy positions — than writing the
same Rust crate directly (Arm B). Ground truth for the policy is the
engine's play (the only coherent definition of a clone's strategy); the
rules layer stays model-decided (D9) as the co-requisite: both arms must
also remain rules-correct, and the smoke set must pass.

**H0.** Defect mass is equal.

Direction is pre-specified; the test is **two-sided** — a result showing the
formal arm is *less* faithful is a real outcome and will be reported as such
(case02's own phrasing, which this design keeps).

**H2 (secondary, cost).** Cost level and cost dispersion per run, reported
with exact tests and no primary claim (cases 01/02 established FCDD costs
more in repair; this measures whether the premium persists in synthesis).

**H3 (secondary).** Rules-layer defect mass μ₁ (model referee, D9) —
the co-requisite gate, not the primary (D12).

**Quality tier (secondary, blinded).** Source-quality grading of the crates,
with the C15 style-leak plan. Under-powered by construction; reported with
intervals and no claim (case02 §5 language).

**Exploratory — Arm B model sweep (secondary, D7).** The control process is
additionally run on `deepseek/deepseek-v4-flash`, k = 3 runs, same task,
same workspace, same oracle budget, via the opencode runner. Reported in
its own section: per-run μ₁ and cost alongside the deepseek-pro Arm B
runs, descriptively and with the same exact tests, clearly labelled
exploratory — model sensitivity of the control arm, NOT part of H1. The
primary comparison remains both arms on `deepseek/deepseek-v4-pro` (C3).

## 2. Design

**Task (identical for both arms).** Produce a Rust crate `chess_clone`
implementing the frozen API (IFACE.md, shipped in the workspace):

```
chess_clone legal   --fen "<FEN>"     # legal moves, one per line: e2e4, a7a8q
chess_clone status  --fen "<FEN>"     # one of: play, white-mated, black-mated,
                                      #          stalemate, draw, flag-fall
chess_clone choose  --fen "<FEN>"     # chosen move, one line (policy layer)
```

The submission's job is to *clone the observable behaviour of the reference
engine*, quirks included: any FIDE divergence the engine exhibits is ground
truth (case01 documented that the engine has them). Responses must be
deterministic and must terminate within the frozen per-query timeouts
(60 s legal/status, 300 s choose (calibration-measured answers: ~5 ms)). Crashes, timeouts and
non-parseable output count as divergence for that query (fail-direction:
degraded input must not read as agreement — the FCDD skill's own rule,
applied to both arms).

**Arm A — FORMAL/EXTRACT.** Express the engine as a Rocq 9.1.1 development;
generate the Rust *exclusively* via `rocq-rust-extraction` 0.2.1. Gates,
checked mechanically per run:
1. the Rocq tree compiles (`rocq compile`, switch `coq-switch`),
2. zero `Admitted` / `admit` / run-added `Axiom` in the shipped tree,
3. the extraction runs and its output is deposited,
4. the crate builds and every Rust file outside the adapter hash-matches the
   deposited extractor output (hash-lock),
5. the adapter (hand-written glue: FEN parse, CLI, type conversion, printing)
   satisfies the frozen adapter rule: ≤ 200 non-comment lines (calibration measured 96–132),
   and none of a frozen list of behaviour tokens (`gen`, `legal`, `search`,
   `eval`, `alpha`, `beta`, `perft`, `mate`, `stalemate`, `castl`, `passant`,
   `promot`) occurs in it outside comments — a token hit is *flagged for
   adversarial review*, not auto-failed.
Proofs are **not required**: the treatment is the formal *expression* plus
mechanical extraction. Proofs attempted are recorded as quality-beyond-bar.
A run failing gates 1–4 has its process-violation reported; its treatment as
data follows §11.

**Arm B — DIRECT.** Write the crate directly in Rust. Process: ordinary
development plus review rounds. Arm B may not use Rocq or any extractor; the
transcript is grepped for `.v` files and Rocq invocations (C13).

**Parity.** Workspaces are byte-identical except `PROMPT.md`, asserted by
`case03/tools/parity_assert.py` at build time; `workspace_manifest_guard.py`
also runs with the sealed corpus and the pristine tape registered as sealed
material (C1). Both arms receive: PROMPT.md, IFACE.md, the oracle CLI, the
public smoke set (§4), the skeleton crate, and **`reference/Contract.lean`** —
case01's kernel-checked formal contract of the engine's rules and the S1–S4
strategy clauses, byte-identical in both workspaces (D6). It is a shared
informational input, not a treatment: Arm A uses it as the formal source for
its Rocq expression, Arm B as reference documentation for direct Rust. The
query cap (§3) remains the budget for everything the contract does not pin
down (eval weights, PST tables, move ordering, TT behaviour). Everything else
is environment.

**Model and effort.** Pinned model for both arms *and their subagents*,
fixed for the whole study, written in at freeze: **primary =
`deepseek/deepseek-v4-pro` for BOTH arms** (D8; any other split would
re-inherit case02's A13 model-mix confound), runner = `opencode run`.
Per-run check from the recorded session accounting that only the pinned
model appears; mismatch aborts the cell (C3).

**Replication and randomisation.** k = 5 independent runs per arm (10 runs;
`(pilot)` may adjust k by measured cost — fallback floor k = 4). One target,
no blocking factor: runs are the statistical units; the estimand is the
run-level distribution of μ₁. Run order is randomised across the 10-run
schedule under a committed seed, so service drift cannot align with arm.

## 3. The information-symmetry control: a capped oracle (D2)

The reference engine is available to both arms **only** through the oracle
CLI, which injects a FEN into the pristine tap (game's own tape loader,
fixed frame schedule — deterministic by construction) and returns the
observed behaviour for the requested layer. The pristine tap itself never
enters a workspace (C1).

**Cap.** Each run holds a query budget of `N_Q = 5,000` probes (calibration arms used 70 and 229; the cap stays generous).
The CLI counts every probe per run-id and refuses past the cap. The refusal,
the final count, and a per-query append-only log are written to the run's
ledger row. One probe = one (FEN, layer, level) oracle invocation.

Rationale: unlimited access degenerates into mass transcription (~5
probes/s measured — ~430k positions/day would be feasible), pushing both
arms to the ceiling (C2). A fixed shipped corpus with no live access was
rejected: corpus curation becomes an attackable design judgement. The cap
makes information scarce *and symmetric* — the formal arm's claimed
advantage is exactly generalisation from limited observations, and this is
the regime the experiment measures it in.

## 4. Hidden corpus and smoke set

**Ground truth is the MODEL (D9), not the engine.** The referee for every
scored position is the formal model — case01's kernel-checked contract
evaluated through its executable twin (`step1_contract/twin/hc91_twin.py`),
which replays the position's path and emits the legal move set and the
terminal status (including the contract's repetition semantics via the
twin's 16-bit key history). The Z80 engine is demoted to a cross-check:
its own answers are collected by replay, and positions where model and
engine disagree are **excluded from scoring and reported** as the
engine-bug inventory (a deliverable). Positions where they agree get
answers that are simultaneously model-derived and empirically confirmed;
positions the engine cannot judge (unjudgeable replays) take the model's
answer. The referee must pass the canonical perft battery (startpos d1–3,
Kiwipete d3, positions 3–6 d1–3) before it emits any answer — the gate is
code, in the sealing job.

The model's own provenance caveat, stated plainly: the contract was
transcribed from the engine (case01, "divergences flagged, not
normalised"), so it is a cleaner but implementation-derived specification;
its fidelity to *intent* is bounded by case01's bridge sampling and the
organic-findings record, not by any proof about the engine.

**Distribution.** Positions are sampled by `tools/corpus_gen.py` from random
chess playouts (python-chess 1.11.2, orchestrator-side only): game-phase
stratified — openings, middlegames, endgames — plus a heavy tail of positions
one ply before termination (mate/stalemate/draw adjacencies), where terminal
statuses concentrate. Seed committed; generator frozen before sampling.

**Hygiene (C16).** Engine-observed behaviours are double-probed; positions
whose engine observation is not self-consistent are excluded from the
cross-check and counted. Corpus paths are legality-filtered through
python-chess `legal_moves` (bare `push` does not validate — PILOT E7).

**Sizes (frozen):** rules layer 11,103 positions; policy layer 1,999
positions at level 1, restricted to Black-to-move, state=play positions with
self-consistent chosen moves.

**Sealing.** The sealed answer file (`ledger/sealed/answers.json`) carries
per position: the model referee's legal set + status, an agreement flag
(model+engine agree / referee-only / engine-unjudgeable), and the path for
reproducibility. It is written once, sha256'd, committed; the content never
enters any workspace and is readable only by the scorer
(`tools/score_case04.py`). The bug inventory (`bug_inventory.json`) is
reported with the study, not hidden.

**Public smoke set.** 50 positions with expected answers, disjoint from the
hidden corpus, shipped to both arms for harness wiring. Its answers are
model-referee answers (re-derived under D9), not engine observations.

## 5. Outcomes, estimators, tests — fixed here, not after seeing data

**Primary outcome μ₁.** For each corpus position, the submission's answers to
`legal` and `status` are compared against the MODEL referee's sealed answers:
- legal set equality on (from, to, promotion-kind) — order and flags ignored;
- status string equality.
Any mismatch makes the position a divergence. **μ₁ = divergent positions /
corpus size.** Move-level mass (summed symmetric differences of move sets /
summed oracle move counts) is reported secondarily — it is not the primary,
because one movegen defect would dominate it.

**Test.** Two-sided exact two-group permutation on per-run μ₁: all C(10,5) =
252 arm-label assignments enumerated, α = 0.05, attainable floor 2/252 =
0.0079 at k = 5 (0.0286 at k = 4). Estimated effect sizes reported with
Hodges-Lehmann-style median-shift intervals `(script: tools/analyse_case04.py)`.
μ is a proportion: unit-free, C4 satisfied. Cost dispersion uses scale-free
`sd(ln cost)`; cost level uses the same exact permutation on dollars (the
`modelUsage` total incl. subagents, cross-checked against `total_cost_usd` as
case02's A7 did) with a raw-token recomputation reported beside it.

**Co-primary completion gate (anti-gaming).** A run that does not deliver a
crate passing the smoke set within its budget scores μ₁ = 1 and is reported
as non-delivering (completion rate per arm is a stated outcome). H1 is
supported only if Arm A's completion is non-inferior within **one** run:
"formally expressed" must not mean "never ships". A submission that
refuses to answer is already maximally divergent; this gate closes the
subtler path of a formal arm that ships nothing at all.

**Multiplicity.** Four pre-registered outcomes (H1, H2, H3, quality tier),
tests specified here in advance, no correction applied — the case02 §5.5
position, restated: readers wanting a family-wise guarantee should discount
accordingly.

## 6. Uninformativeness gate (named in advance — C2)

If the pooled (both arms, all runs) PRIMARY outcome — policy
disagreement mass μ₂, D12 — lies outside `[0.02, 0.95]` (thresholds frozen
from the two calibration points 0.088 / 0.366, which span the interval),
the study is declared **UNINFORMATIVE — a benchmark failure,
not a finding about either method**: below 0.001 the task was too easy to
produce failures (case02's exact fatal condition); above 0.5 the task was
infeasible at this budget. The declaration is pre-committed and named.

## 7. Stopping rule

**No optional stopping.** All scheduled runs execute. No interim analysis of
μ₁ before the schedule completes. A run that dies for infrastructure reasons
is re-run at the same cell with the same tag; its partial cost is recorded
and excluded; every such event is logged. The driver detects and logs
schedule gaps automatically (C6), and sensitivity analyses select cells by
identity (A18).

## 8. Falsification

A permutation *p* ≥ 0.05, or the co-primary gate failing, means the claim
that formal expression reduces divergence is **not supported at this sample
size**, and that is what will be reported. As in case02, the design is
sensitive to large effects — no power analysis is claimed; the floor of
0.0079 says only that significance is *reachable*. The claim does not get a
second pass on a null (case02 §8, kept verbatim as policy).

## 9. Pilot gates — all must pass before this file freezes

- **P1 — oracle self-consistency.** ≥ 99.9% self-agreement on a 1,000-position
  sample per scorable layer (legal set, status, chosen move at level 1);
  self-inconsistent behaviours excluded under §4.
- **P2 — throughput.** Measured probes/s; corpus sizes and per-query timeouts
  set so that scoring all 10 runs takes hours, not days, and so that the
  slowest plausible extracted submission still fits the timeouts.
- **P3 — extraction spike.** A small Rocq chess model (board representation +
  movegen for at least two piece types) extracts via the pinned plugin, the
  resulting Rust builds in a fresh crate, and the adapter pattern (FEN in →
  extracted calls → moves out) matches the oracle on a handful of
  kings+knights positions. **If P3 fails, the design is revised before any
  run** — the toolchain risk must not be the experiment.
- **P4 — calibration runs.** One time-boxed pilot run per arm (excluded from
  inference, as case02's pilots were). They calibrate: k, N_Q, adapter line
  cap, timeout values, and the §6 thresholds.
- **P5 — freeze artefacts (COMPLETED 2026-08-25).** Corpus sampled + sealed
  (answers.json sha256 `b10284674a983d7b78e0146455822c76eacadf4c78869028d95d981fc72a84d6`).
  Analysis script dry-run against the two calibration cells (C5) — done, see
  ledger/analysis_dryrun.txt. Schedule: seed 20260807, 13 cells
  (5 A + 5 B + 3 B-flash sweep), ledger/schedule.json. Pins: model
  `deepseek/deepseek-v4-pro` primary / `deepseek/deepseek-v4-flash` sweep
  (runner opencode; C3 verified per run); hc91emu rebuild sha256
  `97ee7d4fdeda155d29846c8510b62035af5dbfd4bf33512114f9b5b07fb8cc7b`;
  PROMPT hashes armA `aefb2e7c…f092c05`, armB `25ba1656…d9714f22`.

## 10. Cost accounting

Per-run `modelUsage` totals (incl. subagents) in dollars primary, raw tokens
alongside; pilot costs reported separately from scored-run costs. Upfront
tooling costs (this pilot phase) are not attributed to either arm.

## 11. Exclusions

A run whose gate verdict cannot be computed is excluded and reported, not
silently dropped (case02 §7). A run whose process conformance fails (C13) is
excluded and reported as a process violation. No cell may be excluded for
being an outlier.

## 12. Amendments and review

Append-only, dated amendments. The manuscript gets **≥ 2 adversarial review
rounds** before any claim is believed (C11), with the review lenses and
verified-finding counts recorded as case02 did. Every reported number is
emitted by a deposited script (C10).
