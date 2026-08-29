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
