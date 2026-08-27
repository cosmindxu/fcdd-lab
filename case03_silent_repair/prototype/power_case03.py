import numpy as np
from math import comb
rng=np.random.default_rng(11)
def dist(margins):
    d={0:1.0}
    for (nA,nB,m) in margins:
        N=nA+nB; lo,hi=max(0,m-nB),min(m,nA)
        h={a:comb(nA,a)*comb(nB,m-a)/comb(N,m) for a in range(lo,hi+1)}
        nd={}
        for t,p in d.items():
            for a,q in h.items(): nd[t+a]=nd.get(t+a,0.0)+p*q
        d=nd
    return d
def pex(tb):
    m=[(nA,nB,a+b) for a,nA,b,nB in tb]; T=sum(a for a,_,_,_ in tb); dd=dist(m)
    lo=sum(p for t,p in dd.items() if t<=T); hi=sum(p for t,p in dd.items() if t>=T)
    return min(1.0,2*min(lo,hi))
def sim(nd,k,pA,pB,reps=8000):
    h=0
    for _ in range(reps):
        tb=[(rng.binomial(k,pA[d]),k,rng.binomial(k,pB[d]),k) for d in range(nd)]
        if pex(tb)<0.05: h+=1
    return h/reps
base=[(0.30,0.10),(0.45,0.15),(0.55,0.20),(0.60,0.25),(0.80,0.40),(0.50,0.25),(0.70,0.30),(0.35,0.15)]
for nd,k in [(7,4),(7,5),(8,4),(6,5)]:
    pA=[b[0] for b in base[:nd]]; pB=[b[1] for b in base[:nd]]
    print(f"{nd}x{k} = {nd*k*2:>2} runs | heterogeneous power {sim(nd,k,pA,pB):.3f} "
          f"| homogeneous(.55/.20) {sim(nd,k,[0.55]*nd,[0.20]*nd):.3f} "
          f"| type-I {sim(nd,k,pA,pA):.3f}")
# minimum detectable effect at 7x4, 80% power, homogeneous
print("\n7 defects x 4 reps (56 runs): power vs pB at pA=0.55")
for pB in [0.05,0.10,0.15,0.20,0.25,0.30]:
    print(f"   pB={pB:.2f} -> power {sim(7,4,[0.55]*7,[pB]*7):.3f}")
