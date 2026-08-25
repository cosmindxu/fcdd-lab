#!/usr/bin/env bash
# Case 04 — scored-phase runner (opencode). Executes the frozen schedule:
# per cell, a fresh workspace, pinned model, oracle run-id = cell tag,
# opencode run headless, resume on infrastructure death (case02 pattern),
# every attempt timestamped to drive.log (C6 gap logging).
#
# Usage: run_scored.sh <schedule.json> [--dry]
set -u
LAB=/media/sf_Projects/fcdd_lab/case04_coq_rust
RAW="$LAB/ledger/raw"
BASE="$HOME/fcdd_c04_scored"
MAX_ATTEMPTS=3
TIMEOUT=21600
RUNNER="$HOME/.opencode/bin/opencode"
mkdir -p "$RAW" "$BASE"

SCHED=${1:?usage: run_scored.sh <schedule.json> [--dry]}
DRY=${2:-}
touch "$RAW/drive.log"

while read -r cell tag model arm; do
  [ -n "$tag" ] || continue
  WS="$BASE/$tag"
  python3 "$LAB/tools/build_workspace.py" "$WS" --ledger "$LAB/ledger" >/dev/null 2>&1 || {
    echo "$(date) $tag WORKSPACE BUILD FAILED" >> "$RAW/drive.log"; continue; }
  if [ -n "$DRY" ]; then echo "$(date) DRY $tag ($model)"; continue; fi
  OUT="$RAW/${tag}.jsonl"
  PREV_SID=""
  for attempt in $(seq 1 $MAX_ATTEMPTS); do
    echo "$(date) $tag attempt $attempt ($model)" >> "$RAW/drive.log"
    if [ -n "$PREV_SID" ]; then
      SET=(-s "$PREV_SID")
      MSG="Your session died mid-work. Continue the task from where you stopped: re-read the workspace state, keep working per PROMPT.md, and proceed to the definition of done. Do not restart from scratch."
    else
      SET=()
      MSG="$(cat "$WS/PROMPT.md")"
    fi
    ( cd "$WS" && ORACLE_RUN_ID="$tag" timeout $TIMEOUT \
        "$RUNNER" run -m "$model" --format json "${SET[@]}" "$MSG" \
        > "$OUT" 2>> "$RAW/${tag}_stderr.log" )
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
      echo "$(date) $tag COMPLETE attempt $attempt: $LASTTEXT" >> "$RAW/drive.log"
      break
    fi
    PREV_SID="$SID"
    echo "$(date) $tag dead (attempt $attempt), resume=$PREV_SID" >> "$RAW/drive.log"
  done
done < <(python3 - "$SCHED" <<'EOF'
import json, sys
sched = json.load(open(sys.argv[1]))
for c in sched["cells"]:
    print("%d %s %s %s" % (c["cell"], c["tag"], c["model"], c["arm"]))
EOF
)
echo "$(date) schedule done" >> "$RAW/drive.log"
