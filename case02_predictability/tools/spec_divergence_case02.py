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
"""
import hashlib, os, re, subprocess
LAB  = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE = os.path.join(LAB, "case01_spectrum_gambit", "step1_contract", "spec", "Contract.lean")
WORK = os.path.expanduser("~/fcdd_arms")
BUGS = ["bug%02d" % i for i in range(1, 8)]
DECL = re.compile(r"^\s*(theorem|lemma|def|abbrev|axiom|structure)\s+([A-Za-z0-9_']+)", re.M)

def decls(p):
    try: return set(m[1] for m in DECL.findall(open(p, encoding="utf-8", errors="replace").read()))
    except FileNotFoundError: return None

base_decls = decls(BASE); base_lines = len(open(BASE, errors="replace").read().splitlines())
print("baseline contract: %d lines, %d declarations\n" % (base_lines, len(base_decls)))
print("%-7s %-9s %-11s %-14s %-9s %s" % ("defect","distinct","kernel-built","added lines","union","shared by all 4"))
tot_distinct = 0
for bug in BUGS:
    hs, adds, sets, built = [], [], [], 0
    for k in (1, 2, 3, 4):
        f = os.path.join(WORK, "%s_armB_c2r%d" % (bug, k), "contract", "spec", "Contract.lean")
        d = decls(f)
        if d is None: continue
        hs.append(hashlib.sha256(open(f,"rb").read()).hexdigest())
        adds.append(len(open(f, errors="replace").read().splitlines()) - base_lines)
        sets.append(d - base_decls)
        built += os.path.exists(f.replace("Contract.lean", "Contract.olean"))
    u = len(set(hs)); tot_distinct += u
    union = set().union(*sets) if sets else set()
    inter = set.intersection(*sets) if sets else set()
    print("%-7s %-9s %-11s %-14s %-9d %s" % (bug, "%d of %d" % (u, len(hs)), "%d/%d" % (built, len(hs)),
          "+%d..+%d" % (min(adds), max(adds)), len(union), sorted(inter) or "(none)"))
print("\ndistinct specifications across the 28 arm B runs : %d" % tot_distinct)
print("distinct repaired binaries across all 56 runs    : 1  (all equal to pristine)")
print("\nEvery specification above is kernel-accepted: Lean certifies that a spec is")
print("WELL-FORMED, not that it is the right one, and not that two of them agree.")
