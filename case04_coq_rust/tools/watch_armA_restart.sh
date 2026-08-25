#!/usr/bin/env bash
# Case 04 — armA calibration watcher (operator instruction 2026-08-24:
# Claude token credit nearly exhausted; if the armA run dies, wait 2h10m
# then restart it). Resumes the recorded session id when one exists, else
# restarts fresh on the dirty workspace. Exits on a clean completion
# (is_error false). Log: ledger/raw/armA_watch.log
set -u
RAW=/media/sf_Projects/fcdd_lab/case04_coq_rust/ledger/raw
WS=/home/xcos/fcdd_c04_arms/armA
WAIT=18000         # 5h, per operator correction 2026-08-24 (token reset ~02:35)
MAX=5
NEXT=2             # attempt a2 is the one currently running
LOG=$RAW/armA_watch.log

for i in $(seq 1 $MAX); do
  CUR=$RAW/armA_cal_a${NEXT}_result.json
  # wait for completion: file non-empty, OR silent death (no claude -p
  # process alive AND file still empty AND untouched for 10 min — e.g. a
  # usage-limit kill that emitted no record, as already happened twice)
  while [ ! -s "$CUR" ]; do
    sleep 60
    if ! pgrep -f "claud[e] -p" >/dev/null 2>&1; then
      AGE=$(( $(date +%s) - $(stat -c %Y "$CUR") ))
      [ "$AGE" -gt 600 ] && break
    fi
  done
  ERR=$(python3 -c "
import json
try:
    d = json.load(open('$CUR'))
    print(int(bool(d.get('is_error'))))
except Exception:
    print(1)" 2>/dev/null)
  if [ "$ERR" = "0" ]; then
    echo "$(date) armA attempt a$NEXT completed cleanly — watcher done" >> "$LOG"
    exit 0
  fi
  SID=$(python3 -c "
import json
try: print(json.load(open('$CUR')).get('session_id') or '')
except Exception: print('')" 2>/dev/null)
  echo "$(date) armA attempt a$NEXT died (err=$ERR resume=${SID:-none}); sleeping ${WAIT}s" >> "$LOG"
  sleep "$WAIT"
  NEXT=$((NEXT+1))
  OUT=$RAW/armA_cal_a${NEXT}_result.json
  if [ -n "$SID" ]; then
    ( cd "$WS" && ORACLE_RUN_ID=cal-armA setsid nohup timeout 21600 claude -p \
      "The session lost its connection or hit a usage limit mid-work. Continue the task from where you stopped: re-read the workspace state, keep working per PROMPT.md, and proceed to the definition of done. Do not restart from scratch." \
      --resume "$SID" --model claude-opus-5 --effort max --output-format json \
      --allowedTools "Bash,Read,Write,Edit,Glob,Grep,Task" \
      > "$OUT" 2>> $RAW/armA_cal_stderr.log ) >/dev/null 2>&1 &
  else
    ( cd "$WS" && ORACLE_RUN_ID=cal-armA setsid nohup timeout 21600 claude -p \
      "Your previous session was killed by infrastructure and left this workspace with partial work. Read PROMPT.md and the workspace state, continue the task from where it stands, and proceed to the definition of done. Do not restart from scratch." \
      --model claude-opus-5 --effort max --output-format json \
      --allowedTools "Bash,Read,Write,Edit,Glob,Grep,Task" \
      > "$OUT" 2>> $RAW/armA_cal_stderr.log ) >/dev/null 2>&1 &
  fi
  echo "$(date) armA restarted as attempt a$NEXT (pid $!)" >> "$LOG"
done
echo "$(date) armA watcher gave up after $MAX attempts" >> "$LOG"
