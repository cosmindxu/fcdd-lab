#!/usr/bin/env bash
# A4 amendment: solo fresh rerun of armA:bug01 to completion (no cost cap,
# 8h hang-backstop). Result lands as armA_bug01_rerun_result.json; completion
# is logged as "pair bug01-rerun done" so the standing monitor notifies.
set -u
CASE=/media/sf_Projects/fcdd_lab/case01_spectrum_gambit
WORK="$HOME/fcdd_arms"
RAW="$CASE/ledger/raw"
WS="$WORK/bug01_armA"
CLAUDE_BIN="${CLAUDE_BIN:-$(command -v claude)}"
TOOLS_A="Task,Bash,Read,Write,Edit,MultiEdit,Glob,Grep,TodoWrite"
log() { echo "$(date -Is) $*" >> "$RAW/arms_driver.log"; }

[ -d "$WS" ] && mv "$WS" "${WS}_try1_$(date +%H%M)"   # preserve attempt-1 evidence
mkdir -p "$WS/variants"
cp -r "$CASE/arms/harness"           "$WS/harness"
cp -r "$CASE/arms/variants/bug01"    "$WS/variants/bug01"
grep -rl --exclude='*.olean' --exclude='*.png' --exclude='*.sna' \
     "/media/sf_Projects" "$WS" 2>/dev/null \
  | xargs -r sed -i "s|/media/sf_Projects[A-Za-z0-9_/.-]*|EXTERNAL_PATH_REMOVED|g"
{ cat "$CASE/prompts/armA_header.md"
  echo; echo "## The bug report"; echo
  cat "$CASE/bug_reports/bug01.md"
  echo
  cat "$CASE/prompts/arm_footer.md"
} | sed "s/BUGNN/bug01/g" > "$WS/PROMPT.md"

log "armA bug01-rerun START (A4 no-cap, 8h backstop) pid=$$"
cd "$WS" || exit 9
timeout 28800 "$CLAUDE_BIN" -p "$(cat PROMPT.md)" \
    --model claude-opus-5 --effort max --output-format json \
    --allowedTools "$TOOLS_A" \
    > "$RAW/armA_bug01_rerun_result.json" 2> "$RAW/armA_bug01_rerun_stderr.log"
RC=$?
log "pair bug01-rerun done (armA solo rc=$RC)"
