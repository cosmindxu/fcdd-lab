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
