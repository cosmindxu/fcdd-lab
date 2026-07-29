#!/usr/bin/env bash
# case01 arms driver — 7 bugs x 2 arms, pair-per-bug (A+B concurrent, pairs
# sequential so both arms of a bug share the same API weather). Detach me:
#   setsid nohup bash tools/run_arms.sh >> ledger/raw/arms_driver.log 2>&1 &
# The orchestrator assembles PROMPT.md blind (cat, never reads the reports).
set -u
CASE=/media/sf_Projects/fcdd_lab/case01_spectrum_gambit
WORK="$HOME/fcdd_arms"
RAW="$CASE/ledger/raw"
MODEL=claude-opus-5
EFFORT=max
TIMEOUT_S=7200                               # 2h wall cap per run -> DNF-timeout
TOOLS_A="Task,Bash,Read,Write,Edit,MultiEdit,Glob,Grep,TodoWrite"
TOOLS_B="$TOOLS_A,Skill"
CLAUDE_BIN="${CLAUDE_BIN:-$(command -v claude)}"
[ -n "$CLAUDE_BIN" ] || { echo "FATAL: claude not on PATH"; exit 1; }
BUGS="${BUGS:-bug01 bug02 bug03 bug04 bug05 bug06 bug07}"   # override to resume
TIMEOUT_S="${TIMEOUT_OVERRIDE:-$TIMEOUT_S}"
log() { echo "$(date -Is) $*"; }
mkdir -p "$WORK"
echo $$ > "$RAW/arms_driver.pid"   # REAL bash pid (the setsid wrapper's pid is useless for kills)

prep_ws() {                                   # $1=bug $2=arm
  local BUG=$1 ARM=$2 WS="$WORK/${1}_arm${2}"
  rm -rf "$WS"
  mkdir -p "$WS/variants"
  cp -r "$CASE/arms/harness"        "$WS/harness"
  cp -r "$CASE/arms/variants/$BUG"  "$WS/variants/$BUG"
  if [ "$ARM" = B ]; then
    cp -r "$CASE/step1_contract" "$WS/contract"
    # re-point the bridge at THIS workspace (mechanical; disclosed in ledger)
    sed -i "s|/media/sf_Projects/HC91_emulator/build/hc91emu|$WS/harness/build/hc91emu|g" "$WS/contract/bridge/emu.py"
    sed -i "s|/media/sf_Projects/HC91_emulator/roms/48.rom|$WS/harness/roms/48.rom|g"     "$WS/contract/bridge/emu.py"
    sed -i "s|/media/sf_Projects/HC91_emulator/chess/engine.inc|$WS/variants/$BUG/engine.inc|g" "$WS/contract/bridge/b7_findings.py"
  fi
  # neutralize any remaining outside-path signposts in the copies (blind, blanket)
  grep -rl --exclude='*.olean' --exclude='*.png' --exclude='*.sna' \
       "/media/sf_Projects" "$WS" 2>/dev/null \
    | xargs -r sed -i "s|/media/sf_Projects[A-Za-z0-9_/.-]*|EXTERNAL_PATH_REMOVED|g"
  { cat "$CASE/prompts/arm${ARM}_header.md"
    echo; echo "## The bug report"; echo
    cat "$CASE/bug_reports/${BUG}.md"
    echo
    cat "$CASE/prompts/arm_footer.md"
  } | sed "s/BUGNN/$BUG/g" > "$WS/PROMPT.md"
}

run_arm() {                                   # $1=bug $2=arm  (backgrounded)
  local BUG=$1 ARM=$2 WS="$WORK/${1}_arm${2}" TOOLS RC
  [ "$ARM" = A ] && TOOLS="$TOOLS_A" || TOOLS="$TOOLS_B"
  (
    cd "$WS" || exit 9
    timeout "$TIMEOUT_S" "$CLAUDE_BIN" -p "$(cat PROMPT.md)" \
        --model "$MODEL" --effort "$EFFORT" --output-format json \
        --allowedTools "$TOOLS" \
        > "$RAW/arm${ARM}_${BUG}_result.json" 2> "$RAW/arm${ARM}_${BUG}_stderr.log"
    RC=$?
    [ $RC -eq 124 ] && log "arm$ARM $BUG TIMEOUT->DNF (rc=124)" || log "arm$ARM $BUG exit rc=$RC"
  ) &
  echo $! > "$RAW/arm${ARM}_${BUG}.pid"
}

log "ARMS DRIVER START pid=$$ bugs='$BUGS' model=$MODEL effort=$EFFORT timeout=${TIMEOUT_S}s toolsA=$TOOLS_A toolsB=$TOOLS_B"
for BUG in $BUGS; do
  log "prep $BUG"
  prep_ws "$BUG" A
  prep_ws "$BUG" B
  log "launch pair $BUG (A+B concurrent)"
  run_arm "$BUG" A
  run_arm "$BUG" B
  wait
  log "pair $BUG done"
done
log "ALL ARMS DONE"
