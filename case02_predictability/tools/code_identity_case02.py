#!/usr/bin/env python3
"""Do the two arms emit the SAME repair? Checked three ways, mechanically.

All 28 blind graders independently reported that arm A's and arm B's diffs are
byte-identical in executable content. That is a claim about the study's core
object and is verified here rather than taken on their word.

  1. BUILT BINARY   — sha256 of chess.bin, the assembler's own output. Decisive
                      when present: identical bytes means identical program.
  2. INSTRUCTION    — source with ALL comments removed (whole-line AND trailing
     STREAM           ';' comments) and whitespace normalised. Catches the case
                      where a binary is absent or stale.
  3. RAW SOURCE     — byte comparison, for contrast: this is what disagrees, and
                      the gap between 2 and 3 is exactly the comment volume.
"""
import hashlib, os, re, sys
LAB="/media/sf_Projects/fcdd_lab"; WORK=os.path.expanduser("~/fcdd_arms")
SRC=["chess.asm","movegen.inc","engine.inc","tt.inc","zobrist.inc","perft.inc","pieces.inc"]
BUGS=["bug%02d"%i for i in range(1,8)]

def strip_all_comments(text):
    """Remove ';' comments, respecting single-quoted chars, then normalise space."""
    out=[]
    for line in text.splitlines():
        res=[]; q=None
        for ch in line:
            if q:
                res.append(ch)
                if ch==q: q=None
                continue
            if ch in "'\"": q=ch; res.append(ch); continue
            if ch==";": break
            res.append(ch)
        s=re.sub(r"\s+"," ","".join(res)).strip()
        if s: out.append(s)
    return "\n".join(out)

def read(p):
    try: return open(p,encoding="utf-8",errors="replace").read()
    except FileNotFoundError: return None

def h(b): return hashlib.sha256(b).hexdigest()[:12] if b is not None else None

rows=[]
for bug in BUGS:
    for k in (1,2,3,4):
        wa=os.path.join(WORK,"%s_armA_c2r%d"%(bug,k),"variants",bug)
        wb=os.path.join(WORK,"%s_armB_c2r%d"%(bug,k),"variants",bug)
        binA=os.path.join(wa,"chess.bin"); binB=os.path.join(wb,"chess.bin")
        ba=open(binA,"rb").read() if os.path.exists(binA) else None
        bb=open(binB,"rb").read() if os.path.exists(binB) else None
        bin_same = (ba is not None and bb is not None and ba==bb)
        ins_same = raw_same = True; missing=False
        for f in SRC:
            ta, tb = read(os.path.join(wa,f)), read(os.path.join(wb,f))
            if ta is None or tb is None: missing=True; ins_same=raw_same=False; break
            if ta!=tb: raw_same=False
            if strip_all_comments(ta)!=strip_all_comments(tb): ins_same=False
        rows.append(dict(bug=bug,k=k,bin_same=bin_same,ins_same=ins_same,raw_same=raw_same,
                         have_bins=(ba is not None and bb is not None),missing=missing,
                         shaA=h(ba),shaB=h(bb)))

print("%-7s %-3s %-12s %-12s %-10s %-10s" % ("defect","run","binary sha A","binary sha B","same bin?","same instr?"))
for r in rows:
    print("%-7s r%-2d %-12s %-12s %-10s %-10s" % (r["bug"],r["k"],r["shaA"] or "-",r["shaB"] or "-",
          ("YES" if r["bin_same"] else ("no" if r["have_bins"] else "n/a")),
          "YES" if r["ins_same"] else "NO"))

nb=sum(1 for r in rows if r["have_bins"]); nbs=sum(1 for r in rows if r["bin_same"])
ni=sum(1 for r in rows if r["ins_same"]); nr=sum(1 for r in rows if r["raw_same"])
print("\npairs where BOTH binaries exist      : %d/28" % nb)
print("  of those, byte-identical binaries  : %d/%d" % (nbs,nb))
print("pairs with identical INSTRUCTION text: %d/28" % ni)
print("pairs with identical RAW source      : %d/28  <- the gap is comments" % nr)
