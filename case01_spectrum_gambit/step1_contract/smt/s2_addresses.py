#!/usr/bin/env python3
"""
SMT tier — MEMORY-LAYOUT invariants (the ones that fit arithmetic better
than Lean, plus one that a solver can prove and reality already confirmed).

A1  per-ply move buffers stay inside 0x6000..0x7FFF for every ply <= MAXPLY
A2  per-ply undo records stay below killerArr (0xD100) for every ply <= MAXPLY
A3  BOTH bounds break at MAXPLY+1 — the cap is load-bearing, not slack
A4  the search's per-ply arrays (D4xx pages) do not overlap each other
A5  FINDING F5: the repetition key history gameKeys (0x5B00, 2 bytes/ply,
    cap 250) runs INTO the ZX Spectrum system-variable area from ply 128 and
    lands on FRAMES (0x5C78) at ply 188 — proved as a REACHABILITY, i.e. z3
    finds the witness ply rather than being told it.

A1-A3 are ALSO kernel-proved in ../spec/Contract.lean (T22, T23, T23a/b), so
these two independent verifiers satisfy the FCDD two-verifier rule for them.
A4/A5 are z3-only; see D-SMT-1 in ../DECISIONS.md.
"""
import sys

sys.path.insert(0, "/home/xcos/.venvs/quant/lib/python3.14/site-packages")
import z3                                                        # noqa: E402

FAILS = []
MAXPLY = 15

ply = z3.Int("ply")
inrange = z3.And(ply >= 0, ply <= MAXPLY)

# A1 — moveBufBase 0x6000, 512 bytes/ply
s = z3.Solver()
s.add(inrange)
s.add(z3.Or(0x6000 + ply * 512 < 0x6000, 0x6000 + ply * 512 + 511 > 0x7FFF))
if s.check() != z3.unsat:
    FAILS.append("A1 move buffer escapes 0x6000..0x7FFF at ply %s" % s.model())

# A2 — undoBase 0xD000, 16 bytes/ply, killerArr at 0xD100
s = z3.Solver()
s.add(inrange)
s.add(0xD000 + ply * 16 + 15 >= 0xD100)
if s.check() != z3.unsat:
    FAILS.append("A2 undo record reaches killerArr at ply %s" % s.model())

# A3 — non-vacuity / tightness: ply = MAXPLY+1 MUST break both
s = z3.Solver()
s.add(ply == MAXPLY + 1)
s.add(z3.Or(0x6000 + ply * 512 + 511 > 0x7FFF,
            0xD000 + ply * 16 + 15 >= 0xD100))
if s.check() != z3.sat:
    FAILS.append("A3 the ply cap is slack — MAXPLY+1 would still fit")

# A4 — the per-ply arrays on page 0xD4 must not overlap.
#      bestArr 0xD440 (2/ply), depthArr 0xD460 (1), legalArr 0xD470 (1),
#      mptrArr 0xD480 (2), cntArr 0xD4A0 (1), alphaArr 0xD4B0 (2),
#      betaArr 0xD4D0 (2), origAlphaArr 0xD4F0 (2)
ARRAYS = [("bestArr", 0xD440, 2), ("depthArr", 0xD460, 1), ("legalArr", 0xD470, 1),
          ("mptrArr", 0xD480, 2), ("cntArr", 0xD4A0, 1), ("alphaArr", 0xD4B0, 2),
          ("betaArr", 0xD4D0, 2), ("origAlphaArr", 0xD4F0, 2)]
for i, (n1, b1, w1) in enumerate(ARRAYS):
    for n2, b2, w2 in ARRAYS[i + 1:]:
        s = z3.Solver()
        p1, p2 = z3.Ints("p1 p2")
        s.add(p1 >= 0, p1 <= MAXPLY, p2 >= 0, p2 <= MAXPLY)
        s.add(b1 + p1 * w1 <= b2 + p2 * w2 + w2 - 1)
        s.add(b2 + p2 * w2 <= b1 + p1 * w1 + w1 - 1)
        if s.check() != z3.unsat:
            FAILS.append("A4 %s and %s overlap (%s)" % (n1, n2, s.model()))

# A5 — FINDING F5, as a reachability question: does ANY recordable ply land a
#      key on the ZX system variables?  z3 must FIND one (sat), and the
#      smallest such ply must be 128; FRAMES must be reachable too.
s = z3.Solver()
k = z3.Int("k")
s.add(k >= 0, k <= 249)                                  # recordGameKey cap
s.add(0x5B00 + 2 * k >= 0x5C00, 0x5B00 + 2 * k <= 0x5CB5)
if s.check() != z3.sat:
    FAILS.append("A5 no ply reaches the system variables — F5 needs review")
else:
    s.push()
    s.add(k < 128)
    if s.check() != z3.unsat:
        FAILS.append("A5 a ply below 128 already reaches the sysvars: %s" % s.model())
    s.pop()
    s.push()
    s.add(0x5B00 + 2 * k == 0x5C78)                      # FRAMES
    if s.check() != z3.sat:
        FAILS.append("A5 FRAMES is not reachable from gameKeys")
    else:
        frames_ply = s.model()[k].as_long()
        if frames_ply != 188:
            FAILS.append("A5 FRAMES ply is %d, expected 188" % frames_ply)
    s.pop()

print("[s2_addresses] z3: A1/A2 proved in-range for ply 0..%d, A3 tight, "
      "%d array-pair disjointness proofs, A5 reproduces finding F5 "
      "(gameKeys -> sysvars from ply 128, FRAMES at ply 188). %d failures"
      % (MAXPLY, len(ARRAYS) * (len(ARRAYS) - 1) // 2, len(FAILS)))
for f in FAILS:
    print("  FAIL " + f)
sys.exit(1 if FAILS else 0)
