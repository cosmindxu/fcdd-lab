#!/usr/bin/env python3
"""Case 04 — full P1: oracle self-consistency on a 1,000-position sample,
parallelised across cores (each probe boots its own emulator process)."""
import argparse
import json
import multiprocessing as mp
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from oracle_cli import probe_legal  # noqa: E402


def check_entry(e):
    a = probe_legal(e["fen"], e["path"], False)
    b = probe_legal(e["fen"], e["path"], False)
    if a is None or b is None or "error" in a or "error" in b:
        return ("unj", e["ply"], (a or b or {}).get("error", "?"))
    if a["legal"] == b["legal"] and a["status"] == b["status"]:
        return ("agree", e["ply"], None)
    return ("diff", e["ply"], (set(a["legal"]) ^ set(b["legal"])))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("corpus")
    ap.add_argument("--jobs", type=int, default=16)
    args = ap.parse_args(argv)

    data = json.load(open(args.corpus))
    entries = data["entries"][:1000]
    t0 = time.time()
    with mp.Pool(args.jobs) as pool:
        results = pool.map(check_entry, entries)
    dt = time.time() - t0
    counts = {"agree": 0, "diff": 0, "unj": 0}
    for kind, ply, extra in results:
        counts[kind] += 1
        if kind != "agree" and counts[kind] <= 10:
            print("  %s ply=%d %r" % (kind, ply, list(extra)[:3] if extra else ""))
    n = len(entries)
    print("entries=%d  self-consistent=%d (%.2f%%)  inconsistent=%d  "
          "unjudgeable=%d" % (n, counts["agree"], 100.0 * counts["agree"] / n,
                              counts["diff"], counts["unj"]))
    print("wall %.1fs  probes/s %.2f  (jobs=%d, two probes per entry)"
          % (dt, 2 * n / dt, args.jobs))


if __name__ == "__main__":
    main()
