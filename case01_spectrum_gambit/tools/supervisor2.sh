#!/usr/bin/env bash
# A9 supervisor — serial, resilient queue on top of run_resilient.sh.
# Each queue item runs to completion across as many interruptions as it takes
# (resume + wait-for-window inside run_resilient.sh). Serial by design: under a
# quota, concurrency multiplies casualties without buying throughput.
set -u
CASE=/media/sf_Projects/fcdd_lab/case01_spectrum_gambit
RAW="$CASE/ledger/raw"
QUEUE="${QUEUE:-B:bug05 A:bug06 B:bug06 A:bug07 B:bug07}"
GATE_PID="${GATE_PID:-}"
log() { echo "$(date -Is) [sup2] $*" >> "$RAW/arms_driver.log"; }

if [ -n "$GATE_PID" ]; then
  log "waiting for in-flight pid $GATE_PID before taking over"
  while kill -0 "$GATE_PID" 2>/dev/null; do sleep 60; done
  log "pid $GATE_PID finished — taking over"
fi

log "SUPERVISOR2 START (resilient/serial) queue='$QUEUE'"
for item in $QUEUE; do
  ARM="${item%%:*}"; BUG="${item##*:}"
  log "queue -> arm$ARM $BUG"
  RESULT_TAG=v3 MAX_ATTEMPTS=8 bash "$CASE/tools/run_resilient.sh" "$ARM" "$BUG"
done
log "SUPERVISOR2 QUEUE DRAINED"
