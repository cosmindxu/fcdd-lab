# Case 04 — PILOT log (append-only)

Dated empirical findings. Nothing here changes the pre-registration silently;
design consequences are recorded here and mirrored into the docs with a
reference to the dated entry.

---

## 2026-08-24 — oracle mechanics settled (oracle_cli.py v2)

**E1 — FEN injection never populates the ply-0 move buffer.** Two-player-mode
load of the start position: `genCount = 0`. Normal-mode load (White to move):
also 0. A 'h'-style key after load: still 0. The engine runs `updateTerminal`
(which fills the buffer at `0x6000` / count `0xE0A0`) only after a **completed
move**, never at load (consistent with case01 bridge/emu.py's comment that the
buffer is only meaningful when parked in `humanMove`).

**E2 — chosen-move probe is deterministic.** Normal-mode injection of a
Black-to-move position; engine thinks at the level typed before the load; move
read from the move-log tail. Repeated twice at levels 1, 2 and 3 after 1.e4:
all six runs returned `b8c6`.

**E3 — playout replay works.** Two-player load + scripted path of moves →
after the last move the buffer holds the final position's legal list:
`genCount = 20` after 1.e4 (Black) and `29` after 1.e4 e5 (White). The engine's
decoded FEN matches python-chess **exactly**, including castling rights,
en-passant square, halfmove and fullmove clocks (verified on a path containing
both castlings: `rnbq1rk1/... w - - 6 5`).

**E4 — takeback does NOT help.** After e2e4 then `z`, the board returns to the
start position but the buffer stays stale (holds Black's post-1.e4 list).
Takeback does not re-run `updateTerminal`.

**E5 — status by injection is side-dependent.** Two-player injection of a
checkmate position reads `gameState = play` (status-blind). **Normal-mode**
injection of the same position (Black to move, already mated) reads
`black-mated` correctly — the engine's own terminal check runs when it is
activated on its turn. Consequence: `choose` probes get the terminal status of
the injected position for free; `legal`/`status` probes use replay.

**E6 — promotion mechanics.** The engine prompts "Q=Queen R B N" (hardware
rows `0xFBFE` bit0/bit3, `0x7FFE` bit4/bit3 — read from `promptPromo` in
chess.asm). The piece key must arrive in its **own frame slot** after the
move's ENTER has settled; in the shared slot it is eaten as a game key
(lowercase `n` = new game, which reset the board). With its own slot, the
promotion replay works and the engine FEN matches python-chess exactly
(`...g7h8q` path: `rnbqkbnQ/pppppp2/... b KQq - 0 5`, castling rights updated).

**E7 — the engine correctly rejects illegal scripted moves; python-chess's
bare `push()` does not validate legality.** A path containing `d3c2` while the
king was in check was rejected with "Illegal move" — the engine's own legal
list matched python-chess's `legal_moves` (king-only). Corpus and probe paths
must therefore be filtered through `move in board.legal_moves`, never bare
`push`.

**E8 — ply-0 is unobservable for the legal layer.** The buffer is filled only
after a move, and no move leads back to the start position, so the start
position's own legal set cannot be observed by replay. **Corpus rule (frozen):
the corpus excludes the ply-0 start position.** All other corpus positions are
reached by paths of length ≥ 1. (Status of the start position is trivially
`play` and is not needed.)

**E9 — auto-path is a convenience with known limits.** BFS from the start
position with a 300k-node/14-ply cap finds shallow targets (1–3 plies in
milliseconds) but cannot reach 7-ply targets (scholar's-mate FEN) — branching
factor ~20–30. Arms are expected to supply `--path` for anything deep; the
cap is documented in the CLI help.

**Design consequences recorded:** legal/status probes are replay-based with a
target-FEN equality assertion (board part must match python-chess exactly,
else UNJUDGEABLE); promotions type their piece key in a dedicated frame slot;
the corpus excludes ply-0 and filters all paths through `legal_moves`; the
scoring identity is (from, to, promo) with promo from `flag >> 4`.

## 2026-08-24 — Lean→Rocq import route investigated and rejected (D6)

The operator proposed reusing the case01 Lean contract via
`rocq-community/rocq-lean-import`. Findings from the repository README and
local toolchain check (Lean 4.32.2 via elan is installed; the contract is Lean
4 core only, 1,271 lines, 95 theorems, no sorry/native_decide — the right
profile for a translation tool):

1. The plugin is an **experimental alpha** ("useful to compare how Lean and
   Rocq work but probably not much beyond that"); 36 stars, LGPL-2.1.
2. It consumes `lean4export` export files — a third experimental step.
3. **It breaks extraction by design**: Prop→SProp, custom recursors
   (`_indl`/`_recl`), README verbatim "this translation breaks extraction".
   The case04 Arm A path ends in MetaRocq typed erasure → Rust, which needs
   clean computational content. Chaining alpha→alpha with extraction broken
   at the seam is not a viable mechanism for a $2k+ experiment.
4. A pre-translated contract would also be an Arm-A-only artefact — the
   case01 §3.2 / case02 A17 confound wearing a new coat.

**Adopted instead (D6):** `reference/Contract.lean` shipped byte-identical to
BOTH arms as a shared informational input; Arm A transcribes it into its Rocq
executable model (its own work, hash-locked), Arm B reads it as reference
documentation for direct Rust. Symmetry by equality; the query cap stays the
budget for the policy-layer internals the contract does not pin down.

## 2026-08-24 — harness rebuild: MAX_TYPE_OPTS raised (environment pin C12)

`hc91emu` caps `--type` options at 32, which bounds replay paths at ~28 moves
(the pre-`updateTerminal` history is broken if a path is chunked into separate
emulator runs, because the engine's threefold detection depends on its own
gameKeys history — chunking would silently change draw verdicts on deep
positions). The cap is therefore raised to **2048** in the case01 harness copy
(`arms/harness/src/main.c`, single line) and the emulator rebuilt. Only the
CLI option-count cap changed; `z80.c` and the frame scheduling semantics are
untouched, so replay determinism is unaffected. **The harness build is now a
pinned toolchain item (C12)** — the rebuilt binary's sha256 must be recorded
in the frozen pre-registration. (Case01/02 re-runs on this harness are
unaffected: the code path for ≤32 options is identical.)

## 2026-08-24 — deep-path replay solved: chunked .sna replay with clock patches

The engine's clock (`INITCLK equ 15000` = 5:00 per side at 50 Hz) made
single-run replays die by flag-fall at ~28–34 plies with key-safe GAP=900;
smaller GAPs drop keystrokes on slower positions (measured: 150 desyncs at
move 7, 250 at 23–55 moves). The solution, implemented in `oracle_cli.py`:

- **Chunked replay**: paths are split into ≤20-ply segments; each segment
  boots the previous segment's `.sna` with both clock words (`0xE147`,
  `0xE149`) patched back to 15000. All other RAM — including the engine's
  repetition history (`gameKeys`) — survives the boundary, so threefold
  statuses on deep positions are computed against the full game history,
  not a truncated one. The engine's `resetGameState` (hmLoad path) resets
  clocks+history, which is why `.sna` chaining is used instead of re-loading
  position blocks.
- 20 plies/chunk leaves ~2× clock margin (10 moves per side ≈ 10.4k frames).
- Cursor tracking carries across chunks; promotion moves and their piece key
  stay within one chunk (the prompt is transient).
- Measured: 98/130/142/144-ply paths land fully with engine FEN ==
  python-chess FEN exactly (board+side+castling).

**Judicability check narrowed**: the FEN equality check now compares
board+side+castling only. The engine leaves a stale en-passant square where
python-chess clears it; that staleness is engine behaviour a clone must
replicate (it can feed the engine's own ep-move generation), not an
injection failure.

**P1 smoke (20 deep entries): 20/20 self-consistent, 0 unjudgeable.** The
oracle reproduces its own behaviour exactly across independent emulator
runs. Throughput ~0.12 probes/s single-core (≈8.5 s per probe at avg ply
~50); the full 10k-corpus double-probe would be ~47 core-hours ≈ 3 h on 16
cores — scoring must be parallelised (P2).

**P3 — extraction spike PASSED.** End-to-end Rocq→Rust pipeline validated:

1. `spike.v`: Rocq 9.1.1 source — `Z` squares (0x88), `color`/`piece`
   inductives, `Record At` board entries, list board, knight+king movegen.
2. Plugin namespace in the opam 0.2.1 install is `TypedExtraction.Plugin`
   (repo name `RustExtraction`); `Redirect "spike.rs" Rust Extract spikeGen.`
   emits `spike.rs.out` (load paths: `-Q .../TypedExtraction -Q MetaRocq
   -Q Equations`).
3. **Post-extraction step (frozen, documented):** strip `Debug:` lines and
   the five `#![allow(...)]` header lines (rustc ≥1.97 rejects inner
   attributes in `include!` expansions; the plugin's own scripts already
   sed its output).
4. Adapter pattern: `include!("extracted.rs")` at the crate root (inner
   attrs legal at file top; extracted file stays byte-identical =
   hash-lock; privacy moot); `bumpalo` dependency; extracted list is
   `List<&Spike_At>` (records extract as references).
5. Validated against python-chess pseudo-legal moves on 8 kings+knights
   positions (captures, own-piece blocking, black to move, edges): **8/8
   exact agreement**, including the case that exposed the bug below.

**Findings that would have been expensive mid-run (the spike earned its
keep):**

- **`at` is a Rocq keyword** — the board-entry record is named `At`.
- **My suffix bug, not the plugin**: first `genMoves` passed each recursion
  level's local `b` (the suffix from the scan point) to `moves_for`, so
  pieces scanned late saw a truncated board (own-king captures leaked, order-
  dependent). Fixed with a full-board accumulator. Symptom masked twice by
  a stale `extracted.rs` during the rebuild chain — lesson: the post-extract
  copy step must be part of the build script, never manual.
- **Use Records, not right-associative products** for composite data: the
  extractor erases `(sq * color * piece)` inconsistently across functions.
  (The first failure observed — list-order-dependent blocking — was traced
  to the Rocq bug above; the Record change was kept regardless as hygiene.)

## 2026-08-24 — P1 FULL PASSED, P2 measured, corpus candidate frozen, P4 launched

**P1 (full, 1,000 positions, seed 20260808, 16 workers): 1000/1000
self-consistent, 0 inconsistent, 0 unjudgeable** — the oracle reproduces
its own behaviour exactly across independent emulator invocations, at all
depths (ply quantiles 16–150).

**P2 — corpus candidate generated and measured** (seed 20260807, the
pre-registered seed): **11,103 entries** — early 1,739 / mid 3,725 / late
2,288 / special 1,966 / terminal 709 / preTerminal 676; terminal statuses
309 stalemates + 401 mates. Policy subset (Black-to-move, non-terminal):
4,982. Status coverage required two generator extensions, recorded here
because both are part of the frozen distribution, not post-hoc fixes:
(1) check-biased playouts (probability 0.6 of choosing among checking
moves) — pure random play almost never mates, and a rules corpus without
terminal statuses cannot exercise mate detection; (2) a stalemate-hunt
stratum of mobility-minimising playouts (300 found) — random play
effectively never stalemates. Both are mechanical, seeded, and inside the
generator.

**Scoring cost**: ~18.8 core-seconds per probe at the corpus's depth mix
→ sealing the corpus (double-probe, 11.1k) ≈ 115 core-hours ≈ 7.5 h wall
on 16 workers; plus ~2k policy `choose` probes. Sealing is a one-off,
overnight, parallel job (P5). Scoring a submission after sealing needs no
emulator at all (answers are precomputed).

**P4 — calibration runs launched 2026-08-24.** One run per arm
(`~/fcdd_c04_arms/{armA,armB}`), model claude-opus-5 effort max, no web
tools (offline by construction), oracle budget 5,000 probes per run
(`ORACLE_RUN_ID=cal-<arm>`), 6 h wall timeout, results to
`ledger/raw/arm?_cal_a1_result.json`. **Excluded from inference.** They
calibrate: per-run cost/duration, k, query cap, adapter line cap, timeout
values, uninformativeness thresholds. The post-hoc modelUsage assertion
(C3) runs when results land (`tools/check_model_pin.py`).

## 2026-08-24 — P5 sealing launched; freeze checklist written

Sealing job (`tools/seal_corpus.py`, 8 workers to leave headroom for the
calibration arms' oracle queries) started 17:38 against
`ledger/corpus_candidate.json` (11,103 entries, committed); ETA ~14 h for
phase 1 + policy phase 2. Outputs: `ledger/sealed/answers.json` +
`seal.sha256` + exclusion statistics. The scorer (`tools/score_case04.py`)
and the freeze-candidate analysis (`tools/analyse_case04.py`) are written;
the schedule generator (`tools/make_schedule.py`) is written.

**Freeze checklist (P5) — every `(pilot)` mark in PREREGISTRATION.md gets
replaced at freeze, from these sources:**

| mark | source |
|---|---|
| k (runs per arm) | P4 cost/duration calibration |
| N_Q (query cap) | P4 probe-budget usage |
| adapter line cap | P4 Arm A adapter size |
| per-query timeouts | P4 run durations vs scorer limits |
| MU1_LO / MU1_HI (gate) | P4 scored μ₁ of both pilot submissions |
| corpus size + policy n | sealed counts (11,103 / 2,000) |
| harness pin (C12) | sha256 of the rebuilt hc91emu (in this file, 2026-08-24 entry) |
| model pin | claude-opus-5 effort max, modelUsage-asserted (C3) |

Both calibration runs confirmed in-flight and on-process (Arm A: Rocq tree
under `rocq/`; Arm B: direct Rust crate) as of 17:45.

## 2026-08-24 — FCDD skill changed mid-design; PROMPTs amended pre-freeze

The FCDD skill gained two sections since the case04 PROMPTs were written
(recorded in `skills/formal-contract-dev-current/`, both sourced from this
lab's own findings): §15.5 declares the ATTACK budget with **coverage as
the stop condition instead of convergence** (case02 §5.7 /
`method/ATTACK_BUDGET_DIAGNOSIS.md`: unbounded rounds ran 1–18×, r=0.72
with cost, extra rounds bought byte-identical artefacts); §16.5 serialises
solver and reviewer over one working tree (the review turnstile, from the
ikbr_tools race defects).

Consequences recorded here:
- `armA_PROMPT.md` now requires the declared-budget review rule (point 5)
  — the calibration Arm A session (launched before this edit) runs the
  PRE-CHANGE process; its cost is therefore an upper bound for the amended
  process, and this is noted, not hidden. Nothing was frozen at edit time.
- Both PROMPTs now carry the symmetric hygiene line: commit a clean tree
  before launching a reviewer; the reviewer reports the sha it reviewed
  (the turnstile's lesson, applied to both arms so it does not touch the
  treatment contrast).
- Freeze checklist addition: **the PROMPT.md texts are part of the frozen
  design** (the treatment is the prompt); their hashes go into the
  manifest at P5, and any further edit is an amendment.

## 2026-08-24 — D7: exploratory Arm B model sweep (sonnet)

Operator decision: the control arm additionally runs on `claude-sonnet-5`,
k = 3, pre-registered as exploratory (own report section, NOT part of H1).
Primary stays both arms on `claude-opus-5` (C3 — the case02 A13 model-mix
lesson). Deepseek-flash was requested and is BLOCKED here (no runner/API
key; only the Anthropic CLI is launchable) — it joins the sweep section if
a runner appears before the freeze. Schedule generator now emits sweep
cells in the same randomised order; runner will take `--model`.

## 2026-08-24 — D8: primary moved to deepseek; claude exits the study

Operator decision: Arm A on `deepseek/deepseek-v4-pro`; by C3 the primary
Arm B matches. The completed claude-opus-5 Arm B calibration ($53.41,
50/50 smoke, 0 oracle probes) is retained as a cross-model data point,
excluded from inference. The claude token-reset watcher was KILLED (the
claude Arm A calibration is abandoned, its partial state archived in
`~/fcdd_c04_arms/armA`). Fresh P4 calibration for both arms relaunched
23:44 on `deepseek/deepseek-v4-pro` via `opencode run` into
`~/fcdd_c04_ds/{armA,armB}` (results `ledger/raw/arm?_ds_cal.jsonl`).
The scored-phase runner (`tools/run_scored.sh`, opencode, resume-on-death,
drive.log, DRY mode) is written and syntax/DRY-validated.

## 2026-08-25 — D9 implemented: model referee + engine cross-check

Ground truth moved from the engine to the formal model (operator decision,
DESIGN_DECISION D9). `tools/twin_referee.py` replays every corpus path
through the twin (FEN adapter + computeKey from the engine's zobrist
tables + History semantics matching the engine's convention) and emits the
model's legal set + status; it gates on the canonical perft battery before
emitting anything (passed). `tools/crosscheck_referee.py` joins model and
engine answers: agreement → sealed answer = model's (flag recorded);
engine-unjudgeable → model's; disagreement → bug_inventory.json + excluded
from scoring. Engine-answer sealing continues as the cross-check half
(checkpointed). Docs updated: PREREG §1/§4/§5, IFACE, ORACLE, both
PROMPTs. The smoke set is re-derived from the referee. The scorer now
compares submissions against the model referee's sealed answers.

## 2026-08-25 — the permission wall, systemd units, and D9 implementation

Three infrastructure lessons, recorded for the scored phase:

1. **opencode headless auto-rejects every permission prompt.** The arms
   need the Rocq toolchain under `/home/xcos/.opam` — outside their
   workspace — and died on it (this was also the real cause of the
   09:12–09:15 calibration deaths, not just the API outage). The working
   config (verified by probe) is the FLAT schema:
   `"permission": {"bash": "allow", "read": "allow", ..., "external_directory": "allow"}`.
   Nested `allow` maps, string arrays, booleans, `additionalDirectories`
   under `permission`, and `defaultMode` all fail schema validation.
   `workspace/opencode.jsonc` now carries the flat map (identical in both
   arms; web tools stay unlisted — offline by construction).
2. **Background launches die with the tool session** — the surviving
   pattern is a silenced subshell, but the robust mechanism is
   **systemd-run user units** (`--collect`). Calibration arms and the
   watcher now run as `c04-cal-armA/armB`, `c04-watcher` units; the scored
   runner (`run_scored.sh`) must be launched the same way.
3. **Never `>` a live session jsonl** — a manual relaunch truncated the
   previous (dead) sessions' logs. Launches append (`>>`); the scored
   runner already uses `>` only on a cell's first attempt.

**D9 implemented** (model referee + engine cross-check): see the
2026-08-25 D9 entry above and DESIGN_DECISION D9. `twin_referee.py`
(perft-gated) and `crosscheck_referee.py` are written; the referee pass
over the corpus is running; smoke-set answers re-derived from the referee.

## 2026-08-25 — P4 CALIBRATION COMPLETE (both arms, deepseek)

Both calibration runs reached the definition of done — 50/50 smoke on the
model-referee smoke set, release binaries built, NOTES.md written:

| measure | armA (formal/extract) | armB (direct Rust) |
|---|---|---|
| Rocq spec | `rocq/HC91.v`, 608 lines, no Admitted | n/a |
| extracted Rust | 12,787 lines, hash-locked to the deposited extractor output (md5 verified) | n/a |
| adapter | 132 lines (< 200 cap) | n/a |
| answer latency | ~5 ms | ~5 ms |
| oracle probes used | **0** | **0** |
| smoke | 50/50 | 50/50 |
| cost | deepseek-v4-pro; whole pilot (69 sessions, 10 days) totals $4.68 | same pool |

Freeze values settled by these measurements: k = 5/arm primary + 3 sweep
(D7); N_Q = 5,000 (unchanged — arms used none; cap stays generous);
adapter cap 200 lines (measured 132); per-query timeouts 60 s legal/status,
300 s choose (measured 5 ms). **μ₁ gate thresholds still need the sealed
answers** (engine cross-check sealing in progress) — the calibration crates
get scored against the sealed corpus once it exists, and MU1_LO/MU1_HI are
set from those two μ₁ values per the D9/freeze checklist.

Note the watcher's self-inflicted resume storm (STALE=300 declared slow
sessions dead and murdered them mid-tool-call; process-liveness is the
correct death criterion — fixed in the scored-phase watcher) and that the
sessions still completed through it. Both calibration workspaces are
archived as `~/fcdd_c04_ds/{armA,armB}`.

## 2026-08-25 — the uninformativeness gate FIRED; D11 redesign launched

The calibration crates (both arms, with the shared formal spec shipped)
scored against the model referee: **armA μ₁ = 0.00018, armB μ₁ = 0.00018
— 0 legal divergences each, 2 status divergences each, and those two are
the SAME threefold-repetition positions in both arms.** The repetition
statuses are a scoring-spec impossibility (FEN-only interface cannot
decide history-dependent draws) — fixed: the referee now flags
`repDraw`, and the seal/scorer skip status on those positions. With that
artifact removed both arms score exactly 0 — below the 0.001 lower bound
— **the pre-registered gate declares the benchmark UNINFORMATIVE: with
the kernel-checked spec shared, the rules layer is near-free
transcription for both models and there is no variance to measure.**
Operator decision (D11): withdraw the shared formal spec (reverse D6) —
neither arm sees a specification; Arm A's treatment is doing the formal
expression itself; ground truth stays model-decided (D9, orchestrator
only). Workspaces rebuilt contract-free; calibration relaunched on
deepseek-v4-pro (both arms active); referee re-run with the repDraw flag
(v3); informativeness will be re-checked before any scored run.

## 2026-08-25 — D12: policy becomes the primary (rules can't discriminate)

D11's contract-free calibration scored **μ₁ = 0 for both arms again**
(armA 53 probes, armB 237 probes; both arms' NOTES show the
probe→differential-test→self-review loop converging to perfect rules).
At deepseek-v4-pro's capability the chess rules layer is solvable
perfectly by either process — the μ₁ benchmark has no variance to
measure, with or without the shared spec. Operator decision (D12): the
primary outcome becomes **policy agreement** — `choose` vs the engine's
own level-1 play on the 2,000-position policy subset (ground truth: the
engine's play — the only coherent definition of a clone's strategy;
rules stay model-decided as the co-requisite, so the correctness
principle stands). Reverse-engineering the engine's evaluation + search
through probes is genuinely hard; variance should return. Mechanics
updated: scorer (primary μ₂), analysis, cross-check seal merge (policy
answers carried), PROMPTs (choose = scored outcome), PREREG/DESIGN.
One further calibration pair (policy task) runs after the seal lands, to
set the μ₂ gate thresholds.

## 2026-08-25 — CORPUS SEALED; D12 policy calibration launched

Engine sealing finished: 11,103/11,103, **0 self-inconsistencies**, 146
unjudgeable excluded, 1,999 policy (choose) answers. Cross-check complete:
**0 model-vs-engine disagreements on the whole corpus** (10,957 agree,
146 engine-unjudgeable take the model's answer) — the bug inventory is
EMPTY; the corpus does not bite on the engine's known divergent
behaviours, which is a reportable datum in its own right. Final sealed
`answers.json` sha256 `b10284674a983d7b78e0146455822c76eacadf4c78869028d95d981fc72a84d6`
(rules = model referee with repDraw statuses excluded, policy = engine's
level-1 moves). D12 policy-task calibration launched on both arms
(17:33, deepseek-v4-pro); when they complete: score vs the sealed policy
-> μ₂ gate thresholds -> freeze -> 13 scored runs.

## Pending pilot gates

- **P1 — oracle self-consistency** on a 1,000-position sample per layer
  (two independent replays must agree exactly). Smoke version first (~200
  positions), full version at pilot time.
- **P2 — throughput** (probes/s) → corpus sizes + timeouts.
- **P3 — extraction spike**: small Rocq chess model → rocq-rust-extraction →
  cargo build → adapter answers a kings+knights probe correctly.
- **P4 — calibration runs** (one per arm, excluded).
- **P5 — freeze**: corpus sealed, analysis script dry-run, schedule generated.
97ee7d4fdeda155d29846c8510b62035af5dbfd4bf33512114f9b5b07fb8cc7b  /media/sf_Projects/fcdd_lab/case01_spectrum_gambit/arms/harness/build/hc91emu
