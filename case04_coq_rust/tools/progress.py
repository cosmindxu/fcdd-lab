#!/usr/bin/env python3
"""Case 04 — progress monitor. Reports completed/total + measured rates +
ETAs for the checkpointed jobs, liveness of the calibration arms, and the
remaining pipeline checklist."""
import json
import os
import subprocess
import time

LAB = "/media/sf_Projects/fcdd_lab/case04_coq_rust"
RAW = os.path.join(LAB, "ledger", "raw")
REF = "/tmp/opencode/referee_smoke.jsonl"
ENG = os.path.join(LAB, "ledger", "sealing_partial.jsonl")
N = 11103


def count(path):
    try:
        return sum(1 for _ in open(path))
    except OSError:
        return 0


def rate_eta(path, total, t0):
    n = count(path)
    if n == 0:
        return n, total, None
    age = max(time.time() - t0, 60)
    rate = n / age
    eta = (total - n) / rate if rate > 0 else None
    return n, total, eta


def hms(s):
    if s is None:
        return "??"
    s = int(s)
    return "%dh%02dm" % (s // 3600, (s % 3600) // 60)


def unit(arm):
    r = subprocess.run(["systemctl", "--user", "is-active",
                        "c04-cal-%s" % arm], capture_output=True, text=True)
    return r.stdout.strip()


def arm_info(arm):
    jl = os.path.join(RAW, "%s_ds_cal.jsonl" % arm)
    try:
        size = os.path.getsize(jl)
        mtime = time.time() - os.path.getmtime(jl)
    except OSError:
        return None
    ws = "/home/xcos/fcdd_c04_ds/%s" % arm
    notes = os.path.isfile(os.path.join(ws, "NOTES.md"))
    crate = os.path.isfile(os.path.join(ws, "chess_clone", "Cargo.toml")) or \
        os.path.isfile(os.path.join(ws, "skeleton", "Cargo.toml"))
    smoke_pass = False
    for p in (os.path.join(ws, "NOTES.md"),):
        pass
    return dict(size=size, idle="%.1fm" % (mtime / 60), notes=notes,
                crate=crate)


print("=== checkpointed jobs (rate measured over the job's lifetime) ===")
def t0_of(path):
    try:
        st = os.stat(path)
        return getattr(st, "st_birthtime", None) or st.st_ctime - 3600
    except OSError:
        return time.time() - 60

for name, path, total in (("referee (twin)   ", REF, N),
                          ("engine crosscheck", ENG, N)):
    n, tot, eta = rate_eta(path, total, t0_of(path))
    pct = 100.0 * n / total if n else 0
    print("  %s %5d/%d (%5.1f%%)  ETA %s" % (name, n, total, pct, hms(eta)))

print("=== calibration arms (liveness, no % — open-ended agent work) ===")
for arm in ("armA", "armB"):
    u = unit(arm)
    info = arm_info(arm)
    if info is None:
        print("  %s: no session log yet (unit %s)" % (arm, u))
        continue
    print("  %s: unit=%s  events=%dKB  last-event=%s ago  NOTES=%s"
          % (arm, u, info["size"] // 1024, info["idle"], info["notes"]))

print("=== remaining pipeline ===")
done = ["P1 oracle self-consistency", "P2 corpus measured",
        "P3 extraction spike", "D9 referee built (perft-gated)"]
for d in done:
    print("  [x] %s" % d)
print("  [~] referee pass (%d/%d) + engine sealing (%d/%d) "
      % (count(REF), N, count(ENG), N))
print("  [ ] cross-check + seal answers.json + bug inventory")
print("  [ ] calibration completes -> freeze values (k, cap, timeouts, gate)")
print("  [ ] pre-registration frozen (replace (pilot) marks, commit)")
print("  [ ] 13 scored runs (5 A + 5 B + 3 B-flash), systemd, watcher-guarded")
print("  [ ] analysis + >=2 adversarial review rounds + article")
