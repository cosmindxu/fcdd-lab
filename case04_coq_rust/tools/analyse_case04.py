#!/usr/bin/env python3
"""Case 04 — primary analysis (FREEZE CANDIDATE; finalised at P5).

Reads per-run summaries and computes every pre-registered outcome:

  H1 primary   two-sided exact two-group permutation on mu1 (all C(2k,k)
               arm-label assignments), alpha = 0.05;
  interval     bootstrap CI (seed 20260807, B=100000) on the mean
               difference A - B;
  co-primary   completion per arm; H1 supported only if Arm A's completion
               is non-inferior within ONE run;
  H2 cost      exact permutation on per-run cost (dollars, modelUsage
               total), median ratio, dispersion sd(ln cost) per arm
               (scale-free; case02's CV_log defect, A14, is not repeated);
  H3 policy    exact permutation on mu2 (secondary);
  gate         uninformativeness: pooled mu1 outside [LO, HI] declares the
               study UNINFORMATIVE — a benchmark failure, not a finding.

A non-delivering run scores mu1 = 1 (PREREGISTRATION §5).
Multiplicity: four pre-registered outcomes, tests specified in advance,
no correction applied (stated in the report, not applied here).

PILOT VALUES (replaced at freeze from P4 measurements): MU1_LO, MU1_HI,
TIMEOUT-adjacent constants live in the scorer, not here.
"""
import argparse
import json
import math
import random
import statistics as st
from itertools import combinations

MU2_LO = 0.02    # FROZEN 2026-08-25: below this the policy task is trivial
MU2_HI = 0.95    # FROZEN 2026-08-25: above this the policy task is impossible
SEED = 20260807
ALPHA = 0.05


def perm_two_group(vals_a, vals_b):
    """Two-sided exact two-group permutation p: all C(n,m) label splits."""
    n, m = len(vals_a), len(vals_b)
    allv = vals_a + vals_b
    obs = st.mean(vals_a) - st.mean(vals_b)
    worse = 0
    for idx in combinations(range(n + m), n):
        idx = set(idx)
        ma = st.mean(v for i, v in enumerate(allv) if i in idx)
        mb = st.mean(v for i, v in enumerate(allv) if i not in idx)
        if abs(ma - mb) >= abs(obs) - 1e-12:
            worse += 1
    return worse / math.comb(n + m, n)


def bootstrap_ci(vals_a, vals_b, b=100000, seed=SEED):
    rng = random.Random(seed)
    diffs = []
    for _ in range(b):
        sa = [rng.choice(vals_a) for _ in vals_a]
        sb = [rng.choice(vals_b) for _ in vals_b]
        diffs.append(st.mean(sa) - st.mean(sb))
    diffs.sort()
    return diffs[int(0.025 * b)], diffs[int(0.975 * b)]


def sd_ln(costs):
    if len(costs) < 2:
        return None
    ln = [math.log(c) for c in costs]
    m = st.mean(ln)
    return math.sqrt(sum((x - m) ** 2 for x in ln) / (len(ln) - 1))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("runs_json")
    args = ap.parse_args(argv)
    runs = json.load(open(args.runs_json))

    def arm(which):
        return [r for r in runs if r["arm"] == which]

    a, b = arm("A"), arm("B")
    # D12: the primary is POLICY agreement (mu2); rules (mu1) is the
    # co-requisite. A non-delivering run scores mu2 = 1.
    mu_a = [r.get("mu2", 1.0) for r in a]
    mu_b = [r.get("mu2", 1.0) for r in b]
    print("=== H1 primary: policy disagreement mass mu2 (choose vs engine) ===")
    print("armA mu2:", ["%.4f" % x for x in mu_a])
    print("armB mu2:", ["%.4f" % x for x in mu_b])
    print("mean A=%.4f  mean B=%.4f  diff(A-B)=%+.4f"
          % (st.mean(mu_a), st.mean(mu_b), st.mean(mu_a) - st.mean(mu_b)))
    p = perm_two_group(mu_a, mu_b)
    floor = 2 / math.comb(len(mu_a) + len(mu_b), len(mu_a))
    lo, hi = bootstrap_ci(mu_a, mu_b)
    print("exact two-sided p = %.4f (floor %.4f)   bootstrap CI [%+.4f, %+.4f]"
          % (p, floor, lo, hi))
    print("H1 verdict:", "SUPPORTED" if p < ALPHA and st.mean(mu_a) < st.mean(mu_b)
          else "NOT SUPPORTED")

    print("\n=== co-primary: completion ===")
    ca = sum(1 for r in a if r.get("completion", True)) / len(a)
    cb = sum(1 for r in b if r.get("completion", True)) / len(b)
    print("armA completion %.2f  armB completion %.2f" % (ca, cb))

    print("\n=== H2: cost ===")
    cost_a = [r.get("cost_usd") for r in a if r.get("cost_usd")]
    cost_b = [r.get("cost_usd") for r in b if r.get("cost_usd")]
    if cost_a and cost_b:
        print("armA costs:", ["%.2f" % x for x in cost_a])
        print("armB costs:", ["%.2f" % x for x in cost_b])
        print("median ratio B/A = %.2f  exact p = %.4f"
              % (st.median(cost_b) / st.median(cost_a),
                 perm_two_group(cost_a, cost_b)))
        da, db = sd_ln(cost_a), sd_ln(cost_b)
        if da is not None and db is not None:
            print("dispersion sd(ln cost): A=%.3f B=%.3f" % (da, db))

    print("\n=== H3: policy layer mu2 (secondary) ===")
    m2a = [r.get("mu2") for r in a if r.get("mu2") is not None]
    m2b = [r.get("mu2") for r in b if r.get("mu2") is not None]
    if m2a and m2b:
        print("armA mu2:", ["%.4f" % x for x in m2a])
        print("armB mu2:", ["%.4f" % x for x in m2b])
        print("exact p = %.4f" % perm_two_group(m2a, m2b))

    print("\n=== uninformativeness gate (D12: on mu2) ===")
    pooled = mu_a + mu_b
    print("pooled mu2 mean = %.4f" % st.mean(pooled))
    if not (MU2_LO <= st.mean(pooled) <= MU2_HI):
        print("UNINFORMATIVE — benchmark failure, not a finding")
    else:
        print("gate: informative")


if __name__ == "__main__":
    main()
