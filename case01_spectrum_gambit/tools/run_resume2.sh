#!/usr/bin/env bash
# Post-outage resume (2026-07-30 12:40): serial v2 chain for everything the
# 11:39 mass api_error killed. Driver relaunch for bug06/07 runs separately.
set -u
cd /media/sf_Projects/fcdd_lab/case01_spectrum_gambit
export RESULT_TAG=rerunv2
echo "$(date -Is) RESUME2 START (serial: B05 A02 A03 A04 B02 B03 B04 B01 A01)" >> ledger/raw/arms_driver.log
bash tools/run_solo.sh B bug05
bash tools/run_solo.sh A bug02
bash tools/run_solo.sh A bug03
bash tools/run_solo.sh A bug04
bash tools/run_solo.sh B bug02
bash tools/run_solo.sh B bug03
bash tools/run_solo.sh B bug04
bash tools/run_solo.sh B bug01
bash tools/run_solo.sh A bug01
echo "$(date -Is) RESUME2 DONE" >> ledger/raw/arms_driver.log
