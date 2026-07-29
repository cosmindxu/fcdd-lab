# Seeding — 7 sealed single-fault variants (lane: seeding)

You are the SEEDING agent of a pre-registered A/B experiment (FCDD lab
case01). Your outputs are the experiment's GROUND TRUTH; most are SEALED.
Work fully autonomously; NO web access (no WebSearch/WebFetch); do not use
git anywhere.

## Target

`/media/sf_Projects/HC91_emulator/chess/` (READ-ONLY: `chess.asm` +
`engine.inc`, `movegen.inc`, `perft.inc`, `tt.inc`, `zobrist.inc`,
`pieces.inc`; built by `make` via pasmo + `../tools/zxtap.py` → `chess.tap`).
The hc91emu emulator (same repo) and
`/media/sf_Projects/fcdd_lab/case01_spectrum_gambit/upstream/` (node driver)
run it headlessly; the repo docs show how. FIRST: build the PRISTINE tap and
run one sanity game / perft to prove your harness works.

## Task — 7 bugs

Classes (exactly one bug each; subtle, realistic hand-written-asm mistakes —
wrong flag test, off-by-one, wrong register, missed edge case — NEVER syntax
errors and NEVER something that crashes on move 1):
movegen/legality (castling rights, castling-through-check, or en passant) ·
promotion handling · check/mate/stalemate detection · search/TT (probe/store
key or depth bound) · quiescence · eval (sign/asymmetry) · draw accounting
(50-move or repetition).

Assign ids bug01..bug07 in a SHUFFLED order of your own choosing — the id
order must NOT follow the class list above (the orchestrator knows this
prompt and must stay blind).

For EACH bug:
1. Copy the chess sources to
   `/media/sf_Projects/fcdd_lab/case01_spectrum_gambit/arms/variants/bugNN/`
   (no `.git`; make it SELF-BUILDABLE — copy what the Makefile needs, e.g.
   `zxtap.py`, adjusting paths, and write the exact build line in the
   variant's `BUILD.md`). Apply exactly ONE fault. Rebuild the variant's
   `chess.tap` — it must assemble cleanly.
2. VERIFY the fault MANIFESTS: a concrete reproducible wrong behavior through
   the emulator/driver (position / move sequence → observed vs expected). If
   it will not manifest observably, pick a different fault in the same class.
   Keep the repro.
3. Write a SYMPTOM-LEVEL report
   `.../case01_spectrum_gambit/bug_reports/bugNN.md`: observed behavior,
   exact repro steps, expected behavior. NO hints about file, location,
   cause, or class.
4. Record in `.../case01_spectrum_gambit/sealed/answer_key.json`:
   {id, files+lines, class, description, exact diff, repro, acceptance}.
   Also write an ACCEPTANCE CHECK under `sealed/acceptance/bugNN/` — a
   runnable script that exits 0 iff the fault is fixed AND the symptom is
   gone (it may embed expected values; arms never see it).

## Arm harness (shared, once)

Create `.../case01_spectrum_gambit/arms/harness/` = a copy of the hc91emu
repo WITHOUT the `chess/` sources and WITHOUT `.git` — just enough to build/
run the emulator and drive games against any variant's `chess.tap`. Verify a
variant tap actually runs in it, and write `arms/harness/HOWTO.md` (build +
drive commands). This is what the arms will use, so they never touch the
pristine repo.

## Sealing rules (absolute)

- Nothing from `sealed/**` may appear in your final message, in
  `bug_reports/`, in the variant trees, or anywhere outside `sealed/`.
- Final message = ONLY: variants completed (count), sha256 of
  `sealed/answer_key.json`, the list of bug_reports files with one-line
  symptom titles, harness caveats if any. NO classes, NO locations, NO diffs.
