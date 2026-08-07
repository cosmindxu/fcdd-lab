#!/usr/bin/env python3
"""cases.py — the characterisation cases, as data.

Each case is a dict.  Nothing here executes; ``run.py`` interprets it.

Common keys
-----------
id        stable identifier; also the key into golden.json
group     coarse area, for the summary table
tier      1 = RULE, 2 = GOLDEN.  See README.md; the difference is what a
          failure means, not how hard the check is.
title     one line, what the case pins down
rule      (tier 1 only) the chess/UI rule that makes the expectation true
          INDEPENDENTLY of what this engine happens to do
kind      'state'    run the steps, observe the final state          (default)
          'screen'   run the built-in self-test, match screen text
          'saveload' step 0 saves with G, step 1 reloads it with L,
                     and the two states must agree
steps     list of kwargs for charlib.Emu.run
observe   the state fields compared
expect    (tier 1, kind 'state') literal expected values, written from the
          rules of chess — not copied from the engine
contains  (kind 'screen') substrings the screen must contain

Tier-1 expectations were written before the engine was run, and every
disagreement between a written expectation and the pristine build was
resolved by re-deriving the chess, not by editing the expectation to match.
Where the pristine build genuinely diverges from FIDE, the case is demoted
to tier 2 and the divergence is named in its 'note'.
"""

START = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

# The state fields most cases look at.  'moveLogN' is always included: it is
# how a dropped keystroke (a run whose timing was too tight) shows up as a
# loud failure instead of a wrong observation.
POS = ['fen', 'gameStateName', 'moveLogN']
POSC = ['fen', 'gameStateName', 'moveLogN', 'castling', 'ep', 'halfmove']


def state(cid, group, tier, title, steps, observe, expect=None, rule=None,
          note=None):
    c = dict(id=cid, group=group, tier=tier, title=title, kind='state',
             steps=steps, observe=observe)
    if expect is not None:
        c['expect'] = expect
    if rule:
        c['rule'] = rule
    if note:
        c['note'] = note
    return c


CASES = []

# ==========================================================================
# 1. The engine's own perft self-test  (T)
# ==========================================================================
# The strongest single movegen check available: the engine walks its own move
# generator over five positions and compares against counts that are
# mathematical facts about chess, not about this program.

CASES.append(dict(
    id='perft/selftest', group='perft', tier=1, kind='screen',
    title='built-in perft + incremental-state self-test passes',
    rule='perft(startpos) = 20/400/8902/197281 at depths 1-4; Kiwipete d3 = '
         '97862; the standard en-passant position d4 = 43238; the standard '
         'promotion position d3 = 62379. These are published, verifiable '
         'counts, independent of any implementation.',
    steps=[dict(perft=True)],
    contains=['perft 1  20', 'perft 2  400', 'perft 3  8902',
              'perft 4  197281', 'kiwipete d3  97862', 'enpassant d4 43238',
              'promotion d3 62379', 'incr key/phase/pst', 'OK - movegen verified'],
))

# ==========================================================================
# 2. Position loading  (L)  — the state round-trips through the save block
# ==========================================================================
# Every other case depends on this one: if the loader does not install the
# position it was given, nothing below means anything.

_LOAD_FENS = [
    ('start', START),
    ('rights_all', 'r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1'),
    ('rights_partial', 'r3k2r/8/8/8/8/8/8/R3K2R b Kq - 13 40'),
    ('rights_none', 'r3k2r/8/8/8/8/8/8/R3K2R w - - 99 100'),
    ('ep_white', 'rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3'),
    ('ep_black', 'rnbqkbnr/pppp1ppp/8/8/3pP3/8/PPP1PPPP/RNBQKBNR b KQkq e3 0 3'),
    ('endgame', '8/8/8/4k3/8/8/4K3/7R w - - 45 88'),
    ('promo_ready', '8/P6k/8/8/8/8/7K/8 w - - 0 60'),
    ('bare_kings', 'k7/8/8/8/8/8/8/K7 w - - 0 1'),
    ('middlegame', 'r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 6 5'),
    ('movenum_hi', '4k3/8/8/8/8/8/8/4K3 w - - 0 300'),
]
for _name, _fen in _LOAD_FENS:
    CASES.append(state(
        'load/' + _name, 'load', 1,
        'loading "%s" installs exactly that position' % _fen,
        [dict(fen=_fen, two_player=True)],
        ['fen', 'moveLogN'],
        expect={'fen': _fen, 'moveLogN': 0},
        rule='A load must be the identity on the state it was handed: board, '
             'side to move, castling rights, en-passant target, halfmove clock '
             'and move number all come back unchanged.'))

# ==========================================================================
# 3. Move generation and legality  (two-player: the human drives both sides)
# ==========================================================================

_CASTLE = 'r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R %s KQkq - 7 12'

CASES += [
    state('move/castle_white_king', 'movegen', 1,
          'white O-O moves king e1->g1 and rook h1->f1, clearing white rights',
          [dict(fen=_CASTLE % 'w', two_player=True, moves=['e1g1'])], POSC,
          expect={'fen': 'r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R4RK1 b kq - 8 12',
                  'gameStateName': 'play', 'moveLogN': 1,
                  'castling': 12, 'ep': 255, 'halfmove': 8},
          rule='Castling kingside is a single king move of two squares with '
               'the h-rook jumping to f1; both of that side\'s rights are lost.'),

    state('move/castle_white_queen', 'movegen', 1,
          'white O-O-O moves king e1->c1 and rook a1->d1',
          [dict(fen=_CASTLE % 'w', two_player=True, moves=['e1c1'])], POSC,
          expect={'fen': 'r3k2r/pppppppp/8/8/8/8/PPPPPPPP/2KR3R b kq - 8 12',
                  'gameStateName': 'play', 'moveLogN': 1,
                  'castling': 12, 'ep': 255, 'halfmove': 8},
          rule='Castling queenside puts the king on c1 and the a-rook on d1.'),

    state('move/castle_black_king', 'movegen', 1,
          'black O-O moves king e8->g8 and rook h8->f8',
          [dict(fen=_CASTLE % 'b', two_player=True, moves=['e8g8'])], POSC,
          expect={'fen': 'r4rk1/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQ - 8 13',
                  'gameStateName': 'play', 'moveLogN': 1,
                  'castling': 3, 'ep': 255, 'halfmove': 8},
          rule='The same rule for Black, and the move number advances after '
               'Black has moved.'),

    state('move/castle_black_queen', 'movegen', 1,
          'black O-O-O moves king e8->c8 and rook a8->d8',
          [dict(fen=_CASTLE % 'b', two_player=True, moves=['e8c8'])], POSC,
          expect={'fen': '2kr3r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQ - 8 13',
                  'gameStateName': 'play', 'moveLogN': 1,
                  'castling': 3, 'ep': 255, 'halfmove': 8},
          rule='Castling queenside for Black: king c8, rook d8.'),

    state('move/castle_blocked_kingside', 'movegen', 1,
          'O-O refused when a square between king and rook is occupied',
          [dict(fen='r3k2r/8/8/8/8/8/8/R2QK1NR w KQkq - 4 9', two_player=True,
                moves=['e1g1'])], POS,
          expect={'fen': 'r3k2r/8/8/8/8/8/8/R2QK1NR w KQkq - 4 9',
                  'gameStateName': 'play', 'moveLogN': 0},
          rule='Castling requires every square between king and rook to be '
               'empty; a knight on g1 forbids O-O.'),

    state('move/castle_blocked_queenside', 'movegen', 1,
          'O-O-O refused when d1 is occupied',
          [dict(fen='r3k2r/8/8/8/8/8/8/R2QK1NR w KQkq - 4 9', two_player=True,
                moves=['e1c1'])], POS,
          expect={'fen': 'r3k2r/8/8/8/8/8/8/R2QK1NR w KQkq - 4 9',
                  'gameStateName': 'play', 'moveLogN': 0},
          rule='A queen on d1 forbids O-O-O.'),

    state('move/castle_through_check', 'movegen', 1,
          'O-O refused when the transit square f1 is attacked',
          [dict(fen='4kr2/8/8/8/8/8/8/R3K2R w KQ - 4 9', two_player=True,
                moves=['e1g1'])], POS,
          expect={'fen': '4kr2/8/8/8/8/8/8/R3K2R w KQ - 4 9',
                  'gameStateName': 'play', 'moveLogN': 0},
          rule='The king may not pass through an attacked square; a rook on '
               'f8 covers f1 and forbids O-O.'),

    state('move/castle_other_side_still_legal', 'movegen', 1,
          'the same position still allows O-O-O (d1 and c1 are not attacked)',
          [dict(fen='4kr2/8/8/8/8/8/8/R3K2R w KQ - 4 9', two_player=True,
                moves=['e1c1'])], POSC,
          expect={'fen': '4kr2/8/8/8/8/8/8/2KR3R b - - 5 9',
                  'gameStateName': 'play', 'moveLogN': 1,
                  'castling': 0, 'ep': 255, 'halfmove': 5},
          rule='Only the side whose transit square is attacked is forbidden; '
               'the b1 square need not be safe, only empty.'),

    state('move/castle_out_of_check', 'movegen', 1,
          'castling refused while the king is in check',
          [dict(fen='4k3/4r3/8/8/8/8/8/R3K2R w KQ - 4 9', two_player=True,
                moves=['e1g1'])], POS,
          expect={'fen': '4k3/4r3/8/8/8/8/8/R3K2R w KQ - 4 9',
                  'gameStateName': 'play', 'moveLogN': 0},
          rule='A king in check may not castle.'),

    state('move/castle_no_rights', 'movegen', 1,
          'castling refused when the rights bit is gone',
          [dict(fen='r3k2r/8/8/8/8/8/8/R3K2R w - - 4 9', two_player=True,
                moves=['e1g1'])], POS,
          expect={'fen': 'r3k2r/8/8/8/8/8/8/R3K2R w - - 4 9',
                  'gameStateName': 'play', 'moveLogN': 0},
          rule='Castling rights, once lost, are never regained.'),

    state('move/rights_lost_rook', 'movegen', 1,
          'moving the h1 rook clears only the white kingside right',
          [dict(fen='r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 4 9', two_player=True,
                moves=['h1h2'])], POSC,
          expect={'fen': 'r3k2r/8/8/8/8/8/7R/R3K3 b Qkq - 5 9',
                  'gameStateName': 'play', 'moveLogN': 1,
                  'castling': 14, 'ep': 255, 'halfmove': 5},
          rule='A rook move forfeits the castling right on that rook\'s side '
               'only.'),

    state('move/rights_lost_king', 'movegen', 1,
          'moving the king clears both of that side\'s rights',
          [dict(fen='r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 4 9', two_player=True,
                moves=['e1e2'])], POSC,
          expect={'fen': 'r3k2r/8/8/8/8/8/4K3/R6R b kq - 5 9',
                  'gameStateName': 'play', 'moveLogN': 1,
                  'castling': 12, 'ep': 255, 'halfmove': 5},
          rule='A king move forfeits both of its side\'s castling rights.'),

    state('move/double_push_sets_ep', 'movegen', 1,
          'a double pawn push sets the en-passant target on the skipped square',
          [dict(fen=START, two_player=True, moves=['d2d4'])], POSC,
          expect={'fen': 'rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1',
                  'gameStateName': 'play', 'moveLogN': 1,
                  'castling': 15, 'ep': 0x23, 'halfmove': 0},
          rule='The en-passant target is the square the pawn skipped over.'),

    state('move/ep_capture', 'movegen', 1,
          'en passant captures the pawn beside the target square',
          [dict(fen='rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3',
                two_player=True, moves=['e5d6'])], POSC,
          expect={'fen': 'rnbqkbnr/ppp1pppp/3P4/8/8/8/PPPP1PPP/RNBQKBNR b KQkq - 0 3',
                  'gameStateName': 'play', 'moveLogN': 1,
                  'castling': 15, 'ep': 255, 'halfmove': 0},
          rule='The capturing pawn lands on the target square and the captured '
               'pawn, which is NOT on that square, is removed.'),

    state('move/ep_expires', 'movegen', 1,
          'the en-passant right is gone one ply later',
          [dict(fen='rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3',
                two_player=True, moves=['g1f3', 'b8c6', 'e5d6'])], POS,
          expect={'fen': 'r1bqkbnr/ppp1pppp/2n5/3pP3/8/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 4',
                  'gameStateName': 'play', 'moveLogN': 2},
          rule='En passant must be taken immediately; after any other move the '
               'target is cleared and e5d6 is not a legal move.'),

    state('move/pin_along_line_ok', 'movegen', 1,
          'a pinned bishop may still move along the pinning line',
          [dict(fen='4k3/8/8/q7/8/8/3B4/4K3 w - - 5 30', two_player=True,
                moves=['d2c3'])], POS,
          expect={'fen': '4k3/8/8/q7/8/2B5/8/4K3 b - - 6 30',
                  'gameStateName': 'play', 'moveLogN': 1},
          rule='A pin restricts a piece to the line between king and pinner; '
               'c3 is on the a5-e1 diagonal.'),

    state('move/pin_off_line_refused', 'movegen', 1,
          'a pinned bishop may not leave the pinning line',
          [dict(fen='4k3/8/8/q7/8/8/3B4/4K3 w - - 5 30', two_player=True,
                moves=['d2e3'])], POS,
          expect={'fen': '4k3/8/8/q7/8/8/3B4/4K3 w - - 5 30',
                  'gameStateName': 'play', 'moveLogN': 0},
          rule='No move may leave one\'s own king attacked; d2e3 would open '
               'the a5-e1 diagonal onto the white king.'),

    state('move/king_into_check_refused', 'movegen', 1,
          'the king may not step onto an attacked square',
          [dict(fen='4k3/8/8/8/8/8/7r/4K3 w - - 5 30', two_player=True,
                moves=['e1e2'])], POS,
          expect={'fen': '4k3/8/8/8/8/8/7r/4K3 w - - 5 30',
                  'gameStateName': 'play', 'moveLogN': 0},
          rule='A rook on h2 covers the whole second rank.'),

    state('move/must_escape_check', 'movegen', 1,
          'a move that does not answer the check is refused',
          [dict(fen='4k3/4r3/8/8/8/8/8/R3K2R w KQ - 4 9', two_player=True,
                moves=['a1a2'])], POS,
          expect={'fen': '4k3/4r3/8/8/8/8/8/R3K2R w KQ - 4 9',
                  'gameStateName': 'play', 'moveLogN': 0},
          rule='While in check, only a move that ends the check is legal; '
               'Ra1-a2 neither blocks the e-file nor moves the king.'),

    state('move/escape_check_ok', 'movegen', 1,
          'stepping off the checked file is accepted',
          [dict(fen='4k3/4r3/8/8/8/8/8/R3K2R w KQ - 4 9', two_player=True,
                moves=['e1f1'])], POSC,
          expect={'fen': '4k3/4r3/8/8/8/8/8/R4K1R b - - 5 9',
                  'gameStateName': 'play', 'moveLogN': 1,
                  'castling': 0, 'ep': 255, 'halfmove': 5},
          rule='The king may leave the attacked line, and doing so forfeits '
               'both castling rights.'),

    state('move/king_sideways_ok', 'movegen', 1,
          'the same king may step along the safe first rank',
          [dict(fen='4k3/8/8/8/8/8/7r/4K3 w - - 5 30', two_player=True,
                moves=['e1d1'])], POS,
          expect={'fen': '4k3/8/8/8/8/8/7r/3K4 b - - 6 30',
                  'gameStateName': 'play', 'moveLogN': 1},
          rule='The first rank is not attacked, so d1 is legal.'),
]

# -- promotion -------------------------------------------------------------

# After the promotion only K+X vs K is left, so the terminal verdict differs
# by piece: a lone bishop or knight cannot mate, and the position is dead.
_PROMO_BOARD = {'q': ('Q7', 'play'), 'r': ('R7', 'play'),
                'b': ('B7', 'draw'), 'n': ('N7', 'draw')}
for _p, (_row, _stname) in _PROMO_BOARD.items():
    CASES.append(state(
        'move/promote_white_' + _p, 'movegen', 1,
        'white pawn promotes to %s (leaving K+%s vs K, %s)'
        % (_p.upper(), _p.upper(), _stname),
        [dict(fen='8/P6k/8/8/8/8/7K/8 w - - 0 60', two_player=True,
              moves=['a7a8' + _p])], POS,
        expect={'fen': '%s/7k/8/8/8/8/7K/8 b - - 0 60' % _row,
                'gameStateName': _stname, 'moveLogN': 1},
        rule='A pawn reaching the last rank becomes the chosen piece of its '
             'own colour. Here that leaves K+%s vs K, which is %s: a lone '
             'bishop or knight cannot force mate, a queen or rook can.'
             % (_p.upper(), 'a dead position' if _stname == 'draw'
                else 'still a game')))

CASES += [
    state('move/promote_black_queen', 'movegen', 1,
          'black pawn promotes to a BLACK queen',
          [dict(fen='8/7K/8/8/8/8/p6k/8 b - - 0 60', two_player=True,
                moves=['a2a1q'])], POS,
          expect={'fen': '8/7K/8/8/8/8/7k/q7 w - - 0 61',
                  'gameStateName': 'play', 'moveLogN': 1},
          rule='Promotion keeps the mover\'s colour.'),

    state('move/promote_with_capture', 'movegen', 1,
          'a pawn may promote by capturing onto the last rank',
          [dict(fen='1r5k/P7/8/8/8/8/7K/8 w - - 0 60', two_player=True,
                moves=['a7b8q'])], POS,
          expect={'fen': '1Q5k/8/8/8/8/8/7K/8 b - - 0 60',
                  'gameStateName': 'play', 'moveLogN': 1},
          rule='Capture and promotion happen in the same move.'),
]

# -- the fifty-move clock --------------------------------------------------

CASES += [
    state('clock/reset_on_pawn_move', 'clock', 1,
          'the halfmove clock resets on a pawn move',
          [dict(fen='4k3/pppppppp/8/8/8/8/PPPPPPPP/4K3 w - - 37 60',
                two_player=True, moves=['a2a3'])], POSC,
          expect={'fen': '4k3/pppppppp/8/8/8/P7/1PPPPPPP/4K3 b - - 0 60',
                  'gameStateName': 'play', 'moveLogN': 1,
                  'castling': 0, 'ep': 255, 'halfmove': 0},
          rule='The fifty-move counter restarts after every pawn move.'),

    # The spare black pawn keeps these positions out of "insufficient
    # material", so that what is under test is the clock and nothing else.
    state('clock/reset_on_capture', 'clock', 1,
          'the halfmove clock resets on a capture',
          [dict(fen='4k3/7p/8/2p5/4N3/8/8/4K3 w - - 37 60', two_player=True,
                moves=['e4c5'])], POSC,
          expect={'fen': '4k3/7p/8/2N5/8/8/8/4K3 b - - 0 60',
                  'gameStateName': 'play', 'moveLogN': 1,
                  'castling': 0, 'ep': 255, 'halfmove': 0},
          rule='The fifty-move counter restarts after every capture.'),

    state('clock/increment_on_quiet', 'clock', 1,
          'the halfmove clock increments on a quiet move',
          [dict(fen='4k3/7p/8/8/8/8/4N3/4K3 w - - 37 60', two_player=True,
                moves=['e2g3'])], POSC,
          expect={'fen': '4k3/7p/8/8/8/6N1/8/4K3 b - - 38 60',
                  'gameStateName': 'play', 'moveLogN': 1,
                  'castling': 0, 'ep': 255, 'halfmove': 38},
          rule='Any other move advances the counter by one ply.'),
]

# ==========================================================================
# 4. Game-terminal detection
# ==========================================================================
# gameState codes (from the harness's own decoder):
#   0 play  1 white-mated  2 black-mated  3 stalemate  4 draw  5 flag-fall

CASES += [
    state('term/fools_mate', 'terminal', 1,
          'fool\'s mate is reported as White being mated',
          [dict(fen=None, two_player=True,
                moves=['f2f3', 'e7e5', 'g2g4', 'd8h4'])], POS,
          expect={'fen': 'rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3',
                  'gameStateName': 'white-mated', 'moveLogN': 4},
          rule='1.f3 e5 2.g4 Qh4# is checkmate: the white king is attacked '
               'and has no legal reply.'),

    state('term/back_rank_mate', 'terminal', 1,
          'a back-rank mate is reported as Black being mated',
          [dict(fen='6k1/5ppp/8/8/8/8/8/R5K1 w - - 4 30', two_player=True,
                moves=['a1a8'])], POS,
          expect={'fen': 'R5k1/5ppp/8/8/8/8/8/6K1 b - - 5 30',
                  'gameStateName': 'black-mated', 'moveLogN': 1},
          rule='Ra8+ is mate: f8 and h8 are on the attacked rank and f7/g7/h7 '
               'are blocked by Black\'s own pawns.'),

    state('term/stalemate', 'terminal', 1,
          'a stalemate is reported as a stalemate, not a mate or a draw',
          [dict(fen='7k/8/5Q2/8/8/8/8/7K w - - 4 60', two_player=True,
                moves=['f6f7'])], POS,
          expect={'fen': '7k/5Q2/8/8/8/8/8/7K b - - 5 60',
                  'gameStateName': 'stalemate', 'moveLogN': 1},
          rule='After Qf7 the black king is NOT attacked but has no legal '
               'move: g8, g7 and h7 are all covered by the queen.'),

    state('term/insufficient_kk', 'terminal', 1,
          'king vs king is a dead position',
          [dict(fen='7k/8/8/8/8/8/1n6/K7 w - - 4 60', two_player=True,
                moves=['a1b2'])], POS,
          expect={'fen': '7k/8/8/8/8/8/1K6/8 b - - 0 60',
                  'gameStateName': 'draw', 'moveLogN': 1},
          rule='With only the two kings left, no sequence of legal moves can '
               'produce mate.'),

    state('term/insufficient_kb_k', 'terminal', 1,
          'K+B vs K is a dead position',
          [dict(fen='7k/8/8/8/8/8/1n6/KB6 w - - 4 60', two_player=True,
                moves=['a1b2'])], POS,
          expect={'fen': '7k/8/8/8/8/8/1K6/1B6 b - - 0 60',
                  'gameStateName': 'draw', 'moveLogN': 1},
          rule='A lone bishop cannot force mate, so K+B vs K is dead.'),

    state('term/fifty_move_not_yet', 'terminal', 1,
          'the game continues at 98 halfmoves',
          [dict(fen='4k3/8/8/8/8/8/R7/4K3 w - - 97 60', two_player=True,
                moves=['a2a3'])], POSC,
          expect={'fen': '4k3/8/8/8/8/R7/8/4K3 b - - 98 60',
                  'gameStateName': 'play', 'moveLogN': 1,
                  'castling': 0, 'ep': 255, 'halfmove': 98},
          rule='The fifty-move rule needs 100 halfmoves; 98 is not enough.'),
]

# Recorded, not asserted: the exact halfmove boundary, whether K+B vs K is
# called dead, and whether a threefold repetition is detected are all places
# where a program may legitimately differ from FIDE.  The pristine answer is
# what a repair must preserve, so it is a GOLDEN.
CASES += [
    state('term/fifty_move_boundary', 'terminal', 2,
          'what the engine does when the halfmove clock reaches 100',
          [dict(fen='4k3/8/8/8/8/8/R7/4K3 w - - 99 60', two_player=True,
                moves=['a2a3'])], POSC,
          note='FIDE makes the fifty-move draw CLAIMABLE at 100 halfmoves '
               'rather than automatic, and programs differ on >= 100 vs > 100. '
               'Recorded rather than asserted.'),

    state('term/threefold', 'terminal', 2,
          'what the engine does after a position occurs three times',
          [dict(fen=None, two_player=True,
                moves=['g1f3', 'g8f6', 'f3g1', 'f6g8',
                       'g1f3', 'g8f6', 'f3g1', 'f6g8'])], POS,
          note='Repetition detection is a design choice (claim vs automatic, '
               'and whether castling/e.p. rights are part of the key). '
               'Recorded.'),
]

# ==========================================================================
# 5. Interface state: take-back, new game, level
# ==========================================================================

CASES += [
    state('ui/takeback_two_player', 'ui', 1,
          'Z undoes the last move in two-player mode',
          [dict(fen=None, two_player=True, moves=['e2e4'], post='z')],
          ['fen', 'gameStateName', 'castling', 'ep', 'halfmove'],
          expect={'fen': START, 'gameStateName': 'play',
                  'castling': 15, 'ep': 255, 'halfmove': 0},
          rule='A take-back must restore the position exactly, including the '
               'en-passant target that the double push had set.'),

    # Observed on pristine and left as a golden rather than a rule: the take-back
    # restores the POSITION but does not shorten the displayed move log, so
    # after 1.e4 Z the board is the initial array while the log still reads
    # "e2e4".  Whether that is a defect is a judgement the suite does not make;
    # it is recorded so that a change to it is visible.
    state('ui/takeback_movelog', 'ui', 2,
          'what Z leaves in the move log',
          [dict(fen=None, two_player=True, moves=['e2e4'], post='z')],
          ['moveLogN', 'moveLog'],
          note='On the baseline the log is NOT truncated by a take-back.'),

    state('ui/newgame', 'ui', 1,
          'N restores the initial position',
          [dict(fen=None, two_player=True, moves=['e2e4', 'e7e5'], post='n')],
          POSC,
          expect={'fen': START, 'gameStateName': 'play', 'moveLogN': 0,
                  'castling': 15, 'ep': 255, 'halfmove': 0},
          rule='A new game is the standard array with all rights and clocks '
               'reset.'),

    state('ui/takeback_vs_engine', 'ui', 2,
          'what Z does after the engine has replied',
          [dict(fen=None, depth=2, moves=['e2e4'], post='z')], POSC,
          note='Whether a take-back removes one ply or the whole move pair is '
               'a UI design choice. Recorded.'),

    state('ui/endgame_demo', 'ui', 2,
          'the position the E key loads (K+R vs K demo)',
          [dict(fen=None, two_player=True, pre='e')], POSC,
          note='A fixed demo position; recorded so that a change to it shows up.'),
]

for _d in (1, 3, 4, 5):
    CASES.append(state(
        'ui/level_%d' % _d, 'ui', 1,
        'the %d key sets the search level to %d' % (_d, _d),
        [dict(fen=None, depth=_d, two_player=True)], ['aiDepth'],
        expect={'aiDepth': _d},
        rule='The documented strength keys 1..5 select the search depth.'))

# ==========================================================================
# 6. Save / load round-trip through the engine's own G and L
# ==========================================================================
# Not a golden: this is a self-checking invariant.  Whatever the state is
# after the moves, reloading the engine's own saved block must reproduce it.

_SL = ['fen', 'gameStateName', 'castling', 'ep', 'halfmove']
CASES += [
    dict(id='save/after_castling', group='save', tier=1, kind='saveload',
         title='G then L round-trips a position after castling',
         rule='Saving and reloading is the identity on the saved state.',
         steps=[dict(fen='r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 7 12',
                     two_player=True, moves=['e1g1'], post='g'),
                dict(two_player=True)],
         observe=_SL),

    dict(id='save/after_double_push', group='save', tier=1, kind='saveload',
         title='G then L preserves the en-passant target',
         rule='The en-passant target is part of the position and must survive '
              'a save/load.',
         steps=[dict(fen=None, two_player=True, moves=['d2d4'], post='g'),
                dict(two_player=True)],
         observe=_SL),

    dict(id='save/high_halfmove', group='save', tier=1, kind='saveload',
         title='G then L preserves a high fifty-move clock',
         rule='The halfmove clock is part of the position.',
         steps=[dict(fen='4k3/8/8/8/8/8/R7/4K3 w - - 97 60', two_player=True,
                     moves=['a2a3'], post='g'),
                dict(two_player=True)],
         observe=_SL),
]

# ==========================================================================
# 7. Search / evaluation goldens  (tier 2)
# ==========================================================================
# The engine plays Black, so a position loaded with Black to move makes it
# search immediately.  What is recorded is the move it chose, the score it
# printed and the position that resulted.
#
# NOTHING here is a rule.  A different move at the same depth is a BEHAVIOUR
# CHANGE, and after a deliberate change to search or evaluation it is the
# expected outcome, not a defect.  See README.md.

SEARCH_POSITIONS = [
    ('open_e4', 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1',
     'the reply to 1.e4'),
    ('italian', 'r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 4 4',
     'a quiet developed opening position'),
    ('sicilian', 'rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2',
     'an asymmetric opening'),
    ('kiwipete', 'r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R b KQkq - 0 1',
     'the standard wide-branching test position'),
    ('in_check', 'rnbqkbnr/ppp2ppp/8/1B1pp3/4P3/8/PPPP1PPP/RNBQK1NR b KQkq - 1 3',
     'black must answer a check'),
    ('must_recapture', 'r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R b KQkq - 6 5',
     'a position with live captures (exercises quiescence)'),
    ('krk_black_up', '4k3/8/8/8/8/8/r7/4K3 b - - 0 1', 'black is a rook up'),
    ('krk_white_up', '4k3/8/8/8/8/8/R7/4K3 b - - 0 1', 'white is a rook up'),
    ('kqk', '4k3/8/8/8/8/8/Q7/4K3 b - - 0 1', 'black is facing a queen'),
    ('pawn_endgame', '4k3/pp6/8/8/8/8/PP6/4K3 b - - 0 1', 'a symmetric pawn endgame'),
    ('promotion_race', '8/P5k1/8/8/8/8/6p1/6K1 b - - 0 50', 'both sides are promoting'),
    ('opposition', '8/8/8/4k3/8/4K3/4P3/8 b - - 0 60', 'a king-and-pawn opposition'),
    ('rook_endgame', '8/8/8/8/8/4k3/4r3/4K2R b - - 0 60', 'a rook endgame'),
    ('bishop_pair', '4k3/8/8/8/8/8/8/2B1KB2 b - - 0 60', 'black faces two bishops'),
    ('knight_fork', '4k3/8/8/3n4/8/8/4K3/3Q4 b - - 0 60',
     'black has a knight fork available'),
    ('middlegame', 'r2q1rk1/pp1bbppp/2n1pn2/2pp4/3P1B2/2PBPN2/PP1N1PPP/R2Q1RK1 b - - 0 10',
     'a closed middlegame'),
    ('mate_defence', 'R5k1/5ppp/8/8/8/8/8/6K1 b - - 0 30',
     'black must answer a back-rank check'),
]

SEARCH_OBSERVE = ['lastMove', 'lastScore', 'fen', 'gameStateName', 'moveLogN']

for _name, _fen, _why in SEARCH_POSITIONS:
    for _d in (1, 2, 3):
        CASES.append(state(
            'search/%s_d%d' % (_name, _d), 'search', 2,
            'engine reply at depth %d: %s' % (_d, _why),
            [dict(fen=_fen, depth=_d, tail=6000)], SEARCH_OBSERVE,
            note='Recorded pristine behaviour of the search and the '
                 'evaluation it drives. Not a rule.'))

# A couple of deeper searches, and the 128K build, which uses banked RAM for
# the transposition table and is therefore a different code path.
for _name, _fen, _why in SEARCH_POSITIONS[:4]:
    CASES.append(state(
        'search/%s_d4' % _name, 'search', 2,
        'engine reply at depth 4: %s' % _why,
        [dict(fen=_fen, depth=4, tail=12000)], SEARCH_OBSERVE,
        note='Deeper search; more sensitive to move ordering and to the '
             'transposition table.'))

for _name, _fen, _why in SEARCH_POSITIONS[:3]:
    CASES.append(state(
        'search/%s_d3_hc128' % _name, 'search128', 2,
        '128K build, engine reply at depth 3: %s' % _why,
        [dict(fen=_fen, depth=3, tail=6000, machine='hc128')], SEARCH_OBSERVE,
        note='The hc128 build puts the transposition table in a spare RAM '
             'bank, so this is a different code path from the 48K runs.'))

# A rule that does hold of the search, whatever it plays: the move it makes
# must be legal, and it must actually make one.
for _name, _fen, _why in SEARCH_POSITIONS[:6]:
    CASES.append(state(
        'search/%s_moves' % _name, 'search', 1,
        'the engine answers with exactly one move: %s' % _why,
        [dict(fen=_fen, depth=2, tail=6000)], ['moveLogN'],
        expect={'moveLogN': 1},
        rule='Given a position with legal moves, the engine must return one '
             'move (not zero, not several).'))


# ==========================================================================
# 8. Whole scripted games  (tier 2)
# ==========================================================================
# The cases above each exercise one mechanism from a set-up position.  These
# play a real game from the opening instead: the human follows a fixed line
# and the engine answers every move, so make/unmake, the transposition table,
# the incremental Zobrist/phase/evaluation accumulators and the clock are all
# carried across many plies rather than reset for each observation.

# Deliberately SHORT.  Each side has a five-minute clock (15,000 frames) and
# the emulator has to be given enough frames per move for the engine to think
# but not so many that the clock runs out, so long scripted games are not
# reproducible in this harness at all -- eight-move lines were tried and lost
# moves at every frame budget.  These lines were each run twice at GAME_GAP
# and reproduced exactly.
GAME_GAP = 1500
GAMES = [
    ('italian_d2', 2, ['e2e4', 'g1f3', 'f1c4', 'd2d3']),
    ('queens_pawn_d3', 3, ['d2d4', 'c2c4', 'b1c3', 'g1f3']),
    ('open_captures_d1', 1, ['e2e4', 'd2d4', 'g1f3', 'b1c3', 'f1e2']),
]
for _name, _d, _mv in GAMES:
    CASES.append(state(
        'game/' + _name, 'game', 2,
        'a %d-ply game at depth %d, engine answering every move' % (2 * len(_mv), _d),
        [dict(fen=None, depth=_d, moves=_mv, tail=2500, gap=GAME_GAP)],
        ['fen', 'gameStateName', 'moveLogN', 'moveLog', 'halfmove', 'castling'],
        note='The most sensitive golden in the suite and the most brittle: '
             'one different engine choice early changes every ply after it.'))
    CASES.append(state(
        'game/%s_answers' % _name, 'game', 1,
        'the engine answers each of the %d scripted moves' % len(_mv),
        [dict(fen=None, depth=_d, moves=_mv, tail=2500, gap=GAME_GAP)],
        ['moveLogN'],
        expect={'moveLogN': 2 * len(_mv)},
        rule='Every legal human move must be accepted and answered, so the '
             'log holds one engine ply per human ply.'))


def by_id():
    return {c['id']: c for c in CASES}


def groups():
    out = {}
    for c in CASES:
        out.setdefault(c['group'], []).append(c)
    return out


if __name__ == '__main__':
    import collections
    n = collections.Counter((c['group'], c['tier']) for c in CASES)
    print('%d cases' % len(CASES))
    for (g, t), k in sorted(n.items()):
        print('  %-10s tier %d  %3d' % (g, t, k))
