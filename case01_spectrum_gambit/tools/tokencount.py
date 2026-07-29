#!/usr/bin/env python3
"""Token accounting for the FCDD lab ledger.

Modes:
  tokencount.py session <transcript.jsonl> [...]   sum Claude Code session usage
  tokencount.py headless <result.json> [...]       sum `claude -p --output-format json` results

Session transcripts carry one `usage` object per assistant message
(input_tokens, cache_creation_input_tokens, cache_read_input_tokens,
output_tokens). Streamed messages can appear more than once -> dedupe by
message id, last wins. Verified against a live transcript 2026-07-29.

Optional:
  --csv run_id=...,lane=...,arm=...,phase=...,bug=...,gate=...,notes=...
      also print an append-ready row for ledger/runs.csv (totals across models).

Cost: PRICES maps model prefixes to (input, cache_write, cache_read, output)
USD per MTok. Unknown/None -> cost column omitted; raw counters stay the
ledger's ground truth either way. Fill in Fable pricing when known.
"""

import json
import sys

PRICES = {  # USD per MTok: (input, cache_write, cache_read, output)
    "claude-opus-4": (15.0, 18.75, 1.50, 75.0),
    "claude-sonnet": (3.0, 3.75, 0.30, 15.0),
    "claude-haiku-4-5": (1.0, 1.25, 0.10, 5.0),
    "claude-fable-5": None,  # unknown -> raw counters only
}

KEYS = ("input_tokens", "cache_creation_input_tokens",
        "cache_read_input_tokens", "output_tokens")


def price_for(model):
    for prefix, p in PRICES.items():
        if model.startswith(prefix):
            return p
    return None


def cost_usd(model, c):
    p = price_for(model)
    if p is None:
        return None
    return sum(n / 1e6 * rate for n, rate in zip(c, p))


def from_sessions(paths):
    """{model: [in, cw, cr, out, n_msgs]} deduped by message id."""
    seen = {}
    for path in paths:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                m = e.get("message") or {}
                u = m.get("usage")
                if e.get("type") == "assistant" and isinstance(u, dict):
                    key = m.get("id") or e.get("uuid")
                    seen[key] = (m.get("model", "?"), u)
    agg = {}
    for model, u in seen.values():
        a = agg.setdefault(model, [0, 0, 0, 0, 0])
        for i, k in enumerate(KEYS):
            a[i] += int(u.get(k, 0) or 0)
        a[4] += 1
    return agg


def _get(d, *names):
    for n in names:
        if n in d:
            return int(d[n] or 0)
    return 0


def from_headless(paths):
    """Parse `claude -p --output-format json` final objects (camel or snake)."""
    agg, extra_cost = {}, 0.0
    for path in paths:
        with open(path, encoding="utf-8") as f:
            e = json.load(f)
        mu = e.get("modelUsage") or {}
        if mu:
            for model, u in mu.items():
                a = agg.setdefault(model, [0, 0, 0, 0, 0])
                a[0] += _get(u, "inputTokens", "input_tokens")
                a[1] += _get(u, "cacheCreationInputTokens", "cache_creation_input_tokens")
                a[2] += _get(u, "cacheReadInputTokens", "cache_read_input_tokens")
                a[3] += _get(u, "outputTokens", "output_tokens")
                a[4] += 1
        elif isinstance(e.get("usage"), dict):
            u, model = e["usage"], e.get("model", "?")
            a = agg.setdefault(model, [0, 0, 0, 0, 0])
            for i, k in enumerate(KEYS):
                a[i] += _get(u, k)
            a[4] += 1
        if e.get("total_cost_usd") is not None:
            extra_cost += float(e["total_cost_usd"])
    return agg, extra_cost


def main(argv):
    if len(argv) < 3 or argv[1] not in ("session", "headless"):
        print(__doc__)
        return 2
    csv_meta = None
    paths = []
    for a in argv[2:]:
        if a.startswith("--csv"):
            csv_meta = dict(kv.split("=", 1) for kv in
                            a.split("=", 1)[1].split(",") if "=" in kv) if "=" in a else {}
        else:
            paths.append(a)
    reported_cost = None
    if argv[1] == "session":
        agg = from_sessions(paths)
    else:
        agg, reported_cost = from_headless(paths)

    tot = [0, 0, 0, 0]
    print(f"{'model':34} {'input':>10} {'cache_wr':>10} {'cache_rd':>11} "
          f"{'output':>10} {'msgs':>6}  cost_usd")
    total_cost, cost_known = 0.0, True
    for model, a in sorted(agg.items()):
        c = cost_usd(model, a[:4])
        if c is None:
            cost_known = False
        else:
            total_cost += c
        print(f"{model:34} {a[0]:>10} {a[1]:>10} {a[2]:>11} {a[3]:>10} "
              f"{a[4]:>6}  {('%.4f' % c) if c is not None else 'n/a'}")
        for i in range(4):
            tot[i] += a[i]
    cost_s = ("%.4f" % total_cost) if cost_known and agg else "n/a"
    if reported_cost:
        cost_s += f"  (CLI-reported: {reported_cost:.4f})"
    print(f"{'TOTAL':34} {tot[0]:>10} {tot[1]:>10} {tot[2]:>11} {tot[3]:>10} "
          f"{sum(a[4] for a in agg.values()):>6}  {cost_s}")

    if csv_meta is not None:
        models = "+".join(sorted(agg)) or "?"
        row = [csv_meta.get(k, "") for k in
               ("run_id", "date", "lane", "arm", "phase", "bug")]
        row += [models, csv_meta.get("effort", ""), ";".join(paths)]
        row += [str(t) for t in tot]
        row += [("%.4f" % total_cost) if cost_known and agg else "",
                csv_meta.get("gate", ""), csv_meta.get("notes", "")]
        print("CSV: " + ",".join(row))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
