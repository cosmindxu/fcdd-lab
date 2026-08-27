# Case 07 — review round 2, verbatim (2026-08-27, Opus adjudicator charter)

Object: PREREGISTRATION.md r2 (commit b8580e3). Charter: attack r2's repairs;
audit §9's dispositions against the body.

## BLOCKING
B1 The CONV graft is incomplete and produces an incoherent hybrid — the declared
site list misses at least three places the stopping-rule complex lives: the §4
laws header ("12 was bought by measurement… case02, 56 runs"), law 13's two
dangling references to law 12, and the Beat 4 #16.5 ambiguity (the turnstile
exists only in the current skill; a section-verbatim revert silently deletes a
non-treatment component). §3 also says "three sites", lists four, then says
"four sites".
B2 The treatment is provably not delivered by the declared delta: BUDGET's own
reference pack ships the OLD stopping rule — lenses.md 93–95 "stop when a round
yields only residuals", no budget language in the file; SKILL.md's intro says
"until findings converge"; case_study.md narrates ~nine widening rounds. A
BUDGET cell following its full pack can legitimately iterate past the cap.
B3 The finding-identity and residual rules cannot compute the primary: a shared
root cause probed via two callers scores as a false miss; "runs each probe
against the other's site" is a category error on one shared tree; a
broadly-worded residual absorbs would-be misses, making the falsifier evadable
by the arm under test.
B4 The three r2 numbers are underived and falsify the rules-not-numbers header:
0.75 traces to nothing ($28.42/$48.33 ≈ 0.59 is a within-arm subgroup); b ≥ 15
with "3/b (95%)" is a 20% miss ceiling presented as a safety floor, and the
independence assumption fails — misses cluster by unit and round-depth.
B5 The pilot gate has no decision rule that can decide at its size: no arm
named; "affordable n" undefined; a 2-unit rare-event estimate spans an order of
magnitude; conditioning on the passed gate biases the rate upward.

## MAJOR
M1 The isolation envelope's hole is the relay: ibkr_common.py defaults every
tool to 127.0.0.1, port vault→4002 — a probe importing any ib_* tool dials the
host loopback; §5 names no netns/socket topology and no unreachability probe.
M2 The scrub misses secrets-in-code and the tree's own answer key: live account
id hardcoded in ib_autopilot.py:2192, ib_safety.py:424–426,
packaging/build_deb.sh; CHANGELOG.md, docs/REVIEW_*.md and .git document the
tree's defects outside the case-study exclusion.
M3 BLOCKING is undecidable for most of the 136 modules (indicator code emits
numbers, not verdicts); b then depends on the undeposited unit list; §9's
"mechanical" overclaims — adjudicate.md does not exist.
M4 The censoring rule is anti-conservative: excluding timeout-killed CONV cells
can only shrink the miss count — bias toward "safe", wrong fail direction by the
skill's own law 1.
M5 The third party is load-bearing and never identified — human or model, pinned
how, independent of what.
M6 The confirmation branch overreaches the M2 narrowing the falsification branch
carefully applies.

## MINOR
m1 cost falsifier names no statistic (mean vs median); m2 the pack's file set is
unenumerated — TODO.md would ride along and leak the frame, and only the current
copy names law 12's provenance (an undeclared arm delta); m3 law 14's "no study
is named here on purpose" note tells every cell it is inside an experiment
programme; m4 env.sh is not literally "credential-bearing" — name it; m5 wording
drift vs the evidence file (numbers themselves verified correct); m6 round 1's
verbatim report is deposited nowhere — §9 could only be audited against itself.

## DISPOSITION MISMATCHES
§9 B1 "r2 deposits the graft" — nothing deposited; arms/ and tools/ do not
exist. §9 "Majors M1–M7 applied as §6–§8 rules" — M2 and M6 have no locatable
site; "five minor all accepted" — only three traceable. §9 B4 "now mechanical,
third-party only" — the mechanism is an undeposited protocol and an unidentified
party. §3 "three sites" vs §9 "four sites". §9 B6 "an explicit list frozen here"
— no list is here.

## VERDICT
Not freezable, and not one round away. Eighth consecutive round: every blocker
sits in the previous round's repairs; the disposition table again claims
deposits the filesystem does not contain. Largest risk: treatment integrity —
lenses.md ships the CONV stop rule inside BUDGET's pack, so as drafted the study
could spend its budget unable to attribute any difference to the thing it tests.
Second: the primary's computability. The owed artefacts are where the fixes must
land, and they will need their own round.
