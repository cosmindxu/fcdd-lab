# Case 04 — Arm B prompt: DIRECT RUST DEVELOPMENT

You are developing a chess engine clone in this workspace. Read
`IFACE.md` first — it is the binding contract. Then `ORACLE.md`. Then
work.

## The task

Produce the `chess_clone` Rust crate described in IFACE.md. **The scored
outcome is `choose`**: your program must play the move the reference
engine plays at level 1, from any Black-to-move position. Correctness is
measured against the ENGINE'S OWN PLAY (strategy fidelity — the only
meaning of "which move should this clone play"). The rules layer (legal
moves, terminal status) must also be correct — measured against a hidden
formal model — and your crate must pass the smoke set, but the scored
outcome is the chosen move.

To match the engine's play you must reverse-engineer its decision
procedure — its evaluation function and its level-1 search — through the
oracle's `choose` probe and standard chess knowledge. This is the hard
part of the task: budget your probes. Queries are capped and counted.

Start by characterising: probe `choose` on varied positions, form a
hypothesis about the evaluation (material weights? piece-square tables?
mobility terms?), test it with more probes, refine.

## Your process (ordinary development plus review)

1. Design and implement the crate directly in Rust, in this workspace,
   in the way you would build it for production: write the move
   generation, legality and terminal detection, and the move-choice logic,
   from your own chess knowledge and the engine's observed behaviour.
2. **Review rounds**: before you finish, launch a code-review pass over
   your own work (a fresh reviewer perspective), act on its findings, and
   record them in NOTES.md. This mirrors how the ordinary arm reviewed its
   work in the earlier studies of this series. Before launching the
   reviewer, commit a clean tree; the reviewer works from that committed
   sha and reports which one it reviewed.
3. **Oracle probes**: use `tools/oracle_cli.py` freely within your budget.
   Every call counts. Prefer replaying your OWN paths (`--path`) for
   positions you construct; `--auto` only finds shallow targets.

## Hard process constraint

You may NOT use Rocq/Coq, the extraction plugin, or any code generator for
this task. The crate is written by hand in Rust. (Violating this is a
process violation that invalidates the run.) This constraint exists for
the experiment's symmetry, not because the tooling is unavailable.

## Definition of done

- `cargo build --release` succeeds.
- All 50 smoke positions (`smoke/`) pass `legal` and `status` exactly.
- NOTES.md records: your design notes, the review findings and what you did
  about them, divergences discovered between the engine and FIDE, and the
  probe budget used.

Work until done. No network. The oracle is the only ground truth.
