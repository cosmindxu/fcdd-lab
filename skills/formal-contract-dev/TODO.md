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
