# RESUME — paused mid-protocol at operator request (2026-07-31 00:47)

## How it was paused

The serial supervisor loop was stopped; the **cell in flight was left running
to completion** (armB:bug07, started 00:37). Nothing was killed mid-work, so
no cost was wasted and no workspace is half-finished.

## Where the protocol stands (updated 2026-08-01 21:40 — PAUSED)

**Prompt v4 is the current standard** (PROTOCOL A10): a review/attack round
that finds no defect in the fix CLOSES the gate; coverage findings are recorded
but do not compel another round; hard cap 3 rounds. v3 and earlier cells are
NOT cost-comparable and are being re-measured.

### v4 cells complete (the only figures that measure the intended quantity)

| cell | cost | reviewers | gate |
|---|---:|---:|---|
| armA:bug02 | **$7.32** (2 attempts) | 2 | PASS 11/11, pristine binary |
| armA:bug06 | **$16.44** (1 attempt) | 2 | PASS 10/10 — also fixed a LATENT pre-existing TT defect |
| armB:bug06 | **$48.69** raw / **$18.72** completing attempt | 3 | PASS 10/10 |

**First legitimate matched pair — bug06: A $16.44 vs B $48.69 raw (2.96x) or
$18.72 clean (1.14x).** The two bracket the honest ratio; B was interrupted
once and raw sums carry resumption overhead.

| armA:bug03 | **$11.96** (1 attempt) | 1 | PASS 14/14 |

### In flight at pause
None — `armA:bug03` finished cleanly at 22:16 and the queue is fully idle.

## Remaining queue (12 cells, in the intended order)

```
A:bug04 A:bug05 B:bug01 B:bug02 B:bug03 B:bug04 A:bug01 A:bug07 B:bug07 B:bug05
```
(bug07 pair is DONE; B:bug05 is finishing itself outside the queue. Adding
`B:bug05` back is only needed if its in-flight cell is abandoned.)

**Milestone note:** the first three of that list — `A:bug02 A:bug06 B:bug06` —
plus the self-finishing B:bug05 complete **seven matched pairs**, which is the
point at which the article's central table stands on its own. The remaining
seven cells are A7 re-runs of cells that already have valid-but-older data;
they buy metric purity, not coverage.

- First seven of those are cells that never completed with a closed review.
- The last five (A:03, A:04, A:05, B:01…B:04) are the A7 v3 re-runs of cells
  that only ever completed under the old dangling-review prompt.

## To resume exactly where it left off

```sh
cd /media/sf_Projects/fcdd_lab/case01_spectrum_gambit
QUEUE="A:bug07 B:bug05 A:bug02 A:bug06 B:bug06 A:bug03 A:bug04 A:bug05 B:bug01 B:bug02 B:bug03 B:bug04" \
  setsid nohup bash tools/supervisor2.sh >/dev/null 2>&1 &
```

Drop any cell from `QUEUE` to skip it. Each cell is independent; the runner
builds its own workspace, resumes itself across interruptions, and results
auto-book with `python3 tools/ingest.py`.

## After the queue: still owed before the article

1. **Blinded rubric grading** (gate item 3 — never run). Fresh graders, arm
   labels stripped, order alternated by bug parity, 1–5 on correctness-risk /
   clarity / test-quality. Without it, "equivalent quality" is an assumption.
2. **Sealed-gate verification** of each new v3 workspace
   (`bash sealed/acceptance/bugNN/check.sh <ws>/variants/bugNN`).
3. **Rewrite `REPORT.md`** on the v3 dataset — the interim numbers are
   provisional and probably inflated by infrastructure chaos (armA:bug01 cost
   3× more amid caps/outages than it did clean).
4. **Scientific article** (operator request 2026-07-30): protocol as
   pre-registered, all dated amendments A1–A9 as part of the honest record,
   method, results, threats, conclusions.
