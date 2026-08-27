# CASE 06 — does formalising narrow the solution space?

**STATUS: DRAFT r1, not frozen, nothing built.** Supersedes
`case05_prevention/PROPOSAL.md`, which is retained rather than deleted: four
adversarial review rounds on a design that had to be abandoned is the most
instructive artefact this programme has produced about designing these studies,
and every constraint below was bought by one of its findings.

---

## 1. The claim, corrected twice

Cases 01 and 02 measured the dispersion of **cost**. Cases 04 and 05 were built
around **prevention**. Neither is the method's claim:

- **"predictability" appears zero times** in the frozen skill text case 01
  measured.
- **"prevent" appears twice, both times to disclaim it** — *"It caught the hollow
  monitor; it did not prevent it. FCDD's value is late (adversarial review) as
  much as early (proof)."*

What the method now states, as of 2026-08-27 and because this programme's own
analysis forced it (`method/INTENT_COVERAGE.md` §8), is an **objective**:

> Prose underdetermines. Two competent engineers reading one requirement resolve
> its silences differently, silently, and both believe they implemented it. The
> spec's job is to spend that interpretive freedom **explicitly and once,
> upstream** — the space of behaviours consistent with the artefact should be
> narrower than the space consistent with the prose.

**H1.** Given one frozen prose requirement, independent runs of the FCDD arm
produce implementations that agree with each other **more** than independent runs
of the ordinary arm do, on inputs the prose does not determine.

**H0.** They agree equally. Direction is pre-specified; the test is two-sided,
and a result showing FCDD *less* convergent is a real outcome (§7 records prior
evidence pointing that way).

Honest status of the objective: **governing principle with defect motivation, not
a measured benefit.** That is exactly what this study is for.

## 2. The primary outcome needs no oracle — which is the design's best property

Three disjoint scenario classes:

| Class | The prose… | Role |
|---|---|---|
| **Specified** | determines the answer | **coverage gate.** Both arms are expected to score high; that is fine and expected |
| **Delta** | states something that contradicts what a model "knows" | **mechanism probe** (§5, P3) |
| **Underspecified** | does **not** determine the answer | **the primary** |

On the underspecified class there is no right answer, so the measurement is
**within-arm pairwise behavioural agreement across runs**.

**Consequence: the primary requires no ground truth.** There is no answer key, no
sealed corpus, no custody problem, no commit-reveal. **Nothing to steal.** The
failure class that voided case 04 and consumed four review rounds becomes
*unrepresentable* rather than guarded against — a structurally better property
than any of case 05's five revisions bought.

## 3. Subject: FIDE plus a frozen delta

**Requirements = numbered FIDE articles** (external, canonical, authored by
nobody here — the strongest anti-circularity property available for traceability)
**plus a small lab-authored delta**: e.g. castling removed, en passant permitted
after any double-step, a modified draw-claim precedence, an altered repetition
key.

**Why the delta, and why it is not artificial.** Chess movegen is
training-saturated; round 3A named that as a fatal objection to plain chess, and
it does not go away. The delta **turns saturation from the threat into the
difficulty source**: the arm must notice where the spec overrides what it knows.
*"Implements what it remembers rather than what was specified"* is a coverage
failure — a stated requirement not enforced — and it is silent by construction,
because remembered behaviour is self-consistent and passes every ordinary test.

That is also the realistic analogue. Legacy quirks, regional rules, protocol
errata: **the spec says something surprising and the implementer's intuition
quietly wins.** That is where silent failure actually lives.

**Oracle feasibility, verified on this host:** a custom variant is a
`chess.Board` subclass — overriding `generate_castling_moves` took five lines and
gave 48 → 46 moves on Kiwipete. Roughly that per delta. Lab-held, unpublished,
underivable from memory.

## 4. Arms

Both receive the identical frozen prose (FIDE subset + delta), the same crate
interface, and the same definition of done: *"you assert R1…Rn are enforced."*

- **Arm A — ordinary development**, plus a **decision log**. The log exists to
  balance deliberation, not to add formality: without it the study measures
  *"writing a spec is slow and deliberate"* and calls the result formalism (§7).
- **Arm B — FCDD** per the skill, including law 13 traceability and law 14 input
  totality with its interpretation ledger.

**Anti-circularity — r1 refuted the drafted version and supplied the fix from the
skill's own wording.** Tag-existence is not a program: a circular specification
(`legal p m := m ∈ genLegal p`) can tag every requirement ID **honestly**, because
`genLegal` does implement them all, and "traces to nothing" holds only under a
semantic reading of the tag — a judgement, which C1 forbids.

**The mechanical form, adopted:** Beat 3 already requires mutations to trip
**exactly** their clause. So: **a mutant derived from requirement Rᵢ must be
rejected by a clause tagged Rᵢ, and by no other.** A monolithic circular spec
fails that immediately — one clause rejects everything, so selectivity is zero.
Freezing the **requirements** rather than the theorems still leaves the arm doing
FCDD's actual work; selectivity is what removes its ability to self-certify.

## 5. Measurements

| | What | Note |
|---|---|---|
| **P1 primary** | pairwise behavioural agreement within arm, on underspecified inputs | **r1: NOT YET A MEASUREMENT.** No comparator, no equivalence relation, and C(k,2) pairs are not independent observations. Must be redefined with the *run* as the unit, a canonical per-scenario output serialisation, and a scenario-paired permutation test. **Two further defects:** it is winnable by law 14's blanket conservative default (which the treatment text itself prescribes — see the skill's recorded interaction), so agreement must be partitioned into *by-default* vs *substantive*; and it is unconditioned on coverage, so runs that all implement remembered castling despite the delta win the primary while violating the spec |
| **P2 gate** | coverage on specified + delta requirements | both arms expected high; a floor, not a discriminator |
| **P3 mechanism** | coverage split **inherited vs delta** | **pre-registered prediction: FCDD's advantage concentrates on delta items** — a clause you must *trace* beats a habit you *follow*. Inherited items should show little difference |
| **P4 upstream** | do Arm B's *specs* agree with each other, and does spec agreement predict implementation agreement? | this is the funnel actually funnelling, not a correlation |
| **P5 review** | bounded ATTACK (law 12 budget) on both arms: what review finds that the artefact's own evidence missed | tests the claim the method *does* make — value is late |
| Cost | dual COMPLETING / CONSUMED accounting; peak RSS via cgroup `memory.peak` | case 04's lesson: excluding infrastructure deaths prices away a method's failure rate |

P3 is the sharpest thing here: a named mechanism with a named direction,
falsifiable in one study.

## 6. Gates and kill criteria (inherited, and they are the four rounds' real yield)

- **G0 — instrument mutation-calibration.** Mutate the **twin**; require a
  **named clause** to reject each mutant. A mutant no clause rejects is a coverage
  gap in P1…Pn, not a code bug. (Corrected mechanism: `twin.py` carries the
  mutation hooks, the spec file carries none.)
- **G1 — isolation.** bwrap namespace absence (verified on this host: oracle
  reachable over a bound UNIX socket, network blocked, lab tree and `$HOME`
  absent), **disjoint per-cell workspaces**, and the **two-cell concurrent
  probe** — cell 1 writes a nonce, cell 2 must not reach it.
- **G2 — pilot dual rule**, with a stated binomial decision rule and k sized to
  it, not asserted.
- **G3 — adversarial review of the frozen text before freezing.**
- **Kill criterion (case 05's criterion 6, carried):** *the underspecified class
  must actually produce disagreement in pilot.* If both arms converge on it
  anyway, there is nothing to measure and the benchmark is the finding — declared
  in advance, at design-time cost.

## 7. Confounds and prior evidence against, named now

1. **Deliberation, not formalism.** Mitigated by Arm A's decision log; if the
   effect disappears with it, that *is* the finding.
2. **Prior evidence — and r1 caught this citation being one-sided in the
   direction that flattered the sceptical reading.** r1 of this document cited
   case 02's *"23 distinct specification files from 28 runs"* as evidence against
   narrowing, and omitted the comparator its own source file deposits:

   > arm A (test scripts): 28 runs, **28 distinct**
   > arm B (Contract.lean): 28 runs, **23 distinct**
   > *"On this measure the CONTROL arm diverged more, which is the opposite of
   > what a one-sided reading of the treated arm alone would suggest."*
   > — `case02_predictability/ledger/SPEC_DIVERGENCE.txt`

   So the prior evidence, read whole, is **weakly for H1**, not against it — and
   case 02's own article had already corrected this exact error once ("an earlier
   draft called FCDD's artefact 'the least reproducible thing in the study' …
   that is false"). Repeating a correction the repository already contains is the
   programme's own thesis operating on its author. The honest statement: neither
   arm converged on its authored artefact, the treated arm converged *somewhat
   more*, and the measure is file-level and comment-sensitive, so it is weak
   evidence in either direction.
3. **Underdetermination must be engineered.** Case 02's 56 runs produced a
   byte-identical binary because a single-byte fault is fully determined. Without
   deliberate underspecification there is no variance to measure — case 02 is the
   null case, and proves the requirement.
4. **Sampler near-determinism** inflates agreement legitimately; measure
   *effective distinctness*, not variance alone.
5. **The lab authors the delta**, so we control difficulty. Deltas are derived
   from documented spec-surprise classes and pre-registered before any pilot.
6. **Training saturation persists on inherited items** even though the delta
   turns it into signal.

## 8. What this could and could not license

**Could:** *formalising a stated requirement narrows the behaviour space, and the
narrowing concentrates where the spec contradicts prior knowledge.* That is the
method's newly-stated objective, tested.

**Could not:** anything about money paths, kill switches or auth closure — the
method's actual domain. This is one domain, chosen because the instrument is
cheap and the assets exist, and the scope statement belongs in the abstract.

## 9. Review record

- Round 1: owed. Nothing here has been adversarially reviewed, and this
  programme's record is that every round finds its blocking defects inside the
  previous round's repairs.

---

## 10. Review round 1 — two lenses, ten blocking findings

1A (science) and 1B (subject/mechanism/operations) ran independently, no shared
context. **Ten blocking findings, three of them converged.** Status: **r1 is not
freezable.**

### Converged — found independently by both

| Finding | Disposition |
|---|---|
| **The delta converts saturation for P2/P3 but NOT for the primary.** On underspecified inputs both arms can converge on the canonical resolution held in the weights (python-chess's choices are the de-facto standard and saturate training data). The escape — locating underspecification in delta×FIDE interactions — makes the lab the author of both the delta *and* what counts as undetermined, re-importing the artefact-target problem for the one measurement that claimed to have nothing to steal | **Accepted. This is the design's central unresolved risk** and it is not fixable by wording |
| **Traceability is tag-existence, not a program** — a circular spec tags every requirement ID *honestly* | **Accepted; fixed** with the skill's own Beat 3 wording: a mutant from Rᵢ must trip a clause tagged Rᵢ **and no other**. Selectivity is what a monolithic circular spec cannot fake |
| **Nothing classifies an input as "underspecified"** — by lab judgement (C1 forbids) or by a dual-reference rule already refuted as uncomputable | Accepted; needs a deposited classifier and a probe set frozen before any cell runs |

### 1A — the science

- **The primary is not yet a measurement**: no comparator, no equivalence
  relation, and C(k,2) pairs are not independent observations. The
  unpowerable-primary class that fired in case 05 rounds 1, 2 and 3, now at the
  primary itself.
- **The primary is winnable by law 14's blanket conservative default** — a rule
  the treatment text *prescribes*, separable from formalisation entirely.
- **Agreement is never conditioned on coverage**, so converging on a wrong
  reading scores as success.
- **"Nothing to steal" is true only of P1**; P2 and P3 need the lab-held delta
  oracle, which is the same answer-shaped artefact whose custody consumed case 04.
- **Treatment-side memorisation** (public formal chess artefacts) inflates
  *within-B* agreement specifically — it points toward H1 and kill criterion 6,
  which fires only when *both* arms converge, cannot catch it.
- **The treatment text leaked the endpoint**: the skill named this study and the
  method note stated its exact measure. **Closed** — both references stripped, and
  a treated cell can no longer learn what is scored.

### 1B — subject, mechanism, operations

- **The delta list is itself underdetermined prose, verified by execution.** "Ep
  after any double-step" is already FIDE unless *persistence* is meant, which
  needs push/pop state surgery and breaks FEN encoding; "modified draw
  precedence" is behaviourally invisible unless the interface exposes termination
  *reasons*; the castling-removal subclass still keys repetition on castling
  rights, embodying an undecided delta×repetition reading. One clause of evidence
  for the thesis, and one blocking defect in the design.
- **The decision log administers part of the treatment to the control**, so a null
  cannot separate "formalism adds nothing over deliberation" from "the log
  delivered the active ingredient". Needs three arms or an honestly renamed H1.
- **Carried-over defects, dropped in transfer from case 05**: the model relay
  topology, the per-arm informativeness band, the treatment-delivery gate,
  timeout / attempt cap / hang policy / schedule ceiling, the death classifier,
  G0's mutant provenance, and k — *resolved by omission, which is not a
  resolution*.
- **Delta-shopping is unregulated**: if the pilot fails, authoring new deltas and
  re-piloting is seed-shopping with the seed renamed.

### The citation r1 caught, which is the programme's own thesis operating on me

§7.2 cited case 02's *"23 distinct specification files from 28 runs"* as evidence
against narrowing, and omitted the comparator sitting in the same file: the
**control arm produced 28 distinct artefacts from 28 runs**, and the file states
in terms that a one-sided reading of the treated arm alone is *"the opposite"* of
what the data show. Case 02's own article had already corrected this exact error
once. Corrected in §7.2; read whole, the prior evidence is **weakly for** H1.

### Verdict

Both reviewers agree the structural move — an oracle-free primary — is the
programme's best idea, and both agree it is not ready. The largest risk is
unchanged in shape from case 05 and now precisely located: **a fully-run study
that returns nothing**, because P1 converges through saturation and P3 ceilings
through delta salience, with no pilot band gating either and no operational
envelope stating what that null would cost.
