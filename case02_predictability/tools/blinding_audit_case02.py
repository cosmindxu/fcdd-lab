#!/usr/bin/env python3
"""Blinding audit — run BEFORE grading, per case01 §4.5.

§4.5 measured blinding only after the fact and found it had failed: 0 signature
terms for the ordinary arm vs 37 for FCDD in one packet. This runs the same
count on every case02 packet BEFORE a grader sees it, on the text the grader
actually sees (post-scrub), so a failure is caught rather than discovered.

Counts are per SUBMISSION within a packet, then re-attributed to arms via the
sealed key. A blinded design should show no systematic gap between arms.
"""
import glob, json, os, re, statistics as st
from collections import Counter

C2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G  = os.path.join(C2, "grading")
# case01 §4.5's own list, plus terms this study's scrubber can itself introduce.
TERMS = ["theorem", "specification", "clause", "solver", "witness", "mutant",
         "invariant", "proof", "lemma", "formal", "verif", "z3", "smt",
         "conformance", "reference implementation", "machine-checked"]

def submissions(text):
    """Split a packet into the X and Y source-change blocks."""
    parts = re.split(r"^## Submission ([XY]) — source changes\s*$", text, flags=re.M)
    out = {}
    for i in range(1, len(parts), 2):
        out[parts[i]] = parts[i + 1]
    return out

rows = []
for kf in sorted(glob.glob(os.path.join(G, "KEY_*.json"))):
    key = json.load(open(kf))
    pkt = open(os.path.join(G, "PACKET_%s.md" % key["pair"])).read()
    subs = submissions(pkt)
    r = {"pair": key["pair"]}
    for lab in ("X", "Y"):
        body = subs.get(lab, "").lower()
        n = sum(len(re.findall(r"\b" + re.escape(t), body)) for t in TERMS)
        r[key[lab]] = n                      # attribute to the ARM
        r[lab + "_len"] = len(body)
    rows.append(r)

A = [r["A"] for r in rows]; B = [r["B"] for r in rows]
print("packets audited: %d\n" % len(rows))
print("signature-term counts, per submission, in the text graders will see")
print("  arm A : total %4d   mean %.2f   median %.1f   max %d   packets with >0: %d/%d"
      % (sum(A), st.mean(A), st.median(A), max(A), sum(1 for x in A if x), len(A)))
print("  arm B : total %4d   mean %.2f   median %.1f   max %d   packets with >0: %d/%d"
      % (sum(B), st.mean(B), st.median(B), max(B), sum(1 for x in B if x), len(B)))
print("\ncase01 §4.5 comparison point: 0 vs 37 in a single packet.")

leaky = [r for r in rows if abs(r["A"] - r["B"]) > 0]
print("\npackets where the two submissions differ in signature-term count: %d/%d"
      % (len(leaky), len(rows)))
for r in sorted(leaky, key=lambda r: -abs(r["A"] - r["B"]))[:10]:
    print("   %-10s armA=%2d  armB=%2d   (gap %+d)" % (r["pair"], r["A"], r["B"], r["B"] - r["A"]))

# A grader guessing "the submission with more signature terms is FCDD" would be
# right this often. 0.5 = blinding intact; 1.0 = the label is fully legible.
dec = [r for r in rows if r["A"] != r["B"]]
correct = sum(1 for r in dec if r["B"] > r["A"])
print("\nadversary model — guess 'more signature terms = the formal arm':")
if dec:
    print("   decidable packets: %d/%d,  guess correct on %d  (%.0f%% of decidable)"
          % (len(dec), len(rows), correct, 100.0 * correct / len(dec)))
    print("   accuracy over ALL packets (undecidable = coin flip): %.0f%%"
          % (100.0 * (correct + 0.5 * (len(rows) - len(dec))) / len(rows)))
else:
    print("   no packet is decidable on this signal — blinding holds against it")
