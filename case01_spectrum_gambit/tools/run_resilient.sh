#!/usr/bin/env bash
# A8/A9 resilient runner — survives BOTH failure classes seen in this case:
#   (1) API incidents (11:39), (2) subscription session-limit exhaustion (15:02+).
#
# Usage: run_resilient.sh <A|B> <bugNN>
# Env:   RESULT_TAG (default v3), MAX_ATTEMPTS (default 6), PROBE_GAP (default 900)
#
# How it survives an interruption:
#   * the run is pinned to a DETERMINISTIC --session-id (uuid5 of arm+bug+tag),
#     so a killed run is resumed with full conversation context via --resume;
#   * the workspace is NEVER rebuilt between attempts — edits, tests and
#     STATE.md persist on disk, so even a context-less cold start continues;
#   * between attempts it probes the API and waits for the window to reset.
# Each attempt's result JSON is kept (…_a1, _a2 …); the last one is canonical.
# ledger note: attempts are ONE measurement — costs are SUMMED across attempts.
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
SID=$(python3 -c "import uuid;print(uuid.uuid5(uuid.NAMESPACE_URL,'fcdd/$ARM/$BUG/$TAG'))")
log() { echo "$(date -Is) [res] $*" >> "$RAW/arms_driver.log"; }

probe_ok() { cd "$SCRATCH" || return 1
  timeout 120 "$CLAUDE_BIN" -p "Reply with exactly: ok" --model claude-opus-5 \
    --output-format json 2>/dev/null | python3 -c "import json,sys
try: sys.exit(0 if not json.load(sys.stdin).get('is_error') else 1)
except Exception: sys.exit(1)"; }

wait_for_window() { local n=0
  until probe_ok; do n=$((n+1))
    log "arm$ARM $BUG: API/quota unavailable (probe $n) — sleeping ${PROBE_GAP}s"
    sleep "$PROBE_GAP"; done
  [ $n -gt 0 ] && log "arm$ARM $BUG: availability RESTORED after $n probes"; return 0; }

# ---- workspace: build ONCE, never wipe between attempts --------------------
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
  log "arm$ARM $BUG: workspace built ($WS), session $SID"
fi

RESUME_PROMPT='Your previous session was interrupted mid-task by an
infrastructure limit — not by anything you did. The workspace on disk is
exactly as you left it. Read STATE.md (if you wrote one) plus your own
edits, re-establish where you were, and CONTINUE to completion from there.
Do not restart from scratch and do not redo work that is already done.'

cd "$WS" || exit 9
for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
  wait_for_window
  OUT="$RAW/arm${ARM}_${BUG}_${TAG}_a${attempt}_result.json"
  if [ "$attempt" -eq 1 ]; then
    log "arm$ARM $BUG attempt $attempt/$MAX_ATTEMPTS: FRESH (session $SID)"
    timeout 28800 "$CLAUDE_BIN" -p "$(cat PROMPT.md)" --session-id "$SID" \
        --model claude-opus-5 --effort max --output-format json \
        --allowedTools "$TOOLS" > "$OUT" 2>> "$RAW/arm${ARM}_${BUG}_${TAG}_stderr.log"
  else
    log "arm$ARM $BUG attempt $attempt/$MAX_ATTEMPTS: RESUME session $SID"
    timeout 28800 "$CLAUDE_BIN" -p "$RESUME_PROMPT" --resume "$SID" \
        --model claude-opus-5 --effort max --output-format json \
        --allowedTools "$TOOLS" > "$OUT" 2>> "$RAW/arm${ARM}_${BUG}_${TAG}_stderr.log"
  fi
  RC=$?
  ERR=$(python3 -c "
import json,sys
try: print('1' if json.load(open('$OUT')).get('is_error') else '0')
except Exception: print('1')")
  if [ "$RC" -eq 0 ] && [ "$ERR" = "0" ]; then
    log "pair ${BUG}-${TAG} done (arm$ARM COMPLETE on attempt $attempt)"
    exit 0
  fi
  log "arm$ARM $BUG attempt $attempt interrupted (rc=$RC err=$ERR) — will resume"
done
log "pair ${BUG}-${TAG} done (arm$ARM EXHAUSTED $MAX_ATTEMPTS attempts)"
exit 1
