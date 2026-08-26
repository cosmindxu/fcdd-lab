# Pipeline prototype — stale-quote guard

A deliberately small requirement run end to end through the FCDD pipeline, so that the gate
placement in `../pipeline.md` is **tested rather than argued**.

```bash
./gate.sh          # the whole thing; judged by exit code, never by its tail
```

Runs in ~2 s. `GATE GREEN` / exit 0 when everything holds.

## Layout — one directory per pipeline step

| Path | Step |
|---|---|
| `step0_REQUIREMENT.md` | prose requirement + **fail directions** + property list. Frozen *before* any Lean. |
| `step1_contract/StaleQuote.lean` | spec of record: definitions **and** P1–P6 **and** reachability witnesses. Lean 4 core, no mathlib. |
| `step2_twin/twin.py` | transcription of the definitions. Pure; no I/O. |
| `step3_bridge/bridge.py` | conformance suite: witnesses · theorem mirrors · exhaustive small-domain sweep · mutation coverage. |
| `gate.sh` | kernel leg (compile, `sorry`, `axiom`, axiom-profile whitelist) + bridge. |

## The requirement

Trade only on known-fresh quote evidence. Each source reads as a quote with an age, or as
unreadable. Verdict is TRADE / BLOCK / UNKNOWN, composed with a safe-OR: any BLOCK wins;
absent a BLOCK any UNKNOWN wins; TRADE needs positive fresh evidence from every source.
Empty evidence is UNKNOWN, **never** TRADE.

## What this prototype demonstrated

**A property gap, found by execution.** P1–P5 were written, formalized and proved first.
Then bridge mutation `M4_boundary` (`>=` for `>` in `stale`) **survived every layer** —
witnesses, mirrors, and the 1200-case sweep. P1–P5 constrain the *shape* of the verdict but
never pin *where* fresh becomes stale, so an off-by-one at `age == limit` was invisible to
all of them. P6 (`age == limit` is fresh) was added in response; M4 is now caught by P6.

This is the mutation layer earning its place. Reading the spec would not have found it.

**Every clause has a live negative test:** M1→P1, M2→P3, M3→P2, M4→P6.

**The gate is fail-closed** — all four confirmed RED:

| Injected defect | Caught by |
|---|---|
| `sorry` in the spec | axiom-hygiene leg |
| `axiom cheat : False` | source grep |
| `theorem nd := by native_decide` (evades both greps) | axiom profile only |
| twin drifts from the spec | bridge, naming clause P1 |

**Axiom profile:** reachability witnesses are axiom-free (constructive `decide` terms); the
theorems are `[propext]` or `[propext, Quot.sound]`. No `sorryAx`, no `Classical.choice`, no
`Lean.ofReduceBool`.

## Residuals — what this does NOT clear

* **R-1 · common-mode error (the big one).** One session authored the requirement, the spec
  *and* the twin. That is precisely the case `SKILL.md` Beat 3 says the bridge cannot catch:
  a shared misconception makes both sides agree, every layer passes, the kernel is green,
  and confidence is *maximal* while the system is wrong. Only an independent Lens-A reviewer
  who did not write the spec, plus reality (Beat 3.75), can close this. **Neither ran here.**
* **R-2 · the bridge samples.** Finite witnesses, one violating input per theorem,
  single-field mutations, brute force over a *small* domain (1200 cases). High-coverage
  conformance testing, not a proof of refinement.
* **R-3 · no shell.** Beat 3.5 is absent entirely. `twin.py` is pure — no clocks, no
  retries, no source that can lie about its own freshness. A real guard's hardest honesty
  problem is exactly there, and this prototype says nothing about it.
* **R-4 · no Beat 0.5, no Beat 3.75.** The requirement was invented, not elicited from
  deployed missions; nothing was validated against a real quote feed.
* **R-5 · N=1 and self-graded**, like the skill it exercises.

The point of listing these is that the badge must match the detector. This prototype
demonstrates *gate placement and mutation coverage*. It does not demonstrate that the
stale-quote guard is the right guard.
