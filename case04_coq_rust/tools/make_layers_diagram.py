#!/usr/bin/env python3
"""Case 04 — TikZ diagram: Arm A's layered Rocq model -> extracted Rust,
with theorem annotations. Data comes from classify_extracted.analyze()
(the same parser as the artifact-map report). Output:
figures/armA_layers.tex (standalone, pdflatex-ready)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from classify_extracted import analyze, LAYERS  # noqa: E402

SHORT = {
    "byte/bit layer": "byte/bit ops",
    "squares & pieces": "squares \\& pieces",
    "move encoding & dirs": "moves \\& direction tables",
    "attacks": "attacks",
    "move generation": "move generation",
    "make/legality": "make / legality",
    "terminal & draw": "terminal \\& draw",
    "evaluation": "evaluation",
    "search & perft": "search \\& perft",
    "FEN / CLI": "FEN / CLI",
}
ORDER = [l for l, _ in LAYERS] + ["other"]


def tex_escape(s):
    return (s.replace("\\", "\\textbackslash{}").replace("_", "\\_")
            .replace("&", "\\&").replace("%", "\\%").replace("#", "\\#"))


def main():
    ws = "/home/xcos/fcdd_c04_ds/armA"
    data = analyze(ws)
    layers, gen, theorems, defs = (data["layers"], data["gen"],
                                   data["theorems"], data["defs"])
    tset = {name: refs for name, refs in theorems}

    rows = []
    y = 0.0
    step = 1.32
    for layer in ORDER:
        names = sorted(layers.get(layer, []))
        if not names:
            continue
        n_gen = sum(1 for n in names if n in gen)
        ths = [t for t, refs in tset.items()
               if set(refs) & set(names)]
        examples = "\\texttt{" + "}, \\texttt{".join(
            tex_escape(n) for n in names[:4]) + "}"
        if len(names) > 4:
            examples += "\\, (+%d)" % (len(names) - 4)
        rows.append((y, layer, len(names), n_gen, examples, ths))
        y += step

    height = y + 0.6
    out = []
    w = out.append
    w("\\documentclass[border=6pt]{standalone}")
    w("\\usepackage{tikz}")
    w("\\usepackage[sfdefault]{FiraSans}")
    w("\\begin{document}")
    w("\\begin{tikzpicture}[x=1cm,y=1cm,")
    w("  box/.style={draw,rounded corners=2pt,fill=#1,text width=4.9cm,")
    w("    inner sep=4pt,font=\\small},")
    w("  rustbox/.style={draw,rounded corners=2pt,fill=blue!12,")
    w("    text width=4.2cm,inner sep=4pt,font=\\small},")
    w("  thmbox/.style={draw,dashed,rounded corners=2pt,fill=gray!8,")
    w("    text width=3.6cm,inner sep=3pt,font=\\tiny}]")
    w("")
    # left: layers (x 0.35..5.25)
    for (yy, layer, nd, ng, examples, ths) in rows:
        ypos = -yy
        nid = abs(hash(layer)) % 10000
        w("\\node[box=green!15] (L%d) at (2.8,%.2f) {"
          % (nid, ypos))
        w("  \\textbf{%s} — %d defs, %d extracted \\\\"
          % (SHORT.get(layer, layer), nd, ng))
        w("  %s};" % examples)
        # theorem callouts: middle column (x ~5.7..9.3)
        if ths:
            label = "\\& ".join("\\texttt{%s}" % tex_escape(t) for t in ths[:5])
            if len(ths) > 5:
                label += "\\, (+%d)" % (len(ths) - 5)
            w("\\node[thmbox,right=0.35cm of L%d] (T%d) {Theorems: %s};"
              % (nid, nid, label))
    # right: the extracted artifact (x 10.5..14.7)
    w("\\node[rustbox] (R) at (12.6,%.2f) {"
      % (-height / 2 + 0.4))
    w("  \\textbf{Extracted Rust} \\\\")
    w("  $150/161$ definitions generated \\\\")
    w("  $257$ functions ($107$ \\texttt{\\_\\_curried} wrappers) \\\\")
    w("  hash-locked to the extractor output};")
    w("\\node[thmbox,below=0.3cm of R] (E) {"
      "Proofs ($26$ theorems) are \\textbf{erased} at extraction — "
      "they constrain the definitions, they ship no code.};")
    # one mechanical-extraction arrow, column to column
    w("\\draw[->,thick,blue!60] (6.3,%.2f) -- node[above,font=\\tiny,"
      "blue!60]{mechanical extraction} (10.2,%.2f);"
      % (-height / 2 + 0.6, -height / 2 + 0.6))
    w("")
    w("\\end{tikzpicture}")
    w("\\end{document}")

    tex = "\n".join(out)
    os.makedirs(os.path.join(os.path.dirname(HERE), "figures"),
                exist_ok=True)
    path = os.path.join(os.path.dirname(HERE), "figures",
                        "armA_layers.tex")
    open(path, "w").write(tex)
    print("written %s" % path)


if __name__ == "__main__":
    main()
