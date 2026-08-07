#!/usr/bin/env bash
# Executes the FROZEN randomised schedule (schedule.json, seed 20260807) in order.
# Serial by design: parallel runs would contend for the emulator and confound cost.
set -u
C2=/media/sf_Projects/fcdd_lab/case02_predictability
LOG="$C2/ledger/drive.log"
mkdir -p "$C2/ledger"
say() { echo "$(date -Is) $*" | tee -a "$LOG"; }

TOTAL=$(python3 -c "import json;print(len(json.load(open('$C2/schedule.json'))))")
say "case02 START — $TOTAL runs from the frozen schedule"
i=0
python3 -c "
import json
for e in json.load(open('$C2/schedule.json')): print(e['bug'], e['arm'], e['run'])
" | while read BUG ARM K; do
  i=$((i+1))
  WS="$HOME/fcdd_arms/${BUG}_arm${ARM}_c2r${K}"
  RES="/media/sf_Projects/fcdd_lab/case01_spectrum_gambit/ledger/raw/arm${ARM}_${BUG}_c2r${K}_a1_result.json"
  if [ -f "$RES" ]; then say "[$i/$TOTAL] $BUG arm$ARM r$K — already done, skip"; continue; fi
  say "[$i/$TOTAL] $BUG arm$ARM r$K — start"
  bash "$C2/tools/run_case02.sh" "$ARM" "$BUG" "$K" >>"$LOG" 2>&1 \
    && say "[$i/$TOTAL] $BUG arm$ARM r$K — done" \
    || say "[$i/$TOTAL] $BUG arm$ARM r$K — FAILED (recorded, schedule continues)"
done
say "case02 COMPLETE"
