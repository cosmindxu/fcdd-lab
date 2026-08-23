#!/usr/bin/env python3
"""Deposit the comment-volume measurement §5.4 rests on.

v1 asserted that graders scored FCDD lower on minimality because it wrote more
commentary. v2 withdrew that on a measurement that was never deposited. Both
normalisations are reported here, because review pointed out that the whole-file
figure is the wrong denominator: what a grader saw was the DIFF, not the file.
"""
import math, os, re, statistics as st
from itertools import product
W = os.path.expanduser("~/fcdd_arms")
LAB = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SEED = os.path.join(LAB, "case01_spectrum_gambit", "arms", "variants")
SRC = ["chess.asm","movegen.inc","engine.inc","tt.inc","zobrist.inc","perft.inc","pieces.inc"]
BUGS = ["bug%02d" % i for i in range(1,8)]

def comment_chars(d):
    t = 0
    for f in SRC:
        p = os.path.join(d, f)
        if not os.path.exists(p): continue
        for line in open(p, errors="replace"):
            i = line.find(";")
            if i >= 0: t += len(line) - i
    return t

def added_comment_chars(d, bug):
    """Comment characters on lines the run ADDED relative to the seeded tree --
    i.e. what a grader actually read in the diff."""
    import subprocess
    t = 0
    for f in SRC:
        a, b = os.path.join(SEED, bug, f), os.path.join(d, f)
        if not (os.path.exists(a) and os.path.exists(b)): continue
        out = subprocess.run(["diff","-u",a,b], capture_output=True, text=True).stdout
        for line in out.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                i = line.find(";")
                if i >= 0: t += len(line) - i
    return t

def ep(d):
    n=len(d); o=st.mean(d)
    return sum(1 for s in product([1,-1],repeat=n)
               if abs(st.mean([x*y for x,y in zip(s,d)]))>=abs(o)-1e-12)/2**n

for label, fn in (("whole-file comment characters", lambda d,b: comment_chars(d)),
                  ("comment characters ADDED in the diff (what graders saw)", added_comment_chars)):
    A = {}; B = {}
    for bug in BUGS:
        A[bug] = [fn(os.path.join(W,"%s_armA_c2r%d"%(bug,k),"variants",bug), bug) for k in (1,2,3,4)]
        B[bug] = [fn(os.path.join(W,"%s_armB_c2r%d"%(bug,k),"variants",bug), bug) for k in (1,2,3,4)]
    ma = st.mean([x for v in A.values() for x in v]); mb = st.mean([x for v in B.values() for x in v])
    d = [st.mean(B[b]) - st.mean(A[b]) for b in BUGS]
    print("%s:" % label)
    print("   arm A mean %8.1f   arm B mean %8.1f   diff %+.1f (%+.1f%%)"
          % (ma, mb, mb-ma, 100*(mb-ma)/ma if ma else 0))
    print("   paired by defect: mean %+.1f chars, exact p = %.4f\n" % (st.mean(d), ep(d)))
