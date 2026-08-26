# The FCDD pipeline: where the gates go

**Status:** method note, 2026-08-24. Worked prototype in `pipeline_proto/`, gate placement
tested rather than argued (see *Evidence* at the end).

The pipeline this note formalizes:

> write a requirement or mathematical claim → formalize it in Lean (solution elements *and*
> properties) → generate a candidate proof → verify it with Lean → produce the code from the
> constraints, or by implementing the twin.

That is a correct description of **Beats 1–2** of `SKILL.md`. It is also, as stated, the
arrangement most likely to produce a kernel-green, confidently wrong system. This note says
why, and where the gates have to sit for the pipeline to carry weight.

---

## 1. Lean holds both halves

The spec of record carries **solution elements** and **properties** in one file:

| Half | In `StaleQuote.lean` | Role downstream |
|---|---|---|
| Solution elements | `Reading`, `Verdict`, `stale`, `unread`, `verdict` | what the twin **transcribes** |
| Properties | `P1…P6`, `reach_*` witnesses | what **constrains** the transcription, and what the bridge mirrors |

This is what makes "implement the twin" well-defined rather than aspirational: you
transcribe the definitions, and the theorems tell you what the transcription must preserve.
`ikbr_tools/tests/lean/BreachConfirm.lean` already works this way — `step`/`run`/`brkCount`
alongside P1–P4.

---

## 2. The pipeline, with gates

```
  requirement in prose + FAIL DIRECTIONS per degradable input        [party A]
        │                    ── frozen artifact; the formalization is checked AGAINST it
        ▼
  Lean: definitions + properties + non-vacuity obligations           [party A]
        │
        ▼
  candidate proof ──────────────────────────────▶ G1  kernel verdict  ✦ automatable
        │                                          G2  axiom hygiene   ✦ automatable
        │                                          G3  non-vacuity     ✦ automatable
        ▼
  twin: transcription of the DEFINITIONS                             [party B]
        │
        ▼
  bridge: witnesses · mirrors · mutations · sweep ─▶ G4               ✦ automatable
        │
        ▼
  shell: I/O, clocks, retries, degraded paths ────▶ G5               ✦ partly
        │
        ▼
  ATTACK — Lens-A reviewer who did not write the spec   ✗ NOT automatable by party A
        │
        ▼
  VALIDATE on reality
```

### The gates, and what each can actually falsify

Grade every gate by what its evidence can falsify — never by what it is named after.

| Gate | Falsifies | **Cannot** falsify |
|---|---|---|
| **G1** kernel verdict | the proof does not follow | that the theorem is the right theorem |
| **G2** axiom hygiene (`#print axioms` whitelist, `sorry`/`axiom`/`native_decide`) | admitted premises wearing a proof's badge | a true-but-vacuous or too-weak theorem |
| **G3** non-vacuity (`spec_total` — every verdict class reachable, with witnesses) | a class no input can reach | a class reachable but wrongly *defined* |
| **G4** bridge (witnesses, theorem mirrors, mutation coverage, small-domain sweep) | twin ≠ spec, on the sampled domain | common-mode error; refinement in general |
| **G5** shell honesty | a monitor that cannot observe what it claims | intent |

G1–G3 are cheap and belong in the inner loop, on every candidate proof. G4 belongs in the
offline gate. G5 and ATTACK are the ones that catch the errors the earlier gates
structurally cannot — and they are the ones a pipeline is tempted to drop.

---

## 3. The party-separation rule

> **A model may search for proofs. A model may not, in the same pass, also author the
> statement and the twin.**

Rationale, from `SKILL.md` Beat 3, verbatim:

> when the same author (**or model, or session**) writes spec AND twin, a shared
> misconception makes both sides agree, every layer passes, the kernel is green — and the
> user gets *maximal* false confidence in a wrong system.

and §5:

> It proves COHERENCE, never CORRECTNESS-OF-INTENT… Garbage clauses, kernel-checked, are
> still garbage.

Proof search is safe to automate because **Lean's kernel is the arbiter**: a machine-found
proof that typechecks with a clean axiom profile is exactly as good as a human's, and
provenance is irrelevant. Formalization is *not* safe to automate in the same pass, because
nothing downstream re-derives intent. G1–G4 all take the statement as given.

Practical consequence: freeze the prose requirement with its fail directions **before** any
Lean exists, and have the twin written against the definitions by a different party than
the one that authored them. Automating the loop does not create the common-mode hazard — it
scales it.

---

## 4. Two ordering rules inside "formalize it in Lean"

1. **Prose properties with fail directions come first.** For every degradable input
   (missing, stale, NaN, corrupt, ambiguous) name the verdict it must map to, choosing
   asymmetries by recoverability. Without that artifact you validate Lean with Lean.
   Prefer 3-valued SAFE/DANGER/UNKNOWN with a safe-OR wherever "we could not tell" is real.
2. **Prove reachability before the interesting theorems.** A spec no input can drive into a
   class proves that class's theorems for free. In the prototype the `reach_*` witnesses
   come before P1.

---

## 5. Cost note

This pipeline makes the kernel leg a **hot loop** — many candidate proofs verified per
requirement, rather than one CI sweep per commit. Two consequences:

* Parallelising the kernel leg pays continuously, not once. `ikbr_tools/run_tests.sh` went
  9.8 s → 3.8 s (2.6×) on 2026-08-24 for exactly this reason.
* At high candidate volume a warm Lean REPL pool (e.g. `kimina-lean-server`) starts to earn
  its keep, because per-invocation process startup (~0.22 s floor) begins to dominate. It
  does **not** pay for a corpus-sweep gate that already finishes in seconds — see
  `runpod_management/KIMINA.md` for the measurements.

---

## 6. Evidence — the gate placement was tested, not asserted

`pipeline_proto/` runs the pipeline end to end on one small requirement (a stale-quote
guard: TRADE / BLOCK / UNKNOWN with an inclusive freshness limit).

**The finding that justifies the mutation layer.** P1–P5 were written first and all proved.
Bridge mutation `M4_boundary` — `>=` substituted for `>` in `stale` — **survived every
layer**: witnesses, mirrors, the 1200-case sweep. The properties constrained the *shape* of
the verdict but never pinned *where* fresh becomes stale. P6 (`age == limit` is fresh) was
added in response, and M4 is now caught by P6. A property gap found by execution, which no
amount of reading the spec had surfaced.

**Gate negative tests, all confirmed RED:**

| Injected defect | Caught by |
|---|---|
| `sorry` in the spec | G2 |
| `axiom cheat : False` | G2 (source) |
| `native_decide` — evades both source greps | G2 (axiom profile only) |
| twin drifts from the spec | G4, naming clause P1 |

**Mutation coverage, every clause with a live negative test:** M1→P1, M2→P3, M3→P2, M4→P6.

**Residuals this prototype does NOT clear** — recorded in `pipeline_proto/README.md`: it was
authored in a single session, so spec and twin share an author and the common-mode blind
spot is wide open; the bridge samples rather than proves refinement; Beat 0.5 (scenario
discovery), Beat 3.5 (the shell) and Beat 3.75 (reality) are absent entirely.
