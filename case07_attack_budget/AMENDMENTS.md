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
