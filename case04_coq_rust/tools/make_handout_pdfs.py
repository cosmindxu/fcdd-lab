#!/usr/bin/env python3
"""Case 04 — render each arm's hand-out as a PDF. The hand-out is the
natural-language specification each arm receives: PROMPT.md (arm-specific
treatment), IFACE.md (deliverable contract), ORACLE.md (discovery
instrument), smoke/README.md (public smoke set). Markdown -> LaTeX via
pandoc + pdflatex. Output: figures/armA_handout.pdf, armB_handout.pdf."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
WS = os.path.join(LAB, "workspace")


def pdf(arm, out_path):
    prompt = os.path.join(WS, "prompts", "arm%s_PROMPT.md" % arm)
    parts = [("// prompt", prompt), ("// iface", os.path.join(WS, "IFACE.md")),
             ("// oracle", os.path.join(WS, "ORACLE.md")),
             ("// smoke", os.path.join(WS, "smoke", "README.md"))]
    md = os.path.join("/tmp/opencode", "handout_%s.md" % arm)
    with open(md, "w") as f:
        for title, path in parts:
            f.write("\n\n\\newpage\n\n")
            for line in open(path):
                f.write(line)
    subprocess.run(["pandoc", md, "-o", out_path,
                    "--pdf-engine=pdflatex",
                    "-V", "geometry:margin=2.2cm",
                    "-V", "fontsize=10pt",
                    "--toc",
                    "-M", "title=Case 04 — Arm %s hand-out" % arm],
                   check=True, capture_output=True)
    print("written %s" % out_path)


def main():
    outdir = os.path.join(LAB, "figures")
    os.makedirs(outdir, exist_ok=True)
    pdf("A", os.path.join(outdir, "armA_handout.pdf"))
    pdf("B", os.path.join(outdir, "armB_handout.pdf"))


if __name__ == "__main__":
    main()
