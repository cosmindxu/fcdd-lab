# Task — fix a reported bug per FCDD (formal contract-driven development)

You are picking up the current dev state of a ZX Spectrum chess program
written in Z80 assembly, which already has a formal contract. This workspace
is everything you have:

- `variants/BUGNN/` — the program source (self-contained; see its `BUILD.md`;
  `make` assembles the tape, `make test` runs the existing smoke suite).
- `harness/` — the emulator plus scripting tools to boot the program, play
  moves from any position, and read the game state back (see `HOWTO.md`;
  `build/hc91emu` is prebuilt; `tools/play.py` / `tools/chesspos.py`).
- `contract/` — the existing formal contract package for this program:
  `spec/Contract.lean` (kernel-checked spec of record, clauses C1..C14 +
  strategy properties S1..S4), `twin/` (pure Python twin), `bridge/` (the
  conformance suite; `run_all.sh` is the gate), `smt/` (z3 tier), plus
  `SUMMARY.md` / `DECISIONS.md` — read `SUMMARY.md` first.

Work **per FCDD** — the `formal-contract-dev` skill defines the method (load
it with the Skill tool, or read `~/.claude/skills/formal-contract-dev/SKILL.md`).

**Scope rule (hard):** work entirely offline and entirely inside this
workspace. Do not read, run, or fetch anything outside it — the machine has
unrelated projects on it; treat this workspace as the whole world. The only
allowed outside paths are your toolchain: `~/.elan/bin/lean` (Lean 4),
`~/.venvs/quant` (z3), and `~/.claude/skills/` (method definitions). The
bridge's `emu.py` has been pointed at this workspace's `harness/`; if any
script still references a path outside the workspace, re-point it here —
never follow it out.

A user filed the bug report below. Your job, per the method:

1. Reproduce the reported behavior with the harness.
2. Locate the contract clause(s) the buggy behavior violates — or, if the
   contract does not capture it, extend the contract first (spec + twin +
   bridge stay in lockstep).
3. Find and fix the fault in the source.
4. Prove / bridge the fix: the bridge layers relevant to the violated
   clause(s) must pass against the fixed build (extend witnesses/tests so the
   bug's class is pinned — a regression of this fault must trip the bridge).
5. Keep the existing checks green: the variant's `make test` must pass.
6. Then run an attack round: spawn a fresh adversarial reviewer agent with
   the Task tool, give it the diff, your contract delta, and your reasoning;
   address every finding. Iterate until the attack round is clean.

Done means: the reported symptom no longer reproduces, `make test` is green,
the relevant bridge layers pass, the fault's class is pinned by a test or
bridge layer, and the attack round is clean.
