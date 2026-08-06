#!/usr/bin/env python3
"""Publication figures for the FCDD predictability/cost study (v5 reframe).

Supersedes figures/make_figures.py (which generated the v4 draft's figures,
including a fig4 built from the VOIDED first grading round). Every number
plotted here is re-derivable from the deposited artefacts:

  fig1  FCDD method: build-once beats + both arms' per-defect pipelines
        (structure from ~/.claude/skills/formal-contract-dev/SKILL.md and the
        prompt packs; counts from ledger/runs.csv row `step1` and the
        per-cell Contract.lean diffs re-counted 2026-08-06)
  fig2  paired cost per defect          -> tools/analyse.py
  fig3  dispersion: across defects + the bug01 replication
                                        -> tools/analyse_predictability.py
  fig4  counterbalanced quality round   -> tools/analyse_predictability.py
  fig5  cost vs reviewer invocations    -> tools/analyse_predictability.py
        (v4 cells only; the v3 unbounded-rule cells are excluded because
        amendment A10 rules them non-comparable on cost)

Outputs PDF (vector, for LaTeX) and PNG (for review) into figures/, then
copies them into paper/ and paper_springer/.

Palette: dataviz categorical slots 1-2 (#2a78d6 blue = Arm A, #eb6834
orange = Arm B/FCDD), colourblind- and greyscale-safe for this pairing.
Identity is always carried by position/label as well as colour.
"""
import os
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

CASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGDIR = os.path.join(CASE, "figures")

A_COL, B_COL = "#2a78d6", "#eb6834"
INK, MUTED, GRID = "#1a1a1a", "#5a5a5a", "#d8d8d6"
A_NAME, B_NAME = "Ordinary dev + review", "FCDD"

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Nimbus Roman", "DejaVu Serif"],
    "font.size": 9,
    "axes.edgecolor": MUTED,
    "axes.labelcolor": INK,
    "text.color": INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
})


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(FIGDIR, f"{name}.{ext}"),
                    bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  {name}.pdf / .png")


# ---- data (all re-derivable; see module docstring) --------------------------
BUGS = ["bug01", "bug02", "bug03", "bug04", "bug05", "bug06", "bug07"]
LABELS = ["quiescence\nguard", "fifty-move\nclock", "promotion\nassembly",
          "eval\nsign", "castling\nrights", "TT depth\nbound", "mate\ndetection"]
A = [44.27, 7.32, 11.96, 11.30, 8.88, 16.44, 7.11]   # platform USD, v4
B = [49.63, 50.37, 23.98, 55.40, 31.05, 48.69, 24.19]  # bug03/B imputed (D3)
REV_A = [3, 2, 1, 1, 1, 2, 1]
REV_B = [3, 4, 1, 5, 1, 3, 1]
# bug01 replication, v4 instrument, attempts summed (analyse_predictability.py)
B01_A = [(44.27, "redesign"), (11.78, "minimal"), (41.35, "redesign")]
B01_B = [(49.63, "minimal"), (79.28, "minimal"), (51.40, "minimal")]
# counterbalanced quality round, 7 pairs x 2 orders (analyse_predictability.py)
QUAL_AXES = ["Correctness\nrisk", "Clarity", "Test\nquality", "Composite"]
QUAL_A = [4.36, 4.64, 4.14, 4.38]
QUAL_B = [4.50, 4.29, 4.86, 4.55]
PAIR_DIFF = [1.17, 0.00, -0.83, 0.17, -0.17, 0.83, 0.00]   # composite B-A
DIFF_CI = (-0.44, 0.78)


# ============================================================ Figure 1: method
def box(ax, x, y, w, h, title, body, fc, ec, title_c="white", body_c=None,
        fs_t=7.6, fs_b=6.6, lw=1.0, dy=0.033):
    """Rounded box with a bold title anchored at the top and the body text
    anchored below it at a deterministic offset (dy per title line), so
    multi-line titles can never overlap the body."""
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.006",
                                fc=fc, ec=ec, lw=lw, zorder=3))
    if not body:
        ax.text(x + w / 2, y + h / 2, title, ha="center", va="center",
                fontsize=fs_t, fontweight="bold", color=title_c, zorder=4,
                linespacing=1.2)
        return
    n_t = title.count("\n") + 1
    ax.text(x + w / 2, y + h - 0.014, title, ha="center", va="top",
            fontsize=fs_t, fontweight="bold", color=title_c, zorder=4,
            linespacing=1.2)
    ax.text(x + w / 2, y + h - 0.020 - n_t * dy, body, ha="center", va="top",
            fontsize=fs_b, color=body_c or title_c, zorder=4,
            linespacing=1.25)


def arrow(ax, x0, y0, x1, y1, color=MUTED, style="-|>", lw=1.0, ls="-"):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style,
                                 mutation_scale=9, color=color, lw=lw,
                                 linestyle=ls, zorder=2))


fig, ax = plt.subplots(figsize=(7.4, 5.3))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")
DARK, PALE_B, PALE_A, PALE = "#20344c", "#fdeee6", "#e8f0fb", "#f4f4f2"

# --- band 1: build once ---
ax.add_patch(FancyBboxPatch((0.010, 0.660), 0.980, 0.325,
                            boxstyle="round,pad=0.004", fc="#fbf8ec",
                            ec=MUTED, lw=0.8, zorder=1))
ax.text(0.020, 0.968, "BUILD ONCE — the contract package "
        "(separately metered: $21.75; Arm B only)",
        fontsize=8.0, fontweight="bold", color=INK, va="top", zorder=4)
bw, bh, by = 0.225, 0.230, 0.678
xs = [0.022, 0.269, 0.516, 0.763]
box(ax, xs[0], by, bw, bh, "1 · PROVE",
    "spec of record: Contract.lean\n1,271 lines · 95 theorems\n"
    "zero sorry · empty axioms\ntier: kernel-evaluated\nfinite-scope checks (rfl)",
    DARK, DARK, dy=0.030)
box(ax, xs[1], by, bw, bh, "2 · TWIN",
    "pure twin implementation\nclause-for-clause\ntranscription\nno I/O, no clocks",
    DARK, DARK, dy=0.030)
box(ax, xs[2], by, bw, bh, "3 · BRIDGE",
    "conformance suite:\nwitnesses conform, violating\ninputs fail the right clause\n"
    "samples agreement —\nnot a refinement proof",
    DARK, DARK, dy=0.030)
box(ax, xs[3], by, bw, bh, "4 · ATTACK",
    "adversarial review,\nindependent reviewers,\ndistinct lenses; findings\n"
    "fixed at the causing layer",
    DARK, DARK, dy=0.030)
for i in range(3):
    arrow(ax, xs[i] + bw, by + bh / 2, xs[i + 1], by + bh / 2, lw=1.2)

# --- per-defect input ---
box(ax, 0.010, 0.385, 0.150, 0.165, "PER DEFECT",
    "symptom-level\nbug report\n(no location,\nno cause)", PALE, MUTED,
    title_c=INK, body_c=INK)

# --- lane B ---
ax.text(0.175, 0.560, "Arm B — FCDD repair session (fresh context; "
        "contract package on disk)", fontsize=7.4, fontweight="bold",
        color=B_COL, va="bottom")
lbw, lbh, lby = 0.148, 0.150, 0.395
lxs = [0.175, 0.3355, 0.496, 0.6565, 0.817]
box(ax, lxs[0], lby, lbw, lbh, "locate violated\nclause",
    "run bridge on the\nfaulty build", PALE_B, B_COL, title_c=INK,
    body_c=MUTED, fs_t=7.2)
box(ax, lxs[1], lby, lbw, lbh, "extend contract\nif uncovered",
    "+12 to +35 theorems\nobserved per cell", PALE_B, B_COL,
    title_c=INK, body_c=MUTED, fs_t=7.2)
box(ax, lxs[2], lby, lbw, lbh, "fix, then\nre-prove",
    "kernel gate green,\nzero sorry", PALE_B, B_COL, title_c=INK,
    body_c=MUTED, fs_t=7.2)
box(ax, lxs[3], lby, lbw, lbh, "bridge",
    "conformance suite\npasses on the fix",
    PALE_B, B_COL, title_c=INK, body_c=MUTED, fs_t=7.2)
box(ax, lxs[4], lby, lbw, lbh, "attack",
    "independent\nreviewers, ≤3 rounds", PALE_B, B_COL,
    title_c=INK, body_c=MUTED, fs_t=7.2)
for i in range(4):
    arrow(ax, lxs[i] + lbw, lby + lbh / 2, lxs[i + 1], lby + lbh / 2,
          color=B_COL)

# --- lane A ---
ax.text(0.175, 0.305, "Arm A — ordinary repair session (fresh context; "
        "no formal-methods vocabulary)", fontsize=7.4,
        fontweight="bold", color=A_COL, va="bottom")
lay = 0.140
axs_ = [0.175, 0.3355, 0.496, 0.6565]
box(ax, axs_[0], lay, lbw, lbh, "reproduce\nsymptom",
    "emulator harness", PALE_A, A_COL, title_c=INK, body_c=MUTED, fs_t=7.2)
box(ax, axs_[1], lay, lbw, lbh, "fix", "Z80 assembly\nedit", PALE_A, A_COL,
    title_c=INK, body_c=MUTED, fs_t=7.2)
box(ax, axs_[2], lay, lbw, lbh, "add / adjust\ntests",
    "regression stays\ngreen",
    PALE_A, A_COL, title_c=INK, body_c=MUTED, fs_t=7.2)
box(ax, axs_[3], lay, lbw, lbh, "review",
    "fresh reviewer,\n≤3 rounds", PALE_A, A_COL, title_c=INK, body_c=MUTED,
    fs_t=7.2)
for i in range(3):
    arrow(ax, axs_[i] + lbw, lay + lbh / 2, axs_[i + 1], lay + lbh / 2,
          color=A_COL)

# gate (shared)
box(ax, 0.822, 0.140, 0.168, 0.150, "SEALED\nACCEPTANCE\nGATE",
    "written before any\nrepair; hash published", "#3d3d3b", "#3d3d3b",
    fs_t=7.0, fs_b=6.2, dy=0.028)
arrow(ax, axs_[3] + lbw, lay + lbh / 2, 0.822, lay + lbh / 2, color=A_COL)
arrow(ax, lxs[4] + lbw / 2, lby, 0.906, 0.292, color=B_COL)

# input feeds
arrow(ax, 0.160, 0.505, 0.175, 0.480, color=MUTED)
arrow(ax, 0.160, 0.430, 0.175, 0.225, color=MUTED)
# contract feeds lane B
arrow(ax, 0.730, 0.660, 0.730, 0.550, color=B_COL, ls=(0, (4, 3)))
ax.text(0.718, 0.610, "contract constrains the repair: the fix must name "
        "its clause and leave every theorem green", fontsize=6.4, color=MUTED,
        va="center", ha="right")

ax.text(0.010, 0.100, "Residuals the method itself states: the contract "
        "establishes coherence, never correctness of intent; the bridge "
        "samples agreement and cannot catch a\nspec–twin common-mode error. "
        "In this study the contract was built from the pristine engine — an "
        "oracle asymmetry Arm A does not share (see the paper's\noracle-"
        "asymmetry disclosure).",
        fontsize=6.6, color=MUTED, va="top")
save(fig, "fig1_fcdd_process")

# ==================================================== Figure 2: cost per defect
fig, ax = plt.subplots(figsize=(6.6, 3.1))
x = np.arange(len(BUGS))
w = 0.38
ax.bar(x - w / 2, A, w, color=A_COL, label=A_NAME, zorder=3)
ax.bar(x + w / 2, B, w, color=B_COL, label=B_NAME, zorder=3)
for i, (a, b) in enumerate(zip(A, B)):
    ax.text(i - w / 2, a + 1.2, f"{a:.0f}", ha="center", fontsize=7.5, color=MUTED)
    ax.text(i + w / 2, b + 1.2, f"{b:.0f}", ha="center", fontsize=7.5, color=MUTED)
    ax.text(i, max(a, b) + 6.5, f"{b/a:.1f}×", ha="center", fontsize=8,
            color=INK, fontweight="bold")
ax.set_xticks(x, LABELS, fontsize=7.5)
ax.set_ylabel("Cost per defect (USD, list-price index)")
ax.set_ylim(0, 68)
ax.yaxis.grid(True, color=GRID, lw=0.6, zorder=0)
ax.set_axisbelow(True)
ax.legend(frameon=False, loc="upper right", fontsize=8)
save(fig, "fig2_cost_per_defect")

# ============================== Figure 3: dispersion + the bug01 replication
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.8, 3.0),
                               gridspec_kw={"width_ratios": [1, 1.15]})
# (a) across defects
for i, (vals, col) in enumerate([(A, A_COL), (B, B_COL)]):
    jit = np.linspace(-0.07, 0.07, len(vals))
    for j, v in zip(jit, vals):
        is01 = (v == vals[0])
        ax1.scatter(i + j, v, s=34, facecolor="white" if is01 else col,
                    edgecolor=col, linewidth=1.2, zorder=3)
    ax1.plot([i - 0.2, i + 0.2], [np.median(vals)] * 2, color=col, lw=2.2,
             zorder=4)
ax1.scatter([], [], s=34, facecolor="white", edgecolor=MUTED, linewidth=1.2,
            label="bug01 cell")
ax1.set_xticks([0, 1], ["Ordinary\ndev + review", "FCDD"], fontsize=8)
ax1.set_xlim(-0.5, 1.6)
ax1.set_ylim(0, 85)
ax1.set_ylabel("Cost per defect (USD)")
ax1.yaxis.grid(True, color=GRID, lw=0.6, zorder=0)
ax1.set_axisbelow(True)
ax1.legend(frameon=False, loc="upper left", fontsize=7)
ax1.set_title("(a) Across defects (7 cells per arm)", fontsize=8.5)
ax1.text(0.03, 0.87, "all cells: 6.2× vs 2.3× spread\nexcluding bug01: "
         "2.31× vs 2.31×\n— identical", transform=ax1.transAxes, fontsize=7,
         color=INK, va="top")
# (b) bug01 replicates
for i, (runs, col) in enumerate([(B01_A, A_COL), (B01_B, B_COL)]):
    jit = np.linspace(-0.06, 0.06, len(runs))
    for j, (usd, mode) in zip(jit, runs):
        ax2.scatter(i + j, usd, s=52 if mode == "redesign" else 40,
                    marker="D" if mode == "redesign" else "o", color=col,
                    edgecolor="white", linewidth=0.8, zorder=3)
ax2.scatter([], [], s=40, marker="o", color=MUTED, label="minimal one-byte fix")
ax2.scatter([], [], s=52, marker="D", color=MUTED, label="quiescence redesign")
ax2.set_xticks([0, 1], ["Ordinary\ndev + review", "FCDD"], fontsize=8)
ax2.set_xlim(-0.5, 1.75)
ax2.set_ylim(0, 85)
ax2.yaxis.grid(True, color=GRID, lw=0.6, zorder=0)
ax2.set_axisbelow(True)
ax2.legend(frameon=False, loc="lower right", fontsize=7)
ax2.set_title("(b) One defect replicated (bug01, three runs per arm)",
              fontsize=8.5)
ax2.annotate("forks between two\nstrategies, 3.8× apart", xy=(0.08, 28),
             fontsize=7, color=A_COL, ha="left")
ax2.annotate("same strategy\nevery run (1.6×,\nCV 0.28)", xy=(1.12, 60),
             fontsize=7, color=B_COL, ha="left")
ax2.text(0.02, 0.965, "Fisher exact on strategy×arm p = 0.40;\n"
         "3-vs-3 permutation floor p = 0.10 —\nsuggestive, not testable at this k",
         transform=ax2.transAxes, fontsize=7, color=INK, va="top")
save(fig, "fig3_dispersion")

# ================================= Figure 4: counterbalanced quality grading
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.8, 2.9),
                               gridspec_kw={"width_ratios": [1.2, 1]})
y = np.arange(len(QUAL_AXES))
h = 0.36
ax1.barh(y + h / 2, QUAL_A, h, color=A_COL, label=A_NAME, zorder=3)
ax1.barh(y - h / 2, QUAL_B, h, color=B_COL, label=B_NAME, zorder=3)
for i, (a, b) in enumerate(zip(QUAL_A, QUAL_B)):
    ax1.text(a + 0.06, i + h / 2, f"{a:.2f}", va="center", fontsize=7.5,
             color=MUTED)
    ax1.text(b + 0.06, i - h / 2, f"{b:.2f}", va="center", fontsize=7.5,
             color=MUTED)
ax1.axvline(3, color=MUTED, ls=(0, (4, 3)), lw=1)
ax1.text(2.94, -0.44, "gate floor", fontsize=7, color=MUTED, ha="right")
ax1.set_yticks(y, QUAL_AXES, fontsize=8)
ax1.invert_yaxis()
ax1.set_xlim(0, 5.75)
ax1.set_xlabel("Mean rubric score (1–5), 7 pairs × 2 orders")
ax1.xaxis.grid(True, color=GRID, lw=0.6, zorder=0)
ax1.set_axisbelow(True)
# direct labels instead of a legend (nothing to overlap the bars)
ax1.text(0.12, 0 + h / 2, A_NAME, va="center", fontsize=7, color="white",
         zorder=4)
ax1.text(0.12, 0 - h / 2, B_NAME, va="center", fontsize=7, color="white",
         zorder=4)
ax1.set_title("(a) Axis means, all seven pairs", fontsize=8.5)
# (b) paired composite differences
xp = np.arange(len(PAIR_DIFF))
ax2.axhline(0, color=MUTED, lw=1)
ax2.axhspan(DIFF_CI[0], DIFF_CI[1], color=GRID, alpha=0.45, zorder=0)
ax2.scatter(xp, PAIR_DIFF, s=42, color=INK, zorder=3,
            edgecolor="white", linewidth=0.8)
ax2.annotate("bug01", xy=(0, PAIR_DIFF[0]), xytext=(0.35, 1.12), fontsize=7,
             color=MUTED)
ax2.set_xticks(xp, [f"{i+1:02d}" for i in range(7)], fontsize=7.5)
ax2.set_xlabel("Defect pair")
ax2.set_ylabel("Composite diff (FCDD − ordinary)")
ax2.set_ylim(-1.6, 1.6)
ax2.set_axisbelow(True)
ax2.text(0.03, 0.05, "mean +0.17,\n95% CI [−0.44, +0.78]\nspans zero",
         transform=ax2.transAxes, fontsize=7, color=INK, va="bottom")
ax2.set_title("(b) Paired differences", fontsize=8.5)
save(fig, "fig4_quality")

# ===================================== Figure 5: cost vs reviewer invocations
fig, ax = plt.subplots(figsize=(4.6, 3.0))
for revs, usds, col, name in ((REV_A, A, A_COL, A_NAME),
                              (REV_B, B, B_COL, B_NAME)):
    for i, (r, u) in enumerate(zip(revs, usds)):
        imputed = (name == B_NAME and BUGS[i] == "bug03")
        ax.scatter(r, u, s=40, facecolor="white" if imputed else col,
                   edgecolor=col, linewidth=1.2 if imputed else 0.8,
                   zorder=3)
    ax.scatter([], [], s=40, color=col, label=name)
ax.scatter([], [], s=40, facecolor="white", edgecolor=MUTED, linewidth=1.2,
           label="imputed cell (excluded from fit)")
# fit over the 13 cells with a deposited platform cost (bug03/B imputed cell
# excluded), matching tools/analyse_predictability.py
xs = REV_A + [r for i, r in enumerate(REV_B) if BUGS[i] != "bug03"]
ys = A + [u for i, u in enumerate(B) if BUGS[i] != "bug03"]
z = np.polyfit(xs, ys, 1)
xr = np.array([0.6, 5.4])
ax.plot(xr, np.poly1d(z)(xr), color=MUTED, lw=1.2, ls=(0, (5, 3)), zorder=2)
ax.text(0.03, 0.96, "reviewers alone $R^2$ = 0.71\narm alone $R^2$ = 0.58\n"
        "both $R^2$ = 0.87 (13 cells)", transform=ax.transAxes,
        fontsize=7.5, color=INK, va="top")
ax.set_xlabel("Reviewer invocations in the cell")
ax.set_ylabel("Cost of the cell (USD)")
ax.set_xticks([1, 2, 3, 4, 5])
ax.set_ylim(0, 62)
ax.yaxis.grid(True, color=GRID, lw=0.6, zorder=0)
ax.set_axisbelow(True)
ax.legend(frameon=False, loc="lower right", fontsize=8)
save(fig, "fig5_review_effort_vs_cost")

# ---- copy into both paper builds -------------------------------------------
for sub in ("paper", "paper_springer"):
    d = os.path.join(CASE, sub)
    if not os.path.isdir(d):
        continue
    for f in ("fig1_fcdd_process.pdf", "fig2_cost_per_defect.pdf",
              "fig3_dispersion.pdf", "fig4_quality.pdf",
              "fig5_review_effort_vs_cost.pdf"):
        shutil.copy(os.path.join(FIGDIR, f), os.path.join(d, f))
    print(f"  copied PDFs -> {sub}/")

print("figures written")
