#!/usr/bin/env python3
"""
BRIDGE layer 1 — WITNESSES.

Every fact the Lean kernel proves in ../spec/Contract.lean §16 is re-checked
here against the SHIPPED twin.  If the twin ever drifts from the spec, this
layer goes red.  Judged by exit code.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "twin"))

from hc91_twin import *                                          # noqa: F403
from positions import *                                          # noqa: F403

FAILS = []
N = 0


def chk(name, got, want):
    global N
    N += 1
    if got != want:
        FAILS.append("%-34s got %r want %r" % (name, got, want))


h0 = History([7], 7)

# --- §16.1  spec totality, every guard live -------------------------------
chk("T1_start_is_play", updateTerminal(startPos, h0), PLAY)
chk("T2_start_20_moves", len(genLegal(startPos)), 20)
chk("T3_start_perft1", perft(startPos, 1), 20)

chk("T4_mate", updateTerminal(matePos, h0), WHITE_MATED)
chk("T4a_mate_no_moves", genLegal(matePos), [])
chk("T4b_mate_in_check", inCheckSide(matePos, WHITE), True)

chk("T5_stalemate", updateTerminal(stalematePos, h0), STALEMATE)
chk("T5a_stale_no_moves", genLegal(stalematePos), [])
chk("T5b_stale_not_in_check", inCheckSide(stalematePos, BLACK), False)

chk("T6_insufficient", updateTerminal(insufficientPos, h0), DRAW)
chk("T6a_insufficient_holds", isInsufficient(insufficientPos.board), True)
chk("T6b_insufficient_has_moves", genLegal(insufficientPos) != [], True)

chk("T7_fifty", updateTerminal(fiftyPos, h0), DRAW)
chk("T7a_fifty_not_insufficient", isInsufficient(fiftyPos.board), False)
chk("T7b_fifty_clock", fiftyPos.halfmove, 100)
chk("T7c_fifty_has_moves", genLegal(fiftyPos) != [], True)

chk("T8_repetition", updateTerminal(startPos, History([7, 9, 7, 4, 7], 7)), DRAW)
chk("T8a_rep_count", countReps(History([7, 9, 7, 4, 7], 7)), 3)
chk("T8b_two_is_not_a_draw", updateTerminal(startPos, History([7, 9, 4, 7], 7)), PLAY)

# --- §16.2  special-move guards, both directions --------------------------
chk("T9_castle_OO", mkMove(0x04, 0x06, SP_OO) in genLegal(castlePos), True)
chk("T9a_castle_OOO", mkMove(0x04, 0x02, SP_OOO) in genLegal(castlePos), True)
chk("T9b_through_check_kills_OO",
    mkMove(0x04, 0x06, SP_OO) in genLegal(castleBlockedPos), False)
chk("T9c_through_check_spares_OOO",
    mkMove(0x04, 0x02, SP_OOO) in genLegal(castleBlockedPos), True)
chk("T9d_no_rights_no_castle",
    mkMove(0x04, 0x06, SP_OO) in genLegal(castlePos.replace(castling=0)), False)

chk("T10_ep_generated", mkMove(0x44, 0x53, SP_EP) in genLegal(epPos), True)
chk("T10a_ep_needs_target",
    mkMove(0x44, 0x53, SP_EP) in genLegal(epPos.replace(ep=0xFF)), False)

chk("T11_promotions_count",
    len([m for m in genLegal(promoPos) if mvPromo(m) != 0]), 8)
for nm, fl in (("Q", 0x50), ("R", 0x40), ("B", 0x30), ("N", 0x20)):
    chk("T11_promo_" + nm, mkMove(0x61, 0x71, fl) in genLegal(promoPos), True)

# --- §16.3  make/unmake involution ---------------------------------------
def roundTrips(p, m):
    return unmakeMove(makeMove(p, m), undoOf(p, m)) == p


chk("T12a_unmake_dpush", roundTrips(startPos, mkMove(0x14, 0x34, SP_DPUSH)), True)
chk("T12b_unmake_quiet", roundTrips(startPos, mkMove(0x06, 0x25, 0)), True)
chk("T12c_unmake_ep", roundTrips(epPos, mkMove(0x44, 0x53, SP_EP)), True)
chk("T12d_unmake_OO", roundTrips(castlePos, mkMove(0x04, 0x06, SP_OO)), True)
chk("T12e_unmake_OOO", roundTrips(castlePos, mkMove(0x04, 0x02, SP_OOO)), True)
chk("T12f_unmake_promo", roundTrips(promoPos, mkMove(0x61, 0x71, 0x50)), True)
chk("T12g_unmake_promocap", roundTrips(promoPos, mkMove(0x61, 0x70, 0x50)), True)
chk("T12h_OO_changes", makeMove(castlePos, mkMove(0x04, 0x06, SP_OO)) == castlePos, False)
chk("T12i_ep_changes", makeMove(epPos, mkMove(0x44, 0x53, SP_EP)) == epPos, False)
chk("T12j_promo_changes",
    makeMove(promoPos, mkMove(0x61, 0x71, 0x50)) == promoPos, False)

for nm, p in (("start", startPos), ("castle", castlePos),
              ("promo", promoPos), ("kiwi", kiwiPos)):
    chk("T13_all_" + nm, all(roundTrips(p, m) for m in genLegal(p)), True)

# --- §16.4  safety consequences ------------------------------------------
for nm, p, m in (("dpush", startPos, mkMove(0x14, 0x34, SP_DPUSH)),
                 ("castle", castlePos, mkMove(0x04, 0x06, SP_OO)),
                 ("ep", epPos, mkMove(0x44, 0x53, SP_EP)),
                 ("promo", promoPos, mkMove(0x61, 0x70, 0x50)),
                 ("quiet", castlePos, mkMove(0x04, 0x03, 0)),
                 ("kiwi", kiwiPos, mkMove(0x44, 0x63, 0))):
    chk("T14_conf_" + nm, Conforming(obsOf(p, m, h0)), True)

chk("T15_legal_implies_king_safe",
    all((m not in genLegal(kiwiPos)) or (not moverInCheck(makeMove(kiwiPos, m)))
        for m in genMoves(kiwiPos)), True)
chk("T16a_pin_pseudo", len(genMoves(pinPos)), 10)
chk("T16b_pin_legal", len(genLegal(pinPos)), 4)
chk("T16c_pinned_piece_frozen",
    any(m.frm == 0x14 for m in genLegal(pinPos)), False)
chk("T17_kiwi_perft1", perft(kiwiPos, 1), 48)

# --- §16.5  eval antisymmetry --------------------------------------------
for nm, p in (("start", startPos), ("castle", castlePos), ("promo", promoPos),
              ("kiwi", kiwiPos), ("ep", epPos)):
    chk("T19_sym_" + nm, evalWhite(mirrorPos(p)), -evalWhite(p))
chk("T19f_kiwi_nonzero", evalWhite(kiwiPos) != 0, True)
chk("T19g_promo_nonzero", evalWhite(promoPos) != 0, True)
chk("T20a_start_balanced", evalWhite(startPos), 0)
chk("T20b_stm_relative", eval_(kiwiPos.replace(stm=BLACK)), -eval_(kiwiPos))

# --- §16.7  ply bound ----------------------------------------------------
chk("T22_movebuf_in_range",
    all(0x6000 + ply * 512 + 511 <= 0x7FFF for ply in range(MAXPLY + 1)), True)
chk("T23_undo_below_killers",
    all(0xD000 + ply * 16 + 15 < 0xD100 for ply in range(MAXPLY + 1)), True)
chk("T23a_movebuf_tight", 0x6000 + (MAXPLY + 1) * 512 + 511 <= 0x7FFF, False)
chk("T23b_undo_tight", 0xD000 + (MAXPLY + 1) * 16 + 15 < 0xD100, False)

# --- §16.8  the baseline conforms ----------------------------------------
base = obsOf(startPos, mkMove(0x14, 0x34, SP_DPUSH), h0)
chk("T25_base_conforms", failedClauses(base), [])

print("[b1_witnesses] %d checks, %d failures" % (N, len(FAILS)))
for f in FAILS:
    print("  FAIL " + f)
sys.exit(1 if FAILS else 0)
