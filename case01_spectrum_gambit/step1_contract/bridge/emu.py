"""
The SHELL (FCDD Beat 3.5) — the only impure module in the contract package.

It drives the REAL Z80 engine inside hc91emu, dumps a .sna snapshot, and
reads the engine's own state out of Spectrum RAM.  Honesty rules:

  * Provenance is stated per observable (the memory address it comes from,
    with the `equ` line in chess.asm that defines it).
  * A run that does not reach the expected screen is reported as UNJUDGEABLE,
    never silently as "conforming" (fail-direction: a broken harness must
    not read as a clean pass).
  * The move buffer at 0x6000 is only meaningful when the engine is parked
    in `humanMove`; `sample()` checks the status line before trusting it.

Falsifiability tier of everything read here: MONITORED — the twin and the
engine compute their answers from independent code, so a disagreement is a
real finding, not a format regression.
"""
import os
import subprocess
import tempfile

EMU = "/media/sf_Projects/HC91_emulator/build/hc91emu"
ROM = "/media/sf_Projects/HC91_emulator/roms/48.rom"
TAP = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "artifacts", "chess.tap")

# --- provenance: chess.asm equates -------------------------------------
A_BOARD      = 0xE000   # board    equ 0xE000   (128 bytes, 0x88 indexed)
A_STM        = 0xE080   # sideToMove
A_CASTLING   = 0xE081   # castling
A_EP         = 0xE082   # epSquare
A_HALFMOVE   = 0xE083   # halfmove
A_WKING      = 0xE084   # wking
A_BKING      = 0xE085   # bking
A_GAMESTATE  = 0xE088   # gameState 0 play,1 W-mated,2 B-mated,3 stale,4 draw
A_GENCOUNT   = 0xE0A0   # genCount  (moves left in the ply-0 buffer)
A_MOVECOUNT  = 0xE093   # moveCount (2 bytes)
A_MOVEBUF    = 0x6000   # moveBufBase, ply 0: 4 bytes/move (from,to,flag,score)
A_MOVELOG    = 0xE200   # moveLog   (2 bytes/ply: from,to)
A_MOVELOGN   = 0xE15D   # moveLogN
A_GAMEKEYS   = 0x5B00   # gameKeys  (2 bytes/ply, cap 250)
A_GAMEKEYN   = 0xE113   # gameKeyN  (plies recorded, cap 250)
A_HASHKEY    = 0xE10C   # hashKey (2 bytes, 16-bit Zobrist)
A_HAVELAST   = 0xE124   # haveLast (1 once the engine has moved)
A_LASTFROM   = 0xE122   # lastFrom / lastTo
A_AIDEPTH    = 0xE08A   # aiDepth


class Snapshot:
    """A 48K .sna: 27-byte header then RAM 0x4000..0xFFFF."""

    def __init__(self, path):
        with open(path, "rb") as f:
            self.raw = f.read()
        if len(self.raw) < 27 + 49152:
            raise ValueError("short .sna: %d bytes" % len(self.raw))

    def byte(self, a):
        return self.raw[27 + (a - 0x4000)]

    def word(self, a):
        return self.byte(a) | (self.byte(a + 1) << 8)

    def block(self, a, n):
        off = 27 + (a - 0x4000)
        return list(self.raw[off:off + n])


def run(frames, types=(), sna=None, extra=()):
    """Boot chess.tap, apply scheduled key events, snapshot.

    Returns (screen_text, Snapshot|None).  Raises on emulator failure —
    a broken harness must be LOUD."""
    tmp = sna or tempfile.mktemp(suffix=".sna")
    cmd = [EMU, "--machine", "48k", "--rom", ROM, "--autoload",
           "--frames", str(frames), "--text", "--save-sna", tmp]
    for s, f in types:
        cmd += ["--type", "%s@%d" % (s, f)]
    cmd += list(extra) + [os.path.abspath(TAP)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if r.returncode != 0:
        raise RuntimeError("hc91emu exit %d: %s" % (r.returncode, r.stderr[:400]))
    return r.stdout, Snapshot(tmp)


def read_state(sn):
    """The engine's live position + its own legal-move list."""
    board = sn.block(A_BOARD, 128)
    n = sn.byte(A_GENCOUNT)
    moves = [(sn.byte(A_MOVEBUF + 4 * i),
              sn.byte(A_MOVEBUF + 4 * i + 1),
              sn.byte(A_MOVEBUF + 4 * i + 2)) for i in range(n)]
    nlog = sn.byte(A_MOVELOGN)
    log = [(sn.byte(A_MOVELOG + 2 * i), sn.byte(A_MOVELOG + 2 * i + 1))
           for i in range(nlog)]
    return {
        "board": board,
        "stm": sn.byte(A_STM),
        "castling": sn.byte(A_CASTLING),
        "ep": sn.byte(A_EP),
        "halfmove": sn.byte(A_HALFMOVE),
        "wking": sn.byte(A_WKING),
        "bking": sn.byte(A_BKING),
        "moveCount": sn.word(A_MOVECOUNT),
        "gameState": sn.byte(A_GAMESTATE),
        "genCount": n,
        "legal": moves,
        "moveLog": log,
        "aiDepth": sn.byte(A_AIDEPTH),
        "hashKey": sn.word(A_HASHKEY),
        "gameKeyN": sn.byte(A_GAMEKEYN),
        "gameKeys": [sn.word(A_GAMEKEYS + 2 * i)
                     for i in range(sn.byte(A_GAMEKEYN))],
    }


# --- UI scripting -------------------------------------------------------
# Cursor keys with flipFlag = 0 (chess.asm:1295): Q rank+1, A rank-1,
# O file-1, P file+1.  SPACE and ENTER both select/drop (chess.asm:1256-9).

def cursor_path(cur, dst):
    """Key string that walks the cursor from `cur` to `dst`."""
    s = ""
    cf, cr = cur % 8, (cur // 16) % 8
    df, dr = dst % 8, (dst // 16) % 8
    s += "P" * (df - cf) if df > cf else "O" * (cf - df)
    s += "Q" * (dr - cr) if dr > cr else "A" * (cr - dr)
    return s


def move_keys(cur, frm, dst):
    """Keys to play frm->dst starting with the cursor on `cur`; also returns
    where the cursor ends up (chess.asm `hmMove` leaves it on `dst`)."""
    return cursor_path(cur, frm) + " " + cursor_path(frm, dst) + " ", dst


CHAR_FRAMES = 12          # keys.c: HOLD_FRAMES 6 + GAP_FRAMES 6


# After each move the engine runs updateTerminal (a full genLegal) and
# redraws; keys typed during that window are DROPPED.  MOVE_GAP is the
# measured-safe idle margin between moves (60 frames already suffices for the
# 14-ply Italian game; 150 is used for headroom).  A dropped key does NOT
# corrupt a sample silently: b5 compares the engine's own moveLog against the
# script and fails loudly on any mismatch.
MOVE_GAP = 150


def script(moves, start_frame=1000, prefix="", gap=MOVE_GAP):
    """Build --type options for a whole scripted game.

    `moves` is a list of (frm, dst) 0x88 squares.  Returns (types, end_frame).
    """
    types, cur, f = [], 0x14, start_frame          # cursorSq starts at e2
    if prefix:
        types.append((prefix, f))
        f += CHAR_FRAMES * len(prefix) + gap
    for frm, dst in moves:
        keys, cur = move_keys(cur, frm, dst)
        types.append((keys, f))
        f += CHAR_FRAMES * len(keys) + gap
    return types, f
