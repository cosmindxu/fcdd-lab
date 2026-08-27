# CASE 07 — result: the ATTACK budget is not binding in the regime tested

**Retired at the pilot gate, 2026-08-27, by operator decision. The pilot is the
result.** No scored phase ran; none should.

---

## What was asked

Law 12 replaced FCDD's ATTACK stopping rule — *iterate to convergence* became
*stop on coverage against a declared budget* (one mandatory pass, at most one
scoped remediation, hard stop at two). It shipped on a **measured diagnosis with
a predicted benefit**: case 02's runs showed the beat running 1–18 rounds on
repeats of the same defect, round count correlating *r* = +0.72 with cost, and
runs with ≥ 6 rounds costing $48.33 against $28.42 for ≤ 2 — while all 56 runs
produced a byte-identical artefact, so no extra round changed anything.

Nobody had tested whether the bounded rule is **safe**. Case 07 was built to ask
whether bounded ATTACK misses confirmed blocking findings that unbounded ATTACK
finds.

## What the pilot found

**Both unbounded cells ran exactly two rounds**, unprompted, and stated why:

> *"Round 2 over the unchanged review surface produced no new confirmed findings
> — only the six residuals named above."*
> — CONV cell, `live_guard.py`
>
> *"A third round would re-probe surfaces that returned only conformance in R2,
> which is the stopping condition as written."*
> — CONV cell, `ib_risk.py`

**Law 12's budget is two rounds.** The unbounded arm therefore did, unprompted,
exactly what the bounded arm is capped at.

**The consequence for the study is fatal and was pre-registered as such.** If the
arms behave identically, BUDGET cannot miss what CONV finds, H1 passes trivially,
and the study would have run to completion unable to support or refute anything —
the failure mode round 2 named as the programme's most expensive. Two cells cost
what a completed study would not have.

## What this says about law 12

**In this regime — fresh adversarial review of unfamiliar code — the cap is not
binding**, because unbounded review self-limits at the cap. Law 12 is not wrong
here; it is *inert*, and it describes what the beat already does.

**It also reframes the diagnosis that produced it.** Case 02's 1–18 round spread
came from **repair against an existing contract**, where each round re-reads a
specification the agent itself has been editing. That loop has a feedback path
this one does not. The runaway is therefore plausibly a property of
**repair-with-a-contract**, not of the ATTACK beat — which means law 12's real
subject is narrower than its text implies, and its safety question remains open
**in the repair regime only**.

**Recommended amendment to law 12** (not applied here; it belongs to a study that
tested it): scope the rule's motivating evidence to the repair regime, and record
that on fresh-code review the beat was observed to self-limit at the budget.

## The secondary result, which is the programme's first support for the method's own claim

FCDD's skill says, in the section listing what it does *not* do:

> *"It caught the hollow monitor; it did not prevent it. **FCDD's value is late
> (adversarial review) as much as early (proof).**"*

Two ATTACK cells, on two modules of a codebase that **64 prior adversarial review
documents** had already worked over, produced **six confirmed defects**, every one
demonstrated by a runnable probe:

| | Finding | Class |
|---|---|---|
| `live_guard` | barrier E2 compares **2-dp-rounded** percentages, so 10.001 % against a 10.0 % cap is **ALLOWED** | **wrong money-path action**, reachable from both named callers, re-verified against the unscrubbed source |
| `ib_risk` | `cmd_readonly_check:2846` drops `audit_append`'s `False` where `:2199` and `:2313` capture it — a lost HALT row is **completely silent** | the arc's own **hollow-monitor** class, at the site R3's 2026-08-03 fix never reached |
| `ib_risk` | `cmd_readonly_check` runs *over* an existing latch, destroying the original trip record and re-paging | forensic loss; safety preserved |
| `ib_risk` | `limitBoundBy` names the wrong limit leg once the FX conversion is active | wrong operator-facing record; latch correct |
| `live_guard` | barrier H accepts non-finite `whatIf` values, vacating three refusals | guard-level fail-open; callers currently sanitise |
| `ib_risk` | `daystop_review` returns a confident verdict on non-finite input | wrong verdict, advisory surface |

Both filed to the subject repository. **This is the first empirical support in
seven cases for the one claim the method actually makes** — and it arrived
incidentally, from a probe built to decide whether a study should run.

## Honest limits

- **Two cells, one arm, k = 1, two units.** A gate probe (amendment A1), not the
  §7 pilot. It cannot say the budget is safe; it says the question is moot here.
- **No BUDGET arm ran.** The contrast is inferred from CONV's round counts, not
  measured.
- **No namespace isolation** (A1): cells ran as orchestrated subagents against
  the scrubbed tree, read-only and forbidden network. Acceptable because the probe
  produced no scored data; it would be inadmissible for a scored run.
- **The repair regime is untested.** Everything above is about fresh review.
- **The scrub had a defect of its own**: redacting the live account id collapsed
  two deliberately-*different* values onto one literal, so five selftest
  negative-cases began passing the account they were written to reject. Redaction
  that does not preserve distinctness changes program semantics — recorded for
  anyone reusing `tools/scrub.py`.

## What survives for reuse

`tools/scrub.py` (assertion-gated, and its assertions caught four leaks the prose
manifest had missed), `tools/adjudicate.md`, `tools/build_conv_arm.py` (delta by
diff, not grep), `tools/analyse_case07.py` (whose vacuous-SAFE paths round 3
found and which now refuses to render a verdict without evidence), and the three
review rounds deposited in `reviews/`.
