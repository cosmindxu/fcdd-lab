# Scrub manifest — what is removed before any cell sees the tree

The subject is a **live** trading codebase. Verified on this host: the tree holds
`gateway/start_gateway_LIVE.sh`; `env.sh` evals credentials from the ib_creds
vault; `ikbr_common.py` defaults every tool to `127.0.0.1` port `IB_PORT → vault
→ 4002` (4001 = live); the operator's vault sits at
`~/.config/ikbr_tools/{vault.json,vault.key}`; and the live account id is
hardcoded in `ib_autopilot.py`, `ib_safety.py` and `packaging/build_deb.sh`.

## Removed

| Path | Why |
|---|---|
| `gateway/` | live-connection scripts |
| `env.sh` | evals the credential vault |
| `.git/` | full defect history — a rediscovery answer key |
| `CHANGELOG.md`, `docs/REVIEW_*.md` | the tree's own documented defects, same reason |
| `packaging/` | contains the account id and deployment credentials |

## Redacted in place

- **The live account id** — every occurrence replaced with `ACCT_REDACTED`, so it
  cannot flow into probes, finding ledgers, or cell transcripts.

## Asserted, not assumed

The build fails unless, from inside a cell: `~/.config/ikbr_tools` is absent;
`127.0.0.1:4001` and `127.0.0.1:4002` are **unreachable**; no path resolves
outside the workspace; and a grep for the account id over the whole cell closure
returns nothing.

## Rediscovery rule (widened, round 2 M2)

Any finding matching a defect documented **anywhere in the removed material** —
not only `references/case_study.md` — is excluded from the primary and reported
separately as a rediscovery.
