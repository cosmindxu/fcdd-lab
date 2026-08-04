# Worked exemplar — the ikbr_tools live watcher + whole-operation monitor

The arc FCDD was distilled from (2026-07-27 → 07-29). Repo: `/media/sf_Projects/ikbr_tools`. Read
these files as the canonical instance of each beat. Two systems, both FCDD:

- **R18** — a login-free multi-source day-loss dead-man for a live trading account (the SOURCE lane).
- **The ops monitor** — runtime verification of the WHOLE operating day (the MONITOR lane), built
  because R18's evidence soak was waived and monitoring became the safety instrument.

## Beat 1 — PROVE (kernel-checked spec of record)

- `tests/lean/Composite.lean` — the R18 safe-OR composite: 3-valued verdicts, no-suppression,
  all-blind⇒UNKNOWN, empty⇒UNKNOWN, OR-monotonicity, the identity `composite([v]) ≡ v` (the
  behavior-neutral refactor proof), plus the asymmetric-cap money-direction theorems. Zero-axiom
  fragment demonstrates the minimal-profile discipline.
- `tests/lean/DailyOps.lean` — the operating-day spec: `Conforming k t` over ~21 clauses (S1–S21),
  four day kinds, soak + telegram as ORTHOGONAL trace coordinates. Theorems: `spec_total`
  (satisfiability per kind), safety consequences (`halt_blocks_future_orders` = persistence ∘
  barrier-F), `incident_0605_nonconforming` (a REAL incident as a theorem), and the non-vacuous
  witnesses added by review (`cleared_halt_day_conforms` exercising the S3 rm-guard via `dite`;
  `latching_noLogin_conforms`). All profiles zero-axiom.
- `tests/lean/DayStop.lean`, `BreachConfirm.lean`, `DayStopCalibration.lean` — the invariant tiers
  (cap ceilings, the confirm state machine unbounded, a decision-conformity certificate).
- Fail-direction engineering in the code: `ikbr_tools/riskwatch_altsource.py` — every degraded
  input (missing cash, NaN/inf mark, unmarked held name, stale baseline, corrupt book, split, gap)
  maps to UNKNOWN, never CLEAR; the asymmetric plausibility cap (omit implausible GAINS, keep
  declines) chosen by recoverability. `ib_risk.py` `composite`/`enabled_verdicts` — the safe-OR.

## Beat 2 — TWIN (pure implementation)

- `ikbr_tools/opsspec.py` — the pure S1–S21 evaluator, a line-for-line twin of `DailyOps.lean`
  (same clause ids, boundary operators, constants; a frozen `Trace`; `evaluate()` with the window
  constants as overridable params defaulted to the model — the DST derivation seam).
- The R18 verdict math (`estimate_verdict`) is itself the pure core the shell (`_alt_shadow_verdict`)
  wraps.

## Beat 3 — BRIDGE (conformance suite)

- `tests/tests_opsspec.py` — witnesses conform; theorem-violating traces fail the RIGHT clause;
  single-field mutation coverage with EVERY clause negatively tested (the review found 5 uncovered
  and they were added); the O(day) latch-persistence scanner checked against a brute-force
  transcription of the Lean quantifier over **1024 patterns in the shipped gate** (a reviewer's
  one-off probe pushed the same assault to 65,536 with 0 mismatches — recorded in
  `OPS_MONITOR_SPEC.md`, but the gate carries 2^10, not 2^16).
- `tests/tests_formal_riskwatch.py` — the R18 composite's SMT proofs (z3+cvc5) tied to the shipped
  `ib_risk.composite` by an exhaustive tuple sweep; the Mechanism-A degraded⇒UNKNOWN conformance.
- Gate wiring: `run_tests.sh` (exit-code judged, `__pycache__` cleared first, doc-count gate via
  `tests_cli`).

## Beat 3.5 / 3.75 — SHELL + VALIDATE

- `scripts/ops_monitor.py` — the impure observation shell: classification from gateway-UP evidence
  (not launch attempts — a review fix), journal-laundering filters, per-episode halt-release
  synthesis, crontab-derived DST windows, DATED readonly-check records (source fix in
  `ib_risk.py`), judgeability gates, provenance + notes. Validated on real days: 2026-07-29 → exactly
  `['S1']` (the motivating incident, alone); the 07-28 rebalance day → only the documented pre-R18
  posture anachronism; Sunday → CONFORMING. (Separately, re-judging the real 6-latch 2026-07-15
  yields genuine historical catches — off-roster manual orders (S5) + an early watcher (S1) — and is
  what surfaced the per-episode-halt shell bug.)
- `scripts/r18_preflight.py`, `scripts/r18_monitor.py` — the mechanical preflight (exit-0 to arm,
  replacing the waived soak) and the detail monitor.

## Beat 4 — ATTACK (multi-agent adversarial review)

The campaigns are in the git history and the decision log — and their HONEST shape is the lesson,
so don't tidy it. R18 was NOT three clean rounds: it was ~nine reviews of a widening surface —
P0/P1 (F1) → readonly-check review (D11/D12) → anchor re-review (D13) → D14 (F1/F3/F4) →
RR-1/RR-2/RR-3 → a narrow "GO" (D18-era) → **then a full-code review that found NEW reachable
arming blockers A1 (confirm-streak seam) and A2/A3 (anchor)** → Fable re-review GO → whole-repo C/H
closure. That "reachable finds AFTER a GO" is the per-surface-convergence law (§16), lived: widening
the scope re-opened reachable findings. **Reviewer attribution (Law 5, so get it right): the R18
F1/RR rounds were reviewed by OPUS with Fable-quota-exhausted as the documented fallback** (D14, RR
entries) — the arc honestly recorded every fallback; do not retro-credit Fable. Fable genuinely ran
the LATER campaigns (the D15 4-agent full-code review, the D18 GO re-review, the 5-subagent C/H
closure) and the ops-monitor 4-lens review that returned "a good S1/S4/S5/S16 detector wearing an
S1–S18 badge" → fixes → the falsifiability tiering. Throughout, the author ground-truthed every
load-bearing finding by execution before accepting — and this skill's own four-lens review (which
produced these very corrections) was likewise Fable-attacked, Opus-adjudicated.

## Ledgers, deployment, laws

- `docs/design/READONLY_DAY_WATCHER.md` — the R18 decision log D1–D19 (every fork, rejected
  alternative + failure mode, assumptions; D19 = the soak WAIVER with its residual).
- `docs/design/OPS_MONITOR_SPEC.md` — the clause↔observable mapping, the shell honesty rules, and
  the **falsifiability tiering** table (monitored / attempt-adjacent / inert-until-soak /
  internal-consistency) — the "badge matches the detector" artifact.
- `docs/design/FORMAL_VERIFICATION_LEVELS.md` — the L1/L2a/L2g/L2b claim taxonomy.
- `planning/R18_ARMING_RUNBOOK.md`, `planning/live-cutover/ops-monitor.cron` — progressive
  enablement gates + the verify-where-it-runs deployment (the cron `cd` bug caught 5×, incl. twice
  against the author fixing it — the reason for "extract the exact payload, run from `$HOME`").
- `docs/handbook/trading_theory_handbook.tex` §22.4 "Runtime verification: proving the operating
  day" — the method written up in prose, with the honesty/tiering framing.
- Incidents-as-theorems: the 06:05 out-of-window restart (`incident_0605_nonconforming`); the
  v1.8.1 stale-bundle LATENT hazard (a fresh shell would have run the pre-dry-run 1.6.1 bundle;
  caught by extraction, no orders placed — version-content lockstep).

## The defects that BOUGHT each law (so the skill isn't abstract)

- Local-proofs-die-at-seams: the confirm-streak — safe-OR proved per-tick, but an armed alt CLEAR
  reset a gateway breach streak (A1). Fixed by a gateway-authoritative streak verdict + a
  monotonicity proof through the state machine.
- Badge-matches-detector: the ops monitor claimed S1–S18 but S6 was dead after night one, S2 saw
  0.26% of the session, S15/S17 were decorative — hence the tiering.
- Verify-where-it-runs: the stale-1.6.1 deb that a fresh shell would run instead of the dry-run-default fix (caught by extraction, fixed in v1.8.1); the cron `cd` bug (caught 5x).
- Degraded⇒safe: NaN marks reading CLEAR and washing out a real breach (R18 F1); the split /
  interior-gap producing CLEAR (A2/A3).
- Non-vacuous witnesses: `spec_total` first proved only by degenerate all-False witnesses (review
  M3), later given real cleared-halt / latching witnesses.
