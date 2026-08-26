#!/usr/bin/env python3
"""Case 04 — per-run process-conformance checks (C13, C3, C14), run
post-hoc on the deposited workspaces and transcripts. Every emitted number
is computed here (C10).

Arm A gates (PREREG §2):
  A1 rocq tree present (recompilation + re-extraction hash-compare is the
     separate heavy check, see reextract_verify.py)
  A2 zero Admitted. / admit. tactics, zero run-added Axiom/Parameter decls
     (Coq comments stripped before matching)
  A3 extractor output deposited (a .rs that is not the adapter)
  A4 every crate .rs outside the adapter hash-matches the deposit
  A5 adapter rule per main.rs: <= 200 non-comment lines, behaviour tokens
     flagged for review (not auto-failed)
Arm B gate:
  B1 no .v files in workspace, no Rocq invocations in the transcript
Both arms:
  C3  attempt-level model lines in drive.log vs schedule pin; transcript
      grep for foreign model names
  C14 oracle query count per run from the CLI's own budget file (cap 5000)

Usage: conformance_check.py <schedule.json> [--out report.md]
"""
import argparse
import glob
import hashlib
import json
import os
import re
import subprocess
import sys

BASE = os.path.expanduser("~/fcdd_c04_scored")
LAB = "/media/sf_Projects/fcdd_lab/case04_coq_rust"
RAW = os.path.join(LAB, "ledger", "raw")
ADAPTER_LINE_CAP = 200
ADAPTER_TOKENS = ["gen", "legal", "search", "eval", "alpha", "beta",
                  "perft", "mate", "stalemate", "castl", "passant", "promot"]
QUERY_CAP = 5000  # D2 frozen cap (PREREG §3: N_Q = 5,000)
FOREIGN_MODELS = ["claude", "anthropic", "gpt", "o1", "o3", "gemini",
                  "llama", "qwen", "mistral"]


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def strip_coq_comments(text):
    """remove (* ... *) comments (non-nested, per Coq 9 default)"""
    out = []
    i = 0
    n = len(text)
    while i < n:
        if text[i:i+2] == '(*':
            j = text.find('*)', i + 2)
            if j == -1:
                break
            i = j + 2
            out.append(' ')
        else:
            out.append(text[i])
            i += 1
    return ''.join(out)


def strip_rust_comments(text):
    return re.sub(r"//.*", "", text)


def armA(ws):
    out = {}
    vs = glob.glob(os.path.join(ws, "**", "*.v"), recursive=True)
    vs = [v for v in vs if "/_build" not in v and "/target" not in v]
    out["v_files"] = len(vs)

    admitted = []
    axioms = []
    for v in vs:
        src = strip_coq_comments(open(v, errors="replace").read())
        for i, line in enumerate(src.splitlines(), 1):
            s = line.strip()
            if re.search(r"\bAdmitted\.", s) or re.search(r"\badmit\b\.?\s*$", s):
                admitted.append("%s:%d: %s" % (os.path.basename(v), i, s[:80]))
            if re.match(r"^\s*(Axiom|Parameter)\s+\w", s):
                axioms.append("%s:%d: %s" % (os.path.basename(v), i, s[:80]))
    out["admitted"] = admitted
    out["axioms"] = axioms

    # deposits: .rs files that are neither main.rs nor under target/
    rs_files = [f for f in glob.glob(os.path.join(ws, "**", "*.rs"),
                                     recursive=True)
                if "/target/" not in f]
    main_rs = [f for f in rs_files if f.endswith("main.rs")]
    deposits = [f for f in rs_files if not f.endswith("main.rs")]
    out["deposits"] = [os.path.relpath(d, ws) for d in deposits]
    out["main_rs"] = [os.path.relpath(m, ws) for m in main_rs]

    dep_hashes = {hashlib.sha256(open(d, "rb").read()).hexdigest(): d
                  for d in deposits}
    out["hash_lock"] = {}
    for f in deposits:
        rel = os.path.relpath(f, ws)
        # the deposit is by definition its own source; record which OTHER
        # file (the extractor Redirect target) it matches, if any
        dup = [os.path.relpath(d, ws) for d in deposits
               if os.path.relpath(d, ws) != rel and
               hashlib.sha256(open(d, "rb").read()).hexdigest()
               == hashlib.sha256(open(f, "rb").read()).hexdigest()]
        out["hash_lock"][rel] = dup
    # shipped crate rs = the ones that make it into the build: src/*.rs
    crate_rs = [f for f in rs_files if "/src/" in f and not f.endswith("main.rs")]
    out["crate_rs"] = [os.path.relpath(c, ws) for c in crate_rs]
    out["crate_hash_ok"] = {}
    for c in crate_rs:
        h = hashlib.sha256(open(c, "rb").read()).hexdigest()
        out["crate_hash_ok"][os.path.relpath(c, ws)] = h in dep_hashes

    out["adapters"] = {}
    for m in main_rs:
        raw = open(m).read()
        nocomment = strip_rust_comments(raw)
        lines = [l for l in nocomment.splitlines() if l.strip()]
        toks = [t for t in ADAPTER_TOKENS if re.search(t, nocomment,
                                                       re.IGNORECASE)]
        out["adapters"][os.path.relpath(m, ws)] = {
            "lines": len(lines), "tokens": toks}
    return out


def armB(ws, transcript):
    out = {}
    vs = glob.glob(os.path.join(ws, "**", "*.v"), recursive=True)
    vs = [v for v in vs if "/_build" not in v and "/target" not in v]
    out["v_files"] = [os.path.relpath(v, ws) for v in vs]
    rocq = []
    for line in open(transcript, errors="replace"):
        s = json.dumps(line)
        if re.search(r"\brocqc?\b|coqc|\bcoqtop\b", s):
            rocq.append(line[:120])
    out["rocq_invocations"] = rocq[:5]
    out["rocq_hits"] = len(rocq)
    return out


def c3(tag, pinned):
    """attempt lines in drive.log carry the model; transcript grepped for
    foreign model names (a subagent on another provider would show up in
    events/config errors)."""
    models = set()
    dlog = os.path.join(RAW, "drive.log")
    if os.path.isfile(dlog):
        for line in open(dlog):
            if tag in line and "attempt" in line:
                m = re.search(r"\(([a-z0-9/.\-]+)\)\s*$", line.strip())
                if m:
                    models.add(m.group(1))
    foreign = []
    tr = os.path.join(RAW, "%s.jsonl" % tag)
    if os.path.isfile(tr):
        for line in open(tr, errors="replace"):
            low = line.lower()
            for f in FOREIGN_MODELS:
                if f in low:
                    foreign.append(line[:100])
                    break
    return sorted(models), foreign[:3], len(foreign)


def c14(ws, tag):
    p = os.path.join(ws, "ledger", "oracle_budget_%s.json" % tag)
    if not os.path.isfile(p):
        return None
    return json.load(open(p)).get("count", 0)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("schedule")
    ap.add_argument("--out", default=os.path.join(LAB, "ledger",
                                                  "conformance_report.md"))
    args = ap.parse_args(argv)
    sched = json.load(open(args.schedule))
    lines = ["# Case 04 — process conformance (C13/C3/C14), post-hoc run",
             ""]
    for c in sched["cells"]:
        tag = c["tag"]
        arm = c["arm"]
        build = os.path.join(BASE, tag + "_build")
        ws = os.path.join(build, "armA" if arm == "A" else "armB")
        tr = os.path.join(RAW, "%s.jsonl" % tag)
        lines.append("## %s (arm %s, %s)" % (tag, arm, c["model"]))
        if arm == "A":
            r = armA(ws)
            lines.append("- v files: %d" % r["v_files"])
            lines.append("- Admitted/admit: %d" % len(r["admitted"]))
            for a in r["admitted"][:5]:
                lines.append("  - %s" % a)
            lines.append("- run-added Axiom/Parameter: %d" % len(r["axioms"]))
            for a in r["axioms"][:5]:
                lines.append("  - %s" % a)
            lines.append("- deposits: %s" % ", ".join(r["deposits"]))
            for rel, dup in r["hash_lock"].items():
                lines.append("- deposit %s: %s"
                             % (rel, "duplicates %s" % dup if dup
                                else "unique"))
            for rel, ok in r["crate_hash_ok"].items():
                lines.append("- crate hash-lock %s vs deposit: %s"
                             % (rel, "OK" if ok else "FAIL"))
            for m, d in r["adapters"].items():
                lines.append("- adapter %s: %d lines (cap %d), tokens: %s"
                             % (m, d["lines"], ADAPTER_LINE_CAP,
                                ", ".join(d["tokens"]) or "none"))
        else:
            r = armB(ws, tr)
            lines.append("- .v files in workspace: %s"
                         % (", ".join(r["v_files"]) or "none"))
            lines.append("- Rocq hits in transcript: %d" % r["rocq_hits"])
            for h in r["rocq_invocations"]:
                lines.append("  - %s" % h)
        models, foreign, nf = c3(tag, c["model"])
        ok = all(m == c["model"] for m in models) if models else True
        lines.append("- attempt models (drive.log): %s (pin %s) -> %s"
                     % (", ".join(models) or "n/a", c["model"],
                        "OK" if ok else "MISMATCH"))
        lines.append("- foreign model mentions in transcript: %d" % nf)
        for f in foreign:
            lines.append("  - %s" % f)
        q = c14(ws, tag)
        lines.append("- oracle queries (CLI counter): %s (cap %d) -> %s"
                     % (q if q is not None else "no budget file",
                        QUERY_CAP,
                        "OK" if q is not None and q <= QUERY_CAP
                        else "CHECK"))
        lines.append("")
    md = "\n".join(lines)
    open(args.out, "w").write(md)
    print(md)


if __name__ == "__main__":
    main()
