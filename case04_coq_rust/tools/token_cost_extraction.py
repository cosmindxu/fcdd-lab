#!/usr/bin/env python3
"""Case 04 — token-level cost of the Rocq-extraction arm vs direct Rust.

Emits every number quoted in the extraction-cost note (C10). Reads only the
per-cell opencode transcripts under ledger/raw/ and ledger/runs.json.

Two accountings are reported deliberately:
  COMPLETING  — the pre-registered metric (PREREG §7): the last session only,
                i.e. infrastructure-dying attempts excluded.
  CONSUMED    — every session in the cell, i.e. what the work actually cost,
                including attempts killed by OOM and relaunched.
The gap between them is the question: arm A's deaths were a property of its
toolchain (MetaRocq/Rocq memory pressure, CONTEXT 2026-08-26), not of neutral
infrastructure, so excluding them prices a method by ignoring its failure mode.

NOTE: the case04 scored phase is a CONSTRAINT-VIOLATION study (amendment
A-2026-08-26). Nothing here is admissible as evidence about either method.
These are descriptive magnitudes only.
"""
import json, glob, os
from collections import OrderedDict, defaultdict

RAW = os.path.join(os.path.dirname(__file__), "..", "ledger", "raw")
FIELDS = ("input", "output", "reasoning", "cache_read")


def cell_tally(path):
    """-> (ordered session ids, {sid: {field: n}}, {sid: cost})"""
    order, tok, cost = [], defaultdict(lambda: defaultdict(float)), defaultdict(float)
    seen = set()
    for ln in open(path):
        try:
            ev = json.loads(ln)
        except ValueError:
            continue
        sid = ev.get("sessionID")
        if sid and (not order or order[-1] != sid):
            order.append(sid)
        p = ev.get("part") or {}
        t = p.get("tokens")
        psid = p.get("sessionID")
        if isinstance(t, dict) and psid:
            mid = p.get("messageID")
            if mid in seen:            # dedup: case01 §4.4 counted streamed repeats
                continue
            seen.add(mid)
            tok[psid]["input"] += t.get("input", 0) or 0
            tok[psid]["output"] += t.get("output", 0) or 0
            tok[psid]["reasoning"] += t.get("reasoning", 0) or 0
            c = t.get("cache") or {}
            tok[psid]["cache_read"] += c.get("read", 0) or 0
        if ev.get("type") == "step_finish" and isinstance(p.get("cost"), (int, float)):
            cost[psid] += p["cost"]
    return list(OrderedDict.fromkeys(order)), tok, cost


def main():
    cells = {}
    for f in sorted(glob.glob(os.path.join(RAW, "arm?_[rs][0-9].jsonl"))):
        tag = os.path.basename(f)[:-6]
        order, tok, cost = cell_tally(f)
        last = order[-1]
        cells[tag] = {
            "sessions": len(order),
            "completing": {k: tok[last][k] for k in FIELDS},
            "completing_usd": cost[last],
            "consumed": {k: sum(tok[s][k] for s in order) for k in FIELDS},
            "consumed_usd": sum(cost.values()),
        }

    def group(pred):
        g = {"sessions": 0, "completing_usd": 0.0, "consumed_usd": 0.0, "n": 0}
        for k in FIELDS:
            g["c_" + k] = 0.0
            g["x_" + k] = 0.0
        for tag, c in cells.items():
            if not pred(tag):
                continue
            g["n"] += 1
            g["sessions"] += c["sessions"]
            g["completing_usd"] += c["completing_usd"]
            g["consumed_usd"] += c["consumed_usd"]
            for k in FIELDS:
                g["c_" + k] += c["completing"][k]
                g["x_" + k] += c["consumed"][k]
        return g

    A = group(lambda t: t.startswith("armA"))
    B = group(lambda t: t.startswith("armB_r"))
    F = group(lambda t: t.startswith("armB_s"))

    out = []
    out.append("CASE 04 — token cost of Rocq extraction vs direct Rust")
    out.append("INADMISSIBLE as evidence (A-2026-08-26 constraint violation); descriptive only.\n")
    out.append(f"{'cell':<9}{'sess':>5}{'completing tok':>16}{'consumed tok':>14}"
               f"{'disc%':>7}{'compl$':>8}{'cons$':>8}")
    out.append("-" * 67)
    for tag, c in cells.items():
        ct = sum(c["completing"][k] for k in ("input", "output", "reasoning"))
        xt = sum(c["consumed"][k] for k in ("input", "output", "reasoning"))
        disc = 100 * (1 - ct / xt) if xt else 0
        out.append(f"{tag:<9}{c['sessions']:>5}{int(ct):>16,}{int(xt):>14,}"
                   f"{disc:>6.0f}%{c['completing_usd']:>8.2f}{c['consumed_usd']:>8.2f}")

    def line(name, g):
        ct = sum(g["c_" + k] for k in ("input", "output", "reasoning"))
        xt = sum(g["x_" + k] for k in ("input", "output", "reasoning"))
        return (name, g["n"], g["sessions"], ct, xt, g["completing_usd"], g["consumed_usd"],
                g["c_output"], g["c_reasoning"], g["c_cache_read"])

    out.append("\nARM TOTALS")
    out.append(f"{'arm':<26}{'cells':>6}{'sess':>6}{'completing':>14}{'consumed':>14}{'compl$':>9}{'cons$':>8}")
    out.append("-" * 83)
    for nm, g in (("A  Rocq->Rust extraction", A), ("B  direct Rust", B), ("B' flash sweep (exploratory)", F)):
        n, cn, ss, ct, xt, cu, xu, *_ = (nm,) + line(nm, g)[1:]
        out.append(f"{nm:<26}{cn:>6}{ss:>6}{int(ct):>14,}{int(xt):>14,}{cu:>9.2f}{xu:>8.2f}")

    ctA = sum(A["c_" + k] for k in ("input", "output", "reasoning"))
    ctB = sum(B["c_" + k] for k in ("input", "output", "reasoning"))
    xtA = sum(A["x_" + k] for k in ("input", "output", "reasoning"))
    xtB = sum(B["x_" + k] for k in ("input", "output", "reasoning"))
    out.append("\nRATIO A/B (formal-extraction over direct)")
    out.append(f"  COMPLETING tokens : {ctA/ctB:.2f}x        (pre-registered metric)")
    out.append(f"  CONSUMED   tokens : {xtA/xtB:.2f}x        (all attempts)")
    out.append(f"  COMPLETING dollars: {A['completing_usd']/B['completing_usd']:.2f}x")
    out.append(f"  CONSUMED   dollars: {A['consumed_usd']/B['consumed_usd']:.2f}x")
    out.append(f"  restarts per cell : A {A['sessions']/A['n']:.1f}   B {B['sessions']/B['n']:.1f}")
    out.append(f"  discarded token share: A {100*(1-ctA/xtA):.0f}%   B {100*(1-ctB/xtB):.0f}%")
    def med(vals):
        v = sorted(vals); n = len(v)
        return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2
    cA = [sum(c["completing"][k] for k in ("input", "output", "reasoning"))
          for t, c in cells.items() if t.startswith("armA")]
    cB = [sum(c["completing"][k] for k in ("input", "output", "reasoning"))
          for t, c in cells.items() if t.startswith("armB_r")]
    xA = [sum(c["consumed"][k] for k in ("input", "output", "reasoning"))
          for t, c in cells.items() if t.startswith("armA")]
    xB = [sum(c["consumed"][k] for k in ("input", "output", "reasoning"))
          for t, c in cells.items() if t.startswith("armB_r")]
    out.append("\nMEDIAN-OF-CELLS (totals above are outlier-sensitive at n=5)")
    out.append(f"  COMPLETING median A {int(med(cA)):,}  B {int(med(cB)):,}  -> {med(cA)/med(cB):.2f}x")
    out.append(f"  CONSUMED   median A {int(med(xA)):,}  B {int(med(xB)):,}  -> {med(xA)/med(xB):.2f}x")
    out.append("\nCOMPOSITION (completing sessions, share of billed non-cache tokens)")
    for nm, g in (("A extraction", A), ("B direct", B)):
        t = sum(g["c_" + k] for k in ("input", "output", "reasoning"))
        out.append(f"  {nm:<13} input {100*g['c_input']/t:4.1f}%  output {100*g['c_output']/t:4.1f}%"
                   f"  reasoning {100*g['c_reasoning']/t:4.1f}%   cache-read {int(g['c_cache_read']):,}")
    txt = "\n".join(out)
    print(txt)
    dst = os.path.join(os.path.dirname(__file__), "..", "ledger", "extraction_token_cost.txt")
    open(dst, "w").write(txt + "\n")


if __name__ == "__main__":
    main()
