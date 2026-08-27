# Qualifying a subject before designing a study

**2026-08-27.** Written because three consecutive designs failed on subject
choice, and in each one the subject was assumed and the apparatus was designed
around it:

| Case | Subject | How it failed |
|---|---|---|
| 04 | clone a hidden Z80 engine | the target was an *artefact*, so the reward pointed at the filesystem; the best score was a transcription |
| 05 | FIDE movegen scored by perft | mis-specification — the failure mode the claim turns on — is least likely and least consequential in that domain |
| 06 | FIDE + a frozen delta | the coverage endpoints survive saturation; **the primary does not** — priors fill the gaps the prose leaves |

**The rule this establishes: qualify the subject first, mechanically, and design
nothing until it passes.** Case 03 ran a scored multi-design selection and it was
the programme's one methodologically sound step; case 04 skipped it and paid with
a voided study. The step returns here, one level earlier — applied to *subjects*,
not designs.

## 1. The binding criterion, and why it is binding

**C-S1 — the domain's RESOLUTIONS must not be in the weights.**

Not "the domain is obscure" — the *resolutions of its ambiguities* must be
unmemorised. Chess fails precisely here: the prose can under-determine whether
the en-passant square belongs in the repetition key, and every run of both arms
still answers identically, because python-chess's choice saturates the corpus.
The prose under-determines; the priors over-determine; the contract is never
consulted; the study measures recall.

**This is checkable, and the check is cheap.** See §3.

## 2. The rest of the criteria

- **C-S2 — genuine underdetermination.** The prose leaves real decisions open —
  and they are decisions a competent implementer would actually have to make.
- **C-S3 — enumerable requirements**, so traceability and coverage are mechanical
  rather than judged.
- **C-S4 — silent failure.** A wrong resolution passes the obvious tests.
- **C-S5 — externally authored.** The requirement source is not ours, or we
  author the difficulty and the circularity objection returns (case 03 named this
  against its own winner).
- **C-S6 — mechanically comparable behaviour**, so agreement is computable
  without a judge.
- **C-S7 — feasible in one session** for both arms, on this hardware.

**C-S1 and C-S5 pull against each other**, and that tension is the real problem:
anything external and well-known is saturated, anything unsaturated tends to be
ours. Two ways out that satisfy both:

- **Post-cutoff specifications.** A standard, regulation or protocol published
  *after* the pinned model's training cutoff. Externally authored, real, and
  provably unmemorised — the cutoff is a date, and the probe in §3 confirms it.
- **Obscure-but-real specifications.** Real specs rarely implemented: niche file
  formats, regional regulatory rules, protocol errata, domain-specific
  conformance annexes.

## 3. The saturation probe — a mechanical admission test

**Step 0, added 2026-08-27 after the first run failed on it: every probe item must
be CERTIFIED genuinely undetermined before its agreement means anything.**
Certification is by citation (the specification is demonstrably silent on the
point) or by witness (two conforming implementations resolve it differently).
Without this step the probe asks *"what does the standard say?"* — a knowledge
question whose consistent answer is correct recall, not saturation of an
ambiguity. The first run conflated the two and inflated four of five
disqualifications; see `subject_probe/FINDINGS.md`.

Then, for each candidate subject:

1. Take the candidate's **underspecified inputs**.
2. Run the pinned model **k times with no prose at all** — no requirement, no
   contract, just the interface and the input.
3. Measure agreement across those runs.

**If the runs agree without the specification, the domain is saturated and the
subject is disqualified** — no contract can be shown to narrow what priors have
already narrowed.

This is the arm-blind baseline promoted from an analysis control to a **selection
gate**, and it costs a handful of cheap runs against a study that costs weeks.
Every candidate is scored on it before anything is built.

## 4. The procedure

1. Nominate ≥ 5 candidate subjects from different angles (case 03's shape).
2. Run the §3 probe on each. **Disqualify on C-S1 before any other judging** —
   it is the criterion the last three designs died on.
3. Score survivors against C-S2…C-S7 with independent judges.
4. Only then design the study, and re-derive the outcome definitions from the
   winning subject rather than transplanting them.

## 5. What the first run reframed

Where a specification is genuinely silent, the model converges anyway — 100%
agreement on three of four certified items, at the cheapest model tier. That is
not only an obstacle to benchmarking. It is a claim about **when this method can
help at all**:

> Formalisation's narrowing value is a function of **prior strength**. Where
> priors are strong the solution space is already narrow and a contract has
> little left to narrow; where priors are weak — novel domains, post-cutoff
> specifications, genuinely new requirements — narrowing is where the value must
> live.

That is directly actionable, it explains why cases 01 and 02 found nothing on
predictability (a byte-fault in a chess engine is maximally prior-saturated), and
**prior strength is now a measurable quantity** using this same probe. Candidate
nomination should therefore target *low-prior* domains rather than merely obscure
ones.

## 6. The honest possibility

The probe may disqualify every affordable candidate. If the only unsaturated
domains are too obscure to have enumerable requirements, or too new to have
conformance data, then **"does formalising requirements narrow the solution
space" is not answerable at this lab's scale** — and that is a finding worth
having cheaply, at design time, rather than after a fifth study.

**Case 06's chess+delta is not the presumptive subject.** It is one candidate,
and on C-S1 it is the one most likely to fail.
