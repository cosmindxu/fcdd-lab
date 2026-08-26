#!/usr/bin/env python3
"""Case 04 — one scoring shard: runs score_case04's rules+policy scoring
on the K-th slice (of N) of the sealed corpus. Leaves the frozen scorer
untouched; merge_score.py combines the shard outputs."""
import argparse
import json
import sys

sys.path.insert(0, "/media/sf_Projects/fcdd_lab/case04_coq_rust/tools")
from score_case04 import score_rules, score_policy  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--binary", required=True)
    ap.add_argument("--sealed", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--shard", required=True,
                    help="K/N, e.g. 3/8 (1-based K)")
    args = ap.parse_args(argv)
    k, n = (int(x) for x in args.shard.split("/"))
    sealed = json.load(open(args.sealed))
    rules = sealed["rules"][k - 1::n]
    policy = sealed["policy"][k - 1::n]
    result = {
        "primary": score_policy(args.binary, policy),
        "rules": score_rules(args.binary, rules),
        "shard": [k, n],
    }
    json.dump(result, open(args.out, "w"), indent=1)
    print("%s/%s done: policy n=%d mu2=%s rules n=%d"
          % (k, n, result["primary"]["n"], result["primary"]["mu2"],
             result["rules"]["n"]))


if __name__ == "__main__":
    main()
