# CASE 01 — Spectrum Gambit: FCDD vs typical dev, token-cost study

**Pick-up-here document.** After a session clear: read this file top to bottom,
then `PROTOCOL.md` (frozen design), then the last dated entry in the Session log
below. The ledger (`ledger/runs.csv`) says what has already run and cost what.

## Goal

Measure **how many LLM tokens each method needs to reach roughly equivalent code
quality** when fixing bugs in the Spectrum Gambit chess stack:

- **Arm A — typical development**: reproduce → fix → test → code-review rounds
  (reviewer agent) → done when the pre-registered gate passes.
- **Arm B — FCDD** (`~/.claude/skills/formal-contract-dev/SKILL.md`):
  Prove → Twin → Bridge → Attack around a formal contract; done at the same gate
  (plus whatever the method proves beyond it, which we record but don't require).
- **Step 1 (its own measured phase, precedes the arms)**: express the chess game
  + the implemented strategies as a **formal contract**. Its token cost is Arm
  B's upfront investment and is reported separately (upfront vs marginal).

Final deliverable: the token ledger + a report — upfront vs per-bug marginal
cost per arm, the crossover bug-count (if any), and quality achieved vs the bar.

## System under test

- `upstream/` = clone of https://github.com/cosmindxu/spectrum-gambit.git —
  the **web wrapper**: hc91emu core + chess engine compiled to WASM
  (`src/web.c`, Emscripten), JS front-end (0x88-board-diff → PGN move log,
  `.szx` save/resume, clocks), Cloudflare Worker + D1 ladder/correspondence
  backend (`backend/worker.js`, `schema.sql`; `devserver.py` = local mirror).
- **The chess engine itself lives in hc91emu, NOT in this repo**:
  `/media/sf_Projects/HC91_emulator/chess/` — **7,343 lines of Z80 assembly**
  hand-written by Fable: `chess.asm` (2,268) + `engine.inc` (2,489) +
  `movegen.inc` (1,403) + `perft.inc` (578) + `tt.inc` (309) + `zobrist.inc`
  (230) + `pieces.inc` (66); alpha-beta, transposition tables, quiescence,
  zobrist hashing, built-in perft. Built via `chess/Makefile` (pasmo →
  `../tools/zxtap.py` → `chess.tap`). `upstream/build.sh` embeds that tap,
  expecting an hc91emu checkout as a **sibling directory** at build time.
- Harness assets already in hand: the hc91emu emulator (z80full 160/160,
  `make test`); `upstream/verify.mjs` (headless boot + e2-e4 + PNG render);
  `upstream/test_movelog.mjs`; `upstream/TEST_PLAN.md`; an autoplay skill in
  `upstream/.claude/skills/`.
- **GitHub issue tracker is EMPTY** (commit refs #1–#5 are closed PRs) — there
  is no ready-made bug inventory. See PROTOCOL for where the bug set comes from.
- Peripheral: a claude.ai-connected MCP server "Spectrum_Gambit" exists
  (compete/ladder API; unauthenticated in this CLI). Not needed for the core
  experiment.

## Design decisions (operator, 2026-07-29 — full text in PROTOCOL.md §Decisions)

- **D1 surface**: the Z80 engine `chess.asm` (fixes in asm; emulator = harness).
- **D2 bugs**: 7 seeded single-fault variants (sealed answer key, symptom-level
  reports, no-git tarballs, offline arms) + an organic bonus lane for real
  finds. Issue tracker was empty.
- **D3 metric**: cost-weighted USD total (Fable 5 = 10/20/1/50, Opus 4.8 =
  5/10/0.5/25 per MTok at 1-hr cache-write rates); raw counters always logged.
- **D4 contract**: layered — full implemented-rules kernel spec + strategy as
  properties; FIDE divergences flagged, not normalized.
- **D5 arms — AMENDED (A3, operator 2026-07-29): ALL lanes and both arms run
  on the Opus model at effort max.** Same-model parity unchanged.

PROTOCOL is **FROZEN v1.0**; amendments must be dated notes there.

## Measurement mechanics (verified 2026-07-29)

- Every measured phase runs in its **own attributable unit**: a dedicated
  interactive session or a headless `claude -p --output-format json` run.
  Lane tags: `meta`, `seeding`, `step1_contract`, `armA:<bug>`, `armB:<bug>`,
  `grading`.
- Claude Code session transcripts
  (`~/.claude/projects/<slug>/<session>.jsonl`) carry per-assistant-message
  `usage` objects: `input_tokens`, `cache_creation_input_tokens`,
  `cache_read_input_tokens`, `output_tokens` (schema verified against a live
  transcript). `tools/tokencount.py` sums them (deduping streamed repeats by
  message id) and emits a ready `runs.csv` row.
- Headless runs: save the final JSON (`usage` / `modelUsage` /
  `total_cost_usd`) under `ledger/raw/`; `tokencount.py headless` parses it.
- Ledger: `ledger/runs.csv` (machine truth) + `ledger/TOKEN_LEDGER.md`
  (narrative).

## Fairness rules (defaults — operator may veto any)

1. **Same model + same effort for both arms**, logged per run in the ledger.
2. **Isolation**: arms run in separate worktrees + fresh sessions. Arm A never
   sees the contract, proofs, or any Arm B artifact. The orchestrator gives
   both arms the same scripted prompt pack and does not hand-hold either.
3. **Gate pre-registered per bug BEFORE either arm runs**: acceptance test(s)
   for the bug + the repo's regression checks green + a blinded rubric review.
   An arm stops when the gate passes; **tokens-to-gate is the measurement**.
4. Step-1 contract cost is attributed to Arm B, reported as upfront (amortize
   over N bugs to find the crossover, if any).
5. If bugs are seeded: the seeding agent's answer key stays **sealed** (sha256
   recorded in the ledger; the orchestrator never reads the key or the seeded
   diffs) until grading.
6. k=1 run per bug per arm on the first pass; replicate runs where the
   observed gap is within plausible single-run noise before claiming a winner.
7. Record **quality-beyond-bar** per arm (latent bugs found, invariants
   proved, review findings) so "equivalent quality" doesn't hide asymmetric
   upside — FCDD's claim is not token-thrift, and the report must not
   strawman either method.

## State

- [x] Lab folder + case scaffold, upstream cloned (`dfd4f1e` at clone time)
- [x] Engine source located (hc91emu sibling), issue tracker checked (empty)
- [x] Token-usage schema verified; `tools/tokencount.py` v0
- [x] Operator answers to the 4 design questions → **PROTOCOL FROZEN v1.0**
- [x] **Step 1** DONE 2026-07-29 23:07 — gate GREEN 11/11; Contract.lean
      (1,271 L, 95 kernel-proved thms, empty axioms) + twin + bridge + smt +
      10 organic findings (2 HIGH). Ledger row `step1` (opus-5, $21.75 CLI).
- [x] Seeding lane DONE 2026-07-29 23:07 — 7 variants + symptom reports +
      per-bug gates + harness; key sealed (sha256 in ledger, manifest =
      `ledger/sealed_manifest.sha256`, orchestrator unread). Row `seed01`
      (opus-5, $29.69 CLI).
- [ ] ⚠ **D3 price pin for `claude-opus-5`** (lanes ran opus-5 under A3
      "Opus"; frozen table lacks it → cost columns empty, CLI USD in notes).
      Needs a dated PROTOCOL amendment by the operator before report math.
- [~] Arms RUNNING since 2026-07-29 23:28 (operator GO) — detached driver
      `tools/run_arms.sh`, pair-per-bug sequential, opus-5/max, 2 h
      timeout/run, results → `ledger/raw/arm{A,B}_bugNN_result.json`;
      ETA all 7 pairs ≈ overnight. See TOKEN_LEDGER 23:28 entry for the
      full disclosed config.
- [ ] Grading (blinded) + unseal + report

## Remote

`origin` = https://github.com/cosmindxu/fcdd-lab — **PRIVATE** for now
(deliberate: the sealed answer key must stay unpublishable while arms run;
flip to public at report time for pre-registration credibility:
`gh repo edit cosmindxu/fcdd-lab --visibility public
--accept-visibility-change-consequences`). Push after every protocol
amendment and ledger update; the pushed hash of `17588eb` is the
server-timestamped pre-registration mark.

## Session log

- **2026-07-29** — Case created (model: Fable 5 / effort max for orchestration;
  earlier recon this session ran on Opus 4.8). Cloned upstream, located
  `chess.asm` (2,268 L, hc91emu), confirmed empty issue tracker, verified the
  usage-schema fields, wrote scaffold + tokencount v0. Open questions put to
  the operator (surface / bug origin / metric / contract depth). Meta-lane
  tokens for this bootstrap live in session `dc589311-cdbd-4958-9b03-92a69446dfe8`
  (shared with unrelated ikbr_tools work — count only from the first
  spectrum-gambit message onward; noted here for the ledger).
- **2026-07-29 (launch)** — Two auto-mode-classifier blocks hit ORCHESTRATOR
  launch commands (meta lane, before any measured run — measured lanes are
  unpolluted; see PROTOCOL A3). Operator directive mid-launch: **all lanes →
  Opus / effort max** (A3); the ~2-min Fable step-1 was killed (cost
  unrecorded — killed runs emit no result JSON; TOKEN_LEDGER note) and both
  lanes relaunched **detached** (setsid) with scoped `--allowedTools` (no web
  tools → offline by construction). PIDs in `ledger/raw/{step1,seeding}.pid`;
  results will land in `ledger/raw/{step1,seeding}_result.json`. This
  orchestrator session can be `/clear`-ed freely: the runs are detached;
  resume from THIS file (and session tasks #23–#26).
- **2026-07-29 (later)** — Operator answered the 4 design questions (D1–D5
  above); Fable 5 + Opus 4.8 prices pinned by web search and frozen into
  `tools/tokencount.py`; PROTOCOL frozen v1.0 and committed. Next actions in
  order: (1) launch **step 1** (contract authoring, measured) as its own
  attributable run against the pristine `chess.asm`; (2) launch the seeding
  lane in parallel (independent agent, sealed outputs); (3) pre-register
  per-bug gates as seeded variants land; (4) arms; (5) blinded grading +
  unseal + report.
- **2026-07-29 23:07–23:30 (results landed; orchestrator now the /clear-ed
  session, Fable 5)** — BOTH detached lanes exited clean at 23:07 (watcher
  confirmed; PIDs gone). Step 1: gate GREEN 11/11, 95 kernel thms, 10 organic
  findings (2 HIGH). Seeding: 7/7 variants + reports + gates + harness;
  answer key sealed unread (sha256 + 206-file manifest in ledger). Ledger
  rows `step1`/`seed01` appended via tokencount. **Both lanes actually ran
  `claude-opus-5`** — frozen D3 table has no opus-5 row, so cost columns are
  empty and CLI-reported USD sits in notes ($21.75 + $29.69); operator must
  pin opus-5 prices as a dated amendment before report math. Seeding lane
  relocated `work/pristine/` → `sealed/seedkit/pristine` (deletion committed
  as-is). Committed + pushed = pre-registration mark for gates/key/variants.
  Orchestrator session runs a 2-hourly progress-report cron (operator
  request). **Arms NOT launched — awaiting operator GO** (and the price
  pin). Nothing in `sealed/` was read.
