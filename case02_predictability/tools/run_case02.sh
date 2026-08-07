#!/usr/bin/env bash
# Case02 runner. Wraps case01's resilient runner, with two differences:
#   * Arm A now receives the pristine-derived characterisation suite (the
#     cost-matched oracle), so the confound of case01 3.2 is spent symmetrically.
#   * Result tag is c2r<k>, which is what tools/analyse_case02.py globs for.
# Usage: run_case02.sh <A|B> <bugNN> <k>
set -u
ARM=$1; BUG=$2; K=$3
C1=/media/sf_Projects/fcdd_lab/case01_spectrum_gambit
C2=/media/sf_Projects/fcdd_lab/case02_predictability
WORK="$HOME/fcdd_arms"; WS="$WORK/${BUG}_arm${ARM}_c2r${K}"
RAW="$C1/ledger/raw"
log() { echo "$(date -Is) [c02] $*" >> "$RAW/arms_driver.log"; }

if [ ! -d "$WS" ]; then
  mkdir -p "$WS/variants"
  cp -r "$C1/arms/harness"       "$WS/harness"
  cp -r "$C1/arms/variants/$BUG" "$WS/variants/$BUG"
  if [ "$ARM" = B ]; then
    cp -r "$C1/step1_contract" "$WS/contract"
    sed -i "s|/media/sf_Projects/HC91_emulator/build/hc91emu|$WS/harness/build/hc91emu|g" "$WS/contract/bridge/emu.py" 2>/dev/null
    sed -i "s|/media/sf_Projects/HC91_emulator/roms/48.rom|$WS/harness/roms/48.rom|g"     "$WS/contract/bridge/emu.py" 2>/dev/null
    sed -i "s|/media/sf_Projects/HC91_emulator/chess/engine.inc|$WS/variants/$BUG/engine.inc|g" "$WS/contract/bridge/b7_findings.py" 2>/dev/null
  else
    cp -r "$C2/armA_characterisation" "$WS/characterisation"
  fi
  grep -rl --exclude='*.olean' --exclude='*.png' --exclude='*.sna' --exclude='*.tap' \
       "/media/sf_Projects" "$WS" 2>/dev/null \
    | xargs -r sed -i "s|/media/sf_Projects[A-Za-z0-9_/.-]*|EXTERNAL_PATH_REMOVED|g"
  { cat "$C2/prompts_arm${ARM}_header.md"
    echo; echo "## The bug report"; echo
    cat "$C1/bug_reports/${BUG}.md"; echo
    cat "$C2/prompts_arm_footer.md"
  } | sed "s/BUGNN/$BUG/g" > "$WS/PROMPT.md"
  log "arm$ARM $BUG r$K: workspace built ($WS)"
fi
RESULT_TAG="c2r${K}" MAX_ATTEMPTS="${MAX_ATTEMPTS:-6}" exec bash "$C1/tools/run_resilient.sh" "$ARM" "$BUG"
