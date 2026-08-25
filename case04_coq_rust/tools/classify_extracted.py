#!/usr/bin/env python3
"""Case 04 — classify Arm A's extracted artifact.

Builds a layered tree of the Rocq definitions (from ChessSpec.v),
maps the generated Rust functions (extracted.rs, ChessSpec_* names) onto
it, and attaches each kernel-checked theorem (Theorems.v) to the
definitions its statement mentions. Theorems themselves do not extract
(proofs are erased); the mapping shows which computational definitions
each theorem constrains.

Usage: classify_extracted.py <ws_armA> [--out report.md]
"""
import argparse
import os
import re
import sys

KEYWORDS = ("Fixpoint", "Definition", "Inductive", "Record", "Theorem",
            "Lemma", "Notation")

LAYERS = [
    ("byte/bit layer", ["w8", "addB", "negB", "andAux", "orAux", "xorAux",
                        "andB", "orB", "xorB", "pow2", "bitn"]),
    ("squares & pieces", ["onBoard", "sqFile", "sqRank", "sq64", "mirrorIdx",
                          "EMPTY", "WP", "WN", "WB", "WR", "WQ", "WK",
                          "BP", "BN", "BB", "BR", "BQ", "BK", "COLBIT",
                          "TYPEMASK", "pcType", "pcCol", "WHITE", "BLACK",
                          "other", "emptyBoard", "bSet", "bGet"]),
    ("move encoding & dirs", ["SP_", "Move", "mvFrm", "mvDst", "mvFlag",
                              "mvSpecial", "mvPromo", "mvEqb", "promoFlags",
                              "knightDirs", "kingDirs", "bishopDirs",
                              "rookDirs"]),
    ("attacks", ["isAttacked", "scanHop", "scanSlide", "pawnAt", "slideHit",
                 "inCheckSide", "scanSquares", "attacks"]),
    ("move generation", ["genHops", "genRay", "genSlides", "genPawnWhite",
                         "genPawnBlack", "genCastling", "genForSquare",
                         "genMoves", "addPromos", "pawnMoves"]),
    ("make/legality", ["genLegal", "moverInCheck", "makeMove", "unmakeMove",
                       "capSquare", "undoOf", "applyMove", "mkMove",
                       "MkMove", "clrCastleSq"]),
    ("terminal & draw", ["statusOf", "updateTerminal", "isInsufficient",
                         "countReps", "History", "GSplay", "GSwhiteMated",
                         "GSblackMated", "GSstalemate", "GSdraw"]),
    ("evaluation", ["eval", "pst", "pieceVal", "gamePhase", "kingPst",
                    "matingEval", "material", "score"]),
    ("search & perft", ["chooseMove", "negamax", "perft", "depth"]),
    ("FEN / CLI", ["parseFen", "parseBoard", "parseBoardAux", "isDigit",
                   "takeField", "dropField", "nzeros", "pieceOfChar",
                   "render", "entry", "sqName"]),
]


def def_blocks(path):
    """Yield (kind, name, body) for top-level definitions."""
    cur = None
    for line in open(path):
        m = re.match(r"^(Fixpoint|Definition|Inductive|Record|Theorem|Lemma|Notation)\s+([A-Za-z0-9_']+)", line)
        if m:
            if cur:
                yield cur
            cur = (m.group(1), m.group(2), line)
        elif cur:
            cur = (cur[0], cur[1], cur[2] + line)
    if cur:
        yield cur


def classify(name, body, layers):
    # name matches take priority over body mentions (a movegen function's
    # body naturally mentions byte ops, squares, etc.)
    for layer, keys in layers:
        for k in keys:
            if name == k or name.startswith(k) or k + "_" in name:
                return layer
    for layer, keys in layers:
        for k in keys:
            if re.search(r"\b" + re.escape(k) + r"\b", body):
                return layer
    return "other"


def identifiers(text):
    return set(re.findall(r"[A-Za-z][A-Za-z0-9_']*", text))


def analyze(ws):
    spec = os.path.join(ws, "rocq", "ChessSpec.v")
    thms = os.path.join(ws, "rocq", "Theorems.v")
    rust = os.path.join(ws, "chess_clone", "src", "extracted.rs")

    defs = {name: (kind, body) for kind, name, body in def_blocks(spec)
            if kind in ("Fixpoint", "Definition", "Inductive", "Record")}
    # fix Fixpoint body capture bug: bodies of subsequent defs start clean
    layers = {}
    for name, (kind, body) in defs.items():
        layers.setdefault(classify(name, body, LAYERS), []).append(name)

    # generated functions
    gen = {}
    for line in open(rust):
        m = re.match(r"fn (ChessSpec_[A-Za-z0-9_']+)\b", line)
        if m:
            fn = m.group(1)[len("ChessSpec_"):]
            base = fn[:-len("__curried")] if fn.endswith("__curried") else fn
            gen.setdefault(base, set()).add("curried" if fn.endswith("__curried") else "plain")

    # theorems -> referenced definitions
    theorems = []
    for kind, name, body in def_blocks(thms):
        if kind in ("Theorem", "Lemma"):
            toks = identifiers(body)
            refs = sorted(d for d in defs if d in toks)
            theorems.append((name, refs))

    lines = []
    w = lines.append
    w("# Arm A artifact map — Rocq model -> extracted Rust -> theorems\n")
    w("Definitions: %d (spec), generated fns: %d, theorems: %d\n"
      % (len(defs), len(gen), len(theorems)))
    total_fns = sum(len(v) for v in gen.values())
    w("Generated Rust functions: %d total (of which %d `__curried` wrappers)\n"
      % (total_fns, sum(1 for v in gen.values() if "curried" in v)))
    w("Definitions WITHOUT any generated code: %s\n"
      % (sorted(set(defs) - set(gen)) or "none"))
    w("Generated names with NO spec definition (renamed/generated): %s\n"
      % (sorted(set(gen) - set(defs)) or "none"))

    w("\n## Layers\n")
    for layer, _ in LAYERS:
        names = sorted(layers.get(layer, []))
        if not names:
            continue
        w("\n### %s (%d definitions)\n" % (layer, len(names)))
        for n in names:
            kinds = gen.get(n, set())
            ktxt = ", ".join(sorted(kinds)) if kinds else "NOT EXTRACTED"
            # theorems mentioning this def
            ths = [t for t, refs in theorems if n in refs]
            w("- `%s` — generated: %s%s"
              % (n, ktxt,
                 ("  <— " + ", ".join("`%s`" % t for t in ths)) if ths else ""))

    w("\n## Theorems -> definitions (proofs are erased; the mapping shows "
      "what each constrains)\n")
    for t, refs in theorems:
        w("- `%s`" % t)
        for r in refs:
            layer = next((l for l, _ in LAYERS if r in layers.get(l, [])),
                         "other")
            w("  - `%s` (%s)" % (r, layer))

    return {"layers": layers, "gen": gen, "theorems": theorems,
            "defs": defs, "report": "\n".join(lines)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("ws")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    data = analyze(args.ws)
    if args.out:
        open(args.out, "w").write(data["report"])
        print("written to %s" % args.out)
    else:
        print(data["report"][:4000])


if __name__ == "__main__":
    main()
