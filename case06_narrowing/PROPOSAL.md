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

**Anti-circularity, and it is a program.** Every clause must trace to a **frozen
requirement ID**. A self-referential specification (`legal p m := m ∈ genLegal p`
— round 4A's counterexample, refuted by kernel execution) traces to *nothing*.
Freezing the **requirements** rather than the theorems leaves the arm doing
FCDD's actual work while removing its ability to self-certify.

## 5. Measurements

| | What | Note |
|---|---|---|
| **P1 primary** | pairwise behavioural agreement within arm, on underspecified inputs | no oracle; exact behavioural comparison |
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
2. **Prior evidence pointing the other way.** Case 02 produced **23 distinct
   specification files from 28 runs** of one task. If formalising narrowed the
   space, spec convergence is what you would expect, and it did not converge. The
   task differed — editing an existing contract, not authoring from prose — but
   this is a named alternative hypothesis, not a footnote.
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
