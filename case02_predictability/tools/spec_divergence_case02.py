#!/usr/bin/env python3
"""EXPLORATORY (not pre-registered): how reproducible is FCDD's own artefact?

The study's pre-registered outcomes all concern cost and the repaired code. This
asks a question the design did not pose and cannot answer inferentially: given
the same defect and the same frozen contract, do independent FCDD runs converge
on the same FORMAL SPECIFICATION the way they converge on the same code?

Lexical, not semantic. Two agents can formalise the same property under
different names, so declaration-name overlap is a weak proxy and low overlap does
not prove the specifications disagree. It does show they did not converge on a
shared vocabulary, which combined with the volume spread is suggestive. Labelled
exploratory throughout; no p-value is computed and none should be.

BASELINE CORRECTNESS (this script's first version got it wrong). The reference is
NOT the repository's Contract.lean: run_resilient.sh scrubs absolute paths out of
every workspace at build time, so all 28 copies differ from the repo file in one
line before any agent runs. Comparing against the repo baseline therefore scored
all 28 as "modified" when six were untouched. The reference used here is the repo
baseline with the same path substitution applied — i.e. the file the agents were
actually handed.

COUNTING. "Distinct specifications" is counted GLOBALLY over the 28 files, not as
a sum of per-defect distinct counts: the single untouched file appears under three
different defects and a per-defect sum charges it three times. The per-defect sum
is also reported, because the like-for-like comparison against the binaries needs
matching units.
"""
import hashlib, os, re, subprocess
LAB  = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE = os.path.join(LAB, "case01_spectrum_gambit", "step1_contract", "spec", "Contract.lean")
WORK = os.path.expanduser("~/fcdd_arms")
BUGS = ["bug%02d" % i for i in range(1, 8)]
DECL = re.compile(r"^\s*(theorem|lemma|def|abbrev|axiom|structure)\s+([A-Za-z0-9_']+)", re.M)

SCRUB = re.compile(r"/media/sf_Projects[A-Za-z0-9_/.-]*")

def read(p):
    try: return open(p, encoding="utf-8", errors="replace").read()
    except FileNotFoundError: return None

def decls_of(text): return set(m[1] for m in DECL.findall(text))

# The file the agents were handed: repo baseline, path-scrubbed exactly as the
# runner scrubs it. This is the only correct "untouched" reference.
base_raw = read(BASE)
base_handed = SCRUB.sub("EXTERNAL_PATH_REMOVED", base_raw)
base_decls = decls_of(base_handed); base_lines = len(base_handed.splitlines())
print("baseline as handed to agents: %d lines, %d declarations\n" % (base_lines, len(base_decls)))
print("%-7s %-9s %-9s %-12s %-14s %-7s %s"
      % ("defect","modified","distinct","kernel-built","added lines","union","shared by all MODIFIED runs"))
allhashes = []; persum = 0; nmod = 0; untouched = []
for bug in BUGS:
    hs, adds, sets, built, mod = [], [], [], 0, 0
    for k in (1, 2, 3, 4):
        f = os.path.join(WORK, "%s_armB_c2r%d" % (bug, k), "contract", "spec", "Contract.lean")
        t = read(f)
        if t is None: continue
        h = hashlib.sha256(t.encode()).hexdigest(); hs.append(h); allhashes.append(h)
        built += os.path.exists(f.replace("Contract.lean", "Contract.olean"))
        if t == base_handed:
            untouched.append("%s/r%d" % (bug, k)); continue      # agent never touched it
        mod += 1; adds.append(len(t.splitlines()) - base_lines); sets.append(decls_of(t) - base_decls)
    nmod += mod; persum += len(set(hs))
    union = set().union(*sets) if sets else set()
    inter = set.intersection(*sets) if sets else set()
    print("%-7s %-9s %-9s %-12s %-14s %-7d %s"
          % (bug, "%d of %d" % (mod, len(hs)), "%d" % len(set(hs)), "%d/%d" % (built, len(hs)),
             ("+%d..+%d" % (min(adds), max(adds))) if adds else "n/a",
             len(union), sorted(inter) or "(none)"))
print("\nArm B runs that MODIFIED the specification      : %d of 28" % nmod)
print("runs that left it byte-identical as handed      : %d  (%s)" % (len(untouched), ", ".join(untouched)))
print("distinct specification files, counted globally  : %d over 28 runs" % len(set(allhashes)))
print("  (per-defect distinct summed, for contrast     : %d -- this DOUBLE-COUNTS the" % persum)
print("   single untouched file, which recurs under three different defects)")
print("distinct repaired binaries, counted globally    : 1 over 56 runs")
print("  (per-defect summed, matching units            : 7)")
print("\nEvery specification above is kernel-accepted: Lean certifies that a spec is")
print("WELL-FORMED, not that it is the right one, and not that two of them agree.")
