# CASE 07 — is the ATTACK budget safe? (pre-registration, DRAFT r2)

**r2 applies review round 1** (§9): seven blocking findings, all accepted. The
r1 discipline stands — short, rules before numbers, pilot before k — and r2 adds
**rules**, not numbers.

## 1. What is being tested

`method/ATTACK_BUDGET_DIAGNOSIS.md` measured, from case 02's runs: the ATTACK
beat ran **1–18 rounds** across Arm B's 28 repeats of the same defects; round
count correlated **r = +0.72** with cost (≈ half its variance); Arm B runs with
≥ 6 round-mentions (n = 9) cost **$48.33** against **$28.42** for ≤ 2 (n = 12) —
while **all 56 runs, both arms, produced a byte-identical artefact**. The fix —
stop on coverage, budget convergence — shipped as **law 12** on a *predicted*
benefit. Nobody has tested whether the bounded rule is **safe**.

**H1.** Bounded ATTACK **at its two-round default** misses no confirmed blocking
finding, within a fixed declared surface, that unbounded ATTACK confirms — at
materially lower CONSUMED cost.

**Falsified by:** one within-surface miss (→ the two-round *default* is unsafe;
law 12's declared-budget principle is untested by that, and the report must not
overreach it), OR a CONSUMED cost ratio BUDGET:CONV above **0.75** (→ the budget
does not buy the saving that motivated it).

## 2. Why decidable — with the §2 claim scoped honestly

The primary compares the two arms' **outputs**; no hidden truth exists for the
primary, so the case-04 leak class cannot arise **for the primary**. Two
answer-shaped artefacts DO exist and get custody rules: the hardened stratum's
history (§4) and the finding ledgers (§8). Both outcomes are results:
confirmation → the programme's first tested method improvement; refutation →
law 12's default is amended or reverted.

## 3. Arms — the difference, stated exactly

Both arms receive a **deposited, per-cell skill text** (never the shared
`~/.claude` install — that would be cross-arm global state):

- **BUDGET** = the current skill verbatim.
- **CONV** = the current skill with the stopping-rule complex reverted to the
  frozen text at its three sites: Beat 4 (frozen #14–17, verbatim), §15.5
  removed, law 12 removed, and the description's budget clause reverted.
  Deposited as `arms/SKILL_CONV.md` with a diff against BUDGET's text, so the
  delta IS the treatment and is inspectable.

**The r1 symmetry claim was false and is withdrawn**: the arms differ in the
stopping-rule *complex* (four sites), not one line. Everything else — laws 13/14,
Beat 0.5, lenses (byte-identical in both copies, verified) — is shared.

**Surface (B5).** The orchestrator declares an identical initial surface set S
per unit, for both arms, before any run. CONV findings **outside S** are reported
separately and do not count against H1. Under CONV, mid-run widening is permitted
(that is the old rule); its finds are out-of-surface by construction.

**Blinding, honestly (M3).** Full blinding is impossible without editing the
treatment: BUDGET's text cites the diagnosis and calls the benefit predicted;
CONV's text is visibly older than the installed skill. Neither text names case 07
or any endpoint (grep-verified each build). The residual asymmetry is stated in
the report, both directions.

## 4. Subject: ikbr_tools, FCDD-T, with two custody rules

The method's declared domain (money paths, guards, kill switches) — the first
in-scope test in the programme. Variant pinned: **FCDD-T** (the subject's own).
H1 transfers to FCDD-X only as far as Beat 4 is variant-independent.

- **Strata (B6).** The hardened stratum is an **explicit file list frozen here at
  freeze time** (not "named in case_study.md", which is non-mechanical — it also
  names `ib_risk.py`). Both arms' skill text ships `references/case_study.md`,
  which documents the hardened modules' historical defects — an answer key for
  that stratum. Rule: **any finding matching a case-study-documented defect is
  excluded from the primary** and reported separately as a rediscovery.
- **Unit (m3, m5).** One *unit* = an explicit file set, enumerated per unit at
  freeze; "module" is not a size class. The term is *unit* throughout.

## 5. Isolation (B7) — the live-codebase envelope

Verified on this host: the tree contains `gateway/start_gateway_LIVE.sh`, an
`env.sh` that evals credentials from the ib_creds vault, and the operator's live
vault at `~/.config/ikbr_tools/{vault.json,vault.key}`. Therefore, per cell:

- a **scrubbed copy** of the tree — `gateway/` and credential-bearing scripts
  removed, the removal manifest deposited;
- **bwrap namespace isolation** (case 05 L1, verified on this host): no `$HOME`,
  no network beyond the model relay, disjoint workspaces (C23);
- verify-by-execution runs against the scrubbed copy only; anything needing a
  gateway is confirmed by trace or test double, never a live connection.

## 6. Outcomes, now computable

**Finding identity (B2).** A confirmed finding is a tuple
`(unit, site, demonstration)` — site = file plus function/clause; demonstration =
a deposited executable probe showing input → wrong behaviour. **Two findings
match iff their probes demonstrate the same wrong behaviour at the same site**
(the third party runs each probe against the other's site to decide; disputed
matches are reported as such, not silently merged).

**BLOCKING (B4), mechanical:** the demonstration shows a **wrong verdict or
wrong money-path action on a reachable input** — the skill's own HIGH ≈
reachable. Severity is assigned **only by the third party**, per a deposited
adjudication protocol (`tools/adjudicate.md`); arms report findings, never
grade them.

**Aggregation (B2).** Per arm, the finding set is the **union over its k
repeats**, with k equal across arms so union growth is symmetric; per-repeat sets
are also reported. **Missed** = in CONV's confirmed blocking union, within S,
absent from BUDGET's confirmed union **and** from BUDGET's named residuals. A
match to a BUDGET *residual* is the separate category **found-unconfirmed** —
law 12 produces residuals by design, and whether residual-naming suffices is
itself an outcome, not a miss.

**Censoring (M1).** A timeout-killed CONV cell is truncated convergence; it is
excluded from the primary and reported with its direction-of-bias note (censoring
can only shrink the miss count). The timeout is sized in the pilot against the
measured 18-round history.

**Cost (M4).** Headline accounting: **CONSUMED**, named here, now, before any
run; COMPLETING reported alongside. Materiality threshold: BUDGET:CONV ≤ 0.75 on
median CONSUMED cost per unit.

## 7. Pilot — gated on the thing H1 needs

k = 2 per arm on 2 units, excluded from inference. **Gate: ≥ 1 confirmed
BLOCKING finding** (not any-severity — the r1 gate could pass on hygiene trivia
while the primary ran on zero blocking findings).

**Informativeness (B3).** H1 is a universal negative; "missed none" bounds the
miss rate at roughly 3/b (95%) where b = CONV's confirmed blocking total. The
pre-registered floor: **if b < 15 at the end of the study, the quantitative claim
is not made** — the report states "the corpus cannot test H1 quantitatively" and
gives descriptive results. The pilot estimates b's rate; if it projects b < 15
at affordable n, the study stops at the pilot.

**Pilot-shopping (M5).** Unit selection order is pre-registered (descending size
within each stratum, alternating strata). If the pilot gate fails, **exactly one
redraw** of the next units in that order is permitted, and both attempts are
reported. k and n derive from pilot variance by a formula frozen with the
analysis script — never chosen after seeing scored data.

## 8. Bookkeeping

- Analysis script: `tools/analyse_case07.py`, deposited and dry-run against a
  real pilot cell **before freeze** (C5). Every reported number emitted by it
  (C10).
- **Finding ledgers are gitignored** (M7): `case07_attack_budget/ledger/findings/`
  never reaches the public remote — they document real defects in a live trading
  codebase; the tracked ledger carries their sha256 manifest.
- Model pinned by name in the freeze commit and verified per run from recorded
  usage, subagents included (C3, m4).
- Dual accounting with the mechanical death classifier; amendments append-only;
  ≥ 2 review rounds before any result is believed (C11).

## 9. Review round 1 (2026-08-27) — record

Seven blocking, seven major, five minor; **all accepted**. B1 the CONV arm was
not constructable as claimed ("identical except the stopping rule" was false
under both available constructions — r2 deposits the graft and names the delta);
B2 the primary was not computable (no identity/aggregation/residual rules); B3
H1 vacuously passable (gate now BLOCKING-severity with a b ≥ 15 floor); B4
BLOCKING undefined and unassigned (now mechanical, third-party only); B5 the
surface set confounded the comparison (now orchestrator-declared, out-of-surface
finds excluded); B6 the cell-facing skill ships the hardened stratum's answer key
(rediscoveries excluded from primary; stratum an explicit list); B7 no isolation
envelope against a live trading tree with reachable credentials (scrubbed copy +
bwrap + no-live-connection rule). Majors M1–M7 applied as §6–§8 rules. The
reviewer verified the diagnosis numbers quote correctly and named seven things
worth preserving; r2 preserved them. **Round 2 is owed on r2's repairs** — every
prior round found its blockers there.

## 10. Status

**DRAFT r2.** Owed before freeze: round 2, the scrub manifest, `SKILL_CONV.md`,
the adjudication protocol, the analysis script, the frozen strata and unit lists
— then the pilot, then the numbers this document still deliberately lacks.
