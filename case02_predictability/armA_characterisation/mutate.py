#!/usr/bin/env python3
"""mutate.py - patch one byte of a chess.tap, for testing this suite's teeth.

A characterisation suite that is green on pristine has proved nothing until it
has also been shown to go RED when behaviour changes.  This is the tool that
was used to show it (README section 5).

It rewrites one byte of the tape's last (code) block and repairs the block's
XOR checksum so the ROM loader still accepts it.  Offsets are into the block's
PAYLOAD, i.e. the loaded image, counting from 0.

    ./mutate.py pristine.tap /tmp/mut.tap 0x0B05 0x22
    ../armA_characterisation/characterise.py --tap /tmp/mut.tap

HOW THE TARGETS WERE FOUND
--------------------------
Without the pristine assembly source, the tables were located in the binary by
searching for byte patterns that any 0x88-board chess engine must contain --
chosen from first principles about how such engines are written, not from any
knowledge of this program's defects:

  * knight deltas on a 0x88 board are +-0x21, +-0x1F, +-0x12, +-0x0E;
    the ascending run 21 1F 12 0E occurs exactly once, at payload +0x0B05,
    immediately followed by its negation DF E1 EE F2 at +0x0B09
  * the orthogonal king/rook deltas 01 10 FF F0 occur exactly once, at +0x0B19
  * the piece values 100/320/330/500/900 as little-endian 16-bit words occur
    consecutively at +0x238F, +0x2391, +0x2393, +0x2395, +0x2397

The mutants recorded in the README, and how many of the 57 cases each turns red:

    0x0B05  21 -> 22   knight move delta        16 red
    0x0B19  01 -> 02   king orthogonal delta    18 red
    0x238F  64 -> 78   pawn value 100 -> 120     2 red
    0x2393  4A -> 3C   bishop value 330 -> 316   1 red

Offsets are for the pristine tape
(case01_spectrum_gambit/step1_contract/artifacts/chess.tap, 13,516-byte code
payload).  They will not be right for any other build; re-derive them with the
patterns above.
"""

import sys


def main(argv):
    if len(argv) != 5:
        sys.stderr.write(__doc__)
        return 2
    src, out, off, new = argv[1], argv[2], int(argv[3], 0), int(argv[4], 0)
    d = bytearray(open(src, 'rb').read())

    i, blocks = 0, []
    while i + 2 <= len(d):
        ln = d[i] | (d[i + 1] << 8)
        blocks.append((i, ln))
        i += 2 + ln
    if not blocks:
        sys.stderr.write('%s: no tape blocks\n' % src)
        return 2

    bo, bl = blocks[-1]                 # the code block is the last one
    start = bo + 2                      # flag byte
    payload = start + 1
    if off >= bl - 2:
        sys.stderr.write('offset 0x%X past the %d-byte payload\n' % (off, bl - 2))
        return 2

    old = d[payload + off]
    d[payload + off] = new
    chk = 0
    for b in d[start:start + bl - 1]:   # flag + payload
        chk ^= b
    d[start + bl - 1] = chk             # checksum byte

    open(out, 'wb').write(bytes(d))
    print('patched payload +0x%04X: %02X -> %02X  -> %s' % (off, old, new, out))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
