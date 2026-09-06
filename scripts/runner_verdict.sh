# runner_verdict.sh — how `runner` accounts for its legs, and what it is allowed to claim.
#
# Sourced by `runner`. It exists as a separate file for one reason: the accounting was wrong, and
# the reason it stayed wrong is that testing it meant running `runner`, which runs `make check`,
# which takes minutes. **A control whose test is too slow to run is a control nobody runs.** These
# three functions have no side effects and no environment, so
# `tests/unit/test_runner_accounting.py` drives them in milliseconds — the same code, exercised.
#
# THE DEFECT THIS FIXES (REQ-FIX-004). `runner` used to answer an absent environment with
# `record "build" 0` — byte-identical to what a successful build recorded. The log said SKIPPED and
# the accounting said PASS, and the summary a person actually reads said ALL PASS. One leg (Swift)
# recorded nothing at all, so it disappeared from both lists rather than being counted wrongly,
# which is worse: a leg you can see scored wrong is a leg you can argue with.
#
# It had already cost a session. `runner`'s own comment records both Swift branches dying as
# "command not found" while `$FAILED` stayed empty and the run reported ALL PASS with the Swift
# tests red — found by an independent seat, not by the instrument.
#
# THE RULE, stated once so the code below is only its mechanism: **this repository may not claim a
# green run for work it did not do.** Not-run is a third state. It is never a pass, and it always
# costs the all-green claim, because the whole value of `runner` is that a person can read one line
# instead of a log.

PASSED=""
FAILED=""
SKIPPED=""
SKIP_REASONS=""

# record <name> <exit-code> — a leg that RAN. Nothing else may call this.
runner_record() {
  if [ "$2" = "0" ]; then
    PASSED="$PASSED $1"
  else
    FAILED="$FAILED $1"
  fi
}

# skip <name> <reason> — a leg the environment could not run. The reason is mandatory: a skip
# nobody can explain is indistinguishable from a skip nobody noticed.
runner_skip() {
  SKIPPED="$SKIPPED $1"
  SKIP_REASONS="${SKIP_REASONS}    $1: $2
"
}

# summary — the three lines a person reads. `skipped` is printed ONLY when there is something to
# say, so a clean run does not grow a line that is always empty and therefore always ignored.
runner_summary() {
  echo "passed  :$PASSED"
  echo "failed  :${FAILED:- none}"
  if [ -n "$SKIPPED" ]; then
    echo "skipped :$SKIPPED   <-- did NOT run; this is not a pass"
    printf '%s' "$SKIP_REASONS"
  fi
}

# verdict — the claim, and the exit code. A failure outranks a skip because a failure is a thing
# that happened and a skip is a thing that did not; the reader needs the first one first.
runner_verdict() {
  if [ -n "$FAILED" ]; then
    echo "FAILURES:$FAILED"
    return 1
  fi
  if [ -n "$SKIPPED" ]; then
    echo "INCOMPLETE — every leg that ran passed, but these did not run:$SKIPPED"
    echo "             This is not a green run. Supply what is missing, or say so out loud."
    return 1
  fi
  echo "ALL PASS"
  return 0
}
