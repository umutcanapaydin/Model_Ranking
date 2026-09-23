#!/usr/bin/env bash
# The shell this package ships must parse, and must declare one dialect.
#
# Field evidence: a project lost three red CI runs in six days to one root cause -- a script that
# ran differently on a macOS dev box and an ubuntu runner. Two more instances turned up on darwin
# alone: `timeout` absent, and zsh refusing a glob bash passes through.
#
# Two assertions, no dependencies beyond bash itself -- including the bash 3.2 macOS ships as
# /bin/bash, so this script uses no bash-4 builtins:
#   1. every shipped .sh parses under `bash -n`
#   2. every shipped .sh declares the SAME interpreter -- one dialect, stated, not assumed
#
# Exit: 0 clean · 1 a script fails to parse or declares a different interpreter · 2 nothing to check.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 2

want='#!/usr/bin/env bash'
total=0
bad=0
while IFS= read -r f; do
  [ -n "$f" ] || continue
  total=$((total+1))
  if ! bash -n "$f" 2>/dev/null; then
    echo "FAIL $f does not parse under bash -n"
    bash -n "$f" 2>&1 | sed 's/^/     /'
    bad=$((bad+1))
    continue
  fi
  got=$(head -1 "$f")
  # A library meant to be `source`d has no shebang -- it is not executed -- and adding one only to
  # satisfy this check is misleading. Such a file declares its dialect the way shellcheck reads it,
  # on its first line; any OTHER dialect still fails.
  if [ "$got" = "# shellcheck shell=bash" ] && [ ! -x "$f" ]; then
    continue
  fi
  if [ "$got" != "$want" ]; then
    echo "FAIL $f declares '$got', not '$want' -- one dialect on purpose: a script that"
    echo "     declares another runs differently on a macOS dev box and an ubuntu runner, and the"
    echo "     difference is invisible until it is expensive."
    bad=$((bad+1))
  fi
done <<EOF
$(find scripts docs -name '*.sh' -type f 2>/dev/null | sort)
EOF

if [ "$total" -eq 0 ]; then
  echo "shell_dialect_check CANNOT RUN: no .sh files found. An empty set is not a pass -- if the"
  echo "  package has stopped shipping shell, delete this control rather than letting it report"
  echo "  success over nothing."
  exit 2
fi
if [ "$bad" -gt 0 ]; then
  echo "shell_dialect_check FAIL: $total script(s), $bad problem(s)"
  exit 1
fi
echo "shell_dialect_check PASS: $total script(s), one dialect, all parse"
