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
  Verified 2026-07-30: **Lean 4, self-described incomplete** — board
  representation, move legality, turn tracking, checkmate detection, plus a
  `get_next_move` tactic backed by Stockfish and worked proofs of mate
  puzzles ("Morphy mates in two"). So it is oriented to *proving mate
  positions*, not to specifying an engine: the rules/legality/mate layer
  overlaps case 01's C1–C6/C11 well, while the strategy layer case 01 cared
  about (search termination, eval antisymmetry, alpha-beta ≡ minimax, TT
  soundness) is out of its scope. Highest-value use is therefore **as an
  independent oracle**, not as the source of truth: differential-test our
  spec's `genLegal`/terminal decisions against it. That directly attacks
  case 01's standing residual (spec and twin share one author) in a way no
  amount of internal review can.

- **Lean → Rocq bridge**: <https://github.com/rocq-community/rocq-lean-import>
  (operator-supplied). Verified 2026-07-30 — and it does **not** license the
  obvious plan. It makes Rocq act as a Lean typechecker by translating
  **Lean export files** (`lean4export`) into Rocq declarations: inductives,
  constants, axioms, definitions *and* type information. But it is
  explicitly **experimental alpha**, its own README reports that
  **extraction is broken for some constructs**, stdlib needs conversion
  checking disabled to get through (43 s), and **mathlib is intractable**
  (~10 GB RAM, 11,867 of 66,400 entries skipped). Since almost every Lean 4
  project of this kind pulls in mathlib, "import Chess.lean, extract
  certified OCaml" is a **hypothesis to test cheaply, not a plan to adopt**.

  **Spike before committing (≤1 session):** (1) does Chess.lean depend on
  mathlib, and how deeply? (2) does `lean4export` + `Lean Import` survive
  that dependency set at all? (3) does Rocq extraction produce OCaml for the
  imported chess definitions specifically, or hit the broken-construct path?
  Any red ⇒ fall back to Path 1 below and keep Chess.lean as the oracle.

- **Three candidate paths, pick after the spike:**
  1. **Rocq-native spec + `Extraction` to OCaml** (recommended default) —
     extraction is a first-class, well-trodden Rocq feature; cost is that
     the spec is new work. Chess.lean still serves as the external oracle.
  2. **Stay in Lean** and reuse Chess.lean directly — cheapest specification
     path, but Lean's compilation to C is *not* the same guarantee as Coq's
     extraction-from-proof, so the headline claim weakens to "verified spec,
     conventionally compiled".
  3. **Chess.lean → rocq-lean-import → Rocq → OCaml** — the only path that
     gets both reuse *and* certified extraction, and the one the evidence
     above says is most likely to fail. Attractive enough to spike, too
     fragile to plan around.
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
