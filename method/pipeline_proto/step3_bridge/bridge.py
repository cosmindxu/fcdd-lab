"""Step 3 — the BRIDGE: conformance suite tying the twin to the kernel-proved facts.

Honest about its tier (SKILL.md Beat 3): it SAMPLES agreement -- finite witnesses, one
violating input per theorem, single-field mutations, brute force over a SMALL domain. It is
high-coverage conformance testing, NOT a proof of refinement. And it cannot catch
common-mode error: the same session wrote spec and twin here, so a shared misconception
would pass every layer below. That residual is real and is recorded in README.md.

Exit code is the verdict. Never judged by its tail.
"""
import itertools, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "step2_twin"))
import twin
from twin import Ok, UNREADABLE, TRADE, BLOCK, UNKNOWN

fails = []
def check(label, cond, detail=""):
    if cond:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}" + (f"  [{detail}]" if detail else ""))
        fails.append(label)

# ---------------------------------------------------------------- LAYER 1: WITNESSES
# Every kernel-proved witness (the reach_* theorems) must evaluate IDENTICALLY here.
print("-- layer 1: witnesses (mirror the reach_* theorems) --")
WITNESSES = [
    ("reach_unknown_empty",           100, [],                        UNKNOWN),
    ("reach_unknown_unread",          100, [UNREADABLE],              UNKNOWN),
    ("reach_trade",                   100, [Ok(50)],                  TRADE),
    ("reach_block",                   100, [Ok(500)],                 BLOCK),
    ("reach_block_dominates_unread",  100, [UNREADABLE, Ok(500)],     BLOCK),
    ("reach_unknown_mixed",           100, [Ok(50), UNREADABLE],      UNKNOWN),
    ("p6_boundary_trades",            100, [Ok(100)],                 TRADE),
    ("p6_just_past_blocks",           100, [Ok(101)],                 BLOCK),
]
for name, lim, rs, want in WITNESSES:
    got = twin.verdict(lim, rs)
    check(f"witness {name} -> {want}", got == want, f"got {got}")

# Non-vacuity mirrored: all three classes reachable in the twin too.
reached = {twin.verdict(l, rs) for _, l, rs, _ in WITNESSES}
check("non-vacuity: all three verdict classes reachable in the twin",
      reached == {TRADE, BLOCK, UNKNOWN}, f"reached {sorted(reached)}")

# ------------------------------------------------------- LAYER 2: THEOREM MIRRORS
# For each property, an input that would VIOLATE it must fail on the RIGHT clause.
print("-- layer 2: theorem mirrors (P1..P5) --")
check("P1 no-vacuous-trade: verdict(_, []) == unknown",
      twin.verdict(100, []) == UNKNOWN, twin.verdict(100, []))
check("P2 block-dominates: a stale member forces block despite an unreadable one",
      twin.verdict(100, [UNREADABLE, Ok(500), Ok(10)]) == BLOCK)
check("P3 unknown-never-trades: unreadable + only fresh -> unknown",
      twin.verdict(100, [Ok(10), UNREADABLE, Ok(20)]) == UNKNOWN)
check("P4 trade-needs-evidence: trade implies non-empty, no stale, no unread",
      all(rs and not any(twin.stale(l, r) for r in rs) and not any(twin.unread(r) for r in rs)
          for l, rs in [(100, [Ok(1)]), (100, [Ok(1), Ok(99)])]
          if twin.verdict(l, rs) == TRADE))
check("P5 limit-monotone: block at a looser limit still blocks at a tighter one",
      twin.verdict(50, [Ok(500)]) == BLOCK and twin.verdict(100, [Ok(500)]) == BLOCK)
check("P6 boundary: age == limit is FRESH (inclusive limit)",
      twin.stale(100, Ok(100)) is False and twin.verdict(100, [Ok(100)]) == TRADE,
      f"stale={twin.stale(100, Ok(100))} verdict={twin.verdict(100, [Ok(100)])}")

# --------------------------------------------- LAYER 3: ALGORITHM vs QUANTIFIER
# Exhaustive over a small domain: the twin must satisfy P1..P5 for EVERY reading list of
# length <= 3 drawn from a boundary-focused age set, at several limits.
print("-- layer 3: exhaustive small-domain sweep --")
AGES = [0, 1, 99, 100, 101, 500]
LIMITS = [0, 1, 100]
ATOMS = [Ok(a) for a in AGES] + [UNREADABLE]
viol = []
n = 0
for limit in LIMITS:
    for k in range(0, 4):
        for rs in itertools.product(ATOMS, repeat=k):
            rs = list(rs); n += 1
            v = twin.verdict(limit, rs)
            has_stale = any(twin.stale(limit, r) for r in rs)
            has_unread = any(twin.unread(r) for r in rs)
            if not rs and v == TRADE:                      viol.append(("P1", limit, rs, v))
            if has_stale and v != BLOCK:                   viol.append(("P2", limit, rs, v))
            if not has_stale and has_unread and v != UNKNOWN: viol.append(("P3", limit, rs, v))
            if v == TRADE and (not rs or has_stale or has_unread): viol.append(("P4", limit, rs, v))
            if any(isinstance(r, Ok) and r.age_ms == limit for r in rs) and \
               not any(isinstance(r, Ok) and r.age_ms > limit for r in rs) and v == BLOCK:
                viol.append(("P6", limit, rs, v))
            if v == BLOCK:
                for tighter in [l for l in LIMITS if l <= limit]:
                    if twin.verdict(tighter, rs) != BLOCK:  viol.append(("P5", limit, rs, v))
check(f"exhaustive sweep: {n} cases, 0 property violations",
      not viol, f"{len(viol)} violations, first: {viol[:1]}")

# ------------------------------------------------------- LAYER 4: MUTATION COVERAGE
# Every clause needs a LIVE negative test: a mutation that trips exactly that clause.
# Re-executed in a subprocess so the mutated twin is a fresh import.
print("-- layer 4: mutation coverage (each clause must have a live negative test) --")
if not os.environ.get("IKBR_TWIN_MUTATION"):
    import subprocess
    EXPECT = {
        "M1_empty_trades":     "P1",
        "M2_unread_is_stale":  "P3",
        "M3_unread_first":     "P2",
        "M4_boundary":         "P6",   # was surviving until P6 was added (see README)
    }
    for mut, want_clause in EXPECT.items():
        env = dict(os.environ, IKBR_TWIN_MUTATION=mut)
        r = subprocess.run([sys.executable, __file__], capture_output=True, text=True, env=env)
        caught = [ln for ln in r.stdout.splitlines() if ln.strip().startswith("FAIL")]
        if want_clause is None:
            check(f"mutation {mut}: SURVIVES (known property gap, not a bridge defect)",
                  r.returncode == 0, "unexpectedly caught -- update README R-1")
        else:
            hit = any(want_clause in ln for ln in caught)
            check(f"mutation {mut}: caught, and by {want_clause}",
                  r.returncode != 0 and hit,
                  f"rc={r.returncode} caught={[c.strip()[:60] for c in caught[:2]]}")

print()
if fails:
    print(f"BRIDGE FAILED: {len(fails)} check(s)")
    sys.exit(1)
print("BRIDGE GREEN")
sys.exit(0)
