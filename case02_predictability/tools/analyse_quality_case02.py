#!/usr/bin/env python3
"""Case02 §5 quality — unblind and analyse the blinded grading.

Reads grading/VERDICT_<pair>.json (grader output, blind) and KEY_<pair>.json
(the sealed mapping), joins them, and reports:

  * per-axis scores by ARM, paired within packet;
  * overall preference counts;
  * an ORDER-EFFECT check (does Submission X get preferred regardless of arm?),
    which the counterbalancing exists to make measurable;
  * the primary paired test aggregated to DEFECT level, matching the study's
    own unit of pairing (§2: "the pairing is by defect, not by run index"),
    rather than treating 28 nested packets as independent;
  * the blinding manipulation check, reported whichever way it falls.

§5: "Under-powered by construction; reported with its interval and no claim."
"""
import glob, json, math, os, statistics as st
from itertools import product

C2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G  = os.path.join(C2, "grading")
AXES = ["correctness_risk", "minimality", "clarity"]

def load():
    rows = []
    for vf in sorted(glob.glob(os.path.join(G, "VERDICT_*.json"))):
        pair = os.path.basename(vf)[len("VERDICT_"):-len(".json")]
        kf = os.path.join(G, "KEY_%s.json" % pair)
        if not os.path.exists(kf): continue
        v, k = json.load(open(vf)), json.load(open(kf))
        arm_of = {"X": k["X"], "Y": k["Y"]}
        r = {"pair": pair, "bug": k["bug"], "run": k["run"], "Xarm": k["X"]}
        for lab in ("X", "Y"):
            for ax in AXES:
                r["%s_%s" % (arm_of[lab], ax)] = v[lab][ax]
        w = v["which_is_better_overall"]
        r["pref_arm"] = "tie" if w == "tie" else arm_of[w]
        r["pref_pos"] = w
        rows.append(r)
    return rows

def exact_paired_permutation(diffs):
    n = len(diffs); obs = st.mean(diffs)
    hits = sum(1 for s in product([1, -1], repeat=n)
               if abs(st.mean([x * d for x, d in zip(s, diffs)])) >= abs(obs) - 1e-12)
    return hits / 2 ** n

def sign_test(k, n):
    return sum(math.comb(n, i) for i in range(n + 1)
               if abs(i - n / 2) >= abs(k - n / 2)) / 2 ** n if n else 1.0

if __name__ == "__main__":
    rows = load()
    print("verdicts joined to keys: %d / 28\n" % len(rows))
    if not rows: raise SystemExit("no verdicts yet")

    print("=== per-axis mean score by arm (1-5, higher is better) ===")
    print("%-18s %8s %8s %9s" % ("axis", "arm A", "arm B", "B - A"))
    for ax in AXES:
        a = [r["A_" + ax] for r in rows]; b = [r["B_" + ax] for r in rows]
        print("%-18s %8.2f %8.2f %+9.2f" % (ax, st.mean(a), st.mean(b), st.mean(b) - st.mean(a)))

    print("\n=== overall preference (28 packets) ===")
    c = {x: sum(1 for r in rows if r["pref_arm"] == x) for x in ("A", "B", "tie")}
    print("  arm A preferred: %d    arm B preferred: %d    tie: %d" % (c["A"], c["B"], c["tie"]))
    dec = c["A"] + c["B"]
    if dec: print("  sign test over decided packets: two-sided p = %.4f" % sign_test(c["B"], dec))

    print("\n=== ORDER EFFECT (what counterbalancing is for) ===")
    px = sum(1 for r in rows if r["pref_pos"] == "X"); py = sum(1 for r in rows if r["pref_pos"] == "Y")
    print("  Submission X preferred: %d    Submission Y preferred: %d    tie: %d" % (px, py, len(rows) - px - py))
    if px + py: print("  position bias sign test: two-sided p = %.4f" % sign_test(px, px + py))

    print("\n=== primary: paired at DEFECT level (§2 pairs by defect) ===")
    bugs = sorted({r["bug"] for r in rows})
    print("%-7s %s" % ("defect", "  ".join("%s B-A" % ax[:6] for ax in AXES)))
    per_axis_diffs = {ax: [] for ax in AXES}
    for bug in bugs:
        sub = [r for r in rows if r["bug"] == bug]
        line = []
        for ax in AXES:
            d = st.mean([r["B_" + ax] for r in sub]) - st.mean([r["A_" + ax] for r in sub])
            per_axis_diffs[ax].append(d); line.append("%+9.2f" % d)
        print("%-7s %s   (n=%d)" % (bug, " ".join(line), len(sub)))
    print()
    for ax in AXES:
        d = per_axis_diffs[ax]
        if len(d) >= 2:
            print("  %-18s mean B-A = %+.3f   exact paired permutation p = %.4f"
                  % (ax, st.mean(d), exact_paired_permutation(d)))

    # --- blinding manipulation check -------------------------------------
    gf = sorted(glob.glob(os.path.join(G, "GUESS_*.json")))
    if gf:
        print("\n=== blinding manipulation check ===")
        n = ok = cant = 0
        for f in gf:
            g = json.load(open(f)); k = json.load(open(os.path.join(G, "KEY_%s.json" % g["pair"])))
            n += 1
            if g["guess"] == "cannot tell": cant += 1; continue
            if k[g["guess"]] == "B": ok += 1
        dec2 = n - cant
        print("  packets probed: %d   'cannot tell': %d   decided: %d" % (n, cant, dec2))
        if dec2:
            print("  correctly identified the formal arm: %d/%d (%.0f%%)  exact p vs chance = %.4f"
                  % (ok, dec2, 100.0 * ok / dec2, sign_test(ok, dec2)))
        print("  accuracy counting 'cannot tell' as a coin flip: %.0f%%"
              % (100.0 * (ok + 0.5 * cant) / n))
