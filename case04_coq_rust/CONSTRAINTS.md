# Case 04 — constraints inherited from cases 01–03, plus its own

**Read this before designing, building, or running anything.** C1–C11 are
inherited verbatim from `case03/CONSTRAINTS.md` (each records a defect that
actually occurred; the case03 file names the amendments). C12–C16 are new to
this case. The design is not free to trade any of these away; it is free to
choose *how* it meets them.

## Inherited (case03/CONSTRAINTS.md, which inherits case02's amendments)

- **C1 — no arm may hold the answer, and the check is code.** Case02 shipped
  the treated arm the pristine binary (A17). Here: the pristine `chess.tap`
  is orchestrator-side only; `workspace_manifest_guard.py` runs at workspace
  build; the sealed corpus is registered as sealed material. A run that fails
  the guard does not launch.
- **C2 — the benchmark must be able to produce failures.** Plus the named
  gate: if it cannot, the study is declared UNINFORMATIVE (a benchmark
  failure), not a null on the method (PREREG §6).
- **C3 — model identity is verified, not assumed.** Runner pins the model for
  subagents too; per-run check on recorded `modelUsage`; mismatch aborts the
  cell.
- **C4 — the primary estimator is invariance-checked before freezing.** μ is
  a proportion (unit-free by construction); dispersion uses scale-free
  `sd(ln cost)`, never case02's `CV_log`.
- **C5 — dry-run the analysis script against a real completed cell before
  freezing.** A frozen-never-run script ships defects (case02: A7, A8).
- **C6 — schedule discontinuities are logged automatically**, and sensitivity
  analyses select cells by identity, never by list position (A18).
- **C7 — the artefact category is the treatment label.** Both arms ship the
  same category: a Rust crate with the frozen API. (See C15 for the residual.)
- **C8 — the blinding audit covers the scrubber's own output vocabulary.**
- **C9 — the grader is not the model under study.**
- **C10 — every reported number is emitted by a deposited script.**
- **C11 — the amendment log is append-only; budget ≥2 adversarial review
  rounds before believing any result.**

## New for case04

**C12 — the toolchain is pinned and recorded.** Rocq 9.1.1 (switch
`coq-switch`), MetaRocq 1.5.1+9.1, rocq-rust-extraction 0.2.1, rustc 1.97.1,
the harness commit, and the model+effort are written into the frozen
pre-registration. A toolchain change mid-study is an amendment with the same
status as a model change.

**C13 — process conformance is checked by code, per arm, per run.**
Arm A: the shipped crate's extracted modules must hash-match the deposited
extractor output of that run's Rocq sources; the Rocq tree must compile with
zero `Admitted`/`admit`/run-added `Axiom`; the hand-written adapter must
satisfy the frozen adapter rule (PREREG §2). Arm B: no `.v` files, no Rocq
invocations in the transcript. Both checks run mechanically on the workspace
+ transcript; failure is reported as a process violation, not smoothed over.
A finding that the check itself is gameable is a finding and gets recorded.

**C14 — the oracle query cap is enforced by the oracle CLI, not by
instruction.** The CLI counts queries per run and refuses beyond the cap; the
final count lands in the run's ledger row. "The prompt said not to" is not an
enforcement mechanism — case02's history says instructions leak.

**C15 — extracted Rust looks generated; the grading tier plans for that
leak.** Blinded source grading runs with the C8 audit covering style-level
tells (allocator boilerplate, Peano-nat patterns, generated naming), plus a
manipulation check. If the audit fails, the tier is reported as UNBLINDED —
not trusted and silently caveated.

**C16 — only oracle-self-consistent behaviours are scorable.** Before the
corpus is sealed, every candidate behaviour (legal set, status, chosen move at
the frozen level) is evaluated twice from independent emulator invocations.
Anything the oracle does not reproduce on itself is excluded from scoring,
and the exclusion statistics land in the report. The corpus never asserts
something the referee cannot repeat.
