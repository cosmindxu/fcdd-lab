---
name: formal-contract-dev
description: Formal Contract-Driven Development (FCDD) — the lifecycle for building and operating a SAFETY-CRITICAL system around a machine-checked formal contract. USE WHEN building or HARDENING anything load-bearing whose SILENT failure beats its loud one: money paths, dead-man/kill switches, monitors and watchdogs, auth/authorization closure, protocol state machines, "never/always" claims, or when a soak/burn-in is being replaced by runtime verification (read the warnings first — a hollow monitor is worse than the soak). Companion for the proving sub-process: the formal-verification skill (FCDD wraps it). The four beats — PROVE the contract (kernel-checked spec of record; non-vacuous witnesses; real incidents encoded as theorems), TWIN it (a pure implementation that provably/testably agrees with the spec — transcription+bridge, or verified extraction), BRIDGE it (a conformance suite: witnesses conform, theorem-violating inputs fail the RIGHT clause, single-field mutations trip exactly their clause — it SAMPLES agreement, it is not a refinement proof), ATTACK it (multi-agent adversarial review with distinct lenses, verify-by-execution, ground-truth every finding yourself, against a DECLARED BUDGET — coverage is the stop condition, not convergence). Plus the honesty machinery: fail-direction engineering (degraded input ⇒ the CONSERVATIVE/fail-safe verdict, never a vacuous SAFE; asymmetries by recoverability), falsifiability tiering (grade every check by what the evidence can actually falsify — the badge must match the detector), observed-sample semantics for impure shells, decision/assumption ledgers, and verify-where-it-runs deployment (extract-and-execute the installed artifact, never your simulation of it). FCDD proves coherence, NOT correctness-of-intent, and catches defects late (review) as much as early (proof) — it caught, it did not prevent, the arc's hollow monitor. Default tools (Lean 4 core, z3+cvc5, Python pure/impure split, plain-script gates) are DEFAULTS — substitute Coq/Rocq, Isabelle, Rust, OCaml, or a lower claim tier (property tester, model checker, solver-trusted prover) with a recorded downgrade. Exemplar with file paths: references/case_study.md; N=1, distilled 2026-07-29 from the ikbr_tools R18 watcher + ops-monitor arc.
---

# Formal Contract-Driven Development (FCDD)

**Prove → Twin → Bridge → Attack.** A system is developed *around* a machine-checked contract:
the spec is proved coherent before it judges anything, the implementation is bridged to the spec
rather than merely inspired by it, the observation/execution boundary carries explicit honesty
rules, and everything — spec, code, wiring, docs — is adversarially attacked until findings
converge from "reachable" to "hygiene". Naming note (decision-log discipline applied to itself):
the operator proposed *formal contract oriented development*; refined to **FCDD** — same intent,
acronymable, honest lineage (Design-by-Contract + formal methods + adversarial engineering; the
novel parts are the BRIDGE and the honesty machinery).

## 0. When to use / when not

**Use** for anything load-bearing: money paths, kill-switches and dead-man latches, monitors and
watchdogs, auth/authorization closure, protocol state machines, "never happens / always holds"
claims, replacing a soak or burn-in with runtime verification, or any component whose silent
failure is worse than its loud one. **Do not use** for prototypes, cosmetics, or code you can
cheaply re-run and eyeball — FCDD's cost is real; proportionality is part of the method.

**How much to apply (beat dependencies + sizing).** The beats have a dependency order — Bridge
presupposes Prove+Twin; the falsifiability tiering and the shell honesty rules presuppose a runtime
shell; the four review lenses collapse to fewer when a layer is absent (no shell ⇒ no Lens C). Pick
the smallest subset that covers your risk:
- **Smallest useful FCDD** = Prove (the spec + fail directions) + a Bridge on the existing code. Even
  without a twin, encoding the safety properties and testing the code against them buys most of the
  value.
- Add the **Twin** when the implementation is complex enough that "does the code match the spec?"
  isn't eyeball-able. Add the **Shell honesty + tiering** only when there's a runtime observation
  boundary (a monitor). Add **progressive gates + verify-where-it-runs** only when you deploy.
- **Brownfield** (retrofitting onto existing impure code): the entry point is to CARVE a pure core
  out of the impure code first (extract the decision logic into a side-effect-free function), spec
  THAT, and bridge it — the shell is then the residue you didn't extract. Don't spec the whole
  tangle at once.
Whatever subset you run, **say which beats you ran and why** (a partial FCDD honestly labeled beats
a full FCDD pretended — Law 10).

## 1. The beats

### Beat 0.5 — SCENARIO: operational-constraint discovery (where the deployment clauses come from)

§5 below still owns the GENERAL case ("FCDD has no hazard-analysis beat"). But the R2 incident
(2026-08-03 — a correctly-deciding day-loss dead-man false-latched 3× because nobody modeled
watcher-start × gateway-not-yet-up) proved expensive: **operational/deployment constraints are a
slice FCDD CAN partially own**, because they are largely DEDUCIBLE from the deployed missions by
systematic generation — they do not need the open-ended hazard imagination full safety analysis
demands. This beat is that generator. It sits upstream of Beat 1 because its output IS the
P1…Pn for the deployment dimension — the clauses the kernel then checks.

Two generation modes, BOTH needed — they find different bugs:

(a) **Operator elicitation (user querying).** A short structured interrogation that surfaces the
user-KNOWN-but-UNSPOKEN constraints. Per deployed mission, ask: (1) *preconditions* — what must be
true before it runs, especially what ANOTHER mission provides (a gateway, a session, a 2FA); (2)
*human-in-the-loop dependencies* and their failure modes (2FA unapproved, slow login, phone absent);
(3) *ordering* — what must precede/follow it on the clock, and what it must not run concurrently
with; (4) the *recoverability asymmetry* if it fires wrong (Law 1); (5) *self-diagnosability* — can
the mission itself, at decision time, tell its precondition is unsatisfied? (R2's dead-man provably
could not tell "gateway dead" from "gateway late"; that negative answer IS the clause — the
disambiguation must live at the deployment layer.) Record the answers as a constraint ledger; any
"another mission handles that" becomes a cross-mission clause to VERIFY, not assume.

(b) **Combinatorial mission analysis.** Enumerate the deployed missions (gateway-bringup, watcher,
rebalance, soak, monitor, kill-switch) and take their STATEFUL products: "mission A running while
mission B's precondition is unsatisfied." This is the generator that produces scenarios NOBODY
specified — the deductive core. It is tractable where general hazard analysis is not: N missions ⇒
N² pairs, each a small state machine over a shared event alphabet {service_start, service_stop,
gateway_up, gateway_down, human_2fa, tick(verdict), latch, halt}. R2 was exactly (watcher-start ×
gateway-not-yet-up): neither mission's spec alone contains the constraint; their PRODUCT does. For
each product the verdict is one of THREE (not two) — *conforming*, *nonconforming*, or the
R2-revealed third: **per-tick-conforming-yet-deployment-nonconforming** (the dead-man decided every
poll correctly; the wiring still caused a false-latch). That third verdict is the whole reason this
beat is a separate layer and not a fold into Beat 1.

**From scenario to clause.** Each scenario is a TRACE over the shared alphabet. Nonconforming traces
and per-tick-OK/deployment-bad traces both become clauses (the latter as DEPLOYMENT-LAYER clauses
that compose with, never weaken, the per-tick kernel). Real incidents (Law 6) encode as regression
theorems — the 3 observed false-latches are a permanent theorem the deployment spec must catch.

**The enforcement bridge — the spec is not the checker.** Every deployment clause gets a designated
enforcement site, and the badge-matches-detector rule (Law 3) applies to EACH:
- *static* (textual, pre-install) → a deployment/cron validator that catches text regressions (badge:
  attempt-adjacent — it sees the cron line's shape, never real gateway state);
- *runtime* (post-hoc, from independent logs) → the conformance monitor surfacing the symptom (badge:
  monitored — real world state drives it, evidence from independent sources);
- *kernel* (the trace judgment) → the Lean state machine (clause of record, TIMELESS on purpose — it
  judges ORDERING, not wall-clock timing; timing thresholds are shell constants, Beat 3.5).
Forcing a wall-clock timing property into the per-tick kernel spec is wrong-domain; this beat names
where each kind of property lives. Worked exemplar: `tests/lean/DeploymentOrdering.lean` (kernel) +
`ikbr_tools/cron_guard.py watcher_gating_violations` (static) + `opsspec.startup_false_latch`
(runtime) for the R2 ordering clause.

**Proportionality (Law 10).** Run this beat for the DEPLOYMENT/COMBINATORIAL dimension — not for the
core decision logic (Beat 1 owns that from its own P1…Pn). The R2 class — precondition,
precondition-dependency, and ordering bugs across cron lines and human-in-the-loop steps — is its
target; do not inflate it into the general safety analysis it cannot replace.

### Beat 1 — PROVE: the contract of record

0. **Entry obligation (law 13).** Before writing a single clause, fix where clauses may come
   from and how coverage will be shown: each P will carry a provenance tag; every stated
   requirement must end up mapped to ≥ 1 clause and every clause to ≥ 1 requirement, with
   orphans recorded as named residuals; the completeness scope is declared in writing as a
   declaration (not a proof); and the clause set will be mutation-tested against itself at the
   end of the beat. A clause set that no self-mutation can break is not pinning anything.
1. Write the safety properties in prose first (numbered: P1…Pn), each with its **fail direction**:
   for every input that can degrade (missing, stale, NaN, corrupt, ambiguous), name the verdict it
   must map to — and pick asymmetries by **recoverability** (a false halt you can `rm` beats a
   missed halt you cannot; a fake gain must never mask a loss, but a suspicious loss should count).
   Prefer explicit 3-valued logic (SAFE/DANGER/UNKNOWN) over booleans wherever "we could not tell"
   is a real state; compose sources with a safe-OR (any DANGER wins; all-UNKNOWN stays UNKNOWN,
   never a vacuous SAFE).
2. Formalize as the **spec of record** in a kernel-checked prover (default Lean 4 core; Coq/Rocq,
   Isabelle, Agda are equivalents — but "kernel-checked" is the load-bearing word: it EXCLUDES
   solver-trusted verifiers like Dafny/F*/Why3/PVS and Isabelle's `smt`, whose guarantee is an SMT
   backend, not a small trusted kernel; those are a different, weaker tier — say so if you use one).
   Run the **completeness gate**: your prover's OWN accounting must report ZERO unproven obligations
   of any kind — but the mechanism DIFFERS by prover, so know yours: Lean/Rocq surface `sorryAx` /
   `admit` in the axiom report (`#print axioms` / `Print Assumptions`); **Isabelle `sorry` is an
   ORACLE, not an axiom** (a naïve axiom-report check passes a holey Isabelle proof — check the
   oracle/`skip_proof` machinery); Agda has no per-theorem axiom query at all — holes fail
   compilation and `--safe` forbids postulates (structural, not "detection"). Also aim for the
   **minimal axiom profile** (know your kernel's standard axioms; a classical/heavyweight-library
   development changes the profile, not the discipline). The spec is a `Conforming` predicate: one
   clause per property, one clause = one future check = one finding vocabulary.
3. Prove, in this order:
   - **Satisfiability per class** (`spec_total`): every kind of situation the spec classifies has a
     conforming witness — a self-contradictory spec flags everything and trains its users to
     ignore it. Then add **non-vacuous witnesses**: at least one witness must genuinely exercise
     each guard/quantifier (a witness set where every premise is False proves almost nothing —
     found by review, twice).
   - **Safety consequences as theorems**: the end-to-end facts you actually care about, composed
     from clauses (e.g. "a latch actually stops the money": persistence ∘ blocking).
   - **Real incidents as theorems**: when reality produces a failure, encode that exact trace as a
     non-conformance theorem — the spec must provably catch the incident that motivated it, and it
     becomes a permanent regression proof.
4. Model factoring: dimensions that legitimately **compose** with the main classification enter as
   orthogonal trace coordinates, not new classes — a wrongly-factored spec over-forbids, and every
   false alarm teaches the operator to stop reading. State temporal weakenings explicitly (day
   booleans cannot express "A precedes B" — say so where it matters).
5. For the *invariant-proving* sub-process (claim levels L1/L2a/L2g/L2b, MC → SMT → kernel tiers,
   two-independent-solver rule, brute-force-the-statement-first), **invoke the companion
   `formal-verification` skill** — FCDD wraps it, it does the proving.

### Beat 2 — TWIN: the pure implementation

6. Get the implementation to **provably/testably agree with the spec, clause for clause**. Two
   strategies:
   - **Twin + bridge** (default here; the only option when the prover has no extraction path to your
     language, e.g. Lean 4 core → Python): a side-effect-free module that TRANSCRIBES the contract
     (same clause names/ids, same boundary operators, same constants — pin them and cross-check),
     bridged to the spec by Beat 3. Cross-language transcription IS an act of interpretation (that
     is exactly why the bridge exists) — the twin is not "the spec", it is a re-statement whose
     agreement must be earned.
   - **Verified extraction** (Coq/Rocq → OCaml, F* → C, etc.): the prover GENERATES the
     implementation — strictly stronger than transcription, but it redistributes Beat 3's
     obligations onto the extractor's trust, the FFI boundary, and numeric-width remaps rather than
     eliminating them (see the `verified-extraction-hardening` skill). If your toolchain offers it,
     prefer it and adapt Beat 3 to check the boundary, not the transcription.
   Either way: no I/O, no clocks, no environment in this layer — everything impure lives in a
   separate **shell** (Beat 3.5). This split is language-independent (Python/Rust/OCaml/Perl).
7. **Numeric-domain fidelity (tool HIGH-1 — bought by review, execution-proven).** "Same exact
   constants" holds only if the twin's numeric domain CONTAINS the model's. Python bignums/rationals
   match a Lean `ℤ`/`ℚ` spec; a fixed-width or float twin does NOT — `i64` wraps at `MAX+1`
   (silently, in Rust release), OCaml native int is 63-bit, a Perl `0.02` is a double you cannot pin
   to a kernel rational, and an unset field may read as 0 in the wrong direction. So: the twin uses
   bignums/rationals, OR scaled integers with a PROVED input domain that never overflows, and the
   bridge MUST include witnesses at the model's boundaries (caps, `MAX`, exact thresholds) where a
   width mismatch bites — small-valued witnesses hide it.
8. If the environment can legitimately shift a constant (schedules, DST, config), make the twin's
   constants **overridable parameters whose defaults are pinned to the formal model** — the shell
   derives live values, the bridge tests the defaults, and nothing leaks between calls.

### Beat 3 — BRIDGE: the conformance suite

9. The bridge is a test suite tying the SHIPPED twin to the kernel-proved facts (the `composite ↔
   Composite.lean` idiom). Honest about its own tier: the bridge **samples** agreement (finite
   witnesses, one violating input per theorem, single-field mutations, brute force over a *small*
   domain) — it is high-coverage conformance TESTING, not a proof of refinement; grade it by the
   same falsifiability rule you grade everything else. **The common-mode blind spot it cannot cover:**
   when the same author (or model, or session) writes spec AND twin, a shared misconception makes
   both sides agree, every layer passes, the kernel is green — and the user gets *maximal* false
   confidence in a wrong system. The bridge does not catch this; only Beat 3.75 (reality) and a
   Lens-A reviewer WHO DID NOT WRITE THE SPEC do (state it as the residual it is). Mandatory layers:
   - **Witnesses**: every kernel-proved witness evaluates CONFORMING in the twin.
   - **Theorem mirrors**: for each theorem, a violating input fails the RIGHT clause (the incident
     trace fails its clause; the closed hole's input now fails the new clause).
   - **Mutation coverage**: flipping one load-bearing field of a conforming witness trips exactly
     the expected clause — and **every clause has at least one negative test** (a clause whose
     failure path is never exercised is dead code waiting to happen; enumerate and check).
   - **Algorithm-vs-quantifier**: any clever implementation (an O(n) scan replacing a nested
     quantifier) is checked against a direct brute-force transcription of the formal quantifier,
     exhaustively over a small domain plus targeted adversarial patterns.
10. Wire the bridge into the single offline gate; the gate is judged **by exit code, never by its
   tail** (tail-masking loses red gates); clear stale caches/bytecode first; keep any doc-stated
   suite counts under a doc-count gate so drift fails loudly.

### Beat 3.5 — the SHELL: observation/execution honesty

11. The impure boundary (log parsing, device I/O, order placement) carries written **honesty
    rules**, enforced in code and stated in docs:
    - **Observed-sample semantics — and the arbitration rule for "evidence is missing."** There are
      THREE regimes, selected by what the missing thing IS; state the selector, don't leave it to the
      reader:
      (i) a WORLD EVENT the logs failed to carry cannot witness a violation — clauses run
      event→obligation, so an unobserved event is vacuous (fail-quiet);
      (ii) an ABSENCE-DRIVEN clause (its violation is a gap between observations — latch-persistence:
      a protected minute with no protection after it and no recorded release) false-fires on a sparse
      sample, so the shell must densify/synthesize conservatively **per EPISODE** — an *episode* is a
      maximal contiguous run of the state from one onset record to its release/expiry record; where the
      release minute is unobservable, synthesize the most-conservative release consistent with the next
      onset (one synthetic release per episode, never one for the whole day), and the twin's contract
      must NAME this exception (the default fail-quiet rule is FALSE for it);
      (iii) a MONITOR SELF-ARTIFACT that the spec REQUIRES to exist (the end-of-day judgment record) —
      its absence is a LOUD finding, because "the check ran" is itself a monitored obligation, not a
      world event. The selector: world-event ⇒ quiet; absence-clause ⇒ synthesize; required-self-record
      ⇒ loud. Law 1's "degraded ⇒ conservative" is the tiebreaker for any case these three don't cover.
    - **Attempt-adjacency**: when evidence for an obligation comes from the same record as its
      triggering event, say so — such checks catch format regressions, never world failures.
    - **Unjudgeable ≠ violated ≠ satisfied**: facts the evidence cannot decide (overwritten
      state, pre-feature eras, not-due-yet) are declined with a note, gated by judgeability rules
      — never guessed in either direction.
    - **Provenance per observable** (which log/file/socket decides it) and notes for every
      conservative synthesis, truncation, or fallback the shell performed.
12. Publish the **falsifiability tiering** (this is *monitorability analysis*, Pnueli–Zaks — grade
    every clause by what the evidence can actually falsify). The four tiers, each with its decision
    test:
    - **Monitored** — a real WORLD state can drive a violation, and the evidence for the two sides of
      the clause comes from INDEPENDENT sources. The only tier that earns "a quiet result is a checked
      claim."
    - **Attempt-adjacent (decorative)** — the evidence for the obligation and for its trigger comes from
      the SAME record (or the same process's co-written records — the "circular evidence" case: not
      literally one record, but no independent signal), so the check can catch a format/logic
      regression but never a world failure (e.g. delivery). Decision test: *could this clause fire on a
      real-world state, with the evaluator correct?* If no → here.
    - **Inert until X arms** — no observer for the clause's inputs runs yet (a gated feature); the
      clause is dormant and activating X REQUIRES adding its observers (the spec needs no change, the
      shell does). Not a defect if labeled; a silent failure if the badge omits it.
    - **Internal-consistency only** — the clause constrains observables the CLASSIFICATION already
      derived, so it is unsatisfiable by construction and can fire ONLY on a shell/evaluator bug, never
      on any world state (e.g. "noLogin ⇒ gateway-never-up" when the day was CLASSIFIED noLogin *from*
      gateway-never-up). Distinct from attempt-adjacent: that one has a real trigger but no independent
      confirmation; this one has no independent trigger at all. Value = a self-test of the shell, not
      monitoring.
    The badge must match the detector; a monitor that advertises more falsifiability than its logs
    afford is itself a silent failure — and the tiering is a LIVING artifact: re-derive it after any
    shell change, and pair each *monitored* clause with a per-run evidence-volume floor (#22) so a
    clause that silently DECAYS to inert (a broken parser, a rotated log) is caught, not read as a
    permanent quiet pass.

### Beat 3.75 — VALIDATE on reality

13. Before any review, run the system against **real historical data/days** — including the
    motivating incident (expect exactly it, and nothing else) and boring cases (weekends must be
    quietly conforming). Expect validation to find shell bugs; that is its job. Every false
    finding on a real case is a defect in spec, twin, or shell — decide which and fix at that
    layer, never by special-casing the test.

### Beat 4 — ATTACK: adversarial review against a declared budget

14. Fan out **independent reviewers with distinct lenses** (never one generalist):
    (a) spec adequacy — bad-cases-that-CONFORM (under-spec, the dangerous direction) and
    good-cases-that-VIOLATE (alarm fatigue), vacuity/tautology hunting, constants-vs-reality;
    (b) twin fidelity — clause-by-clause diff, boundary operators, exhaustive assault on any
    clever algorithm, bridge blind spots;
    (c) shell truthfulness — "can it lie?": structurally-unfalsifiable checks, circular evidence,
    tz/parsing, classification fragility, false-negative paths first;
    (d) integration + docs — will the wiring actually run (see #18), do the docs overclaim, does
    the package contain what it says. Full prompt pack: `references/lenses.md`.
15. Reviewer contract: **prove findings by execution** (probes in a scratchpad, target read-only),
    mark CONFIRMED vs hypothesis, and state "attacked, no defect found" per clean area — padding
    is a review defect. Route adversarial work to your strongest/most-independent reviewer
    (operator rule here: the Fable model; generalize: a different model or person than the
    author).
15.5 **DECLARE THE ATTACK BUDGET BEFORE THE BEAT STARTS — coverage is the stop
    condition, not convergence.** Bought by case02 (56 runs, `fcdd_lab/method/ATTACK_BUDGET_DIAGNOSIS.md`):
    under the old iterate-to-convergence rule the ATTACK beat ran **1 to 18 rounds**
    across runs of the *same* defect, round count correlated **r = 0.72** with run
    cost and explained about half its variance, and runs with >= 6 rounds cost
    **$48.33** against **$28.42** for runs with <= 2 — while **all 56 runs, both
    arms, produced a byte-identical artefact**. Every extra round bought nothing
    measurable, at 1.7x the price and an 18x spread. The control arm's bounded
    review varied 3x and correlated **-0.21**. Unbounded review is where FCDD's
    unpredictability lives, and predictability is the property the method is sold
    on.
    The rule conflates two things and stops on the wrong one:
    - **coverage** — have all four lenses been applied to the declared surface?
      Bounded, checkable, priceable in advance.
    - **convergence** — has iteration stopped producing findings? Unbounded,
      judgement-based, priced only in arrears.
    So: **stop on coverage; budget convergence.**
    - Declare the surface set **S** before the beat begins.
    - **Mandatory pass:** every lens against every surface, **one round, in
      parallel**. Cost = |S| x 4 agents, known before you start.
    - **Remediation:** if a finding is CONFIRMED blocking, exactly **one** further
      round, scoped to the affected surface, re-verifying that finding only.
    - **Hard stop at two rounds.** Remaining findings become named residuals and
      ship — which #16 already requires.
    - **Widening the surface starts a NEW attack with its own declared budget.**
      It is not a continuation and its price is quoted separately.
    The mandatory pass keeps the property that actually catches defects — four
    independent lenses — and removes the iteration, which on the measured benchmark
    caught nothing. The budget is **operator-set, not small**: if you believe your
    surface needs six rounds, declare six and pay a known price. What is removed is
    the *agent's* discretion to keep going, which is where the variance came from.
    **Honest status:** the diagnosis is strongly evidenced; the fix's benefit is
    predicted, not demonstrated. The evidence comes from a benchmark on which
    nothing failed, so it cannot show what bounding would lose on harder work. If
    you are working where a late round plausibly earns its cost, declare a larger
    budget — do not reopen the loop.
16. **Ground-truth every load-bearing finding yourself by execution before accepting it** — and
    equally before *rejecting* it. Then fix, then **re-review the fixes** (a focused pass,
    inside the declared budget of #15.5).
    Convergence is **per review-surface, not global**: reachability decreases within a FIXED scope,
    but *widening the scope legitimately re-opens reachable findings* — in the arc, a narrow "GO" was
    followed by a full-code review that found new reachable arming blockers, and one deployment bug
    recurred five times (twice against the author fixing it). So the criterion is: within an
    unchanged surface, severity trends down and a round yields only accepted residuals; when you
    WIDEN the surface (a new lens, a bigger diff, the shipped-vs-staged artifact), reset and expect
    reachable finds again. A late-round reachable find is not a failure of convergence — it is
    evidence the surface grew. "pure-contract-only" = a defect real in the pure spec/twin but
    unreachable from the live inputs (the safe residual band). Residuals get **named, in writing**,
    with their trigger conditions. (Severity map: HIGH≈reachable, MED≈pure-contract/fragility,
    LOW≈hygiene.)
16.5 **SERIALIZE the solver and the reviewer over one working tree** — a turnstile, not a
    reminder. Bought by three consecutive defects in the 2026-08-07 ikbr_tools loop, each
    costing a MEDIUM finding that was a pure artefact of the race: a review flagged work as
    "uncommitted" that had been committed 20 minutes earlier; another measured test counts while
    an agent rewrote the suites; the third caught the ORCHESTRATOR's own `git add -A` sweeping an
    agent's in-progress edit into an unrelated commit — violating a rule the orchestrator had
    already written down after the first. Reminders had failed three times; the fix has to be
    mechanical.
    - **One token, two holders, and the token's state is COMMITTED.** `SOLVER` = the tree may
      change. `REVIEWER` = the tree is FROZEN at a named sha; the solver must not edit, commit,
      or launch agents that edit. Because the flip is itself a commit, at any commit the token
      says who owned the tree from that commit onward.
    - **The last act of a solver turn is `release`** (freeze at HEAD, refusing a dirty tree —
      uncommitted work is work no commit records, so the reviewer would be measuring ghosts);
      **the first act of the next solver turn is `claim`**, naming the review just assessed.
    - **It cannot force an external reviewer to wait — and does not pretend to.** What it buys is
      DETECTION that is deterministic instead of archaeological: a review whose reported sha
      names different CODE than the freeze was racing, and one command says so rather than three
      findings later. (Reported *sha*, not code, is the wrong test — an honest reviewer runs at
      HEAD, which is the flip commit itself. Same off-by-one as below; it bit both branches.)
    - **The honest handoff must be SILENT.** The flip is itself a commit, so `release` reads HEAD
      *before* that commit exists and the correct handoff always leaves HEAD one ahead of the
      frozen sha — a raw sha comparison cries RACE every single time. Found on the protocol's
      FIRST execution. Compare what the reviewer actually measures (the code: diff the trees with
      the token's own path excluded), because an alarm that fires on the honest path trains the
      operator to ignore the one that matters.
    - **"Dirty" means TRACKED edits, not untracked files.** A `git status --porcelain` that
      counts untracked files made the guard cry RACE over the operator's own tooling dropped in
      the tree, though no committed code had moved -- the THIRD honest-path false-positive, after
      the two flip-commit ones. An untracked file is in no commit and alters no sha; a review of a
      named ref never reads it. Count only `--untracked-files=no`. Each of the three was the same
      root error: the guard answered a question (did the reviewed code move?) with a cheaper proxy
      (did the sha / working tree change at all?) that fires on the honest path. Test the guard
      against its OWN honest handoff before trusting it.
    - **Fail direction: a missing or garbled token is NOT permission.** It refuses (the same rule
      as every other guard: degraded input yields refusal, never a free pass).
    - Reference implementation + its regression suite: `scripts/review_turnstile.py`,
      `tests/tests_review_turnstile.py` (ikbr_tools). The generalisation: whenever a reviewer and
      an author share mutable state, make the handoff an artefact, not an etiquette.

17. Ledgers throughout (append-only, supersede-don't-delete):
    - **Decision log**: every fork records the choice, the rejected alternative *with its concrete
      failure mode*, and the assumptions it rests on. Waived gates (e.g. a skipped soak) get an
      entry with the honest basis, the accepted residual, and the mechanical gate replacing them.
    - **Assumptions ship with conclusions** (data, model/domain, statistical, interpretation,
      scope — per the formal-verification skill §2.8): a conclusion whose assumptions would not
      survive being listed is not a conclusion.

## 2. Shipping and operating (the beats keep running)

18. **Verify where it runs, never in your simulation of it.** Deployment artifacts are verified by
    *extraction and execution*: packages are unpacked and greped (secrets scrubbed by a
    fail-closed build gate, then independently re-checked by extraction — never trust the
    builder's own report); scheduled jobs are verified by extracting the EXACT installed payload
    and running it from a hostile cwd (`$HOME`) — this specific check caught the same cwd bug
    five times, twice against the author fixing it, once masked by a manual `cd` in the
    simulation and once by a silent no-op edit. Keep installed bundles in **version–content
    lockstep** with the repo; a stale bundle silently shadowing new safety behavior is a recorded
    incident class.
19. **Progressive enablement gates**, outermost first: a behavior-neutral foundation with an
    identity proof (`f([x]) ≡ x` ⇒ the refactor is provably a no-op) → a code gate (a constant
    flipped only in the same commit as its FV + review) → an operator gate (an explicit config
    token, fail-direction chosen per key: enabling keys fail-safe-ON, arming keys fail-safe-OFF)
    → an evidence gate (soak, or its documented waiver + a mechanical preflight with exit-code
    semantics). Rollback must be a config revert, never a redeploy.
20. **Composition seams are proof obligations.** A property proved per-tick/per-call does NOT
    survive stateful composition (a streak counter, an accumulator, a cache) — re-verify at every
    seam, with the meta-property stated (e.g. "adding a source can only ADD protection", proved
    through the state machine, not just the tick).
21. **Operator interface honesty**: commands handed to a human are copy-paste-exact and idempotent
    (an abbreviated line WITH `...` was once pasted verbatim into a crontab); prefer installing
    config programmatically from the staged file over hand-editing; announce postures (silence
    must never encode a state); alerts run event→alert only, so no notification state can gate a
    safety action; window-guard operational actions that are only safe at certain times.
22. **Runtime verification can replace SOME soak evidence — never assume it replaces the soak.**
    This is the arc's most expensive lesson, so state it in full: the soak was waived, the monitor
    became the safety instrument, and *that monitor's own review verdict was "a good four-clause
    detector wearing a full-spec badge"* — the replacement shipped hollow and was caught only by
    Beat 4. Therefore, before waiving a soak:
    - **Compare clause-by-clause** what the soak would have measured against what the monitor can
      actually falsify (its *monitored*-tier clauses only — #11). A monitor replaces soak evidence
      ONLY for monitored-tier clauses; for attempt-adjacent/inert clauses it replaces NOTHING.
    - Note what the soak measured that NO conformance monitor can: a **rate over time** (e.g. a
      false-halt frequency) is a statistical property, not a per-day clause — clause-conformance does
      not measure it at all. Keep the statistical gate for statistical claims (the `formal-verification`
      skill's L2b tier).
    - **The monitor must have survived its own ATTACK (Beat 4) first** — an untriaged monitor is
      *worse* than the soak: evidence lost, false confidence gained.
    Then the nightly judge writes a conformance ledger, posts a **liveness/posture line every run**
    (Law 9 — never alert-only-on-violation: a silent lane must be distinguishable from a clean
    night; a quiet night is a *checked* claim ONLY for monitored-tier clauses that observed evidence
    this run — pair each with a per-run evidence-volume floor so a clause that decayed to inert is
    caught, #11). Its own health is part of the spec (a missing end-of-day record is a finding), but
    a dead judge cannot judge its own absence — an **independent liveness observer** (a second cheap
    watchdog, not the monitor) must alert if the judge did not run. Judgeability gates keep refusals
    and not-yet-due checks from false-firing on night one; trace the FIRST night's exact sequence
    before shipping.

## 3. Default toolchain — and what survives substitution

| Role | Default here | Substitutes | The invariant that must survive |
|---|---|---|---|
| Kernel prover (spec of record) | Lean 4 core, no mathlib | Coq/Rocq, Isabelle, Agda | **kernel-checked** (excludes solver-trusted Dafny/F*/Why3); minimal axiom profile; completeness gate = zero unproven obligations in the prover's OWN accounting, whatever its form (axioms / admits / **oracles** / holes — mechanism differs, see Beat 1.2); witnesses + consequences + incident theorems |
| Quantified checking | z3 **and** cvc5, UNSAT-of-negation | Yices, MathSAT, Alt-Ergo | TWO independent verifiers agree; negation-UNSAT over ALL inputs. **If you drop to one solver, or to a property-based tester (QuickCheck/proptest) that can only SAMPLE, that is a claim-level DOWNGRADE (proved → exhaustively-checked → not-falsified-in-N) — legal, but recorded in the decision log and the badge** (never call sampled "proved") |
| Exact numbers | sympy | Mathematica, PARI, by-hand rationals | every tier pins the SAME exact constant |
| Twin + shell | Python (pure module + impure script) | Rust, OCaml, Haskell, Perl | pure/impure split; twin AGREES with the spec clause-for-clause (transcription+bridge, OR verified extraction — Beat 2); **the twin's numeric domain CONTAINS the model's** (bignum/rational, or scaled ints with a proved domain — a fixed-width/float twin silently diverges at boundaries, tool HIGH-1); constants pinned with parametrized overrides |
| Bridge + gate | plain-script suites, one gate, exit codes | pytest, cargo test, CI | witnesses/mirrors/mutations/brute-force layers; judged by exit code; every clause negatively tested; the bridge SAMPLES agreement (not a refinement proof) |
| Adversaries | subagent fan-out, strongest model | different humans/teams, red team | independence from the author; distinct lenses; execution-proved findings; author ground-truths |
| Ops wiring | cron+systemd+telegram, deb packaging | Task Scheduler, k8s, rpm | verify-where-it-runs; extraction re-check; version-content lockstep; event→alert direction |

**Substitution rule (tool review):** a substitution that CANNOT preserve a row's invariant is legal
only with an explicit **claim-level downgrade** recorded in the decision log and reflected in the
badge (proved → exhaustively-checked → sampled/not-falsified) — never silently. The formal-verification
skill's L1/L2a/L2g/L2b claim levels are the vocabulary for this. A shop with only a property-based
tester, or a model checker (TLA+/TLC) that explores a bounded state space, or a solver-trusted verifier,
is doing FCDD at a lower claim tier — which is fine, *labeled*.

## 4. The laws (cross-cutting; laws 1–7 and 9 were each bought by a named defect in the arc; 8, 10 and 11 are governing principles, not defect-derived — 11 added after the R2 incident; **12 was bought by measurement, not incident** — case02, 56 runs)

1. Degraded input ⇒ the **conservative (fail-safe) verdict**, never the convenient one — for a 3-valued
   source that is UNKNOWN (never a vacuous SAFE), and the safe verdict is whatever forces protection to
   engage in the domain at hand; asymmetries by recoverability.
2. Local proofs die at stateful seams — re-prove the composition.
3. The badge must match the detector (publish the falsifiability tiering).
4. Verify claims where they RUN: exit codes, extracted packages, exact installed payloads.
5. Two independent verifiers for anything load-bearing — including your reviewers, including you
   re-executing your reviewers.
6. Real incidents become theorems.
7. Spec coherence (satisfiability, non-vacuous witnesses) before code conformance.
8. Every conclusion ships its assumptions; every decision its rejected alternative's failure mode;
   every waived gate its residual.
9. Silence never encodes a posture; alerts never gate actions.
10. Proportionality: FCDD is for load-bearing systems — and a partial FCDD honestly labeled beats
    a full FCDD pretended.
11. Operational constraints are deduced, not given — combinatorial mission analysis + operator
    elicitation (Beat 0.5) produce the deployment invariants the kernel then checks. The per-tick
    spec is necessary but not sufficient at the deployment seam: a trace can be per-tick-conforming
    yet deployment-nonconforming, and only the deployment layer can disambiguate what the mission
    cannot self-diagnose. (Earned by R2, 2026-08-03: a correctly-deciding dead-man false-latched 3×
    because nobody modeled watcher-start × gateway-not-yet-up; caught by Beat 4 review, not by the
    per-tick kernel — the gap Beat 0.5 now partially closes.)
12. **No unbounded loop in the method. Every iterative beat declares its budget before it
    starts, and stops on coverage rather than on a judgement that iteration is done.**
    Predictability is what this method is sold on, so a step whose cost the operator cannot
    quote in advance is a defect in the method, not a property of the work. Measured: under
    iterate-to-convergence the ATTACK beat ran 1–18 rounds on repeats of the *same* defect,
    round count correlated r = 0.72 with cost, and the extra rounds changed no artefact
    (`fcdd_lab/method/ATTACK_BUDGET_DIAGNOSIS.md`). The bounded control arm varied 3× and
    correlated −0.21. Budgets may be large — set by the operator, declared in writing — but
    they are set *before*, and the agent does not get to extend them.
13. **Every clause declares where it came from, and the clause set must survive
    mutation of itself.** The kernel proves coherence; it cannot prove the spec is
    the right spec (§5). But three things it *can* prove are currently left
    unowned, and "where P1…Pn come from is on you" is not an interface — every
    other seam in this method carries an obligation with a mechanical exit.
    On entry to Beat 1, therefore:
    (a) **provenance** — every clause tags its source (a stated requirement, a real
    incident per law 6, or a named generator such as Beat 0.5's mission products);
    (b) **bidirectional traceability** — every stated requirement maps to ≥ 1 clause
    and every clause to ≥ 1 requirement, with orphans in either direction written
    down as named residuals rather than passed over in silence;
    (c) **a declared completeness scope** — "these hazards, by this technique, and
    here is what we did not consider": a declaration, never a proof, and labelled
    as one (law 3);
    (d) **pinning, measured by mutation that names its clause** — mutate the TWIN
    and require a *named clause* to reject each mutant. The mutation is applied to
    the implementation; **the inference is about the clause set**: a mutant that no
    clause rejects is not an implementation bug, it is a COVERAGE GAP in P1…Pn.
    (A complementary check, mutating the spec's own definitions and asking whether
    the theorems still prove, is weaker than it looks — a definition that IS its
    own specification is maximally mutation-sensitive while proving nothing.)
    (d) is the one that earns its place by execution: in `pipeline_proto` the
    mutation `M4_boundary` survived the reachability witnesses, the theorem
    mirrors and a 1,200-case exhaustive sweep, because P1–P5 constrained the
    *shape* of the verdict and never pinned *where* fresh becomes stale. P6 closed
    it. Reading the spec would not have found that.
    This does NOT make the method cover intent — it covers *stated* intent, and a
    need nobody wrote down stays unreachable. What it buys is that the residue is
    **named** instead of invisible. Do not add a hazard-analysis *beat*: its exit
    condition is unbounded judgement, which laws 3 and 12 both forbid.
    Derivation and honest tier: `fcdd_lab/method/INTENT_COVERAGE.md` (derived
    diagnosis, predicted benefit, N = 1 supporting execution — weaker evidence
    than law 12's 56 runs, and it should be cited that way).

## 5. What FCDD does NOT do (read before trusting it)

- **It proves COHERENCE, never CORRECTNESS-OF-INTENT.** The kernel proves the spec is
  self-consistent and its consequences follow; it cannot prove the spec is the RIGHT spec. FCDD has
  no GENERAL hazard-analysis beat — where P1…Pn come from is on you (FMEA/STPA/threat-modeling
  upstream). Garbage clauses, kernel-checked, are still garbage. **Caveat (the third category):**
  operational/deployment constraints sit BETWEEN coherence (fully FCDD-owned) and correctness-of-
  intent (fully upstream) — they are largely deducible by combinatorial mission analysis + operator
  elicitation (Beat 0.5), so this slice IS partially FCDD-owned. R2 (2026-08-03) is the defect that
  bought that caveat: the per-tick dead-man spec was coherent and the dead-man decided correctly,
  yet a deployment-ordering hole nobody had modeled false-latched it 3×. The hole was deducible
  from the deployed missions; it just had no beat to deduce it until Beat 0.5.
  **What IS owned (law 13, added 2026-08-26):** coverage of *stated* intent —
  clause provenance, bidirectional requirement↔clause traceability, a declared
  completeness scope, and pinning measured by spec-side mutation. So the precise
  claim is: FCDD cannot prove the spec is right; it can prove the spec is complete
  against what was **stated**, traceable to why each clause exists, and strong
  enough to reject a mutation of itself. A need nobody wrote down stays
  unreachable, and that residue is what this bullet is still right about.
- **The bridge cannot catch common-mode error** (spec and twin sharing the author's mistake) — only
  an independent Lens-A reviewer and reality (Beat 3.75) can. So the author grading their own
  homework is the standing residual: FCDD reduces it (independent reviewers, execution-proof,
  ground-truthing) but never removes it. The truly independent party in the arc — the human operator
  — has no mandated role here; add one for anything high-consequence.
- **It caught the hollow monitor; it did not prevent it.** FCDD's value is *late* (adversarial
  review) as much as *early* (proof). Present it that way; a reader who thinks the proof stops all
  bugs will be surprised the way this arc was.
- **Evidence base = N=1**, distilled the same day the arc ended, largely author-reviewed. Treat the
  laws as well-motivated hypotheses hardened once, not validated practice. (Applying the skill's own
  badge-matches-detector rule to itself.)

## 6. Prior art (the honest lineage — most of this is naming, not inventing)

FCDD is a *packaging* of established ideas; cite them, don't reinvent them. Design-by-Contract
(Meyer); the functional-core/imperative-shell split (Bernhardt) = Beat 2/3.5; **mutation testing**
(DeMillo–Lipton–Sayward) = the single-field-trip-exactly-its-clause bridge layer; **model-based /
conformance testing** (Tretmans ioco) and property-based testing (QuickCheck) = the bridge; the
**small-scope hypothesis** (Jackson/Alloy) = brute-force-over-a-small-domain; **runtime
verification** (Havelund–Roşu) and **3-valued LTL monitoring** (Bauer–Leucker–Schallhart, literally
true/false/? ) = Beat 3.5; **monitorability** (Pnueli–Zaks) = the falsifiability tiering, renamed;
fail-safe design = fail-direction engineering; Architecture Decision Records (Nygard) = the decision
log; refinement/verified extraction (Coq, seL4, CompCert) = the stronger Beat-2 alternative. Beat
0.5's two generators owe: **STPA** (Leveson — unsafe control actions over controller/controllee
feedback loops; the "mixed-missions product" is the control-loop-hazard idiom) for the combinatorial
mode, and **scenario-based modeling / Live Sequence Charts** (Harel et al.) for the
trace-generation idiom. What is locally new is only the *assembly*: the beat sequence, Beat 0.5's
two-mode operational-constraint generator (elicitation + combinatorial mission analysis) with its
three-valued scenario verdict and its static/runtime/kernel enforcement bridge,
incidents-as-kernel-theorems as a regression habit, the falsifiability-tiering-as-published-badge
discipline, and the verify-where-it-runs deployment checklist as one bundle.

## 7. Files

- `references/lenses.md` — the four adversarial lens prompts + reviewer contract + convergence.
- `references/case_study.md` — the worked exemplar (ikbr_tools watcher + ops monitor), mapping
  every beat to real files you can read.
