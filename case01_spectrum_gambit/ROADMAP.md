# CASE 01 — roadmap: what is left, and what is worth doing next

`REPORT.md` states interim conclusions from a partial run. This file is the
resumption plan. **Nothing here is blocked by findings** — the case was
concluded early for cost reasons under a Pro subscription; the operator
moved to a **Max plan on 2026-07-30**, so the throughput constraint that
forced the early conclusion no longer applies and any section below can be
picked up as-is.

Tooling is ready and interruption-hardened: `tools/run_resilient.sh`
(resume by real `session_id`, workspace preserved across attempts, quota
probe + wait-for-reset, failure classification) driven by
`tools/supervisor2.sh` (strictly serial). Prompt v3 mandates rolling
`STATE.md` checkpoints. See PROTOCOL amendments A4–A9 for the full history.

---

## A. Finish the frozen protocol (highest value per dollar)

Ordered by how much each buys the conclusion:

1. **bug01 / Arm A — clean re-run.** *The single most important gap.* The
   report's strongest pro-FCDD data point (A never fixed bug01) rests on a
   contaminated cell: attempt 1 was truncated by a since-removed $40 cap and
   a 2 h wall cap, attempt 2 died in the 11:39 API incident. Until Arm A
   gets one uninterrupted run at bug01, that finding is not safe to quote.
2. **bug07 pair (A + B)** — never run; the seventh class (mate/stalemate
   detection) is unrepresented.
3. **Blinded rubric grading (gate item 3)** — never run at all. Two fresh
   grader agents, arm labels stripped and order alternated by bug parity,
   scoring correctness-risk / clarity / test-quality 1–5. This is what turns
   "both passed the acceptance script" into "equivalent quality", which the
   cost comparison currently *assumes*.
4. **v2/v3 re-runs of the v1 cells** (A7 ruling, unfinished) so that
   review/attack rounds are actually closed and the review tail is counted.
   Cheaper alternative: keep the v1 rows and quantify the undercount by
   re-running **one** pair under v3 and measuring the delta.
5. **Replication (k = 2–3)** on at least bug04, where the gap (6×) is the
   widest and therefore the most likely to be single-run noise.

## B. Fix what the case exposed in the method's own packaging

- **Reviewer-model choice must be explicit** in the FCDD skill, not silently
  baked in (incident A5). TODO already filed at
  `~/.claude/skills/formal-contract-dev/TODO.md`; apply after this case
  closes so the measured method text stays frozen.
- **The step-1 package shipped a gate measured against a stale binary**
  (found by armB:bug02). Re-run `bridge/run_all.sh` on a clean rebuild and
  re-issue the step-1 claim set before reusing that contract anywhere.
- **Fix-vs-verification split**: instrument runs so the moment the fix first
  passes acceptance is timestamped. §2 of the report suggests the fix lands
  early and verification dominates; that deserves to be measured, not
  inferred, and it is the number a practitioner would actually budget on.

## C. New direction — Rocq/Coq contract + certified extraction (operator idea)

The natural next case, and a genuinely different point in the design space
from case 01's "prove *about* hand-written Z80" approach:

> Specify the contract in **Rocq (Coq)**, prove the properties there, and
> **extract executable OCaml** from the proved specification — so the
> extracted chunks are correct *by construction* rather than by conformance
> sampling. The interesting comparison is not cost-per-bug but **which
> defect classes become impossible** rather than merely detected.

Concrete shape for a case02:

- **Reuse the existing partial chess specification in Lean**:
  <https://github.com/dwrensha/Chess.lean> (operator-supplied, 2026-07-30).
  Case 01's `spec/Contract.lean` was written from scratch; a comparison
  against an independently authored spec is *itself* a finding — it directly
  attacks case 01's standing residual that spec and twin share one author.
  Decide deliberately whether case02 is Lean (reuse Chess.lean, extraction
  story is weaker) or Rocq (extraction story is the point, spec is new work).
- **Toolchain already present**: `rocq` MCP server + the `rocq:*` skills
  (prove/autoprove/golf/axiom-eliminator), and the
  **`verified-extraction-hardening`** skill, which exists precisely for the
  three leaks that make "extracted ⇒ correct" false in practice: numeric
  width remaps (Z → i64), FFI marshalling, and host-language coercion. Read
  that skill *before* claiming any extracted component is bug-free.
- **Honest framing to preserve**: extraction certifies the extracted core
  against *its own spec*. It does not certify the spec, the FFI boundary,
  the emulator, or the parts left in Z80/JS. The case must state which
  fraction of the system is actually covered — the same
  falsifiability-tiering discipline case 01 applied.
- **Cost question worth answering**: extraction moves cost from
  *per-bug verification* to *upfront specification*. Case 01 found FCDD's
  upfront never amortised because its marginal cost stayed high. If
  extraction drives the marginal cost of a whole defect class to ~zero, the
  crossover arithmetic changes qualitatively — that is the hypothesis.

## D. Housekeeping

- **D3 price pin**: `claude-opus-5` is absent from the frozen price table, so
  every cost column falls back to CLI-reported USD. Pin it (dated amendment)
  before any cross-case comparison.
- **Repo visibility**: `cosmindxu/fcdd-lab` is private because the answer key
  had to stay sealed. The key is now unsealed for grading; flipping to public
  gives the pre-registration credibility the commit history already supports
  (`gh repo edit cosmindxu/fcdd-lab --visibility public
  --accept-visibility-change-consequences`).
- **Workspace hygiene**: `~/fcdd_arms/` holds ~38 workspaces including
  `_prev_*` and `_try1_*` snapshots. They are grading evidence — the fixes
  verified in `REPORT.md` live there — so archive rather than delete.
