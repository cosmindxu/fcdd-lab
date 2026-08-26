# Step 0 — the requirement, in prose, with fail directions

**Frozen before any Lean was written.** This file is the artifact the formalization is
checked *against*; without it you would be validating Lean with Lean.

## R1 (requirement)

A trading decision may only proceed on quote evidence that is known-fresh. Each price
source yields a reading: either a readable quote with an age in milliseconds, or an
unreadable source. Given a staleness limit, the guard returns TRADE, BLOCK or UNKNOWN.

## Fail directions (per degradable input)

| Degraded input | Verdict it MUST map to | Why (recoverability) |
|---|---|---|
| No sources at all (empty evidence) | **UNKNOWN**, never TRADE | A blocked trade is recoverable by re-running; a trade on no evidence is not. |
| Source unreadable | **UNKNOWN**, never TRADE | "We could not tell" is a real state and must not collapse to SAFE. |
| Any source readable but older than the limit | **BLOCK** | A *known* stale quote is DANGER, and DANGER wins over "could not tell". |

Three-valued on purpose (SAFE/DANGER/UNKNOWN), composed with a safe-OR: any BLOCK wins;
absent a BLOCK, any UNKNOWN wins; TRADE requires positive fresh evidence from every source.

## Safety properties

* **P1 no-vacuous-trade** — empty evidence never yields TRADE.
* **P2 block-dominates** — if any reading is known-stale, the verdict is BLOCK, whatever
  else is present.
* **P3 unknown-never-trades** — absent a stale reading, any unreadable source yields UNKNOWN.
* **P4 trade-needs-evidence** — TRADE implies a non-empty reading set with no stale and no
  unreadable member. (The converse of P1–P3: nothing else can produce a TRADE.)
* **P5 limit-monotone** — tightening the limit never trades where a looser limit blocked.

## Non-vacuity obligation

Every verdict class must be *reachable*: exhibit a witness for TRADE, for BLOCK and for
UNKNOWN. A spec no input can drive into a class proves its theorems about that class for
free.
