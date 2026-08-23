#!/usr/bin/env python3
"""Case02 figures. Vector PDF for LaTeX + PNG for review, into figures/.

Palette: dataviz categorical slots 1-2, identical to case01 so that "blue = the
ordinary arm, orange = FCDD" holds across the whole programme — colour follows
the entity, never its rank. Validated: worst adjacent pair dE 24.7 (protan),
33.6 (normal), all five checks pass. Identity is carried by position and direct
label as well as by colour, so nothing depends on colour alone.

  fig1  attack rounds vs run cost, by arm   <- the method finding (§5.7)
  fig2  cost per defect, paired             <- §5.5
  fig3  CV_log dispersion, paired by defect <- §5.1
  fig4  artefact convergence by arm         <- §5.2 / §5.6
"""
import glob, json, math, os, re, statistics as st
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

CASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAB  = os.path.dirname(CASE)
RAW  = os.path.join(LAB, "case01_spectrum_gambit", "ledger", "raw")
W    = os.path.expanduser("~/fcdd_arms")
FIG  = os.path.join(CASE, "figures")
BUGS = ["bug%02d" % i for i in range(1, 8)]

A_COL, B_COL = "#2a78d6", "#eb6834"
INK, MUTED, GRID = "#1a1a1a", "#5a5a5a", "#d8d8d6"
A_NAME, B_NAME = "Ordinary dev + review", "FCDD"

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Nimbus Roman", "DejaVu Serif"],
    "font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
    "text.color": INK, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 150, "savefig.dpi": 150,
})

def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(FIG, "%s.%s" % (name, ext)),
                    bbox_inches="tight", facecolor="white")
    plt.close(fig); print("  wrote %s.pdf/.png" % name)

# ---------------------------------------------------------------- data
def cost(arm, bug, k):
    for x in glob.glob(os.path.join(RAW, "arm%s_%s_c2r%d_a*_result.json" % (arm, bug, k))):
        d = json.load(open(x))
        if not d.get("is_error"): return float(d["total_cost_usd"])
    return None

ROUND = re.compile(r'round\s*[1-9#]|attack round|review round', re.I)
def rounds(arm, bug, k):
    p = os.path.join(W, "%s_arm%s_c2r%d" % (bug, arm, k), "FIX_NOTES.md")
    return len(ROUND.findall(open(p, errors="replace").read())) if os.path.exists(p) else None

cells = {(b, a): [cost(a, b, k) for k in (1, 2, 3, 4)] for b in BUGS for a in "AB"}
cv = lambda c: st.stdev([math.log(x) for x in c]) / abs(st.mean([math.log(x) for x in c]))

# ---------------------------------------------------------------- fig1
fig, ax = plt.subplots(figsize=(5.6, 3.5))
for arm, col, nm in (("A", A_COL, A_NAME), ("B", B_COL, B_NAME)):
    xs, ys = [], []
    for b in BUGS:
        for k in (1, 2, 3, 4):
            r, c = rounds(arm, b, k), cost(arm, b, k)
            if r is not None and c is not None: xs.append(r); ys.append(c)
    ax.scatter(xs, ys, s=34, facecolor=col, edgecolor="white", linewidth=0.8,
               label="%s  (n=%d)" % (nm, len(xs)), zorder=3)
    mx, my = st.mean(xs), st.mean(ys)
    den = (sum((x-mx)**2 for x in xs) * sum((y-my)**2 for y in ys)) ** .5
    r_ = sum((x-mx)*(y-my) for x, y in zip(xs, ys)) / den
    # least-squares guide, drawn thin and behind the marks
    sl = sum((x-mx)*(y-my) for x, y in zip(xs, ys)) / sum((x-mx)**2 for x in xs)
    xr = [min(xs), max(xs)]
    ax.plot(xr, [my + sl*(x-mx) for x in xr], color=col, lw=1.2, alpha=.55, zorder=2)
    ax.annotate("r = %+.2f" % r_, (xr[1], my + sl*(xr[1]-mx)), textcoords="offset points",
                xytext=(6, -1), color=col, fontsize=8.5, fontweight="bold")
ax.set_xlabel("adversarial / review rounds recorded in the run")
ax.set_ylabel("run cost (USD)")
ax.set_title("Review rounds drive cost under FCDD, not under ordinary review",
             fontsize=9.5, loc="left", pad=9)
ax.grid(axis="y", color=GRID, lw=.6); ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=8.5, loc="upper left")
save(fig, "fig1_rounds_vs_cost")

# ---------------------------------------------------------------- fig2
fig, ax = plt.subplots(figsize=(5.6, 3.2))
y = range(len(BUGS))
for i, b in enumerate(BUGS):
    a_, b_ = st.mean(cells[(b, "A")]), st.mean(cells[(b, "B")])
    ax.plot([a_, b_], [i, i], color=GRID, lw=2.2, zorder=1, solid_capstyle="round")
    ax.scatter([a_], [i], s=40, color=A_COL, zorder=3, edgecolor="white", linewidth=.8)
    ax.scatter([b_], [i], s=40, color=B_COL, zorder=3, edgecolor="white", linewidth=.8)
    ax.annotate("%.2fx" % (b_/a_), (b_, i), textcoords="offset points", xytext=(8, -3),
                fontsize=8, color=MUTED)
ax.set_yticks(list(y)); ax.set_yticklabels(BUGS); ax.invert_yaxis()
ax.set_xlabel("mean cost per run (USD)")
ax.set_title("FCDD was dearer on 7 of 7 defects  (sign test $p$ = 0.0156)",
             fontsize=9.5, loc="left", pad=9)
ax.scatter([], [], s=40, color=A_COL, label=A_NAME); ax.scatter([], [], s=40, color=B_COL, label=B_NAME)
ax.legend(frameon=False, fontsize=8.5, loc="lower right")
ax.grid(axis="x", color=GRID, lw=.6); ax.set_axisbelow(True)
save(fig, "fig2_cost_per_defect")

# ---------------------------------------------------------------- fig3
fig, ax = plt.subplots(figsize=(5.6, 3.2))
for i, b in enumerate(BUGS):
    a_, b_ = cv(cells[(b, "A")]), cv(cells[(b, "B")])
    ax.plot([a_, b_], [i, i], color=GRID, lw=2.2, zorder=1, solid_capstyle="round")
    ax.scatter([a_], [i], s=40, color=A_COL, zorder=3, edgecolor="white", linewidth=.8)
    ax.scatter([b_], [i], s=40, color=B_COL, zorder=3, edgecolor="white", linewidth=.8)
ax.set_yticks(list(range(len(BUGS)))); ax.set_yticklabels(BUGS); ax.invert_yaxis()
ax.set_xlabel(r"CV of log cost within the 4-run cell  (lower = more predictable)")
ax.set_title("The predictability claim: FCDD is right of the control on 5 of 7",
             fontsize=9.5, loc="left", pad=9)
ax.scatter([], [], s=40, color=A_COL, label=A_NAME); ax.scatter([], [], s=40, color=B_COL, label=B_NAME)
ax.legend(frameon=False, fontsize=8.5, loc="lower right")
ax.grid(axis="x", color=GRID, lw=.6); ax.set_axisbelow(True)
save(fig, "fig3_dispersion")

# ---------------------------------------------------------------- fig4
fig, ax = plt.subplots(figsize=(5.6, 2.5))
labels = ["repaired program\n(both arms, 56 runs)",
          "%s artefact\n(28 runs)" % A_NAME, "%s specification\n(28 runs)" % B_NAME]
vals, cols = [1, 28, 23], [MUTED, A_COL, B_COL]
bars = ax.barh(range(3), vals, color=cols, height=.55, zorder=3)
for i, v in enumerate(vals):
    ax.annotate(str(v), (v, i), textcoords="offset points", xytext=(6, -3),
                fontsize=9, fontweight="bold", color=cols[i])
ax.set_yticks(range(3)); ax.set_yticklabels(labels, fontsize=8.5); ax.invert_yaxis()
ax.set_xlabel("distinct artefacts produced")
ax.set_title("The code converged; neither arm's own artefact did",
             fontsize=9.5, loc="left", pad=9)
ax.grid(axis="x", color=GRID, lw=.6); ax.set_axisbelow(True); ax.set_xlim(0, 31)
save(fig, "fig4_artefact_convergence")
print("done")
