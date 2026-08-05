#!/usr/bin/env python3
"""Publication figures for the FCDD cost study.

Palette: dataviz default categorical slots 1-2 (#2a78d6 blue, #eb6834 orange),
validated colourblind-safe for this pair (worst-case protan ΔE 24.7, normal
33.6, both well above the 8/15 floors). Print target, so no interaction layer;
identity is carried by legend AND position AND direct labels, never by colour
alone. Greyscale-safe as a secondary check: the two hues differ in lightness.

Outputs PDF (vector, for LaTeX) and PNG (for review) into this directory.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

A_COL, B_COL = "#2a78d6", "#eb6834"
INK, MUTED, GRID = "#1a1a1a", "#5a5a5a", "#d8d8d6"

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

# ---- data (v4 cells; bug03/B is the transcript-recovered figure) -----------
BUGS = ["bug01", "bug02", "bug03", "bug04", "bug05", "bug06", "bug07"]
LABELS = ["quiescence\nguard", "fifty-move\nclock", "promotion\nassembly",
          "eval\nsign", "castling\nrights", "TT depth\nbound", "mate\ndetection"]
# bug03/B imputed at pre-registered rates (was $45.76 via a borrowed blended
# rate, ~1.6x inflated); bug05/B is a lower bound (interrupted, gate passes).
A = [44.27, 7.32, 11.96, 11.30, 8.88, 16.44, 7.11]
B = [49.63, 50.37, 23.98, 55.40, 21.70, 48.69, 24.19]
A_ALL = A
QUAL_AXES = ["Correctness\nrisk", "Clarity", "Test\nquality", "Overall"]
QUAL_A = [4.25, 4.50, 4.25, 4.33]
QUAL_B = [4.50, 4.25, 5.00, 4.58]   # shown for completeness; comparison withdrawn
# reviewer count vs cost, pooled across cells (instrument finding §4.3)
REV_N = [1, 2, 5, 8, 14, 2, 1, 1, 1, 2, 3, 4, 1, 3, 5]
REV_USD = [8.66, 14.68, 43.46, 106.69, 60.68, 7.32, 11.96, 11.30, 8.88,
           16.44, 49.63, 50.37, 7.11, 44.27, 55.40]
REV_ARM = list("ABBBA" "AAAA" "ABBAAB")


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(f"{name}.{ext}", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  {name}.pdf / .png")


# ---- Figure 2: paired cost per defect --------------------------------------
fig, ax = plt.subplots(figsize=(6.6, 3.1))
x = np.arange(len(BUGS))
w = 0.38
ax.bar(x - w/2, A, w, color=A_COL, label="Ordinary dev + review", zorder=3)
ax.bar(x + w/2, B, w, color=B_COL, label="FCDD", zorder=3)
for i, (a, b) in enumerate(zip(A, B)):
    ax.text(i - w/2, a + 1.2, f"{a:.0f}", ha="center", fontsize=7.5, color=MUTED)
    ax.text(i + w/2, b + 1.2, f"{b:.0f}", ha="center", fontsize=7.5, color=MUTED)
    ax.text(i, max(a, b) + 6.5, f"{b/a:.1f}×", ha="center", fontsize=8,
            color=INK, fontweight="bold")
ax.set_xticks(x, LABELS, fontsize=7.5)
ax.set_ylabel("Cost per defect (USD, list-price index)")
ax.set_ylim(0, 68)
ax.yaxis.grid(True, color=GRID, lw=0.6, zorder=0)
ax.set_axisbelow(True)
ax.legend(frameon=False, loc="upper right", fontsize=8)
save(fig, "fig2_cost_per_defect")

# ---- Figure 3: dispersion ---------------------------------------------------
fig, ax = plt.subplots(figsize=(4.0, 3.1))
for i, (vals, col, name) in enumerate([(A_ALL, A_COL, "Ordinary\ndev + review"),
                                       (B, B_COL, "FCDD")]):
    jit = np.linspace(-0.07, 0.07, len(vals))
    ax.scatter([i + j for j in jit], vals, s=34, color=col, zorder=3,
               edgecolor="white", linewidth=0.8)
    ax.plot([i - 0.22, i + 0.22], [np.median(vals)] * 2, color=col, lw=2.2, zorder=4)
    ax.annotate("", xy=(i + 0.32, min(vals)), xytext=(i + 0.32, max(vals)),
                arrowprops=dict(arrowstyle="<->", color=MUTED, lw=0.9))
    ax.text(i + 0.38, np.sqrt(min(vals) * max(vals)),
            f"{max(vals)/min(vals):.1f}×\nspread", fontsize=7.5, color=MUTED, va="center")
ax.set_xticks([0, 1], ["Ordinary\ndev + review", "FCDD"], fontsize=8)
ax.set_xlim(-0.45, 1.75)
ax.set_ylabel("Cost per defect (USD)")
ax.yaxis.grid(True, color=GRID, lw=0.6, zorder=0)
ax.set_axisbelow(True)
ax.text(0.02, 0.985, "horizontal bar = median", transform=ax.transAxes,
        fontsize=7, color=MUTED, va="top")
ax.text(0.02, 0.925,
        "excluding bug01: 2.31× vs 2.55×\n(finding withdrawn)",
        transform=ax.transAxes, fontsize=7, color="#8a1f1f", va="top")
save(fig, "fig3_dispersion")

# ---- Figure 4: blinded quality ---------------------------------------------
fig, ax = plt.subplots(figsize=(4.6, 3.0))
y = np.arange(len(QUAL_AXES))
h = 0.36
ax.barh(y + h/2, QUAL_A, h, color=A_COL, label="Ordinary dev + review", zorder=3)
ax.barh(y - h/2, QUAL_B, h, color=B_COL, label="FCDD", zorder=3)
for i, (a, b) in enumerate(zip(QUAL_A, QUAL_B)):
    ax.text(a + 0.06, i + h/2, f"{a:.2f}", va="center", fontsize=7.5, color=MUTED)
    ax.text(b + 0.06, i - h/2, f"{b:.2f}", va="center", fontsize=7.5, color=MUTED)
ax.axvline(3, color=MUTED, ls=(0, (4, 3)), lw=1)
ax.text(3.04, len(QUAL_AXES) - 0.35, "gate threshold", fontsize=7, color=MUTED)
ax.set_yticks(y, QUAL_AXES, fontsize=8)
ax.set_xlim(0, 5.6)
ax.set_xlabel("Blinded rubric score (1–5, n = 4 pairs)")
ax.xaxis.grid(True, color=GRID, lw=0.6, zorder=0)
ax.set_axisbelow(True)
ax.legend(frameon=False, loc="lower right", fontsize=8)
save(fig, "fig4_quality")

# ---- Figure 5: the instrument finding ---------------------------------------
fig, ax = plt.subplots(figsize=(4.6, 3.0))
for arm, col, name in (("A", A_COL, "Ordinary dev + review"), ("B", B_COL, "FCDD")):
    xs = [n for n, a in zip(REV_N, REV_ARM) if a == arm]
    ys = [u for u, a in zip(REV_USD, REV_ARM) if a == arm]
    ax.scatter(xs, ys, s=40, color=col, label=name, zorder=3,
               edgecolor="white", linewidth=0.8)
z = np.polyfit(REV_N, REV_USD, 1)
xr = np.array([0.6, 14.6])
ax.plot(xr, np.poly1d(z)(xr), color=MUTED, lw=1.2, ls=(0, (5, 3)), zorder=2)
r = np.corrcoef(REV_N, REV_USD)[0, 1]
ax.text(0.03, 0.96, f"pooled r = {r:.2f}", transform=ax.transAxes,
        fontsize=8, color=INK, va="top")
ax.annotate("unbounded review:\n12 rounds, 85 findings,\nno defect in the fix",
            xy=(14, 60.68), xytext=(8.4, 88), fontsize=7, color=MUTED,
            arrowprops=dict(arrowstyle="->", color=MUTED, lw=0.8))
ax.set_xlabel("Reviewer invocations in the cell")
ax.set_ylabel("Cost of the cell (USD)")
ax.set_ylim(0, 118)
ax.yaxis.grid(True, color=GRID, lw=0.6, zorder=0)
ax.set_axisbelow(True)
ax.legend(frameon=False, loc="lower right", fontsize=8)
save(fig, "fig5_review_effort_vs_cost")

print("figures written")
