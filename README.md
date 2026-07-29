# FCDD Lab

Experiments with the `formal-contract-dev` (FCDD) skill
(`~/.claude/skills/formal-contract-dev/SKILL.md`) — measuring what Formal
Contract-Driven Development actually costs and buys versus conventional
LLM-assisted development.

Each case is a self-contained folder with its own `CONTEXT.md` (orientation +
state, read this first), `PROTOCOL.md` (the pre-registered experiment design,
frozen before runs), and `ledger/` (token accounting).

| Case | Subject | Question |
|---|---|---|
| `case01_spectrum_gambit/` | Spectrum Gambit chess (Z80 engine + web stack) | Tokens to reach equivalent quality: typical dev + code review vs FCDD |
