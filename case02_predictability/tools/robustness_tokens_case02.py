#!/usr/bin/env python3
"""Robustness: rerun the PRIMARY estimator on raw tokens instead of dollars.

Case01's D3 legislated "Opus 5 unpriced -> raw-only if it ever appears", and
case02 §7 fixes cost as "the modelUsage total including subagents" without
settling dollars vs tokens. A7 established total_cost_usd equals the modelUsage
costUSD sum exactly, so dollars are defensible as the pre-registered measure and
remain PRIMARY. This is a labelled robustness check, not a substitute: if the
verdict is sensitive to that choice, that must be known and reported.
"""
import glob, json, math, os, re, statistics as st
from itertools import product
RAW="/media/sf_Projects/fcdd_lab/case01_spectrum_gambit/ledger/raw"
BUGS=["bug%02d"%i for i in range(1,8)]
KEYS=("inputTokens","cacheCreationInputTokens","cacheReadInputTokens","outputTokens")

def cells(measure):
    out={}
    for f in glob.glob(RAW+"/arm*_c2r*_a*_result.json"):
        m=re.search(r'arm([AB])_(bug\d+)_c2r(\d)_a(\d)_result\.json$',f)
        if not m: continue
        try: d=json.load(open(f))
        except Exception: continue
        if d.get("is_error"): continue
        arm,bug,k,_=m.groups()
        mu=d.get("modelUsage") or {}
        v = d.get("total_cost_usd") if measure=="usd" else \
            sum(sum(x.get(kk) or 0 for kk in KEYS) for x in mu.values())
        if measure=="out": v=sum(x.get("outputTokens") or 0 for x in mu.values())
        out.setdefault((bug,arm),[]).append(float(v))
    return out

def cv_log(c): 
    ln=[math.log(x) for x in c]; m=st.mean(ln)
    return st.stdev(ln)/abs(m) if m else None
def exact_p(d):
    n=len(d); obs=st.mean(d)
    return sum(1 for s in product([1,-1],repeat=n)
               if abs(st.mean([x*y for x,y in zip(s,d)]))>=abs(obs)-1e-12)/2**n
def sign_p(k,n):
    return sum(math.comb(n,i) for i in range(n+1) if abs(i-n/2)>=abs(k-n/2))/2**n

for measure,name in (("usd","dollars (PRIMARY, pre-registered)"),
                     ("tok","raw tokens, all four kinds (D3's preferred unit)"),
                     ("out","output tokens only")):
    C=cells(measure)
    assert all(len(v)==4 for v in C.values()), "cells must hold 4 runs"
    diffs=[cv_log(C[(b,"A")])-cv_log(C[(b,"B")]) for b in BUGS]
    ratios=[st.mean(C[(b,"B")])/st.mean(C[(b,"A")]) for b in BUGS]
    k=sum(1 for r in ratios if r>1)
    print("%-46s  mean CV diff %+0.4f   perm p = %.4f | median ratio %.2fx  %d/7  sign p = %.4f"
          % (name, st.mean(diffs), exact_p(diffs), st.median(ratios), k, sign_p(k,7)))
