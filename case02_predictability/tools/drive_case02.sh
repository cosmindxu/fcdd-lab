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
# Read the whole schedule into an array FIRST. Piping it into `while read` let
# the model call inside the loop consume the pipe's stdin and swallow the
# remaining 55 lines: the loop exited after one run and logged COMPLETE.
# The `</dev/null` on the run is the belt to that braces.
mapfile -t SCHED < <(python3 -c "
import json
for e in json.load(open('$C2/schedule.json')): print(e['bug'], e['arm'], e['run'])
")
say "schedule loaded: ${#SCHED[@]} entries"
for LINE in "${SCHED[@]}"; do
  set -- $LINE; BUG=$1; ARM=$2; K=$3
  i=$((i+1))
  RES="/media/sf_Projects/fcdd_lab/case01_spectrum_gambit/ledger/raw/arm${ARM}_${BUG}_c2r${K}_a1_result.json"
  if [ -f "$RES" ]; then say "[$i/$TOTAL] $BUG arm$ARM r$K — already done, skip"; continue; fi
  say "[$i/$TOTAL] $BUG arm$ARM r$K — start"
  bash "$C2/tools/run_case02.sh" "$ARM" "$BUG" "$K" >>"$LOG" 2>&1 </dev/null \
    && say "[$i/$TOTAL] $BUG arm$ARM r$K — done" \
    || say "[$i/$TOTAL] $BUG arm$ARM r$K — FAILED (recorded, schedule continues)"
done
say "case02 COMPLETE"
