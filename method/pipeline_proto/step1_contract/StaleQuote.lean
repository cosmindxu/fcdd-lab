/- Stale-quote guard — the SPEC OF RECORD for step0_REQUIREMENT.md.

   Lean 4 core, no mathlib: a small trusted surface, and the goals here are decidable
   enumeration plus structural induction, which core closes with `decide`/`simp`/`omega`.

   This file carries BOTH halves of the contract:
     * solution elements — `Reading`, `Verdict`, `stale`, `unread`, `verdict`. These are
       what the twin transcribes.
     * properties        — P1..P5 and the non-vacuity witnesses. These are what constrain
       the transcription, and what the bridge mirrors.

   Verify: ~/.elan/bin/lean StaleQuote.lean   (exit 0, zero sorry, axioms whitelisted) -/

namespace StaleQuote

/-- One price source's reading: a readable quote of some age, or an unreadable source. -/
inductive Reading where
  | ok (ageMs : Nat)
  | unreadable
  deriving DecidableEq

/-- Three-valued verdict. `unknown` is a real state, never a vacuous `trade`. -/
inductive Verdict where
  | trade
  | block
  | unknown
  deriving DecidableEq

/-- KNOWN-stale: readable, and older than the limit. An unreadable source is NOT stale —
    it is unknown, a distinction P2/P3 depend on. -/
def stale (limit : Nat) : Reading → Bool
  | .ok ageMs => decide (ageMs > limit)
  | .unreadable => false

def unread : Reading → Bool
  | .ok _ => false
  | .unreadable => true

/-- The guard. Safe-OR: any DANGER wins; absent DANGER any UNKNOWN wins; `trade` demands
    a non-empty set with every member readable and fresh. The `isEmpty` arm is the
    no-vacuous-trade fail direction made structural rather than incidental. -/
def verdict (limit : Nat) (rs : List Reading) : Verdict :=
  if rs.any (stale limit) then .block
  else if rs.any unread then .unknown
  else if rs.isEmpty then .unknown
  else .trade

/- ── Non-vacuity first (`spec_total`): every verdict class is REACHABLE. A class no input
      can produce would make its theorems vacuously true. -/
theorem reach_unknown_empty : verdict 100 [] = .unknown := by decide
theorem reach_unknown_unread : verdict 100 [.unreadable] = .unknown := by decide
theorem reach_trade : verdict 100 [.ok 50] = .trade := by decide
theorem reach_block : verdict 100 [.ok 500] = .block := by decide
theorem reach_block_dominates_unread : verdict 100 [.unreadable, .ok 500] = .block := by decide
theorem reach_unknown_mixed : verdict 100 [.ok 50, .unreadable] = .unknown := by decide

/- ── P1 — empty evidence never trades. -/
theorem p1_no_vacuous_trade (limit : Nat) : verdict limit [] = .unknown := by
  simp [verdict]

/- ── P2 — a known-stale reading forces BLOCK, whatever else is present. -/
theorem p2_block_dominates (limit : Nat) (rs : List Reading)
    (h : rs.any (stale limit) = true) : verdict limit rs = .block := by
  simp [verdict, h]

/- ── P3 — absent a stale reading, an unreadable source yields UNKNOWN. -/
theorem p3_unknown_never_trades (limit : Nat) (rs : List Reading)
    (hs : rs.any (stale limit) = false) (hu : rs.any unread = true) :
    verdict limit rs = .unknown := by
  simp [verdict, hs, hu]

/- ── P4 — nothing but positive fresh evidence produces a TRADE. -/
theorem p4_trade_needs_evidence (limit : Nat) (rs : List Reading)
    (h : verdict limit rs = .trade) :
    rs ≠ [] ∧ rs.any (stale limit) = false ∧ rs.any unread = false := by
  unfold verdict at h
  split at h
  · exact absurd h (by simp)
  · split at h
    · exact absurd h (by simp)
    · split at h
      · exact absurd h (by simp)
      · rename_i hs hu he
        refine ⟨?_, by simpa using hs, by simpa using hu⟩
        intro hnil; subst hnil; simp at he

/- ── P5 — tightening the limit never trades where a looser limit blocked. -/
theorem p5_stale_antitone (l1 l2 : Nat) (h : l1 ≤ l2) (r : Reading)
    (hs : stale l2 r = true) : stale l1 r = true := by
  cases r with
  | unreadable => simp [stale] at hs
  | ok ageMs => simp [stale] at hs ⊢; omega

/-- BLOCK is reached only through a stale reading — the inversion P5 needs. -/
theorem block_imp_stale (limit : Nat) (rs : List Reading)
    (hb : verdict limit rs = .block) : rs.any (stale limit) = true := by
  unfold verdict at hb
  split at hb
  · rename_i hcond; exact hcond
  · split at hb
    · exact absurd hb (by simp)
    · split at hb
      · exact absurd hb (by simp)
      · exact absurd hb (by simp)

theorem p5_block_antitone (l1 l2 : Nat) (h : l1 ≤ l2) (rs : List Reading)
    (hb : verdict l2 rs = .block) : verdict l1 rs = .block := by
  apply p2_block_dominates
  have hany := block_imp_stale l2 rs hb
  simp only [List.any_eq_true] at hany ⊢
  obtain ⟨r, hmem, hst⟩ := hany
  exact ⟨r, hmem, p5_stale_antitone l1 l2 h r hst⟩

/- ── P6 — the BOUNDARY. Added 2026-08-24 because bridge mutation `M4_boundary` (>= for >)
      SURVIVED every layer: P1..P5 constrain the shape of the verdict but never pin where
      fresh becomes stale, so an off-by-one was invisible. Found by execution, not review —
      the loop working as intended. `age == limit` is FRESH (the limit is inclusive). -/
theorem p6_boundary_is_fresh (limit : Nat) : stale limit (.ok limit) = false := by
  simp [stale]

theorem p6_boundary_trades : verdict 100 [.ok 100] = .trade := by decide

theorem p6_just_past_blocks : verdict 100 [.ok 101] = .block := by decide

end StaleQuote
