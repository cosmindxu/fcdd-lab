#!/usr/bin/env bash
# Executes the FROZEN randomised schedule (schedule.json, seed 20260807) in order.
# Serial by design: parallel runs would contend for the emulator and confound cost.
set -u
C2=/media/sf_Projects/fcdd_lab/case02_predictability
LOG="$C2/ledger/drive.log"
mkdir -p "$C2/ledger"
say() { echo "$(date -Is) $*" | tee -a "$LOG"; }

RAW=/media/sf_Projects/fcdd_lab/case01_spectrum_gambit/ledger/raw

# A cell is DONE iff some attempt file parses as JSON with is_error false —
# i.e. exactly the condition under which run_resilient.sh exits 0.
#
# Mere existence of arm*_a1_result.json is NOT completion: run_resilient
# creates that file empty by redirect at attempt start, so a crashed or
# still-running cell has one. Skipping on existence would silently drop a
# cell from a design that requires all 56 (PREREGISTRATION §6). Conversely
# a cell that succeeded on attempt 2 writes _a2_, so an _a1_-only check
# would re-run a completed cell. Both directions are wrong; glob the
# attempts and ask the JSON.
cell_done() {   # $1=arm $2=bug $3=run
  python3 - "$RAW" "$1" "$2" "$3" <<'PY'
import glob, json, sys
raw, arm, bug, k = sys.argv[1:5]
for f in glob.glob(f"{raw}/arm{arm}_{bug}_c2r{k}_a*_result.json"):
    try:
        if not json.load(open(f)).get('is_error'):
            sys.exit(0)
    except Exception:
        pass
sys.exit(1)
PY
}

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
  if cell_done "$ARM" "$BUG" "$K"; then
    say "[$i/$TOTAL] $BUG arm$ARM r$K — already done, skip"; continue
  fi
  # A previous aborted attempt leaves a dirty workspace; a fresh start on it
  # would inherit another agent's partial edits. run_resilient only builds the
  # workspace when absent, so clear it and let it rebuild pristine.
  WS="$HOME/fcdd_arms/${BUG}_arm${ARM}_c2r${K}"
  if [ -d "$WS" ]; then say "[$i/$TOTAL] $BUG arm$ARM r$K — clearing dirty workspace from an aborted attempt"; rm -rf "$WS"; fi
  say "[$i/$TOTAL] $BUG arm$ARM r$K — start"
  bash "$C2/tools/run_case02.sh" "$ARM" "$BUG" "$K" >>"$LOG" 2>&1 </dev/null \
    && say "[$i/$TOTAL] $BUG arm$ARM r$K — done" \
    || say "[$i/$TOTAL] $BUG arm$ARM r$K — FAILED (recorded, schedule continues)"
done
say "case02 COMPLETE"
