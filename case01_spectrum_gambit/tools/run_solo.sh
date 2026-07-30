#!/usr/bin/env bash
# Generic solo (re)run of one arm on one bug, A4 no-cap semantics.
# Usage: run_solo.sh <A|B> <bugNN> [wait_pid]
#   wait_pid: optionally block until that pid exits before starting (load gating).
# Result: ledger/raw/arm<ARM>_<bug>_rerun_result.json; completion logs
# "pair <bug>-rerun done (arm<ARM> solo rc=N)" for the standing monitor.
set -u
ARM=$1; BUG=$2; GATE_PID="${3:-}"
CASE=/media/sf_Projects/fcdd_lab/case01_spectrum_gambit
WORK="$HOME/fcdd_arms"; RAW="$CASE/ledger/raw"
WS="$WORK/${BUG}_arm${ARM}"
CLAUDE_BIN="${CLAUDE_BIN:-$(command -v claude)}"
TOOLS="Task,Bash,Read,Write,Edit,MultiEdit,Glob,Grep,TodoWrite"
[ "$ARM" = B ] && TOOLS="$TOOLS,Skill"
log() { echo "$(date -Is) $*" >> "$RAW/arms_driver.log"; }

if [ -n "$GATE_PID" ]; then
  log "arm$ARM $BUG-rerun QUEUED behind pid $GATE_PID"
  while kill -0 "$GATE_PID" 2>/dev/null; do sleep 60; done
fi

[ -d "$WS" ] && mv "$WS" "${WS}_prev_$(date +%H%M)"
mkdir -p "$WS/variants"
cp -r "$CASE/arms/harness"          "$WS/harness"
cp -r "$CASE/arms/variants/$BUG"    "$WS/variants/$BUG"
if [ "$ARM" = B ]; then
  cp -r "$CASE/step1_contract" "$WS/contract"
  sed -i "s|/media/sf_Projects/HC91_emulator/build/hc91emu|$WS/harness/build/hc91emu|g" "$WS/contract/bridge/emu.py"
  sed -i "s|/media/sf_Projects/HC91_emulator/roms/48.rom|$WS/harness/roms/48.rom|g"     "$WS/contract/bridge/emu.py"
  sed -i "s|/media/sf_Projects/HC91_emulator/chess/engine.inc|$WS/variants/$BUG/engine.inc|g" "$WS/contract/bridge/b7_findings.py"
fi
grep -rl --exclude='*.olean' --exclude='*.png' --exclude='*.sna' \
     "/media/sf_Projects" "$WS" 2>/dev/null \
  | xargs -r sed -i "s|/media/sf_Projects[A-Za-z0-9_/.-]*|EXTERNAL_PATH_REMOVED|g"
{ cat "$CASE/prompts/arm${ARM}_header.md"
  echo; echo "## The bug report"; echo
  cat "$CASE/bug_reports/${BUG}.md"
  echo
  cat "$CASE/prompts/arm_footer.md"
} | sed "s/BUGNN/$BUG/g" > "$WS/PROMPT.md"

log "arm$ARM $BUG-rerun START (A4 no-cap, 8h backstop) pid=$$"
cd "$WS" || exit 9
timeout 28800 "$CLAUDE_BIN" -p "$(cat PROMPT.md)" \
    --model claude-opus-5 --effort max --output-format json \
    --allowedTools "$TOOLS" \
    > "$RAW/arm${ARM}_${BUG}_rerun_result.json" 2> "$RAW/arm${ARM}_${BUG}_rerun_stderr.log"
RC=$?
log "pair ${BUG}-rerun done (arm$ARM solo rc=$RC)"
