#!/usr/bin/env python3
"""Case 04 — merge scoring shards into the full per-run result JSON
(same shape as score_case04.py --out). mu2 = 1 - sum(agree)/sum(n);
mu1 = sum(legalDiv+statusDiv)/sum(n)."""
import argparse
import json
import os


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("shards", nargs="+")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    n2 = agree = 0
    rn = 0
    legal_div = status_div = timeouts = parse_fail = 0
    for p in args.shards:
        d = json.load(open(p))
        pr = d["primary"]
        n2 += pr["n"]
        agree += pr["agree"]
        r = d["rules"]
        rn += r["n"]
        legal_div += r["legalDiv"]
        status_div += r["statusDiv"]
        timeouts += r["timeouts"]
        parse_fail += r["statusParseFail"]
    mu2 = 1 - agree / n2 if n2 else None
    mu1 = (legal_div + status_div) / rn if rn else None
    result = {
        "primary": {"mu2": mu2, "n": n2, "agree": agree},
        "rules": {"n": rn, "mu1": mu1,
                  "legalDiv": legal_div, "statusDiv": status_div,
                  "timeouts": timeouts, "statusParseFail": parse_fail,
                  "moveMass": None, "moveMassSym": None},
    }
    json.dump(result, open(args.out, "w"), indent=1)
    print("merged %d shards -> %s (n=%d, mu2=%s, mu1=%s)"
          % (len(args.shards), args.out, n2, mu2, mu1))


if __name__ == "__main__":
    main()
