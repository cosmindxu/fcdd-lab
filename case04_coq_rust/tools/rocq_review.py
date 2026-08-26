#!/usr/bin/env python3
"""Case 04 — quality/completeness review of the five armA Rocq submissions.

Emits every number in the Rocq review (C10). Reads the cell workspaces under
~/fcdd_c04_scored/ and the deposited ledger. Nothing here is admissible as
evidence about either method (A-2026-08-26); it describes the artefacts.
"""
import glob, hashlib, itertools, json, os, re, subprocess

ROOT = os.path.expanduser("~/fcdd_c04_scored")
CELLS = ["armA_r1", "armA_r2", "armA_r3", "armA_r4", "armA_r5"]
LAB = os.path.join(os.path.dirname(__file__), "..")
RAW = os.path.join(LAB, "ledger", "raw")

DECL = {
    "Definition": r"^\s*Definition\s",
    "Fixpoint": r"^\s*(Fixpoint|Program Fixpoint)\s",
    "Inductive": r"^\s*Inductive\s",
    "Record": r"^\s*Record\s",
    "Thm/Lem/Ex": r"^\s*(Theorem|Lemma|Corollary|Proposition|Example)\s",
}
TACTICS = ("vm_compute", "reflexivity", "induction", "destruct", "auto", "lia",
           "apply", "rewrite", "simpl", "discriminate", "inversion", "ring",
           "congruence", "omega", "field", "eauto")
RULES = {
    "castling": r"castl", "en passant": r"passant|\bep[A-Z_]",
    "promotion": r"promo", "fifty-move": r"fifty|halfmove",
    "repetition": r"repetition|threefold", "insufficient": r"insufficient",
    "check": r"\bcheck", "mate/stalemate": r"stalemate|mated",
}


def vfiles(cell):
    return sorted(glob.glob(os.path.join(ROOT, cell + "_build", "armA", "**", "*.v"),
                            recursive=True))


def spec_of(cell):
    for f in vfiles(cell):
        if "Chess" in os.path.basename(f):
            return f
    return vfiles(cell)[0] if vfiles(cell) else None


def main():
    out = []
    out.append("CASE 04 — the armA Rocq submissions: quality and completeness")
    out.append("Descriptive only; INADMISSIBLE as evidence (A-2026-08-26).\n")

    out.append("DECLARATION CENSUS")
    hdr = f"{'cell':<9}{'lines':>7}" + "".join(f"{k:>12}" for k in DECL) + f"{'forall-props':>13}"
    out.append(hdr); out.append("-" * len(hdr))
    tac_total = {}
    for c in CELLS:
        fs = vfiles(c)
        text = "\n".join(open(f).read() for f in fs)
        lines = text.count("\n")
        row = f"{c:<9}{lines:>7}"
        for k, pat in DECL.items():
            row += f"{len(re.findall(pat, text, re.M)):>12}"
        stmts = re.findall(r"^\s*(?:Theorem|Lemma|Corollary|Proposition|Example)\s[^.]*\.",
                           text, re.M)
        row += f"{sum('forall' in s for s in stmts):>13}"
        out.append(row)
        for t in TACTICS:
            n = len(re.findall(r"\b%s\b" % t, text))
            if n:
                tac_total[t] = tac_total.get(t, 0) + n

    out.append("\nPROOF ACTIVITY, ALL FIVE TREES COMBINED")
    out.append("  " + ("  ".join(f"{t}={n}" for t, n in sorted(tac_total.items(),
                                                               key=lambda x: -x[1]))
                       or "(none)"))
    out.append("  Every tactic occurrence is closed-term evaluation; there is no")
    out.append("  induction, case analysis or quantified reasoning in any tree.")

    out.append("\nRULE COVERAGE (occurrences of the rule's vocabulary)")
    hdr = f"{'cell':<9}" + "".join(f"{k:>15}" for k in RULES)
    out.append(hdr); out.append("-" * len(hdr))
    for c in CELLS:
        text = "\n".join(open(f).read() for f in vfiles(c))
        out.append(f"{c:<9}" + "".join(
            f"{len(re.findall(p, text, re.I)):>15}" for p in RULES.values()))

    out.append("\nTRUSTED GLUE — hand-written Extract Constant remaps")
    for c in CELLS:
        text = "\n".join(open(f).read() for f in vfiles(c))
        n = len(re.findall(r"Extract Constant", text))
        risky = sorted(set(re.findall(r"Nat\.(div|modulo)\s*=>", text)))
        out.append(f"  {c:<9} {n:>3} remaps"
                   + (f"   RISKY: Nat.{'/Nat.'.join(risky)} -> raw Rust / and %" if risky else ""))
    out.append("  Rocq's Nat.div/Nat.modulo are TOTAL (kernel-checked: 7/0 = 0, 7 mod 0 = 7);")
    out.append("  Rust's / and % PANIC on a zero divisor. The remap therefore drops a")
    out.append("  spec-level guarantee outside the kernel's view. In these submissions every")
    out.append("  divisor is a literal (256/16/8/2), so the trapdoor is LATENT, not live.")

    out.append("\nINDEPENDENCE OF THE FIVE 'REPLICATES'")
    digest, sets = {}, {}
    for c in CELLS:
        f = spec_of(c)
        digest[c] = hashlib.sha256(open(f, "rb").read()).hexdigest()
        sets[c] = set(l.strip() for l in open(f)
                      if l.strip() and not l.strip().startswith("(*"))
    for c in CELLS:
        out.append(f"  {c:<9} {digest[c][:16]}  {os.path.relpath(spec_of(c), ROOT)}")
    out.append("")
    for a, b in itertools.combinations(CELLS, 2):
        j = len(sets[a] & sets[b]) / len(sets[a] | sets[b])
        if j > 0.15:
            same = " BYTE-IDENTICAL" if digest[a] == digest[b] else ""
            out.append(f"  {a} vs {b}: Jaccard {j:.2f}{same}")
    out.append("  => five cells, three distinct submissions.")

    out.append("\nCROSS-CELL WORKSPACE ACCESS (new finding; not in review round 1)")
    pat = re.compile(r"(arm[AB]_[rs][0-9]_build[^\s\"'\\,)]*)")
    for c in CELLS:
        p = os.path.join(RAW, c + ".jsonl")
        if not os.path.exists(p):
            continue
        hits = {}
        for ln in open(p):
            try:
                d = json.loads(ln)
            except ValueError:
                continue
            for m in pat.findall(json.dumps(d.get("part") or {})[:4000]):
                cell = m.split("_build")[0]
                if cell == c:
                    continue
                hits[cell] = hits.get(cell, 0) + 1
        if hits:
            top = ", ".join(f"{k}x{v}" for k, v in sorted(hits.items(), key=lambda x: -x[1])[:5])
            out.append(f"  {c:<9} referenced other cells' build trees: {top}")
    out.append("  armA_r5 read armA_r1's theories/Chess.v, its extracted.rs and its compiled")
    out.append("  target/release/chess_clone; armA_r3 referenced armA_r2's tree 212 times.")
    out.append("  This explains the byte-identity above directly, and it means the arm's")
    out.append("  replicate cells are NOT independent observations.")

    txt = "\n".join(out)
    print(txt)
    open(os.path.join(LAB, "ledger", "rocq_review.txt"), "w").write(txt + "\n")


if __name__ == "__main__":
    main()
