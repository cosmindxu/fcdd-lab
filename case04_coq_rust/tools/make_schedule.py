#!/usr/bin/env python3
"""Case 04 — scored-phase schedule. k runs per arm, randomised across the
whole 2k-run schedule under a committed seed, so service drift cannot align
with arm (case02 §2 pattern). Committed before the first scored run."""
import argparse
import json
import random


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--k-sweep", type=int, default=3,
                    help="Arm B exploratory model-sweep runs (flash, D7)")
    ap.add_argument("--seed", type=int, default=20260807)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    rng = random.Random(args.seed)
    cells = [{"arm": "A", "run": i, "model": "deepseek/deepseek-v4-pro"}
             for i in range(1, args.k + 1)] + \
            [{"arm": "B", "run": i, "model": "deepseek/deepseek-v4-pro"}
             for i in range(1, args.k + 1)] + \
            [{"arm": "B", "run": i, "model": "deepseek/deepseek-v4-flash",
              "sweep": True, "tag_override": "armB_s%d" % i}
             for i in range(1, args.k_sweep + 1)]
    rng.shuffle(cells)
    for i, c in enumerate(cells, 1):
        c["cell"] = i
        c["tag"] = c.get("tag_override") or "arm%s_r%d" % (c["arm"], c["run"])
        c.pop("tag_override", None)
    json.dump({"k": args.k, "k_sweep": args.k_sweep, "seed": args.seed,
               "cells": cells}, open(args.out, "w"), indent=1)
    print("schedule: %d cells (primary %d + sweep %d), seed %d -> %s"
          % (len(cells), 2 * args.k, args.k_sweep, args.seed, args.out))
    for c in cells:
        print("  cell %2d  %s  %s%s" % (c["cell"], c["tag"], c["model"],
                                        "  [sweep]" if c.get("sweep") else ""))


if __name__ == "__main__":
    main()
