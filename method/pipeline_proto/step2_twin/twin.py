"""Step 2 — the TWIN: a transcription of StaleQuote.lean's DEFINITIONS.

Transcription, not generation: every function below mirrors one Lean definition
line-for-line. What the theorems constrain, the bridge checks (step3_bridge).

Deliberately pure and dependency-free -- the shell (I/O, clocks, retries) is a separate
concern and a separate honesty problem (SKILL.md Beat 3.5).

MUTATIONS: env IKBR_TWIN_MUTATION selects a deliberate defect, used by the bridge to prove
each clause has a live negative test. Never set it in production.
"""
import os
from dataclasses import dataclass

MUTATION = os.environ.get("IKBR_TWIN_MUTATION", "")

# --- Reading: `inductive Reading | ok (ageMs : Nat) | unreadable` -------------------
@dataclass(frozen=True)
class Ok:
    age_ms: int
UNREADABLE = "unreadable"

def reading_ok(age_ms: int) -> Ok:
    return Ok(age_ms)

# --- Verdict: `inductive Verdict | trade | block | unknown` -------------------------
TRADE, BLOCK, UNKNOWN = "trade", "block", "unknown"

# --- `def stale (limit) : Reading -> Bool` -----------------------------------------
def stale(limit: int, r) -> bool:
    if isinstance(r, Ok):
        if MUTATION == "M4_boundary":
            return r.age_ms >= limit          # off-by-one at age == limit
        return r.age_ms > limit
    if MUTATION == "M2_unread_is_stale":
        return True                            # unreadable misread as DANGER
    return False

# --- `def unread : Reading -> Bool` ------------------------------------------------
def unread(r) -> bool:
    return not isinstance(r, Ok)

# --- `def verdict (limit) (rs) : Verdict` ------------------------------------------
def verdict(limit: int, rs) -> str:
    if MUTATION == "M3_unread_first":
        if any(unread(r) for r in rs):         # UNKNOWN checked before DANGER
            return UNKNOWN
        if any(stale(limit, r) for r in rs):
            return BLOCK
        return UNKNOWN if not rs else TRADE
    if any(stale(limit, r) for r in rs):
        return BLOCK
    if any(unread(r) for r in rs):
        return UNKNOWN
    if not rs:
        if MUTATION == "M1_empty_trades":
            return TRADE                       # vacuous SAFE on no evidence
        return UNKNOWN
    return TRADE
