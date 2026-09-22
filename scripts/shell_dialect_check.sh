#!/usr/bin/env bash
# Condition 15-12 — the shell GP ships must parse, and must declare one dialect.
#
# Open since 2026-09-10, reporting EVAPORATED for ten days. The council BUILT it at Increment 18 in
# the smallest form that can run in CI, and explicitly refused the original's second half (a
# "stripper self-test"): that would be a script checking a script, which is the layer the same
# sitting adopted 18-I to constrain.
#
# Field evidence, measured by the PM seat from the 2026-08-19 harvest: "3 red runs across 6 days
# from one root cause (D-136)", ~30 lines, "the project built it; GP has no equivalent" -- while
# GP's own control surface IS shell. Two more instances turned up in-session on darwin: `timeout`
# absent, and zsh refusing a glob bash passes through.
#
# Two assertions, no dependencies beyond bash itself:
#   1. every shipped .sh parses under `bash -n`
#   2. every shipped .sh declares the SAME interpreter -- one dialect, stated, not assumed
#
# Exit: 0 clean · 1 a script fails to parse or declares a different interpreter · 2 nothing to check.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 2

mapfile -t scripts < <(find scripts docs -name '*.sh' -type f 2>/dev/null | sort)
if [ ${#scripts[@]} -eq 0 ]; then
  echo "shell_dialect_check CANNOT RUN: no .sh files found. An empty set is not a pass -- if GP has"
  echo "  stopped shipping shell, delete this control rather than letting it report success over nothing."
  exit 2
fi

want='#!/usr/bin/env bash'
bad=0
for f in "${scripts[@]}"; do
  if ! bash -n "$f" 2>/dev/null; then
    echo "FAIL $f does not parse under bash -n"
    bash -n "$f" 2>&1 | sed 's/^/     /'
    bad=$((bad+1))
    continue
  fi
  got=$(head -1 "$f")
  if [ "$got" != "$want" ]; then
    echo "FAIL $f declares '$got', not '$want' -- GP ships one dialect on purpose; a script that"
    echo "     declares another runs differently on a macOS dev box and an ubuntu runner, and the"
    echo "     difference is invisible until it is expensive."
    bad=$((bad+1))
  fi
done

if [ "$bad" -gt 0 ]; then
  echo "shell_dialect_check FAIL: ${#scripts[@]} script(s), $bad problem(s)"
  exit 1
fi
echo "shell_dialect_check PASS: ${#scripts[@]} script(s), one dialect, all parse"
