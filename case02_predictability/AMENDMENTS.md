# Case 02 — amendments to the frozen pre-registration

Dated, appended, never rewritten. The pre-registration (commit `16b95fe`) is
frozen; everything that departs from it is recorded here with its reason, as
case01's A1–A10 were.

---

## A1 — the Arm A artefact came in under budget, and was not padded to match
**2026-08-07, before any repair run.**

Pre-registration §3 specified a cost-matched artefact at **$21.75**, the measured
cost of Arm B's contract. The delivered suite cost an estimated **~$8** (the
builder could not observe its own spend; it will be measured from the transcript
the same way step 1's $21.75 was).

The builder stopped early and explained why, and its reasoning is accepted: the
binding constraint was not money but the engine's **observable surface**. The
program's only outputs are keystrokes in, screen OCR out, and a 48K memory
snapshot; there is no way to ask it for a move list, a static evaluation, or
perft on an arbitrary position. Emulator runs cost seconds and zero tokens, so
~500 were used freely. Additional budget would have bought more *positions*, not
more *kinds of observation*, and padding to the number with near-duplicate
goldens would have produced a worse artefact.

**Consequence for the design:** the artefacts are **scope-matched, not
cost-matched.** This is a departure from §3 as written and is reported as such.
It weakens the symmetry claim in one direction (Arm A's oracle was cheaper) while
strengthening it in another (it was not inflated with filler). Any predictability
result must be read with this stated, not with §3's original wording.

---

## A2 — the artefact builder had seen the fault-class list; artefact rebuilt
**2026-08-07, before any repair run.**

The builder disclosed, unprompted, that it had read
`case01_spectrum_gambit/prompts/seeding_prompt.md`, which **names the seven
seeded fault classes**. Arm B's contract author never saw that document.

This is an asymmetry pointing the opposite way to case01's: it hands Arm A's
oracle author knowledge of *where the faults live*. The builder argued its
coverage checklist derived from the contract's own C1–C14 / S1–S4 clause map and
from the task statement, both of which predate and are independent of that
prompt, and that no test was aimed at a specific fault. It named the residual
honestly as one of **emphasis** — `term/`, `clock/` and the draw goldens are
where over-weighting would show.

That mitigation is plausible but not verifiable, and the entire purpose of case02
is to *remove* case01's confound rather than restate it. Launching a $1,560 study
with a known, avoidable asymmetry — when removing it costs roughly 0.5% of the
budget — would repeat the mistake this study exists to correct.

**Action:** the artefact is rebuilt by a fresh agent explicitly forbidden from
reading `prompts/`, the sealed directory, or the variants. The first artefact is
**retained, not deleted**, and the two are compared: if they cover substantially
the same ground, that is evidence the exposure did not bias the first, and the
comparison is reported either way. The rebuilt artefact is the one shipped to Arm
A runs.

---

## A3 — a predicted asymmetry in artefact *character*, recorded before data
**2026-08-07, before any repair run.**

Recorded now so it cannot be offered as a post-hoc explanation later. The builder
observed that **half its suite is not falsifiable as "wrong"**: 66 of 132 cases
are goldens, and a golden diff is not a defect — an Arm A run that legitimately
changes the search will correctly see red tier-2 cases. Arm B's contract has no
such category; every clause is a claim.

Its prediction, verbatim: this "may make the artefact **less decision-forcing**
than the contract, and it is the most likely route by which the two arms'
artefacts differ in their effect on run cost. If you expect the artefacts to
equalise dispersion and they don't, this is the first place to look."

If case02 finds a dispersion difference, this is a live alternative explanation
for it, and it was written down before any run.

---

## A4 — rebuild delivered; the v1/v2 comparison supports the decision to rebuild
**2026-08-07, before any repair run.**

The clean artefact is delivered and verified green on pristine independently by
the orchestrator (57 cases, 0 failed, exit 0). The rebuild agent confirmed it
read none of the forbidden paths; one disclosed nuance is that an `ls` of
`case02_predictability/` showed it the v1 directory's *name*, nothing inside.

**The comparison A2 promised.** A2 said that if the two artefacts covered
substantially the same ground, that would be evidence the fault-class exposure
had not biased v1. They do not. Counting identifier mentions in each suite's
case file, in exactly the areas v1's own builder predicted over-weighting would
show:

| area    | v1 (exposed) | v2 (clean) |
|---------|--------------|------------|
| clock   | 15           | 5          |
| draw    | 8            | 2          |
| terminal| 10           | 11         |

Three times the clock emphasis and four times the draw emphasis. This is a crude
proxy — the suites are structured differently and raw string counts are not
coverage — so it is offered as directional, not decisive. But the direction
matches a prediction recorded **before** the comparison was run, which is the
only version of this test worth anything. **The rebuild was justified**, and v2
is the artefact shipped to Arm A runs.

**New residuals from v2, recorded before data:**

1. **One observation channel was inherited, not discovered.** The legal-move
   buffer at `0x6000`/`genCount` — the sharpest instrument in the suite — came
   from D7 of `step1_contract/DECISIONS.md`, a read the task permitted. Not
   independently sourced.
2. **The artefacts are not nested.** Save/load round-trips are covered by v2 and
   were explicitly *out of scope* for Arm B's contract (D-SCOPE-1). Each artefact
   covers ground the other does not, so "same scope" is false in both directions.
3. **Extensional vs intensional.** The contract states properties that judge any
   position; the suite records what happened at 57 points. A repair can be green
   here while changing behaviour everywhere unobserved. No number of cases
   converts one into the other.
4. **A characterisation failure cannot distinguish a regression from a fix**,
   and names a position rather than a clause. Per v2's builder: *"if Arm B turns
   out more predictable, 'the contract localises the fault and the suite does
   not' is a live alternative explanation that this rebuild does not remove."*
   Recorded now, before any run, so it cannot be produced afterwards.
5. **Coverage calibration, measured.** An earlier 49-case version of v2 passed a
   pawn-value single-byte mutant 49/49 — the value table was invisible until
   `material` and lopsided-`search` cases were added. The delivered suite catches
   four single-byte mutants and a different build (44 red). Four mutants is the
   whole evidence that the case selection bites.

---

## A5 — two driver defects, found and fixed in the first two cells; one cell restarted
**2026-08-07, after run 1, before the schedule ran unattended.**

Logged under §6 ("every such event is logged"). Neither defect touches the
design, the artefacts, or the analysis; both are in the shell script that walks
the frozen schedule.

**Defect 1 — the schedule stopped after one run.** `schedule.json` was piped into
a `while read` loop; the model invocation inside the body consumed the pipe and
swallowed the remaining 55 lines. The driver logged `case02 COMPLETE` after cell
1 of 56. Fixed by reading the schedule into an array first, plus `</dev/null` on
the run. Verified by a dry run with a deliberately stdin-consuming body: 56/56
cells iterated.

**Defect 2 — the resume check could have silently dropped a cell.** The driver
skipped a cell when `arm<A>_<bug>_c2r<k>_a1_result.json` existed. But
`run_resilient.sh` creates that file **empty, by redirect, at attempt start**, so
a crashed or still-running cell has one — on any relaunch that cell would be
skipped and the design would quietly finish with fewer than 56 runs. The same
check is wrong in the other direction: a cell that succeeds on attempt 2 writes
`_a2_`, and an `_a1_`-only test would re-run a completed cell. Replaced with a
predicate that globs all attempts and requires JSON with `is_error` false —
exactly the condition under which `run_resilient.sh` exits 0. Unit-tested against
the real completed run, the empty stub, an absent file, and an `is_error:true`
file; all four classify correctly.

**Consequence for the data.** Cell **bug06 / arm A / run 4** had been executing
for ~8 minutes when the driver was stopped to apply defect 2's fix. Its workspace
carried partial edits, and a fresh agent starting on a dirty workspace is not the
run the design specifies, so the workspace is deleted and the cell is re-run from
pristine. The aborted attempt wrote no result JSON (the file was still the empty
stub), so **its partial cost is not captured in the ledger** — an under-count of
a few dollars against a ~$1,560 study, recorded here rather than estimated. The
driver now clears a dirty workspace before any restart of a cell, so this cannot
recur silently.

Cell 1 (bug01 / arm B / run 3) completed normally under the old driver and is
unaffected: the defects are in schedule traversal, not in how a run is executed.

---

## A6 — the host rebooted mid-schedule; cell 52 restarted after a nine-day gap
**2026-08-22, after cell 51, before the final five cells.**

Logged under §6 ("every such event is logged"). Nothing about the design, the
artefacts or the analysis changed; the machine went down.

**What happened.** The host rebooted at **2026-08-13 14:22:09** (`uptime -s`),
roughly 37 minutes into cell **52 / bug04 / arm B / run 1**, which had started at
13:44:50. The driver was `setsid`-detached, which survives a closing session but
not a reboot, so the schedule stopped at 51 of 56. There is no application-level
failure behind it: the cell's stderr log is empty, no `FAILED` line was ever
written, and all 51 completed cells succeeded on attempt 1.

The A5 fixes did their job on restart. `cell_done()` correctly classified cell 52
as **not** done despite its zero-byte `_a1_` result stub — the exact silent-drop
failure A5 was written to prevent — and the driver deleted the dirty workspace
`~/fcdd_arms/bug04_armB_c2r1` (last written 14:09, carrying a partially built
contract) so the restarted cell begins pristine. As in A5, the aborted attempt
wrote no result JSON, so **its partial cost is not captured in the ledger**: an
under-count of roughly one cell-hour against a ~$1,560 study, recorded here
rather than estimated.

**The confound this introduces, stated plainly.** The schedule resumed on
**2026-08-22 23:33**, a **nine-day gap** between cell 51 and cell 52. Cells 1–51
ran against whatever model and CLI build were current 2026-08-07 to 08-13; cells
52–56 run against whatever is current on 08-22. If either moved in between, the
last five cells were produced by a different generator than the first 51.

This is not neutral with respect to the design. The randomised schedule put
**three arm B cells and two arm A cells** in the tail (52 bug04/B, 53 bug03/B,
54 bug07/A, 55 bug03/B, 56 bug01/A), so any drift lands unevenly across arms and
falls hardest on bug03, which contributes two of its four arm B replicates from
after the gap. Because the estimator is a *within-defect dispersion* statistic,
a level shift in cost between the two eras inflates `CV_log` for exactly the
defect-arm cells that straddle it — and it inflates arm B's more than arm A's.
The direction of that bias is toward *less* apparent predictability for arm B,
which is against the authors' hypothesis, but a bias that happens to be
conservative is still a bias and is reported as one.

No re-run of the first 51 cells is attempted: re-running them would cost the
study over again and would itself be run in the new era, trading a known
five-cell exposure for an unknown fifty-one-cell one. The gap is recorded here
instead, before the statistic is computed, so it cannot be produced afterwards
as an explanation of whatever the result turns out to be.

---

## A7 — a defect in the frozen analysis script: the excluded partial run was not excluded
**2026-08-23, after all 56 cells completed, before the analysis script was run.**

Recorded under §6, which permits exactly this: the script "is not edited
afterwards except to fix a defect, which is recorded as an amendment." Written
and committed **before** `analyse_case02.py` was executed for the first time. No
dispersion statistic had been computed or inspected at the time of writing.

**The defect.** `cell_costs()` globbed `arm<A>_<bug>_c2r*_result.json` and kept
every file carrying a truthy `total_cost_usd`. It never tested `is_error`. Since
`run_resilient.sh` writes one result file **per attempt**, a cell that needed a
second attempt leaves two files, and both would enter the estimator.

**Blast radius: exactly one cell.** Thirteen of the fourteen (defect, arm) cells
glob exactly four clean files. The exception is **bug05 / arm B**, where run 1's
first attempt hit the weekly usage limit after 108 turns and $19.51, and a second
attempt resumed the same session and completed in 34 turns for $8.59. That cell
would have been analysed with **five** observations, one of them a partial run
that §6 requires be "recorded and excluded".

**The fix.** One line — `if d.get("is_error"): continue` — before the cost is
read. Nothing else in the script changed: the estimator, the test, the
enumeration and the verdict logic are untouched.

**The residual this does not fix, stated before the result was seen.** §6
specifies that an infrastructure-killed run is **re-run** at the same cell. The
runner **resumed** it instead, so the retained observation ($8.59) is the cost of
*finishing* a repair that was already 108 turns advanced — not the cost of a
whole repair, which is what the other 55 observations measure. Excluding the
partial attempt satisfies §6's letter while leaving one non-exchangeable,
unusually cheap observation in bug05 arm B.

The direction is determinate. A single low outlier among four widens that cell's
spread of log cost, so `CV_log(bug05, B)` is **inflated**. H1 predicts arm B is
the *less* dispersed arm, so this defect works **against** the authors'
hypothesis. A conservative bias is still a bias, and bug05 arm B should be read
with it in mind — including in the sensitivity direction, since dropping the cell
would remove one of only seven paired defects.

No attempt is made to repair this by re-running the cell. Doing so now would run
it in the post-gap era described in A6, trading a known distortion for an unknown
one, and would be a re-run chosen **after** the schedule completed — precisely
the discretion this pre-registration exists to remove.

**A §7 conformance check that passed, recorded for completeness.** §7 fixes the
cost measure as "the `modelUsage` total including subagents", and the script
reads `total_cost_usd` instead — its `KEYS` tuple of modelUsage fields is
defined and never used. All 57 case02 result files were checked: `total_cost_usd`
equals the sum of per-model `costUSD` **exactly**, to zero relative deviation.
The script therefore measures the pre-registered quantity. The mismatch is a dead
constant and a docstring, not a data defect, and is left in place rather than
edited, since §6 permits editing only to fix a defect.

---

## A8 — a second defect in the frozen script: it read a directory that does not exist
**2026-08-23, minutes after A7, still before the analysis script was run.**

Recorded separately from A7 rather than folded into it, because it was found
after A7 was written. The amendment log is append-only and its value is that it
preserves the true order of discovery.

**The defect.** The script derived its input directory from its own location:

    CASE = dirname(dirname(abspath(__file__)))       # .../case02_predictability
    RAW  = join(CASE, "ledger", "raw")               # .../case02_predictability/ledger/raw

That directory **does not exist**. Every case02 result file is in
`case01_spectrum_gambit/ledger/raw`, because the runner is case01's
`run_resilient.sh`, which hardcodes `CASE=/…/case01_spectrum_gambit` at line 20
and derives `RAW` from it. The case02 driver reuses that runner deliberately —
identical execution machinery across both cases — and inherited its output path
with it. All 57 result files (56 cells + one excluded partial) are there; zero
are where the analysis script looked.

**The fix.** `RAW` now points at the directory the runner actually writes to,
expressed relative to the repository rather than as an absolute path. No
estimator, test, selection rule or verdict logic is touched.

**Why this one could not have corrupted a result.** It is fail-loud, not
fail-silent. With `RAW` pointing at a non-existent directory the glob returns
nothing, `cell_costs` returns an empty list for all fourteen cells, and the
script exits at its own guard — `not enough complete defects yet (need >=2,
have 0)`. It cannot produce a wrong number; it can only produce no number. That
is the opposite failure mode from A7, which would have silently admitted a fifth
observation into one cell, and it is why A7 is the one that needed care.

**What this says about the freeze.** `analyse_case02.py` was committed in
`16b95fe` on 2026-08-07, before the first run began at 18:07:57 that day — the
freeze §6 requires genuinely held. But committing a script before the data
exists means committing a script that has never been run against real data, and
both A7 and A8 are the consequence. The pre-registration bought the property it
was designed to buy (no estimator choice was made after seeing results) at the
cost of shipping two defects into the frozen artefact. Self-testing the script
against synthetic fixtures — which was done, and which caught neither — does not
substitute for pointing it at the real ledger. For any future case, freeze the
script **and** dry-run it against a single completed cell before the schedule
starts.

---

## A9 — §5 fixed H2's method but not its threshold; three operationalisations, and a classifier defect fixed mid-analysis
**2026-08-23, after the primary result, during the secondary analysis.**

**The gap.** §5 says each fix is "classified mechanically as *minimal* or
*redesign* by binary diff against pristine (zero marginal cost, no judgement)".
That fixes the *method* — diff against pristine, no LLM in the loop — but never
fixes a *threshold*. Taken literally, "binary diff" means byte-identity, and
byte-identity turns out to be nearly vacuous: agents add explanatory comments, so
**1 of 56** runs is byte-identical to pristine and the 2×2 is degenerate
(p = 1.0000). Reporting only that would hide the question rather than answer it.

Three judgement-free operationalisations are therefore computed and **all three
reported**, with the literal one designated primary because it is what §5 says:

| | rule | arm A (min/redes) | arm B | Fisher p |
|---|---|---|---|---|
| PRIMARY | byte-identical to pristine | 1 / 27 | 0 / 28 | 1.0000 |
| S1 | identical after dropping blank lines and whole-line `;` comments | 4 / 24 | 7 / 21 | 0.5027 |
| S2 | the only non-comment edit is a one-line replace **of the seeded line itself** | 7 / 21 | 15 / 13 | 0.0543 |

No LLM classified anything; all three are lexical operations on the source plus
the sealed key's own diff hunk. That the threshold was not pre-registered is a
defect in the pre-registration, disclosed here rather than resolved by picking
whichever of the three reads best.

**A classifier defect, found and fixed after its first output.** S2's first
implementation detected only pristine lines that had gone *missing* from the
fix; insertions were invisible, so a run that reverted the seeded line and then
added fifty lines of new code scored *minimal*. It was rewritten as a proper
`SequenceMatcher` alignment in which every non-equal hunk counts, and
self-tested against seven constructed workspaces (perfect revert; revert plus a
comment; the seeded line replaced by equivalent text; revert plus fifty added
lines; an unrelated line deleted; the seeded line fixed plus one edit elsewhere;
a whole source file removed) — all seven now classify correctly.

Disclosed in full because the fix came **after** seeing the defective version's
output: S2 moved from 11/19 to **7/15**, and its exact p from 0.0598 to
**0.0543**. The correction did not manufacture a result — neither version
crosses α = 0.05, and the shift is a fifth of the distance to it. One of the
seven self-test expectations was also wrong and was corrected rather than the
code: a fix that changes only the seeded line, even to semantically equivalent
text (`cp 15` for `cp MAXPLY`), *is* minimal under S2's definition.

**What H2 actually shows, and it is not what H2 predicted.** H2 held that "Arm
A's cost dispersion is driven by bimodal strategy selection — forking between a
minimal fix and a redesign — while Arm B's strategy is stable." Under S2 the
assignment is **reversed**: arm B is the near-even split (15/13, 54% minimal)
and arm A is the concentrated one (7/21, 25% minimal, consistently redesigning).
This is coherent with the primary result — H1 also reversed, with arm A the
*less* cost-dispersed arm — but at p = 0.0543 it is a trend and is reported as
one, not as a claim. H2 was offered as the mechanism *for* H1; H1 did not hold in
the predicted direction, so there is no dispersion difference of the predicted
kind for this mechanism to explain.

**An independence caveat §5 did not address.** The Fisher test treats the 56
runs as independent units, as §5 specifies. They are not: runs are nested within
seven defects, and the per-defect breakdown shows strong defect effects — bug07
is minimal in 8 of 8 runs across both arms, bug04 redesign in 8 of 8. The true
number of independent units is nearer seven than fifty-six, so the reported p is
anti-conservative. Since S2 does not reach significance even at its
anti-conservative value, the conclusion is unaffected; a defect-clustered test
would only widen it further.

---

## A10 — the quality tier redesigned so that blinding actually occurs
**2026-08-23, packets built and audited before any grader saw one.**

§5 asks for "blinded, counterbalanced grading as in case01 §5.3, **with the
packet defects of §4.5 fixed**". §4.5's central finding was not that case01's
scrubbing was imperfect. It was that blinding **did not happen at all**:
signature terms ran 0 for the ordinary arm against 37 for FCDD in a single
packet, so "every grader could identify the treatment with certainty", and
"blinded grading must be withdrawn as a competing-interest mitigation".

**Why scrubbing harder cannot fix it.** Measured across this study's own
workspaces: all 28 arm B workspaces carry a `contract/` package — a Lean
specification, a Python twin, a bridge conformance suite, z3 scripts. None of
the 28 arm A workspaces does; arm A's tests are loose scripts inside
`variants/`. The artefact **category** is the treatment label. No vocabulary
substitution disguises a Lean file as a pytest script.

**The change.** The blinded tier grades **the source repair only** — the
unified diff against the seeded tree, across the seven engine sources — where
both arms emit the same kind of object. Verification packages are excluded from
it entirely, and with them the **test-quality axis is dropped**, because §4.5
showed that axis "mechanically rewards shipping more verification material,
which is FCDD's definition". The blinded axes are correctness risk, minimality
and clarity. Counterbalancing is deterministic and balanced *within* every
defect: run indices 1 and 3 present arm A as Submission X, 2 and 4 present arm
B, so each defect contributes two packets each way and order cannot align with
arm.

**What this costs, stated plainly.** The blinded tier can no longer speak to
FCDD's principal deliverable. If the method's value is the specification and the
conformance suite rather than the diff, this tier is blind to exactly that. It
answers a narrower question — *is the repair itself better?* — and that is the
only quality question this design can ask under genuine blinding. Any claim
about artefact quality would require an openly unblinded comparison and must be
labelled as such; none is made here.

**Blinding audited before grading, not after.** Case01 measured its blinding
only once the verdicts were in. The same signature-term count was run here on
all 28 packets, on the post-scrub text graders actually receive, before any
grader was launched.

The first build **failed** that audit: 0 for arm A against 5 for arm B, leaking
in 3 of 28 packets. The cause was the scrubber itself. Its replacement
vocabulary — "specification", "a specification rule" — consisted of signature
terms, so scrubbing *introduced* the tell it was removing, and two overlapping
rules collided into the visibly censored phrase "specification a specification
rule", which announces that the text was redacted. Only the treated arm can
trigger that. The replacement vocabulary was made arm-neutral ("the design
note", which either arm could plausibly cite) and a collapse pass added for
overlapping rules. The rebuilt packets audit at **0 against 0**, with no packet
decidable on that signal.

**An independent manipulation check.** Term counting is a proxy. Seven further
agents — one per defect, separate from the graders so the scoring is not primed
— are given a packet, told that one submission came from a formal-methods
process and the other from ordinary development plus review, and asked which,
with "cannot tell" offered as an explicitly acceptable answer. Their accuracy is
the real blinding measure, and it is reported whatever it shows.

**Graders run on a different model from the one under study.** All 56 repairs
were produced by `claude-opus-5`. Grading them with `claude-opus-5` would have
the model score its own output, on a study whose authors are evaluating their
own method — a second conflict layered on the one §4.5 already withdrew a
mitigation for. Graders and blinding-checkers therefore run on `fable`. This is
a departure from case01, where grading used the same model as the arms, and it
is recorded rather than quietly adopted.

---

## A11 — grader model: Fable was unavailable; graders run on the model under study
**2026-08-23, after A10's first grading launch failed, before any grading data existed.**

A10 specified `fable` for graders and blinding-checkers, to avoid having
`claude-opus-5` — the model that produced all 56 repairs — score its own output.
That launch failed outright: all 35 agents returned "You've reached your Fable 5
limit" within 13 seconds, producing zero tokens, zero cost and zero verdicts.
A10's routing is therefore superseded here rather than in place, since this log
is append-only.

**Decision, taken by the operator when the alternatives were put to them:**
grading proceeds on **`claude-opus-5`**, the same model that wrote every
submission. The alternatives offered and declined were: Sonnet 5 (a different
model, available immediately), waiting for the Fable quota to reset, and running
both models for an inter-model reliability measure.

**The limitation this creates, stated without hedging.** The grader is the
author. On a study whose authors already evaluate their own method, the judge is
now the same system that produced both arms' work. If `claude-opus-5` has any
systematic preference for the style of output it generates under a formal
process, this design cannot separate that preference from a genuine quality
difference. No result from this tier should be read as independent evaluation.

**What bounds it, and why the bound is checkable rather than asserted.** The
grader sees only blinded source diffs, with verification packages excluded and
the arm-identifying vocabulary removed; that material audits at 0 signature
terms against 0 across all 28 packets (A10). So the grader cannot straightforwardly
identify which submission came from which process — and the seven blinding-check
agents, which run on the same model, measure precisely that. If they identify
the treated submission at better than chance, this tier's verdicts are
compromised and will be reported as such. If they sit at chance, the
self-grading confound is bounded by the same blinding the term count already
passed. Either way the check is reported, and it is reported whichever way it
comes out.

---

## A12 — every run in both arms produced the identical program; H2 as reported in A9 was measuring comments
**2026-08-23, after the blinded grading returned.**

**The finding.** All 28 blind graders independently reported that the two
submissions in their packet were byte-identical in executable content. That
claim was checked rather than accepted. The sha256 of every repaired
`chess.bin` — all 56, both arms, all seven defects — equals
`c107dfaf5b124f1d68770dc0937312933e55d4e21ed0e3b458ebc3a8c168dc0f`, which the
sealed answer key records as the **pristine** binary. Confirmed three ways:
built-binary hash (28/28 pairs identical), instruction stream with all comments
stripped and whitespace normalised (28/28 identical), raw source (0/28 identical
— the entire gap is commentary).

**Every one of the 56 runs found the seeded fault and reverted it exactly.**
Both arms, every defect, every replicate. The repair is not merely similar
across arms; it is the same program, and it is the original program.

**This corrects A9's H2 result, which was an artefact of my comment handling.**
A9 reported a 2×2 of 7/21 (arm A) against 15/13 (arm B) on the "seeded-line
only" rule, p = 0.0543, and read it as arm B choosing the minimal fix more
often. That reading is wrong. The `strip_comments` helper dropped blank lines and
*whole-line* `;` comments but not **trailing** comments, so a line reading
`cp MAXPLY ; new note` differed from pristine's `cp MAXPLY ; too deep` and was
counted as a changed hunk. The 2×2 was therefore counting **comment edits**, not
repair strategy, on all three of its rules — the near-vacuous byte-identity rule
included.

At the level of emitted code the corrected table is:

|        | minimal | redesign |
|--------|---------|----------|
| arm A  | 28      | 0        |
| arm B  | 28      | 0        |

Fisher exact p = 1.0000, degenerate: there is no variation to test. **H2 is not
supported, and not because the trend was weak — because the phenomenon H2
describes does not occur in this data.** H2 held that arm A forks between a
minimal fix and a redesign while arm B stays stable. Neither arm forked. No
run in either arm chose a redesign.

**What this does to the quality tier.** The blinded graders were asked which
repair was better. Since every pair of repairs compiles to the same bytes, there
was no repair-quality difference available to detect, and the scores they
returned necessarily reflect the only thing that varied: the prose of the source
comments. The tier is reported for completeness, but it does not measure repair
quality, and no claim about repair quality can rest on it. That is a stronger
statement than §5's pre-registered "under-powered by construction": the tier is
not under-powered, it is measuring a different variable than intended.

**What this does to the cost result, which is the opposite of weakening it.**
The §5 cost finding — FCDD dearer on 7 of 7 defects, median 2.26×, sign test
p = 0.0156 — is now anchored to an identical work product. The premium did not
buy a different repair, a better repair, or a more minimal repair. It bought the
same 15,295 bytes, plus a specification package and more comments.

**A limitation this creates for the study's external validity, stated against
interest.** Total convergence at 56/56 also means these seven defects were, for
this model at this effort, easy: single-byte faults with unambiguous reports and
a reachable ground truth. A benchmark on which every run of both arms succeeds
perfectly cannot discriminate methods on outcome quality, and can only
discriminate on cost. Whether FCDD's verification apparatus pays for itself on
defects hard enough to produce failures is a question this study is structurally
unable to answer, and the design should not be read as having answered it.

---

## A13 — a second model ran inside 51 of the 56 cells, and its share differs by arm
**2026-08-23, found by adversarial review of the article draft, after all results were computed.**

§2 of the pre-registration requires "Model and effort: **identical across arms**,
fixed for the whole study, no mid-study change", and the article draft asserted
that the study ran on `claude-opus-5` throughout. That is false, and the ledger
had said so all along in a field nobody read.

Recomputed from the `modelUsage` block of all 56 non-error result files:

| model | runs containing it | spend | share |
|---|---|---|---|
| `claude-opus-5` | 56 / 56 | $986.71 | 71.4% |
| `claude-fable-5` | **51 / 56** | **$396.03** | **28.6%** |

And the mix is **not balanced across arms**:

| arm | total | opus-5 | fable-5 |
|---|---|---|---|
| A | $417.94 | $269.75 (64.5%) | $148.18 (**35.5%**) |
| B | $964.80 | $716.96 (74.3%) | $247.85 (**25.7%**) |

**Mechanism.** Both arm prompts instruct the repair agent to spawn a reviewer
with the Task tool — arm A a code reviewer, arm B an adversarial attack round.
Those subagents did not inherit the `--model claude-opus-5` passed to the parent;
they resolved to `claude-fable-5`. The runner set the model for the session it
launched and had no control over what the session delegated to. The
pre-registration's "identical across arms" clause was written about the agent and
silently did not bind its children.

**What this contaminates.**

1. **The model claim is withdrawn.** The study did not run on a single model. It
   ran on a *mixture*, in proportions the design did not control and did not
   measure until now.
2. **The arms are not model-matched.** Arm A spent 35.5% of its budget on the
   second model against arm B's 25.7%. Any per-token price difference between
   the two models therefore enters the cost ratio as a component that is not
   method.
3. **It is a source of dispersion unrelated to method.** How much of a run went
   to subagents varied run to run. That variance lands directly in the primary
   estimator, which measures within-cell dispersion of cost. Some unknown part
   of every `CV_log` in §5.1 is subagent-mix variance rather than method
   variance — in both arms.

**What it does not touch.** The convergence result (A12) is a property of the
emitted binaries and is independent of which model produced them: all 56 still
hash to pristine. The 7/7 direction of the cost premium is likewise unaffected,
since arm B was dearer in every defect in all three units; only the *magnitude*
of the ratio is now known to carry a model-mix component.

No re-run is attempted. Re-running would cost the study again and could not
restore the pre-registered condition retroactively. The contamination is
disclosed, quantified, and carried into the article's threats section instead.

---

## A14 — the pre-registered primary estimator is not scale-invariant; its verdict moves with the currency unit
**2026-08-23, found by adversarial review, after the primary result was computed and reported.**

§4 fixed the estimator as

    CV_log(d,a) = sd( ln c₁..c₄ ) / | mean( ln c₁..c₄ ) |

and justified it as removing the estimator freedom that moved case01's headline.
It does not remove that freedom; it hides it. **The statistic is a function of
the unit the costs are expressed in.** Scaling every cost by *k* sends
`ln c → ln c + ln k`, which leaves the numerator unchanged and shifts the
denominator, so the ratio moves. Demonstrated on this study's own data, changing
nothing but dollars to cents:

| estimator | in dollars | in cents |
|---|---|---|
| `CV_log` (pre-registered) | mean −0.0547, *p* = **0.1094** | mean −0.0254, *p* = **0.0469** |
| `sd(ln c)` (scale-free) | mean −0.2152, *p* = **0.0156** | mean −0.2152, *p* = **0.0156** |

The pre-registered statistic **crosses α = 0.05 on a change of currency unit**.
A second defect compounds it: because `|mean(ln c)|` sits in the denominator and
arm B's costs are systematically ~2.26× higher, arm B's dispersion is divided by
a larger number in every defect (e.g. bug01: 3.01 for A against 4.03 for B). The
estimator is therefore **biased in favour of H1** — it deflates the treated arm's
measured dispersion by construction.

**How this is handled, and how it is not.** The pre-registered result stands as
**primary and is not replaced**: *p* = 0.1094, H1 not supported. Swapping in a
better estimator after seeing the data is exactly the freedom §4 exists to
remove, and the fact that the better estimator is more favourable to *our own*
reported conclusion makes the temptation worse, not better.

What changes is disclosure. Every version of the analysis agrees on **direction**
— the ordinary arm is the less dispersed one — and they differ only in whether it
reaches significance:

* pre-registered `CV_log` in dollars: not significant (*p* = 0.1094);
* the same statistic in cents: significant (*p* = 0.0469);
* scale-free `sd(ln c)`, in any unit: significant at the design's floor
  (*p* = 0.0156).

So the headline conclusion — **H1 is not supported** — is robust; no estimator
rescues it. What is *not* robust is the article's implicit claim that the null is
merely an absence of evidence. Under a correctly scale-free dispersion measure
this data set significantly favours the **opposite** of H1. That stronger
statement is not claimed, because it was not pre-registered and is reachable only
post-hoc, but suppressing it would be the same sin in the other direction.

The estimator defect is a defect in the **pre-registration**, not in the analysis
script, which implemented §4 faithfully. Future cases should require the primary
estimator to be checked for invariance under the transformations its own units
admit, before the schedule starts.

---

## A15 — v1 of the article was adversarially reviewed before publication; what it got wrong
**2026-08-23, after draft v1, before any submission.**

Draft v1 was put through a five-lens adversarial review (numerical fidelity,
overclaiming, statistical validity, internal consistency, reproducibility), with
every finding independently verified before it was accepted. Sixty-seven findings
were raised and **43 survived verification**: 11 blocking, 17 major, 15 minor.
Two of the blocking ones are large enough to have their own amendments (A13,
A14). This entry records the rest, because a paper that reports a null on someone
else's method should be at least as exact about its own errors.

**Numbers v1 asserted that were wrong.**

* **"15,295 bytes"** for the repaired program. Invented; it appears in no
  deposited artefact. The binary is **13,516 bytes** (`chess.tap`, a different
  artefact, is 13,596). The figure also appears in A12 above, which is left
  standing as written per this log's append-only rule and corrected here.
* **"three matched pairs"** for case01's predictability data. Case01 replicated
  one defect at three runs per arm; its attainable floor was *p* = 0.10, not what
  v1 implied.
* **"single-byte change to one instruction operand"** for all seven faults. Five
  are operand changes; two (`bug04`, `bug06`) change the condition code in the
  opcode byte itself.
* **case01's 7/7 cost premium** was cited without its own published caveat: one
  pair's cost is imputed, and on deposited values alone it is 6/7 at *p* = 0.125.

**Claims v1 made without measuring, now measured.**

* **The minimality result is not comment volume.** v1 asserted that graders
  scored FCDD lower on minimality because it wrote more commentary. Measured:
  comment characters differ by **+40 across the whole engine source — 0.10% —
  paired *p* = 0.2344**. The explanation is withdrawn, and no replacement is
  offered, because we do not have one.
* **The nine-day gap's bias runs the other way.** A6 predicted it was
  conservative with respect to H1. Measured: dropping the five post-gap runs
  moves the mean difference from −0.0547 to −0.0575, so those runs pulled *toward*
  H1. Small, verdict-neutral, and the opposite of the prediction.
* **"Enough power"** was asserted three times and never computed. Replaced
  throughout with the accurate statement — the design could in principle *reach*
  significance, which is not the same as being powered for a given effect.
* **"Neither arm ever forked"** claimed a fact about strategy from evidence about
  final source. Narrowed to what the measurement supports: no fork survived into
  the emitted code.

**Provenance gaps, fixed by repairing the tooling rather than softening the
prose.** v1's header promised every number re-derived from the named scripts.
That was false in three places, all now true: `h2_strategy_case02.py` still
emitted the numbers A12 withdrew (the A12 fix had only ever been applied
inline, never written back); the per-defect token table had no deposited source;
and `code_identity_case02.py` compared the arms to each other without ever
opening the sealed key whose hash §5.2 cites. Two new deposited scripts,
`estimator_sensitivity_case02.py` and `model_mix_case02.py`, carry A14 and A13.
The quality tier now reports the interval §5 always required. The unblinding keys
are now protected by an explicit `.gitignore` rule instead of by omission.

**Under-reported disclosures now restored.** A3 — the alternative explanation
recorded on 2026-08-07, before any run, predicting that Arm A's golden-heavy
artefact would be "less decision-forcing than the contract" and would be "the
first place to look" if the artefacts failed to equalise dispersion — appeared
nowhere in v1 despite describing exactly the outcome that occurred. It is now in
§7. Multiplicity across the four pre-registered outcomes is now stated, including
the uncomfortable consequence that the surviving cost result sits exactly at the
design's attainable floor and would not survive a correction over four tests.

**The general lesson.** Every one of these was found by review, not by the
authors, and the two blocking ones had been sitting in plain sight — the model
contamination was recorded in the `modelUsage` field of all 56 result files from
the first day, and the estimator's non-invariance is a one-line algebraic
property of a formula printed in the pre-registration. Freezing an analysis plan
protects against choosing a statistic to fit the data. It does not protect
against choosing a *wrong* statistic before the data exists, and it does not read
your own ledger for you.

---

## A16 — round two of adversarial review: 47 findings, three of them against v2's own corrections
**2026-08-23, before submission.**

Draft v2 — itself the product of A15's corrections — was put through a second
adversarial review with seven lenses, including two that round one lacked (a
hostile referee arguing for rejection, and a proponent arguing the paper is
unfair to FCDD) and a completeness critic asked what the other lenses missed.
Sixty-six findings raised, **47 verified: 13 blocking, 24 major, 10 minor**.

**Three of v2's own corrections were wrong.**

1. **The §5.6 baseline was the wrong file.** `run_resilient.sh` scrubs absolute
   paths out of every workspace at build time, so all 28 copies of
   `Contract.lean` differ from the repository file in one line *before any agent
   runs*. Comparing against the repository baseline scored all 28 as modified.
   Correct: **22 of 28 modified it; six left it byte-identical to the file they
   were handed**, having judged the frozen contract adequate — which is the
   method working as designed, and evidence against the claim it replaced.
2. **"Twenty-five distinct specifications" double-counted.** That figure summed
   per-defect distinct counts, charging the single untouched file once under each
   of three defects. Counted globally over the 28 files it is **23**. The
   comparison against "one distinct binary" was also unit-inconsistent: per-defect
   summed, the binary figure is 7, not 1.
3. **"FCDD's own artefact was the least reproducible thing in the study" is
   false.** It compared the treated arm's artefact against the *binary* and never
   against the control arm's artefact, sitting in the same workspaces. Measured:
   Arm A produced **28 distinct test artefacts across 28 runs**, Arm B 23 across
   28. **On this measure the control arm diverged more.** The superlative is
   withdrawn; what survives is that neither arm converged on its supporting
   artefact while both converged on the program.

**A14 overstated its own replacement.** `sd(ln c)` is invariant under *scaling* —
which is what the dollars-to-cents demonstration shows — but that is not
invariance under a change of *measure*. Dollars and tokens are not proportional
(two models at different prices; cached input near-free), and the statistic gives
*p* = 0.0156 in dollars against **0.0625 in tokens**. A14's "in any unit" is
withdrawn.

**A second schedule discontinuity, never disclosed.** `drive.log` records cell 14
(`bug05/armB/r1`) running **88.6 hours wall clock** between 2026-08-08 and 08-12,
against roughly 55 minutes of agent time across its two result files: the
schedule stalled on a weekly usage limit. A6 reasons about one gap; there are
two, so more cells straddle an era boundary than A6 assumes. Removing both the
post-gap runs and the suspended cell: mean −0.0628, *p* = 0.1094 — verdict
unchanged, direction marginally stronger against H1.

**Two claims that were wrong in FCDD's favour, now corrected against it.**

* The model-mix contribution **can** be bounded, from the same field that
  revealed it; v2 said it could not. On primary-model spend alone the cost
  premium is **2.75×** (not 2.26×) and the primary estimator moves to −0.0718
  (*p* = 0.0625 from 0.1094). The contamination was flattering FCDD on both.
* The Bonferroni claim was wrong in the other direction: v2 said no result could
  survive correction over four outcomes. At 0.05/4 = 0.0125 the cost result at
  0.0156 indeed does not clear it, but the floor is a property of the seven-pair
  sign test rather than of the design, and the narrower statement is now given.

**The comment-volume withdrawal was measured against the wrong denominator.** v1
said the minimality deficit was comment volume; v2 withdrew that on whole-file
comment characters (+40, 0.10%, *p* = 0.2344). A grader never saw whole files. On
the **diff** — the object actually read — FCDD added **+26.4% more comment text**
(212 characters against 168), *p* = 0.1875. Not significant at seven defects, but
directionally what v1 guessed. Both the assertion and the confident withdrawal
were unwarranted; the measurement is now deposited
(`tools/comment_volume_case02.py`) and the text says what it supports.

**Blinding failed on three packets, by the mechanism the audit was built to
catch.** The audit's term list was written *before* the scrubber's replacement
vocabulary was chosen, so it never tested for the scrubber's own output. Adding
those phrases: **0 for Arm A against 3 for Arm B, leaking in 3 of 28 packets** —
the substituted phrase "the design note" appears only where an FCDD comment cited
its contract. The first scrubber introduced the tell it removed; so did the
second, less. Blinding held on 25 of 28.

**Smaller corrections.** `IQR(ln c)` was not an interquartile range — on n = 4 it
is the mid-two spread, now named accurately. `addendum_case02.py`'s "independent
implementation" imports the script it checks and shares its cost extractor and
estimator, so it verifies the permutation *enumeration* only; the claim is
narrowed. The `h2_strategy_case02.py` docstring still described the pre-A12
classifier. The two restarted cells' partial costs were never captured at all —
excluded but not recorded, contrary to §6 — so the reported total understates
spend. A1's magnitude (63% under budget) and two of A4's residuals about the
control arm's oracle were suppressed in the paper and are now in §2. A3 bears on
the cost result and not only on dispersion; §7 now says so.

**What we conclude from our own error rate.** Round one found 43 defects in a
paper its authors believed finished; round two found 47 more in the corrected
version, three of them *in the corrections*. The core result — a 2.26×–2.75× cost
premium, no support for H1, and byte-identical programs — survived both rounds
untouched, which is the strongest thing that can be said for it. Everything
sharper than that core has now been wrong at least once. That is worth stating
plainly in a paper about whether formal machinery makes work more reliable: what
caught these was adversarial review, repeatedly, and each round found errors the
previous round's fixes introduced.

---

## A17 — the oracle confound was not spent symmetrically; it was inverted. Arm B was shipped the answer.
**2026-08-23, found by the third adversarial review round, before submission.**

This is the most serious defect found in the study, and it goes to the design's
central control rather than to its analysis.

**What was shipped.** `run_resilient.sh` builds an Arm B workspace with
`cp -r "$CASE/step1_contract" "$WS/contract"` — the whole tree. That tree contains
an `artifacts/` directory holding `chess.tap` with sha256
`33ed86b2cdec18ab3147376903739882210581f303321882141770dd6ba978b4`, **bit-identical
to the sealed answer key's pristine tape**, together with pristine memory
snapshots. Measured: the pristine binary was present as an *input* in **28 of 28
Arm B workspaces and 0 of 28 Arm A workspaces**. All 28 Arm B `FIX_NOTES.md`
reference the shipped artefacts.

**What Arm B could therefore do, and did.** Each seeded variant differs from
pristine in one byte plus the tape checksum. A single `cmp -l` localises the
fault exactly. From `bug06_armB_c2r2/FIX_NOTES.md`:

    $ cmp -l contract/artifacts/chess.tap variants/bug06/chess.tap
    11497  70  50        # octal: 0x38 (JR C) pristine vs 0x28 (JR Z) variant
    13596 210 230        # the tape checksum byte

**Arm A was denied that object deliberately, for a reason that was false.** From
`armA_characterisation_v1_PROVENANCE.md`:

> The pristine `.tap` itself is deliberately **not** shipped with the suite. Only
> observable values are recorded. Shipping the binary would let an Arm A run diff
> it against the variant and localise the fault instantly, **which would be a
> strictly stronger oracle than the contract Arm B holds.**

Arm B held exactly that binary, in every run. The stated justification for
withholding it from the control is a precise description of the advantage the
treatment actually had.

**What this does to the study.** Case01's disclosed confound was that Arm B's
contract had been *derived from* the pristine engine. Case02 exists to spend that
confound symmetrically. It did not: it **inverted and amplified** it. Arm B did
not merely hold a pristine-derived artefact, it held the pristine artefact.

Three consequences, stated in order of severity.

1. **§5.2's convergence result is not arm-comparable.** "Every run in both arms
   found the seeded fault and reverted it exactly" is true, but the two arms
   reached it by different routes: Arm A by reasoning from reported symptoms
   through a characterisation suite, Arm B by a byte comparison against the
   answer. The 56/56 convergence is still a fact; it is no longer evidence that
   the two *methods* are equally capable of localising a fault.
2. **The cost and dispersion comparisons are biased toward the treatment.**
   Localising a fault by `cmp -l` is faster and far less variable than deducing
   it. This should depress both Arm B's cost and its within-cell dispersion —
   which is to say it biases *toward* H1 and *toward* a smaller measured premium.
3. **The headline conclusions survive, as conservative.** H1 failed anyway, and
   the premium was 2.26× (2.75× on primary-model spend) anyway. Both results were
   obtained against a design tilted in FCDD's favour, so removing the tilt could
   only strengthen them. That is the only reason this amendment is a disclosure
   rather than a retraction.

**Why it went unseen for three review rounds.** Nothing in the paper, the
pre-registration or amendments A1–A16 mentions `artifacts/`. §6's enumeration of
the Arm B package — "Lean specification, twin, bridge suite, z3 scripts" — omits
it. A4 reasoned carefully about suite-versus-contract expressiveness without
noticing that the contract package also contained the answer. The directory was
inherited from case01's step 1, where it was a legitimate build artefact, and it
was copied wholesale into every treated workspace by a line of shell nobody
re-read.

No re-run is attempted, for the reasons in A6 and A13: it would cost the study
again, in a changed environment, and could not restore the pre-registered
condition retroactively. The defect is disclosed, quantified and carried into the
threats section. A case03 must ship the treated arm a package whose contents have
been enumerated and diffed against the sealed material, and the check belongs in
the runner, not in a reviewer's diligence.

---

## A18 — the second-gap sensitivity dropped the wrong run
**2026-08-23, same review round.**

A16 reported that removing both the post-gap runs and the suspended cell gives
mean −0.0628, "direction slightly stronger against H1". Both halves are wrong.

`estimator_sensitivity_case02.py` removed the suspended observation **by count**,
slicing `[:3]` over an unsorted `glob.glob`. On this filesystem that kept the
suspended run (`bug05/armB/r1`, $8.59) and discarded an unrelated one
(`bug05/armB/r3`, $36.26). The reported figure was an artefact of directory order.

Dropping the suspended run **by identity**: mean **−0.0345**, *p* = 0.1094. The
verdict is unchanged, but the direction is **weaker** against H1 than post-gap
removal alone (−0.0575) and weaker than the headline (−0.0547) — which is what
threat 5 predicts, since that run is the cheap resumed observation A7 flagged as
the largest single contributor to the anti-H1 direction. Removing it shrinks that
cell's dispersion and softens the reversal.

The script now selects by identity and the constant is named. A16's sentence is
superseded here rather than rewritten, per this log's append-only rule.

---

## A19 — the repository deposits the engine, and the fault locations with it
**2026-08-26, after the study closed; found by a pre-publication audit of the
repository, not by a review round.**

A17 established that the treated arm was shipped the pristine binary. This
amendment records that **the repository itself deposits it**, and has since
2026-07-29:

1. `case01_spectrum_gambit/step1_contract/artifacts/chess.tap` is tracked and is
   byte-identical to the sealed `sealed/seedkit/pristine/chess.tap` — sha256
   `33ed86b2cdec18ab3147376903739882210581f303321882141770dd6ba978b4`. The
   `.gitignore` rule `case*/sealed/` never applied to it, because the step-1
   contract package wrote its own copy under `artifacts/`.
2. `case01_spectrum_gambit/work/pristine/chess.bin` (`c107dfaf…dc0f`, the hash
   case04 records as *the sealed oracle*) was added and deleted in commit
   `590b5d1`; the blob is still reachable in history.
3. The three tracked `.sna` artefacts embed the engine's code verbatim.
4. Case 02's own **28 grading packets carry the fix diffs against
   `engine.inc`**, and 39 raw result files state fault locations, byte offsets
   and before/after values in prose. §10's note that "the 28 unblinding keys are
   excluded by an explicit `.gitignore` rule — the seal is a convention, not a
   guarantee" was righter than it knew: the keys are excluded and the answers
   are deposited anyway, by a different route.

**Consequence for this paper: none of the numbers move.** The runs executed
offline against tarballs and could not read the repository; the deposit is an
artefact-integrity defect, not a contamination path into the data. What it does
retire is the **reuse** of these seven faults as a blind benchmark, by us or by
anyone else. §10 is corrected accordingly, per the operator's *accept and
declare* ruling of 2026-08-26.

**Why it matters beyond bookkeeping.** This is A17's failure mode a second time,
one level out: the control enumerated *paths* while the hazard was *content*, so
a second copy under an uncovered path was invisible to it, and nobody re-read
the tracked file list. Three adversarial review rounds, an amendment log
eighteen entries long, and a constraint document written specifically to prevent
this class (`case03/CONSTRAINTS.md` C1) all missed it, because every one of them
was pointed at the *runs* and none at the *deposit*. The check C1 already
specifies — hash every file against the sealed manifest — is owed to the
repository, not only to a workspace.
