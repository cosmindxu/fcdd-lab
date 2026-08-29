# Solution dispersion and prior capture: two named pressures on the same degrees of freedom

**2026-08-29; revised 2026-08-30 after a four-lens adversarial review (record in
§7). Status, re-graded by that review: §§1–5 measure nothing and predict
nothing — they name two concepts, show the corpus already contains evidence
bearing on both, and anchor each to an established literature. §6 (added
2026-08-30) is different in kind and is graded separately: a predictive
schematic at hypothesis tier, with no corpus test of its weak-prior half.**
Both concepts were proposed by the operator (2026-08-29); the names below are
the result of checking the operator's working terms ("solution dispersion",
"model bias") against what the literatures already call these things.

## 1. The two concepts, stated

**Concept 1 — solution dispersion.** Given fixed requirements, how widely do
independently produced implementations vary? Not cost dispersion (what cases 01
and 02 measured), and not defect rate: the spread of the *artefacts themselves*
— structure, interpretation of silences, choice among admissible designs — for
one statement of requirements. The claim the FCDD skill's §0 objective
*implies, but has never tested as stated*, is that a contract should *narrow*
this spread: the space of behaviours consistent with the artefact "narrower
than the space consistent with the prose" (quoting the skill's frontmatter;
its §0 body states it in the indicative).

**Concept 2 — prior capture.** The model resolves whatever the requirements
leave open by pulling toward solutions well-represented in its training
distribution — *even when the requirements are perfectly understood* — because
requirements are never complete: completeness is unattainable in general (the
programme's own reward-gap finding: an instruction set is finite and the
behaviour space it governs is not), so degrees of freedom generally remain, and
something must spend them. When the human does not, the prior does.

**The two are duals, and that is the point of naming them together.**
Requirements underdetermine; the training prior spends the leftover freedom;
*dispersion is what you observe when the prior is too weak to spend it the
same way every run*. Strong prior → low dispersion (every run lands on the
canonical solution — which may or may not be the intended one). Weak prior →
high dispersion (every run spends the freedom differently). Either way the
freedom is spent silently, which is exactly the condition law 14 exists to
prohibit at the specification layer.

## 2. Names, and the naming decisions

| concept | name adopted | operator's working term | nearest literature term |
|---|---|---|---|
| the condition | **requirements underdetermination** | "requirements are not complete… or leave degrees of freedom" | *underspecification* (D'Amour et al.) |
| the observable | **solution dispersion** | "solution dispersion" — kept | *predictive multiplicity* / the *Rashomon effect* (Marx–Calmon–Ustun; Breiman) |
| the mechanism | **prior capture** | "model bias" — replaced | output-probability bias, *embers of autoregression* (McCoy et al.); *design fixation* (Jansson–Smith) |

Decisions:

- **"Solution dispersion" is kept.** It is the operator's term, it is accurate,
  and the nearest literature terms don't fit better: "predictive multiplicity"
  is defined over classifiers in a Rashomon set, not over generated artefacts,
  and "output variance" collides with token-level sampling noise. One
  discipline: the corpus now contains **three distinct dispersions** and every
  future use must say which — *cost* dispersion (cases 01/02, measured, null),
  *artefact* dispersion (case02 §5.6, exploratory: 23 distinct specs / 28
  runs), and *solution* dispersion (this note: the artefact-level spread
  **conditional on fixed requirements**, the one the method's objective is
  actually about). Case02 §5.6 is a lexical, uncontrolled *precursor*
  observation — artefact dispersion per this taxonomy, since the artefacts
  served different defects and its distinctness measure was textual, not
  semantic. **Solution dispersion has not yet been measured by anything.**
- **"Model bias" is replaced by "prior capture."** "Bias" is overloaded past
  usefulness (statistical bias, fairness bias, the estimator bias of A14 —
  already in this corpus). "Prior capture" composes with the vocabulary the
  programme already has: §9a.3 established **prior strength** as a measurable
  design input; *capture* names what a strong-enough prior does with the
  degrees of freedom. Strength is the magnitude; capture is the effect.
- Rejected alternatives, recorded per law 8: "solution-space collapse"
  (presumes the strong-prior case only), "canonical-solution attraction"
  (accurate but unwieldy), "distributional regression" (collides with the
  statistics term), "Einstellung effect" (the human analogue, kept as lineage
  not as name).

## 3. What the corpus already shows — evidence for both concepts, with its confounds stated

Case02's 56 runs bear on *both* concepts, in opposite directions — but the
strong-prior exhibit must be split by arm, because half of it is confounded by
the study's own A17:

- **Where the prior is strong, dispersion collapsed — cleanly in one arm.**
  All 56 repairs compiled to a byte-identical binary (case02 §5.2). §5.2
  itself rules this "not an arm-comparable achievement": Arm B's workspaces
  held the pristine binary (A17), so its 28 convergences had a reward-side
  channel — in this note's later notation, the answer key entered r, not π.
  The clean capture evidence is **Arm A's 28 key-free runs**, which converged
  on the same single binary with no oracle. A single-byte fault in a chess
  engine is, in §9a.3's words, maximally prior-saturated: the admissible
  solution set was already (close to) a point before either method arrived.
- **Where the prior is weak, textual spread was large.** The same 56 runs:
  FCDD's bespoke Lean contract for this engine has negligible
  training-distribution mass, and its artefact went 23-distinct-in-28 on a
  textual measure; the control arm's ad-hoc test artefacts went
  28-distinct-in-28 (§5.6). Both figures are lexical and uncontrolled
  (§5.6's own caveat: low overlap shows no shared vocabulary, not that they
  formalised different things), so this is a precursor observation, not a
  measurement of solution dispersion.
- The subject probe (`method/subject_probe/`) is a **prior-capture protocol**,
  built before the concept had a name: agreement-without-spec on a
  certified-undetermined item *is* capture, probed. Its status is what its
  own FINDINGS.md says: one valid partial run, one model tier, four certified
  items (three at ceiling, one at 4-of-5), items certified by this lab after
  a half-invalid first run — and a small model can only *disqualify* a
  domain, never clear it. So concept 2 has a debugged protocol today, not a
  certified instrument.
- §9a.2's diagnosis — "the programme measured the wrong dispersion" — is
  concept 1 stated negatively. This note is that diagnosis given a positive
  object: the dispersion worth measuring is solution dispersion conditional
  on requirements, in a domain where prior strength does not force it to zero.

**Distinction that must not be flattened (the §7 lesson).** Prior capture is
not the reward gap wearing a new name. Both fill the region no instruction
covers, but by different pressures: the reward gap is *optimisation* pressure
(the agent fills the gap in whatever direction the reward points — A17, the
five faces); prior capture is *distributional* pressure (the model fills the
gap with whatever its training data made typical, no reward required). They
can co-occur and they can oppose. An earlier draft of §7 flattened two
different failures into one slogan and had to be unflattened; this pair should
not repeat that. (The review found this note's first §6 committing a version
of the same flattening — its duality schematic omitted the reward term
entirely; §6 below carries the corrected form.)

**Connection to the standing common-mode residual.** The skill's §5 keeps the
bridge's inability to catch common-mode error — spec and twin sharing the
author's mistake, the author grading their own homework — as the standing
residual. Prior capture supplies a candidate *mechanism* and makes it worse:
with a single model in both roles — or two models trained on similar corpora —
the "independent" artefacts are drawn from overlapping priors, so their
choices correlate exactly where the requirements are silent. That is
Knight–Leveson's result transplanted: independently developed versions failed
together far in excess of the independence assumption (their own statistic:
z = 100.51), because the developers shared a culture; models sharing a
training distribution are the natural limiting case. Law 5's "two independent
verifiers" assumes an independence that prior capture erodes — stated here
for artefact *generation*, and as a conjecture for verification (§6). This
week's EDA practitioner testimony is *consistent with* the mechanism —
"generated properties can quietly encode the AI's own misreading of the spec
as if it were ground truth" (Darbari, in Bailey 2026-08-27) — but tests
nothing about cross-verifier correlation; the only measured evidence in this
paragraph is the 1986 human study.

## 4. Anchors (verified against primary or near-primary sources, 2026-08-29; re-verified against primary texts by the 2026-08-30 review)

- **Underspecification** — D'Amour et al., *Underspecification Presents
  Challenges for Credibility in Modern ML*, JMLR 23 (2022); arXiv:2011.03395.
  A pipeline is underspecified when many predictors have equivalently strong
  *held-out* performance in the training domain yet diverge in deployment.
  The ML-side cognate of requirements underdetermination: held-out
  performance ↔ acceptance gate, deployment divergence ↔ the behaviour the
  gate never pinned.
- **Predictive multiplicity / Rashomon effect** — Marx, Calmon, Ustun, ICML
  2020 (arXiv:1909.06677); Breiman's Rashomon framing. Formal *measures* of
  multiplicity (ambiguity, discrepancy) over classifiers within ε of a
  baseline's accuracy — the spirit a solution-dispersion metric over
  gate-passing artefacts should imitate. Note their definitions' shape:
  both are computed *relative to a designated baseline model*, and
  discrepancy is a *maximum*, not a mean (this matters in §6).
- **Embers of autoregression** — McCoy et al., PNAS 121 (2024);
  arXiv:2309.13638. LLM accuracy tracks output-sequence probability even on
  deterministic tasks (GPT-4 cipher decoding: 51% for high-probability
  outputs vs 13% for low). The measured mechanism of prior capture: the model
  pulls toward typical outputs *even when the task is fully specified*.
- **Design fixation / Einstellung** — Jansson & Smith, *Design Studies* 12(1)
  1991; Luchins 1942. The human analogue: exposure to an example solution
  causes designers to copy its features, flaws included — in the original
  experiments, even when the flaws were highlighted. Prior capture is
  fixation with the training distribution as the ever-present example.
- **Knight–Leveson** — *An Experimental Evaluation of the Assumption of
  Independence in Multiversion Programming*, IEEE TSE 12(1) 1986. Correlated
  failures among 27 independently written versions (z = 100.51, the paper's
  own figure); the consequence side of prior capture for any design that
  counts on N-version-style independence — including law 5 and every
  multi-agent ATTACK panel drawn from one model family.
- **Non-determinism of LLM codegen** (background for the dispersion
  observable): same-prompt structural variability is established empirically
  — arXiv:2506.10204's *baseline* condition (unperturbed prompts at
  temperature 0 still yield structurally distinct outputs, ~0.7 similarity;
  the paper's headline result is about prompt perturbation) — and
  arXiv:2607.03174 is N-version programming *with* LLM-generated versions,
  sitting exactly on this note's two concepts.

## 5. What a study would have to do (design implication, not a design)

The programme's next-study logic (root ARTICLE.md §10) already retired the Z80
subject and prefers cheap probes before expensive cases. This note adds two
requirements to whatever comes next, both derived from §3 above:

1. **Measure solution dispersion, conditional on requirements, as a primary
   outcome** — an artefact-level distance in the spirit of Marx et al.'s
   multiplicity measures, over gate-passing artefacts, not cost CV. Case02's
   §5.6 numbers show the raw material exists; what was missing was fixed
   requirements, a semantic (not lexical) distance, and a pre-registered
   metric.
2. **Select the subject by measured prior strength, weak side of the scale.**
   §9a.3 said narrowing value lives where priors are weak; the subject probe
   is the debugged protocol for that selection (disqualify-only, per its own
   FINDINGS.md). A domain the probe cannot disqualify — agreement well below
   ceiling on certified-undetermined items — would be the first admissible
   subject this programme has had. This is a precondition for a
   *dispersion-only* design; §6 names the interventions that can substitute
   for it when Ĉ is high.

And one requirement on the method rather than the study: any claim that
FCDD *reduces* solution dispersion must state against which pressure. Reducing
dispersion in a weak-prior domain is the method doing its stated job (spending
the freedom explicitly, once, upstream). Reducing it in a strong-prior domain
is indistinguishable — from dispersion alone — from the prior doing the work,
which is precisely the null cases 01 and 02 bought, twice, before the
distinction had a name.

## 6. Formal sketch (2026-08-30; revised same day after review — hypothesis tier)

**Status: this section defines symbols and states one one-sided bound and one
falsifiable hypothesis. It goes beyond §§1–5: the bound's weak-prior side has
no corpus test, and nothing here is a restatement of measured fact unless
marked so. Assumptions are stated inline because the review found the first
draft's omissions were where its errors lived.**

**Setup.** Let 𝒜 be the artefact space and d : 𝒜 × 𝒜 → ℝ≥0 a *semantic
pseudometric*: d(a, a′) = 0 iff a and a′ are observationally equivalent at the
declared interface (a metric on the quotient 𝒜/≈; symmetry assumed, the
triangle inequality is not needed below). For requirements R with derived
acceptance gate G_R:

- **A(R) = { a ∈ 𝒜 : a ⊨ G_R }** — the admissible set, assumed non-empty.
- **U(R) = diam_d A(R)** — the *underdetermination* of R. The reward-gap
  finding supports: U(R) > 0 is the *generic* case for finite R over an
  infinite behaviour space — not a universal (a finite R can pin behaviour up
  to observational equivalence: "return the input unchanged" has U = 0 in the
  quotient). Where U appears below, assume 0 < U(R) < ∞.
  *(Rejected formalisations, per law 8: entropy of a reference measure on
  A(R) — needs the measure the whole point is we don't have; covering number
  — scale-dependent.)*

**The generator, factored.** A method m run on R induces a distribution
μ_{R,m} over shipped artefacts. Idealisation, with its assumptions explicit:

> **μ_{R,m}(a) ∝ π(a) · exp(λ·r_m(a)) · 1[a ⊨ G_R]**

where π is the model's training prior (the embers-of-autoregression pull),
r_m the reward/optimisation tilt the method's instructions create, λ > 0 its
weight, and the gate an indicator. *Assumed for normalisability: π(A(R)) > 0
and λ·r_m bounded above on A(R).* The support condition is substantive: §3's
"negligible training-distribution mass" must mean small, not zero — a π-null
admissible set makes μ undefined, and the corpus shows novel contracts do get
produced. On A(R) the gate factor is identically 1, so *everything that
varies inside the admissible set is spent by π and r*. The factorisation
carries §3's guarded distinction: **prior capture is the π-factor dominating
on A(R); the reward gap is the r-factor dominating on A(R)** — same uncovered
region, two pressures, two factors of one product. (A17 in this notation: the
answer key entered r_m, not π. The corpus's one D = 0 datum therefore has an
r-component in Arm B; only Arm A's half is a clean π story — §3.)

**The two observables.**

- **Solution dispersion:** D(R, m) = 𝔼_{a,a′ ∼ μ_{R,m}}[ d(a, a′) ] — mean
  pairwise semantic distance *conditional on fixed R*. This is a multiplicity
  measure in the *spirit* of Marx–Calmon–Ustun, but not their definition:
  their ambiguity and discrepancy are baseline-relative, and discrepancy is a
  maximum — a pre-registration binding an estimator must not conflate the
  two. *(Rejected per law 8: a baseline-relative D — needs a privileged
  reference artefact no generative setting has.)*
- **The three corpus dispersions, typed correctly.** Cost is a functional of
  the *run*, not the artefact: let Ω be the run space, c : Ω → ℝ the cost,
  and a : Ω → 𝒜 the artefact map, with μ̃ the run distribution and
  μ = a∗μ̃. Then *cost* dispersion is disp(c∗μ̃); *solution* dispersion is D
  computed under μ; *artefact* dispersion is D computed without holding R
  fixed. Case02 in this typing: D = 0 exactly (μ a point mass — one binary)
  while disp(c∗μ̃) > 0 (within-cell cost spreads of 1.30×/1.75× per §5.7 —
  the correct dispersion exhibits; the 2.26× premium is a location contrast
  and the 18× figure is round-count spread). A cost functional typed on 𝒜
  would be constant on case02's data — the first draft made exactly that
  type error. So cost dispersion identifies neither concept: §9a.2, now as a
  typed statement.
- **Prior-capture strength:** C(R) = ℙ_{a,a′ ∼ π|A(R)}[ d(a, a′) = 0 ] — the
  collision probability of two independent draws from the prior restricted to
  the admissible set. *(Rejected per law 8: 1 − C is the Gini–Simpson index;
  entropy-based concentration — less interpretable as an agreement
  probability, which is what the probe can estimate.)* What the subject probe
  actually estimates is three steps away from C(R), and each step must be
  owned: (i) it samples the deployed model's generation process — π tilted by
  instructions and temperature — not π|A(R); (ii) it measures agreement on
  *one interface coordinate* (one item's answer), which upper-bounds
  full-artefact collision; (iii) its recorded "agreement" is modal share, and
  modal share is not collision probability below ceiling. The corrected
  estimator is the pairwise-match U-statistic over k runs,
  **Ĉ = Σᵢ C(kᵢ,2) / C(k,2)** over answer-equivalence classes: the probe's
  4-of-5 en passant item gives Ĉ = 6/10 = **0.6**, not 0.8; the 5-of-5 items
  give Ĉ = 1, where modal share and collision coincide. Ĉ is an
  *upper-bound proxy* for C(R) on the probed coordinate, biased by the
  probe's own r-factor — usable to disqualify a domain (high Ĉ), never to
  certify one (low Ĉ could still hide capture on unprobed coordinates).

**The bound (replacing the first draft's "duality schematic").** Let C_μ(R,m)
be the collision probability under μ_{R,m} itself (not under π|A(R)). Since
every non-colliding pair is at distance ≤ U(R):

> **D(R, m) ≤ (1 − C_μ(R, m)) · U(R)**

One-sided, and loose — it is not an approximation, and the first draft's
"D ≈ (1−C)·U" was wrong twice: it mixed C computed under π with D computed
under μ (the tilt exp(λ·r_m) can move μ far from π, so C_π → 1 does *not*
force D → 0 for every m unless the tilt is bounded), and it erased the
r-factor the note itself insists must never be flattened into the prior. What
survives with hypotheses attached: **if U(R) < ∞ and λ·r_m is bounded on
A(R), then C_π(R) → 1 forces D(R,m) → 0** — the retrodicted (not measured:
no Ĉ was ever taken for chess repair, and Arm B's r-channel violates the
boundedness hypothesis) reading of the cases-01/02 null. The weak-prior side —
C ≪ 1, where D is supposed to track the method — has **no corpus evidence of
any kind**: the probe has never once returned a low Ĉ.

**The narrowing hypothesis (not the skill's claim).** The skill's §0 claims
set-narrowing: A(R ∧ 𝒞) ⊊ A(R). It nowhere claims lower dispersion, and the
implication does not hold: refinement shrinks the *diameter* weakly, but D is
measure-dependent and can *rise* under refinement — if π|A(R) has mass 0.9 on
the canonical class and 0.05 on each of two others (all pairwise at distance
L), D ≈ 0.19·L; a contract that excludes the canonical class leaves ½/½ and
D = 0.5·L. **Dispersion increases exactly when the contract rejects the
prior's mode — the method's most important use case.** So the testable
hypothesis this note adds (its own, not the method's): *in a weak-prior
domain (measured Ĉ ≪ 1), D(R ∧ 𝒞, FCDD) < D(R, ordinary).* Falsifiable, and
stated with its refutation condition: it is refuted if such a domain yields
D(FCDD) ≥ D(ordinary), and the whole framework is challenged if a measured
Ĉ ≪ 1 domain yields D ≈ 0 under an ordinary method with no reward-side
channel.

**The identifiability trap, scoped.** From D at fixed R and m *alone*,
D ≈ 0 cannot distinguish A(R ∧ 𝒞) small (the contract worked) from π|A(R)
concentrated (the prior worked). At high C the hypotheses remain separable by
intervention: a control arm on the same R (if the ordinary arm's D ≈ 0 too,
the prior sufficed); a cross-model replication under a different training
corpus (different π, same 𝒞); or a compatibility check — if the
prior-canonical solution *violates* 𝒞 and FCDD runs still converge, the
landing *location*, not the spread, shows the contract acted. So §5's
requirement 2 is a precondition for a dispersion-only design, and a
preference elsewhere.

**Law 5's erosion — a conjecture, typed correctly.** The first draft asserted
verifier-error correlation from the overlap of *generation* priors, a type
error (verifiers emit verdicts on given artefacts; they do not sample
artefacts). Stated properly: *we conjecture that verifier-error correlation
on the silent region of A(R) grows with the overlap of the verifiers' verdict
distributions there, and that a shared training prior is the mechanism.* Same
model does not imply *maximal* common mode — temperature alone produces
self-disagreement — only an elevated floor. What is measured is the
generation-side analogue: Knight–Leveson's correlated failures of
independently *written* versions (z = 100.51) with humans who merely shared a
culture; models sharing a training distribution are the natural limiting case
of the same mechanism, on the generation side.

*Limits of the sketch, per law 8:* the factorised μ is an idealisation — real
generation is sequential and the three factors are not separable in the
weights; d is named but not constructed, and constructing a computable
semantic distance is the hard step a study design must solve (case02's
identity check was sha256 plus a comment-stripped, whitespace-normalised
instruction-stream comparison — a nontrivial lexical quotient, but not a
semantic distance, and its §5.6 distinctness measure was textual); U(R) is
generally unmeasurable, which is why the operational quantity is always Ĉ;
and Ĉ itself is a coordinate-wise, r-biased upper-bound proxy, fit to
disqualify domains and nothing else.

## 7. Review record

Adversarially reviewed 2026-08-30 under a declared budget (4 lenses ×
1 surface, one round, parallel, on the operator's designated review model;
one remediation round; hard stop at two): mathematical coherence, corpus
fidelity, literature accuracy, overclaim/self-consistency. Findings:
2 BLOCKING (a cost-functional type error in §6; a stale status header
contradicted by §6), 11 MAJOR, ~11 MINOR — with three independent
convergences (the Ĉ arithmetic, found by three lenses; the §5.2/A17
misuse and the erased r-factor, each by two). All BLOCKING and MAJOR
findings and all actionable MINOR findings are addressed in this revision;
the review also *verified* the primary-source numbers (Knight–Leveson's
z = 100.51 is the paper's own statistic; McCoy's 51%/13% is verbatim;
Jansson–Smith, Luchins, and both arXiv IDs check out). Residuals shipped
named: d remains unconstructed; the weak-prior half of §6 remains untested;
Ĉ remains a coordinate-wise upper-bound proxy.
