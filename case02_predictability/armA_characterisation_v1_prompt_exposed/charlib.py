#!/usr/bin/env python3
"""charlib — the emulator driver behind the characterisation suite.

Everything here is a thin, deterministic wrapper around the harness:

    hc91emu  +  roms/48.rom  +  <build under test>.tap

It reuses the harness's own ``tools/chesspos.py`` for the FEN <-> save-block
encoding and for decoding a ``.sna`` snapshot back into a game state, so the
suite never re-implements the engine's memory layout.

The only thing this module adds is a *fixed keystroke schedule*.  The engine
repaints the whole screen between moves and ignores keys that arrive during a
repaint, so every run in the suite uses the same frame budget per action.  Two
invocations with the same arguments therefore produce the same run, byte for
byte — that is what makes a recorded value a usable expectation.

No test logic lives here.  See ``cases.py`` for the cases and ``run.py`` for
the runner.
"""

import os
import shutil
import subprocess
import sys
import tempfile

# --------------------------------------------------------------------------
# Locating the harness
# --------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))


class HarnessNotFound(RuntimeError):
    pass


class BuildNotFound(RuntimeError):
    pass


def find_harness(explicit=None):
    """Return the harness directory (the one holding build/hc91emu).

    Order: --harness / $HC91_HARNESS, then a short list of places the suite is
    likely to sit relative to it.  Raises with a helpful message if not found.
    """
    cands = []
    if explicit:
        cands.append(explicit)
    if os.environ.get('HC91_HARNESS'):
        cands.append(os.environ['HC91_HARNESS'])
    cands += [
        os.path.join(HERE, 'harness'),
        os.path.join(HERE, '..', 'harness'),
        os.path.join(HERE, '..', '..', 'harness'),
        os.path.join(HERE, '..', 'arms', 'harness'),
        os.path.join(HERE, '..', '..', 'arms', 'harness'),
        os.path.join(HERE, '..', '..', '..', 'arms', 'harness'),
    ]
    for c in cands:
        c = os.path.abspath(c)
        if os.path.isfile(os.path.join(c, 'build', 'hc91emu')) and \
           os.path.isfile(os.path.join(c, 'tools', 'chesspos.py')):
            return c
    raise HarnessNotFound(
        "characterisation suite: cannot find the harness.\n"
        "Looked for a directory containing build/hc91emu and tools/chesspos.py in:\n  "
        + "\n  ".join(os.path.abspath(c) for c in cands) +
        "\nPass --harness DIR (or set HC91_HARNESS) to point at arms/harness.")


def load_chesspos(harness):
    """Import the harness's chesspos module (single source of truth for layout)."""
    tools = os.path.join(harness, 'tools')
    if tools not in sys.path:
        sys.path.insert(0, tools)
    import chesspos                                          # noqa: E402
    return chesspos


# --------------------------------------------------------------------------
# The fixed frame schedule
# --------------------------------------------------------------------------
#
# LOAD_FRAME   when the pre-keys (level digit, V, L) are typed
# WAIT         frames the tape load and the following repaint get
# GAP          frames each scripted move gets (must cover an engine reply)
# TAIL         frames after the last action, before the snapshot is taken
#
# These are deliberately generous: a run that is too tight silently drops a
# keystroke and produces a wrong "observation" rather than an error.  Every
# case that expects a move to land also asserts moveLogN, which catches a
# dropped keystroke loudly.

LOAD_FRAME = 700
WAIT = 200
GAP = 900
TAIL = 1500


class Emu:
    """One build under test, driven headlessly."""

    def __init__(self, harness, tap, machine='48k', rom=None):
        self.harness = os.path.abspath(harness)
        self.tap = os.path.abspath(tap)
        self.machine = machine
        self.rom = rom or os.path.join(self.harness, 'roms', '48.rom')
        self.emu = os.path.join(self.harness, 'build', 'hc91emu')
        self.chesspos = load_chesspos(self.harness)
        if not os.path.isfile(self.tap):
            raise BuildNotFound('build under test not found: %s' % self.tap)

    # -- low level ---------------------------------------------------------

    def _tap_with(self, blocks):
        """chess.tap with extra tape blocks appended (position / saved game)."""
        data = open(self.tap, 'rb').read()
        for b in blocks:
            data += b
        return data

    def run(self, fen=None, depth=2, two_player=False, moves=(), pre='', post='',
            post_gap=None, extra_blocks=(), load_block=None, load=None,
            want_screen=False, save_tape=None, gap=GAP, tail=TAIL, wait=WAIT,
            machine=None, keep=None):
        """Boot the build, drive it, and return the decoded final state.

        fen           start position, injected through the game's own tape
                      loader (``L``).  None = the normal new game.
        depth         engine strength 1..5, typed before the load so that the
                      engine (which plays Black) actually gets it.
        two_player    press ``V`` first: the engine never moves.
        moves         list of "e2e4" / "a7a8q" strings, played with the cursor.
        pre           extra raw keys pressed with the pre-key burst.
        post          raw keys pressed after the last move (``z``, ``n``,
                      ``g`` ...), given their own frame slot.
        extra_blocks  raw tape blocks appended after chess.tap (used to replay
                      a game the engine itself saved).
        load_block    a pre-built 71-byte save-block payload, instead of fen.
        load          press ``L``.  Default: yes iff a fen/load_block/extra
                      block was supplied.
        want_screen   also capture the OCR of the final screen.
        save_tape     capture the engine's own ``SAVE`` output to this path.
        keep          directory to keep the .sna in (else a temp dir).

        Returns the dict from chesspos.state_dict, plus:
            _screen   the OCR text, if want_screen
            _cmd      the exact emulator command line (for failure reports)
        """
        cp = self.chesspos
        tmp = tempfile.mkdtemp(prefix='charsuite.')
        try:
            blocks = list(extra_blocks)
            if fen is not None or load_block is not None:
                payload = load_block if load_block is not None else \
                    cp.fen_to_block(fen, depth)
                blocks.insert(0, cp.tap_data_block(payload))

            tap = self.tap
            if blocks:
                tap = os.path.join(tmp, 'run.tap')
                with open(tap, 'wb') as f:
                    f.write(self._tap_with(blocks))

            sna = os.path.join(keep or tmp, 'final.sna')
            cmd = [self.emu, '--machine', machine or self.machine,
                   '--rom', self.rom, tap, '--autoload', '--turbo',
                   '--save-sna', sna]
            if save_tape:
                cmd += ['--save-tape', save_tape]

            frame = LOAD_FRAME
            keys = ''
            # The strength digit sets BOTH sides' depth; a tape load restores
            # only White's, so it must be pressed BEFORE the load.
            if depth != 2:
                keys += str(depth)
            # V must precede the load: a loaded Black-to-move position goes
            # straight to the engine, and a later V would arrive too late.
            if two_player:
                keys += 'v'
            do_load = bool(blocks) if load is None else load
            if do_load:
                keys += 'l'
            keys += pre
            if keys:
                cmd += ['--type', '%s@%d' % (keys, frame)]
            frame += wait

            cursor = 'e2'
            for mv in moves:
                # 'x' is unbound in the game and pads the string so that a
                # trailing ENTER is never eaten.
                cmd += ['--type', '%sx@%d' % (cp.move_keys([mv], cursor), frame)]
                cursor = mv[2:4]
                frame += gap

            if post:
                cmd += ['--type', '%sx@%d' % (post, frame)]
                frame += post_gap or gap

            cmd += ['--frames', str(frame + tail)]
            if want_screen:
                cmd += ['--text']

            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                raise EmuError('emulator exited %d\n%s\ncmd: %s'
                               % (r.returncode, r.stderr[-2000:], ' '.join(cmd)))
            if not os.path.isfile(sna):
                raise EmuError('no snapshot written\ncmd: %s' % ' '.join(cmd))

            st = cp.state_dict(cp.sna_ram(sna))
            st['_cmd'] = ' '.join(cmd)
            if want_screen:
                st['_screen'] = r.stdout
            return st
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def perft_selftest(self, frames=95000, machine=None):
        """Press ``T`` and return the self-test screen (OCR text)."""
        cmd = [self.emu, '--machine', machine or self.machine, '--rom', self.rom,
               self.tap, '--autoload', '--turbo', '--keys', '960:T',
               '--frames', str(frames), '--text']
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise EmuError('emulator exited %d\n%s' % (r.returncode, r.stderr[-2000:]))
        return r.stdout


class EmuError(RuntimeError):
    pass


# --------------------------------------------------------------------------
# Observation
# --------------------------------------------------------------------------
#
# Fields the suite NEVER compares, and why:
#
#   hashKey   the Zobrist tables are PRNG-seeded at boot from the code image,
#             so any change in code size or layout moves every key.  It is not
#             a behavioural observable.
#   cursor    an artefact of the keystroke script, not of the chess.
#   clocks    (not in state_dict, read off the screen) depend on how many
#             frames the search burned, i.e. on code speed, not correctness.
#   aiDepth / twoPlayer are echoes of the harness's own inputs; only the
#             cases that specifically test the level keys look at them.

VOLATILE = ('hashKey', 'cursor', '_cmd', '_screen')


def observe(state, fields):
    """Project a state dict onto the fields a case declares it cares about."""
    out = {}
    for f in fields:
        if f in VOLATILE:
            raise ValueError('%s is excluded from comparison by design' % f)
        if f not in state:
            raise KeyError('no such observable: %s' % f)
        out[f] = state[f]
    return out
