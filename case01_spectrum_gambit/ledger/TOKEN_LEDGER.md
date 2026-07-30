# Token ledger — case01 (narrative)

Machine truth lives in `runs.csv`; this file carries the story per run
(what the phase was, anything anomalous, gate outcome color). One dated
bullet per run, newest last. Lanes: meta / seeding / step1_contract /
armA:<bug> / armB:<bug> / grading.

- **2026-07-29 · smoke01 · meta** — isolation smoke (fresh cwd sees NONE of
  the orchestrator project's memory); Fable 5, $0.34; row in runs.csv.
- **2026-07-29 · (aborted, unrecorded) · step1_contract** — first step-1
  launch ran ~2 min on Fable/high and was killed on the operator's
  models-directive (PROTOCOL A3) before writing anything; killed `claude -p`
  runs emit no result JSON, so its small cost is honestly UNRECORDED here.
  Relaunched on Opus/max.
- **2026-07-29 · step1 · step1_contract** — contract authoring, detached
  headless, **claude-opus-5**/max, 108 turns, ~53 min API. Gate **GREEN 11/11**
  (`bridge/run_all.sh`, exit 0): `spec/Contract.lean` 1,271 L / 95
  kernel-proved theorems (empty axiom profile), Python twin, bridge b0–b7,
  z3 tier s1–s3, **10 organic findings** in the pristine engine (2 HIGH: F5
  ROM-sysvar corruption from ply 128; F10 16-bit Zobrist ~18 % collisions).
  Beat 4 (ATTACK) deliberately not run — recorded residual. ⚠ cost column
  EMPTY: the frozen D3 price table has no `claude-opus-5` row (lanes were
  launched on opus-5 under A3 "Opus"); raw counters are the ledger truth,
  CLI-reported **$21.7527** noted in the row. Price pin = pending dated
  amendment (operator).
- **2026-07-29 · seed01 · seeding** — 7 sealed single-fault variants
  (`arms/variants/bug01..07`, no-git), symptom reports (`bug_reports/`),
  per-bug acceptance gates (`sealed/acceptance/`), arm harness
  (`arms/harness/`). Answer key **sealed unread**: sha256
  `27d47c88136107f0e9c2f236de85b0ba7cf2cc4e92d8ccdea19c8de72d0ebd2f`; full
  206-file manifest → `ledger/sealed_manifest.sha256` (tracked; the push
  timestamp is the pre-registration mark). Lane also relocated
  `work/pristine/` → `sealed/seedkit/pristine` (the `work/` deletion is
  committed as-is). Same opus-5 price-pin caveat; CLI-reported **$29.6886**.
- **2026-07-29 23:28 · arms launched · armA:*/armB:*** — operator GO received;
  detached driver `tools/run_arms.sh` (pid in `raw/arms_driver.pid`), 7 bugs ×
  2 arms, **pair-per-bug**: A+B of the same bug run concurrently (same API
  weather for both arms), pairs sequential. Config: `claude-opus-5` /
  effort **max** (A3), `--output-format json`, 2 h wall timeout per run
  (rc=124 → DNF-timeout), offline by construction — allowedTools
  A=`Task,Bash,Read,Write,Edit,MultiEdit,Glob,Grep,TodoWrite`, B=+`Skill`
  (no web tools). $40/run cap enforced post-hoc on CLI-reported USD
  (opus-5 D3 pin still pending). Prompt packs `prompts/arm{A,B}_header.md` +
  `arm_footer.md`; **orchestrator assembled prompts blind** (script cats
  `bug_reports/*.md`; reports remain unread by the orchestrator). Arm B
  workspace copies get a disclosed mechanical re-point: `bridge/emu.py` →
  workspace harness, `b7_findings.py` → variant `engine.inc`, then a blanket
  scrub of any remaining `/media/sf_Projects/*` signpost in BOTH arms' copies
  (the pristine engine lives on this disk; arms must not be led to it).
  Results land in `raw/arm{A,B}_bugNN_result.json`; driver log
  `raw/arms_driver.log`.
- **2026-07-30 01:03–01:33 · bug01 pair complete → EXPERIMENT PAUSED** —
  **armB:bug01**: rc=0 at 95 min, self-reported gate GREEN 12/12 (quiescence
  ply-cap fault fixed; contract extended +S5 +25 theorems + new bridge layer
  b8; `make test` 5/5) at **$89.28 CLI — 2.2× the frozen $40 cap** → headline
  booking per frozen protocol = DNF-at-cap, gate-reached + quality-beyond-bar
  recorded. Its attack round ran **claude-fable-5 subagents** (the FCDD
  skill's own routing) — method-inherent A3 deviation, flagged.
  **armA:bug01**: killed by the orchestrator's 2 h wall cap at **$43.48**,
  gate not reached — already over the $40 cost cap, so protocol DNF-at-cap
  stands on its own. **Cap calibration is broken for opus-5/max on this
  task class; trajectory = every run DNFs ⇒ scientifically void at ~$150/pair
  ⇒ PAUSED.** Ops honesty: the first pause attempt killed the setsid WRAPPER
  pid (recorded by `echo $!`), not the driver bash — the driver survived two
  kill attempts and started bugs 02, 03, 04; their 6 kill remnants
  ($0.59–$1.38 each, $5.10 total) are booked lane=meta/killed-pause,
  EXCLUDED from the A/B (reruns get fresh workspaces). Driver fixed
  (`echo $$` + BUGS/TIMEOUT_OVERRIDE env). Orchestrator contamination log:
  read armB:bug01's final self-report (fix summary), and bug04's symptom
  report scrolled through a pgrep dump — symptom-level only, sealed key
  untouched; grading stays blinded via fresh agents. Arms spend tonight:
  **$138.86** ($132.76 measured bug01 + $5.10 pause waste + $0.87+$0.13
  rounding in rows); prep lanes $51.44; case total ≈ **$190.6**.
- **2026-07-30 07:47–08:01 · pair bug02 closed (A4 no-cap regime)** —
  **armB:bug02 VALID: gate GREEN 13/13 self-reported at $23.42, 44 min,
  156 turns** — Arm B's marginal cost fell $89.28 → $23.42 (the H1
  amortization pattern, n=2). Bonus finding: B reports the step-1 gate's
  11/11 green was measured against a wrong/stale binary, now rebuilt and
  pinned byte-identical (quality-beyond-bar + a step-1 package caveat to
  verify at grading). Reviewer-model note: THIS run's attack agents were
  opus-5 (no fable in modelUsage) — the skill's fable routing is
  non-deterministic run-to-run; disclosed per A5, per-run models in
  runs.csv. **armA:bug02 EXCLUDED — `api_error` crash** at 57 min /
  $14.76 / 103 turns (infra, not a method verdict); fresh rerun QUEUED
  (tools/run_solo.sh, gated behind the bug01 solo, pid-watch on 1205320)
  to avoid 4-way concurrency (suspected factor in the api_error).
  Contamination log grows: orchestrator read B:bug02's self-report
  (mkHalf WN-vs-WP root cause). In flight: solo armA:bug01-rerun +
  pair bug03; armA:bug02-rerun queued.
