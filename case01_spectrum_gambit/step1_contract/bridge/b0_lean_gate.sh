#!/usr/bin/env bash
# BRIDGE layer 0 — the KERNEL COMPLETENESS GATE (FCDD Beat 1.2).
#
# Lean's own accounting must report ZERO unproven obligations.  Three
# independent conditions, all judged by exit code:
#
#   G1  `lean` exits 0 on spec/Contract.lean (no errors, no `sorry` warnings)
#   G2  EVERY `#print axioms` line reads "does not depend on any axioms" —
#       so no sorryAx, no Classical.choice, no propext, and in particular no
#       Lean.ofReduceBool (which is what `native_decide` would inject)
#   G3  the source contains no `sorry`, no `axiom`, no `native_decide`,
#       no `@[implemented_by]` and no `partial` — the ways a Lean file can
#       look proved while evaluating something else
#
# G3 exists because G1+G2 alone can be defeated: `native_decide` shows up in
# the axiom report, but an `@[implemented_by]` override does NOT.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
SPEC="$HERE/../spec"
LEAN="$HOME/.elan/bin/lean"
OUT="$(mktemp)"
rc=0

"$LEAN" "$SPEC/Contract.lean" >"$OUT" 2>&1
g1=$?
if [ $g1 -ne 0 ]; then
  echo "[b0_lean_gate] FAIL G1: lean exited $g1"
  head -40 "$OUT"
  rc=1
fi

total=$(grep -c "#print axioms" "$SPEC/Contract.lean")
clean=$(grep -c "does not depend on any axioms" "$OUT")
dirty=$(grep "depends on axioms" "$OUT")
if [ -n "$dirty" ]; then
  echo "[b0_lean_gate] FAIL G2: non-empty axiom profile"
  echo "$dirty"
  rc=1
fi
if [ "$clean" -ne "$total" ]; then
  echo "[b0_lean_gate] FAIL G2: $clean clean axiom reports, expected $total"
  rc=1
fi
if grep -qiE "sorry|warning" "$OUT"; then
  echo "[b0_lean_gate] FAIL G1: lean emitted a warning or a sorry"
  grep -iE "sorry|warning" "$OUT" | head
  rc=1
fi

# G3 — banned constructs.  Comments are stripped first so the prose in the
# header (which legitimately names `sorry` and `native_decide`) cannot mask
# or fake a violation.
STRIPPED="$(mktemp)"
sed -e 's,--.*$,,' "$SPEC/Contract.lean" | sed -e '/\/-/,/-\//d' >"$STRIPPED"
for bad in 'sorry' 'native_decide' 'implemented_by' 'partial def' 'extern'; do
  if grep -qE "(^|[^A-Za-z_])$bad" "$STRIPPED"; then
    echo "[b0_lean_gate] FAIL G3: banned construct '$bad' in the spec"
    grep -nE "(^|[^A-Za-z_])$bad" "$STRIPPED" | head -3
    rc=1
  fi
done
if grep -qE "^axiom " "$STRIPPED"; then
  echo "[b0_lean_gate] FAIL G3: the spec declares an axiom"
  rc=1
fi

thms=$(grep -c "^theorem " "$SPEC/Contract.lean")
defs=$(grep -c "^def " "$SPEC/Contract.lean")
if [ $rc -eq 0 ]; then
  echo "[b0_lean_gate] OK: lean exit 0, $thms theorems, $defs definitions, $clean/$total axiom reports EMPTY, no banned constructs"
fi
rm -f "$OUT" "$STRIPPED"
exit $rc
