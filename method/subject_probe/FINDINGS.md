# Saturation probe — first run, and the defect in the probe itself

**2026-08-27.** Model `claude-haiku-4-5-20251001`, k = 5, no specification
supplied. Raw output: `probe_result.json`, emitted by `saturation_probe.py`.

## The defect, found before the result was used

**Half the items were not underdetermined at all.** `expires-vs-maxage` is
explicitly settled by RFC 9111 (max-age overrides Expires); `30-360-end-rule`,
`act-365-leap` and `pax-size-vs-ustar` are each specified in their own standards.
For those, high agreement is **correct recall of a determined rule** — it says
nothing about whether an *ambiguity* has been pre-resolved in the weights.

Scoring recall as saturation inflated four of the five disqualifications. The
per-subject verdicts printed by the first run are therefore **withdrawn**, and
`SUBJECT_SELECTION.md` §3 gains the certification step that would have caught it.

## What survives: the certified subset

| item | why genuinely undetermined | agreement |
|---|---|---|
| `month-end-add` | ISO 8601 does not define duration arithmetic; 2026-02-28 is convention | **100%** |
| `duration-order` | unspecified | **100%** |
| `pax-vs-gnu-longname` | POSIX does not cover GNU headers, so precedence is undefined | **100%** |
| `ep-in-repetition-key` | FIDE arguably ambiguous | 80% |

Direction survives; strength and ranking do not. Four items, one model tier, and
a small model can only ever disqualify — never clear — a candidate.

## The reframing this produced

Where a specification is silent, the model converges anyway. Read as a finding
rather than an obstacle:

> **Formalisation's narrowing value is a function of prior strength.** Where
> priors are strong, the solution space is already narrow and a contract has
> little left to narrow. Where priors are weak, narrowing is where the value must
> live.

Consequences: it explains cases 01 and 02's null on predictability (a byte-fault
in a chess engine is maximally prior-saturated); it makes *prior strength* a
measurable design input rather than an assumption; and it redirects candidate
nomination from "obscure" to **low-prior** — post-cutoff specifications above all.

## Next

Re-run on a **certified** item set over low-prior candidates, at the tier a study
would actually pin. Until then no candidate is qualified, and `case06_narrowing`
stays suspended.
