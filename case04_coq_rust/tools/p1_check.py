#!/usr/bin/env python3
"""Case 04 — P1/P2 pilot: oracle self-consistency + throughput.

For each corpus entry: replay the path through the live oracle TWICE
(independent emulator invocations) and compare the legal set and status.
Self-inconsistent entries are excluded by rule (C16); the exclusion
statistics are the deliverable. Also reports probes/second.
"""
import argparse
import json
import subprocess
import sys
import time

HERE = os_path = None  # noqa
import os
HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "oracle_cli.py")


def probe(fen, path):
    cmd = [sys.executable, CLI, "--run-id", "p1check", "--internal",
           "legal", "--fen", fen, "--path", ",".join(path)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    if r.returncode != 0:
        return None
    return json.loads(r.stdout)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("corpus")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args(argv)

    data = json.load(open(args.corpus))
    entries = data["entries"][:args.limit] if args.limit else data["entries"]
    agree = disagree = unjudgeable = 0
    exclusions = []
    t0 = time.time()
    for i, e in enumerate(entries):
        a = probe(e["fen"], e["path"])
        b = probe(e["fen"], e["path"])
        if a is None or b is None or "error" in a or "error" in b:
            unjudgeable += 1
            exclusions.append((e["ply"], "unjudgeable",
                               (a or b or {}).get("error", "?")))
            continue
        if (a["legal"] == b["legal"] and a["status"] == b["status"]):
            agree += 1
        else:
            disagree += 1
            exclusions.append((e["ply"], "inconsistent",
                               (set(a["legal"]) ^ set(b["legal"]))))
        if (i + 1) % 25 == 0:
            print("  %4d/%d  agree=%d disagree=%d unj=%d (%.1f/s)"
                  % (i + 1, len(entries), agree, disagree, unjudgeable,
                     (i + 1) / (time.time() - t0)), flush=True)
    dt = time.time() - t0
    print("entries=%d  self-consistent=%d (%.2f%%)  inconsistent=%d "
          "unjudgeable=%d" % (len(entries), agree,
                              100.0 * agree / max(1, len(entries)),
                              disagree, unjudgeable))
    print("throughput: %.2f probes/s (two probes per entry)"
          % (2 * len(entries) / dt))
    for ply, why, extra in exclusions[:10]:
        print("  excluded: ply=%d %s %r" % (ply, why, list(extra)[:3]))


if __name__ == "__main__":
    main()
