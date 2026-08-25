#!/usr/bin/env python3
"""Case 04 — workspace builder. Assembles the two arm workspaces, then runs
the C1 controls:
  - parity_assert.py: the two workspaces must be byte-identical except
    PROMPT.md (the treatment lives in one file, nothing else);
  - workspace_manifest_guard.py: nothing hash-matches sealed material.

Workspace content (identical in both arms):
  PROMPT.md            (differs by arm — the treatment)
  IFACE.md             the deliverable contract
  ORACLE.md            how to query the reference engine
  reference/           Contract.lean (case01 kernel-checked rules contract)
  smoke/               public smoke set (50 positions + answers)
  skeleton/            the crate to fill in (fixed API)
  tools/oracle_cli.py  the query budget CLI (arm-facing wrapper)

Usage:  build_workspace.py <target_dir> [--ledger DIR]
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
WS = os.path.join(LAB, "workspace")
CASE03 = os.path.join(os.path.dirname(LAB), "case03")
CASE01 = os.path.join(os.path.dirname(LAB), "case01_spectrum_gambit")

ARM = {"armA": "armA_PROMPT.md", "armB": "armB_PROMPT.md"}


def copy_common(dst):
    for name in ("IFACE.md", "ORACLE.md", "opencode.jsonc", "smoke",
                 "skeleton"):
        src = os.path.join(WS, name)
        tgt = os.path.join(dst, name)
        if os.path.isdir(src):
            shutil.copytree(src, tgt, dirs_exist_ok=True)
        else:
            shutil.copy2(src, tgt)
    os.makedirs(os.path.join(dst, "tools"), exist_ok=True)
    shutil.copy2(os.path.join(LAB, "tools", "oracle_cli.py"),
                 os.path.join(dst, "tools", "oracle_cli.py"))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("target_dir")
    ap.add_argument("--ledger", default=os.path.join(LAB, "ledger"))
    args = ap.parse_args(argv)

    ws_a = os.path.join(args.target_dir, "armA")
    ws_b = os.path.join(args.target_dir, "armB")
    for ws, arm in ((ws_a, "armA"), (ws_b, "armB")):
        shutil.rmtree(ws, ignore_errors=True)
        os.makedirs(ws)
        copy_common(ws)
        shutil.copy2(os.path.join(WS, "prompts", ARM[arm]),
                     os.path.join(ws, "PROMPT.md"))

    r = subprocess.run([sys.executable,
                        os.path.join(CASE03, "tools", "parity_assert.py"),
                        ws_a, ws_b, "--allow", "PROMPT.md"])
    if r.returncode != 0:
        print("PARITY ASSERTION FAILED — workspaces differ beyond PROMPT.md")
        return r.returncode
    print("parity: OK (workspaces identical except PROMPT.md)")

    # manifest: per-arm inventory with sha256 (the guard needs it)
    def sha(p):
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for c in iter(lambda: f.read(1 << 16), b""):
                h.update(c)
        return h.hexdigest()

    def inventory(root):
        out = {}
        for dp, dn, fs in os.walk(root):
            dn[:] = [d for d in dn if d not in ("__pycache__", ".git")]
            for f in fs:
                p = os.path.join(dp, f)
                out[os.path.relpath(p, root)] = sha(p)
        return out

    manifest = {"arms": {"armA": inventory(ws_a), "armB": inventory(ws_b)},
                "intentionally_shared": []}
    manifest_path = os.path.join(args.target_dir, "manifest.json")
    json.dump(manifest, open(manifest_path, "w"), indent=1)
    for ws, arm in ((ws_a, "armA"), (ws_b, "armB")):
        r = subprocess.run([sys.executable,
                            os.path.join(CASE03, "tools",
                                         "workspace_manifest_guard.py"),
                            ws, arm, manifest_path,
                            os.path.join(CASE01, "sealed")])
        if r.returncode != 0:
            print("MANIFEST GUARD FAILED for %s" % ws)
            return r.returncode
    print("manifest guard: OK (no sealed material in either workspace)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
