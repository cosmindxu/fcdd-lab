# CASE 07 — is the ATTACK budget safe? (pre-registration, DRAFT r4)

**r3 applies review round 2** (§9b): five blocking, six major — the eighth
consecutive round in this lab whose blockers sat inside the previous round's
repairs, including three numbers r2 invented against its own rules-not-numbers
header (all three withdrawn below). Round 2's chief yield was a defect in the
LIVE METHOD, not the study: `references/lenses.md` still shipped the pre-law-12
stopping rule a full revision after Beat 4 changed — fixed in the live skill in
the same commit as this revision. r2 applied round 1 (§9).

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
history (§4) and the finding ledgers (§8). Both outcomes are results, **symmetrically scoped (r2 M6)**: refutation
falsifies the two-round default; confirmation confirms **the same default only —
on this subject, within declared surfaces, at the achieved resolution** — not
law 12's declared-budget principle in general.

## 3. Arms — the difference, stated exactly

Both arms receive a **deposited, per-cell skill text** (never the shared
`~/.claude` install — that would be cross-arm global state):

- **BUDGET** = the current skill verbatim.
- **CONV** = the current skill with the stopping-rule complex reverted — and the
  site list is **not hand-enumerated** (r2 listed "three sites", counted four, and
  missed at least three more: the §4 laws header naming law 12's evidence, law
  13's two references to law 12, and the lenses.md convergence block). The delta
  is built by **grep over `budget|law 12|converg`** across the skill AND its
  references, every hit dispositioned in the deposited diff. Decisions the grep
  forces, made here: **#16.5 (the review turnstile) is KEPT in both arms** — it
  postdates the frozen text but is not part of the stopping rule, and deleting it
  from CONV would add an undeclared second treatment; law 13's law-12 references
  are neutralised in CONV ("which law 3 forbids"), recorded in the diff; the laws
  header drops its law-12 clause in CONV. **Each arm's pack gets the matching
  `lenses.md`**: BUDGET the corrected budget-rule block, CONV the frozen
  convergence block (round 2 found BUDGET's own reference pack shipping the OLD
  stopping rule — a cell following its full pack could legitimately iterate past
  the cap, collapsing the arms). **Delivered-treatment check:** rounds executed
  per BUDGET cell ≤ its declared budget is a recorded outcome, not an assumption.
  The pack's file set is **enumerated** in the deposit and **excludes
  `TODO.md`**, which names the case-01 experiment and law 12's provenance (m2).
  Files: `arms/SKILL_CONV.md`, `arms/lenses_CONV.md`, `arms/PACK_MANIFEST.txt` —
  **owed before freeze, not yet deposited.**

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
- **relay topology, mechanical (round 2 M1):** network namespace fully unshared;
  the model relay enters by per-cell unix socket; **loopback is not host-shared**
  — the tree's tools default to `127.0.0.1:4002` (the live gateway's loopback
  port), so G1's probe **asserts 127.0.0.1:4001/4002 are unreachable from inside
  a cell** before any run;
- **scrub manifest, extended (round 2 M2):** besides `gateway/` — `env.sh` (evals
  the credential vault), **`.git`**, `CHANGELOG.md` and `docs/REVIEW_*.md` (the
  tree's own defect history: an answer key the case-study exclusion did not
  cover), and the **hardcoded live account id** (verified at `ib_autopilot.py`,
  `ib_safety.py`, `packaging/build_deb.sh`) redacted so it cannot flow into
  probes, ledgers or transcripts. The rediscovery exclusion (§4) widens from
  case-study-documented to **any tree-documented defect**;
- verify-by-execution runs against the scrubbed copy only; anything needing a
  gateway is confirmed by trace or test double, never a live connection.

## 6. Outcomes, now computable

**Finding identity (B2).** A confirmed finding is a tuple
`(unit, site, demonstration)` — site = file plus function/clause; demonstration =
a deposited executable probe showing input → wrong behaviour. **Two findings
match iff their probes demonstrate the same wrong behaviour at the same site**
(the third party runs each probe against the other's site to decide; disputed
matches are reported as such, not silently merged).

**BLOCKING, mechanical and now decidable (r2 M3):** the demonstration shows a
**wrong verdict or wrong money-path action reachable via a named caller**. Since
most of the 136 modules emit indicators, not verdicts, **the unit list is
restricted to verdict/money-path modules** — the guards, watchers, risk and
autopilot layer — so the definition is decidable on every unit. Severity is
assigned **only by the third party**: an **Opus adjudicator, model pinned in the
freeze commit, which sees the probes and the scrubbed tree and never an arm's
transcript** (r2 M5), per `tools/adjudicate.md` — owed before freeze.

**Aggregation (B2).** Per arm, the finding set is the **union over its k
repeats**, with k equal across arms so union growth is symmetric; per-repeat sets
are also reported. **Missed** = in CONV's confirmed blocking union, within S,
absent from BUDGET's confirmed union **and** from BUDGET's named residuals. A
match to a BUDGET *residual* is the separate category **found-unconfirmed** —
law 12 produces residuals by design, and whether residual-naming suffices is
itself an outcome, not a miss.

**Censoring — fail direction corrected (r2 M4).** r2 excluded timeout-killed
CONV cells, which can only shrink the miss count: a bias toward "safe" in a
safety study, the wrong fail direction by the skill's own law 1. r3: a censored
CONV cell renders its unit **NOT DECIDABLE** — the unit cannot support the safety
claim and is reported as such, never dropped. The timeout is sized in the pilot
against the measured 18-round history so truncation is demonstrably rare.

**Cost.** Headline accounting: **CONSUMED**, named here, now, before any run;
COMPLETING reported alongside; the statistic is **median CONSUMED cost per unit**
(H1's "materially lower" points here). **The r2 threshold 0.75 is withdrawn** —
it traced to nothing (the only measured ratio, $28.42/$48.33 ≈ 0.59, is a
within-arm subgroup, not bounded-vs-unbounded). The materiality threshold is a
freeze input with a **written derivation** from a declared tolerable bound.

## 7. Pilot — gated on the thing H1 needs

k = 2 per arm on 2 units, excluded from inference. **Gate: ≥ 1 confirmed
BLOCKING finding** (not any-severity — the r1 gate could pass on hygiene trivia
while the primary ran on zero blocking findings).

**Informativeness — r2's numbers withdrawn (round 2, B4).** The b ≥ 15 floor and
its "3/b (95%)" presumed b independent trials; misses **cluster** — the findings
only deep iteration reaches are exactly what a two-round cap misses together —
and b ≥ 15 was a 20% miss-rate ceiling presented as a safety floor with no
argument that 20% is tolerable. r3: the bound is stated **per unit** (rule of
three over units, the clustering unit), and the floor derives at freeze from a
**written tolerable-miss-rate argument**, not a round number. If the achievable
bound cannot meet that argument, the quantitative claim is not made and the
report says so.

**Pilot-shopping, and the gate's arm (r2 B5).** The gate counts confirmed
blocking findings **in the CONV arm** (the arm whose findings define b). Unit
selection order pre-registered (descending size within stratum, alternating
strata); one redraw, both attempts reported. The projection rule — estimator, CI
convention, and the **affordability ceiling as a formula** — is frozen inside the
analysis script before the pilot, and a 2-unit rare-event estimate is treated as
the order-of-magnitude signal it is: the pilot can **stop** the study, it cannot
alone justify proceeding past a failed floor.

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
not constructable as claimed (r2 promised the graft; **round 2 found the promise
itself false in tense — nothing was deposited — and the site list incomplete**;
r3 replaces enumeration with grep-built delta, still owed);
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

## 9b. Review round 2 (2026-08-27, Opus) — record

Five blocking, six major, six minor, five disposition mismatches; **all
accepted**; verbatim report deposited at `reviews/ROUND2.md` (its own m6 — round
1's verbatim text was not preserved, a gap now recorded rather than repaired).
The round's chief yield was a **live-method defect**: `references/lenses.md`
shipped the pre-law-12 stopping rule inside every FCDD cell's prompt pack a full
revision after Beat 4 changed — the treatment would not have been delivered by
the declared delta. Fixed in the live skill alongside this revision. Also: the
graft's site list replaced by a grep-built delta with a #16.5 ruling; the
probe-transfer identity test; BLOCKING restricted to verdict/money-path units
and its adjudicator named (Opus, pinned, transcript-blind); censoring flipped to
the conservative fail direction; **all three r2 numbers withdrawn** (0.75 traced
to nothing; b ≥ 15 was an unargued 20% miss ceiling on an independence assumption
the clustering structure violates); the pilot gate assigned to the CONV arm; the
scrub and relay holes closed (§5). **Round 3 is owed on the artefacts** —
SKILL_CONV, lenses_CONV, PACK_MANIFEST, adjudicate.md, the scrub manifest, the
unit lists and the analysis script — each of which will be written under review
pressure, which is where eight consecutive rounds found their blockers.

## 10. Status

**DRAFT r4 — the artefacts exist.** Built and deposited:

| Artefact | What it is |
|---|---|
| `tools/build_conv_arm.py` | builds the CONV pack from the **frozen→current diff**, 11 hunks classified (5 revert, 6 keep); grep was rejected as the enumerator because `law 12` misses *"laws 3 and 12"* and *"12 was bought by measurement"* |
| `arms/SKILL_CONV.md`, `arms/lenses_CONV.md`, `arms/DELTA.diff` | the CONV arm and the inspectable delta — **61 added / 12 removed lines**; the builder's residual check (no `declared budget`/`law 12`/`stop on coverage` survives) passes |
| `arms/PACK_MANIFEST.md` | the enumerated cell-facing file set; `TODO.md` excluded |
| `tools/adjudicate.md` | third party pinned (Opus, transcript-blind, arm-stripped), BLOCKING mechanical, probe-transfer matching, residual-specificity criterion |
| `tools/scrub_manifest.md` | what is removed and redacted, and the four assertions the build must pass |
| `tools/build_units.py`, `ledger/units.json` | **15 units, 5 hardened / 10 unhardened**, restricted to modules that DECIDE or ACT so BLOCKING is decidable |
| `tools/analyse_case07.py` | the analysis, **dry-run green on fixtures** |

**Two honest residuals in the artefacts**, recorded rather than smoothed:
`build_architecture_pdf.py` and `build_target_architecture_pdf.py` survive the
unit filter as false positives (they match on prose); the BLOCKING definition
filters them to zero, so they cost review budget and cannot corrupt the primary.
And C5's dry-run is against **fixtures, not a real pilot cell** — the real
dry-run is still owed.

Owed before freeze: **round 3 on these artefacts** (every one written under
review pressure, which is where nine consecutive rounds found their blockers),
then the pilot, then the derived thresholds.
