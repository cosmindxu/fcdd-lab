#!/usr/bin/env bash
# THE GATE.  One entry point, judged by EXIT CODE — never by its tail.
#
#   b0  kernel completeness gate (lean exit 0 + empty axiom profile)
#   b1  witnesses: every kernel-proved fact re-checked in the shipped twin
#   b2  mutations: 16 observation + 10 implementation faults, every clause
#       negatively tested
#   b3  spec-vs-twin brute force over 300 generated positions, 9 observables
#   b4  perft cross-check against the RUNNING Z80 engine (410,082 nodes)
#   b5  emulator-as-oracle: 9 real games, engine legal lists vs twin
#   b6  alpha-beta == minimax, widened beyond the kernel's small scope
#   b7  organic findings pinned as regression probes
#   s1-s3  SMT tier (z3): int16 no-overflow, memory layout, dead aspiration
#
# Stale bytecode is cleared first so a cached .pyc cannot mask a red gate.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE" || exit 2
find "$HERE/.." -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null
rm -f "$HERE/../spec/Contract.olean"

PY=python3
VPY="$HOME/.venvs/quant/bin/python"
fail=0
declare -a RED=()

run() {   # run <label> <cmd...>
  local label="$1"; shift
  if "$@"; then
    :
  else
    echo "  ^^^ $label RED (exit $?)"
    RED+=("$label")
    fail=1
  fi
}

echo "=== HC-91 formal contract — conformance gate ==="
run b0 bash "$HERE/b0_lean_gate.sh"
run b1 $PY "$HERE/b1_witnesses.py"
run b2 $PY "$HERE/b2_mutations.py"
run b3 $PY "$HERE/b3_spec_twin_brute.py"
run b4 $PY "$HERE/b4_perft_cross.py"
run b5 $PY "$HERE/b5_emulator_oracle.py"
run b6 $PY "$HERE/b6_alphabeta.py"
run b7 $PY "$HERE/b7_findings.py"
run s1 "$VPY" "$HERE/../smt/s1_eval_range.py"
run s2 "$VPY" "$HERE/../smt/s2_addresses.py"
run s3 "$VPY" "$HERE/../smt/s3_aspiration.py"

echo "==============================================="
if [ $fail -eq 0 ]; then
  echo "GATE: GREEN (11/11 layers)"
else
  echo "GATE: RED — ${RED[*]}"
fi
exit $fail
