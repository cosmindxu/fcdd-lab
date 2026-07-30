#!/usr/bin/env bash
# A9 resilient runner (v2 — fixes the 20:19 spin incident).
#
# Survives BOTH failure classes seen in this case:
#   (1) API incidents (11:39), (2) subscription session-limit exhaustion (15:02+).
#
# Lessons encoded after the first version failed:
#   * `--session-id <uuid>` does NOT bind in this CLI — the returned session_id
#     differs, so resuming by our own uuid always said "No conversation found".
#     => we resume by the REAL session_id parsed from the previous attempt's
#        result JSON.
#   * A deterministic error (instant, ~$0 cost) is NOT an interruption. Retrying
#     it burned 8 attempts in 15s. => classify before retrying, and back off.
#
# Usage: run_resilient.sh <A|B> <bugNN>
# Env:   RESULT_TAG (default v3) MAX_ATTEMPTS (6) PROBE_GAP (900) DRY (unset)
set -u
ARM=$1; BUG=$2
TAG="${RESULT_TAG:-v3}"; MAX_ATTEMPTS="${MAX_ATTEMPTS:-6}"; PROBE_GAP="${PROBE_GAP:-900}"
CASE=/media/sf_Projects/fcdd_lab/case01_spectrum_gambit
WORK="$HOME/fcdd_arms"; RAW="$CASE/ledger/raw"
WS="$WORK/${BUG}_arm${ARM}_${TAG}"
SCRATCH=/tmp/claude-1000/-media-sf-Projects/9f3d3354-b2ff-4d82-ba6a-0e2b8a260273/scratchpad
CLAUDE_BIN="${CLAUDE_BIN:-$(command -v claude)}"
TOOLS="Task,Bash,Read,Write,Edit,MultiEdit,Glob,Grep,TodoWrite"
[ "$ARM" = B ] && TOOLS="$TOOLS,Skill"
log() { echo "$(date -Is) [res] $*" >> "$RAW/arms_driver.log"; }

probe_ok() { ( cd "$SCRATCH" || exit 1
  timeout 120 "$CLAUDE_BIN" -p "Reply with exactly: ok" --model claude-opus-5 \
    --output-format json 2>/dev/null | python3 -c "import json,sys
try: sys.exit(0 if not json.load(sys.stdin).get('is_error') else 1)
except Exception: sys.exit(1)" ); }   # SUBSHELL: a cd here must not follow the caller

wait_for_window() { local n=0
  until probe_ok; do n=$((n+1))
    log "arm$ARM $BUG: unavailable (probe $n) — sleeping ${PROBE_GAP}s"
    sleep "$PROBE_GAP"; done
  [ $n -gt 0 ] && log "arm$ARM $BUG: availability RESTORED after $n probes"; return 0; }

# ---- workspace: built ONCE, never wiped between attempts -------------------
if [ ! -d "$WS" ]; then
  mkdir -p "$WS/variants"
  cp -r "$CASE/arms/harness"       "$WS/harness"
  cp -r "$CASE/arms/variants/$BUG" "$WS/variants/$BUG"
  if [ "$ARM" = B ]; then
    cp -r "$CASE/step1_contract" "$WS/contract"
    sed -i "s|/media/sf_Projects/HC91_emulator/build/hc91emu|$WS/harness/build/hc91emu|g" "$WS/contract/bridge/emu.py"
    sed -i "s|/media/sf_Projects/HC91_emulator/roms/48.rom|$WS/harness/roms/48.rom|g"     "$WS/contract/bridge/emu.py"
    sed -i "s|/media/sf_Projects/HC91_emulator/chess/engine.inc|$WS/variants/$BUG/engine.inc|g" "$WS/contract/bridge/b7_findings.py"
  fi
  grep -rl --exclude='*.olean' --exclude='*.png' --exclude='*.sna' "/media/sf_Projects" "$WS" 2>/dev/null \
    | xargs -r sed -i "s|/media/sf_Projects[A-Za-z0-9_/.-]*|EXTERNAL_PATH_REMOVED|g"
  { cat "$CASE/prompts/arm${ARM}_header.md"
    echo; echo "## The bug report"; echo
    cat "$CASE/bug_reports/${BUG}.md"; echo
    cat "$CASE/prompts/arm_footer.md"
  } | sed "s/BUGNN/$BUG/g" > "$WS/PROMPT.md"
  log "arm$ARM $BUG: workspace built ($WS)"
fi
# HARD GUARD: never invoke with an empty prompt (attempt-1 failure mode).
if [ ! -s "$WS/PROMPT.md" ]; then
  log "arm$ARM $BUG: FATAL PROMPT.md missing/empty — aborting run"; exit 2
fi

RESUME_PROMPT='Your previous session was interrupted mid-task by an
infrastructure limit — not by anything you did. The workspace on disk is
exactly as you left it. Read STATE.md (if you wrote one) plus your own
edits, re-establish where you were, and CONTINUE to completion from there.
Do not restart from scratch and do not redo work that is already done.'

cd "$WS" || exit 9
PREV_SID=""; BACKOFF=60
for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
  [ -n "${DRY:-}" ] || wait_for_window
  OUT="$RAW/arm${ARM}_${BUG}_${TAG}_a${attempt}_result.json"
  if [ -n "$PREV_SID" ]; then
    log "arm$ARM $BUG attempt $attempt/$MAX_ATTEMPTS: RESUME real session $PREV_SID"
    SET=(-p "$RESUME_PROMPT" --resume "$PREV_SID")
  else
    log "arm$ARM $BUG attempt $attempt/$MAX_ATTEMPTS: FRESH start"
    SET=(-p "$(cat "$WS/PROMPT.md")")
  fi
  if [ -n "${DRY:-}" ]; then echo "DRY: ${SET[0]} ${SET[1]:0:40}… resume=${PREV_SID:-none}"; continue; fi
  START=$(date +%s)
  timeout 28800 "$CLAUDE_BIN" "${SET[@]}" \
      --model claude-opus-5 --effort max --output-format json \
      --allowedTools "$TOOLS" > "$OUT" 2>> "$RAW/arm${ARM}_${BUG}_${TAG}_stderr.log"
  RC=$?; ELAPSED=$(( $(date +%s) - START ))
  # classify: err / cost / real session id
  read -r ERR COST SID <<<"$(python3 -c "
import json
try:
    d=json.load(open('$OUT'))
    print(int(bool(d.get('is_error'))), '%.4f'%(d.get('total_cost_usd') or 0), d.get('session_id') or '')
except Exception:
    print(1, '0.0000', '')")"
  [ -n "$SID" ] && PREV_SID="$SID"
  if [ "$RC" -eq 0 ] && [ "$ERR" = "0" ]; then
    log "pair ${BUG}-${TAG} done (arm$ARM COMPLETE attempt $attempt, \$$COST, ${ELAPSED}s)"
    exit 0
  fi
  # A deterministic failure is instant and free — do NOT spin on it.
  if [ "$ELAPSED" -lt 120 ] && [ "$(python3 -c "print(1 if float('$COST')<0.5 else 0)")" = "1" ]; then
    log "arm$ARM $BUG attempt $attempt: INSTANT/\$0 failure (rc=$RC, ${ELAPSED}s) — deterministic, not an interruption"
    if [ "$attempt" -ge 2 ]; then
      log "pair ${BUG}-${TAG} done (arm$ARM ABORTED — deterministic failure twice, needs a human)"
      exit 3
    fi
    sleep "$BACKOFF"; BACKOFF=$((BACKOFF*2)); continue
  fi
  log "arm$ARM $BUG attempt $attempt: interrupted after ${ELAPSED}s (\$$COST) — will resume from $PREV_SID"
  sleep 60
done
log "pair ${BUG}-${TAG} done (arm$ARM EXHAUSTED $MAX_ATTEMPTS attempts)"
exit 1
