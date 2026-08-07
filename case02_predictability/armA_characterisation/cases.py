#!/usr/bin/env python3
"""cases.py - the characterisation cases.

Each case is a scripted session against the engine.  Nothing here says what
chess rules require; the recorded observations in expected.json say what the
PRISTINE build did.  Choosing the positions is the only judgement exercised
here, and the criterion was coverage of the engine's *machinery* -- move
generation in crowded and sparse positions, the four special moves, the
terminal classifier, the state that has to survive a save/load, and the search
at depths that finish inside the engine's own time budget.

Fields
------
  name         unique id
  group        for --filter
  what         one line, printed next to the verdict
  kind         'session' (drive the game) | 'perft' (the engine's own self-test)
  fen          start position injected through the game's own tape-load (L);
               omit for a normal new game
  depth        engine strength 1..5; also the depth field of the injected block
  two_player   press V first -> the engine never moves, the script drives both
  pre          extra raw keys after the load
  moves        moves played with the cursor keys, e.g. 'e2e4', 'a7a8q'
  post         raw keys pressed after the moves, one gap apart (e.g. 'g' = save)
  cursor       square the cursor starts on (the game boots it on e2)
  expect_save  capture the game's own SAVE to tape and load it straight back
  machine      '48k' (default) or 'hc128'
  timeout      seconds

THE ILLEGAL-NUDGE IDIOM
-----------------------
The engine only materialises its legal-move list (genCount + the 4-byte
records at 0x6000) when it has to decide something.  A bare tape load leaves
the list empty, and so does picking up an enemy piece or an empty square -- the
game rejects those before generating.  Attempting an ILLEGAL move with one's
OWN piece does force generation, and leaves the position untouched.  So every
movegen case ends with one such attempt, which is also a test in its own right:
the status line must read 'Illegal move' and the position must be unchanged.
The nudge is always the last thing a case does.
"""

START = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
START_B = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1'
KIWI = 'r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1'
KIWI_B = 'r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R b KQkq - 0 1'
EPPOS = '8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1'
PROMO = 'n1n5/PPPk4/8/8/8/8/4Kppp/5N1N w - - 0 1'
PROMO_B = 'n1n5/PPPk4/8/8/8/8/4Kppp/5N1N b - - 0 1'
CASTLE = '4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1'


def _c(**kw):
    kw.setdefault('kind', 'session')
    kw.setdefault('depth', 2)
    kw.setdefault('two_player', False)
    kw.setdefault('moves', [])
    kw.setdefault('post', [])
    kw.setdefault('pre', '')
    kw.setdefault('cursor', 'e2')
    kw.setdefault('machine', '48k')
    return kw


CASES = [

    # ---------------------------------------------------------------- perft
    # The engine's own built-in self-test: perft 1-4 from the start position,
    # Kiwipete d3, an en-passant torture position d4, a promotion position d3,
    # and its incrementally maintained Zobrist key / game phase / PST
    # accumulator re-checked against a recomputation.  One keystroke buys a
    # multi-hundred-thousand-node exercise of movegen + make/unmake.
    _c(name='perft_selftest_48k', group='perft', kind='perft', timeout=600,
       what='built-in perft + incremental-state self-test (48K)'),
    _c(name='perft_selftest_hc128', group='perft', kind='perft', machine='hc128',
       timeout=600,
       what='the same self-test on the 128K build (banked transposition table)'),

    # -------------------------------------------------------------- movegen
    # Each case records genCount and the engine's own legal-move list, in
    # GENERATION ORDER, with each move's flag byte (0 normal, 1 double push,
    # 2 O-O, 3 O-O-O, and whatever the engine uses for e.p. and promotions).
    _c(name='mg_start_white', group='movegen', two_player=True, fen=START,
       moves=['a1a3'], what='legal moves for White at the start position'),
    _c(name='mg_start_black', group='movegen', two_player=True, fen=START_B,
       moves=['a8a6'], what='legal moves for Black at the start position'),
    _c(name='mg_kiwipete_white', group='movegen', two_player=True, fen=KIWI,
       moves=['a1a4'], what='Kiwipete, White: castling both sides, pins, captures'),
    _c(name='mg_kiwipete_black', group='movegen', two_player=True, fen=KIWI_B,
       moves=['a8a5'], what='Kiwipete, Black to move'),
    _c(name='mg_kiwipete_hc128', group='movegen', two_player=True, fen=KIWI,
       moves=['a1a4'], machine='hc128',
       what='Kiwipete, White, on the 128K build'),
    _c(name='mg_enpassant_pos', group='movegen', two_player=True, fen=EPPOS,
       moves=['e2e5'], what='the en-passant torture position, White'),
    _c(name='mg_ep_target_live', group='movegen', two_player=True,
       fen='rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3',
       moves=['a1a4'], what='an e.p. capture is generated when the target is set'),
    _c(name='mg_promotion_white', group='movegen', two_player=True, fen=PROMO,
       moves=['a7a5'], what='promotion position, White: promotions and captures'),
    _c(name='mg_promotion_black', group='movegen', two_player=True, fen=PROMO_B,
       moves=['f2f4'], what='promotion position, Black'),
    _c(name='mg_castling_free', group='movegen', two_player=True, fen=CASTLE,
       moves=['a1b2'], what='both castlings available on an empty board'),
    _c(name='mg_castling_blocked', group='movegen', two_player=True,
       fen='4k3/8/8/8/8/8/5r2/R3K2R w KQ - 0 1', moves=['a1b2'],
       what='O-O killed by a covered transit square, O-O-O still generated'),
    _c(name='mg_castling_norights', group='movegen', two_player=True,
       fen='4k3/8/8/8/8/8/8/R3K2R w - - 0 1', moves=['a1b2'],
       what='no castling generated when the rights bits are clear'),
    _c(name='mg_in_check_pin', group='movegen', two_player=True,
       fen='4k3/8/8/8/8/8/4B3/4K2r w - - 0 1', moves=['e1d1'],
       what='in check: only evasions and the blocking move survive'),
    _c(name='mg_krk_endgame', group='movegen', two_player=True,
       fen='8/8/8/4k3/8/8/8/R3K3 w Q - 0 1', moves=['a1b2'],
       what='K+R vs K: a sparse board'),
    _c(name='mg_illegal_refused', group='movegen', two_player=True, fen=START,
       moves=['e2e5'], what='an illegal move is refused and changes nothing'),

    # ------------------------------------------------------- move machinery
    _c(name='mv_italian_castles', group='moves', two_player=True,
       moves=['e2e4', 'e7e5', 'g1f3', 'b8c6', 'f1c4', 'f8c5', 'e1g1', 'e8g8'],
       what='8-ply Italian: both kings castle short, rights and king squares'),
    _c(name='mv_enpassant_capture', group='moves', two_player=True,
       moves=['e2e4', 'a7a6', 'e4e5', 'd7d5', 'e5d6'],
       what='an e.p. capture removes the pawn behind the target'),
    _c(name='mv_queenside_castle', group='moves', two_player=True, fen=CASTLE,
       moves=['e1c1'], what='O-O-O: king and rook both land, rights cleared'),
    _c(name='mv_kingside_castle', group='moves', two_player=True, fen=CASTLE,
       moves=['e1g1'], what='O-O: king and rook both land, rights cleared'),
    _c(name='mv_promote_q', group='moves', two_player=True,
       fen='4k3/P7/8/8/8/8/8/4K3 w - - 0 1', moves=['a7a8q'],
       what='promotion to queen'),
    _c(name='mv_promote_r', group='moves', two_player=True,
       fen='4k3/P7/8/8/8/8/8/4K3 w - - 0 1', moves=['a7a8r'],
       what='promotion to rook'),
    _c(name='mv_promote_b', group='moves', two_player=True,
       fen='4k3/P7/8/8/8/8/8/4K3 w - - 0 1', moves=['a7a8b'],
       what='promotion to bishop (and the terminal call that follows)'),
    _c(name='mv_promote_n', group='moves', two_player=True,
       fen='4k3/P7/8/8/8/8/8/4K3 w - - 0 1', moves=['a7a8n'],
       what='promotion to knight (and the terminal call that follows)'),
    _c(name='mv_promote_pending', group='moves', two_player=True,
       fen='4k3/P7/8/8/8/8/8/4K3 w - - 0 1', moves=['a7a8'],
       what='a promotion left un-chosen does not complete the move'),
    _c(name='mv_rights_lost', group='moves', two_player=True,
       fen='r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1', moves=['a1a2', 'h8h7'],
       what='moving a rook clears exactly that side of the castling rights'),
    _c(name='mv_halfmove_ticks', group='moves', two_player=True,
       fen='4k3/8/8/8/8/8/8/R3K3 w - - 10 30',
       moves=['a1a2', 'e8e7', 'a2a3', 'e7e8'],
       what='the fifty-move clock counts quiet moves; move number advances'),
    _c(name='mv_halfmove_pawn_reset', group='moves', two_player=True,
       fen='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 5 3',
       moves=['g1f3', 'b8c6', 'e2e4'],
       what='a pawn move resets the fifty-move clock'),
    _c(name='mv_halfmove_capture_reset', group='moves', two_player=True,
       fen='4k3/8/8/3q4/8/8/8/3QK3 w - - 20 40', moves=['d1d5'],
       what='a capture resets the clock and the material balance moves'),
    _c(name='mv_takeback', group='moves', two_player=True, fen=START,
       moves=['e2e4'], post=['z'],
       what='take-back (Z) restores the position, clock and move log'),
    _c(name='mv_takeback_castle', group='moves', two_player=True, fen=CASTLE,
       moves=['e1g1'], post=['z'],
       what='take-back of a castling move puts the rook back too'),

    _c(name='mv_long_game', group='moves', two_player=True, gap=400,
       moves=['e2e4', 'e7e5', 'g1f3', 'b8c6', 'f1b5', 'a7a6', 'b5a4', 'g8f6',
              'e1g1', 'f8e7', 'f1e1', 'b7b5', 'a4b3', 'd7d6', 'c2c3', 'e8g8',
              'h2h3', 'c6b8', 'd2d4', 'b8d7', 'c3c4', 'c7c6', 'c4b5', 'a6b5',
              'b1c3', 'c8b7', 'c1g5', 'b5b4', 'c3b1', 'h7h6'],
       what='a 30-ply Ruy Lopez: move log, undo stack and both castlings'),

    # ---------------------------------------------------- material readout
    # The engine's own 'Matl' panel figure, which it computes from its own
    # piece-value table.  One case per piece type, with the imbalance
    # multiplied up so that a change of a few centipawns in one entry moves
    # the displayed figure.  Without these the suite is blind to the value
    # table -- measured: a pawn 100 -> 120 mutant passed every other case.
    _c(name='ev_matl_pawns', group='material', two_player=True,
       fen='4k3/pppppppp/8/8/8/8/8/4K3 w - - 0 1', moves=['e1e3'],
       what='material readout with eight pawns of imbalance'),
    _c(name='ev_matl_knights', group='material', two_player=True,
       fen='1n1nkn1n/8/8/8/8/8/8/4K3 w - - 0 1', moves=['e1e3'],
       what='material readout with four knights of imbalance'),
    _c(name='ev_matl_bishops', group='material', two_player=True,
       fen='2b1kb2/8/1b6/8/8/1b6/8/4K3 w - - 0 1', moves=['e1e3'],
       what='material readout with four bishops of imbalance'),
    _c(name='ev_matl_rooks', group='material', two_player=True,
       fen='r2rkr2/8/8/8/8/8/8/4K3 w - - 0 1', moves=['e1e3'],
       what='material readout with three rooks of imbalance'),
    _c(name='ev_matl_queens', group='material', two_player=True,
       fen='3qkq2/8/8/8/8/8/8/4K3 w - - 0 1', moves=['e1e3'],
       what='material readout with two queens of imbalance'),

    # ------------------------------------------------------------- terminal
    _c(name='tm_fools_mate', group='terminal', two_player=True,
       moves=['f2f3', 'e7e5', 'g2g4', 'd8h4'],
       what="fool's mate: White is mated, gameState and message"),
    _c(name='tm_scholars_mate', group='terminal', two_player=True,
       moves=['e2e4', 'e7e5', 'f1c4', 'b8c6', 'd1h5', 'g8f6', 'h5f7'],
       what="scholar's mate: Black is mated"),
    _c(name='tm_stalemate', group='terminal', two_player=True,
       fen='7k/8/5QK1/8/8/8/8/8 w - - 0 1', moves=['f6f7'],
       what='stalemate is distinguished from mate'),
    _c(name='tm_insufficient', group='terminal', two_player=True,
       fen='7k/8/8/8/8/8/6B1/K6r w - - 0 1', moves=['g2h1'],
       what='K+B vs K is called a draw as soon as the rook is taken'),
    _c(name='tm_fifty_move', group='terminal', two_player=True,
       fen='4k3/8/8/8/8/8/8/R3K3 w - - 99 60', moves=['a1a2'],
       what='the fifty-move rule fires at the recorded boundary'),
    _c(name='tm_threefold', group='terminal', two_player=True,
       fen='4k1n1/8/8/8/8/8/8/4K1N1 w - - 0 1',
       moves=['g1f3', 'g8f6', 'f3g1', 'f6g8', 'g1f3', 'g8f6', 'f3g1', 'f6g8'],
       what='repetition draw after the knights shuffle back twice'),
    # Recorded, not assumed: the pristine build does NOT put a check
    # announcement on the status line.  It reads 'Your move' with the side to
    # move in check, and the game continues.  That is what is pinned.
    _c(name='tm_check_not_terminal', group='terminal', two_player=True,
       fen='4k3/8/8/8/8/8/8/R3K3 w - - 0 1', moves=['a1a8'],
       what='giving check leaves gameState in play and the status unchanged'),

    # --------------------------------------------------------------- search
    # The engine plays Black.  Depths kept low so the search finishes well
    # inside the engine's own time allocation (~1/32 of its remaining clock);
    # see the README on why deeper search is deliberately not pinned.
    _c(name='se_reply_d1', group='search', depth=1, moves=['e2e4'],
       what="engine reply to 1.e4 at depth 1"),
    _c(name='se_reply_d2', group='search', depth=2, moves=['e2e4'],
       what="engine reply to 1.e4 at depth 2"),
    _c(name='se_reply_d3', group='search', depth=3, moves=['e2e4'],
       what="engine reply to 1.e4 at depth 3"),
    _c(name='se_reply_d2_hc128', group='search', depth=2, moves=['e2e4'],
       machine='hc128', what="engine reply to 1.e4 at depth 2, 128K build"),
    _c(name='se_mate_in_one', group='search', depth=2,
       fen='7r/8/8/8/8/k7/8/K7 b - - 0 1',
       what='engine to move with a mate in one available'),
    _c(name='se_recapture', group='search', depth=2,
       fen='rnbqkbnr/ppp1pppp/8/8/3pP3/5N2/PPPP1PPP/RNBQKB1R b KQkq e3 0 3',
       what='engine to move in an open middlegame position'),
    _c(name='se_win_material', group='search', depth=2,
       fen='4k3/8/8/8/8/8/7q/4K2R b - - 0 1',
       what='engine to move with an undefended rook to take'),
    # The engine's search score is the only window onto its evaluation, and it
    # only says anything when the position is lopsided.  These two make it say
    # something about the pawn and the knight.
    _c(name='se_pawn_up', group='search', depth=2,
       fen='4k3/pppppppp/8/8/8/8/5PPP/4K3 b - - 0 1',
       what='engine to move five pawns up: the score reflects the pawn value'),
    _c(name='se_knight_up', group='search', depth=2,
       fen='1n1nk3/8/8/8/8/8/8/4K3 b - - 0 1',
       what='engine to move two knights up: the score reflects the knight value'),

    # ------------------------------------------------------------ save/load
    # The game's own G (save) captured off the tape port, byte for byte, and
    # then fed straight back into L (load).  This is the one part of the
    # engine that turns the whole game state into an external representation.
    _c(name='sv_roundtrip_rich', group='saveload', two_player=True, depth=4,
       fen='r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R b KQkq e3 7 12',
       post=['g'], expect_save=True,
       what='save/load round-trip of a position with rights, e.p. and clocks set'),
    _c(name='sv_roundtrip_played', group='saveload', two_player=True,
       moves=['e2e4', 'e7e5', 'g1f3'], post=['g'], expect_save=True,
       what='save/load round-trip after three played moves'),
    _c(name='sv_roundtrip_castled', group='saveload', two_player=True, fen=CASTLE,
       moves=['e1g1'], post=['g'], expect_save=True,
       what='save/load round-trip after castling (rights must be gone)'),
]

_names = [c['name'] for c in CASES]
assert len(_names) == len(set(_names)), 'duplicate case name'
