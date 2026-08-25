#!/usr/bin/env bash
# Case 04 — one scored cell (systemd unit). Launch opencode, wait,
# classify, resume on death (process-liveness is the death criterion —
# the calibration watcher's mtime heuristic murdered slow sessions).
# Usage: cell_unit.sh <tag> <model> <workspace> <result.jsonl> [--dry]
set -u
TAG=$1; MODEL=$2; WS=$3; OUT=$4; DRY=${5:-}
RAW=/media/sf_Projects/fcdd_lab/case04_coq_rust/ledger/raw
RUNNER="$HOME/.opencode/bin/opencode"
MAX_ATTEMPTS=3
TIMEOUT=21600
LOG="$RAW/drive.log"

log(){ echo "$(date) $TAG $*" >> "$LOG"; }

[ -n "$DRY" ] && { log "DRY ($MODEL)"; exit 0; }

PREV_SID=""
for attempt in $(seq 1 $MAX_ATTEMPTS); do
  log "attempt $attempt ($MODEL)"
  if [ -n "$PREV_SID" ]; then
    SET=(-s "$PREV_SID")
    MSG="Your session died mid-work. Continue the task from where you stopped: re-read the workspace state, keep working per PROMPT.md, and proceed to the definition of done. Do not restart from scratch."
  else
    SET=()
    MSG="$(cat "$WS/PROMPT.md")"
  fi
  ( cd "$WS" && ORACLE_RUN_ID="$TAG" timeout $TIMEOUT \
      "$RUNNER" run -m "$MODEL" --format json "${SET[@]}" "$MSG" \
      >> "$OUT" 2>> "$RAW/${TAG}_stderr.log" )
  read -r STATUS SID LASTTEXT <<<"$(python3 - "$OUT" <<'PYEOF'
import json, sys
try:
    lines = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
except Exception:
    print("DEAD - ''"); sys.exit(0)
sids = [p.get("sessionID") for p in lines if p.get("sessionID")]
texts = [p.get("part", {}).get("text", "") for p in lines
         if p.get("type") == "text" and p.get("part", {}).get("text")]
finishes = [p.get("part", {}).get("reason") for p in lines
            if p.get("type") == "step_finish" and p.get("part", {}).get("reason")]
last = texts[-1][:160] if texts else ""
if finishes and finishes[-1] in ("stop", "end_turn") and texts:
    print("COMPLETE %s %s" % (sids[-1] if sids else "", last.replace("'", "")))
else:
    print("DEAD %s ''" % (sids[-1] if sids else ""))
PYEOF
)"
  if [ "$STATUS" = "COMPLETE" ]; then
    log "COMPLETE attempt $attempt: $LASTTEXT"
    exit 0
  fi
  PREV_SID="$SID"
  log "dead (attempt $attempt), resume=$PREV_SID"
done
log "GAVE UP after $MAX_ATTEMPTS attempts"
exit 1
