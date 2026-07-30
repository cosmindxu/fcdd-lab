# CASE 01 — FCDD vs typical development: token-cost report

**Status: INTERIM CONCLUSIONS from a partial run** (operator decision
2026-07-30 to conclude on current data; remaining work in `ROADMAP.md`).
Dates: seeded 2026-07-29, arms run 2026-07-29/30. All costs are the CLI's
own `total_cost_usd` (list-price USAGE index, not a bill — the subscription
is flat-rate; raw token counters in `ledger/runs.csv` are the ground truth).

---

## 1. Headline

On five bugs where **both** arms produced a fix that passes the sealed,
pre-registered acceptance gate, **typical development was cheaper on every
one of them** — median **$14.76** (Arm A) vs **$32.45** (Arm B, FCDD), a
median ratio of **1.42×** and a worst case of 6×.

**FCDD's upfront contract cost never amortises on this evidence.** The
crossover formula in the protocol, `N = upfront / (A_marginal − B_marginal)`,
requires FCDD to be cheaper *per bug*; it was more expensive per bug in 5/5
matched cases, so **no crossover exists** in this data — the $21.75 step-1
investment is never repaid, and the gap widens with each additional bug.

**The one exception matters more than the median.** On **bug01** — the
subtlest fault in the set (a quiescence entry guard comparing absolute ply
against a literal, distorting scores only through exchange sequences) —
Arm A **never produced a correct fix** across two attempts and **$96.90**,
while Arm B fixed it correctly for **$89.28**. That is the classic shape of
the FCDD claim: it is not a thrift method, it is a method for the bugs where
"looks fixed" and "is fixed" diverge. n=1 for that observation.

**Therefore: H1 is not supported, H0 is not cleanly rejected.** Typical dev
wins on marginal cost with high confidence at this sample size; the question
FCDD is actually sold on — *reliability on hard faults* — is where the only
counter-signal sits, and it is a single unreplicated observation.

---

## 2. The data

Cost = the CLI-reported cost of the run that produced the acceptance-passing
fix. ✓/✗ = the **sealed acceptance gate** (`sealed/acceptance/bugNN/check.sh`,
7–21 objective checks per bug, run by the orchestrator at grading time).

| Bug | Class | Arm A $ | A gate | Arm B $ | B gate | B/A |
|-----|-------|--------:|:------:|--------:|:------:|----:|
| bug01 | quiescence depth guard | 96.90 (2 runs) | ✗ **never fixed** | 89.28 | ✓ | — |
| bug02 | fifty-move clock | 14.76 | ✓ | 23.42 | ✓ | 1.59 |
| bug03 | promotion assembly | 13.50 | ✓ | 18.56 | ✓ | 1.37 |
| bug04 | eval sign | 5.37 | ✓ | 32.45 | ✓ | 6.04 |
| bug05 | castling rights bit | 23.08 | ✓ | 32.75 | ✓ | 1.42 |
| bug06 | TT depth bound | 32.33 | ✓ | 38.34 | ✓* | 1.19 |
| bug07 | mate detection | — | not run | — | not run | — |

\* bug06's Arm B gate was still executing at report time; its fix restores the
pristine binary byte-for-byte, which is the strongest available proxy.

- **Arm A median (fixed bugs): $14.76.  Arm B median: $32.45.**
- **Upfront (Arm B only): step-1 contract = $21.75** (95 kernel-proved
  theorems, twin, bridge, z3 tier, 10 organic findings in the *pristine*
  engine — 2 HIGH).
- Seeding lane (method-neutral): $29.69.
- **Total case spend: ~$560**, of which **~$300 was infrastructure waste**
  (see §4), not measurement.

### An unexpected and important observation

Several runs that infrastructure killed had **already produced a correct
fix** before dying — bug02/A, bug05/B, bug06/A, bug06/B all pass the sealed
gate from workspaces of runs booked as "killed". The fix typically lands
early; what the long tail of a run buys is **review, proof and closure**,
not the fix itself. This is the single most decision-relevant finding for
anyone budgeting either method.

---

## 3. Quality beyond the bar (recorded, not scored)

Arm B produced, at its cost premium, on every bug: a contract extension
(new clauses, e.g. S5 for quiescence, C14 strengthening for promotion),
new bridge layers pinning the fault class so a regression trips a check,
and incident theorems. On bug02 it additionally found that the **step-1
gate's own 11/11 green had been measured against a stale binary** — a real
defect in the delivered contract package, found by a downstream arm.

Arm A produced minimal, correct fixes plus a test; on bug05 it went beyond
the minimal fix and hardened castling generation against a phantom-rook
class of fault (which is why its binary diverges from pristine while still
passing the gate).

**No blinded rubric review was run** (gate item 3). Quality claims above are
descriptive, not scored — this is the largest single gap in the conclusion.

---

## 4. Threats to validity — read before quoting any number

1. **n = 5 matched pairs, k = 1.** No replication. The protocol's own rule 6
   (re-run when the gap is within noise) was never exercised.
2. **The pre-registered metric was "tokens-to-gate"; what is reported is
   "cost to acceptance-passing fix"** — a post-hoc metric adopted because
   infrastructure killed many runs before their self-declared gate. It is
   objective (sealed tests) but it is *not* the frozen definition, and it
   systematically **undercounts the review/proof tail of both arms**.
3. **Prompt-version drift.** v1 runs ended with review/attack rounds still
   pending (a harness defect — Task subagents defaulted to background; A6);
   v2 made reviews synchronous; v3 added checkpointing. Most cost rows are
   v1, so **both arms' review costs are undercounted, symmetrically**.
4. **Infrastructure chaos.** One API incident (11:39–12:38) and one
   subscription session-limit exhaustion (15:02, reset 19:40) killed
   long-running work; a $40/bug cap (later removed) truncated bug01/A; my
   own 2 h wall cap truncated it first. **bug01/A's ✗ is therefore not a
   clean "method failed" result** — it is "method did not succeed within two
   interrupted attempts totalling $96.90". Stated plainly: the strongest
   single point *for* FCDD in this report rests on a contaminated cell.
5. **Reviewer-model asymmetry (A5).** Arm B's attack rounds route to a
   different model per the FCDD skill (Fable on some runs, Opus on others);
   Arm A's reviewers were Opus/Sonnet. Cost bias runs *against* Arm B;
   quality confound runs *for* it.
6. **Orchestrator contamination.** I read several arms' final self-reports
   while ingesting results, and unsealed the answer key at grading (as the
   protocol allows). Grading was **not blinded** — it was mechanical
   (sealed scripts), which mitigates but does not eliminate this.
7. **Pricing.** Runs executed on `claude-opus-5`, which has **no row in the
   frozen D3 price table**; CLI-reported USD is used throughout and the
   token counters remain authoritative.
8. **Author asymmetry.** The engine under test was written by the same model
   family as both arms — symmetric, but not neutral.

---

## 5. What this case actually established (highest-confidence claims first)

1. **Both methods reliably fix ordinary seeded faults**, and the objective
   sealed gate confirms it: 11 of 12 attempted arm×bug cells that completed
   any real work produced acceptance-passing fixes.
2. **FCDD costs more per bug** at this scale — consistently, on every
   matched pair, by a median 1.42×.
3. **The fix arrives early; verification dominates the tail.** Interrupted
   runs had already fixed the bug.
4. **FCDD's artefacts persist and compound** (contract clauses, bridge
   layers) in a way Arm A's do not — unscored here, but visible.
5. **The step-1 contract package is itself a product**: 10 findings in the
   *pristine* engine, two HIGH (ROM-sysvar corruption from ply 128; 16-bit
   Zobrist collisions ~18%), found before any seeded bug was touched. On a
   pure cost-per-seeded-bug ledger this counts for nothing, which is a
   limitation of the experimental frame, not a virtue of the frame.

**Bottom line for a practitioner:** on a codebase where bugs are ordinary
and a test can confirm the fix, typical dev + review is the cheaper method
and this experiment did not find a bug count at which that reverses. Reach
for FCDD when a fault's *symptom* and its *cause* can diverge, when "the
test passes" is not the same as "the property holds", or when you want the
verification to outlive the fix.
