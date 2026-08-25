#!/usr/bin/env bash
# Case 04 — P4 calibration runner. One fresh run per arm, detached,
# time-boxed, results to ledger/raw. Excluded from inference by design
# (PREREGISTRATION §9 P4).
set -u
LAB=/media/sf_Projects/fcdd_lab/case04_coq_rust
RAW="$LAB/ledger/raw"
ARMS="$HOME/fcdd_c04_arms"
TOOLS="Bash,Read,Write,Edit,Glob,Grep,Task"
MODEL=claude-opus-5
TIMEOUT=21600   # 6h wall per calibration run
mkdir -p "$RAW" "$ARMS"

python3 "$LAB/tools/build_workspace.py" "$ARMS" --ledger "$LAB/ledger" || exit 1

for arm in armA armB; do
  WS="$ARMS/$arm"
  OUT="$RAW/${arm}_cal_a1_result.json"
  LOG="$RAW/${arm}_cal_stderr.log"
  rm -f "$OUT" "$LOG"
  echo "launching $arm (calibration) ..."
  ( cd "$WS" && ORACLE_RUN_ID="cal-$arm" \
      timeout "$TIMEOUT" "$(command -v claude)" -p "$(cat "$WS/PROMPT.md")" \
        --model "$MODEL" --effort max --output-format json \
        --allowedTools "$TOOLS" > "$OUT" 2>> "$LOG" ) &
  echo $! > "$RAW/${arm}_cal.pid"
done
echo "both calibration runs launched (see $RAW for pids)"
