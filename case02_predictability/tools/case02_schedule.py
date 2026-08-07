#!/usr/bin/env python3
"""Randomised run schedule for case02. Seed frozen in PREREGISTRATION.md (20260807).

Order is randomised across the whole 56-run schedule so that any drift in
service quality over the study cannot align with arm.
"""
import random, json, sys
SEED = 20260807
BUGS = ["bug%02d" % i for i in range(1, 8)]
ARMS = ["A", "B"]
K = 4

def schedule():
    cells = [(b, a, r) for b in BUGS for a in ARMS for r in range(1, K + 1)]
    rng = random.Random(SEED)
    rng.shuffle(cells)
    return cells

if __name__ == "__main__":
    s = schedule()
    assert len(s) == len(BUGS) * len(ARMS) * K == 56
    for b in BUGS:
        for a in ARMS:
            assert sum(1 for x in s if x[0] == b and x[1] == a) == K
    if "--json" in sys.argv:
        print(json.dumps([{"bug": b, "arm": a, "run": r} for b, a, r in s], indent=1))
    else:
        for i, (b, a, r) in enumerate(s, 1):
            print("%2d  %s  arm%s  r%d" % (i, b, a, r))
