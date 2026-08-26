# Case 04 — Adversarial Review Round 1: process conformance & result integrity

Date: 2026-08-26. Lenses: (1) process conformance (C13/C3/C14, PREREG §2,§3),
(2) result integrity (degenerate strategies, answer leakage, scorer trust).
Budget declared: one operator-driven round, verify-by-execution everywhere a
claim is made. All numbers emitted by deposited scripts (C10).

## Verdict

**The scored phase is INVALID as evidence for the prevention claim.**
The sealed reference engine — its Z80 source (`chess.asm`, `engine.inc`,
`pieces.inc`, …), its binaries (`chess.tap`, `chess.bin`), and the full
case01 analysis tree (memory map, contract provenance, harness, articles) —
was readable from every cell workspace during the entire scored phase.
Transcripts prove 7 of 13 cells read engine source material and 6 ran the
emulator directly, bypassing the query cap. The policy-layer outcome is
therefore confounded with source access, which is exactly what the
information-symmetry controls (C1, D2, C14) existed to prevent.

## F1 — the leak: a shared symlink to the whole case01 tree (SEVERITY: fatal)

- `~/fcdd_c04_scored/case01_spectrum_gambit` is a symlink to
  `/media/sf_Projects/fcdd_lab/case01_spectrum_gambit`, created
  2026-08-25 20:44 by **armB_r4's own cell** (transcript: `ln -sfn
  /media/sf_Projects/fcdd_lab/case01_spectrum_gambit
  /home/xcos/fcdd_c04_scored/case01_spectrum_gambit`). It landed in the
  SHARED scored root, so every later cell found it there.
- Root causes (orchestrator-side): the shipped oracle CLI computes
  `CASE01 = <build>/case01_spectrum_gambit` for the emulator/ROM/tap,
  but the builder never creates that tree — the cells were forced to
  bridge to the real case01 tree to make the oracle work at all;
  `external_directory: allow` plus the lab living on the same shared
  filesystem made the whole tree reachable; and the C1 guard
  (`workspace_manifest_guard.py`) inventories only the arm workspace
  subtree and does not follow symlinks — the leak is invisible to it.
  C1's "check is code" was code, but the threat model missed symlinks,
  shared-directory reachability, and the CLI's broken-by-construction
  dependency layout.
- Every cell had `external_directory: allow` and cwd near that root;
  transcripts show cells doing `ls /home/xcos/fcdd_c04_scored/` and then
  traversing the symlink (`.../sealed/seedkit/pristine/`).
- 12 of 13 build dirs ended up with their own
  `<build>/case01_spectrum_gambit` symlink; at least one cell (armB_s1)
  is seen creating it itself (`ln -s …` in transcript).
- The C1 guard (`workspace_manifest_guard.py`) inventories only the arm
  workspace subtree and does not follow symlinks → the leak is invisible
  to the guard. C1's "check is code" was code, but the threat model
  missed symlinks and shared-directory reachability.

## F2 — cells consumed engine source (SEVERITY: fatal; per-cell evidence)

Content-reads of `sealed/seedkit/pristine/` files (cat/sed/grep/cp/diff
on `chess.asm` / `engine.inc` / `bookgen.py` etc.) and direct `hc91emu`
runs, from each cell's own transcript:

| cell | source content-reads | direct hc91emu runs | mu2 |
|---|---|---|---|
| armA_r1 | 32 (sed engine.inc 1-420) | 16 | 0.088 |
| armA_r2 | 4 (searched for sealed dirs) | 1 | 0.078 |
| armA_r3 | 14 (grep equ chess.asm) | 2 | 0.078 |
| armA_r4 | 12 (grep WP/WN… chess.asm) | 2 | 0.010 |
| armA_r5 | 8 (cat bookgen.py) | 2 | 0.088 |
| armB_r1 | 0 | 0 | 0.183 |
| armB_r2 | 10 (grep aiDepth/setupBoard) | 6 | 0.231 |
| armB_r3 | 0 | 1 | 0.302 |
| armB_r4 | 67 (md5sum diff chess.asm…) | 12 | 0.088 |
| armB_r5 | 1 | 1 | 0.119 |
| armB_s1 | 0 | 1 | 0.503 |
| armB_s2 | 4 (cp seedkit material) | 0 | 0.000 |
| armB_s3 | 0 | 1 | 0.088 |

(Emitted by `tools/review_evidence.py` — C10. Every cell except armA_r2
created the symlink bridge itself in-transcript; armA_r2 copied the
harness to /tmp/r2_wsRED instead. armB_r4 created the SHARED-root link
that later cells reused.)

Direct emulator runs = uncapped oracle access (C14's counter lives in the
CLI; the emulator itself is local and countable only by transcript).

## F3 — the perfect-policy cluster is a transcription, not skill

armB_s2 (μ₂ = 0.000, 1999/1999) self-describes as "a faithful port of the
engine's eval … bit-for-bit". Verified by code diff:
- `engine.inc:2421`: `defw 0,100,320,330,500,900,0`  == armB_s2 eval.rs
  `MATERIAL: [i16; 7] = [0, 100, 320, 330, 500, 900, 0]`
- `engine.inc:2428`: `defb 5, 10, 10,-20,-20, 10, 10, 5` == armB_s2's
  pawn PST row, byte for byte
- `PHASE_EG equ 8` == `PHASE_EG: u8 = 8`; MVV-LVA/SEE-lite/alpha-update
  search details match engine.inc's documented level-1 search
So the two "best" runs (armA_r4 0.010, armB_s2 0.000) reproduce the
engine's exact eval tables — obtainable only from the leaked source
(PREREG §2 says eval weights/PST are precisely what the query cap was
supposed to make the cells *probe for*, not read).

## F4 — the clustered μ₂ structure

- Pairwise choose-identity on a 60-position sample: cluster 1 =
  {armA_r1,r2,r3,r5, armB_r4, armB_s3} mutually 60/60 identical;
  cluster 2 = {armA_r4, armB_s2} 60/60 identical. Cross-arm identity
  shows the policy function is largely determined by shared inputs
  (skeleton ordering + leaked constants), not by the treatment.
- choose == first-legal-move only 13-22%: the first-move-default
  degenerate strategy is REJECTED; the convergence is via shared eval
  constants.
- Consequence: the 13 runs are not 13 independent explorations; the
  permutation test's exchangeability assumption is strained. This is a
  design observation, not by itself a violation.

## F5 — conformance checks otherwise pass (with one recorded deviation)

- Arm A (all 5): Rocq trees recompile clean; zero Admitted/admit /
  run-added Axiom; extraction re-runs; adapters 104-124 lines (≤200);
  behaviour tokens present but as CLI dispatch words (flagged per rule,
  not auto-failed).
- A4 deviation (recorded, not excluded): shipped `extracted.rs`
  hash-differs from the re-extracted output by exactly 7 header lines
  (2 nondeterministic debug-timing lines + 5 `#![allow]` pragmas);
  the 43,697-line body is byte-identical. Cosmetic-header deviation;
  no behavioural difference.
- Arm B (all 8): zero `.v` files, zero Rocq invocations in transcripts.
- C3: attempt models in drive.log all match schedule pins; no
  model/agent overrides in any workspace config.
- C14 (CLI counters): max 1,345/5,000 (armB_s1); all within cap. Note:
  the counter is bypassable via direct emulator use (F2), so this
  number understates real engine access.

## F6 — R1.7 verify-by-execution (scorer spot check)

The scorer was already validated at seal time (P1: 1000/1000
self-consistency; crosscheck: 0 disagreements). Post-hoc spot check of
scored outputs against manual re-probing was superseded by F1-F3 (the
scored outcomes are explained; re-verifying their arithmetic adds
nothing). Deprioritised, recorded as such.

## Consequences for the manuscript

1. The pre-registered analysis (H1 p = 0.118, NOT SUPPORTED) stands as
   computed, but **no causal interpretation of the arm difference is
   admissible**: differential source access confounds the comparison in
   the observed direction (heavier readers → lower μ₂; the two best runs
   are proven transcriptions of leaked constants).
2. Options for the operator:
   a. Report as a constraint-violation study (the honest default):
      the experiment measured "access to the answer" more than the
      treatment; publish the failure + the design's weak point.
   b. Re-run the scored phase with fixed isolation (self-contained
      oracle service; cells confined to their workspace with no
      external-directory permission; symlink traversal blocked; fresh
      schedule/seal/budget). Budget ~$10-15, ~1 day.
3. Either way the amendment log records this review and its findings
   verbatim (C11).
