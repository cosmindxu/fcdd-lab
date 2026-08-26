#!/usr/bin/env python3
"""Case 04 — heavy Arm A gate re-verification (A1/A3/A4), post-hoc:
recompile each cell's Rocq tree with the cell's own load-path mapping,
re-run the extraction (the Redirect target), and hash-compare the fresh
extractor output against the shipped crate extracted.rs.

Uses the coq-switch opam environment. Emits a per-cell verdict line.
"""
import argparse
import glob
import hashlib
import os
import re
import subprocess
import sys

BASE = os.path.expanduser("~/fcdd_c04_scored")
LAB = "/media/sf_Projects/fcdd_lab/case04_coq_rust"


def run_env(cmd, cwd, timeout=1200):
    env = dict(os.environ)
    r = subprocess.run(["bash", "-lc",
                        'eval "$(opam env --switch=coq-switch 2>/dev/null)"; '
                        + cmd],
                       capture_output=True, text=True, cwd=cwd,
                       timeout=timeout, env=env)
    return r


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def verify(tag):
    ws = os.path.join(BASE, tag + "_build", "armA")
    vs = [v for v in glob.glob(os.path.join(ws, "**", "*.v"),
                               recursive=True)
          if "/_build" not in v and "/target" not in v]
    # the file that carries the Redirect (extraction trigger)
    redirect_file = None
    redirect_line = None
    for v in vs:
        for line in open(v, errors="replace"):
            if "Redirect" in line and "Rust Extract" in line:
                redirect_file = v
                redirect_line = line.strip()
    if not redirect_file:
        return "%s: NO Redirect/Rust Extract found (files: %s)" % (
            tag, ", ".join(os.path.basename(v) for v in vs))

    # replay: compile every .v with the dir-local -Q mapping, extraction last
    d = os.path.dirname(redirect_file)
    results = []
    for v in sorted(set(vs) - {redirect_file}):
        rel = os.path.basename(v)
        r = run_env("rocq compile -Q . \"\" %s 2>&1" % rel, d)
        ok = (r.returncode == 0)
        results.append("compile %s: %s" % (rel, "OK" if ok
                                           else r.stderr[-160:].strip()
                                           or "rc=%d" % r.returncode))
    r = run_env("rocq compile -Q . \"\" %s 2>&1" % os.path.basename(redirect_file), d)
    ok = (r.returncode == 0)
    if not ok:
        results.append("extract-file compile: FAIL %s"
                       % (r.stderr[-200:].strip() or "rc=%d" % r.returncode))
        return "%s: %s" % (tag, " | ".join(results))

    # locate the fresh extractor output (.rs or .rs.out in the tree)
    outs = glob.glob(os.path.join(ws, "**", "*.rs.out"), recursive=True) + \
        [f for f in glob.glob(os.path.join(ws, "**", "*.rs"), recursive=True)
         if "/target/" not in f and "src/extracted.rs" not in f
         and not f.endswith("main.rs")]
    # newest .rs.out is the one we just made
    fresh = None
    for f in outs:
        if fresh is None or os.path.getmtime(f) > os.path.getmtime(fresh):
            fresh = f
    if fresh is None:
        return "%s: %s | no extractor output produced" % (tag, " | ".join(results))

    shipped = os.path.join(ws, "src", "extracted.rs")
    alt_shipped = glob.glob(os.path.join(ws, "**", "extracted.rs"),
                            recursive=True)
    shipped = shipped if os.path.isfile(shipped) else (alt_shipped[0]
                                                        if alt_shipped else None)
    if not shipped:
        return "%s: shipped extracted.rs not found" % tag
    match = sha(fresh) == sha(shipped)
    return ("%s: %s | re-extraction %s -> hash vs shipped %s %s"
            % (tag, " | ".join(results), os.path.relpath(fresh, ws),
               os.path.relpath(shipped, ws),
               "MATCH" if match else "MISMATCH"))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("tags", nargs="*")
    args = ap.parse_args(argv)
    tags = args.tags or ["armA_r1", "armA_r2", "armA_r3", "armA_r4", "armA_r5"]
    for t in tags:
        print(verify(t), flush=True)


if __name__ == "__main__":
    main()
