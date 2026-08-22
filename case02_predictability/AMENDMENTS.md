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
