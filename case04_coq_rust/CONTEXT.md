# CASE 04 — Coq-extracted Rust vs direct Rust: cloning the Z80 chess engine

**Pick-up-here document.** After a session clear: read this file, then
`DESIGN_DECISION.md` (D1–D5, the operator's forks), then `CONSTRAINTS.md`
(C1–C16), then `PREREGISTRATION.md` (**DRAFT — freezes only after pilot gates
P1–P5 pass**), then `PILOT.md` for pilot state.

## Goal

Cases 01/02 measured **repair** (bug injection → fix). That design cannot see
FCDD's actual claim, which is **prevention**: a target expressed formally
*before* coding should produce fewer defects in the first place. Case 04 tests
the prevention claim by **forward synthesis**:

> Reimplement the Spectrum Gambit Z80 chess engine in Rust, twice —
> once by formally expressing it in Rocq and mechanically extracting Rust,
> once by direct Rust development — and count behavioural divergences from
> the pristine Z80 engine, which is the hidden oracle.

Primary outcome: per-run defect mass μ₁ = fraction of a sealed position corpus
where the submission's *rules-layer* behaviour (legal move set + terminal
status) diverges from the oracle. See PREREGISTRATION §1, §4.

## Arms (D1, D5)

- **Arm A — FORMAL/EXTRACT.** Engine expressed in Rocq 9.1.1; Rust generated
  **exclusively** by `rocq-rust-extraction` 0.2.1 (AU-COBRA, MetaRocq 1.5.1;
  installed in opam switch `coq-switch`; source `~/src/coq-rust-extraction`,
  public on GitHub). Gate: `rocq compile` clean, zero `Admitted`/`admit`/new
  `Axiom`, extraction runs, crate builds. Thin hand-written adapter allowed
  under the frozen adapter rule (PREREG §2). Proofs are NOT required —
  the treatment is formal *expression* + mechanical extraction; proofs
  attempted are recorded as quality-beyond-bar.
- **Arm B — DIRECT.** The same crate contract, written directly in Rust,
  ordinary development + review rounds. Arm B may not touch Rocq/extraction.

Both arms: same pinned model (subagents pinned too, C3), same workspace
byte-for-byte except `PROMPT.md` (`case03/tools/parity_assert.py`), same
oracle CLI with the same hard query cap (D2), same definition of done.

## Assets inventory (all verified to exist, 2026-08-24)

- **Oracle (sealed, orchestrator-side only):**
  `case01_spectrum_gambit/sealed/seedkit/pristine/chess.tap`
  (tape sha256 `33ed86b2…78b4`; the `c107dfaf…dc0f` recorded here until
  2026-08-26 is the sibling `chess.bin`, not the tape — a mislabel that would
  have made C1's hash check miss the file it names). NEVER shipped to any arm
  workspace (C1) — but see the audit note in `case03/CONSTRAINTS.md` C1: a
  byte-identical copy of the tape is tracked in the repository itself.
- **Harness:** `case01_spectrum_gambit/arms/harness/` — `build/hc91emu`,
  `roms/48.rom`, `tools/chesspos.py` (FEN→save-block encoding, .sna decode).
- **FEN injection + fixed frame schedule:** case02's
  `armA_characterisation_v1_prompt_exposed/charlib.py` (inject via the game's
  own tape loader; deterministic runs; ~5 probes/s measured there).
- **Memory map (provenance: chess.asm equates, via
  `case01/step1_contract/bridge/emu.py`):** legal-move buffer at `0x6000`
  (4 bytes/move: from,to,flag,score), count at `0xE0A0`; `gameState` at
  `0xE088` (0 play, 1 W-mated, 2 B-mated, 3 stalemate, 4 draw, 5 flag-fall);
  moveLog at `0xE200`, count `0xE15D`. Buffer is meaningful only when the
  engine is parked awaiting input — the CLI must check judgability loudly.
- **Corpus sampling:** `python-chess` 1.11.2 installed (orchestrator-side only;
  used to sample random reachable positions, never shipped to arms).
- **Shared reference (D6):** `case01_spectrum_gambit/step1_contract/spec/
  Contract.lean` — 1,271 lines, Lean 4 core only, no sorry/native_decide,
  95 kernel-proved theorems, empty axiom profile. Shipped byte-identical to
  BOTH arms as `reference/Contract.lean`. The Lean→Rocq import route
  (`rocq-community/rocq-lean-import`) was investigated and rejected —
  extraction-breaking alpha (see DESIGN_DECISION D6).
- **Extraction mechanics:** `From RustExtraction Require Import Loader` +
  `ExtrRustBasic` (+ `ExtrRustUncheckedArith` for native int remaps), then
  `Redirect "out.rs" Rust Extract <ident>.` (pattern from the plugin's tests).
- **Inherited guards:** `case03/tools/parity_assert.py`,
  `case03/tools/workspace_manifest_guard.py` (the sealed corpus registers as
  sealed material).

## Toolchain pins (C12)

Rocq 9.1.1 (opam switch `coq-switch`, OCaml 5.2.1), MetaRocq 1.5.1+9.1,
rocq-rust-extraction 0.2.1, rustc/cargo 1.97.1, python3 + python-chess 1.11.2,
hc91emu at `arms/harness/build/hc91emu` (rebuilt, MAX_TYPE_OPTS 2048).
**Models (D7/D8): primary = `deepseek/deepseek-v4-pro` for BOTH arms via
`opencode run`; Arm B exploratory sweep = `deepseek/deepseek-v4-flash`
(k=3). Claude exits the design entirely.** Subagents pinned + verified
per-run (C3).

## State

- [x] Design forks decided by operator (D1–D5, 2026-08-24): Coq→Rust (not
      OCaml), capped symmetric oracle queries, rules-primary/policy-secondary
      scoring, new case04 with pilot first. D6: Lean contract as symmetric
      shared reference; rocq-lean-import rejected.
- [x] Toolchain verified installed; extraction invocation pattern identified.
- [x] Docs written: CONSTRAINTS.md, PREREGISTRATION.md (draft), DESIGN_
      DECISION.md, PILOT.md (append-only).
- [x] Oracle CLI built + validated: replay-based legal/status probes
      (chunked .sna replay with clock patches), choose probe (deterministic),
      query cap enforced in code. P1 smoke: 20/20 self-consistent.
- [x] Corpus generator built (python-chess playouts, legality-filtered,
      phase/special/terminal strata). Harness rebuilt with MAX_TYPE_OPTS
      2048 (environment pin, recorded in PILOT).
- [x] **P3 PASSED**: extraction spike end-to-end (Rocq→rust-extraction→
      cargo→adapter), 8/8 agreement with python-chess on kings+knights.
- [x] **P1 PASSED (full, 1,000 positions): 1000/1000 self-consistent,
      0 unjudgeable** (16 parallel workers).
- [x] **P2 measured**: corpus candidate 11,103 entries (seed 20260807,
      709 terminal incl. 309 stalemates + 401 mates, 4,982 policy subset);
      scoring ≈ 18.8 core-s/probe; sealing ≈ 7.5 h wall on 16 workers.
- [x] Arm infrastructure: IFACE.md, ORACLE.md, skeleton crate, smoke set
      (50/50 consistent), PROMPT.md per arm, workspace builder passing both
      C1 controls (parity + manifest guard), model-pin checker (C3).
- [~] **P4 IN FLIGHT since 2026-08-24 17:25**: one calibration run per arm
      (claude-opus-5 max effort, 6 h wall cap, excluded from inference),
      results → `ledger/raw/arm?_cal_a1_result.json`.
- [ ] P5 freeze: seal the corpus (overnight parallel double-probe + choose
      answers), analysis script dry-run against a real cell, schedule with
      committed seed, replace all `(pilot)` marks in PREREGISTRATION.md.
- [x] 13 scored runs completed (13/13 binaries), scoring done
      (`ledger/scored/*.json`), analysis computed (`ledger/analysis_result.txt`:
      H1 p=0.1181 NOT SUPPORTED, gate informative).
- [x] ≥2 adversarial review rounds (C11): round 1 (ledger/review_round1.md)
      found the sealed engine LEAKED to every cell (symlink bridge to
      case01 tree; 7/13 cells read engine source; 2 best runs are
      transcriptions). Round 2 (REPORT.md §10) reviewed the report.
- [x] **OUTCOME: constraint-violation study.** Scored phase invalid as
      evidence (PREREG Amendment A-2026-08-26); REPORT.md is the study's
      output; prevention claim remains untested. Decision: Option A
      (report, no re-run) chosen by operator 2026-08-26.

## Session log

- **2026-08-24** — Case created. Operator criticism accepted: case02 tested
  repair, FCDD claims prevention; design switched to forward synthesis in
  Rust against the Z80 oracle. Four design forks put to the operator and
  answered (D1–D5). Assets audited: pristine tap (sealed), harness, charlib
  FEN-injection, bridge memory map, python-chess, Rocq+extraction plugin —
  all present. Docs + pilot tooling in progress.
- **2026-08-26** — Scored schedule finished 13/13 (after a deepseek 402
  outage, OOM kills of Rocq cells, a 16 GB swapfile added by operator, and
  a driver rewrite for silent-death relaunch + armA concurrency cap).
  Scoring sharded for the slow armA binaries. Analysis: H1 p=0.1181 (NOT
  SUPPORTED), gate informative. Round-1 adversarial review then found the
  fatal leak: every cell bridged to the real case01 tree (oracle CLI
  depended on paths the builder never ships; external_directory allowed);
  sealed engine source + emulator readable by all cells; 7/13 read it, 6
  ran the emulator uncapped; armB_s2's 1999/1999 is a byte-exact
  transcription of engine.inc tables. Operator chose Option A: report as
  a constraint-violation study (REPORT.md, PREREG amendment). Conformance
  otherwise passes (F5). Round 2 reviewed REPORT.md (R2-1..R2-6).
