# FCDD Lab

Experiments with the `formal-contract-dev` (FCDD) skill — measuring what Formal
Contract-Driven Development actually costs, and what it buys, versus
conventional LLM-assisted development.

The method under test is vendored here: `skills/formal-contract-dev/SKILL.md`
is the **frozen** text case 01 measured; `skills/formal-contract-dev-current/`
tracks the live installed skill so it has a version history
(`skills/README.md` explains why the two must not be merged).

Every case is a self-contained folder with a pre-registered design frozen
before any run (`PROTOCOL.md` / `PREREGISTRATION.md`), an append-only
amendment log for every departure from it (`AMENDMENTS.md`, or amendments in
place), a `ledger/` holding the run accounting and the analysis output, and
`tools/` holding the scripts that emit every reported number.

---

## The cases at a glance

| Case | Question | Design | Runs | Outcome |
|---|---|---|---|---|
| [`case01_spectrum_gambit/`](case01_spectrum_gambit) | What does FCDD **cost** per defect, and is it more predictable? | Repair: 7 seeded single-byte faults in a 7,343-line Z80 chess engine, 2 arms, sealed acceptance gates | 7 matched pairs (+1 replicated cell ×3/arm) | **Cost answered:** FCDD dearer on 7/7 pairs, *p* = 0.016, median 4.74× raw tokens. **Predictability not answerable** at this design |
| [`case02_predictability/`](case02_predictability) | Does FCDD make repair cost **predictable**? (pre-registered) | Same 7 faults, k = 4 per arm per fault, randomised order under a committed seed | 56 runs | **Pre-registered null.** H1 not supported (*p* = 0.1094), point estimate *against* the hypothesis. Cost premium replicates: 7/7, median 2.26×. Fatal caveat found in review round 3: the treated arm held the answer key |
| [`case03/`](case03) | Does the premium buy fewer **silent** failures? | Design study only — five designs generated, judged, one (PORTGUARD) selected | none | Superseded by case 04; its constraint list and parity guard were inherited |
| [`case04_coq_rust/`](case04_coq_rust) | Does formal expression **prevent** defects (forward synthesis, not repair)? | Reimplement the Z80 engine in Rust twice — Rocq → mechanical Rust extraction vs direct Rust — scored against a sealed 11,103-position corpus | 13 scored cells | **Constraint-violation study.** The sealed oracle leaked to every cell; the computed numbers are inadmissible. The prevention claim remains **untested** |
| [`case06_narrowing/`](case06_narrowing) | Does formalising **narrow** the space of behaviours a requirement admits? | Inter-run agreement on *underspecified* inputs — an oracle-free primary, so nothing can leak | **none yet** | **Open, subject search active.** Chess was disqualified as prior-saturated; case 07 opened a lead — a real private operating specification satisfies the criteria chess cannot |
| [`case05_prevention/`](case05_prevention) | Does the contract prevent **silent** failure? *(in preparation — nothing run)* | Forward synthesis of FIDE-legal move generation, scored by **perft**; sandboxed cells, model tier as a factor | **none yet** — design at r5, three adversarial review rounds, not frozen | **Not freezable yet.** Rounds 1–3 returned 4, 4 and 9 blocking findings; every round's blockers sat inside the previous round's repairs |
| [`case07_attack_budget/`](case07_attack_budget) | Is the ATTACK **budget** safe — does bounded review miss what unbounded finds? | Two arms differing only in the stopping rule, on a live trading codebase — the method's own declared domain | **2 pilot cells** | **Retired at the pilot gate.** Both unbounded cells ran exactly **two rounds** — law 12's budget — so the contrast is nil and the question is moot in this regime. The pilot is the result |
| [`method/`](method) | Where does FCDD's cost variance live, and where do the gates belong? | Secondary analysis of case 02's 56 runs + a worked end-to-end pipeline prototype | — | ATTACK-beat round count varies 18× and explains ~half of FCDD's cost variance while changing no artefact → a bounded-budget replacement is proposed |

Running total: the programme has priced the method twice and has not yet
managed to test what the method is *for*.

---

## Case 01 — Spectrum Gambit: the price of predictability

**Subject.** The Spectrum Gambit chess stack: a 7,343-line Z80 assembly engine
(alpha-beta, transposition tables, quiescence, Zobrist hashing) exercised
headlessly through the hc91emu emulator.

**Design** (`PROTOCOL.md`, frozen v1.0, amendments A1–A10).

- An independent agent seeded **7 single-fault variants**, verified each fault
  manifests, wrote symptom-level bug reports (no location or cause hints), and
  sealed the answer key — the orchestrator stayed blind until grading.
- **Arm A — ordinary development**: reproduce → fix → test → review rounds.
  No formal-methods vocabulary in the prompt.
- **Arm B — FCDD**: the same bug report and the same gate, worked around a
  pre-built machine-checked contract.
- **Step 1** (Arm B's upfront investment, metered alone, **$21.75**): the
  engine's implemented rules expressed as a spec of record — `Contract.lean`,
  1,271 lines, **95 kernel-proved theorems, zero `sorry`, empty axiom
  profile** — plus twin, bridge and an SMT tier. It also produced **10 organic
  findings in the pristine engine** before any seeded bug was touched, two of
  them HIGH.
- Gate per defect: sealed acceptance tests + regressions green + blinded
  rubric review.

**Results.**

- **Cost (answered).** FCDD was dearer on **7 of 7** matched pairs, exact
  two-sided sign test *p* = 0.016 — the study's only statistically supportable
  result. Median ratio **4.74× on raw tokens** (the pre-registered primary
  metric, since the executed model was unpriced in the frozen table), ≈3.3–3.4×
  on priced bases, interval [1.12, 6.88]. The upfront contract **never
  amortised**, because FCDD was cheaper on no defect.
- **Predictability (not answered).** The across-defect dispersion contrast
  (6.23× vs 2.31×) rests entirely on one cell; excluding it both arms spread
  identically at 2.31×. Replicating that cell 3× per arm showed the shape the
  method predicts — the ordinary arm forking between a minimal repair and an
  unrequested redesign, FCDD single-mode — at a depth where the best attainable
  *p* is 0.10 (observed Fisher *p* = 0.40). Reported as a hypothesis, not a
  finding.
- **Quality: no claim.** Counterbalanced regrade favoured FCDD on 6/7 pairs
  (*p* = 0.125), paired composite CI [−0.44, +0.78] spanning zero.
- **Instrument findings** (§4 of the manuscript, and the most transferable
  part): an instruction to review "until no findings remain" **has no fixed
  point**; measured cost covaries with review-loop length at least as strongly
  as with method; processes killed by infrastructure **emit no cost record**,
  in one cell under-counting by ~20×. Three striking results turned out to be
  artefacts of the apparatus and were withdrawn.

**Deposited here.** The protocol and its amendments, the per-cell ledger
(`ledger/`, 264 raw result files), the prompt packs, the seeded-bug reports,
the step-1 contract summary and organic findings, the grading packets and
verdicts, the analysis and figure scripts (`tools/analyse.py`,
`tools/analyse_predictability.py`, `tools/make_figures.py`) and the figures. **The LaTeX/PDF manuscript was
deleted on 2026-08-27**: it covered case 01 alone and was organised around
"predictability" as the method's purpose — a framing §9a.1 of `ARTICLE.md` shows
the method's own text never states. The programme report `ARTICLE.md` is the
record of what was found.

**Not deposited:** the sealed answer-key file, the acceptance scripts and the
seeded variant trees — excluded by the repository's ignore rules; the ledger
carries their SHA-256 manifest (206 files). The per-cell workspaces also sit
outside the repository, so the reviewer counts, binary comparisons and per-cell
theorem counts are **not independently checkable from the artefact**. The
subject engine *is* deposited, contrary to what earlier versions of this
statement said — see **The benchmark is not blind** below. Working notes (`ARTICLE.md`,
`REPORT.md`) are kept local by deliberate policy; `REPORT.md`'s interim
conclusions are superseded by the manuscript.

---

## Case 02 — predictability, pre-registered, and the null it returned

Case 01 could not decide the predictability question, so case 02 was designed
to be decidable **before it was run** (`PREREGISTRATION.md`, frozen commit
`16b95fe`).

**Design.** The same seven faults, **k = 4 replicate repairs per arm per
fault** = 56 runs, 28 matched pairs, randomised across the whole schedule under
seed 20260807. Primary estimator, test and falsification condition all fixed in
advance: coefficient of variation of log cost per defect-arm cell, two-sided
exact paired permutation test across the seven defects, attainable floor
*p* = 0.016. No optional stopping, no outlier exclusion.

The oracle confound case 01 disclosed was addressed by giving **Arm A a
pristine-derived characterisation suite** built to the same budget — delivered
under budget and rebuilt once after its author disclosed prior exposure to the
fault-class list (A1, A2).

**Results** (`ledger/*_RESULT.txt`, all script-emitted).

- **H1 not supported.** Mean CV difference −0.0547 (the *ordinary* arm was less
  dispersed in five of seven defects), exact *p* = 0.1094, bootstrap CI on the
  median spanning zero. Both pre-registered falsification conditions fired. The
  direction holds in raw tokens, output tokens, and under a scale-free
  dispersion statistic (where it reaches the design floor *p* = 0.0156, still
  against the hypothesis).
- **The pre-registered estimator was itself defective** (A14): `CV_log` is not
  scale-invariant — its verdict moves between dollars (*p* = 0.1094) and cents
  (*p* = 0.0469) — and it is biased in FCDD's favour. Disclosed rather than
  swapped for a friendlier headline.
- **H2 degenerate.** No strategy fork survived into the emitted code: all 56
  repairs, both arms, produced a **byte-identical program**.
- **Quality.** No difference in overall preference (12–13, *p* = 1.0000) or
  correctness; FCDD scored significantly *lower* on **minimality**
  (*p* = 0.0312, CI excluding zero).
- **Cost replicates.** 7/7 defects dearer under FCDD, median **2.26×**
  (2.75× once model contamination is removed), *p* = 0.0156. Study total
  $1,382.74 over 56 runs.
- **Neither method's authored artefact converged**, though the code did: 23
  distinct specification files across Arm B's 28 runs; **28 distinct test
  artefacts across Arm A's 28**.

**What disqualifies it as a verdict on FCDD** (A17, found in the *third*
review round): every Arm B workspace shipped the pristine binary,
bit-identical to the sealed answer key, while the control was deliberately
denied it — one `cmp -l` localises any seeded fault. The asymmetry runs
*toward* FCDD, so the null and the premium are both conservative. Two further
limits are the experimenters': a second model executed inside 51 of 56 cells
(A13), and the benchmark is too easy — both arms scored 100%, and a method
designed to prevent failures cannot be evaluated on a benchmark that produces
none.

Three adversarial review rounds verified 43, then 47, then 72 findings; round
three found the worst one. All eighteen amendments are in `AMENDMENTS.md`; the
manuscript is `ARTICLE.md`.

---

## Case 03 — the design study (not run)

`CONSTRAINTS.md` converts every defect that actually occurred in cases 01–02
into a constraint on any successor design (C1–C11), each naming the amendment
that records it: no arm may hold the answer **and the check must be code**; the
benchmark must be able to produce failures; model identity must be verified,
not assumed; the primary estimator must be invariance-checked before freezing;
the analysis script must be dry-run against a real cell; schedule
discontinuities must be logged automatically; the graded object must be one
both arms produce in the same form.

Five candidate designs were generated from deliberately different angles and
scored by three independent judges on five axes. **PORTGUARD** won (22.0/25):
nothing seeded, so there is no answer key to leak; difficulty generated by a
frozen grammar; cross-arm byte parity asserted per cell by
`tools/parity_assert.py`, which replaces the judgement call that case 02 lost
with an equality test. The recurring fatal pattern among the losing designs is
recorded because it is the same leak one level up: three of five shipped Arm B
a runnable twin of the semantics the sealed oracle implements.

The selected design was superseded by case 04's forward-synthesis design; the
constraints and the parity guard carried forward.

---

## Case 04 — Rocq-extracted Rust vs direct Rust: the prevention claim

Cases 01/02 measured **repair**. FCDD's actual claim is **prevention**, so case
04 switched to forward synthesis:

> Reimplement the Z80 chess engine in Rust twice — once expressed in Rocq 9.1.1
> and mechanically extracted with `rocq-rust-extraction` 0.2.1, once written
> directly — and count behavioural divergences from the pristine engine, which
> is the hidden oracle.

**Design** (`PREREGISTRATION.md` v1.0, `DESIGN_DECISION.md` D1–D12,
`CONSTRAINTS.md` C1–C16). Both arms ship the same crate interface
(`legal` / `status` / `choose`), the same workspace byte-for-byte except
`PROMPT.md`, the same capped oracle CLI, and the same pinned model
(`deepseek/deepseek-v4-pro` for both arms, with a `deepseek-v4-flash` sweep of
the control as an exploratory arm). Primary outcome: policy-disagreement mass
μ₂ against the engine over a sealed corpus of **11,103 rules positions +
1,999 policy positions**, sealed by engine replay. The case 01 Lean contract
was shipped byte-identical to **both** arms as a symmetric shared reference.

Pilot gates P1–P3 passed (oracle self-consistency 1000/1000 with 0 unjudgeable;
extraction spike end-to-end, 8/8 against `python-chess`), the corpus was
sealed, and 13 cells ran to completion, all producing working crates.

**Outcome: a constraint-violation study** (amendment A-2026-08-26). Adversarial
review round 1 found that the shipped oracle CLI depended on orchestrator-side
paths the workspace builder never created, so **every cell bridged to the real
case 01 tree itself** (12/13 by in-transcript symlink) — which put the sealed
engine source, the tape and the emulator inside reach. 7 of 13 cells
demonstrably read sealed source; 6 ran the emulator directly, bypassing the
query counter; the two best policy scores are **byte-exact transcriptions of
leaked constants**. The C1 manifest guard was symlink-blind and subtree-scoped,
so it saw none of it.

The computed analysis (H1 *p* = 0.1181, H2 *p* = 0.93, informativeness gate
passed) is deposited for the record and is **inadmissible as evidence about
either arm**. The prevention claim remains untested.

**What survives.** The infrastructure — oracle CLI, referee, corpus sealing,
scorer, restart-safe driver, conformance checker, re-extraction verifier — is
validated and reusable, and the conformance machinery demonstrated that a
formal/extract arm can be checked mechanically: all five Rocq trees recompile
clean with **zero `Admitted`/`admit`/added `Axiom`**, and re-extraction is
body-byte-identical to the shipped `extracted.rs`. Five design lessons for any
successor are recorded (in the local-only report, §8, and reproduced here): the
oracle must be a service the
cells cannot read, cells get no external filesystem reach, the guard must
follow symlinks over the whole reachable closure, the query cap must be
enforced where the engine runs, and a sealed corpus on the same disk as the
cells is not sealed.

`ledger/review_round1.md` carries the findings ledger, the amendment in
`PREREGISTRATION.md` carries the verdict, and `ledger/descriptive_read.md`
carries a post-verdict descriptive reading that is explicitly **not** evidence.
As in case 01, the manuscript (`REPORT.md`) is kept local by policy.

---

## Case 07 — the ATTACK budget, retired at its own gate

**The only study in this programme that tested a claim the method actually
makes** — the skill's §5 says *"FCDD's value is **late** (adversarial review) as
much as early (proof)"*. Law 12 had replaced the ATTACK stopping rule on a
measured diagnosis with a *predicted* benefit; nobody had tested whether the
bounded rule is safe.

**It was retired at the pilot gate, and the pilot is the finding.** Both
unbounded cells ran **exactly two rounds**, unprompted — and law 12's budget *is*
two rounds. The unbounded arm did what the bounded arm is capped at, so the
bounded arm cannot miss what it finds, H1 would pass trivially, and the study
would have run to completion unable to support or refute anything. Two cells cost
what a completed study would not.

**What that establishes:** in *fresh adversarial review of unfamiliar code* the
cap is **not binding** — unbounded review self-limits at it. Law 12 is not wrong
there; it is inert. And it reframes the diagnosis that produced it: case 02's
1–18 round spread came from **repair against an existing contract**, a loop whose
feedback path this regime lacks. The runaway is plausibly a property of
repair-with-a-contract rather than of the beat, so law 12's real subject is
narrower than its text, and its safety question stays open **in the repair regime
only**.

**The secondary result is the programme's first empirical support for the
method's own claim.** Two ATTACK cells, on two modules of a codebase that **64
prior adversarial review documents** had already worked over, produced **six
confirmed defects**, every one demonstrated by a runnable probe — including a
**wrong money-path action** (a guard comparing 2-dp-rounded percentages, so
10.001% against a 10.0% cap is allowed; re-verified against the unscrubbed
source) and the arc's own **hollow-monitor** class at a latch site a 2026-08-03
fix never reached. Both were filed to the subject repository.

Full result, with its limits stated, in
[`case07_attack_budget/RESULT.md`](case07_attack_budget/RESULT.md).

## Case 05 — the prevention claim, in preparation

**Status: design only. Nothing has been run, no schedule exists, and the
pre-registration is not frozen.** `case05_prevention/PROPOSAL.md` is at revision
**r5** after three adversarial review rounds. It is published in this state
deliberately: the review record is the most useful thing the programme currently
has to offer about designing this kind of study.

**The question** is the one two prior cases failed to reach: does a
machine-checked contract prevent the *silent* failure — the implementation that
looks right, passes the obvious checks, and is wrong?

**The design, in its current form.**

- **Target: FIDE-legal move generation and adjudication. Oracle: perft.** Case 04
  asked arms to clone *"whatever this particular Z80 engine plays"* — a target
  defined by an artefact, so nothing was statable, the reward pointed at the
  filesystem, and the best score in the study was obtained by transcribing leaked
  constants. Against a *specification*, correctness becomes provable, so proof can
  displace testing — which is the differential the experiment exists to measure.
- **Isolation by absence, not by prohibition.** Cells run under `bwrap` with no
  network and no view of the lab tree — verified on the host: a sandboxed cell
  reached an orchestrator-held oracle over a bound UNIX socket while a public API
  call failed and `/home` was absent. Case 04's leak becomes unrepresentable
  rather than guarded against.
- **Difficulty is calibrated, not assumed.** The instrument must catch every
  injected fault class before the study runs (C24), and both the benchmark's
  failure rate *and* each model tier's ability to deliver the treatment are
  pilot-measured (C25).
- **Model tier is an experimental factor**, so "the task may be too easy" becomes
  a measured dimension rather than a threat.
- **Six phases, four stop points**, three of them before any scored run.

**What the reviews did to it, which is the part worth reading.** Round 1 found 4
blocking defects; round 2 found 4 more, **all inside round 1's repairs**, and
overturned three of its dispositions; round 3 — two reviewers, separate lenses,
no shared context — found 9, again all inside r4's repairs, converging
independently on the two worst. Among them: an oracle-leak argument that was
false, a delivery gate satisfiable by writing `legal p m := m ∈ genLegal p` and
proving it by `reflexivity`, a co-primary gate that could not have fired at any
sample size the programme can afford, and a sentence in the proposal contradicted
by the table printed directly above it.

**The risk that survives every fix**, recorded in §11 of the proposal rather than
buried in a threats list: the prevention claim turns on **mis-specification** — a
sound and complete proof against a *wrong* formalisation ships a
provably-conformant wrong program with maximal confidence — and chess movegen is
the domain where that is least likely to happen and least likely to matter. The
subject chosen to fix case 04's leak may have optimised away the failure the study
exists to observe.

A fourth review round is owed on r5's own repairs before anything is frozen.

## Method notes

**`method/ATTACK_BUDGET_DIAGNOSIS.md` — where FCDD's unpredictability lives.**
A secondary analysis of case 02's 56 runs (`tools/attack_budget_evidence.py`,
output in `ATTACK_BUDGET_EVIDENCE.txt`) locates the variance in the ATTACK
beat: the ordinary arm's review runs 1–3 rounds (3× spread, *r* = −0.21 with
cost), FCDD's runs 1–**18** (18× spread, *r* = **+0.72**, r² ≈ 0.52). Runs with
≥6 rounds cost $48.33 against $28.42 for runs with ≤2 — and since all 56 runs
produced a byte-identical binary, **no extra round changed any artefact**. The
diagnosis is that Beat 4 stops on *convergence* (unbounded, judgement-based)
where it could stop on *coverage* (bounded, priceable in advance); the proposed
change is a declared adversarial budget — one mandatory parallel pass of all
lenses over a declared surface, at most one scoped remediation round, hard stop
at two, widening the surface starts a new attack with its own quoted price.

**`method/pipeline.md` + `method/pipeline_proto/` — where the gates go.** A
deliberately small requirement (a stale-quote trading guard) run end to end
through the pipeline so gate placement is tested rather than argued: prose
requirement with fail directions → Lean spec of record carrying definitions
*and* properties → twin → bridge → gate, in ~2 s. It earned its keep by finding
a **property gap by execution**: mutation `M4_boundary` survived witnesses,
theorem mirrors and a 1,200-case sweep because P1–P5 constrained the verdict's
shape but never pinned where fresh becomes stale; P6 was added in response. The
gate is confirmed fail-closed against four injected defects, including a
`native_decide` theorem that evades both source greps and is caught only by the
axiom profile. Its stated residual is the one the method itself names as
uncloseable by the bridge: one session authored requirement, spec and twin, so
common-mode error remains open.

---

## What has replicated, and what has not

**Replicated (twice, in opposite units and independent analyses):** FCDD costs
more per defect than ordinary development-plus-review — 7/7 defects in case 01,
7/7 in case 02, median 2.26×–4.74× depending on metric and study.

**Not supported:** that FCDD makes repair cost more predictable on faults of
this difficulty. The point estimate ran against the hypothesis in every unit and
statistic tried.

**Newly supported, and it is the method's own claim:** *value is late, in
adversarial review.* Case 07's two-cell probe found six confirmed defects in a
money-path codebase that 64 prior adversarial reviews had worked over — the first
empirical support in seven cases, arrived at incidentally.

**Still untested:** the claim the method is actually sold on — that it prevents
*silent* failure, the repair that looks right and is wrong. Case 02's benchmark
could not produce failures at all (100% in both arms); case 04's attempt at the
prevention claim was voided by an information leak. That is the study worth
running next, and the constraint list in `case03/CONSTRAINTS.md` plus case 04's
§8 lessons are the price of admission.

**A methodological finding neither study set out to make:** on work of this
difficulty, careful adversarial review found the blocking defects — a second
model inside 51 of 56 cells, an estimator whose verdict moves with the currency
unit, a treated arm shipped the answer key, an oracle CLI that forced every
cell to breach its own sandbox — and formality found none of them. All had been
sitting in plain sight.

---

## The benchmark is not blind

An audit of this repository before it went public (case01 `PROTOCOL.md` A11,
case02 `AMENDMENTS.md` A19) found that **the deposit contains the subject
engine and the answers**:

- `case01_spectrum_gambit/step1_contract/artifacts/chess.tap` is tracked and
  byte-identical to the sealed pristine tape (sha256 `33ed86b2…78b4`). The
  step-1 contract package wrote its own copy under a path the `case*/sealed/`
  ignore rule never covered.
- `case01_spectrum_gambit/work/pristine/chess.bin` (`c107dfaf…dc0f`) was added
  and deleted in commit `590b5d1`; the blob is still reachable in history.
- The three tracked `.sna` artefacts are 48K RAM images that embed the engine's
  code verbatim.
- The seven seeded faults' **locations are recoverable in prose** — 39 tracked
  raw result files give file, line, byte offset and before/after value, and
  every bug has six tracked grading packets carrying the fix diff against
  `engine.inc`.

**Ruling: accept and declare.** The engine is the authors' own work, so nothing
is withdrawn and no measurement changes — every arm ran offline against a
tarball and could never reach this repository. What it costs is reuse: **the
seven-fault set is retired as a blind benchmark**, for us and for anyone else.
Treat it as an open one.

It is worth naming the failure mode, because it is the same one the programme
keeps reporting about other people's work. Case 02's A17 was a sealed artefact
reaching a workspace; case 04's F1 was a guard that did not follow symlinks;
this is a second copy under a path the ignore rules did not enumerate. Every
version of the control has enumerated **paths** while the hazard is **content**,
and each was aimed at the runs rather than at the deposit. The check
`case03/CONSTRAINTS.md` C1 already specifies — hash every file against the
sealed manifest — is owed to the repository too, and was not run against it
until now.

---

## If this is ever written up as a paper

`ARTICLE.md` is the record. A programme-level LaTeX manuscript built from it is
the natural eventual output — and a better paper than the case-01 one deleted on
2026-08-27, because **its contribution is the measurement findings and the design
failures, not a verdict on FCDD.** The honest framing is a methodology and
negative-results contribution: five cases, one replicated cost finding, one
pre-registered null, one voided study, two designs abandoned before running, and
a body of instrument findings that transfer to anyone measuring agentic work.

What it would need, none of which exists yet:

- **A resolved abstract.** The current one opens by stating FCDD's purpose is
  predictability and its payoff is prevention — which §9a.1 then shows the
  method's own text never claims. That tension reproduces the programme's path of
  discovery honestly, but a paper has to choose whether to lead with the claim or
  with its correction.
- **A figure set.** Nine figure PDFs survive under `case0*/figures/` (case 01's
  five, case 02's four); case 04's are ignored, and cases 05–06 have none. A
  programme paper needs its own.
- **The bibliography, which is recoverable.** The deleted `refs.bib` held **46
  entries**, verified during case 01. Recover it with
  `git show 2cf1f00:case01_spectrum_gambit/paper_springer/refs.bib > refs.bib`.
- **A venue decision.** Five cases plus two method changes is journal-length, not
  a conference paper.

Not scheduled. Recorded so the intent and the recovery path are not lost.

---

## Conventions

- **Pre-registration is a commit.** The commit that freezes a design is its
  timestamped pre-registration mark; nothing is edited silently afterwards.
- **Every reported number is emitted by a deposited script** (C10). Figures
  quoted in prose without a source have been withdrawn when found.
- **Amendment logs are append-only** and the manuscripts cite all of them.
- **Sealed material never enters the repository** — answer keys, acceptance
  scripts, seeded variants, the subject engine and the emulator are excluded by
  `.gitignore`; the ledgers carry their hashes.
- **Costs** are the platform's own USD self-report (a list-price index, not a
  bill — the subscription is flat-rate); raw token counters in the ledgers are
  the ground truth wherever the two disagree.
