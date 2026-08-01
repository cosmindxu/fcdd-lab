# Task — fix a reported bug in a Z80 chess program

You are a software developer picking up the current dev state of a ZX Spectrum
chess program written in Z80 assembly. This workspace is everything you have:

- `variants/BUGNN/` — the program source (self-contained; see its `BUILD.md`;
  `make` assembles the tape, `make test` runs the existing smoke suite).
- `harness/` — the emulator plus scripting tools to boot the program, play
  moves from any position, and read the game state back (see `HOWTO.md`;
  `build/hc91emu` is prebuilt; `tools/play.py` and `tools/chesspos.py` do most
  of the work).

**Scope rule (hard):** work entirely offline and entirely inside this
workspace. Do not read, run, or fetch anything outside it — the machine has
unrelated projects on it; treat this workspace as the whole world.

A user filed the bug report below. Your job, in the usual way:

1. Reproduce the reported behavior with the harness.
2. Find the fault in the source and fix it.
3. Add or adjust a test that would have caught this bug (a scripted harness
   run or host-side check committed next to the source is fine).
4. Keep the existing checks green: the variant's `make test` must pass.
5. Then get your work code-reviewed: spawn a fresh reviewer agent with the
   Task tool — **run it synchronously (`run_in_background: false`), never in
   the background** — give it the diff and your reasoning.
   **Termination rule (read carefully — it is a hard stop, not a target):**
   - A round that reports **no defect in the fix** CLOSES the review gate.
     Stop there. Coverage, robustness, style and documentation findings are
     **recorded in `FIX_NOTES.md` and NOT required to be resolved** — a
     reviewer can always name one more uncovered case, so "no findings at
     all" is not a reachable state and is not the bar.
   - Only a finding that shows the fix is **wrong, incomplete, or breaks
     something** obliges you to fix it and run one more round.
   - **Hard cap: 3 rounds.** If you reach it, stop and record why.
   **Do not end your session while a reviewer is still running.**

Done means: the reported symptom no longer reproduces, `make test` is green,
your new test passes, and the review round is clean.

## Interruption resilience (READ THIS — it applies from the first minute)

This environment can cut your session off at any moment (infrastructure
limits). You may be resumed later, possibly WITHOUT your conversation
context, into the same workspace. Work so that an interruption costs
minutes, not hours:

- Keep a **`STATE.md`** at the workspace root, updated as you go — not at
  the end. It must always answer, in a few lines: what the bug is, what you
  have established, what you have already changed (files + why), what is
  verified vs unverified, and the SINGLE next action you intended.
- Prefer many small verified steps over one long unverified stretch: apply a
  change, run the check, record the result in `STATE.md`, continue.
- Never leave the workspace in a state where a fresh reader cannot tell
  whether a change is finished or half-applied.
- If you are resumed: read `STATE.md` and your own edits FIRST, re-establish
  where you were, and continue — do not restart, do not redo finished work.
