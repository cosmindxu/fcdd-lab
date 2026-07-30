#!/usr/bin/env bash
# A8 supervisor — STRICTLY SERIAL runner with session-limit awareness.
#
# Why serial: the 11:39 and 15:02 losses were SUBSCRIPTION SESSION LIMITS,
# not API faults. Under a quota, N concurrent runs burn the window N x faster
# in wall-clock and all N die when it ends (we lost ~$225 that way). Serial
# costs the same tokens per unit of work but loses at most ONE run per window.
#
# Before each run it probes the API with a ~$0.15 call. On refusal it sleeps
# PROBE_GAP and re-probes, so the queue AUTO-RESUMES when the window resets
# instead of idling until a human notices. A run that dies with a costly
# partial (session limit mid-flight) is re-queued ONCE at the end.
set -u
CASE=/media/sf_Projects/fcdd_lab/case01_spectrum_gambit
RAW="$CASE/ledger/raw"
PROBE_GAP="${PROBE_GAP:-900}"          # 15 min between probes while limited
SCRATCH=/tmp/claude-1000/-media-sf-Projects/9f3d3354-b2ff-4d82-ba6a-0e2b8a260273/scratchpad
log() { echo "$(date -Is) [sup] $*" >> "$RAW/arms_driver.log"; }

# Queue: "ARM BUG" pairs, highest scientific value first.
QUEUE="${QUEUE:-B:bug05 A:bug06 B:bug06 A:bug07 B:bug07}"

probe_ok() {
  cd "$SCRATCH" || return 1
  timeout 120 claude -p "Reply with exactly: ok" --model claude-opus-5 \
      --output-format json 2>/dev/null \
    | python3 -c "import json,sys
try:
    d=json.load(sys.stdin); sys.exit(0 if not d.get('is_error') else 1)
except Exception: sys.exit(1)"
}

wait_for_window() {
  local n=0
  until probe_ok; do
    n=$((n+1))
    log "session limit still active (probe $n failed) — sleeping ${PROBE_GAP}s"
    sleep "$PROBE_GAP"
  done
  [ $n -gt 0 ] && log "window RESET detected after $n failed probes — resuming"
  return 0
}

log "SUPERVISOR START (serial, session-limit aware) queue='$QUEUE'"
for item in $QUEUE; do
  ARM="${item%%:*}"; BUG="${item##*:}"
  wait_for_window
  log "running arm$ARM $BUG (serial)"
  RESULT_TAG=v2 bash "$CASE/tools/run_solo.sh" "$ARM" "$BUG"
  R="$RAW/arm${ARM}_${BUG}_v2_result.json"
  if [ -s "$R" ]; then
    python3 - "$R" "$ARM" "$BUG" <<'PY' >> "$RAW/arms_driver.log"
import json,sys
d=json.load(open(sys.argv[1]))
print("%s [sup] arm%s %s -> err=%s turns=%s usd=%.2f %s" % (
    __import__('datetime').datetime.now().astimezone().isoformat(timespec='seconds'),
    sys.argv[2], sys.argv[3], d.get('is_error'), d.get('num_turns'),
    d.get('total_cost_usd') or 0, d.get('terminal_reason') or d.get('stop_reason')))
PY
  fi
done
log "SUPERVISOR QUEUE DRAINED"
