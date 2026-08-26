# CASE 05 — proposal: testing the prevention claim under isolation that holds

**STATUS: DRAFT r6 — NOT CONVERGING; SEE §11 BEFORE READING FURTHER.**

r6 applies review round 4's coherence fixes and records its findings, but **does
not claim to repair the design.** Four rounds have returned 4, 4, 9 and 14
blocking-or-mismatch findings, every round's inside the previous round's repairs.
Round 4 refuted r5's central anti-circularity fix **by kernel execution**, and a
disposition audit found six places where a recorded fix was absent, stale, or
invalidated — including one applied everywhere except the line the finding cited.
**The recommendation r6 carries forward is to stop patching this subject** (§11).

Superseded status line: DRAFT r5 — not frozen, nothing scheduled, nothing built.** **r5 applies review round 3** — run as two reviewers with separate lenses (3A
science, 3B plan). They returned **nine blocking findings between them, every one
inside r4's own new material**, converging independently on two: the checksum
argument that justified retiring L3, and the replication mechanism orphaned when
the grammar was retired. One correction is to this document's own deposited
evidence: an r4 sentence claiming startpos depth 5 "detects neither fault" was
**false**, refuted by the table printed directly above it. Full record and
dispositions in §14. **r4 resolved D1** — the subject is now FIDE-legal move generation scored by
perft (§5), retiring both the Z80-clone and PORTGUARD options — adds the
mutation-calibration gate and the capability-window rule (C24, C25), makes model
tier an experimental factor (§6), and sets out the six-phase plan with its four
stop points (§10). r3 applied review round 2
(§14), which found four further blocking defects — all of them in the *repairs*
round 1 produced, exactly as this lab's history predicted. r2 applied round 1's
four blocking findings and thirteen others (§13). Two of them changed the design rather than its wording: the co-primary
gate was unpowerable at any scale this lab has run (B2, independently
re-simulated), and Option B is retired (B3). Freezing is
the operator's act. **D1 is resolved (§5); the §8 kill criteria — including the
new criterion 6, which §11's own conclusion implies — must be checked against
reality before any freeze.** This document exists
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
- **it will read its sibling cells' workspaces** — their sources, their
  extracted output, even their compiled binaries — if any path reaches them.
  This is not hypothetical: case04's A-2026-08-26b proved every armA cell did
  it, and two submissions came out byte-identical as a result;
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
      --bind  $ORACLE_SOCK /work/.oracle.sock \   # Option B only (m2)
      --bind  $RELAY_SOCK  /work/.model.sock  \   # per-cell, always (B3)
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
gate — **but only the half of it that is mechanical (B3)**. **G-RELAY** is a
full traffic log plus **per-cell byte accounting against a pre-registered
threshold**, which is countable and therefore a gate; **per-cell relay sockets
and tokens** make that accounting attributable. *Oracle-shaped-query detection
is demoted to a deposited descriptive detector*: deciding whether free text
paraphrases a query is a judgement or a blocklist, which are the two things this
design has already refused elsewhere and §3-L2's "only through a UNIX socket" is stated as *two*
sockets, both orchestrator-held and both logged.

*Verified on this host, 2026-08-26:* a cell under `--unshare-all` reached an
orchestrator-held oracle over a bind-mounted socket (`ANSWER(query='legal --fen
startpos', served-by-orchestrator)`) while `urllib` to a public API raised
`URLError`, `/media/sf_Projects` and `/home` were absent, and `/proc` showed only
sandbox-local processes. Practical constraint found in the same test: `AF_UNIX`
caps socket paths at 108 bytes, so cell roots must be short.

**Image immutability (M3).** `/usr`, `/lib` and `/bin` are bound from the live
host, so the "hashed image" is whatever the host is at probe time; a system
update during a long schedule would silently change the toolchain mid-run and
stop cells being exchangeable. Either an immutable snapshot is bound, or the
closure hash is re-checked **per cell at start** against the frozen manifest,
with mismatch aborting as infrastructure. (`/etc/alternatives` without `/etc`
also breaks common toolchain lookups; the pilot must confirm the bind set.)

**No chess reference inside the cell (r5 — 3A M3, 3B M1).** This host carries
python-chess at `~/.local/lib/python3.14/site-packages/chess` and stockfish at
`~/bin/stockfish` — in the very home directory §3-L1 vendors toolchains from. If
either reaches the image, **G-ISO blesses it** (it is in the manifest), both arms
self-test against the scoring oracle, silent failures vanish, and G2 reports a
false *empty capability window* — a wrong **kill verdict**, which is worse than a
wrong run. A freeze-time **image-content check** — no chess movegen library,
engine, perft tool or vendored chess crate in the manifest — is deposited as part
of G1's evidence.

**Memorisation is a named, unclosable threat.** Chess movegen is
training-saturated: mature Rust movegen crates are the in-weights answer for the
control's deliverable, and **ChessRocq — a public Rocq chess development this
programme's own report cites — is a treatment-side channel no gate detects.**
Round 1's B3 retired the Z80 subject for exactly this reason and the principle
applies here with more force, not less. The scope statement goes in the abstract:
*FCDD on a formalisation-friendly, training-saturated domain*, with a
pre-registered memorisation reading.

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

> **r5 note — L2 stays retired; L3 IS REINSTATED.** r4 retired both on the claim
> that a checksum oracle's leak conveys no solution. **Round 3 refuted that on two
> counts and r5 accepts both.** First, a leaked *suite* is actionable without
> inverting any count: knowing which positions you diverge on, an agent computes
> divide-perft itself and bisects to the offending move — the standard
> perft-debugging loop, which converges by iteration rather than understanding.
> Second, §5.3's adjudication set leaks as labelled `(fen, history) → verdict`
> pairs, which **are** answers, transcribable exactly as `engine.inc`'s tables
> were in case 04. **The "load-bearing wall to belt" demotion of L1 is withdrawn**,
> and a suite leak remains fatal under fail-direction. L2's retirement stands:
> there is genuinely no per-cell query oracle to meter.
>
> Superseded r4 reasoning, kept for the record: the arms are
> given the FIDE rules and a small public smoke set, and the scored suite is
> simply withheld. L1 (namespace absence) and the relay remain load-bearing, for
> the ordinary reason that cells must not read each other (C23). The two
> subsections below are retained as the design to reinstate **if** a future
> subject reintroduces a hidden-function target — they should not be built for
> this one.

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
| G-ISO closure hash | any file in the cell's reachable closure not in `image manifest ∪ /work ∪ {/proc,/dev,/tmp}` — symlinks resolved, mounts enumerated, **sibling trees proved absent**; the `/work` delta is deposited as the submission's provenance record (M2) | material the cell never wrote down |
| G-NET no-egress probe | a network path out of the sandbox | an out-of-band channel through the socket |
| G-XSCRIPT constant match | submissions containing byte-equal runs of engine constants (case04 F3's check, promoted from a review finding to an automatic gate) | a paraphrased transcription |
| G-CLUSTER cross-arm identity | submissions whose behaviour is mutually identical across arms (case04 F4) | genuine convergence on an easy target |
| G-DEPOSIT manifest hash | sealed content deposited anywhere in the repository, by any path (A11/A19) | content leaked outside git |

**A cell failing G-ISO, G-NET or G-RELAY is excluded before scoring and
reported as excluded** — **G-CAP is struck in r5 (3B B5)**: it read the retired
L2 daemon's query-cap log, which does not exist under this subject, and an
uncomputable gate on the operative checklist either excludes every cell under the
inherited rule or gets silently skipped, which is worse. **C20** (cap enforced
where the engine runs) is struck with it, and **C22**'s manifest is restated as
*the withheld suite and its references* rather than a sealed corpus that no longer
exists — mechanically, no judgement. **G-XSCRIPT and G-CLUSTER
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

## 4. New constraints, C17–C25

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
- **C20 — STRUCK (r5, applied r6).** The query cap belonged to the retired L2
  oracle daemon; under this subject there is no per-cell query oracle to meter.
- **C21 — the scored corpus is generated after the last cell closes**, from a
  seed committed by hash in the pre-registration and held off-host.
- **C23 — cells share no writable mount and no host path (A-2026-08-26b).**
  Each `$CELL_WS` is freshly created, disjoint and non-nested; no scored root,
  ledger directory or raw-output directory is mounted into more than one cell;
  the orchestrator collects results *after* the namespace closes, never through
  a path the cell can also see. Sibling absence is one of the properties the
  G-ISO closure walk exists to prove, and is asserted as such. An
  infrastructure re-run rebuilds the workspace from the image; it never reuses
  the dead cell's tree.
- **C24 — the scoring instrument is mutation-calibrated before freeze, and this
  is a hard gate.** Inject each fault class into a correct reference and require
  the chosen position suite and depth to catch **every one**. **r5 widens the
  mutant set on both reviewers' insistence, because r4's evidence base could not
  reach the classes that matter.** The deposited demo injects faults by filtering
  a reference's *legal-move list*, which structurally cannot express **inclusion**
  faults — castling through check permitted, pinned pieces moved, en passant into
  check — the very classes §5.2 calls the hard ones; a **mutable** reference is
  required. It also cannot express **mis-specification** faults, and those are the
  delivered-treatment arm's characteristic silent failure: *a sound and complete
  proof against a mis-formalised `legal` ships a provably-conformant wrong
  program.* **That is the failure mode the whole prevention claim turns on**, so
  the mutant set must include spec-side mutants (see the delivery gate, §6) and
  the fault taxonomy is derived from an external FIDE clause list — at least one
  mutant per clause, movegen **and** adjudication — pre-registered before the
  suite is built, with a named author, and evaluated by a deposited script whose
  predicate is *all mutants caught* **and** *two independent references agree on
  every value* (python-chess × stockfish, both present on this host). If the
  instrument cannot detect an injected silent failure, the study cannot detect a
  real one and **must not run**. This is the method's own bridge/mutation layer
  turned on the experiment's own instrument — the same move that found a real
  property gap in `method/pipeline_proto` (a boundary mutation that survived
  witnesses, theorem mirrors and a 1,200-case sweep).
- **C25 — difficulty and capability are calibrated, never assumed.** Both the
  benchmark's silent-failure rate *and* the tier's ability to deliver the
  treatment are measured in a pilot, per model tier, before the schedule is
  frozen (§6). Case 02 discovered its 100%-in-both-arms ceiling after 56 runs;
  case 05 declares the measurement in advance and is willing to stop.
- **C22 — the deposit is audited like a workspace**: every tracked file hashed
  against the sealed manifest before publication, and on every subsequent
  push. The check case03 C1 already specified, pointed at the repository.

---

## 5. The subject (D1 — RESOLVED in r4)

Both r1 options are retired. **The target is FIDE-legal move generation and game
adjudication; the oracle is perft.**

Each arm ships a crate exposing `legal(fen)`, `status(fen, history)`. Correctness
is defined by the **FIDE rules**, not by any implementation's behaviour, and
scoring is the exact node count at depth *n* (`perft`), computed
orchestrator-side and compared for equality, with **divide-perft** per root move
for localisation.

### 5.1 Why this and not the two retired options

**Case 04 asked for "whatever this particular Z80 engine plays".** That is a
target defined by an *artefact*, not by a property, and three consequences
followed. Nothing was statable, so the treated arm's distinctive capability —
proving things — had no purchase. The task was *learn-a-hidden-function*, so the
reward gradient pointed straight at the filesystem. And the best score in the
study was obtained by **transcribing leaked constants**, because with an artefact
target, copying the artefact *is* the optimal strategy.

Against a specification target, all three invert:

- **Correctness is statable.** Soundness (`m ∈ genLegal p → legal p m`),
  completeness (the converse) and terminal correctness are theorems. The treated
  arm can prove them and thereby retire rules-layer testing — which is precisely
  the differential this experiment exists to measure and which case 04 made
  unmeasurable by construction.
- **The oracle is harder to transcribe than an engine — but NOT useless if
  leaked, and r4's claim that it was has been withdrawn (round 3; see the §3 r5
  note).** A perft *count* cannot be inverted into an implementation. That is
  where the property stops: a leaked *suite* is still actionable, because an agent
  can compute divide-perft itself and bisect to the offending move — convergence
  by iteration, without understanding — and §5.3's adjudication set leaks as
  labelled `(fen, history) → verdict` pairs, which **are** answers. So the subject
  removes the *transcribe-the-artefact* strategy that dominated case 04, and it
  does **not** remove the need for isolation. **L1 remains load-bearing and a suite
  leak remains fatal under fail-direction.**
- **No circularity.** FIDE is canonical, public, and **not authored by us**.
  Case 03 named this risk against its own PORTGUARD design — a grammar
  manufactures exactly the clause-interaction difficulty formalisation is best
  at. An external standard cannot be accused of it.
- **The spec-form dilemma is NARROWED, not dissolved (r5, round 3A B2).** r4
  claimed FIDE is "complete for this purpose". **It is not, at the adjudication
  layer.** A pure `status(fen, history)` does not exist in the rules: threefold
  and fifty-move are **claim-based** while fivefold and 75-move are automatic
  (with a mate-precedence exception), so the function needs a stipulated claims
  model; "insufficient material" as every implementation ships it is the material
  shortcut, not FIDE's dead-position rule — the installed reference's own
  docstring concedes "the converse does not necessarily hold"; and whether the
  en-passant square enters the repetition key is an interpretive choice the
  reference makes one particular way. Scoring against an implementation would
  therefore make correctness *operationally an artefact's behaviour again* —
  the very defect this subject was chosen to escape.

  **Fix adopted:** a **pinned interpretation addendum** ships as part of the
  shared spec — claims model, the material-shortcut-or-drop decision for dead
  positions, the repetition key, and the input domain — published identically to
  both arms. The honest consequence, and it goes in the abstract: the treatment
  is *formalising FIDE **plus a lab-authored disambiguation***, so round 2's
  narrowed-claim language is reopened rather than retired.

### 5.2 Silent failure is native to this domain, and we measured it

Movegen faults are depth-latent by nature. Measured with `python-chess` as
reference (`tools/latency_demo.py`, deposited):

| position / depth | correct | en passant omitted | castling omitted |
|---|---:|---:|---:|
| startpos d4 | 197,281 | **197,281** (invisible) | **197,281** (invisible) |
| startpos d5 | 4,865,609 | 4,865,351 (−258, 0.005%) | **4,865,609** (invisible) |
| Kiwipete d1 | 48 | 48 (invisible) | **46 (−2, caught)** |
| Kiwipete d3 | 97,862 | 97,766 (−96, caught) | **86,677 (−11%, caught)** |

An implementation **missing an entire chess rule** passes every check through
depth 4 from the start position, and a missing castling rule is invisible there
at any depth reachable in reasonable time. This is the fault class whose symptom
and cause separate — C2 satisfied by the domain rather than by construction.

**The finding that sets the design — corrected in r5 (round 3A, M1).** An r4
version of this sentence claimed startpos at depth 5 "detects neither fault".
**That is false and the table above refutes it**: d5 catches the en-passant
omission (−258). What the evidence actually supports is narrower and still
decisive: **startpos d4 detects neither fault; depth flips en passant from
invisible to visible; and no reachable depth from startpos ever reveals the
castling omission, which Kiwipete exposes at depth 1 in forty-eight nodes.**
Depth helps for some fault classes and cannot help for others; position
selection is what makes a rule reachable at all. The scored suite must therefore be
stratified so that every rule is *immediately reachable* in some position:
castling both sides, castling through check, en passant, **en passant where the
capture exposes a horizontal pin**, promotion and underpromotion, pinned-piece
pseudo-legality.

### 5.3 Widen past movegen to what perft cannot see

Perft counts the movegen tree; it never touches adjudication. The requirement
therefore includes **threefold repetition, the fifty-move rule, insufficient
material**, and their interactions — mate on the hundredth half-move outranking
the draw claim, K+B vs K+B on same-coloured squares. These are fully
FIDE-specified, require game history rather than a position, and are where real
engines actually fail; case 04's own subject engine has documented divergences
there. They are scored by adjudication verdict on generated game histories, not
by perft.

### 5.4 What is dropped

The engine-clone / policy layer, entirely. It was never provable, it was the leak
vector, and it is the half of case 04 that could not have been won by any method.

## 6. Outcome design

- **Primary (concrete under D1; categories corrected in r5, round 3A M5).**
  Classification uses **orchestrator-observable facts only** — ships, compiles,
  passes the shared public smoke set, agrees with the withheld suite. "Passes the
  arm's own tests" is demoted to a deposited descriptive field, because it was
  arm-controlled and left a hole in the partition: a cell shipping no tests passes
  vacuously, and one shipping a deliberately failing test made its own divergent
  submission unclassifiable. **Silent failure** = a submission that passes
  the shared public smoke set, yet diverges from
  reference perft at depth ≥ 4 on the withheld suite, or returns a wrong
  adjudication verdict on a withheld game history. Scoring is exact-match on
  counts with divide-perft for localisation — a 258-node divergence in 4,865,609
  is invisible to anything approximate. **Loud failure** = fails the smoke set,
  fails to compile, or does not ship. This is C2's requirement — the benchmark must be able
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

  **Round 2 found neither horn sound as written (B2), and r3 replaces both.**
  *D2a* does not bind: silent-failure rate is silent/N, so a non-shipping cell
  still lowers the primary even with M5's denominator fix — the co-primary gate
  was the actual control on the refuse-to-ship strategy, and inverting the
  burden defangs it. At n = 30/arm an *observed* 30-point correctness harm still
  yields an interval containing the −10-point margin, so the block essentially
  cannot fire below n ≈ 130. *D2b*'s arithmetic used the COMPLETING average
  ($0.35/cell) — the accounting this same section rules against; on CONSUMED it
  is $0.69/cell, about **$360** at 520 cells, still trivial. The binding cost is
  wall-clock: case04's 13 cells took **~16 hours** with the treated arm capped at
  one concurrent cell, so 260 serial treated cells is plausibly **weeks**, against
  a programme record that already contains a nine-day host reboot and an 88.6-hour
  usage suspension (C6).

  **Adopted instead: one ordinal outcome, tested once.** Each submission is
  scored CORRECT ≻ LOUD-FAILURE ≻ SILENT-FAILURE, and the arms are compared on
  that ordering with a single pre-registered test. A method that converts silent
  failures into loud ones moves *up* the order; one that converts working
  programs into broken ones moves *down*; refusing to ship is a LOUD failure and
  cannot win. One powered test then carries both directions, and the
  unpowerable two-proportion gate disappears rather than being weakened.
  **The n and the schedule are pilot-measured freeze inputs** — per-cell
  wall-clock, peak RSS and CONSUMED cost — not assumed.
- **Estimator.** A proportion, unit-free by construction (C4); dispersion, where
  reported, uses scale-free `sd(ln ·)`, never case02's `CV_log`. **Invariance
  tested under every transformation the units admit, before freezing.**
- **The obligation asymmetry is named, and balanced (r5 — round 3A M7).** r4's
  mandated-proof treatment is a *third* variant: cases 01/02 measured arms
  stopping at the **same** gate, whereas here the treated arm must produce
  machine-checked correctness evidence while the control owes nothing beyond the
  public smoke set. A treated win would then measure the *obligation* as much as
  the method, and continuity with the 2–5× cost figures does not carry, since no
  prior arm ever delivered non-vacuous quantified proofs. **The control receives
  a registered comparable obligation** — a mutation-scored test suite meeting a
  declared kill rate — so both arms owe evidence of comparable weight; if the
  operator prefers the unbalanced design, the contrast is pre-registered in the
  abstract as *machine-checked obligation vs none*.
- **Model tier is an experimental FACTOR, not a setting.** The same two-arm
  experiment runs at 2–3 tiers (arms model-matched *within* tier, C3 intact).
  This is what converts the "the task may be too easy" risk from a threat into a
  measured dimension, and it makes even a null informative: *does the method's
  benefit grow as capability falls?* — which is the question a practitioner
  deciding whether to spend 2–5× on a cheap model actually has.

  **The lever is weaker than it looks, and the one piece of in-lab evidence is
  discouraging.** Case 04's flash sweep against its pro arm: mean μ₂ **0.197 vs
  0.184** — essentially identical — with sd **0.269 vs 0.086**. The smaller model
  was not systematically worse, it was **three times more variable**, and its best
  cell (μ₂ = 0.000) was the transcription of leaked constants, not competence.
  Difficulty arriving as variance rather than as a shifted mean makes a benchmark
  *noisier*, not more discriminating. (n = 3, voided study — weak evidence, but
  it is the only evidence there is.) **Power is therefore computed from each
  tier's own observed variance**, never from the strongest tier's.

  **D3 — no specialist prover model. Operator ruling, 2026-08-26: excluded.**
  A dedicated theorem-proving model (Kimina-class) would dissolve the window
  tension below by pairing a weak coding model with a strong prover. **It is
  ruled out of this design and any successor**, for three reasons worth recording
  because they are not all obvious:

  1. **It breaks arm model-matching (C3)** — the constraint case 02 violated by
     accident (A13, a second model inside 51 of 56 cells) and paid for in the
     contamination of its own premium.
  2. **It changes the treatment** away from what cases 01/02 measured — the
     method as the skill defines it, not the method plus a specialist toolchain —
     and it would import an unvalidated capability, since strength on competition
     mathematics is not evidence of strength on inductive proofs about
     list-returning move generators.
  3. **It would engineer away the measurement.** The capability window is a
     *finding*, not an obstacle: whether a given tier can deliver the treatment is
     precisely what a practitioner needs to know before spending 2–5× on it.
     Bringing in a prover to make the treated arm able to deliver would hide the
     answer rather than produce it.

  **Consequence, stated rather than hidden:** with this lever removed there is no
  way to open the window if it turns out to be empty, so **G2 becomes more likely
  to stop the programme** — which is consistent with §11's standing
  recommendation, and cheap, since G2 is early by design.

  **The binding constraint is a capability window, and it may be empty.** The
  benchmark needs a model weak enough to fail; the treatment needs one strong
  enough to write Rocq *and prove soundness and completeness non-vacuously*. The
  evidence on the second gate is bad: **deepseek-v4-pro wrote zero quantified
  properties across ~4,500 lines when proofs were optional.** Making them
  mandatory changes the incentive, but a weaker model is less likely to clear the
  bar, not more — and formalising is plausibly harder than coding, so scaling down
  may handicap the treated arm specifically (a confound running *against* FCDD,
  unlike case 02's and case 04's, which both ran toward it). **If no tier is
  simultaneously weak enough to fail and strong enough to formalise, that is the
  finding**, and a publishable one: the method's prevention benefit would be
  unmeasurable at this task because it demands more capability than the regime
  where it would help.
- **Replication (r5 — round 2's fix was ORPHANED by r4 and is rebuilt).** Round 2
  made replicates independent by having a grammar emit a distinct spec instance
  per cell. **r4 retired the grammar with Option A and left that sentence
  standing**, so under a fixed FIDE spec every cell in an arm×tier received an
  identical workspace, prompt and pinned model — precisely the sampler-noise
  degeneracy round 2 named, and the condition that produced case 04's
  byte-identical submissions. Both round-3 reviewers caught it independently.

  **r5's replacement, stated honestly rather than papered over:** with one fixed
  specification there is no spec-instance dimension, so the unit of replication
  is the **sampler** — a registered variation dimension (seed and prompt frame),
  with the claim explicitly narrowed to *this one specification*. **Power is
  computed from sampler-noise variance measured in Phase 2**, never assumed iid,
  and the per-cell scored-suite instances are drawn from disjoint generator seeds
  so cells do not share a test set.
- **Tier multiplicity (r5 — round 3A M4).** With 2–3 admissible tiers the primary
  is either run per tier (2–3 primary tests, needing an α allocation) or pooled;
  and the question the factor is sold on — *does the benefit grow as capability
  falls?* — is an **interaction**, which nothing currently powers. The
  pre-registration picks exactly one: a named primary tier, a declared α-split, or
  the interaction as primary with its own power computation.
- **Multiplicity (m4).** r3 now carries a primary, cost (two totals), resource
  ceiling and a delivery criterion. The pre-registration names the primary and
  takes case02 §5.5's disclose-and-discount position on the rest, before the
  outcomes multiply further.
- **Power — r6: this section named two incompatible methods.** "Exact simulation
  over the n_defects × k grid" is the retired seeded-defect design's method; the
  live source is **Phase-2 sampler-noise variance** (see Replication above), and
  that is what the pre-registration uses. The `power_case03.py` reference below
  remains **uncommitted three revisions after its disposition claimed otherwise**,
  so under C10 it cannot be cited until deposited. Superseded text: exact
  simulation over the n_defects × k grid before the schedule is
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
- **The delivery gate must resist CIRCULARITY (r5 — round 3A B4), or it is
  case 04's vacuous pass one level up.** A treated cell that defines
  `legal p m := m ∈ genLegal p` earns soundness *and* completeness by
  `reflexivity`: universally quantified, machine-checked, witness-bearing,
  clause-vocabulary-covering — **every criterion below passes while nothing is
  proved.** Deciding by inspection whether a declarative spec is independent of
  the generator is a judgement, which C1 forbids as a control. **r5's fix is REFUTED BY EXECUTION (round 4A, B1) and does not stand.** A
  reviewer compiled the counterexample in Rocq: for `legal p m := In m (genLegal
  p)`, soundness and completeness both discharge by `exact H`, and *every*
  semantic spec mutant breaks at least one proof — so the predicate "injected spec
  mutants must break the proofs" is **maximally satisfied by the circular spec**,
  a spec identical to its generator being the most mutation-sensitive spec
  possible. r5's sentence "a specification the proofs cannot lose against is
  circular by construction" asserted a **false converse**. The freeze-ordering half
  fails too: it names no verifying mechanism and cannot order cognition, since a
  cell may design the generator in context and transcribe it as the spec. The
  consequence is worse than a missed gate — a circular cell reads as *treatment
  delivered*, so G2 would call a tier admissible where the treatment is in fact
  undeliverable, which is the wrong-kill-verdict class.

  **The only candidate fix that is a program rather than an opinion** is
  **lab-frozen theorem statements**: cells prove against statements the lab
  authors and freezes, which also gives the interpretation addendum the author,
  freeze point and amendment rule it currently lacks. It renames the treatment,
  and §11 already half-concedes that rename.
- **Treatment delivery is verified, not assumed (B4) — the gate this programme
  most obviously lacked.** Case04's treated arm wrote **zero quantified
  properties across ~4,500 lines of Rocq**, and its "zero `Admitted`" conformance
  check passed *vacuously* because there was nothing to admit: the treatment had
  degenerated into "write a functional program in a prover's syntax", and the
  design would have scored that as FCDD. Case05 pre-registers a **mechanical
  delivery criterion** — at least *k* universally quantified, machine-checked,
  **non-vacuous** properties (each with a witness), covering a stated fraction of
  the spec's clause vocabulary — and pre-registers the analysis of
  non-delivery **before the first cell**: an intention-to-treat comparison plus a
  declared per-protocol one, with *treatment-not-delivered* as a named outcome
  category. It is never a post-hoc exclusion, because excluding cells
  differentially by arm is a selection confound.
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
  and why, before any cell runs. **"Infrastructure death" gets a mechanical
  classifier (M5)**, because whoever classifies deaths post-hoc chooses which
  tokens count: OOM-killer log, API 5xx, host reboot ⇒ infrastructure; agent
  gave-up, budget exhausted, non-compiling exit ⇒ method-attributed; anything
  unclassifiable ⇒ **method-attributed by default**, per fail-direction. And
  COMPLETING is defined for resume-completed cells or resumes are forbidden —
  case04's runner could resume a dead session in place, and though 0 of its 13
  completing sessions turned out to be resumed, the metric was undefined for a
  case that nearly occurred.
- **Cache contamination caveat (m5).** The relay proxy and the model provider
  are cross-cell shared state: provider-side prompt caching (case04 logged 188M
  cache-read tokens) means one cell's context can change another's cost and
  latency. No content crosses, so this threatens the *cost* outcome only; the
  pre-registration either pins cache behaviour or states the caveat on every
  per-cell cost figure.
- **Resource ceiling is a first-class outcome (case04 finding).** Peak RSS is
  read from the cell unit's cgroup `memory.peak`, not by polling `/proc`, which
  misses spikes; "achievable concurrency" is defined as a host-schedule property
  measured in the pilot, and RSS compared across arms run at different
  concurrency is flagged as contention-confounded (m3). Peak RSS and
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

> **r6 — this section priced a retired design for three revisions.** Round 1's
> M1 disposition claimed §7 was "re-costed"; it was not. What follows was written
> for Option A (a grammar, a reference semantics, an enumerator), quotes the
> COMPLETING per-cell figure that §6 itself later ruled against ($0.35 rather than
> $0.69 CONSUMED), and states that commit-reveal is "not built" — which r5
> reinstated and Phase 0 now builds. **The live cost estimate is §10's "What this
> costs"; the text below is retained only as the record of what was claimed.**

**Superseded (r1-M1 disposition, never executed).** Review round 1 caught a real
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
3. **The instrument cannot see an injected silent failure (C24).** If the
   mutation calibration fails to catch every injected fault class at the chosen
   suite and depth, stop — a study that cannot detect the outcome it names is
   not a study.
4. **No model tier clears both gates (C25).** If every tier is either too strong
   to fail or too weak to deliver the treatment, stop and report the empty
   capability window. It is a real result about where the method can apply.
5. **The circularity reading cannot be defended.** Restated in r6 for the live
   subject: the grammar this criterion used to name was retired in r4. The live
   circularity threat is the **circular-spec bypass** — a treated cell defining
   `legal p m := m ∈ genLegal p` and proving it by `reflexivity` — and the design
   must be able to state in advance what result would *not* be explained by
   "the treated arm proved its generator against itself". §6's spec-freeze and
   spec-side mutation are the mechanism; if they cannot be made to work, stop.
6. **The domain cannot exhibit the failure mode the claim is about (r6).** §11
   concludes that the prevention claim turns on **mis-specification** and that
   chess movegen is a domain where that is least likely to occur and least likely
   to matter. Round 4 was right that stating this as an essay while omitting it
   from the kill list is the shape of a hedge: a criterion that would fire *now,
   at design time, at zero cost* was the one criterion not written. **It is now
   written.** Before freeze, the design must demonstrate — not assert — that a
   plausible mis-formalisation of the shared spec is (a) reachable by a competent
   arm and (b) detectable by the instrument. If it cannot, the subject fails and
   must be re-derived from the mis-specification requirement.

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
oracle, so it exercises L1, the runner, the ledger, the mechanical gates **and — contrary
to what r2 said here (m1) — the relay under load, since with the agent inside the
sandbox every model call of every cell traverses it**; it does not exercise
**L2** or **L3** — it validates the
layers that held last time and skips the ones that failed. Run it because it is
the lab's one actionable finding and it is cheap and decidable, **not** as
evidence that case 05's isolation works. That evidence only a case-05 pilot can
produce, and §8.1's escape probe is what produces it.

---

## 10. The plan

Six phases. Every phase ends in a gate that can stop the programme, and no
phase begins before its predecessor's gate is green. Nothing after Phase 0 is
authorised by this document — freezing is the operator's act.

### Phase 0 — build the instrument (no arms, no models)  ≈ 1–2 agent-days
Reference perft and adjudication via `python-chess`, orchestrator-side only.
Position suite stratified by rule-reachability (§5.2): castling both sides,
castling through check, en passant, **ep exposing a horizontal pin**, promotion
and underpromotion, pinned-piece pseudo-legality; plus generated game histories
for repetition / fifty-move / insufficient material. Published positions
(Kiwipete, CPW 3–6) go in the **public smoke set only**; the scored suite is
generated with computed references, to defeat memorisation.
**Custody, reconciled (r5 — 3B B1).** r4's Phase 0 generated the scored suite up
front, which breached C21 ("generated after the last cell closes") on day one,
while G0 structurally needs *a* suite to calibrate against. The resolution keeps
both: **Phase 0 calibrates the generator on a throwaway instance**; the scored
instance is generated **after the last cell closes** from a committed seed held
off-host (C21 intact), and G0's calibration is **re-run on the generated
instance** before scoring. Nothing sealed sits on the cells' host during Phase 4.

**Gate G0 — C24 mutation calibration.** Inject every known fault class into a
correct reference; the suite must catch **all** of them. A miss means the
instrument is blind: fix it or stop.

### Phase 1 — the cell harness  ≈ 2 agent-days
`bwrap` cell (verified on this host: oracle reachable over a bound UNIX socket,
network blocked, lab tree and `$HOME` absent, `/proc` sandbox-local), the model
relay with per-cell sockets and byte accounting (B3), **disjoint per-cell
workspaces (C23)**, the positive-closure probe (M2), immutable image or per-cell
start-time closure re-check (M3), vendored toolchain (m1).
**Gate G1 — stated as a predicate, not as absence of evidence (r5 — 3B).** Pass
requires: the positive-closure walk diffs **empty** against
`manifest ∪ /work ∪ {/proc,/dev,/tmp}`; the egress probe fails to reach the
network; the **image-content check** finds no chess library, engine or perft tool;
and — the channel that actually fired last time — a **two-cell concurrent probe**:
cell 1 writes a nonce, cell 2's closure walk must not reach it and must fail to
use cell 1's relay socket and token (C23, A-2026-08-26b). Transcript and closure
hash deposited. A failure distinguishes *fix the bind and re-probe* from *stop*.

### Phase 2 — capability calibration  ≈ 1 day + cheap runs
k per arm per tier — **r5 stated "k = 3" here and "likely 10–20" ten lines below,
and r6 does not paper over it: the binomial rule sets k, the schedule must absorb
it (10–20 × 2 arms × 2–3 tiers = 40–120 cells, treated serial at >6 h each), and
Phase 2's "≈ 1 day" is therefore false by an order of magnitude** — across 2–3 tiers (a frontier tier, a mid tier such as
Sonnet, a small tier such as deepseek-flash). Excluded from inference, as case
04's calibration was.
**Gate G2 — the dual rule (C25), now with a decision rule (r5 — 3B B4, 3A M6).**
r4 stated an admissibility condition and no way to evaluate it, and **k = 3 could
not have supported one**: under the literal reading a genuinely centred tier
(true rate 0.5) is falsely excluded 25% of the time and a near-ceiling tier (0.92)
admitted ~22%, while "n from each tier's observed variance" is arithmetic on two
degrees of freedom. This lab treated an unpowerable gate as blocking in round 1;
the same standard applies here. **r5 states G2 as an exact binomial rule with
declared false-exclusion and false-admission rates, and sets k to whatever that
implies — likely 10–20 per arm per tier — pricing the schedule consequence, or
runs G2 sequentially under a pre-registered escalation rule.** The **delivery
criterion's numbers are fixed in Phase 0/1**, before any Phase-2 cell runs, since
G2(b) cannot evaluate a criterion frozen a phase later (3B M7). A tier is
admissible only if (a) its rate clears the band under that rule, **and** (b) the
treated arm ships non-vacuous soundness and completeness proofs. Tiers failing
(b) are recorded as *treatment not deliverable at this capability* — an outcome,
not an exclusion. **If no tier clears both, stop** (§8.4).

### Phase 3 — freeze  ≈ 1 day
Pre-registration completed and committed: the admissible tiers, n per cell
computed **from each tier's own observed variance**, the ordinal outcome
(CORRECT ≻ LOUD ≻ SILENT) with its single test, the delivery criterion and its
ITT/per-protocol pair, the mechanical infrastructure-death classifier (M5), the
dual COMPLETING/CONSUMED cost accounting, peak-RSS via cgroup `memory.peak`, the
multiplicity position, and the analysis script **dry-run against a real Phase-2
cell** (C5). The committing commit is the pre-registration mark.
**Gate G3 — a second adversarial review round on the frozen text** (C11), which
this programme has now twice seen catch blocking defects that its own authors
introduced while fixing earlier ones.

### Phase 4 — run  ≈ cheap in tokens, days–weeks in wall-clock
Randomised schedule under a committed seed. Integrity gates (G-ISO, G-NET,
G-RELAY — **G-CAP struck in r5, and this line is where r5 failed to strike it;
corrected in r6**) computed **before** any score is joined; failures excluded
mechanically and reported. Schedule discontinuities logged automatically (C6).

**Scoring runs untrusted code, and is sandboxed too (r5 — 3B M2).** A submitted
crate's `build.rs` executes arbitrary code **at compile time in the
orchestrator's namespace**, where the withheld suite and its references live; a
submission can also hang perft or exhaust host memory. Case 04 scored 13 binaries;
case 05 scores hundreds. **Every submission is built and scored under the same
bwrap profile as a cell**, with a per-position timeout, a memory cap, and a
declared verdict for hung or crashed scoring runs.

**Declared before Phase 4 (r5 — 3B M5, M6, M8, m5).** Per-cell **timeout and
attempt cap** (case 04 used 6 h × 3, and the treated arm still averaged 3.0
restarts) and a **hung-cell policy** — without them "does not ship" has no
meaning. A **wall-clock ceiling** computed from Phase 2's measured per-cell time ×
the Phase-3 n, as a **freeze-blocking criterion**: case 04's 13 *no-proof* cells
took ~16 h with the treated arm capped at one concurrent cell at 32 GB peak, and
r5 demands strictly more per cell. The **concurrency-aware scheduling rule**, with
its confound stated: serialised treated cells make schedule position correlate
with arm. Plus who runs the arms, what the operator is blind to, and the retention
and deposit rule for relay traffic logs.

### Phase 5 — analyse and review  ≈ 2–3 agent-days
Pre-registered analysis only; exploratory work labelled as such. **At least two
adversarial review rounds before believing any result** (C11), the second aimed
at the corrections the first produces.

**Stop-the-programme points: G0, G1, G2, G3.** Three of the four are before any
scored run. That ordering is the whole design lesson of the previous four cases.

### What this costs
Engineering ≈ 7–9 agent-days to G3. Token spend is minor — case 04's cells ran
≈ $0.69 each on the consumed accounting, so even n = 260 per arm is a few
hundred dollars. **Wall-clock and memory are the real budget**, and Phase 2 is
what measures them rather than assuming.

## 11. Is this still worth building? — r5's honest position

Round 3 did not merely find defects; it located a risk that survives all of its
own fixes, and it deserves to sit here rather than in a findings table.

**The prevention claim turns on mis-specification, and this subject makes
mis-specification hard to see.** The treated arm's characteristic silent failure
is not a coding slip — it is *a sound and complete proof against a wrong
formalisation*, which ships a provably-conformant wrong program with maximal
confidence. Chess movegen is the domain where that is least likely to happen and
least likely to matter: the rules are famously well specified, saturated in
training data, and any error is caught by a reference the world already agrees on.
So the subject that fixed case 04's leak may have optimised away the very failure
the study exists to observe.

**And the capability window is plausibly empty or inverted here**, because writing
correct movegen is much easier for a model than *proving* it correct — the
opposite of the ordering the design needs.

Two consequences r5 accepts rather than argues away:

1. **G2 should run as early and as cheaply as possible**, because it is the phase
   most likely to end the programme, and ending early is the cheapest good
   outcome available.
2. **The claim must be scoped in the abstract, not the threats section**: *FCDD on
   a formalisation-friendly, training-saturated domain, against a lab-authored
   disambiguation of an external standard.* Every qualifier there was earned by a
   review finding, and dropping any of them would overstate what the study could
   support.

**r6 — round 4 called this section a hedge, and it was right.** A section titled
*"Is this still worth building?"* that diagnoses the fatal problem and then
declines to draw the conclusion, deferring on unestimated cost, is the shape the
programme's own report diagnoses in its experimenters: gaps in one's own protocol
filling themselves in the flattering direction. The tell was structural — §8 held
five kill criteria, none encoding §11's own conclusion, and the missing one would
have fired *now, at design time, at zero cost*. **It is now §8's criterion 6.**

**The conclusion, drawn:** this subject can test the mechanism but **not the
motivating case**, and four review rounds could not make it freezable. The
recommendation carried forward is therefore:

1. **Do not build case 05 as drafted.**
2. **Run the ATTACK-budget experiment instead** — the programme's one actionable
   finding, cheap, decidable, needing no hidden oracle, and the first *improvement*
   to the method rather than a fifth price tag.
3. **If the prevention claim is to be tested, re-derive the subject from the
   mis-specification requirement** — a genuinely contested or ambiguous
   specification — through a case03-style multi-design scored selection. That is
   the step case 04 skipped and paid for with a voided study.

Nothing in that discards the four rounds' yield: the bwrap isolation (verified on
this host), the gate discipline, the ordinal outcome, the dual cost accounting and
the calibration machinery all transfer to whatever subject that process selects.

## 12. Review rounds

- **Round 1 (Fable, adversarial, 2026-08-26):** 4 blocking, 5 major, 5 minor.
  All 14 accepted; 2 changed the design, 1 retired an option, 1 was corrected on
  a point of fact. Record in §11. C11's "≥ 2 rounds" applies to the frozen
  pre-registration, not to this draft. **Four rounds have now run (§13–§16).**

## 13. Review round 1 — findings and disposition

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

## 14. Review round 2 — the repairs, attacked

Round 2's charter was this lab's own history: case02's round two overturned three
of round one's corrections, so the fixes are the least-reviewed part of any
revision. It found **four blocking defects, all of them in round 1's repairs.**

| # | Finding | Disposition |
|---|---|---|
| **B1** | Sibling-to-sibling isolation is nowhere in the design; A-2026-08-26b's proven channel (cells reading each other's trees) has no constraint, no gate and no threat-model line | **Accepted, design changed.** New **C23**; threat model gains the sibling line; G-ISO now explicitly proves sibling absence |
| **B2** | Neither horn of round 1's D2 replacement is sound: D2a cannot bind below n ≈ 130 and reopens the refuse-to-ship path; D2b priced itself with the COMPLETING accounting §6 forbids ($0.35 vs $0.69/cell) and ignored wall-clock (case04: 13 cells ≈ 16 h, treated arm serial → 260 cells ≈ weeks) | **Accepted, both horns dropped.** Replaced by a single **ordinal outcome** CORRECT ≻ LOUD ≻ SILENT tested once, so one powered test carries both directions; n and schedule become pilot-measured freeze inputs |
| **B3** | G-RELAY's "oracle-shaped-query detection" is a judgement or a blocklist — the two things this design refuses elsewhere — and round 1 recorded it as a mechanical gate | **Accepted.** Byte accounting (countable) stays a gate; query-shape detection demoted to a descriptive detector; per-cell relay sockets and tokens added |
| **B4** | Nothing verifies the treatment was *delivered*; case04's arm wrote zero quantified properties and its zero-`Admitted` check passed vacuously | **Accepted, gate added.** Mechanical delivery criterion (k non-vacuous quantified properties with witnesses, clause coverage) plus a pre-declared ITT/per-protocol pair, with *treatment-not-delivered* as a named outcome |
| **M1** | B4's precedence fix takes the second horn rather than escaping it; §8.3's pilot rule is unoperationalised | Accepted — the claim is narrowed *in the abstract* to formal re-expression of an already-disambiguated spec, and the pilot rule becomes numeric |
| **M2** | The G-ISO exit scan fails every productive cell, since cells legitimately write to `/work` | Accepted — writable-set rule stated mechanically; the `/work` delta is deposited as provenance |
| **M3** | The image is the live host; a system update mid-schedule changes the toolchain invisibly | Accepted — immutable snapshot, or per-cell start-time closure re-check |
| **M4** | The power grid assumes iid cells while nothing makes replicates independent | Accepted — the grammar emits a distinct spec instance per cell, paired across arms; sampling policy stated |
| **M5** | "Infrastructure death" is undefined and gameable, and COMPLETING is undefined for a resume-completed cell | Accepted — mechanical classifier with method-attribution as the default. *Point of fact:* we verified 0 of case04's 13 completing sessions were resume targets, so the defect was latent there, not realised |
| **M6** | The reference semantics is the answer-shaped artefact and the draft never says where it lives during runs | Accepted — built after the last cell closes, under commit-reveal custody, or off-host |
| m1 | r2 wrongly claimed the ATTACK-budget study would not exercise the relay | Accepted, corrected — with the agent inside, every model call traverses it |
| m2, m3, m5 | Oracle socket should be Option-B-conditional; RSS needs cgroup `memory.peak`; provider-side caching contaminates per-cell cost | All accepted |
| m4 | Multiplicity unstated as outcomes multiply | Accepted — disclose-and-discount, primary named |

**Round 2's overturns of round 1**, recorded because they are the point of a
second round:

1. **M5's disposition was incomplete.** Keeping non-shipment in the denominator
   does not close the trivial win — a non-shipping cell still *lowers* the
   silent-failure rate. The finding was right; its fix was not. This is what
   forced the ordinal outcome.
2. **M4's demotion of G-CLUSTER was conditionally wrong.** Round 1 demoted the
   only duplication detector days before A-2026-08-26b proved duplication is a
   *realised* failure. The demotion is affordable only because C23 now legislates
   structural sibling isolation; without C23 it would have to be reversed.
3. **B1's disposition passed on topology and failed on gating.** Agent-inside
   with a relay is the right horn, but recording G-RELAY as mechanical held the
   fix to a laxer standard than the same review had just applied to G-XSCRIPT.

**Round 2's verdict:** not freezable as r2; all four blockers fixable in writing;
an **r3 followed by a round-3 pass targeted at r3's fixes** is the honest path,
since fixes made under review pressure are the least-reviewed text in any study.
The largest remaining risk it names is the outcome design: a study that runs to
completion and still cannot support or refute its hypothesis by construction is
this programme's most expensive failure mode, and the only one that spends the
budget before revealing itself.

---

## 15. Review round 3 — two lenses, nine blocking findings, all in r4's repairs

Round 3 ran as two independent reviewers: **3A** on the science (the D1 target,
outcomes, statistics) and **3B** on the plan (gates, feasibility, operations).
They shared no context. **Every blocking finding they returned lies inside r4's
own new material** — the third consecutive round for which that is true.

**The two they found independently, which is the strongest signal in the record:**

| Converged finding | 3A | 3B | Disposition |
|---|---|---|---|
| The "checksum oracle's leak is useless" premise is false, so retiring L3 was wrong | B1 | B2 | **L3 reinstated**; the "wall to belt" demotion of L1 withdrawn. A leaked suite is actionable by divide-perft bisection without inverting a single count, and §5.3's adjudication pairs *are* answers |
| Round 2's replication fix was orphaned when the grammar retired with Option A | B3 | B3 | **Rebuilt honestly**: with one fixed spec the replication unit is the sampler; power from Phase-2 sampler-noise variance; per-cell suite instances from disjoint seeds |

**3A — science:**

| # | Finding | Disposition |
|---|---|---|
| B2 | "FIDE is complete for this purpose" is **false** at the adjudication layer — threefold and fifty-move are claim-based, fivefold and 75-move automatic, insufficient-material is a shortcut not the dead-position rule (the reference's own docstring concedes it), and the ep-in-repetition key is an interpretive choice. Scoring against an implementation makes correctness an artefact's behaviour again | Accepted. A **pinned interpretation addendum** ships with the shared spec; the claim is renarrowed to *FIDE plus a lab-authored disambiguation*, in the abstract |
| B4 | The delivery gate is satisfiable by **circularity**: `legal p m := m ∈ genLegal p` earns soundness and completeness by `reflexivity`, passing every criterion while proving nothing — case 04's vacuous zero-`Admitted` one level up | Accepted. Declarative spec **frozen before generator code**, and **spec-side mutation**: injected spec mutants must break the proofs. A spec the proofs cannot lose against is circular by construction |
| M1 | §5.2's headline **contradicted its own deposited table** — startpos d5 does catch the ep omission (−258) | Accepted, corrected in the proposal **and in the script, which printed the false conclusion** |
| M2 | The mutant set cannot reach the classes that matter: list-filtering cannot express **inclusion** faults, nor **mis-specification** faults — the treated arm's characteristic silent failure | Accepted; C24 widened, mutable reference required, spec-side mutants added |
| M3 | Memorisation applies *more* strongly to this subject than to the one round 1 retired for it — movegen crates for the control, **ChessRocq for the treatment** | Accepted; scope statement in the abstract, image-content check, pre-registered memorisation reading |
| M4, M5, M7 | Tier factor multiplies the primary with no α allocation; outcome categories were arm-controlled and left a hole; the mandated-proof treatment carries an **obligation asymmetry** the control does not | All accepted — one of three multiplicity options pre-registered; categories restricted to orchestrator-observable facts; the control gets a registered comparable obligation |

**3B — plan:**

| # | Finding | Disposition |
|---|---|---|
| B1 | Phase 0 **violated C21** on day one, and nothing said where the withheld suite lives during Phase 4 | Accepted — calibrate the *generator* on a throwaway instance; generate the scored instance after close; re-run calibration on it |
| B4 | G2 had **no decision rule and could not have one at k = 3** (a true-0.5 tier falsely excluded 25% of the time; variance on 2 df) | Accepted — exact binomial rule with declared error rates, k sized to it, schedule consequence priced |
| B5 | Phase 4 listed **G-CAP**, which reads the retired L2 daemon's log and cannot be computed | Accepted — G-CAP and C20 struck, C22's manifest restated |
| M1 | python-chess and stockfish sit in the home directory the image vendors from; if either lands in the image, **G-ISO blesses it** and G2 returns a false *empty capability window* — a wrong kill verdict | Accepted — freeze-time image-content check in G1's evidence |
| M2 | Scoring executes untrusted crates: `build.rs` runs **in the orchestrator's namespace**, where the withheld references live | Accepted — submissions built and scored under the cell's own bwrap profile |
| M3, M5–M8 | G0's fault set self-selected and single-referenced; no timeout, attempt cap or hang policy though "does not ship" depends on them; no schedule ceiling; G2(b) evaluated a criterion frozen a phase later; serialised treated cells make schedule position correlate with arm | All accepted and written into Phase 0/1 deliverables and Phase-3 freeze inputs |
| G-gates | 3B's judgement that **G0 and G2 were aspirations wearing gate badges**, and that G1's "finds nothing" is absence-of-evidence | Accepted — each restated as a predicate; G1 gains the **two-cell concurrent probe** that tests C23 directly |

**Round 3's overturns of rounds 1–2:** r4's retirement of L3 (falls); round 1 B4's
dilemma and its r4 "dissolution" (the dilemma stands, narrowed); round 2 M4's fix
(orphaned); round 2 B4's delivery criterion (insufficient against the circular-spec
bypass). **Checked and standing:** C23, the dual cost accounting, the death
classifier, the per-arm informativeness gate, and the ordinal outcome itself.

**Verdict:** not freezable at r5 either. A round 4 is owed on r5's repairs, on the
evidence of what rounds 2 and 3 did to their predecessors' — and §11 records the
risk that survives every fix.

---

## 16. Review round 4 — the repairs refuted, and a disposition audit

Round 4 ran two lenses: **4A** attacking r5's repairs, **4B** auditing whether
recorded dispositions match the body and assessing whether the design is
converging. Both were told the pattern they were continuing. Both found it held.

### 4A — six blocking findings, one settled by kernel execution

| # | Finding | Status |
|---|---|---|
| **B1** | **r5's anti-circularity fix is refuted by execution.** For `legal p m := In m (genLegal p)`, soundness and completeness discharge by `exact H`, and *every* semantic spec mutant breaks a proof — so "spec mutants must break the proofs" is **maximally satisfied by the circular spec**. r5 asserted a false converse | **Accepted; the fix does not stand.** Only candidate: lab-frozen theorem statements, which renames the treatment |
| **B2** | C24's dual-reference predicate is **uncomputable on the adjudication half** — stockfish answers `go perft` but exposes no game-status query and implements no claim model, dead-position or insufficient-material adjudication (verified by running it) | Accepted — needs a second real adjudication implementation, scored on the two references' agreement set |
| **B3** | The pinned addendum **enumerates interpretive points while the hazard is the whole underdetermination space** — §1's own thesis recurring in the spec layer. No phase authors or freezes it; no named author; no amendment rule | Accepted |
| **B4** | Disjoint per-cell suites are **inert for independence under reinstated L3** (no cell sees any instance) and harmful — cells scored on different instruments | Accepted — a grammar-era fix transplanted where it does nothing |
| **B5** | r5 says "k = 3" and "likely 10–20" **ten lines apart**, and the schedule consequence is unpriced: 40–120 cells, treated serial, makes Phase 2's "≈ 1 day" false by an order of magnitude | Accepted, marked at both sites |
| **B6** | L3's reinstatement was applied to §3 only; §7 and §9 still say commit-reveal is not built. And **no rule exists for G0's re-run failing on the revealed instance** — the seed is spent, and re-drawing is seed-shopping | Accepted |
| M1–M5 | The control's new obligation **changes what the control is** (H1 becomes FCDD vs mutation-tested development) and has no place in the ordinal partition; the image-content check is a blocklist or a judgement — *the two things this design refuses elsewhere*; sampler inference is narrower than claimed and its degenerate case blinds G-CLUSTER; binomial error rates are ill-posed without an indifference zone; §7/§8.5 still price and gate the retired design | All accepted |

### 4B — the disposition audit: six recorded fixes that were not what they claimed

Verified independently against the body before acceptance:

| # | Claimed | Actual |
|---|---|---|
| D1 | "L3 reinstated; wall-to-belt demotion withdrawn" | §3 withdrew it; **§5.1 still asserted the refuted premise verbatim** as live rationale |
| D2 | "G-CAP and C20 struck" | Struck in §3 prose — **not at Phase 4, the one location the finding cited**; C20 still stood in §4 |
| D3 | "§7 re-costed" (round 1) | **Never done.** §7 still priced Option A, quoted the COMPLETING figure §6 later ruled against, and said commit-reveal was not built — while r5 reinstates it |
| D4 | — | §8's circularity kill criterion still gated "the grammar", retired two revisions earlier |
| D5 | "demoted to descriptive detectors" | Demotion present; its justification ("no hidden artefact to transcribe") **contradicted by r5's own L3 reinstatement** |
| D6 | "deposit the power script" (round 1) | **Still untracked three revisions later**, while §6 cites it and names two incompatible power methods |
| D8 | — | Cross-reference rot: the header said a third round was owed *in the revision that applied it*; section pointers off by one; a fixed fork described as open |

All are corrected in r6. **The mechanism matters more than the list**: an
off-by-one pointer and a stale sentence are exactly how round 2's orphaned
replication fix stayed hidden for a whole revision.

### The convergence assessment, accepted

4B's argument, from content rather than counts: **the same defect classes recur
under new names.** The unpowerable-gate class fired in rounds 1, 2 and 3 — three
consecutive rounds installing a gate without checking it could decide. The
vacuous-pass class ran case 04's zero-properties arm → round 2's delivery gate →
round 3's `reflexivity` bypass → round 4's refutation of the fix for that bypass,
each repair creating the next bypass one level up. **The deepest findings arrived
last**, which is the signature of divergence, not convergence. And repairs inject
defects about as fast as rounds remove them: r5 applied nine findings and shipped
six coherence failures.

**What is converging is the instrumentation** — C23, the ordinal outcome, the dual
cost accounting, the death classifier, the per-arm gate have all held across
rounds. What is not converging is the thing the instrument would be pointed at.

**Round 4's verdict, adopted as this document's own: see §11.** Do not build case
05 as drafted; run the ATTACK-budget experiment; re-derive the subject from the
mis-specification requirement through a scored multi-design selection.
