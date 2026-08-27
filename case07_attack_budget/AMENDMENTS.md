# Case 07 — amendments to the pre-registration

Dated, appended, never rewritten.

## A1 — the gate probe is a REDUCED pilot, and runs without the §5 sandbox
**2026-08-27, written before any cell returned.**

§7 specifies a pilot of k = 2 per arm on 2 units, and §5 specifies bwrap
namespace isolation for every cell. What is running now departs from both:

- **Reduced scope.** Two CONV cells, k = 1, on the first unit of each stratum in
  the pre-registered order (`ib_risk.py` HARDENED, `live_guard.py` UNHARDENED —
  the order is descending-lines-within-stratum, alternating strata). No BUDGET
  cells. **This is a gate probe, not the §7 pilot:** it answers only the one
  question that can stop the study cheaply — *can unbounded review find a
  confirmed blocking finding in a codebase 64 prior adversarial reviews have
  already worked over?*
- **No bwrap.** Cells run as orchestrated subagents against the scrubbed tree
  (`tools/scrub.py`, assertions passing, 1,082 files), instructed read-only and
  explicitly forbidden to open sockets or contact a gateway. The isolation the
  scrub provides — no credentials, no `gateway/`, no archives, account id
  redacted — is real; the *namespace* isolation of §5 is not applied.

**Why this is acceptable here and not for scored runs.** The probe produces **no
scored data**. Its only output is a yes/no on the gate. Nothing it observes
enters the primary, the cost comparison, or any published number. A scored run
under these conditions would be inadmissible; a gate probe under them is a
cheaper way to reach the same stop decision.

**What it cannot tell us**, stated in advance so the result is not over-read:

- A **pass** (≥ 1 confirmed blocking finding) does not qualify the corpus. It
  says the corpus is not obviously exhausted; the §7 pilot still owes k, n,
  timeout and the b-floor projection.
- A **fail** is the more informative outcome and closer to decisive: if unbounded
  review with an execution requirement cannot produce one confirmed blocking
  finding across the two largest decision modules, the corpus is very likely
  unable to support H1 at any affordable n — round 3 already established that the
  achievable bound at 15 units is 20%, and a thin finding rate makes even that
  unreachable.
- Either way it says nothing about BUDGET, and nothing about the arms' contrast.

**Recorded before the results existed**, so the framing cannot be fitted to them.

---

## A2 — the gate passed, and the pilot found something that may retire the study
**2026-08-27, after both CONV cells returned.**

### The gate: PASSED

`live_guard.py` F2 — barrier E2 allows orders breaching `max_position_pct` /
`max_gross_exposure_pct`, because the caps are compared against **2-dp-rounded**
percentages. A true 10.001 % against a 10.0 % cap rounds to 10.00 and is
ALLOWED. **Wrong money-path action, reachable from both named callers**
(`ib_live.cmd_order` and the unattended mandate lane from cron), demonstrated by
probe and **independently re-verified by the orchestrator against the unscrubbed
source**. b ≥ 1: the corpus is not exhausted.

`ib_risk.py` added five more, including R3's 2026-08-03 fix never reaching the
third latch site — a lost HALT row is completely silent, so `LIVE_HALT` can exist
with no evidence row and nothing says so. Filed to the subject repository.

### The signal that matters more than the gate

**Both CONV cells ran exactly two rounds.** Their stated stopping reasons:

> *"Round 2 over the unchanged review surface produced no new confirmed
> findings — only the six residuals named above."*
> *"A third round would re-probe surfaces that returned only conformance in R2,
> which is the stopping condition as written."*

**Law 12's budget is one mandatory pass plus at most one scoped remediation —
two rounds.** So the *unbounded* arm did, unprompted, exactly what the *bounded*
arm is capped at. If that generalises, the treatment contrast in this study is
**nil**: BUDGET cannot miss what CONV finds, because CONV stops where BUDGET
stops, and H1 passes trivially without testing anything.

This is round 2's named worst case — *"a study that runs to completion and cannot
support or refute its hypothesis by construction"* — detected by a two-cell probe
instead of by a completed study. **That is the gate doing its job**, and it is why
§7 exists.

### What it implies about case 02's 18 rounds

The 1–18 round spread that motivated law 12 came from **repair against an
existing contract**, where each round re-reads a spec the agent itself edited.
Two cells of **fresh adversarial review of unfamiliar code** self-limited at 2.
The runaway may be specific to the repair-with-contract loop rather than a
property of the ATTACK beat — which would mean law 12's cap is **not binding in
the regime tested here**, and the safety question is moot in it.

**Consequence for case 07: the design must be re-decided before any scored run.**
Either the subject moves to the regime where the runaway was observed
(repair-against-a-contract), or the study is retired with this pilot as its
result. Recorded before either path is chosen.
