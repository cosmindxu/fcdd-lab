# Case 04 — Arm A prompt: FORMAL EXPRESSION + MECHANICAL EXTRACTION

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

## Your process (the treatment under study)

1. **Express the rules formally in Rocq** (Rocq 9.1.1, opam switch
   `coq-switch`). A complete functional model of the rules as you have
   discovered them: board representation, move generation, legality,
   terminal detection — enough to answer `legal` and `status` — and, as
   far as you can, the move choice for `choose`. The formal expression is
   YOUR work: no reference specification is provided. **The Rocq
   development must compile with zero `Admitted`, zero `admit`, and no new
   `Axiom`.** Proofs of properties are not required, but any you complete
   are recorded as quality-beyond-bar in NOTES.md.
2. **Extract Rust mechanically**: `rocq compile` with
   `Redirect "out.rs" Rust Extract <entry>.` using the installed plugin
   (`From TypedExtraction.Plugin Require Import Loader.` plus
   `ExtrRustBasic` and, where you want native integer arithmetic,
   `ExtrRustUncheckedArith`). Deposit the extractor's raw output in
   `artifacts/` BEFORE any post-processing. The only permitted
   post-processing is the frozen mechanical step: delete lines beginning
   `Debug:` and lines beginning `#![allow`. Your crate must contain that
   post-processed file byte-identical; the hash is checked.
3. **Adapter**: hand-written glue (FEN parsing, CLI, printing, converting
   into the extracted representations) may live in the crate, at most
   **200 non-comment lines**, and must not contain chess semantics — no
   move generation, legality, or status logic outside the extracted
   module. If a construct in the generated code confuses you, read the
   extracted code; do not reimplement its semantics in the adapter.
4. **Oracle probes**: use `tools/oracle_cli.py` freely within your budget.
   Every call counts. Prefer replaying your OWN paths (`--path`) for
   positions you construct; `--auto` only finds shallow targets.
5. **Adversarial review against a declared budget.** Before your first
   review round, write in NOTES.md which checks you will apply (e.g. each
   move-generation rule class once) and treat that list as the coverage
   budget: the review stops when the list is covered, NOT when review
   stops finding things. Before launching any reviewer, commit a clean
   tree; the reviewer works from that committed sha and reports which one
   it reviewed.

## Definition of done

- `cargo build --release` succeeds.
- All 50 smoke positions (`smoke/`) pass `legal` and `status` exactly.
- NOTES.md records: what you formalised, what you proved (if anything),
  divergences discovered between the engine and FIDE, and the probe budget
  used.

Work until done. No network. The oracle is the only ground truth.
