# The gap upstream of Beat 1: coverage of stated intent

**2026-08-26.** A proposed addition to FCDD, of the same kind as
`ATTACK_BUDGET_DIAGNOSIS.md` — derived from a gap the method admits in itself,
with a checkable mechanism and one worked precedent already in this repository.
**Status is stated up front and is weaker than the ATTACK note's: that one was a
measured diagnosis with a predicted benefit; this is a _derived_ diagnosis with a
predicted benefit and a single supporting execution.**

## 1. The gap, in the method's own words

> **It proves COHERENCE, never CORRECTNESS-OF-INTENT.** The kernel proves the
> spec is self-consistent and its consequences follow; it cannot prove the spec
> is the RIGHT spec. FCDD has **no GENERAL hazard-analysis beat** — where P1…Pn
> come from is on you (FMEA/STPA/threat-modeling).

Beat 0.5 already claims one slice of this back: operational/deployment
constraints, on the argument that they are *deducible* by combinatorial mission
analysis rather than requiring open-ended hazard imagination. That beat exists
because the R2 incident proved the slice expensive, and it is the right shape.

**What remains uncovered is not a slice of hazards — it is an obligation.**
"On you" is not an interface. Everywhere else the method demands obligations with
mechanical exits: a decision ledger, an assumption ledger, a fail direction per
degradable input, a declared attack budget. There is no analogous obligation for
**clause provenance and coverage**, and that is the one place intent enters the
system.

## 2. Three things are bundled under "intent", and only one is unprovable

| | Status |
|---|---|
| **Correctness of intent** — is this the spec the world actually needs? | Genuinely unprovable. Intent lives outside the formal system |
| **Consistency** — does the spec contradict itself; do its consequences follow? | The kernel already owns this |
| **Coverage of _stated_ intent** — does every stated requirement have a clause, does every clause have a source, and does the clause set **pin** behaviour rather than merely constrain its shape? | **Mechanically checkable, and currently unowned** |

The disclaimer in §5 is precise about the first and silent about the third. The
silence is the defect.

## 3. Why this must NOT be a beat

A hazard-analysis beat would violate two of the method's own rules.

- **Falsifiability tiering (law 3): the badge must match the detector.** A
  hazard-analysis beat cannot falsify *"we missed a hazard."* Its exit condition
  is unbounded judgement, so it could carry no honest badge.
- **Law 12: no unbounded loop in the method.** A beat whose stop condition is
  "we have thought of enough hazards" is exactly the defect law 12 was added to
  remove from Beat 4 — priced only in arrears.

Adding an uncheckable beat to a method whose entire value is checkable exits
would corrupt the property that makes it worth using. There is also a
composition argument: FMEA/STPA/HAZOP are mature separate disciplines, and a
method that absorbed them badly would be worse than one that names the
dependency.

**So the fix is an interface, not an activity.**

## 4. The proposal: four obligations, each with its honest tier

| # | Obligation | Falsifies | Cannot falsify |
|---|---|---|---|
| 1 | **Provenance.** Every clause P1…Pn carries a tag naming its source: a stated requirement, a real incident (law 6), or a named generator (e.g. Beat 0.5's mission products) | a clause with no stated source | that the source was the right source |
| 2 | **Bidirectional traceability.** Every stated requirement maps to ≥ 1 clause; every clause maps to ≥ 1 requirement. Orphans in either direction are named residuals, not silence | an uncovered requirement; an unmotivated clause | a requirement nobody wrote down |
| 3 | **Declared completeness scope.** "These hazards, by this technique, and here is what we did not consider" — a declaration, never a proof | that the scope was never written down | that the scope is adequate |
| 4 | **Pinning, measured by clause-naming mutation.** Mutate the *twin*; require a **named clause** to reject each mutant. The mutation lands on the implementation, the inference is about P1…Pn: a mutant no clause rejects is a coverage gap, not a code bug | a property set that constrains shape without pinning value | common-mode error between requirement and clause |

Obligations 1, 2 and 4 are programs. Obligation 3 is explicitly a declaration,
and **saying so is the point** — it is the same move the method already makes
when it says the bridge *samples* agreement and is not a refinement proof.

> **Correction, same day.** An earlier wording of obligation 4 said "mutate the
> clause set, not the implementation". That misdescribes the mechanism its own
> evidence uses: `twin.py` carries the six mutation hooks and `StaleQuote.lean`
> carries none. The mutation is applied to the **twin**; what makes it a
> *coverage* test rather than a conformance test is the requirement that a
> **named clause** reject it.

## 5. The worked precedent: obligation 4 has already caught a real gap

`method/pipeline_proto/` ran one small requirement end to end. P1–P5 were written
in prose, formalised, and proved first. Then the bridge mutation `M4_boundary`
(`>=` for `>` in `stale`) **survived every layer** — the reachability witnesses,
the theorem mirrors, and a 1,200-case exhaustive sweep.

The reason is exactly obligation 4's target: **P1–P5 constrained the _shape_ of
the verdict but never pinned _where_ fresh becomes stale.** An off-by-one at
`age == limit` was invisible to all of them. P6 (`age == limit` is fresh) was
added in response, and M4 is now caught by name.

That is coverage-of-intent measured by execution, in this method, on a real
clause set — and reading the spec would not have found it. It is one data point,
and it is the only one.

## 6. What this does and does not buy

**Does:** the method can then state something it currently cannot — *every stated
requirement has a clause, every clause has a source, and the clause set pins
behaviour rather than merely constraining it.* That is a real strengthening of
the coherence claim toward intent, and it makes the residue **named** instead of
invisible.

**Does not:** it remains coverage of *stated* intent. A need nobody wrote down
stays unreachable by any of this, and §5's disclaimer is right about that. The
honest formulation is therefore not "FCDD now covers intent" but:

> FCDD cannot prove the spec is right. It can prove the spec is complete against
> what was stated, traceable to why each clause exists, and strong enough to
> reject a mutation of itself.

## 7. Status and what would test it

**Tier: derived diagnosis, predicted benefit, N = 1 supporting execution.** The
ATTACK-budget change was adopted on 56 measured runs; this has one mutation
result. It should be labelled that way wherever it is used, and the honest test
is a study in which requirement-level gaps — not code faults — are seeded, and
the outcome is how many *stated requirements* each arm's artefact actually
enforces. That is the study `case05_prevention/PROPOSAL.md` §11 concludes it
should have been all along, and it puts mis-specification inside the measurement
instead of leaving it an untestable confound.

---

## 8. The objective the method never stated (2026-08-27)

Law 13 closes the *coverage* half of the spec↔intent seam. Operator observation,
and it is the more fundamental half: **the method carries narrowing devices
without ever declaring narrowing as an objective.**

Prose underdetermines. Two competent engineers reading one requirement resolve
its silences differently, silently, and both believe they implemented it. The
value a contract is supposed to deliver is that **the interpretive freedom gets
spent explicitly and once, upstream**, instead of implicitly and differently in
every implementation. Not "proofs are good" — *the space of behaviours consistent
with the artefact is narrower than the space consistent with the prose*.

The devices are all present and none of them says so: fail directions per
degradable input, 3-valued logic with safe-OR composition, Beat 0.5's elicitation
of user-known-but-unspoken constraints, law 13's traceability. Because the
objective was never named, nothing checked whether the narrowing occurred — **and
this programme spent two studies measuring dispersion of _cost_ when the claim
was about dispersion of _interpretation_.** That is the sharpest single
consequence of leaving an objective implicit.

**The checkable form is the missing dual of an existing rule.** `spec_total`
requires every *verdict class* to be reachable. Nothing required every *input
class* to be decided — and that direction is exactly where prose leaks through.
An undecided input class has not been narrowed; it has been deferred to whoever
writes the code. Hence **law 14**: input totality (every input class mapped to a
declared verdict, with "we do not decide this" legitimate only when written down
and mapped conservatively) plus an **interpretation ledger** recording every
place the prose admitted more than one reading.

**Motivating defects, both real:** R2 — nobody modelled watcher-start ×
gateway-not-yet-up, an undecided input class that cost three false latches; and
case02's measured residue, **23 distinct specification files from 28 runs of the
same task**, which is what an unnarrowed space looks like when you count it.

**Honest tier: governing principle with defect motivation, not a measured
benefit.** Whether formalising actually narrows the behaviour space is an open
empirical question — and it is the one `case06` is designed to answer, by
measuring inter-run agreement on *underspecified* inputs, where there is no right
answer and therefore nothing to leak.
