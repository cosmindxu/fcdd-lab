# Solution dispersion and prior capture: two named pressures on the same degrees of freedom

**2026-08-29.** A naming-and-anchoring note, of the same family as
`INTENT_COVERAGE.md` and `ATTACK_BUDGET_DIAGNOSIS.md` but with a **weaker
status than either: this note measures nothing and predicts nothing. It names
two concepts the programme has been circling without vocabulary, shows that the
existing corpus already contains evidence for both, and anchors each to an
established literature so that a future study can operationalise them instead
of rediscovering them.** Both concepts were proposed by the operator
(2026-08-29); the names below are the result of checking the operator's working
terms ("solution dispersion", "model bias") against what the literatures
already call these things.

## 1. The two concepts, stated

**Concept 1 — solution dispersion.** Given fixed requirements, how widely do
independently produced implementations vary? Not cost dispersion (what cases 01
and 02 measured), and not defect rate: the spread of the *artefacts themselves*
— structure, interpretation of silences, choice among admissible designs — for
one statement of requirements. The claim FCDD's own §0 objective implies, never
yet tested as stated, is that a contract should *narrow* this spread: "the
space of behaviours consistent with the artefact should be narrower than the
space consistent with the prose."

**Concept 2 — prior capture.** The model resolves whatever the requirements
leave open by pulling toward solutions well-represented in its training
distribution — *even when the requirements are perfectly understood* — because
requirements are never complete: completeness is unattainable in general (the
programme's own reward-gap finding: an instruction set is finite and the
behaviour space it governs is not), so degrees of freedom always remain, and
something must spend them. When the human does not, the prior does.

**The two are duals, and that is the point of naming them together.**
Requirements underdetermine; the training prior spends the leftover freedom;
*dispersion is what you observe when the prior is too weak to spend it
uniformly*. Strong prior → low dispersion (every run lands on the canonical
solution — which may or may not be the intended one). Weak prior → high
dispersion (every run spends the freedom differently). Either way the freedom
is spent silently, which is exactly the condition law 14 exists to prohibit at
the specification layer.

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
  actually about). Case02 §5.6 is a first, uncontrolled measurement of
  solution dispersion — uncontrolled because the requirements were not held
  fixed across what the artefacts were *for*.
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

## 3. What the corpus already shows — the two concepts are both in the 56-run dataset, in opposite directions

Case02 demonstrates *both* concepts simultaneously, and their duality, without
having had names for either:

- **Where the prior is strong, capture dominated and dispersion collapsed to
  zero.** All 56 repairs — both arms, seven defects, every replicate —
  compiled to a **byte-identical binary** (case02 §5.2). A single-byte fault
  in a chess engine is, in §9a.3's words, maximally prior-saturated: the
  admissible solution set was already a point before either method arrived.
- **Where no prior exists, dispersion was maximal.** The same 56 runs, the
  same requirements: FCDD's bespoke Lean contract for this engine has no
  training-distribution mass, and its artefact went 23-distinct-in-28; the
  control arm's ad-hoc test artefacts went 28-distinct-in-28 (§5.6).
- The subject probe (`method/subject_probe/`) is already a **prior-capture
  instrument**, built before the concept had a name: agreement-without-spec on
  a certified-undetermined item *is* capture, measured. 100% agreement on
  three of four certified items at the cheapest tier is capture near its
  ceiling. Concept 2 is therefore measurable **today**, with a protocol this
  repository already debugged (including the withdrawn first run, whose items
  confused recall of a determined rule with resolution of a silence).
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
not repeat that.

**Connection to the standing common-mode residual.** The skill's §5 keeps
"one author writing spec AND twin" as the residual the bridge cannot catch.
Prior capture supplies the *mechanism* and makes it worse: with a single model
in both roles — or two models trained on the same corpus — the "independent"
artefacts are drawn from the same prior, so their errors correlate exactly
where the requirements are silent. That is Knight–Leveson's result
transplanted: independently developed versions failed together far in excess
of the independence assumption (z ≈ 100), because the developers shared a
culture; models sharing a training distribution are the limiting case. Law
5's "two independent verifiers" quietly assumes an independence that prior
capture erodes, and this week's external corroboration says the same from the
EDA side — "generated properties can quietly encode the AI's own misreading
of the spec as if it were ground truth" (Darbari, in Bailey 2026-08-27) is
prior capture operating at the spec boundary.

## 4. Anchors (verified against primary or near-primary sources, 2026-08-29)

- **Underspecification** — D'Amour et al., *Underspecification Presents
  Challenges for Credibility in Modern ML*, JMLR 23 (2022); arXiv:2011.03395.
  A pipeline is underspecified when many predictors perform equivalently on
  the training objective yet diverge in deployment. The ML-side cognate of
  requirements underdetermination: held-out performance ↔ acceptance gate,
  deployment divergence ↔ the behaviour the gate never pinned.
- **Predictive multiplicity / Rashomon effect** — Marx, Calmon, Ustun, ICML
  2020 (arXiv:1909.06677); Breiman's Rashomon framing. Formal *measures* of
  multiplicity (ambiguity, discrepancy) over models of equal accuracy — the
  shape a solution-dispersion metric over artefacts of equal gate-passing
  should imitate.
- **Embers of autoregression** — McCoy et al., PNAS 121 (2024);
  arXiv:2309.13638. LLM accuracy tracks output-sequence probability even on
  deterministic tasks (GPT-4 cipher decoding: 51% for high-probability
  outputs vs 13% for low). The measured mechanism of prior capture: the model
  pulls toward typical outputs *even when the task is fully specified*.
- **Design fixation / Einstellung** — Jansson & Smith, *Design Studies* 12(1)
  1991; Luchins 1942. The human analogue: exposure to an example solution
  causes designers to copy its features, flaws included. Prior capture is
  fixation with the training distribution as the ever-present example.
- **Knight–Leveson** — *An Experimental Evaluation of the Assumption of
  Independence in Multiversion Programming*, IEEE TSE 12(1) 1986. Correlated
  failures among independently written versions; the consequence side of
  prior capture for any design that counts on N-version-style independence —
  including law 5 and every multi-agent ATTACK panel drawn from one model
  family.
- **Non-determinism of LLM codegen** (background for the dispersion
  observable): same-prompt structural variability is established empirically
  (e.g. arXiv:2506.10204; LLM-diversity-for-reliability, arXiv:2607.03174 —
  the latter is N-version programming *with* LLMs, sitting exactly on this
  note's two concepts).

## 5. What a study would have to do (design implication, not a design)

The programme's next-study logic (root ARTICLE.md §10) already retired the Z80
subject and prefers cheap probes before expensive cases. This note adds two
requirements to whatever comes next, both derived from §3 above:

1. **Measure solution dispersion, conditional on requirements, as a primary
   outcome** — an artefact-level distance (the shape of Marx et al.'s
   ambiguity/discrepancy, over gate-passing artefacts), not cost CV. Case02's
   §5.6 numbers show the raw material exists; what was missing was fixed
   requirements and a pre-registered metric.
2. **Select the subject by measured prior strength, weak side of the scale.**
   §9a.3 said narrowing value lives where priors are weak; the subject probe
   is the certified instrument for that selection. A domain the probe cannot
   disqualify (agreement well below ceiling on certified-undetermined items)
   is the first admissible subject this programme would have had.

And one requirement on the method rather than the study: any claim that
FCDD *reduces* solution dispersion must state against which pressure. Reducing
dispersion in a weak-prior domain is the method doing its stated job (spending
the freedom explicitly, once, upstream). Reducing it in a strong-prior domain
is indistinguishable from the prior doing the work — which is precisely the
null cases 01 and 02 bought, twice, before the distinction had a name.

## 6. Formal sketch (2026-08-30 — notation, not theory)

**Status: this section defines symbols and states one schematic identity. It
proves nothing; every claim below is a restatement of §§1–5 in a form a future
pre-registration can bind estimators to.**

**Setup.** Let 𝒜 be the artefact space and d : 𝒜 × 𝒜 → ℝ≥0 a *semantic*
distance: d(a, a′) = 0 iff a and a′ are observationally equivalent at the
declared interface (byte-identical binaries are one point; so are behaviourally
identical rewrites). For requirements R with derived acceptance gate G_R:

- **A(R) = { a ∈ 𝒜 : a ⊨ G_R }** — the admissible set.
- **U(R) = diam_d A(R)** — the *underdetermination* of R. The reward-gap
  finding, restated: U(R) > 0 for every finite R over an infinite behaviour
  space; completeness (U = 0) is unattainable in general.

**The generator, factored.** A method m run on R induces a distribution
μ_{R,m} over shipped artefacts. Idealisation:

> **μ_{R,m}(a) ∝ π(a) · exp(λ·r_m(a)) · 1[a ⊨ G_R]**

with π the model's training prior (the embers-of-autoregression pull), r_m the
reward/optimisation tilt the method's instructions create, and the gate as an
indicator. On the interior of A(R) the gate contributes nothing, so *everything
that varies inside the admissible set is spent by π and r*. The factorisation
carries §3's guarded distinction: **prior capture is the π-factor dominating on
A(R); the reward gap is the r-factor dominating on A(R)** — same uncovered
region, two pressures, two factors of one product. (A17 in this notation: the
answer key entered r_m, not π.)

**The two observables.**

- **Solution dispersion:** D(R, m) = 𝔼_{a,a′ ∼ μ_{R,m}}[ d(a, a′) ] — mean
  pairwise semantic distance *conditional on fixed R*; the Marx–Calmon–Ustun
  discrepancy analogue. The corpus's three dispersions are formally distinct:
  *cost* dispersion is the dispersion of the pushforward c∗μ for a cost
  functional c : 𝒜 → ℝ; *artefact* dispersion is D computed without holding R
  fixed (case02 §5.6); *solution* dispersion is D as written. Case02 shows the
  first two identify neither concept: D = 0 exactly (one binary) while
  disp(c∗μ) > 0 (the 2.26× premium and the 18× round spread) — §9a.2 as an
  equation.
- **Prior-capture strength:** C(R) = ℙ_{a,a′ ∼ π|A(R)}[ d(a, a′) = 0 ] — the
  collision probability of two independent draws from the prior *restricted to
  the admissible set*, i.e. agreement-without-spec. The subject probe estimates
  exactly this: k-run agreement on a certified-undetermined item is an
  empirical Ĉ. The probe's 100%-agreement items are Ĉ = 1 (capture at
  ceiling); en passant's 80% is Ĉ = 0.8. §9a.3's *prior strength* is C; §1's
  *capture* is the event that U(R) > 0 gets spent by π.

**The duality, schematically.** For fixed R with U(R) > 0:

> **D(R, m) ≈ (1 − C(R)) · U(R)**, modulated by what m narrows

with the two limits the corpus measured:

- **C(R) → 1 ⟹ D(R, m) → 0 for every m.** No method can demonstrate narrowing
  where the prior already spent the freedom — the cases-01/02 null in one line
  (single-byte chess repair: C ≈ 1).
- **C(R) ≪ 1 ⟹ D tracks the method.** FCDD's claim becomes: the contract 𝒞
  refines the gate, **A(R ∧ 𝒞) ⊊ A(R)**, so D(R ∧ 𝒞, FCDD) < D(R, ordinary).
  Law 14 in this language: the verdict map on A(R ∧ 𝒞) is a *function* on
  every declared input class, not a relation.

**The identifiability trap, formally.** Observing D ≈ 0 cannot distinguish
A(R ∧ 𝒞) small (the contract worked) from π|A(R) concentrated (the prior
worked); the two are separable only when C(R) ≪ 1. Hence §5's requirement 2 is
a *precondition*, not a preference: measure Ĉ first, and run the dispersion
study only where Ĉ sits well below ceiling.

**Law 5's erosion.** Two verifiers with priors π₁, π₂ have errors on the
silent region of A(R) that correlate with the overlap of π₁|A(R) and π₂|A(R).
Same model ⟹ π₁ = π₂ ⟹ maximal common mode; Knight–Leveson measured that even
human priors overlap enough to break the independence assumption (z ≈ 100).
One model family in both roles is the limiting case of a result forty years
old.

*Limits of the sketch, stated per law 8:* the factorised μ is an idealisation —
real generation is sequential and the three factors are not separable in the
weights; d is named but not constructed, and constructing a computable semantic
distance for real artefacts is the hard step a study design must solve
(case02's d was the degenerate "sha256 equality", which is d after quotienting
by *nothing*); the duality line is a schematic, not an identity — no
functional form is claimed, only the two limits; and U(R) is generally
unmeasurable, which is why the operational quantity is always Ĉ, never U.
