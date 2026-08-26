# CASE 05 — proposal: testing the prevention claim under isolation that holds

**STATUS: DRAFT r2 — not frozen, nothing scheduled, nothing built.** r2 applies
the four blocking findings and thirteen others from adversarial review round 1
(§11). Two of them changed the design rather than its wording: the co-primary
gate was unpowerable at any scale this lab has run (B2, independently
re-simulated), and Option B is retired (B3). Freezing is
the operator's act, and it should not happen until the D1 fork in §6 is decided
and the §9 kill criteria are checked against reality. This document exists
because case 04 answered nothing and named why; it is the design that would
have to be true for a re-run to be worth its cost.

---

## 1. The defect to design against: one flaw wearing three coats

| # | What leaked | The control that existed | Why it missed |
|---|---|---|---|
| A17 (case02) | The pristine binary, shipped into 28 of 28 treated workspaces | Human diligence about what a workspace should contain | It was a judgement, not a program. Survived three review rounds |
| F1 (case04) | The whole case01 tree, via a symlink 12 of 13 cells created themselves | `workspace_manifest_guard.py`, hashing files in the arm workspace | Subtree-scoped and symlink-blind. A symlink target is not a file in the subtree |
| A11/A19 (repo) | The engine tape, deposited in the public repository since 2026-07-29 | `.gitignore` rules on `sealed/`, `KEY_*.json` | The step-1 package wrote a second copy under a path no rule enumerated |

**The common shape: every control enumerated _paths_ while the hazard was
_content_, and each was aimed at the runs while one of the three leaks was in
the deposit.** A fourth instance should be assumed to exist somewhere this
proposal has not looked.

**The case04-specific accelerant, which matters more than the mechanics.** The
task was *clone a hidden engine*. The cell's reward was agreement with a
function it could not see, so **every information channel was a scoring
channel** and the agent's incentive pointed straight at the leak. The cells did
not misbehave; they optimised. A design that hides the answer and then pays for
proximity to it is a design that must make the answer *physically absent*,
because it has made finding it the whole job.

---

## 2. Threat model, stated as an attacker

The cell is a capable coding agent with `bash`, a wall-clock budget, and a
scored objective. Assume, with no malice attributed:

- it will `ls` upward from its cwd, and follow anything it finds;
- it will create symlinks, copy trees to `/tmp`, and run any executable on the
  box, including the emulator that the query cap was meant to meter;
- it will read any file it can open, including another case's sealed material;
- it will not be stopped by a prompt saying not to. **Case02's own conclusion —
  "instructions leak" — is a finding of this lab, not a hypothetical.**

It follows that none of these are controls: a sentence in `PROMPT.md`; a
counter living in the client the cell can bypass; a guard that inventories a
subtree the cell can step outside of; a reviewer's later diligence.

**Only one thing is a control: the material is not in the cell's namespace.**

---

## 3. The isolation architecture

Four layers, each falsifiable by a test that runs before any cell does.

### L1 — Namespace absence (the load-bearing layer)

Each cell runs under `bwrap` (verified present on this host, unprivileged
userns enabled — no Docker required):

```
bwrap --unshare-all --die-with-parent \
      --ro-bind /usr /usr --ro-bind /lib /lib --ro-bind /lib64 /lib64 \
      --ro-bind /bin /bin  --ro-bind /etc/alternatives /etc/alternatives \
      --tmpfs /tmp --proc /proc --dev /dev \
      --bind  $CELL_WS /work \
      --bind  $ORACLE_SOCK /work/.oracle.sock \
      --chdir /work  --setenv HOME /work \
      -- <runner>
```

- `--unshare-all` includes `--unshare-net`: **the cell has no network at all**,
  so there is no egress to allow-list and no model-side fetch to police.
- The lab tree is not bind-mounted. `/media/sf_Projects` and `$HOME` are simply
  **not in the namespace** — there is nothing to symlink *to*. F1 becomes
  unrepresentable rather than guarded against, which is the standard case03 set
  for itself and then failed to meet.
- The toolchain (Rocq, rustc, python) is reachable read-only via `/usr`; if a
  toolchain lives in the operator's home (opam switch), it is copied into the
  cell image, never bound from home.

**Runner topology (B1) — the agent's own model access.** `--unshare-net` also
blocks the coding agent's inference calls, so the design is unrunnable until this
is stated. **Resolution adopted: the agent loop runs INSIDE the sandbox, and
reaches its model through a second bind-mounted socket** relayed by an
orchestrator-side proxy. The alternative — harness outside, exec each tool into
the sandbox — moves the trust boundary onto the harness's own context assembly
(cwd, env, prompt files), which is precisely A17's surface, and a harness with
enough filesystem reach to orchestrate cells can also see the lab tree, reviving
F1. The relay is honest about its cost: it is a bidirectional channel and
therefore a richer exfiltration path than the oracle socket, so it gets its own
gate (**G-RELAY**: full traffic log, oracle-shaped-query detection, byte
accounting per cell) and §3-L2's "only through a UNIX socket" is stated as *two*
sockets, both orchestrator-held and both logged.

*Verified on this host, 2026-08-26:* a cell under `--unshare-all` reached an
orchestrator-held oracle over a bind-mounted socket (`ANSWER(query='legal --fen
startpos', served-by-orchestrator)`) while `urllib` to a public API raised
`URLError`, `/media/sf_Projects` and `/home` were absent, and `/proc` showed only
sandbox-local processes. Practical constraint found in the same test: `AF_UNIX`
caps socket paths at 108 bytes, so cell roots must be short.

**Toolchain (m1, m4).** cargo and opam resolve dependencies over the network at
build time, which `--unshare-net` forbids: every dependency is **vendored into
the cell image** and the image itself is a hashed input to G-ISO, not merely the
workspace. For any subject derived from a sealed artefact, the image is where a
smuggled copy would hide.

**Test before use (M2):** the probe cell performs a **positive closure
enumeration** — walk the entire reachable filesystem, resolve every symlink,
enumerate the mount table, hash what it finds, and diff against the image
manifest. It does *not* check a blocklist of paths named in case04's
transcripts: §1's whole thesis is that controls fail because they enumerate
paths, and last time's leak is the one channel a new design is least likely to
repeat. The probe's transcript and closure hash are deposited as the isolation
evidence.

### L2 — The oracle is a service, not a program the cell owns

The oracle daemon runs **outside** the sandbox as the orchestrator, holding the
engine, the emulator and the ROM. The cell reaches it only through a UNIX socket
bind-mounted into `/work`. Therefore:

- the cell cannot run the emulator directly (C14's failure — six case04 cells
  bypassed the client-side counter by doing exactly this), because the emulator
  is not in its namespace;
- the query counter lives **server-side**, in the daemon's log, and is the
  ledger's ground truth. A cap is enforced by refusal to answer, not by client
  bookkeeping;
- every query is logged with its arguments hashed, so the *information the cell
  bought* is measurable after the fact — not just its count;
- the socket carries a per-cell token; cross-cell reuse is detectable and is an
  integrity failure, not a curiosity;
- **the daemon is stateless per cell (m3)**: no cache, no adaptive counter, no
  answer that depends on another cell's queries. A shared daemon with memory is
  case04's shared-root reuse one level in.

### L3 — The scored corpus does not exist while the cells run

Case04 sealed a corpus and then had to defend it. **A corpus that does not exist
cannot leak.** Commit-reveal instead:

1. The pre-registration commits the corpus *generator*, its parameters, and a
   salted hash of the seed. The seed itself is held by the operator, off the
   machine the cells run on.
2. All cells run. Nothing about the scoring set exists on disk, in any
   namespace, at any point during the runs.
3. After the last cell closes, the seed is revealed, the corpus is generated,
   the hash is checked against the pre-registered commitment, and every
   submission is scored against it.

The seed's entropy is stated in the pre-registration (m5): the generator and its
parameters are public at commit time, so a low-entropy seed would let the corpus
be narrowed offline before reveal. With no cell-side network the risk is small,
but the claim must be checkable rather than assumed.

This also kills a subtler leak the obvious fix would have introduced: a
held-out corpus that the *oracle refuses to answer about* turns refusal into a
**membership oracle** — probe the boundary, learn the test set. Commit-reveal
needs no disjointness enforcement, because there is no boundary to probe.

### L4 — Forensics as pre-registered gates, computed before the scores are seen

Case04's leak was found by an adversarial review round *after* the numbers
existed, which is how a broken study acquires a plausible result first and a
verdict second. In case 05 the integrity checks are **gates, ordered before
scoring, and blind to outcome**:

| Gate | Falsifies | Cannot falsify |
|---|---|---|
| G-ISO closure hash | any file in the cell's reachable closure not in the image manifest — symlinks resolved, mounts enumerated | material the cell never wrote down |
| G-NET no-egress probe | a network path out of the sandbox | an out-of-band channel through the socket |
| G-CAP server log | queries beyond cap, cross-cell token reuse | whether the answers bought were *enough* |
| G-XSCRIPT constant match | submissions containing byte-equal runs of engine constants (case04 F3's check, promoted from a review finding to an automatic gate) | a paraphrased transcription |
| G-CLUSTER cross-arm identity | submissions whose behaviour is mutually identical across arms (case04 F4) | genuine convergence on an easy target |
| G-DEPOSIT manifest hash | sealed content deposited anywhere in the repository, by any path (A11/A19) | content leaked outside git |

**A cell failing G-ISO, G-NET, G-CAP or G-RELAY is excluded before scoring and
reported as excluded** — mechanically, no judgement. **G-XSCRIPT and G-CLUSTER
are NOT controls (M4)**, and r2 stops calling them gates in all but name: both
end in a human adjudication, which is exactly what C1 forbids ("the check is
code, not a person's diligence"), and G-XSCRIPT's own row concedes it cannot
catch a paraphrased transcription. They are retained as **descriptive detectors
whose output is deposited**, and the design does not rely on them. Under Option A
that is affordable, because there is no hidden artefact to transcribe; it would
not have been affordable under Option B, which is one more reason B is retired. The order matters: the
integrity verdict must not be reachable from the score, or the temptation
case04 documented reappears.

---

## 4. New constraints, C17–C22

Inheriting C1–C16 verbatim (case04, which inherits case03, which inherits
case02's amendments), and converting case04 §8's lessons plus A11/A19 into
checkable form:

- **C17 — the oracle is a service the cell cannot read, never a CLI whose
  dependencies resolve into the orchestrator's tree.** Case04's CLI was broken
  by construction: it referenced paths the builder never created, so bridging to
  the real tree was the only way to make it work at all. *The cells were
  effectively instructed to leak.*
- **C18 — cells get no filesystem reach outside their workspace, and the
  workspace does not live where the lab lives.** No `external_directory: allow`.
- **C19 — the guard scans the reachable closure, not a subtree**: symlinks
  resolved, mount table enumerated, at cell start *and* at cell exit.
- **C20 — the query cap is enforced where the engine runs.**
- **C21 — the scored corpus is generated after the last cell closes**, from a
  seed committed by hash in the pre-registration and held off-host.
- **C22 — the deposit is audited like a workspace**: every tracked file hashed
  against the sealed manifest before publication, and on every subsequent
  push. The check case03 C1 already specified, pointed at the repository.

---

## 5. The subject: a fork for the operator (D1)

The seven-fault set is retired (A11/A19), so case 05 needs a subject regardless.
Two live options; this is the operator's call, per the lab's convention.

**Option A — revive PORTGUARD (case03's selected design).** A pre-trade risk
gate whose specification is *generated* by a frozen grammar, given **identically
and publicly to both arms**; difficulty comes from clause interaction and
precedence, not from a hidden artefact; defect mass is measured by exhaustive
enumeration of a ~3.1M-state space (63 s per submission, no sampling, no LLM
grader).

*Why it is the right answer to the leak specifically:* **there is nothing to
steal.** The spec is public to both arms by design, and the only hidden object
is an enumeration mechanically derived from that public spec. The reward
gradient does not point at the filesystem. Case03's judges scored it 5.0/5 on
oracle safety for exactly this reason, and case04 abandoned it for a design that
then failed on that axis.

**The hidden-object dilemma, and its resolution (B4).** Review round 1 found
that "nothing to steal" is not free: *something* is hidden, namely how clause
interaction and precedence resolve — which is the declared difficulty source. If
the public spec is prose, that resolution lives only in the hidden reference
semantics, and scoring an arm wrong on an ambiguous clause scores it against an
**undisclosed disambiguation** — the answer key in a new coat. If the spec is
formal enough to remove ambiguity, then both arms hold a formal specification and
**the treatment has leaked into the control**.

*Resolution adopted:* the spec ships as **prose with its precedence order stated
explicitly and exhaustively**, so no disambiguation is withheld, and difficulty
comes from **combinatorial interaction volume** rather than from ambiguity — many
fully-specified clauses whose composition is easy to get wrong and hard to check.
This is a real narrowing of the claim and must be stated as one: case 05 would
test whether formal expression helps on *specified-but-intricate* requirements,
not on *under-specified* ones. If a pilot shows that removing ambiguity also
removes the difficulty, the subject fails kill-criterion §8.3 and the design
stops.

*Carried forward honestly, from case03's own file:* a spec assembled by a
grammar from randomised clauses manufactures precisely the pedantic
clause-interaction difficulty formalisation is best at. If FCDD wins here, the
honest reading is "FCDD wins on machine-generated clause interactions", and that
belongs in the abstract, not the threats section.

**Option B — re-run the Z80 clone under the full L1–L4 stack. RETIRED (B3).**
It kept the question the operator asked in case01's ROADMAP §C (does Rocq → Rust
extraction change what defects are *possible*) and reused validated
infrastructure. It is retired because **no sandbox reaches a model's weights.**
The engine's fault locations and the tape are deposited in this lab's repository
and A11/A19 has now declared them public; the upstream `spectrum-gambit` web
wrapper has been a public GitHub repository throughout. For any model trained or
refreshed after that material was indexed, the reference semantics may already be
in the cell's cognition, and L1–L4 isolate the filesystem, not the training set.

*Correction to the review on one point of fact:* `fcdd-lab` is **private as of
2026-08-26** — the visibility flip has not been made — so the exposure today runs
through the upstream public repo rather than through ours. This does not save
Option B: the ruling to publish stands, and a design whose validity depends on a
repository never becoming public is not a design this lab should freeze.

*What would revive it:* a **new subject the model cannot have seen** — an engine
or reference implementation written after the pinned model's cutoff and never
published. That is a real option and a real cost, and it should be priced
separately rather than smuggled in as "the follow-on".

**Recommendation: A.** B is retired rather than deferred, and the extraction
question needs its own subject before it can be asked again.

---

## 6. Outcome design

- **Primary.** Silent-failure rate: submissions that pass the arm's own checks
  and the shared smoke set but diverge from the reference semantics on the
  enumerated state space. This is C2's requirement — the benchmark must be able
  to produce failures — and it is the claim FCDD is actually sold on.
- **Denominators are closed against the trivial win (M5).** A cell that refuses
  to ship, ships something that does not compile, or ships something failing the
  smoke set counts as **NOT-CORRECT (loud failure)** in the correctness outcome
  and stays in the denominator of the silent-failure rate. It is *not* an
  exclusion. Otherwise FCDD drives silent failure to zero by not shipping, which
  is the failure mode the co-primary was invented to catch.
- **Co-primary: REPLACED (B2).** case03's rule — H1 holds only if the treated
  arm's CORRECT rate is non-inferior within 10 points — is **unpowerable at any
  scale this lab has run.** Simulated (two-proportion NI, 10-point margin,
  one-sided α = 0.05, arms *genuinely equal* at 0.70), the power to
  *demonstrate* non-inferiority is:

  | n per arm | 5 | 13 | 28 | 56 | 130 | 260 |
  |---|---|---|---|---|---|---|
  | power | 0.24 | 0.16 | 0.23 | 0.31 | 0.54 | 0.80 |

  Case04 ran 13 cells in total and case02 ran 28 per arm, so the gate would have
  blocked H1 roughly four times in five **even when FCDD was perfectly fine** —
  the same structural floor case02 taught the lab to check before spending, now
  found on the other side of the ledger. Two fixes, and the choice is the
  operator's (**D2**):

  - **D2a — invert the burden.** Report the correctness difference with its
    interval, and let only *demonstrated inferiority* (the interval excluding
    the −10-point margin) block H1. Powered, honest, and weaker: it licenses
    "no evidence of harm", never "shown to be equivalent", and the abstract must
    say so.
  - **D2b — buy the sample.** At case04's ≈ $0.35 per cell, n = 260 per arm is
    roughly **$180 of tokens** — the binding constraint is wall-clock and memory
    (case04 hit OOM kills), not money, and PORTGUARD's 63 s enumeration scores
    520 submissions in about 9 core-hours. This is the first design in the
    programme where the honest answer to "underpowered" is *run more cells*.

  **Recommendation: D2b if the harness survives a pilot at n ≈ 30, D2a if it
  does not** — and whichever is chosen is frozen before the first scored cell.
- **Estimator.** A proportion, unit-free by construction (C4); dispersion, where
  reported, uses scale-free `sd(ln ·)`, never case02's `CV_log`. **Invariance
  tested under every transformation the units admit, before freezing.**
- **Power.** Exact simulation over the n_defects × k grid before the schedule is
  committed, by the method prototyped in `case03_silent_repair/prototype/
  power_case03.py` (currently untracked — commit it or restate the method
  in-line before citing it). Case02's floor lesson stands: a design whose best
  attainable *p* exceeds α cannot be run and called a test.
- **Informativeness gate, declared with a verdict attached — applied PER ARM
  (M3).** If *either* arm's CORRECT rate leaves [0.10, 0.90], the study is
  **UNINFORMATIVE — a benchmark failure, not a null on FCDD**. The pooled form
  drafted in r1 was gameable by asymmetry: an arm pinned at 0.05 against one at
  0.85 pools to 0.45 and reads "informative" while one arm is degenerate. The
  ceiling case02 hit was per-arm, so the gate must be too. Case02 discovered its ceiling in the
  post-mortem; case03 legislated for it in advance; case05 keeps that.
- **Fail direction.** Any load-bearing control found broken after the fact
  yields the conservative verdict, as case04 §6 did. This must stay written
  down *before* there is a result to be reluctant about.
- **Cost accounting, fixed before the first cell (case04 finding).** Two totals
  are recorded per cell and both are reported: **COMPLETING** (the last, clean,
  from-scratch session — the cost of one successful run) and **CONSUMED** (every
  attempt, including those killed by infrastructure). Case04's pre-registered
  metric reported only the first, and the choice moved its answer from *the
  formal arm is 0.88× the cost* to *1.33×*, because that arm discarded 62% of
  its tokens to killed attempts against the control's 42%. **Excluding
  infrastructure deaths silently prices away a method's failure rate**, which
  case01's A5 already ruled is method-inherent, not a config error. Neither
  total is the headline by default; the pre-registration must name which one is,
  and why, before any cell runs.
- **Resource ceiling is a first-class outcome (case04 finding).** Peak RSS and
  achievable concurrency are recorded per cell. Case04's driver carried a hard
  cap of one concurrent treated cell because Rocq/MetaRocq extraction peaks
  ~32 GB — the treated arm was **unparallelisable on a 61 GB host** while the
  control ran concurrently. No token or dollar metric in four cases could see
  that, and for a practitioner it is likely the binding constraint.
- **Stopping.** No optional stopping, no interim peeking, no outlier exclusion.
  Infrastructure deaths re-run at the same cell with the same tag and are logged.

---

## 7. Cost, and what it is actually spent on

Model spend is not the constraint. Case04's 13 cells cost roughly **$0.35 each**
on `deepseek-v4-pro` — about **$5 of tokens for the whole scored phase**, against
case02's $1,382 on a frontier model. The price of case 05 is **engineering**:
the bwrap cell harness, the oracle daemon and its socket protocol, the
commit-reveal corpus machinery, the six gates, and — for Option A — a grammar,
a reference semantics and an enumerator that do not yet exist.

**Corrected for the chosen option (M1).** Review round 1 caught a real
inconsistency in r1: L2 (oracle daemon, socket protocol, server-side cap) and L3
(commit-reveal) exist to serve the *hidden-function* shape, which only the
retired Option B has. PORTGUARD scores by post-hoc exhaustive enumeration with no
query oracle during the runs, so under Option A **L2 largely drops out and L3
becomes trivial** — there is no oracle to meter and no corpus to seal, only a
seed to withhold. The r1 estimate was pricing machinery the recommended study
would never use.

Rough shape for **Option A**, in agent-days: isolation stack (L1 + relay + G-ISO
closure hashing) ~2; gates ~1; subject — grammar, reference semantics, enumerator
~3–4; analysis + both power grids ~1; runs cheap (~$180 of tokens even at
n = 260/arm, wall-clock and memory being the real constraints); then **≥2
adversarial review rounds before believing anything** (C11). The oracle daemon
and commit-reveal are **not built** unless a future hidden-function subject
revives them.

---

## 8. Kill criteria — what would make this not worth running

Checked before freezing, not after:

1. **The probe cell escapes.** If L1 cannot be demonstrated airtight by the
   escape-attempt probe, stop. Everything else is decoration on a broken wall.
2. **The power grid says the design cannot reach α.** Case02's structural floor
   lesson, applied before the money is spent.
3. **The subject cannot produce silent failures in pilot.** If a pilot's
   CORRECT rate pins at 100% (case02) or the defect mass is degenerate, the
   benchmark is the finding and the study should not run.
4. **The circularity reading cannot be defended.** If, for Option A, we cannot
   state in advance what result would *not* be explained by "the grammar
   manufactures formalisation-shaped difficulty", the claim is unfalsifiable and
   should not be dressed as a test.

---

## 9. Sequencing recommendation

Run the **ATTACK-budget experiment first**, as the shakedown of this harness.

`method/ATTACK_BUDGET_DIAGNOSIS.md` is the lab's one actionable finding: the
beat's round count varies 18-fold, correlates *r* = +0.72 with cost, explains
~half of FCDD's cost variance, and — measured — changed no artefact. The
proposed fix (stop on coverage, budget convergence, hard stop at two rounds) is
a **single-arm, within-method A/B** on a method parameter. It needs no hidden
oracle, so it is nearly leak-proof by construction; it is cheap; it is
decidable; and it exercises L1, the runner, the ledger and the gates on a study
whose failure costs little.

**Corrected claim (review round 1).** r1 oversold this as a "harness shakedown".
It is not one: by its own description the ATTACK-budget study needs no hidden
oracle, so it exercises L1, the runner, the ledger and the mechanical gates but
**not** the relay under load, **not** L2, and **not** L3 — it validates the
layers that held last time and skips the ones that failed. Run it because it is
the lab's one actionable finding and it is cheap and decidable, **not** as
evidence that case 05's isolation works. That evidence only a case-05 pilot can
produce, and §8.1's escape probe is what produces it.

---

## 10. Review rounds

- **Round 1 (Fable, adversarial, 2026-08-26):** 4 blocking, 5 major, 5 minor.
  All 14 accepted; 2 changed the design, 1 retired an option, 1 was corrected on
  a point of fact. Record in §11. C11's "≥ 2 rounds" applies to the frozen
  pre-registration, not to this draft — a second round is owed before freeze.

## 11. Review round 1 — findings and disposition

Reviewer: Fable, adversarial charter, reading this proposal against case04's
REPORT/review ledger, both CONSTRAINTS files and case02's A17/A19.

| # | Finding | Disposition |
|---|---|---|
| **B1** | Not runnable: the agent needs network for its own model; `--unshare-net` forbids it, and the proposal never said where the agent loop runs | **Accepted, design changed.** Topology now declared: agent inside, model via a second orchestrator-held socket, with G-RELAY. Both horns of the alternative documented (§3-L1) |
| **B2** | The co-primary non-inferiority gate is unpowerable, so H1 can never be supported | **Accepted, design changed. Independently re-simulated** — power 0.16 at n = 13, 0.23 at 28, 0.54 at 130, 0.80 at 260. Gate replaced by fork D2a/D2b (§6) |
| **B3** | Option B's target is public, so the answer may be in the model's weights, which no sandbox reaches | **Accepted, option retired** (§5), with one factual correction: `fcdd-lab` is private today; the live exposure is the upstream public repo. The correction does not save B |
| **B4** | Option A's "nothing to steal" is false — the clause-interaction resolution is hidden; prose form withholds the disambiguation, formal form leaks the treatment into the control | **Accepted, resolved:** prose spec with precedence stated exhaustively; difficulty becomes interaction volume, not ambiguity. The claim narrows accordingly, and a pilot must show difficulty survives (§8.3) |
| **M1** | The L2/L3 machinery serves the retired Option B; the recommended study uses almost none of it | **Accepted**, §7 re-costed; L2/L3 not built unless a hidden-function subject returns |
| **M2** | The escape probe enumerates paths from case04's transcripts — the failure class §1 itself names | **Accepted**, probe rewritten as positive closure enumeration. (Reviewer credited G-ISO as the first content-based control in four cases) |
| **M3** | The informativeness band is pooled, hiding a degenerate arm | **Accepted**, applied per arm |
| **M4** | G-XSCRIPT and G-CLUSTER end in human adjudication — the judgement C1 forbids | **Accepted**, demoted from gates to deposited detectors the design does not rely on |
| **M5** | Silent-failure rate undefined for non-shipment, letting FCDD win by refusing to ship | **Accepted**, non-shipment and non-compilation defined as loud failure, kept in both denominators |
| **m1** | cargo/opam need network at build time | Accepted — dependencies vendored into the image |
| **m2** | The cited power script is untracked (C10) and powers only the difference test | Accepted — deposit it, and add the correctness grid |
| **m3** | A shared oracle daemon with state is a cross-cell channel | Accepted — daemon specified stateless per cell |
| **m4** | The copied-in toolchain image can smuggle sealed material | Accepted — image is a hashed G-ISO input |
| **m5** | Commit-reveal leaks if the seed's entropy is low | Accepted — entropy stated in the prereg |

**Reviewer's verdict on running it:** conditional; do not freeze as drafted; fix
B1–B4 in writing first. Recorded here rather than paraphrased, because the
lab's convention is that a review's verdict is deposited whether or not the
authors like it.
