#!/usr/bin/env bash
# A7: serial v2 rerun chain for all prompt-v1 runs (operator directive
# 2026-07-30). One run at a time, cheap-first, B01 late, A01 last and
# gated behind the still-running v1 solo (pid arg). v1 artifacts are
# preserved (_prev workspaces, distinct result names).
set -u
cd /media/sf_Projects/fcdd_lab/case01_spectrum_gambit
export RESULT_TAG=rerunv2
echo "$(date -Is) V2-REQUEUE START (serial: A03 A04 B02 B03 B04 B01 A01)" >> ledger/raw/arms_driver.log
bash tools/run_solo.sh A bug03
bash tools/run_solo.sh A bug04
bash tools/run_solo.sh B bug02
bash tools/run_solo.sh B bug03
bash tools/run_solo.sh B bug04
bash tools/run_solo.sh B bug01
bash tools/run_solo.sh A bug01 "${SOLO01_PID:-}"
echo "$(date -Is) V2-REQUEUE DONE" >> ledger/raw/arms_driver.log
