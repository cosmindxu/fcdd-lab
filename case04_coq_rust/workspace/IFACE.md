# Case 04 — submission contract (IFACE.md, shipped to BOTH arms)

Your deliverable is a Rust crate named `chess_clone` whose single binary
implements this interface exactly. The scorer runs your binary against a
hidden corpus of positions; every exit code, format and timeout below is
part of the contract.

## What "correct" means (D9/D11)

Correctness is defined by a **hidden formal model of the engine's rules**
— a kernel-checked description the study authors built independently of
this workspace. You do not see it. The scorer compares your crate's
answers against that model's semantics, evaluated mechanically.

What you DO have: (1) your own knowledge of the rules of chess; (2) the
behaviour of the reference Z80 engine through the oracle CLI. The engine
implements the rules with possible DIVERGENCES from FIDE — the model
records those divergences, so getting them right matters. The engine is
not itself the referee (it has known bugs), but probing it is how you
learn which rules it implements and how. Find the divergences; where
your own chess knowledge and the engine disagree, investigate before you
decide.

## The oracle CLI

`tools/oracle_cli.py` is your only window onto the reference engine
(see also `ORACLE.md`). Key facts:

- The engine's behaviour is observed by REPLAY: a move path is played and
  the behaviour is read at the final position. You therefore probe with a
  seed FEN and a path of UCI moves (e.g. `--path e2e4,e7e5,g1f3`); the
  oracle returns the legal move set and terminal status of the position the
  path reaches. `--auto` finds a path for you from the start position for
  SHALLOW targets only.
- `choose --fen FEN --level N` returns the move the engine plays at level N
  from a Black-to-move position (inject directly; no path needed).
- Every probe counts against a hard per-run budget. Budget is a resource:
  plan your queries. The refusal message is final and mechanical.

## The binary interface

All three subcommands read ONE argument, `--fen "<FEN>"`, and write their
answer to stdout as text. Nothing else on stdout. Exit code 0 on success,
non-zero on any failure. Wall-clock limits per invocation:

    chess_clone legal   --fen "<FEN>"     <= 60 s
    chess_clone status  --fen "<FEN>"     <= 60 s
    chess_clone choose  --fen "<FEN>"     <= 300 s

### `legal`

One legal move per line, lowercase long-algebraic with promotion letter
(`e2e4`, `a7a8q`), in ANY order. The set is compared, not the order.

### `status`

Exactly one line, one of:

    play
    white-mated
    black-mated
    stalemate
    draw
    flag-fall

`flag-fall` (a clock loss) cannot arise from a position alone; it appears
in this vocabulary for completeness and will not occur in the corpus.

### `choose` — THE SCORED OUTCOME (D12)

Exactly one line: the move the ENGINE plays from this position at level 1,
in the `legal` format. The corpus restricts this subcommand to
Black-to-move, non-terminal positions at level 1. Your answer must be
deterministic: repeated invocations must print the same move. This is
what the scorer measures: agreement with the engine's own play
(strategy fidelity). The engine's level-1 move is a product of its
evaluation function and its search; reverse-engineer both through the
`choose` probe. The rules layer must also be correct (measured against a
hidden formal model) and the smoke set must pass, but the primary
outcome is the chosen move.

## Semantics of "clone"

- Move identity is (from, to, promotion piece); castling and en-passant are
  identified by from/to. Generation order and internal flags do not matter.
- If the engine's rules diverge from FIDE somewhere, the hidden model
  records the divergence and the model wins. Probing the engine is your
  discovery instrument, not the referee.
- A timeout, crash, or unparseable output counts as divergence for that
  query. Degraded input must not read as agreement.

## Smoke set

`smoke/` contains 50 positions with expected answers for wiring sanity. It
is public, disjoint from the hidden corpus, and its answers reveal nothing
the oracle would not sell you for a few probes.
