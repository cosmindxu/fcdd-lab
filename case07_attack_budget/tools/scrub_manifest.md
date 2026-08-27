# Scrub manifest — what is removed before any cell sees the tree

The subject is a **live** trading codebase. Verified on this host: the tree holds
`gateway/start_gateway_LIVE.sh`; `env.sh` evals credentials from the ib_creds
vault; `ikbr_common.py` defaults every tool to `127.0.0.1` port `IB_PORT → vault
→ 4002` (4001 = live); the operator's vault sits at
`~/.config/ikbr_tools/{vault.json,vault.key}`; and the live account id is
hardcoded in `ib_autopilot.py`, `ib_safety.py` and `packaging/build_deb.sh`.

> **Corrected 2026-08-27 by its own enforcement.** Everything below was prose
> until `tools/scrub.py` existed. When the assertions first ran they failed, and
> the four leaks they caught were all of the same shape — *a copy of the removed
> material surviving somewhere else*:
>
> | Leak | How it survived |
> |---|---|
> | `dist/*.deb` | built packages carrying the **entire pre-scrub tree**, account id included — removing source paths while an archive of them survives is no removal at all |
> | `.opencode/` | the tree ships its own **adversarial-reviewer agent and review-loop command** — the study's own treatment, pre-cooked, handed to both arms |
> | `BACKTEST_LOG.md` | a dated defect/finding log outside the removed doc trees |
> | `README.md` lines | *"the adversarial-review tranche adds three…"* — an answer in the project's own front page |
>
> The original glob `docs/REVIEW_*.md` matched **zero files** while 64 review
> documents sat in `planning/`. A manifest nothing executes is a manifest nothing
> checks.

## Removed

| Path | Why |
|---|---|
| `gateway/` | live-connection scripts |
| `env.sh` | evals the credential vault |
| `.git/` | full defect history — a rediscovery answer key |
| `CHANGELOG.md`, `docs/REVIEW_*.md` | the tree's own documented defects, same reason |
| `packaging/` | contains the account id and deployment credentials |
| `planning/`, `docs/` | **64 review/audit/incident documents** naming every unit — `live_guard` alone appears in 131 files |
| `dist/`, any `*.deb *.tar *.gz *.zip *.whl *.rpm` | archived copies of everything above |
| `.opencode/` | a prior adversarial-reviewer agent definition + review-loop command |
| `BACKTEST_LOG.md` | dated defect/finding log |

## Redacted in place

- **The live account id** — every occurrence replaced with `ACCT_REDACTED`, so it
  cannot flow into probes, finding ledgers, or cell transcripts.

## Retained but line-redacted

Documentation that is part of the system yet mentions prior findings (`README.md`,
`tests/lean/README.md`) keeps the file and loses the lines: deleting a project
README changes what the system tells a reviewer about itself, while leaving
*"an adversarial-review tranche found three…"* hands over an answer.

**In-code incident references stay** — the R18 incident theorems and their tests
are part of the system, and removing them would change the code under review.
They are answer-key-ish for the hardened stratum, and the **rediscovery rule** is
what handles them, not deletion.

## Asserted, not assumed

`tools/scrub.py` exits non-zero unless: no account-id pattern survives anywhere
(including inside archives); none of the removed trees exist; no markdown carries
adversarial-review material. **No cell is built from a tree that has not passed.**
Additionally, from inside a cell: `~/.config/ikbr_tools` is absent;
`127.0.0.1:4001` and `127.0.0.1:4002` are **unreachable**; no path resolves
outside the workspace; and a grep for the account id over the whole cell closure
returns nothing.

## Rediscovery rule (widened, round 2 M2)

Any finding matching a defect documented **anywhere in the removed material** —
not only `references/case_study.md` — is excluded from the primary and reported
separately as a rediscovery.
