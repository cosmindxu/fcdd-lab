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
   Task tool, give it the diff and your reasoning, and address every finding
   it raises. Iterate until the reviewer has no findings left.

Done means: the reported symptom no longer reproduces, `make test` is green,
your new test passes, and the review round is clean.
