#!/usr/bin/env python3
"""A17 GUARD — refuse to launch a run whose workspace can leak the answer.

Case02's design was invalidated because `run_resilient.sh` copied a whole tree
into every treated workspace, and that tree contained the pristine binary
bit-identical to the sealed answer key. One `cmp -l` localised any seeded fault.
Nobody noticed for three review rounds because the check was a person's
diligence, not a program.

This is that check as a program. It runs at workspace-build time, BEFORE the
agent is invoked, and exits non-zero if the workspace is compromised. A run that
cannot pass it does not happen.

Three independent tests, because the leak can take three shapes:

  1. SEALED-CONTENT MATCH. No file in the workspace may hash-match any file in
     the sealed directory, except files the manifest explicitly declares as
     intentionally shared (e.g. the seeded variant itself). Catches the A17 case
     directly.
  2. NEAR-MISS BINARY. No file in the workspace may differ from a sealed binary
     in fewer than THRESHOLD bytes. A "nearly pristine" artefact is as good as
     the answer for a single-byte fault, and hashing alone would miss it.
  3. MANIFEST DECLARATION. Every file shipped must be listed in the arm's
     manifest with its expected hash. An undeclared file is a failure whether or
     not it matches anything sealed -- that is what stopped A17 being seen: the
     artifacts/ directory was never enumerated anywhere.

Usage:  workspace_manifest_guard.py <workspace> <arm> <manifest.json> <sealed_dir>
Exit :  0 clean, 1 leak detected, 2 usage/IO error
"""
import hashlib, json, os, sys

NEAR_MISS_BYTES = 64          # a file within this many bytes of a sealed binary
SKIP_EXT = (".olean", ".pyc", ".png", ".gif", ".log")

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()

def walk(root):
    for dirpath, dirnames, files in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ("__pycache__", ".git")]
        for f in files:
            if f.endswith(SKIP_EXT): continue
            yield os.path.join(dirpath, f)

def byte_distance(a, b, cap):
    """Number of differing bytes, short-circuiting past `cap`. Sizes must match."""
    if os.path.getsize(a) != os.path.getsize(b): return None
    n = 0
    with open(a, "rb") as fa, open(b, "rb") as fb:
        while True:
            ba, bb = fa.read(1 << 16), fb.read(1 << 16)
            if not ba: return n
            for x, y in zip(ba, bb):
                if x != y:
                    n += 1
                    if n > cap: return None

def main():
    if len(sys.argv) != 5:
        print(__doc__); return 2
    ws, arm, manifest_path, sealed = sys.argv[1:5]
    manifest = json.load(open(manifest_path))
    allowed = manifest["arms"][arm]           # {relpath: sha256}
    shared_ok = set(manifest.get("intentionally_shared", []))

    sealed_files = {}
    for p in walk(sealed):
        try: sealed_files[sha(p)] = p
        except OSError: pass

    failures = []
    seen = set()
    for p in walk(ws):
        rel = os.path.relpath(p, ws)
        seen.add(rel)
        try: h = sha(p)
        except OSError: continue

        # 3. undeclared
        if rel not in allowed:
            failures.append(("UNDECLARED", rel, "not listed in the %s manifest" % arm))
            continue
        if allowed[rel] not in (h, "*"):
            failures.append(("ALTERED", rel, "hash differs from the manifest"))

        # 1. sealed-content match
        if h in sealed_files and rel not in shared_ok:
            failures.append(("SEALED-MATCH", rel,
                             "byte-identical to sealed %s" % os.path.basename(sealed_files[h])))

        # 2. near-miss
        if rel not in shared_ok:
            for sp in sealed_files.values():
                d = byte_distance(p, sp, NEAR_MISS_BYTES)
                if d is not None and 0 < d <= NEAR_MISS_BYTES:
                    failures.append(("NEAR-MISS", rel,
                                     "differs from sealed %s in only %d bytes"
                                     % (os.path.basename(sp), d)))
                    break

    for rel in allowed:
        if rel not in seen and allowed[rel] != "*":
            failures.append(("MISSING", rel, "declared in the manifest but not shipped"))

    if failures:
        print("WORKSPACE GUARD: FAILED (%d)" % len(failures))
        for kind, rel, why in failures[:40]:
            print("  [%-12s] %-52s %s" % (kind, rel, why))
        return 1
    print("WORKSPACE GUARD: clean — %d files, all declared, none recoverable from sealed" % len(seen))
    return 0

if __name__ == "__main__":
    sys.exit(main())
