#!/usr/bin/env python3
"""C1 PRIMARY CONTROL — assert the two arms' workspaces are byte-identical.

Case02 shipped the arms two DIFFERENT packages and argued about their relative
value; three review rounds later one of them turned out to contain the answer
(A17). The argument was the vulnerability. This replaces it with an equality
test.

Both arms' workspaces must agree on every file, byte for byte, except an
explicitly declared difference list — in practice PROMPT.md alone, which carries
the method instruction. Anything else differing is a design defect and the cell
does not launch.

The property this buys: a leak that survives is necessarily SYMMETRIC. It
degrades the benchmark for both arms, which the pooled-CORRECT-rate gate
detects loudly, instead of tilting one arm, which case02 could not see for three
rounds.

Usage:  parity_assert.py <ws_armA> <ws_armB> [--allow PROMPT.md ...]
Exit :  0 identical modulo the allow-list, 1 parity violated, 2 usage error
"""
import hashlib, os, sys

SKIP = ("__pycache__", ".git")

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 16), b""): h.update(c)
    return h.hexdigest()

def inventory(root):
    out = {}
    for dp, dn, fs in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP]
        for f in fs:
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, root)
            if os.path.islink(p):
                out[rel] = ("symlink", os.readlink(p))
            else:
                out[rel] = ("file", sha(p), os.path.getsize(p), oct(os.stat(p).st_mode & 0o777))
    return out

def main():
    argv = sys.argv[1:]
    allow = set()
    if "--allow" in argv:
        i = argv.index("--allow")
        allow = set(argv[i + 1:])          # everything after --allow is a path
        argv = argv[:i]                     # positional args are what precedes it
    if len(argv) != 2:
        print(__doc__); return 2
    args = argv
    A, B = inventory(args[0]), inventory(args[1])

    bad = []
    for rel in sorted(set(A) | set(B)):
        if rel in allow: continue
        if rel not in A: bad.append(("ONLY-IN-B", rel, ""))
        elif rel not in B: bad.append(("ONLY-IN-A", rel, ""))
        elif A[rel] != B[rel]:
            why = "content" if A[rel][0] == "file" and A[rel][1] != B[rel][1] else "mode/type/target"
            bad.append(("DIFFERS", rel, why))

    for rel in allow:
        if rel not in A or rel not in B:
            bad.append(("ALLOW-MISSING", rel, "declared as differing but absent from an arm"))

    if bad:
        print("PARITY: VIOLATED (%d)" % len(bad))
        for k, rel, why in bad[:40]:
            print("  [%-13s] %-56s %s" % (k, rel, why))
        return 1
    print("PARITY: clean — %d files identical across arms; %d declared difference(s): %s"
          % (len(A) - len(allow), len(allow), ", ".join(sorted(allow)) or "none"))
    return 0

if __name__ == "__main__":
    sys.exit(main())
