#!/usr/bin/env bash
# The single offline gate for the pipeline prototype. Judged BY EXIT CODE, never by its
# tail (SKILL.md Beat 3, step 10). Runs the kernel leg then the bridge; either can fail it.
set -u
cd "$(dirname "$0")"
LEAN_BIN="${LEAN_BIN:-$HOME/.elan/bin/lean}"
SPEC=step1_contract/StaleQuote.lean
WHITELIST="propext Quot.sound Classical.choice"
fail=0

say() { printf "%s\n" "$*"; }
bad() { printf "  FAIL %s\n" "$*"; fail=1; }
good(){ printf "  ok   %s\n" "$*"; }

say "-- kernel leg --"
if [ ! -x "$LEAN_BIN" ] || ! "$LEAN_BIN" --version 2>/dev/null | grep -q "^Lean (version"; then
  bad "no Lean toolchain at $LEAN_BIN"
else
  want=$(sed -n 's|.*lean4:v||p' step1_contract/lean-toolchain | tr -d '[:space:]')
  have=$("$LEAN_BIN" --version | sed -n 's/^Lean (version \([^,]*\).*/\1/p')
  [ "$want" = "$have" ] || bad "toolchain drift: spec pins $want, lean is $have"

  out=$("$LEAN_BIN" "$SPEC" 2>&1); rc=$?
  if [ $rc -ne 0 ]; then bad "spec does not compile"; printf '%s\n' "$out" | head -6
  elif grep -qE "^[[:space:]]*(axiom|opaque)[[:space:]]+[A-Za-z_]" "$SPEC"; then
    bad "spec DECLARES an axiom/opaque -- an admitted premise, not a proof"
  elif printf '%s' "$out" | grep -qE "declaration uses .sorry.|sorryAx"; then
    bad "spec has a sorry -- ADMITTED, not proved"
  else
    # The only testimony layout cannot spoof: the kernel's own axiom profile.
    probe=$(mktemp --suffix=.lean)
    cat "$SPEC" > "$probe"
    grep -oE "^theorem [A-Za-z_0-9]+" "$SPEC" | sed 's/theorem /#print axioms StaleQuote./' >> "$probe"
    prof=$("$LEAN_BIN" "$probe" 2>&1); prc=$?
    rm -f "$probe"
    if [ $prc -ne 0 ]; then bad "axiom-profile probe did not compile"
    else
      offending=$(printf '%s\n' "$prof" | sed -n 's/.*depends on axioms: \[\(.*\)\]/\1/p' \
                  | tr ',' '\n' | tr -d ' ' | sort -u \
                  | while read -r a; do [ -n "$a" ] && ! printf '%s' "$WHITELIST" | grep -qw "$a" && echo "$a"; done)
      if [ -n "$offending" ]; then bad "axioms outside the whitelist: $(echo $offending)"
      else
        n=$(grep -cE "^theorem " "$SPEC")
        good "spec compiles, 0 sorry, $n theorems within the axiom whitelist"
      fi
    fi
  fi
fi

say "-- bridge --"
if python3 step3_bridge/bridge.py > /tmp/bridge.$$.log 2>&1; then
  good "bridge green ($(grep -c '^  ok' /tmp/bridge.$$.log) checks)"
else
  bad "bridge red"; grep -E "^  FAIL|BRIDGE FAILED" /tmp/bridge.$$.log | head -6
fi
rm -f /tmp/bridge.$$.log

say ""
if [ "$fail" -ne 0 ]; then say "GATE RED"; exit 1; fi
say "GATE GREEN"; exit 0
