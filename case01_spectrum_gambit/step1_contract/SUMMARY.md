# SUMMARY — HC-91 chess engine, formal contract (case01 step 1)

Target: `/media/sf_Projects/HC91_emulator/chess/` — 7,343 lines of Z80
assembly (`chess.asm`, `engine.inc`, `movegen.inc`, `perft.inc`, `tt.inc`,
`zobrist.inc`, `pieces.inc`), built by `pasmo` into `chess.tap`, exercised
head­lessly inside `hc91emu`.

Depth: **LAYERED** (protocol D4).  Beats run: **1 (PROVE), 2 (TWIN),
3 (BRIDGE), 3.5 (SHELL), 3.75 (VALIDATE ON REALITY)**.
Beat 4 (adversarial ATTACK) was **not** run — see *Residuals*.

---

## What is in the package

| Path | What it is |
|---|---|
| `spec/Contract.lean` | The spec of record. 1,271 lines, 155 definitions, **95 theorems**, kernel-checked, **empty axiom profile**. |
| `twin/hc91_twin.py` | Pure Python twin, clause-for-clause, same names and boundary operators. No I/O. |
| `twin/positions.py` | The 11 Lean witness positions + the engine's own perft boards from `perft.inc`. |
| `bridge/b0..b7`, `bridge/run_all.sh` | The conformance suite; one gate, judged by exit code. |
| `bridge/emu.py` | The **shell** — the only impure module: drives `hc91emu`, reads `.sna` RAM. |
| `smt/s1..s3` | z3 tier: int16 no-overflow, memory layout, the dead aspiration window. |
| `organic_findings.md` | 10 findings in the pristine engine, with claim levels. |
| `DECISIONS.md` | Forks, rejected alternatives with their failure modes, assumptions. |

**Gate verdict: GREEN, 11/11 layers, exit 0.**  Wall clock ≈ 3 min 15 s
(`bash bridge/run_all.sh`).

---

## The contract

**14 clauses** (`C1`..`C14`), one per property, sharing a single finding
vocabulary across Lean, the twin and the bridge:

| | Clause | What it forbids |
|---|---|---|
| C1 | `pseudoLegal` | a move no piece can make |
| C2 | `legal` | a move that survives generation but not the check filter |
| C3 | `makeAgrees` | a post-position that is not `makeMove pre mv` |
| C4 | `unmakeInverts` | a make/unmake pair that does not round-trip |
| C5 | `sideAlternates` | the side to move not changing |
| C6 | `kingSafe` | the mover leaving its own king attacked |
| C7 | `rightsMonotone` | castling rights being invented |
| C8 | `epDiscipline` | an e.p. target without / dropped after a double push |
| C9 | `halfmove` | the fifty-move clock not resetting on a pawn move or capture |
| C10 | `kingSquares` | `wking`/`bking` not tracking the board |
| C11 | `terminal` | a misreported mate / stalemate / draw |
| C12 | `pieceCount` | material appearing or vanishing |
| C13 | `kingsUnique` | not exactly one king per side |
| C14 | `promotion` | a promotion of the wrong colour or type |

Plus the strategy layer as **properties, not a determinisation**: returns a
legal move (S1), search terminates within a ply budget (S2), evaluation
antisymmetry (S3), alpha-beta ≡ minimax under a full window (S4).

---

## Claim levels — what is actually established

> The badge must match the detector.  Nothing below is rounded up.

### KERNEL-PROVED (Lean 4, empty axiom profile, no `sorry`, no `native_decide`)

95 theorems.  All proofs are `rfl` on decidable Booleans, so `#print axioms`
reports **"does not depend on any axioms"** for all 31 audited declarations (29 theorems + the `Conforming` predicate and `perft` themselves) — not
even `propext` (the contract defines its own structural `bitOp`/`getD'`/`set'`
because core's versions use well-founded recursion; the equality of the two is
itself checked over all 256 byte values, `T0a`..`T0j`).

* **Spec totality**: every terminal class has a conforming witness — play,
  checkmate, stalemate, insufficient material, fifty-move, threefold.
* **Non-vacuity of every guard**: mate really has *no moves and is in check*;
  stalemate really has *no moves and is not*; the fifty-move witness is *not*
  also insufficient-material; two repetitions are *not* a draw.
* **Special moves both ways**: castling generated *and* killed by a covered
  transit square *and* killed by missing rights; e.p. generated *and* absent
  without the target; all four promotion flags present.
* **make/unmake involution** on all five special classes and on *every* legal
  move of four positions (start, castle, promotion, Kiwipete).
* **C2 ⇒ C6** over every pseudo-legal move of Kiwipete; the pin filter really
  rejects moves (10 pseudo-legal → 4 legal).
* **Evaluation antisymmetry** `evalWhite(mirror p) = -evalWhite p` on five
  witnesses, two of them non-zero.
* **Alpha-beta ≡ minimax**, exhaustively over all 81 depth-2 trees — a
  **small-scope** result, not a general theorem (D5).
* **Ply bounds**: buffers and undo records fit for ply ≤ 15 *and break at 16*.
* **Clause non-vacuity**: every clause has a failing witness; the baseline
  fails nothing; a self-pinned move trips *exactly* `C2` and `C6`.
* **perft = 20** (start) and **48** (Kiwipete) at depth 1.

### SOLVER-PROVED (z3, UNSAT of the negation)

* the evaluation and every search arithmetic around it stays inside int16
  (worst case 11,465 of 32,767) — **single solver**, bounds recomputed from the
  engine's own tables;
* the eight per-ply arrays on page 0xD4 are pairwise disjoint (28 proofs) —
  **single solver**;
* the aspiration window is unconditionally dead on all three reachable root
  exits — **single solver, over a hand-extracted control-flow model**;
* ply/undo address bounds — z3 **and** the Lean kernel, two independent
  verifiers;
* `gameKeys` reaching the ZX system variables — z3 **and** execution.

Only z3 is installed here; the single-solver rows are a recorded claim-level
downgrade (`DECISIONS.md` D-SMT-1) and must not be quoted as "proved" bare.

### EXHAUSTIVELY-CHECKED (finite domain, fully enumerated)

* **perft against the RUNNING Z80 ENGINE: 410,082 leaf nodes** over 7
  positions — start depths 1-4, Kiwipete depth 3 (97,862), the e.p. torture
  position depth 4 (43,238), the promotion position depth 3 (62,379). The twin
  reproduces **every** number the engine printed. The engine's own incremental
  Zobrist/phase/PST self-check (`checkKey`) was OK on the same run.
* **spec vs twin**: 300 generated positions × 9 observables — the full ordered
  `genMoves` and `genLegal` lists with flags, in-check, `evalWhite`,
  `gamePhase`, `isInsufficient`, `updateTerminal`, make/unmake round-trip,
  perft 1. 8,197 pseudo-legal and 5,704 legal moves compared, byte-identical.
* **alpha-beta**: all 6,561 depth-3 trees agree under a full window; 93 of
  them provably *disagree* under a narrow one (the non-claim is not vacuous);
  pruning actually happens on 5,619 of them.
* **mutation coverage**: 26 seeded faults — 16 observation mutations each
  tripping exactly its expected clause set, 10 implementation mutations
  (wrong knight offset, double push from any rank, castling through check,
  the `< 2` insufficient-material boundary, `>= 100` vs `> 100`,
  mate/stalemate inverted, wrong e.p. capture square, promotion losing the
  colour bit, eval sign error, rights never cleared) — **all caught**.
  All 14 clauses have at least one negative test.

### SAMPLED (real execution, finite sample — NOT a proof)

* **9 emulator runs, 72 checks.** Five scripted two-player games (Italian with
  both castlings, en passant, double queenside castling, fool's mate ending in
  `gameState = 1`, a Ruy-Lopez exchange with captures) plus four
  engine-plays-Black games at `aiDepth 2`.
* Per game: the engine's position after replaying its **own** move log agrees
  with the twin field by field (board, side, castling, e.p., halfmove, king
  squares, move number); its legal-move list agrees **element for element in
  generation order with flags**; its `gameState` agrees with the twin's
  `updateTerminal` fed the engine's own key history.
* **S1**: every move the engine chose was legal in the twin.

### CODE-READ (asserted from the source, not executed)

* **F6** (back-rank pawn indexes past the board) — the end-to-end
  demonstration through the setup editor was cut for effort (D-SCOPE-1).
* **F7**, **F8**, **F9** — hygiene and documentation findings.
* **F11** is CODE-READ but *mechanically pinned*: `b7` asserts the absence of
  `countReps`/`halfmove` in `engine.inc`, so adding either turns it red.

---

## Findings

**10 findings** in the pristine engine (`organic_findings.md`), plus a
"attacked, no defect found" list so the clean areas are visible.

| | Finding | Severity | Claim level |
|---|---|---|---|
| F5 | repetition history overwrites the ZX ROM system variables from ply 128; lands on `FRAMES` at ply 188 | HIGH | CONFIRMED (z3 + execution) |
| F10 | 16-bit Zobrist: 18.2 % of an 8,652-position tree collides, using the engine's own tables | HIGH | CONFIRMED (execution) |
| F4 | aspiration window is dead code; every deepening iteration searches twice — and masks a latent root hazard | MED | SOLVER-PROVED (extracted model) |
| F6 | a pawn on the back rank indexes past `board[]` into `sideToMove` | MED | CODE-READ |
| F11 | the search cannot see repetition or the fifty-move rule | MED | CONFIRMED by absence |
| F1 | castling trusts the rights bits, conjures a rook, deletes the corner piece | MED (pure-contract-only) | CONFIRMED in the model |
| F2 | e.p. target set after every double push ⇒ missed repetitions | LOW (FIDE divergence) | CONFIRMED |
| F3 | K+B vs K+B same colour not called dead | LOW (FIDE divergence) | CONFIRMED in the model |
| F7 | fifty-move clock is an unsaturated byte | LOW | CODE-READ |
| F8 | "Auto-queens promotions" comment contradicts the code | LOW | CODE-READ |
| F9 | draws declared automatically rather than claimed | LOW (FIDE divergence) | CODE-READ |

F4's second half is the one worth repeating: **fixing the aspiration window
alone would expose an engine that can return no move at all**, because the
unconditional re-search is currently what repairs `bestFrom` after a root-level
reverse-futility or null-move cutoff.

---

## Assumptions this package ships with

1. **The 128-byte board is the whole board.** Violated by F6; the contract
   makes it explicit (`P_PAWN_RANK`) rather than assuming it silently, and the
   position generator refuses to generate into the violated region *and says
   why*.
2. **The engine's int16 never overflows** — discharged by s1 under component
   bounds recomputed from the engine's own tables, single solver.
3. **`.sna` layout** is a 27-byte header + RAM `0x4000..0xFFFF`; the addresses
   in `emu.py` are the `equ` lines of `chess.asm`. Cross-checked by the twin
   reproducing the engine's `hashKey` from tables read at `0xD540`.
4. **s3's control-flow extraction** of `aiMove`/`negamax` is faithful. That is
   a hand extraction and the weakest link in F4; the instructions it was taken
   from are quoted verbatim in `organic_findings.md`.
5. **The Zobrist function is not modelled** (its tables are PRNG-seeded at
   boot), so `C11_terminal` tests the draw *decision rule*, not the key. D9.
6. **`aiDepth ∈ 1..5`** (the UI enforces it), which is what keeps `searchPly`
   inside `MAXPLY = 15` together with the quiescence cap.
7. **Emulator determinism**: `hc91emu` is a cycle-accurate deterministic
   emulator, so a scripted key sequence reproduces the same run.

---

## Residuals — what this package does NOT establish

* **Beat 4 was not run.** No independent adversarial review with distinct
  lenses. The standing FCDD residual — spec and twin share one author, and the
  bridge cannot catch a common-mode misconception — applies at full strength.
  The partial mitigation is real but partial: layers b4 and b5 compare against
  **7,343 lines of assembly written by someone else**, so a shared
  misunderstanding of the *rules* would have to be shared with the Z80 author
  too. It would not catch a shared misunderstanding of what the *contract
  should say*.
* **The bridge SAMPLES agreement; it is not a refinement proof.** perft
  compares counts, so two compensating errors on the same subtree cancel — b5
  closes part of that by comparing the move *lists*, but only over 9 games.
* **Evaluation is barely observable in the real engine.** The screen shows the
  search score and material balance, not the static evaluation, so
  `evalWhite` is verified spec↔twin (kernel + 300 positions) but **not**
  engine↔twin. This is the largest un-bridged surface in the package.
* **The search is verified only through its outputs.** No claim is made about
  TT correctness, LMR soundness, null-move safety or move ordering beyond what
  S1/S2 assert — and F10 gives concrete reason to think the TT is *not* sound.
* **Alpha-beta equivalence is small-scope** (81 trees in the kernel, 6,561 +
  20,000 in the twin), not a theorem for all trees.
* **Nine games is nine games.** No long game was played, so F5's ply-128 and
  ply-188 corruption is proved by arithmetic and by showing the region is live
  — not by watching a 188-ply game go wrong.
* **Three of the five SMT rows rest on a single solver.**

---

## Reproducing

```bash
bash bridge/run_all.sh          # the gate: 11 layers, exit code is the verdict
~/.elan/bin/lean spec/Contract.lean   # the spec alone; every #print axioms must be empty
```

Requires `~/.elan/bin/lean` (4.32.2), `python3`, `~/.venvs/quant` (z3), and
`hc91emu` + `roms/48.rom` from the read-only upstream tree. Nothing in
`/media/sf_Projects/HC91_emulator` or `upstream/` is written to.
