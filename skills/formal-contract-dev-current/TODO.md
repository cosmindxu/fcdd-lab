# TODO — FCDD skill, future development

*(This file is deliberately NOT referenced from SKILL.md — a live A/B
experiment (fcdd_lab case01) loads SKILL.md into measured runs and the
method text must stay byte-identical mid-experiment. Fold this in at the
next skill revision, after case01 closes.)*

## Make the attack-reviewer model an EXPLICIT user choice (2026-07-30, operator)

Beat 4 (ATTACK) currently hardcodes the operator rule "route adversarial
review to the Fable model" (line ~213, distilled from
`use-fable-for-sensitive-tasks`). That silent default caused a real
incident: in fcdd_lab case01 the frozen protocol prescribed same-model
attack reviewers for both arms (§Arms), the skill's baked-in Fable routing
silently overrode it, and the deviation was only caught in the ledger's
per-model usage — resolved by operator amendment A5.

Change for the next revision:
- Replace the hardcoded model with an explicit parameter the user chooses
  per engagement (e.g. `attack_reviewer: <model|person|same-model>`),
  asked for or clearly surfaced at Beat 4 entry — never silently applied.
- The *principle* stays: prefer a different (ideally stronger) model or
  person than the author, for independence. Fable is today's best choice;
  it will not always be. Name the principle, parameterize the model.
- When the skill runs inside a measured/protocolized context, the choice
  must be visible in the run's own output so downstream ledgers catch it.

## DONE — folded in 2026-08-26

- **Attack-reviewer model as an explicit choice** (the item above): superseded in
  practice by **law 12** (declared attack budget), which landed in the installed
  skill from `fcdd_lab/method/ATTACK_BUDGET_DIAGNOSIS.md`. The model-choice
  parameterisation is still owed; the unbounded-iteration half is closed.
- **Law 13 — intent coverage** (`fcdd_lab/method/INTENT_COVERAGE.md`): clause
  provenance, bidirectional traceability, declared completeness scope, and
  spec-side mutation, plus a Beat 1 entry obligation and a restated §5 that now
  says what IS owned rather than only what is not. Tier: derived diagnosis,
  predicted benefit, N = 1 supporting execution (`pipeline_proto`'s `M4_boundary`).

## Version hygiene — a defect this repo is supposed to catch

The vendored copy under `skills/formal-contract-dev-current/` had **drifted from
the installed skill**: law 12 and the Beat 4 rewrite were live in
`~/.claude/skills/` and absent here. That is exactly the silent divergence
`skills/README.md` was written to detect, and it went undetected until someone
diffed it on 2026-08-26. Refresh the vendored copy in the same commit as any
installed-skill change.

**The frozen copy under `skills/formal-contract-dev/` was NOT touched** and must
never be: it is the text case01 measured, and every Arm B number in the paper is
bound to it.
