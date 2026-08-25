#!/usr/bin/env python3
"""Case 04 — C3 model-pin assertion. Reads a result JSON's modelUsage and
fails unless every model present is on the pinned allow-list."""
import argparse
import json
import sys

PINNED = {"claude-opus-5"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("result_json")
    args = ap.parse_args(argv)
    try:
        d = json.load(open(args.result_json))
    except Exception:
        print("MODEL PIN: UNREADABLE — treat as mismatch")
        return 1
    usage = d.get("modelUsage") or {}
    bad = {m for m in usage if m not in PINNED}
    if bad:
        print("MODEL PIN: MISMATCH — unexpected models in modelUsage: %s"
              % sorted(bad))
        return 1
    if not usage:
        print("MODEL PIN: no modelUsage block (is_error run?)")
        return 1
    spend = {m: usage[m].get("costUSD", 0) for m in usage}
    print("MODEL PIN: OK — %s" % spend)
    return 0


if __name__ == "__main__":
    sys.exit(main())
