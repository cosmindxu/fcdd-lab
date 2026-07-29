# Decision ledger — step 1 (HC-91 formal contract)

Append-only; supersede, never delete.  Every entry records the choice, the
**rejected alternative with its concrete failure mode**, and the assumptions
it rests on (FCDD law 8).

---

### D1 — Spec of record: Lean 4 core, single file, zero axioms

**Chosen.** One self-contained `spec/Contract.lean` (1,271 lines), kernel-checked,
proofs by `rfl` on decidable Booleans.

**Rejected — multi-module spec with `lake`.** Needs a toolchain manifest and a
build dir; the gate would then depend on `lake`'s cache state, and a stale
`.olean` could make a red spec look green. One file compiled by `lean` directly
has no such state.

**Rejected — `decide` tactic everywhere.** `decide` builds a `Decidable`
instance term and drags `propext` into the axiom profile; `rfl` evaluates the
Boolean directly and needs nothing. Switching cost: statements had to be
phrased as `<bool> = true` rather than as Props.

**Rejected — `native_decide`.** It would make the 6,561-tree alpha-beta sweep
and deep perft cheap, but it injects `Lean.ofReduceBool` — the proof would then
rest on the *compiler*, not the kernel. Ruled out; the wide sweeps moved to the
twin at a lower, labelled claim level instead.

**Assumption:** Lean 4.32.2 with an empty axiom profile is the strongest tier
available here. **Consequence:** core's `Nat.land`/`List.getD`/`List.set` are
defined by well-founded recursion and pull `propext`, so the contract defines
its own structural `bitOp`/`getD'`/`set'`. Their equality with the core/masked
forms is *itself* machine-checked (`T0a`..`T0j`) over all 256 byte values, so
the substitution cannot silently change the contract.

---

### D2 — Board as `List Byte`, arithmetic as wrapping `Nat`

**Chosen.** `Board = List Byte` (128 entries), squares and pieces are `Nat`
kept in 0..255 by `w8`, exactly mirroring `add a,r` on the Z80.

**Rejected — `Board = Byte → Byte` (a function).** Much faster kernel
evaluation for sparse witness positions, but board equality then needs
`funext`, which pulls `propext` + `Quot.sound`. The zero-axiom target won.

**Rejected — `UInt8` / `Fin 256`.** Closer to the hardware in name, but kernel
reduction routes through `Fin`→`Nat` anyway while making every proof term
larger. `Nat` + explicit `w8` is the same semantics with GMP-accelerated
kernel arithmetic.

**Assumption:** the engine's board is exactly 128 bytes at `0xE000` and every
index the rules produce is `w8`-wrapped. **Violated by finding F6** — which is
why F6 is a finding and why `P_PAWN_RANK` is an explicit precondition rather
than a silent modelling convenience.

---

### D3 — Scores as unbounded `Int`, with the 16-bit gap discharged by SMT

**Chosen.** Spec and twin score in unbounded integers; the obligation "the
engine's HL never overflows" is proved separately (`smt/s1_eval_range.py`).

**Rejected — modelling HL as a wrapping 16-bit value in the spec.** Faithful,
but it makes every evaluation theorem carry a wrap-around case that is
*unreachable*, so the spec would be harder to read and the witnesses would
prove less. Splitting it into (unbounded semantics) + (a range proof) says
exactly the same thing and keeps the range proof falsifiable on its own.

**Assumption (FCDD Beat 2.7 numeric-domain rule):** Python's bignums contain
Lean's `Int`, which contains the engine's `int16` **given s1**. If s1's
component bounds are wrong, twin and engine diverge silently. The bounds are
therefore recomputed from the engine's own tables at run time, not hard-coded.

---

### D4 — Strategy layer specified as PROPERTIES, not as the engine's search

**Chosen.** The contract specifies a reference `minimax`/`alphaBeta` on an
abstract game tree and proves full-window equivalence; it specifies the ply
bound, the mate/stalemate leaf convention, and evaluation antisymmetry. It does
**not** claim that the engine's `negamax` returns the minimax value.

**Rejected — specifying `negamax` as implemented.** The engine layers TT
cutoffs, null-move pruning, LMR, reverse futility and an aspiration window on
top of alpha-beta. Every one of those *deliberately* changes the returned
value. A contract asserting minimax-equality would be false, and a contract
transcribing all five heuristics would only be able to say "the code does what
the code does" — a tautology that catches nothing.

**Recorded as an explicit NON-claim** (`T21d`, and `b6`'s N1/N2): a narrow
window provably does not return the minimax value. That is the honest statement
of what alpha-beta buys, and it is what makes the heuristics' divergence a
design fact rather than a hidden defect.

---

### D5 — Alpha-beta equivalence: kernel at depth 2, twin at depth 3+random

**Chosen.** The kernel proves it exhaustively for all 3⁴ = 81 depth-2 trees;
the twin extends to all 3⁸ = 6,561 depth-3 trees plus 20,000 random trees with
branching 1..4 and centipawn-range scores.

**Rejected — the general theorem by induction.** It is the right result
(fail-soft alpha-beta bounds + window invariant), but it is ~150 lines of Lean
proof, and the pre-registered priority puts rules-core first. **Residual, named:**
the equivalence is a *small-scope* result (Jackson), not a theorem for all
trees. Claim level in SUMMARY.md says so.

**Rejected — depth 3 (6,561 trees) in the kernel.** Measured: kernel `rfl`
exceeds the heartbeat limit. Raising `maxHeartbeats` would trade a ~5× longer
gate for one extra depth — not worth it when the twin covers it and the
spec↔twin agreement is separately checked (b3).

---

### D6 — Kernel perft capped at depth 1; deeper perft is the twin's job

**Chosen.** `T3`/`T17` prove `perft = 20` and `perft(kiwipete) = 48` in the
kernel; depths 2-4 are checked twin-vs-engine (410,082 nodes).

**Rejected — `perft startPos 2 = 400` in the kernel.** Measured: `whnf`
timeout at 200,000 heartbeats. It is expressible but not affordable, and the
same fact is checked against the *real engine* one layer down, which is
stronger evidence than checking it against the spec twice.

---

### D7 — The emulator oracle reads the engine's own legal-move buffer

**Chosen.** After every move `afterMove` → `updateTerminal` → `genLegal` leaves
the full legal list for the side to move in the ply-0 buffer at `0x6000` with
its count at `genCount` (0xE0A0). A `.sna` dump therefore yields the engine's
own move list, **in generation order, with flags**, and `b5` compares it
element by element.

**Rejected — screen-scraping the board only.** The rendered board shows a
position, not a move set; a movegen bug that produces an *extra* legal move is
invisible until someone plays it. Reading `genCount` + the buffer makes the
generator itself observable.

**Rejected — the WASM harness in `upstream/`.** `verify.mjs` boots the same
tap but exposes no memory peek, and `test/driver.mjs` drives a **live public
website** — forbidden by the offline policy of this case. The native
`hc91emu --save-sna` path is fully offline.

**Assumption:** `.sna` is a 27-byte header followed by RAM `0x4000..0xFFFF`.
Cross-checked: the twin's `computeKey` reproduces the engine's `hashKey` at the
start position from tables read at `0xD540` through the same offset arithmetic.

---

### D8 — Fail direction of the emulator shell: UNJUDGEABLE, never "pass"

**Chosen.** A run whose screen never settles on a known status line (`Your
move`, `Check!`, or a terminal message) is reported **UNJUDGEABLE and fails**.
Separately, `b5` compares the engine's own `moveLog` against the script it was
given, so a dropped keystroke is a loud failure rather than a silently
mis-sampled position.

This was bought by a real incident during construction: the 14-ply Italian game
initially lost a key at ply 12 and the engine printed "Illegal move". Without
the moveLog check it would have looked like a *movegen divergence*; with it,
it was immediately visible as a harness artefact and ground-truthed by
re-running at three key cadences (60/150/300 frames — all three pass; 12 does
not). `MOVE_GAP = 150` is the chosen margin, documented at the constant.

---

### D9 — Repetition history modelled abstractly, not as Zobrist

**Chosen.** `History` carries an opaque list of keys plus the current key;
`countReps` counts occurrences. The bridge feeds the twin the **engine's own**
`gameKeys`/`hashKey` when checking `C11_terminal`.

**Rejected — modelling `computeKey` in the contract.** The Zobrist tables are
filled at run time from a PRNG seeded off the frame counter (`zobInit`,
`seedRng`), so they are not a constant of the program; a spec that pinned them
would be pinning one boot.

**Named consequence — a bridge blind spot:** `C11_terminal` therefore tests the
*decision rule* (≥ 3 occurrences ⇒ draw), not the key function. The key
function is attacked separately and adversarially in finding **F10**, where the
tables are read out of live RAM.

---

### D10 — Divergences are specified as the engine behaves, and flagged

**Chosen (pre-registered as protocol D4's honesty rule).** Every place the
engine differs from FIDE — automatic draw declaration, e.p. target always set,
K+B vs K+B not dead, the missing back-rank pawn guard — is specified **as the
engine does it**, with a `DIVERGENCE Fn` marker at the clause and an entry in
`organic_findings.md`.

**Rejected — normalising the spec to FIDE.** The contract would then fail on
correct engine behaviour, every arm would spend tokens "fixing" non-bugs, and
the experiment's organic lane would be polluted with the contract author's
opinions instead of the engine's defects.

---

### D-SMT-1 — One solver, not two: a recorded claim-level downgrade

The FCDD toolchain table requires **two independent verifiers** (z3 *and*
cvc5) for anything load-bearing. Only z3 is installed on this machine and the
case runs offline, so cvc5 cannot be added.

**Effect, stated rather than hidden:**

| Claim | Verifiers | Tier |
|---|---|---|
| ply/undo address bounds (s2 A1-A3) | z3 **and** the Lean kernel (T22/T23/T23a/T23b) | two independent — rule MET |
| per-ply array disjointness (s2 A4) | z3 only | SOLVER-PROVED, single solver |
| `gameKeys` → sysvars (s2 A5) | z3 **and** execution (`b7` F5) | two independent — rule MET |
| int16 no-overflow (s1) | z3 only, over bounds recomputed from the engine's tables | SOLVER-PROVED, single solver |
| aspiration window dead (s3) | z3 only, over a hand-extracted control-flow model | SOLVER-PROVED, single solver, **extraction is an assumption** |

The three single-solver rows are labelled as such in `SUMMARY.md` and must not
be quoted as "proved" without the qualifier.

---

### D-GATE-1 — The gate is judged by exit code, and clears its own caches

`bridge/run_all.sh` deletes `__pycache__` and the stale `spec/Contract.olean`
before running, then judges each of the 11 layers by **exit status only** and
prints the red ones by name. Tail-matching was rejected: a layer that prints
"0 failures" and exits 1 (e.g. an exception after the summary line) would pass
a tail check.

---

### D-SCOPE-1 — What was cut, and why

Named so the coverage claim in `SUMMARY.md` cannot quietly overstate itself:

* **Beat 4 (multi-agent adversarial ATTACK) was not run.** Step 1's brief is
  Beats 1-3 plus the emulator oracle; the adversarial round belongs to the
  arms. The standing FCDD residual therefore applies at full strength: spec and
  twin share one author, and the bridge cannot catch a common-mode
  misconception. What *does* attack that residual here is the engine itself —
  b4/b5 compare against 7,343 lines of assembly written by someone else.
* **The setup-editor demonstration of F6 was cut** (~25 scripted keystrokes);
  F6 is recorded at the CODE-READ claim level instead of CONFIRMED.
* **`negamax`'s heuristics are not transcribed** (see D4). The contract
  constrains what the search *returns* (a legal move, within a ply bound), not
  how it searches.
* **Opening book, clock, save/load, display and the setup editor are out of
  scope** entirely. They are inputs to the position, not rules of the game;
  F1 and F6 both note that they are the paths by which an out-of-contract
  position could reach the engine.
