# Vendored skills

Two copies of the same skill live here, deliberately, and they must not be
merged.

## `formal-contract-dev/` — FROZEN, do not update

The version of the FCDD method that **case01 actually measured**. Arm B loads
the skill at run time (its prompt directs the agent to invoke it before
working), so every Arm B number in the paper is bound to this exact text.

Pinned in `case01_spectrum_gambit/ARTICLE.md` §3.1 and `PROTOCOL.md` as:

    commit 4ca5bb3, 2026-08-04, 436 lines, sha256 68e384df562bad87…

Updating this directory would destroy the only record of what was measured and
silently invalidate the paper's reproducibility claim. If a future case study
measures a newer version, archive that one under its own dated path rather than
overwriting this.

## `formal-contract-dev-current/` — tracked, expected to move

The live skill as installed at `~/.claude/skills/formal-contract-dev/`,
vendored so it has a version history at all. Refresh it deliberately, with the
diff visible in the commit.

### Why this exists

On 2026-08-07 the installed skill gained item 16.5 (a solver/reviewer
serialisation turnstile) two days after the paper's runs and one day after the
article was finalised. Nothing measured was invalidated — the change was purely
additive, so the runs could not have followed it — but the divergence happened
**silently**, on a mutable path, in a study whose results depend on that text.
Nobody would have noticed by reading either the skill or the paper.

The installed skills directory is not a git repository, so all ten local skills
share this exposure. Vendoring the FCDD one addresses the skill this study
depends on; a dedicated skills repository would be the better general fix.

### Keeping the copy honest

    diff -u skills/formal-contract-dev-current/SKILL.md \
            ~/.claude/skills/formal-contract-dev/SKILL.md

**Refresh `SKILL.md` and `references/` only.** `TODO.md` in this directory is the
installed file *plus* repo-only annotations (the DONE ledger and the version-
hygiene note), so a blanket `rsync --delete` from the install silently truncates
it. A refresh on 2026-08-29 did exactly that; it was caught by reading the diff
before committing, which is the only reason this warning exists. Diff first,
then copy the files that actually changed.

An empty diff means the vendored copy is current. A non-empty diff means the
installed skill has moved and this copy has not been refreshed — which is the
condition that went undetected before.
