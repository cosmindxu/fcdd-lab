# Step 1 — Formal contract of the HC-91 chess engine (lane: step1_contract)

You are running Step 1 of a pre-registered experiment (FCDD lab case01). Work
fully autonomously — no user is present; never wait for input or ask questions.
NO web access by policy: do not use WebSearch or WebFetch. Do not use git
anywhere. Everything you need is local.

## Task

Express the chess game and its implemented playing strategies as a FORMAL
CONTRACT, following the `formal-contract-dev` (FCDD) skill — invoke it FIRST
with the Skill tool; use its companion `formal-verification` skill for the
proving tiers. Depth = LAYERED (protocol D4).

The engine: `/media/sf_Projects/HC91_emulator/chess/` — 7,343 lines of Z80
assembly across `chess.asm`, `engine.inc`, `movegen.inc`, `perft.inc`,
`tt.inc`, `zobrist.inc`, `pieces.inc`. Built by `make` in that dir (pasmo →
`../tools/zxtap.py` → `chess.tap`). The hc91emu emulator (same repo) runs it;
the repo docs (README / ROADMAP / CLAUDE_VS_ENGINE / SELFPLAY_EXPERIMENT) and
`/media/sf_Projects/fcdd_lab/case01_spectrum_gambit/upstream/` (node driver:
`verify.mjs`, `test/driver.mjs`) show how to drive it headlessly.
READ THE ASM — the contract covers the rules AS IMPLEMENTED, not
FIDE-as-you-remember-it.

## Deliverables (write ONLY under /media/sf_Projects/fcdd_lab/case01_spectrum_gambit/step1_contract/)

1. **Beat 1 — spec/**: Lean 4 core (no mathlib; `~/.elan/bin/lean`;
   zero-axiom discipline, `#print axioms` clean, non-vacuous witnesses).
   Kernel spec of the implemented rules: board/state model, movegen, legality,
   check/checkmate/stalemate, castling/en-passant/promotion, the draw rules
   the engine actually has. Strategy layer as PROPERTIES (not determinized):
   returns-a-legal-move-when-one-exists, search terminates within budget,
   eval symmetry where the code intends it, alpha-beta ≡ minimax at small
   depth. Where the engine diverges from FIDE: spec the ENGINE's actual rule
   and FLAG the divergence in organic_findings.md — never silently normalize.
2. **Beat 2 — twin/**: a pure Python twin of the spec (board, rules,
   reference minimax/alpha-beta), clause-for-clause faithful (same names,
   same boundary operators).
3. **Beat 3 — bridge/**: conformance suite, plain scripts, judged by exit
   code: Lean witnesses conform in the twin; mutations fail the RIGHT clause;
   twin-vs-spec brute force on small positions; **perft cross-check** (the
   engine's perft.inc vs the twin's perft on standard + engine-relevant
   positions); emulator-as-oracle sampling — drive real games and check every
   engine move against twin legality + the strategy properties. Document
   bridge blind spots honestly.
4. SMT (z3+cvc5 in `~/.venvs/quant`) where an invariant fits arithmetic
   better than Lean, per the formal-verification tiers.
5. `organic_findings.md` (real engine bugs / FIDE divergences found — log
   candidly; this feeds the experiment's organic lane), `DECISIONS.md` (FCDD
   decision ledger: forks, rejected alternatives, assumptions), `SUMMARY.md`
   (what is KERNEL-PROVED vs SOLVER-PROVED vs EXHAUSTIVELY-CHECKED vs
   SAMPLED — claim levels; assumptions enumerated; honest coverage).

## Constraints

- `/media/sf_Projects/HC91_emulator` and `.../upstream` are READ-ONLY: run
  their builds/tests freely; never edit, never commit.
- Priority if effort balloons: rules-core (spec+twin+bridge incl. perft)
  FIRST, strategy properties second, emulator game-sampling third. A smaller
  HONEST contract with correct claim levels beats a bigger pretended one —
  ship the partial and say so in SUMMARY.md.
- DONE = bridge suite green by exit code + `lean` exits 0 on spec/ with clean
  axioms + SUMMARY.md honest.
- Final message ≤ 10 lines: counts (clauses / theorems / witnesses / suites),
  bridge verdict, findings count. Nothing else.
