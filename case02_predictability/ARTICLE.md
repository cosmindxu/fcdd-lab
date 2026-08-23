# Predictability Was the Claim: A Pre-Registered Null

**Case 02 — a pre-registered replication of the predictability hypothesis that Case 01 was structurally unable to test.**

**Draft v3 — 2026-08-23.** This manuscript has been through two adversarial
review rounds before submission. Round one raised 67 findings, **43 verified: 11
blocking, 17 major, 15 minor**. Round two, on the revised text, raised 66 and
**47 verified: 13 blocking, 24 major, 10 minor** — several of them overturning
round one's own corrections. Both rounds are recorded in `AMENDMENTS.md`
(A15, A16). We report our own error count with the same precision we report
FCDD's, because a paper returning a null on someone else's method has no standing
to be vague about its own.

Round one's two findings that changed what the paper can claim: a **second model executed inside
51 of the 56 cells** (A13), and the **pre-registered primary estimator is not
scale-invariant** (A14). Both are new sections below and new threats. Three
claims v1 asserted without measuring are withdrawn: the "15,295 bytes" figure
(the binary is 13,516), the attribution of the minimality result to comment
volume (measured: +40 characters, *p* = 0.2344), and the direction of the
nine-day gap's bias (measured: the opposite of what A6 predicted). Every number
here re-derives from the scripts named in §10 against the deposited artefacts;
where v1 claimed a provenance it did not have, the script was fixed rather than
the claim softened. Round two overturned three of v2's own corrections — the specification-divergence
baseline and count, the superlative drawn from them, and A14's claim that the
scale-free result held "in any unit" — and surfaced a second, previously
undisclosed schedule suspension. All are in A16. Departures from the frozen
pre-registration are in `AMENDMENTS.md` (**A1–A16**).

---

## Abstract

Formal Contract-Driven Development (FCDD) organises an AI coding agent around a
machine-checked contract. Its stated purpose is **predictability**: work pinned
to a kernel-checked specification should land in a narrower band of cost and
behaviour than an unconstrained agentic session. Case 01 measured a cost
premium for FCDD but could not test the predictability claim at all: its
dispersion contrast rested on unreplicated cells, and the single defect it
replicated carried three runs per arm, a design whose best attainable two-sided
*p* is 0.10.

Case 02 was pre-registered to test it. Seven seeded single-byte faults in a
7,343-line Z80 assembly chess engine, four replicate repairs per arm per fault,
two arms, 56 runs, randomised order under a committed seed, with the estimator,
the test and the falsification condition all fixed before the first run. The
primary estimator is the coefficient of variation of log cost within each
defect-arm cell; the test is a two-sided exact paired permutation test across
the seven defects, whose attainable floor is *p* = 0.016.

**The predictability hypothesis is not supported.** The mean difference in
dispersion runs *against* it (−0.0547 — the ordinary arm was the less dispersed
one in five of seven defects), exact *p* = 0.1094, and the interval on the
median difference spans zero. Both pre-registered falsification conditions
fired. The verdict is unchanged in raw tokens (*p* = 0.0625) and output tokens
(*p* = 0.0625).

We also report, as disclosure rather than as a substituted headline, that the
**pre-registered estimator is defective**: it is not invariant under a change of
currency unit, and it is biased in FCDD's favour. Expressed in cents rather than
dollars the same data give *p* = 0.0469; under a scale-free dispersion
measure priced in dollars, *p* = 0.0156 — the design's floor — still against the
hypothesis, though that same measure gives *p* = 0.0625 in token units. Every
variant agrees on direction and they differ only on significance, so the reported
conclusion is robust.

The mechanism proposed to explain predictability fares worse. It held that the
ordinary arm forks between a minimal fix and a redesign while FCDD stays
stable. **No fork survived into the emitted code in either arm.** All 56 repairs — both arms, all seven
faults, every replicate — produced a binary byte-identical to the pristine
program, verified by sha256 against the sealed answer key. There is no strategy
variation to test, and no repair-quality difference available to detect;
blinded graders scoring 28 counterbalanced packets split 12–13 with three ties
(*p* = 1.0000).

What replicates is cost. FCDD was dearer on **7 of 7 faults**, median 2.26×
(1.83×–3.39× depending on the unit), exact sign test *p* = 0.0156 — the
attainable floor. The premium bought a byte-identical **program**; the arms'
wider work products differ, since only FCDD ships a specification package.

One observation outside the pre-registered set is worth the abstract's space.
While the repaired code converged completely, **neither arm's supporting
artefact did**: one distinct binary across 56 runs, against 23 distinct
kernel-accepted specification files across FCDD's 28 runs and 28 distinct test
artefacts across the control arm's 28 (§5.6, exploratory). The divergence is
symmetric and, on this measure, slightly worse for the control.
If predictability is the goal, it did not appear in the deliverable the method is
named for.

**Status of the method, as of this study:** for single-fault repairs of this
difficulty, FCDD's overhead bought no detectable improvement in cost
predictability or repair strategy, and no graded quality improvement, while
producing an **identical program** — though not an identical work product — for
roughly 2.3× the price, rising to 2.75× once the model contamination of A13 is
removed. We report this as a null on the method's
central claim, with two limitations that cut hardest against the study itself: 56/56 perfect convergence means this
benchmark can discriminate methods on cost and on nothing else, and the model
contamination in A13 means the arms were not, in the end, model-matched.

---

## 1. What Case 01 left open

Case 01 compared FCDD against ordinary development-plus-review on the same
seven seeded faults, one repair per arm per fault. It found a cost premium on
7 of 7 pairs (*p* = 0.016) and called that "the only statistically supportable
result in the study" — a figure that rests on one imputed value, since one pair's
cost was reconstructed from recovered token counts after the platform emitted no
record; on deposited values alone it is 6 of 7 at *p* = 0.125. On predictability
it could say almost nothing: only one defect was replicated, at three runs per
arm, and no dispersion statistic can reach α = 0.05 at that depth — the best
attainable two-sided *p* in a 3-vs-3 design is 0.10. The claim that FCDD exists to deliver
therefore *survived* Case 01 without being tested.

Case 01 also documented an oracle confound — FCDD's contract had been built by
reading the pristine engine, so the treated arm held a derived oracle the
control never received — and a grading round whose blinding, on its own later
measurement, had not occurred.

Case 02 exists to remove all three problems: give the design enough paired
units to reach significance, spend the oracle symmetrically, and build a
grading tier in which blinding is achievable and audited rather than asserted.

## 2. Design

**Faults.** All seven of Case 01's seeded single-fault variants (`bug01`–`bug07`),
reused unchanged with the sealed answer key intact. Each differs from pristine
in exactly one byte, in one instruction, in one routine — five in an instruction
operand (`bug01`, `bug02`, `bug05` an immediate; `bug03`, `bug07` the low byte of
a symbolic target) and two in the condition code of the opcode itself (`bug04`
`ret z`→`ret nz`, `bug06` `jr c`→`jr z`).

**Arms.** Arm A is ordinary development plus review, equipped with a
characterisation test suite. Arm B is FCDD, equipped with the frozen contract
package (Lean specification of record, Python twin, bridge conformance suite,
z3 tier).

**Replication and blocking.** k = 4 repairs per arm per fault. 7 × 4 × 2 = 56
runs, 28 matched pairs. Defect is the blocking factor; pairing is by defect,
not by run index.

**Randomisation.** Run order randomised across the whole 56-run schedule under
seed **20260807**, committed before the first run, so drift in service quality
cannot align with arm.

**Model — the claim as designed, and what actually ran.** The design required
the model to be "identical across arms, fixed for the whole study". Each run was
launched as `claude-opus-5` at maximum effort, in a fresh isolated session with
no network. **That requirement was not met, and we discovered it only under
adversarial review of this paper's first draft.** Both arm prompts instruct the
repair agent to spawn a reviewer with the Task tool, and those subagents did not
inherit the parent's model: `claude-fable-5` executed inside **51 of the 56
runs** and accounts for **28.6% of total spend**. Its share is not balanced
across arms — 35.5% of Arm A's budget against 25.7% of Arm B's, a 9.8-point
imbalance. The study therefore ran on a *mixture* in proportions the design
neither controlled nor measured. A13 records this in full and §8 carries it as a
threat; the consequences are stated where they bite, in §5.1 and §5.5.

**The oracle confound, spent asymmetrically in practice.** Arm A receives a
pristine-derived artefact of its own — a characterisation suite built by an agent
with the same access to the pristine engine FCDD's contract author had. The
heading in earlier drafts said "symmetrically"; the log does not support that
word. The design specified a cost-matched artefact at $21.75; the delivered suite
cost roughly **$8, some 63% under budget**, and was deliberately not padded
because the binding constraint was the engine's observable surface rather than
money (A1). The artefacts are therefore **scope-matched, not cost-matched**, and
they are not nested: Arm A's suite covers save/load round-trips that Arm B's
contract explicitly excludes, and Arm B's contract states properties that judge
any position where Arm A's suite records behaviour at 57 (A4).

Two further residuals from A4 belong here rather than in the log alone. The
suite's sharpest instrument — the legal-move buffer probe — was **inherited from
Arm B's own contract documentation**, not independently derived. And its measured
fault-detection was calibrated on four single-byte mutants; an earlier 49-case
version passed a pawn-value mutant 49/49 until material cases were added. Four
mutants is the whole evidence that the control's oracle bites.

The first build was discarded and rebuilt by an agent forbidden from reading the
fault-class list, after its builder disclosed having seen it (A2); the rebuild
comparison supported that decision (A4).

**Primary estimator and test, fixed before any run.** For defect *d* and arm
*a*, dispersion is the coefficient of variation of log cost across that cell's
four runs:

    CV_log(d,a) = sd( ln c₁..c₄ ) / | mean( ln c₁..c₄ ) |

Paired across the seven defects, tested by a two-sided **exact** permutation
test on `CV_log(d,A) − CV_log(d,B)`, enumerating all 2⁷ = 128 arm-label
assignments. α = 0.05; the attainable two-sided floor at seven pairs is
2/128 = **0.016**. Log scale because cost is positive and right-skewed — Case 01
watched estimator choice move its own headline from 2.8× to 4.3×, and this
pre-registration exists to remove that freedom.

**This estimator is defective, and we report the defect rather than the
replacement.** `CV_log` is not invariant under a change of unit: scaling every
cost by *k* sends `ln c → ln c + ln k`, which leaves the numerator alone and
moves the denominator. It therefore does not remove the estimator freedom it was
chosen to remove — it conceals it. §5.1 quantifies the consequence. The
pre-registered statistic is nonetheless retained as primary, because replacing it
after seeing the data is the very freedom §4 exists to close, and because the
better statistic favours the conclusion we already reported (A14).

**Attainable significance is not statistical power.** The floor of 0.016 says
only that *some* data could reach α; it says nothing about the effect size this
design could detect. No power analysis was performed, before or after. At seven
paired defects with four replicates the design is sensitive only to large
differences in dispersion — roughly a halving of log-cost spread — and a null
here is evidence of no *large* effect, not evidence of no effect.

**Falsification, stated in advance.** "A permutation *p* ≥ 0.05, or a median CV
difference whose CI spans zero, means the predictability claim is **not
supported** at this sample size, and that is what will be reported. The claim
has now survived one study that could not test it; it does not get a second
pass on a null."

## 3. Execution

The schedule ran from 2026-08-07 to 2026-08-23: 56 runs, 56.5 hours of agent
compute, mean 110 turns per run, **$1,382.74** total (Arm A $417.94, Arm B
$964.80). Every cell ultimately produced a clean result and no cell was
abandoned. **Three of the 56 were disrupted before completing**, in three
different ways: one hit a usage limit and was resumed in-session
(`bug05/B/r1`, A7); one was aborted deliberately when the driver was stopped to
fix a defect, and restarted from a pristine workspace (`bug06/A/r4`, A5); one was
killed by a host reboot and likewise restarted (`bug04/B/r1`, A6). Fifty-five of
the 56 *retained* results come from a first attempt, which is a different
statement and was conflated in v1.

**An under-count in the reported total.** Pre-registration §6 requires that a
disrupted run's partial cost be "recorded and excluded". For the two restarted
cells the partial attempts wrote no result JSON, so their cost was never captured
at all — it is excluded but not recorded. The reported $1,382.74 therefore
understates true spend by an unmeasured amount, plausibly a few tens of dollars
against a study of this size (A5, A6). It affects the total only; every
per-defect figure and every estimator input comes from completed runs.

Three execution events are recorded in `AMENDMENTS.md` rather than smoothed
over. Two defects in the schedule driver were found and fixed in the first two
cells (A5): a stdin bug that stopped the schedule after one run, and a
resume predicate that would have silently dropped a crashed cell from a design
requiring all 56. A host reboot killed the driver 37 minutes into cell 52,
leaving a nine-day gap before the final five cells (A6) — a gap that falls
unevenly across arms (three Arm B cells, two Arm A) and is disclosed as a
confound. A6 predicted its bias would be conservative — working against the
hypothesis. **That prediction was wrong in sign.** Measured: removing the five
post-gap runs moves the mean difference from −0.0547 to −0.0575, so the post-gap
runs pulled the result *toward* H1, not away. The effect is small and the verdict
is *p* = 0.1094 either way, but the guess is replaced by the measurement.

## 4. Two defects in the frozen analysis script

The pre-registration required the analysis script to be committed before the
first run, and it was (commit `16b95fe`, 2026-08-07, hours before the schedule
began). It was never run against real data, and shipped with two defects. Both
were found and fixed **before** it was executed for the first time, under §6's
clause permitting edits that fix a defect provided they are recorded.

**A7 — the excluded partial run was not excluded.** The cost extractor kept
every result file carrying a cost, never testing the error flag. Because the
runner writes one file per attempt, the interrupted attempt of `bug05/armB/r1`
would have entered that cell as a **fifth** observation, in violation of the
stopping rule's requirement that a partial cost be "recorded and excluded".
Blast radius: exactly one cell. Fixed with a one-line predicate.

**A8 — the script read a directory that does not exist.** It derived its input
path from its own location, but the runner hardcodes its output directory, so
all 57 result files sit in Case 01's ledger. As frozen, the script found zero
runs. This defect is fail-loud, not fail-silent: it could produce no number, not
a wrong one, which is why A7 was the one that needed care.

The lesson generalises past this study: **freezing a script before the data
exists means freezing one that has never seen real input.** Self-tests against
synthetic fixtures were run and caught neither. Future cases should freeze the
script *and* dry-run it against one completed cell before the schedule starts.

## 5. Results

### 5.1 Predictability (primary): not supported

| defect | nA | nB | CV_log A | CV_log B | A − B |
|---|---|---|---|---|---|
| bug01 | 4 | 4 | 0.1049 | 0.0995 | +0.0054 |
| bug02 | 4 | 4 | 0.0506 | 0.0418 | +0.0088 |
| bug03 | 4 | 4 | 0.0174 | 0.0745 | −0.0571 |
| bug04 | 4 | 4 | 0.0422 | 0.0830 | −0.0408 |
| bug05 | 4 | 4 | 0.0172 | 0.2199 | −0.2027 |
| bug06 | 4 | 4 | 0.0200 | 0.0206 | −0.0006 |
| bug07 | 4 | 4 | 0.0484 | 0.1439 | −0.0955 |

**Mean CV difference (A − B) = −0.0547. Exact two-sided permutation
*p* = 0.1094.** Median difference −0.0408, bootstrap interval (B = 100 000, seed
20260807) **[−0.0955, +0.0054]**, spanning zero.

That interval carries a caveat the pre-registration did not anticipate: a
bootstrap on the median of seven values can only return observed data points as
endpoints, so at n = 7 it is closer to a statement about the sign pattern of the
seven differences than to a smooth interval estimate. It is reported because §4
required it, and read as corroborating the permutation test rather than as
independent evidence.

Both pre-registered falsification conditions fired: *p* ≥ 0.05 **and** the
median CI spans zero. **H1 is not supported.**

The sign is worth stating separately from the significance. The point estimate
runs *against* the hypothesis: the ordinary arm was the less dispersed arm in
five of the seven defects under the pre-registered dollar measure — and in five
and six of seven respectively under the two token measures, with the H1-favouring
defects not always the same pair. FCDD did not make repair cost more predictable here; the
data lean the other way. The *p* forbids claiming that reversal as a finding,
but it also forbids reporting the result as a mere absence of evidence.

The exact *p* was recomputed by an independent implementation written from the
definition rather than reusing the frozen one; both return 0.1094 to machine
precision.

**Robustness to the cost unit.** Case 01's D3 rule held that Opus 5 is unpriced
and raw tokens should be the headline unit. Case 02's §7 fixes cost as the
`modelUsage` total, and we verified that `total_cost_usd` equals the per-model
`costUSD` sum exactly across all 57 files, so dollars are the pre-registered
measure and remain primary. Recomputing on other units does not rescue H1:

| unit | mean CV diff (A−B) | exact *p* |
|---|---|---|
| dollars (pre-registered, primary) | −0.0547 | 0.1094 |
| raw tokens, all four kinds | −0.0169 | 0.0625 |
| output tokens only | −0.0220 | 0.0625 |

All three are negative and all three miss α = 0.05. Under tokens the *reversal*
is nearer significance than under dollars. These are not three independent
confirmations — they are three recomputations over the same 56 runs differing
only in how effort is priced, and are collinear by construction. Their agreement
shows the verdict is not an artefact of the pricing model, nothing more.

**The estimator sensitivity, which is larger than any of the above.** §2 noted
that `CV_log` moves with the unit its inputs are expressed in. That is not a
theoretical concern here:

| dispersion statistic | in dollars | in cents |
|---|---|---|
| `CV_log` (pre-registered) | mean −0.0547, *p* = **0.1094** | mean −0.0254, *p* = **0.0469** |
| `sd(ln c)` (scale-free) | mean −0.2152, *p* = **0.0156** | mean −0.2152, *p* = **0.0156** |
| mid-spread of `ln c` (scale-free)† | mean −0.1729, *p* = **0.0156** | mean −0.1729, *p* = **0.0156** |

† the spread of the middle two of four log costs. An earlier draft called this an
interquartile range; on n = 4 it is not one, and the label is corrected rather
than the statistic.

**The pre-registered statistic crosses α on a change of currency unit.**

A necessary qualification on the replacement: `sd(ln c)` is invariant under
*scaling*, which is what the dollars/cents column demonstrates, but that is not
the same as invariance under a change of *measure*. Dollars and tokens are not
proportional to one another — the two models in play are priced differently and
cached input is nearly free — so `sd(ln c)` gives *p* = 0.0156 in dollars and
*p* = 0.0625 in tokens. The scale-free statistic removes the defect A14 names; it
does not make the significance of the reversal unit-independent, and an earlier
draft of A14 overstated this as "in any unit".

`CV_log` is also biased toward the hypothesis it tests: `|mean(ln c)|` sits in the
denominator and Arm B's costs are systematically ~2.26× higher, so Arm B's
dispersion is divided by a larger number in every defect (bug01: 3.01 for A
against 4.03 for B).

The pre-registered number stays the headline. Every statistic above agrees on
direction, so **H1 is unsupported under all of them**; they disagree only on
whether the reversal is significant. Two things follow, and the second is
uncomfortable for us. The reported conclusion is robust. And reading that
conclusion as a mere absence of evidence is *not* robust: under either scale-free
measure this data set significantly favours the opposite of H1, at the design's
floor. We do not claim that — it is reachable only post-hoc — but declining to
state it would be the same error in the direction that flatters the method.

**Robustness to any single defect.** Leave-one-defect-out, labelled post-hoc.
The pre-registration forbids excluding any cell for being an outlier, so none of
these is a headline. Note also what such a check can and cannot show: with all
seven differences already pointing one way or being near zero, no single deletion
could have produced significance *for* H1, so "no deletion makes H1 significant"
is a property of the sign pattern rather than evidence of robustness. What the
table does show is that no single defect drives the magnitude: *p* ranges 0.0938–0.2188 and
**no deletion makes H1 significant**. Dropping `bug05` — the cell flagged in
advance by A7 as holding one resumed-completion cost, with its predicted
inflating effect on that cell's CV — moves the mean difference from −0.0547 to
−0.0300. A7's prediction was correct in direction, and correcting for it
weakens the anti-H1 result without rescuing H1.

### 5.2 Both arms produced the identical program

All 28 blind graders independently reported that the two submissions in their
packet were byte-identical in executable content. The claim was verified rather
than accepted.

**Every repaired `chess.bin` — all 56, both arms, all seven faults — hashes to
`c107dfaf5b124f1d68770dc0937312933e55d4e21ed0e3b458ebc3a8c168dc0f`, which the
sealed answer key records as the *pristine* binary.** Confirmed three ways:
built-binary sha256 (28/28 pairs identical), instruction stream with all
comments stripped and whitespace normalised (28/28 identical), raw source
(0/28 identical — the entire difference is commentary).

Every run in both arms found the seeded fault and reverted it exactly. This is
the central empirical fact of the study, and it governs how §5.3 and §5.4 must
be read.

### 5.3 Strategy (H2): degenerate, not merely unsupported

H2 held that the ordinary arm's dispersion is driven by bimodal strategy
selection — forking between a minimal fix and a redesign — while FCDD stays
stable. §5 fixed the method for classifying a fix ("binary diff against pristine,
no judgement") but never a threshold, so all three judgement-free
operationalisations are reported (A9):

| rule | arm A (min/redesign) | arm B | Fisher *p* |
|---|---|---|---|
| **PRIMARY** — byte-identical to pristine, comments included | 1 / 27 | 0 / 28 | 1.0000 |
| **instruction stream** — all comments stripped | **28 / 0** | **28 / 0** | 1.0000 |
| **seeded line only** | **28 / 0** | **28 / 0** | 1.0000 |

The literal rule is near-vacuous: agents write explanatory comments, so exactly
one of 56 fixes is byte-identical to pristine. On the two rules that speak to
*code*, both arms are unanimous.

**H2 is not supported, and not because the trend was weak — because the
phenomenon it describes does not occur in the emitted code.** Neither arm ever
shipped a redesign.

That last qualifier is doing real work and v1 omitted it. This measurement sees
the *final* source, not the path taken to it. The paper's own cost data show
substantial within-cell variation, so runs plainly differed in how much work they
did; what the classification establishes is that **no fork survived into the
artefact**, not that no fork occurred during the session. The stronger claim
would need process traces, which this design did not capture.

An earlier version of this analysis (A9) reported a 7/21 versus 15/13 split at
*p* = 0.0543 on the seeded-line rule. A9 designated the literal byte-identity
rule primary and hedged that split explicitly as a trend rather than a claim;
even so, its reading — that FCDD chose the minimal fix more often — was wrong and
is withdrawn. The classifier stripped whole-line comments but not **trailing**
comments, so a changed trailing comment on an unchanged instruction counted as
changed code, and the 2×2 measured comment edits. A12 records the correction; the
classification script has been fixed so that the table above is what it actually
emits.

### 5.4 Quality: nothing left to measure

Twenty-eight counterbalanced packets, each pairing one Arm A and one Arm B
repair of the same fault, graded blind. Counterbalancing is exact and balanced
*within* every defect (two packets each way), so order cannot align with arm.

| axis | arm A | arm B | B − A | 95% CI | exact *p* |
|---|---|---|---|---|---|
| correctness_risk | 4.64 | 4.61 | −0.04 | [−0.14, +0.07] | 1.0000 |
| minimality | 4.71 | 4.32 | −0.39 | [−0.64, −0.18] | 0.0312 |
| clarity | 4.25 | 4.46 | +0.21 | [−0.18, +0.57] | 0.4375 |

Overall preference: **Arm A 12, Arm B 13, three ties; sign test *p* = 1.0000.**
Order effect: Submission X preferred 14, Y 11, three ties, *p* = 0.6900. That
test has little power over 25 decided packets and is not evidence *of* no
position bias; what warrants the claim is the design — counterbalancing is exact
and balanced within every defect, so any position preference is orthogonal to arm
by construction rather than by this *p*.

**These scores do not measure repair quality.** Since every pair compiles to the
same bytes (§5.2), no repair-quality difference was available to detect, and
the only thing that varied between submissions was the prose of the source
comments. The single significant axis is minimality, where graders scored FCDD lower.
v1 attributed that to comment volume without measuring it; v2 withdrew the
attribution on a measurement taken against the wrong denominator. Both are
corrected here. Whole-file comment characters differ by +40 (0.10%,
*p* = 0.2344) — but a grader never saw whole files, only the diff. **On the
diff, FCDD added +26.4% more comment text (212 characters against 168), paired
*p* = 0.1875.** So the direction v1 guessed is the direction the data show, on
the object graders actually read, and it is not significant at seven defects.
The honest position is that the minimality axis cannot be tracking repair scope,
since the repairs are identical; that added commentary is the leading candidate
and is directionally consistent; and that this study cannot establish it. This is a stronger statement than the pre-registration's predicted
"under-powered by construction": the tier is not under-powered, it is measuring
some property of prose we have not identified, and no claim rests on it.

### 5.5 Cost: the one result that replicates

| defect | mean A | mean B | ratio | A tokens† | B tokens† | token ratio |
|---|---:|---:|---:|---:|---:|---:|
| bug01 | $20.98 | $59.48 | 2.84× | 15.7M | 58.2M | 3.72× |
| bug02 | $13.84 | $24.39 | 1.76× | 9.1M | 21.3M | 2.34× |
| bug03 | $14.92 | $33.77 | 2.26× | 10.1M | 41.2M | 4.07× |
| bug04 | $14.77 | $38.96 | 2.64× | 9.8M | 42.3M | 4.31× |
| bug05 | $12.29 | $27.36 | 2.23× | 7.4M | 25.0M | 3.39× |
| bug06 | $14.92 | $27.24 | 1.83× | 10.5M | 24.2M | 2.30× |
| bug07 | $12.76 | $29.99 | 2.35× | 9.8M | 24.9M | 2.54× |

† per-run means within each four-run cell, not cell totals — the same basis as
the dollar columns.

**FCDD was dearer on 7 of 7 faults. Exact two-sided sign test *p* = 0.0156 —
the attainable floor at seven pairs.** Median ratio 2.26× in the
pre-registered dollar measure, 3.39× in raw tokens, 1.83× in output tokens; the
premium is robust in sign and 7/7 in every unit, while its magnitude depends on
the unit and is reported as a range rather than a point.

Case 01's only solid finding replicates, at four times the sample size and as
strongly as this design permits — and §5.2 anchors it to an identical program.

**Two qualifications.** First, **multiplicity**: this paper reports four
pre-registered outcomes and the *p* values are uncorrected, because the
pre-registration specified each test in advance and specified no correction. An
earlier draft claimed no result here could survive a Bonferroni correction; that
was wrong. At four tests the threshold is 0.05/4 = 0.0125, and the cost result at
0.0156 does *not* clear it — but the floor of 0.0156 is a property of the
seven-pair sign test, not of the design as such, and a different admissible test
would have a different floor. The accurate statement is narrower: **the cost
result is nominally significant and would not survive Bonferroni over these four
outcomes**, and readers who want a family-wise guarantee should treat it as
suggestive. Second, **model mix**: A13 established that Arm A spent 35.5% of its budget on a
second model against Arm B's 25.7%. An earlier draft said the contribution could
not be bounded with the data collected. **It can, from the same field that
revealed it.** Recomputing on the primary model's spend alone — removing the
subagent model entirely — gives a median ratio of **2.75×**, still 7 of 7, still
*p* = 0.0156. The contamination was therefore working in FCDD's favour: the
reported 2.26× understates the premium between like and like.

### 5.6 The specification did not converge (exploratory)

Not pre-registered. Found while investigating §5.2 and reported because it bears
directly on the method's central claim; it carries no inferential weight and no
*p*-value is computed for it.

§5.2 established that the repaired *code* converged completely. FCDD's own
principal artefact did not. **Twenty-two of the 28 Arm B runs modified
`Contract.lean`**; the other six — bug02/r2, bug02/r4, bug05/r1, bug05/r4,
bug07/r3, bug07/r4 — returned it byte-identical to the file they were handed,
having judged the frozen contract already adequate. Among the runs that did edit
it, the results do not agree with one another:

| defect | modified (of 4) | added lines | declarations shared by all *modified* runs |
|---|---|---|---|
| bug01 | 4 | +171 .. +236 | `qsearch` |
| bug02 | 2 | +75 .. +151 | `bug02KnightPos` |
| bug03 | 4 | +90 .. +157 | `bPromoPos` |
| bug04 | 4 | +140 .. +277 | `twoQueensPos` |
| bug05 | 2 | +87 .. +187 | none |
| bug06 | 4 | +159 .. +242 | none |
| bug07 | 2 | +32 .. +209 | none |

**Twenty-three distinct specification files across the 28 treated runs — the 22
edits, no two alike, plus the one untouched baseline — against a single distinct
binary across all 56 runs.** The units are stated explicitly because the
comparison is easy to inflate: counted per defect and summed, the figures are 25
and 7, not 25 and 1.

Four cautions bound this. The "shared by all modified runs" column is computed
over modified runs only; an earlier draft included untouched runs, whose empty
added-declaration set forced three intersections to zero by construction rather
than by disagreement. The comparison is **lexical, not semantic**: two
agents may formalise the same property under different names, so low name overlap
shows they did not converge on a shared vocabulary, not that they formalised
different things. **Six runs judged the existing contract sufficient**, which is
evidence for the method as much as against it — those runs did the cheap thing
correctly, and any reading of this section that treats specification-writing as
unavoidable overhead has to account for them. And every specification is **kernel-accepted** — all 28 `.olean` files are
present. That evidence is file existence, not a fresh build: we did not verify
that each `.olean` corresponds to the *final* `Contract.lean`, and for the six
untouched runs it is the seed build shipped into the workspace. That is the point worth carrying: Lean certifies that a
specification is well-formed, not that it is the right one, and not that two of
them say the same thing. Twenty-two mutually distinct formalisations of these
seven behaviours all passed the kernel, alongside six runs that added nothing.

The suggestive reading, offered as a hypothesis for a future pre-registration
rather than a finding here: on defects of this difficulty the fragile step is not
translating a specification into code — that step converged perfectly — but deciding what to write in the specification
in the first place. The convergence figure to quote here is **28 of 28**, the
treated runs; only those had a specification to translate from, and an earlier
draft cited 56 of 56, which counts control runs that never had one.
Note what this does *not* show. No specification here was demonstrated wrong;
none was even checked against another for semantic agreement. Variance is not
error, and establishing that these 22 formalisations actually disagree would take
a pairwise semantic comparison this study did not perform.

## 6. Blinding: audited, not asserted

Case 01 measured its blinding only after the verdicts were in, and found it had
failed: signature terms ran 0 for the ordinary arm against 37 for FCDD in a
single packet, so "every grader could identify the treatment with certainty",
and "blinded grading must be withdrawn as a competing-interest mitigation".

Scrubbing harder cannot fix that, and this study measured why. All 28 Arm B
workspaces carry a `contract/` package — Lean specification, twin, bridge
suite, z3 scripts. None of the 28 Arm A workspaces does; its tests are loose
scripts inside the variant directory. **The artefact category is the treatment
label.** No vocabulary substitution disguises a Lean file as a pytest script.

The blinded tier therefore grades **the source repair only**, where both arms
emit the same kind of object, and the test-quality axis is dropped with the
packages, because Case 01 showed that axis mechanically rewards shipping more
verification material — which is FCDD's definition (A10).

**The audit ran before grading.** The same signature-term count was applied to
all 28 packets, on the post-scrub text graders actually receive, before any
grader was launched. The first build **failed** it, 0 against 5, leaking in
3 of 28 packets — and the cause was the scrubber itself: its replacement
vocabulary ("specification", "a specification rule") consisted of signature
terms, so scrubbing introduced the tell it was removing, and two overlapping
rules collided into the visibly censored phrase *"specification a specification
rule"*, which announces redaction and only the treated arm can trigger. With arm-neutral replacements the rebuilt packets audited at 0 against 0 — **but
that audit was itself incomplete, and review of this manuscript found it so.**
The term list was written before the replacement vocabulary was chosen, so it did
not test for the scrubber's own output. Adding those phrases, the honest figure
is **0 for Arm A against 3 for Arm B, leaking in 3 of 28 packets**: the
substituted phrase "the design note" appears only where an FCDD comment cited its
contract. Blinding held on 25 of 28 packets and failed on three, by the same
mechanism — a scrubber introducing the tell it removes — that the first attempt
failed by. An adversary using this signal would be right on 3 of 3 decidable
packets and at chance on the rest: 55% overall.

**An independent manipulation check.** Seven further agents, separate from the
graders so scoring was not primed, were told one submission came from a
formal-methods process and asked which. Three answered "cannot tell"; of the four that decided, three were correct
(*p* = 0.6250 against chance). **That is a null, and we do not convert it into a
finding.** Seven probes, four decisions, and no counterbalancing within the check
itself mean its accuracy cannot be separated from a position preference; it
establishes neither that blinding held nor that it failed.

What the check does supply is qualitative and worth more than its arithmetic:
every one of the seven first observed that the two diffs were functionally
identical, then reasoned about **comment register** — a stated invariant, a named
failure mode, a citation to an external note. Term counting cannot detect that
channel, so we can say our audit was blind to a channel the probes used, without
being able to say how legible that channel actually is. It is an open residual, not a measured failure — and it sits alongside the
measured, if small, failure of the term-level audit above.

**The grader is the author.** All 56 repairs were produced by sessions launched
as `claude-opus-5`, with `claude-fable-5` reviewer subagents executing inside 51
of them (A13, §2); grading was run on `claude-opus-5` after the intended
alternative was unavailable (A11). On a study whose authors evaluate their own method, the judge
is the same system that produced both arms' work. No result in §5.4 should be
read as independent evaluation. What bounds it is that §5.2 leaves nothing to
be biased about.

## 7. Discussion

**The claim under test did not survive its first real test.** FCDD's stated
purpose is predictability. Given a design able in principle to reach *p* = 0.016,
the dispersion difference was not significant and its point estimate pointed the
wrong way. We are careful not to inflate that into "enough power": no power
analysis was done, and this design is sensitive only to large differences in
dispersion (§2). The result is evidence against a *large* predictability effect,
not against any effect. The pre-registration
committed in advance to reporting exactly this, and to the position that the
claim "does not get a second pass on a null".

**The convergence result is the more interesting finding, and it was not
predicted.** Both arms, on all seven faults, across all four replicates,
recovered the pristine program byte-for-byte. Two development methods with a
2.26× cost separation produced output that is not merely equivalent but
identical. Whatever FCDD's contract, twin, bridge suite and solver tier
contributed to the process, they did not change the artefact.

**What the premium bought.** Not a different repair, not a better repair, not a
more minimal one — the same **13,516-byte binary**, plus a specification package
and differently-worded comments. The specification package is a real deliverable
and a reader may value it; the arms' work products are emphatically *not*
identical, only their programs are. What the premium did not buy is
predictability or repair quality, because on this benchmark neither varied.

**An alternative explanation recorded before any run.** A3, written on
2026-08-07, predicted that Arm A's artefact — half of whose cases are golden
outputs rather than falsifiable assertions — "may make the artefact **less
decision-forcing** than the contract, and it is the most likely route by which
the two arms' artefacts differ in their effect on run cost. If you expect the
artefacts to equalise dispersion and they don't, this is the first place to
look." The artefacts did not equalise dispersion. A3 is therefore a live alternative to
any method-level reading of §5.1, and it was on the record before the data
existed. It bears on §5.5 as well, and earlier drafts applied it only to
dispersion: A3 names **run cost** explicitly as the channel it expects to differ,
so the surviving cost premium is exactly as exposed to it. A reader may
legitimately read the 2.26×–2.75× premium as the price of FCDD's method, or as
the price of holding a *more decision-forcing artefact* than the control was
given. This study cannot separate those, and the alternative was recorded before
any run.

## 8. Threats to validity

1. **The benchmark cannot discriminate on outcome.** 56/56 perfect convergence
   means these seven faults were, for this model at this effort, easy: single
   byte changes, unambiguous reports, reachable ground truth. A benchmark where
   every run of both arms succeeds perfectly can separate methods on cost and on
   nothing else. **Whether FCDD's apparatus pays for itself on faults hard
   enough to produce failures is a question this design is structurally unable
   to answer**, and it should not be read as having answered it. This is the
   single most important limitation of the study.
2. **The arms were not model-matched (A13).** `claude-fable-5` executed inside
   51 of 56 runs and took 28.6% of total spend, in unequal proportions by arm
   (35.5% of Arm A against 25.7% of Arm B), undetected until adversarial review.
   It injects into the primary estimator a source of within-cell dispersion that
   is not method. Its contribution **is** boundable, from the same per-model field
   that revealed it: on primary-model spend alone the cost premium rises to 2.75×
   and the primary estimator moves to −0.0718 (*p* = 0.0625). Both corrections run
   against FCDD, so the reported figures are the conservative ones.
3. **The pre-registered estimator is defective (A14).** `CV_log` is not
   scale-invariant — its verdict crosses α between dollars and cents — and it is
   biased toward H1 because the dearer arm is divided by a larger denominator.
   The pre-registered value is retained as primary and the sensitivity is
   disclosed in §5.1; a reader who prefers a scale-free statistic reaches a
   *stronger* anti-H1 conclusion than the one we headline.
4. **Two schedule discontinuities, not one.** A host reboot split the last five
   cells from the first 51 by nine days (A6); the tail holds three Arm B and two
   Arm A cells, so drift lands unevenly. A6 predicted its bias would be
   conservative and measurement showed the opposite sign, small (§3). Review of
   this manuscript then found a **second, previously undisclosed suspension**:
   `drive.log` records cell 14 running 88.6 hours wall clock against roughly 55
   minutes of agent time, the schedule having stalled on a weekly usage limit
   between 2026-08-08 and 08-12. More cells straddle an era boundary than A6
   assumed. Removing both the post-gap runs and the suspended cell gives
   mean −0.0628, *p* = 0.1094 — verdict unchanged, direction slightly stronger
   against H1 (A16).
5. **One non-exchangeable observation.** `bug05/armB/r1` was resumed rather than
   re-run after a usage limit, so its recorded cost is that of *finishing* an
   already-advanced repair (A7). It is the largest single contributor to the
   anti-H1 direction; removing it does not rescue H1.
6. **Artefacts are scope-matched, not cost-matched** (A1), and the arms are not
   nested — each covers ground the other does not (A4).
7. **The grader is the model under study** (A11), and blinding held at the level
   of vocabulary but not rhetorical style (§6).
8. **Single system, single language.** Seven faults in one Z80 assembly program
   at one effort setting — and, per A13, not one model.
9. **No correction for multiplicity.** Four pre-registered outcomes, uncorrected
   *p* values, and a cost result sitting exactly at the design's attainable floor
   (§5.5).
10. **Authors evaluate their own method.** Stated plainly; the pre-registration,
   the append-only amendment log, the deposited scripts and the committed
   falsification condition are the mitigations, and they are procedural, not
   structural.

## 9. Conclusions — the current status of the method

**On this benchmark, FCDD cost roughly 2.3× more than ordinary
development-plus-review and delivered nothing measurable in return.** That is the
status of the method as of this study, stated without qualification because the
qualifications that follow do not soften it — they bound what it generalises to.

The claim under test was predictability, which is the reason the method exists.
It failed. Under the pre-registered estimator the dispersion difference is not
significant (*p* = 0.1094) and its point estimate runs *against* the hypothesis.
Under a correctly scale-free dispersion statistic the same data favour the
opposite of the hypothesis at the design's attainable floor (*p* = 0.0156). We
headline the pre-registered number, but the direction is consistent across every
unit and every statistic examined, so this is not "we could not tell". **What
evidence exists points the other way.**

The mechanism offered to explain predictability is not merely unsupported but
degenerate: no run in either arm shipped anything other than the minimal fix.
Blinded grading found no difference in overall preference (12–13, *p* = 1.0000)
and none in correctness; it did score FCDD significantly lower on **minimality**
(*p* = 0.0312, CI excluding zero), which we report rather than round to "no
difference". Since all 56 repairs produced the identical program, that axis
cannot be tracking repair scope, and §5.4 sets out what little we can say about
what it is tracking. What replicates from Case 01 is
the cost premium — **7 of 7 faults, median 2.26×, *p* = 0.0156** — now anchored
to a byte-identical binary.

The sharpest single observation is not one of the pre-registered outcomes.
**Both arms converged on one program while neither converged on its own
supporting artefact.** Arm B produced 23 distinct specification files across 28
runs (22 mutually distinct edits, six runs leaving the contract untouched). Arm A
produced **28 distinct test artefacts across 28 runs — every one different**. An
earlier draft called FCDD's artefact "the least reproducible thing in the study";
measured against the control arm rather than against the binary, that is false,
and by this measure it is the *control* arm whose artefact is less reproducible.
What survives is the symmetric statement: the code converged completely and
neither method's authored artefact did (§5.6).

**What this does not license.** It is not a verdict on FCDD. The benchmark is too
easy: seven single-byte faults with reproducible symptoms, and both arms scored
100%. A method designed to prevent failures cannot be evaluated on a benchmark
that produces none — such a benchmark can only measure what the method costs.
Whether the specification, twin and conformance suite earn their premium on
defects hard enough to produce wrong answers is untouched here, and that is the
study worth running next. Two further limits are ours: the arms were not
model-matched (A13), so the premium's magnitude is contaminated; and the
pre-registered estimator was defective (A14).

**The scope of the claim, stated precisely.** For single-fault repairs of this
difficulty, in this language, under this model configuration and effort setting,
FCDD's overhead bought no detectable improvement in cost predictability or repair
strategy, and no improvement in graded repair quality except a *deficit* on
minimality; it produced an **identical program** — not an identical work product,
since only FCDD ships a specification package — for roughly 2.3× the price, or
2.75× once the model contamination is removed. Every word of that sentence is
load-bearing, and the method's proponents are entitled to every escape route it
leaves open.

**A closing observation, offered as an anecdote and not as evidence.** This
study's own two blocking defects — a second model running inside 51 of 56 cells,
and a primary estimator whose verdict moves with the currency unit — were caught
by an adversarial review panel, not by any formal check. Both had been sitting in
plain sight: one in a JSON field present in every result file from day one, the
other a one-line algebraic property of a formula printed in the pre-registration.
Pre-registration protects against choosing a statistic to fit the data. It does
not protect against choosing a wrong statistic before the data exists. On work of
this difficulty, careful adversarial review found what formality did not, and
found it more cheaply — which is the same shape as the result this paper reports.

## 10. Reproduction

**Runs from the deposited repository alone** — these read only the result JSON
under `case01_spectrum_gambit/ledger/raw/`:

```
tools/case02_schedule.py              # the frozen schedule (seed 20260807)
tools/analyse_case02.py               # PRIMARY: CV_log + exact paired permutation
tools/addendum_case02.py              # interval, independent p, §5 cost sign test
tools/robustness_tokens_case02.py     # per-defect token table + unit robustness
tools/estimator_sensitivity_case02.py # A14 scale-invariance + A6 gap sensitivity
tools/model_mix_case02.py             # A13 per-model, per-arm spend
```



**Requires the run workspaces** (`~/fcdd_arms/`, 56 directories, not in version
control — they hold full agent transcripts and build trees):

```
tools/h2_strategy_case02.py           # H2 2x2 (three rules) + Fisher
tools/code_identity_case02.py         # binaries vs the sealed key's pristine hash
tools/make_packets_case02.py          # 28 blinded counterbalanced packets
tools/blinding_audit_case02.py        # blinding audit (needs the packets + keys)
tools/comment_volume_case02.py        # §5.4 comment volume, both normalisations
tools/spec_divergence_case02.py       # §5.6 spec convergence + arm A comparator
tools/analyse_quality_case02.py       # unblind + quality analysis (needs the keys)
tools/drive_case02.sh                 # executes the schedule (needs the runner + API)
```

A replicator can re-derive every statistical claim in §5.1 and §5.5 from the
deposit, but **not** §5.2, §5.3, §5.4, §5.6, or §6's audit, which depend on
artefacts too large and too transcript-bearing to commit. Paths are absolute to
the host they ran on and would need adjusting.

Results are deposited under `ledger/`. The *raw* result files live in
`case01_spectrum_gambit/ledger/raw/`, because Case 02 deliberately reuses Case
01's runner (§4, A8); `case02_predictability/ledger/` holds derived outputs and
the driver log.

The pre-registration is frozen at commit `16b95fe` and every departure is in
`AMENDMENTS.md` (A1–A16). The 28 unblinding keys are excluded by an explicit
`.gitignore` rule — note they are deterministically regenerable from
`make_packets_case02.py`, so the seal is a convention, not a guarantee.
