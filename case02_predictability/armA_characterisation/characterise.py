#!/usr/bin/env python3
"""characterise.py - characterisation-test suite for the HC-91 ZX-CHESS engine.

WHAT THIS IS
------------
A behavioural pin.  Every expected value in `expected.json` was RECORDED from
the pristine build by running it; nothing here encodes an opinion about what
chess rules say.  A green run therefore means "this build still behaves, at the
recorded observation points, exactly as the pristine build behaved".  It does
NOT mean "this build is correct".

HOW IT OBSERVES
---------------
The engine is a ZX Spectrum tape.  Its entire observable surface, from outside,
is three channels:

  1. keystrokes in            (--type / --keys)
  2. the 24x32 screen out     (--text OCR; piece glyphs render as '?')
  3. a 48K memory image out   (--save-sna, decoded with the harness's
                               tools/chesspos.py)
  plus  4. whatever the game itself SAVEs to tape (--save-tape), which is the
           game's own 71-byte position block.

Every assertion in this suite is built from those four.

USAGE
-----
  ./characterise.py --tap PATH/TO/chess.tap                 # run the suite
  ./characterise.py --tap ... --filter movegen              # subset
  ./characterise.py --tap ... --verbose
  ./characterise.py --tap ... --record OUT.json             # re-record (see README)
  ./characterise.py --tap ... --record OUT.json --profile B # alternate schedule

Exit status: 0 = all cases matched, 1 = at least one mismatch, 2 = harness error.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True   # never leave a __pycache__ in case01's harness

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(os.path.dirname(HERE))
DEFAULT_HARNESS = os.path.join(LAB, 'case01_spectrum_gambit', 'arms', 'harness')

sys.path.insert(0, HERE)
from cases import CASES                                     # noqa: E402


# --------------------------------------------------------------------------
# scheduling profiles
#
# Profile A is the ordinary one.  Profile B shifts EVERY frame number: the tape
# load lands later, the keys arrive later, each move gets more room.  Nothing
# about the chess changes.  A field that disagrees between A and B is
# timing-sensitive and is dropped from expected.json automatically -- that is
# how the clocks, the frame-seeded Zobrist key and anything else volatile get
# excluded, by measurement rather than by assumption.
# --------------------------------------------------------------------------

PROFILES = {
    'A': dict(load_frame=700, wait=120, gap=900, tail=900, perft_frames=95000),
    'B': dict(load_frame=780, wait=200, gap=1050, tail=1150, perft_frames=99000),
    # C gives the engine roughly three times as long per move.  It exists to
    # test one specific hazard: the engine allocates itself ~1/32 of its
    # remaining clock per move, so a search that was being cut short would
    # answer differently when given more room.  If C agrees with A, the
    # recorded search results are converged, not truncated.
    'C': dict(load_frame=700, wait=300, gap=3000, tail=2000, perft_frames=95000),
}

# Fields never written to the baseline, whatever the two passes say.
#
# hashKey is the engine's 16-bit Zobrist key.  Its tables are filled at boot
# from a PRNG, so the key is a property of one build's boot, not of the chess.
# It proved stable here across scheduling and boot timing, but it is an
# internal hash rather than behaviour, and a repair that shifts code layout
# could move it without changing a single move.  Asserting it would buy
# nothing and could cost a false alarm.  Excluded by policy, on purpose.
POLICY_EXCLUDE = {'hashKey'}

# 0x88 workspace addresses.  Every one of these was confirmed by execution on
# the pristine tape (e.g. board[] read back the FEN that was injected;
# genCount/moveBuf read back 20 at the start position and 48 at Kiwipete).
ADDR = {
    'board':      0xE000,   # 128 bytes: 8 ranks of 16, only files 0..7 on-board
    'sideToMove': 0xE080,
    'castling':   0xE081,
    'epSquare':   0xE082,
    'halfmove':   0xE083,
    'wking':      0xE084,
    'bking':      0xE085,
    'cursorSq':   0xE086,
    'selSq':      0xE087,
    'gameState':  0xE088,
    'humanSide':  0xE089,
    'aiDepth':    0xE08A,
    'moveCount':  0xE093,
    'genCount':   0xE0A0,
    'gamePhase':  0xE107,
    'lastScore':  0xE120,
    'twoPlayer':  0xE0F3,
    'blackDepth': 0xE15E,
    'moveBuf':    0x6000,   # ply-0 legal-move buffer, 4 bytes/move
}


def load_chesspos(harness):
    # The harness lives inside case01, which is a published record: importing
    # from it must not leave a __pycache__ behind.
    sys.dont_write_bytecode = True
    sys.path.insert(0, os.path.join(harness, 'tools'))
    try:
        import chesspos
    except ImportError:
        sys.stderr.write('cannot import %s/tools/chesspos.py\n' % harness)
        raise
    return chesspos


# --------------------------------------------------------------------------
# screen handling
# --------------------------------------------------------------------------

CLOCK_RE = re.compile(r'\b([WB]) \d+:\d\d')


def screen_lines(text):
    """The final screen, normalised to the parts that are not timing noise.

    - piece glyphs OCR as '?' and carry no information -> deleted
    - the two chess clocks tick with wall-frames -> masked
    - blank lines dropped
    """
    if '=== SCREEN ===' in text:
        text = text.split('=== SCREEN ===', 1)[1]
    if '=== END ===' in text:
        text = text.split('=== END ===', 1)[0]
    out = []
    for raw in text.splitlines():
        line = raw.replace('?', '')
        line = CLOCK_RE.sub(r'\1 -:--', line)
        line = line.rstrip()
        if line.strip():
            out.append(line.strip())
    return out


def status_line(lines):
    """The game's status message: the line two above the key-help footer."""
    for i, ln in enumerate(lines):
        if ln.startswith('QAOP+ENT'):
            return lines[i - 1] if i >= 1 else ''
    return ''


PANEL_RE = {
    'Level': re.compile(r'Level\s+(\S+)'),
    'Matl': re.compile(r'Matl\s+(-?\S+)'),
    'Move': re.compile(r'Move\s+(\S+)'),
    'Eval': re.compile(r'Eval\s+(-?\S+)'),
}


def panel(lines):
    blob = '\n'.join(lines)
    out = {}
    for k, rx in PANEL_RE.items():
        m = rx.search(blob)
        if m:
            out[k] = m.group(1)
    return out


# --------------------------------------------------------------------------
# snapshot handling
# --------------------------------------------------------------------------

def observe_sna(C, path):
    ram = C.sna_ram(path)
    u8 = lambda a: C.u8(ram, a)                              # noqa: E731
    st = C.state_dict(ram)
    n = u8(ADDR['genCount'])
    buf = C.peek(ram, ADDR['moveBuf'], max(n, 1) * 4)
    moves = []
    for i in range(n):
        f, t, fl = buf[i * 4], buf[i * 4 + 1], buf[i * 4 + 2]
        moves.append('%s%s.%d' % (C.sqname(f), C.sqname(t), fl))
    board128 = C.peek(ram, ADDR['board'], 128)
    return {
        'fen': st['fen'],
        'side': st['side'],
        'castling': st['castling'],
        'ep': st['ep'],
        'halfmove': st['halfmove'],
        'gameState': st['gameState'],
        'gameStateName': st['gameStateName'],
        'lastMove': st['lastMove'],
        'lastScore': st['lastScore'],
        'material': st['material'],
        'gamePhase': st['gamePhase'],
        'moveLogN': st['moveLogN'],
        'moveLog': st['moveLog'],
        'moveCount': C.u16(ram, ADDR['moveCount']),
        'wking': C.sqname(u8(ADDR['wking'])),
        'bking': C.sqname(u8(ADDR['bking'])),
        'aiDepth': u8(ADDR['aiDepth']),
        'blackDepth': u8(ADDR['blackDepth']),
        'twoPlayer': u8(ADDR['twoPlayer']),
        'cursor': st['cursor'],
        'selSq': u8(ADDR['selSq']),
        'hashKey': st['hashKey'],
        'genCount': n,
        'moveList': ' '.join(moves),
        'board128': board128.hex(),
    }


# --------------------------------------------------------------------------
# running one case
# --------------------------------------------------------------------------

def tap_with_position(C, base_tap, fen, depth, out_path):
    blk = C.tap_data_block(C.fen_to_block(fen, depth))
    with open(out_path, 'wb') as f:
        f.write(open(base_tap, 'rb').read() + blk)
    return out_path


def schedule(case, sched, C):
    """Return (list of --type args, final frame)."""
    typ = []
    frame = sched['load_frame']
    pre = ''
    if case.get('depth', 2) != 2:
        pre += str(case['depth'])
    if case.get('two_player'):
        pre += 'v'
    if case.get('fen'):
        pre += 'l'
    pre += case.get('pre', '')
    if pre:
        typ.append('%s@%d' % (pre, frame))
    frame += sched['wait']
    cursor = case.get('cursor', 'e2')
    # A case may ask for a tighter cadence (long two-player games would
    # otherwise run a side's 5:00 clock out).  The profile still scales it, so
    # the A/B cross-check keeps its teeth.
    gap = sched['gap']
    if case.get('gap'):
        gap = max(150, int(case['gap'] * sched['gap'] / 900.0))
    for mv in case.get('moves', []):
        typ.append('%sx@%d' % (C.move_keys([mv], cursor), frame))
        cursor = mv[2:4]
        frame += gap
    for k in case.get('post', []):
        typ.append('%s@%d' % (k, frame))
        frame += gap
    return typ, frame + sched['tail']


def run_emulator(args, tap, typ_args, frames, sna, save_tape, timeout):
    cmd = [args.emu, '--machine', args.machine, '--rom', args.rom, tap,
           '--autoload', '--turbo', '--frames', str(frames), '--text']
    if sna:
        cmd += ['--save-sna', sna]
    if save_tape:
        cmd += ['--save-tape', save_tape]
    for t in typ_args:
        cmd += ['--type', t]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise RunError('emulator TIMEOUT after %ds (%s)' % (timeout, ' '.join(cmd)))
    if r.returncode != 0:
        raise RunError('emulator exit %d: %s' % (r.returncode, r.stderr.strip()[:400]))
    return r.stdout


class RunError(Exception):
    pass


def tap_blocks(path):
    d = open(path, 'rb').read()
    out, i = [], 0
    while i + 2 <= len(d):
        ln = d[i] | (d[i + 1] << 8)
        out.append(d[i + 2:i + 2 + ln])
        i += 2 + ln
    return out


def run_case(args, C, case, sched, tmpdir):
    """Run one case and return its observation dict."""
    args.machine = case.get('machine', '48k')
    obs = {}
    tap = args.tap
    if case.get('fen'):
        tap = tap_with_position(C, args.tap, case['fen'], case.get('depth', 2),
                                os.path.join(tmpdir, 'pos.tap'))

    if case['kind'] == 'perft':
        # the engine's own built-in perft / incremental-state self-test (key T)
        frames = sched['perft_frames']
        cmd = [args.emu, '--machine', args.machine, '--rom', args.rom, tap,
               '--autoload', '--turbo', '--keys', '%d:T' % sched['load_frame'],
               '--frames', str(frames), '--text']
        try:
            r = subprocess.run(cmd, capture_output=True, text=True,
                               timeout=case.get('timeout', 600))
        except subprocess.TimeoutExpired:
            raise RunError('emulator TIMEOUT after %ds' % case.get('timeout', 600))
        if r.returncode != 0:
            raise RunError('emulator exit %d' % r.returncode)
        obs['screen'] = screen_lines(r.stdout)
        return obs

    typ, frames = schedule(case, sched, C)
    sna = os.path.join(tmpdir, 'final.sna')
    save_tape = os.path.join(tmpdir, 'saved.tap') if case.get('expect_save') else None
    if save_tape and os.path.exists(save_tape):
        os.unlink(save_tape)
    out = run_emulator(args, tap, typ, frames, sna, save_tape,
                       case.get('timeout', 300))
    lines = screen_lines(out)
    obs['screen'] = lines
    obs['status'] = status_line(lines)
    obs['panel'] = panel(lines)
    obs.update(observe_sna(C, sna))

    if save_tape:
        if not os.path.exists(save_tape):
            raise RunError('the game never SAVEd: no tape captured')
        blocks = tap_blocks(save_tape)
        if len(blocks) != 1:
            raise RunError('expected one saved block, got %d' % len(blocks))
        obs['savedBlock'] = blocks[0].hex()

        # ...and load it straight back in: a genuine save -> load round-trip.
        rt = os.path.join(tmpdir, 'roundtrip.tap')
        with open(rt, 'wb') as f:
            f.write(open(args.tap, 'rb').read() +
                    open(save_tape, 'rb').read())
        rt_case = {'kind': 'session', 'two_player': True, 'fen': None,
                   'depth': case.get('depth', 2), 'pre': 'l', 'moves': [],
                   'post': case.get('rt_post', [])}
        rt_typ, rt_frames = schedule(rt_case, sched, C)
        rt_sna = os.path.join(tmpdir, 'rt.sna')
        run_emulator(args, rt, rt_typ, rt_frames, rt_sna, None, 300)
        rt_obs = observe_sna(C, rt_sna)
        for k in ('fen', 'side', 'castling', 'ep', 'halfmove', 'moveCount',
                  'wking', 'bking', 'aiDepth', 'board128'):
            obs['rt_' + k] = rt_obs[k]
    return obs


# --------------------------------------------------------------------------
# comparison
# --------------------------------------------------------------------------

def diff(expected, actual):
    bad = []
    for k in sorted(expected):
        if k not in actual:
            bad.append((k, expected[k], '<missing>'))
        elif actual[k] != expected[k]:
            bad.append((k, expected[k], actual[k]))
    return bad


def fmt(v, width=120):
    s = json.dumps(v) if not isinstance(v, str) else v
    return s if len(s) <= width else s[:width] + ' ...(%d chars)' % len(s)


def build_baseline(paths, out):
    """Intersect several recordings; a field survives only if all agree.

    This is the whole verification protocol for the baseline.  The recordings
    are taken under DIFFERENT scheduling profiles, so anything that depends on
    when the keys arrived rather than on what the engine computed disagrees and
    is silently dropped, together with a note of why.  Nothing timing-sensitive
    can reach expected.json without at least two profiles agreeing on it.
    """
    recs = [json.load(open(p)) for p in paths]
    if len(recs) < 2:
        sys.stderr.write('--build-baseline needs at least two recordings\n')
        return 2
    taps = {r.get('tap') for r in recs}
    if len(taps) != 1:
        sys.stderr.write('recordings are of different tapes: %s\n' % taps)
        return 2
    base, dropped, thin = {}, [], []
    for n in sorted(recs[0]['cases']):
        others = [r for r in recs[1:] if n in r['cases']]
        if not others:
            thin.append(n)
            continue
        keep = {}
        for k, v in recs[0]['cases'][n].items():
            if k in POLICY_EXCLUDE:
                dropped.append((n, k, 'policy'))
                continue
            if all(r['cases'][n].get(k) == v for r in others):
                keep[k] = v
            else:
                dropped.append((n, k, 'disagreed across profiles'))
        base[n] = keep
    if thin:
        sys.stderr.write('these cases were recorded only once, so nothing '
                         'corroborates them -- refusing:\n  %s\n'
                         % '\n  '.join(thin))
        return 2
    with open(out, 'w') as f:
        json.dump({'source': [os.path.abspath(p) for p in paths],
                   'tap': recs[0].get('tap'),
                   'profiles': [r.get('profile') for r in recs],
                   'cases': base}, f, indent=1, sort_keys=True)
    print('baseline: %d cases, %d fields, %d dropped -> %s'
          % (len(base), sum(len(v) for v in base.values()), len(dropped), out))
    for n, k, why in dropped:
        print('  dropped %-28s %-12s (%s)' % (n, k, why))
    return 0


# --------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tap', help='the chess.tap under test (required to run)')
    ap.add_argument('--harness', default=DEFAULT_HARNESS,
                    help='hc91emu harness directory (default: the case01 harness)')
    ap.add_argument('--emu', help='hc91emu binary (default: <harness>/build/hc91emu)')
    ap.add_argument('--rom', help='48K ROM (default: <harness>/roms/48.rom)')
    ap.add_argument('--expected', default=os.path.join(HERE, 'expected.json'))
    ap.add_argument('--filter', default='',
                    help='only cases whose name or group contains this string')
    ap.add_argument('--record', metavar='OUT.json',
                    help='RECORD mode: write observations to OUT.json instead '
                         'of comparing.  Only ever legitimate against the '
                         'pristine tape -- see README.')
    ap.add_argument('--profile', default='A', choices=sorted(PROFILES),
                    help='scheduling profile (A default, B = shifted frames)')
    ap.add_argument('--verbose', action='store_true')
    ap.add_argument('--keep', action='store_true', help='keep temp artefacts')
    ap.add_argument('--build-baseline', nargs='+', metavar='REC.json',
                    help='combine two or more --record files into --expected: '
                         'a field is kept only if every recording agrees on it')
    args = ap.parse_args(argv)

    if args.build_baseline:
        return build_baseline(args.build_baseline, args.expected)

    if not args.tap:
        sys.stderr.write('--tap is required\n')
        return 2
    args.machine = '48k'
    args.emu = args.emu or os.path.join(args.harness, 'build', 'hc91emu')
    args.rom = args.rom or os.path.join(args.harness, 'roms', '48.rom')
    for p in (args.tap, args.emu, args.rom):
        if not os.path.exists(p):
            sys.stderr.write('missing: %s\n' % p)
            return 2
    C = load_chesspos(args.harness)

    sched = PROFILES[args.profile]
    cases = [c for c in CASES
             if not args.filter or args.filter in c['name'] or args.filter in c['group']]
    if not cases:
        sys.stderr.write('no cases match --filter %r\n' % args.filter)
        return 2

    expected = {}
    if not args.record:
        if not os.path.exists(args.expected):
            sys.stderr.write('no %s -- run with --record first\n' % args.expected)
            return 2
        expected = json.load(open(args.expected))['cases']

    tmpdir = tempfile.mkdtemp(prefix='armA_char.')
    recorded, npass, nfail, nerr = {}, 0, 0, 0
    try:
        for c in cases:
            label = '%-28s' % c['name']
            try:
                obs = run_case(args, C, c, sched, tmpdir)
            except RunError as e:
                print('ERROR %s %s' % (label, e))
                nerr += 1
                continue
            if args.record:
                recorded[c['name']] = obs
                print('rec   %s %d fields' % (label, len(obs)))
                continue
            exp = expected.get(c['name'])
            if exp is None:
                print('ERROR %s no recorded baseline' % label)
                nerr += 1
                continue
            bad = diff(exp, obs)
            if bad:
                nfail += 1
                print('FAIL  %s %s' % (label, c['what']))
                for k, e, a in bad:
                    print('        %-12s expected %s' % (k, fmt(e)))
                    print('        %-12s actual   %s' % ('', fmt(a)))
            else:
                npass += 1
                print('ok    %s %s' % (label, c['what']))
                if args.verbose:
                    for k in sorted(exp):
                        print('        %-12s %s' % (k, fmt(exp[k])))
    finally:
        if args.keep:
            print('artefacts in %s' % tmpdir)
        else:
            shutil.rmtree(tmpdir, ignore_errors=True)

    if args.record:
        with open(args.record, 'w') as f:
            json.dump({'profile': args.profile, 'tap': os.path.abspath(args.tap),
                       'cases': recorded}, f, indent=1, sort_keys=True)
        print('\nrecorded %d cases -> %s' % (len(recorded), args.record))
        return 0

    print('\n%d ok, %d failed, %d errors (of %d cases)'
          % (npass, nfail, nerr, len(cases)))
    return 0 if (nfail == 0 and nerr == 0) else 1


if __name__ == '__main__':
    sys.exit(main())
