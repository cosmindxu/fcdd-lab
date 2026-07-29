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
