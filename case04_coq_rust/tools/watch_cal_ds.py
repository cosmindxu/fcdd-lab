#!/usr/bin/env python3
"""Case 04 — deepseek calibration watcher. Resumes dead calibration
sessions (opencode run -s sid) until each completes (last step_finish
reason stop/end_turn) or 8 attempts are spent. Appends resumed events to
the same jsonl. Log: ledger/raw/cal_watch_ds.log"""
import json
import os
import subprocess
import sys
import time

RAW = "/media/sf_Projects/fcdd_lab/case04_coq_rust/ledger/raw"
LAB = "/media/sf_Projects/fcdd_lab/case04_coq_rust"
ARMS = {
    "armA": dict(ws="/home/xcos/fcdd_c04_ds/armA", runid="cal-ds-armA",
                 model="deepseek/deepseek-v4-pro"),
    "armB": dict(ws="/home/xcos/fcdd_c04_ds/armB", runid="cal-ds-armB",
                 model="deepseek/deepseek-v4-pro"),
}
OPENCODE = os.path.expanduser("~/.opencode/bin/opencode")
DONE_REASONS = ("stop", "end_turn")
MAX_ATTEMPTS = 12
STALE = 300          # jsonl mtime older than this => dead
POLL = 60
CONTINUE_MSG = ("Your session was interrupted. Continue the task from where "
                "you stopped: re-read the workspace state, keep working per "
                "PROMPT.md, and proceed to the definition of done. Do not "
                "restart from scratch.")


def log(msg):
    with open(os.path.join(RAW, "cal_watch_ds.log"), "a") as f:
        f.write("%s %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))


def last_state(jl):
    if not os.path.isfile(jl):
        return None, None
    reason, sid = None, None
    try:
        for line in open(jl):
            if not line.strip():
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get("sessionID"):
                sid = d["sessionID"]
            if d.get("type") == "step_finish":
                r = (d.get("part") or {}).get("reason")
                if r:
                    reason = r
    except OSError:
        pass
    return reason, sid


def alive(jl):
    try:
        return time.time() - os.path.getmtime(jl) < STALE
    except OSError:
        return False


def kill_arm(arm):
    ws = os.path.realpath(ARMS[arm]["ws"])
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            cwd = os.readlink("/proc/%s/cwd" % pid)
        except OSError:
            continue
        if cwd.startswith(ws):
            try:
                with open("/proc/%s/cmdline" % pid, "rb") as f:
                    cmd = f.read().replace(b"\x00", b" ").decode(errors="replace")
            except OSError:
                continue
            if "opencode" in cmd and "run" in cmd:
                os.kill(int(pid), 9)


def launch(arm, sid=None):
    a = ARMS[arm]
    jl = os.path.join(RAW, "%s_ds_cal.jsonl" % arm)
    err = os.path.join(RAW, "%s_ds_cal_stderr.log" % arm)
    cmd = [OPENCODE, "run", "-m", a["model"], "--format", "json"]
    if sid:
        cmd += ["-s", sid, CONTINUE_MSG]
    else:
        with open(os.path.join(a["ws"], "PROMPT.md")) as f:
            cmd += [f.read()]
    env = dict(os.environ, ORACLE_RUN_ID=a["runid"])
    with open(jl, "a") as out, open(err, "a") as e:
        subprocess.Popen(cmd, cwd=a["ws"], env=env, stdout=out, stderr=e,
                         start_new_session=True)
    log("%s launched (resume=%s)" % (arm, sid or "fresh"))


def main():
    attempts = {a: 0 for a in ARMS}
    done = {a: False for a in ARMS}
    log("watcher started")
    while True:
        for arm in ARMS:
            if done[arm]:
                continue
            jl = os.path.join(RAW, "%s_ds_cal.jsonl" % arm)
            reason, sid = last_state(jl)
            if reason in DONE_REASONS:
                done[arm] = True
                log("%s COMPLETE (reason=%s)" % (arm, reason))
                continue
            if alive(jl):
                continue
            if attempts[arm] >= MAX_ATTEMPTS:
                done[arm] = True
                log("%s GAVE UP after %d attempts" % (arm, attempts[arm]))
                continue
            attempts[arm] += 1
            log("%s dead (attempt %d, reason=%s, sid=%s) — resuming"
                % (arm, attempts[arm], reason, sid))
            # kill only THIS arm's stuck opencode processes before
            # resuming: stacked resumes deadlock on the session DB
            # (observed 2026-08-25). Surgical: match on cwd, never on
            # the other arm's healthy session.
            kill_arm(arm)
            time.sleep(5)
            launch(arm, sid or None)
        if all(done.values()):
            log("all arms settled — watcher exiting")
            return
        time.sleep(POLL)


if __name__ == "__main__":
    main()
