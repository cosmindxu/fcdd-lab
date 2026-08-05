#!/usr/bin/env bash
# Rule-5 replication of bug01 (the cell whose arm gap was 10.8%, below the 30%
# trigger, and whose two existing measurements differ 5.1x: $8.66 with one
# reviewer under the unbounded rule, $44.27 with three under the bounded one).
#
# Two additional runs per arm -> k=3 per arm under the FINAL (v4) prompt.
# Serial, resilient, same runner as every other measured cell.
set -u
CASE=/media/sf_Projects/fcdd_lab/case01_spectrum_gambit
log() { echo "$(date -Is) [rep] $*" >> "$CASE/ledger/raw/arms_driver.log"; }

log "BUG01 REPLICATION START (rule 5): A r2, A r3, B r2, B r3"
for spec in "A r2" "A r3" "B r2" "B r3"; do
  set -- $spec
  RESULT_TAG="v4$2" MAX_ATTEMPTS=8 bash "$CASE/tools/run_resilient.sh" "$1" bug01
done
log "BUG01 REPLICATION DONE"
