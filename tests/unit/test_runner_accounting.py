"""`runner` cannot score an unrun leg as a pass — cites REQ-FIX-004.

**The defect.** When the Epoch bundle was absent `runner` printed `SKIPPED` into the log and then
called `record "build" 0` — the same call a successful build makes. Two more sites did the same for
the engine and the iOS build, and a fourth (Swift) recorded nothing at all, so that leg vanished
from both the passed and the failed list. The summary could therefore read `ALL PASS` while major
legs had not executed, and `runner` is the instrument this project reports its own health with.

This is the W-023 / W-058 shape once more, turned inward: healthy to every existence check,
answering nothing. It had already bitten once — the comment at `runner:267` records a session where
both Swift branches died as "command not found", `$FAILED` stayed empty and `runner` reported
ALL PASS with the Swift tests red.

**Why the accounting moved to `scripts/runner_verdict.sh`.** The plan's stated verification was to
run `runner` with the bundle path unset — but a real run executes `make check`, which takes minutes,
so nothing would ever have run it. A control whose test is too slow to run is a control nobody
checks. The accounting is now a sourced file with no side effects, and these tests drive it
directly through bash: the same code `runner` executes, exercised in milliseconds.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

#: Resolved from THIS FILE, not from the working directory — seed F.4, and a finding against the
#: first version of this module: run from the repo's parent it failed 11 of 14, and two assertions
#: in the skip test were satisfied by a bash that had sourced nothing at all.
REPO = Path(__file__).resolve().parents[2]
LIB = REPO / "scripts" / "runner_verdict.sh"
RUNNER = REPO / "runner"


def _bash(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-c", f"set -u; . {LIB}\n{script}"],
        capture_output=True,
        text=True,
        check=False,
    )


def test_a_clean_run_is_all_pass() -> None:
    result = _bash("runner_record a 0; runner_record b 0; runner_verdict")
    assert result.returncode == 0
    assert "ALL PASS" in result.stdout


def test_a_failure_is_reported_and_exits_non_zero() -> None:
    result = _bash("runner_record a 0; runner_record b 1; runner_verdict")
    assert result.returncode != 0
    assert "b" in result.stdout


def test_a_skipped_leg_is_not_counted_as_passed() -> None:
    """REQ-FIX-004's first half: the leg must not appear in the passed list."""
    result = _bash('runner_record a 0; runner_skip build "no Epoch bundle"; runner_summary')
    assert (
        "build" not in result.stdout.split("passed")[1].split("\n")[0]
    ), f"a skipped leg was listed as passed:\n{result.stdout}"


def test_a_skip_prevents_the_all_pass_claim() -> None:
    """REQ-FIX-004's second half, and the one that matters.

    Not counting a skip as a pass is worth nothing if the summary still says everything passed —
    the reader's takeaway is the verdict line, not the list.
    """
    result = _bash('runner_record a 0; runner_skip build "no Epoch bundle"; runner_verdict')
    assert result.returncode != 0, "a run with an unexecuted leg claimed success"
    assert "ALL PASS" not in result.stdout
    assert "build" in result.stdout


def test_the_skip_reason_survives_into_the_summary() -> None:
    """A skip nobody can explain is indistinguishable from a skip nobody noticed."""
    result = _bash('runner_skip ios-build "xcodebuild is not on PATH"; runner_summary')
    assert "xcodebuild is not on PATH" in result.stdout


def test_a_failure_outranks_a_skip() -> None:
    """Both present: the failure is what the reader must be told first."""
    result = _bash('runner_skip build "no bundle"; runner_record tests 1; runner_verdict')
    assert result.returncode != 0
    assert "tests" in result.stdout


@pytest.mark.parametrize("leg", ["build", "engine", "swift-tests", "ios-build"])
def test_every_environment_dependent_leg_has_a_skip_path(leg: str) -> None:
    """Pin the CLAIM in `runner` itself, not only the library it now calls.

    **The first version of this test forbade the literal `record "<leg>" 0` anywhere in `runner`,
    and it was wrong — which is worth recording, because the wrongness is the interesting part.**
    That literal has a legitimate use: the build leg maps exit 3 (D-128 refused a candidate) onto a
    pass deliberately, because a refusal is the guard working rather than the build failing. A test
    banning the literal would have forced that decision to be rewritten to satisfy a grep.

    The defect was never the literal. It was that the ENVIRONMENT-ABSENT path scored a pass. So the
    claim pinned here is the one that was actually violated: each of these four legs must have a
    branch that calls `skip`, which cannot be counted as a pass by construction.
    """
    text = RUNNER.read_text(encoding="utf-8")
    assert (
        f'skip "{leg}"' in text
    ), f"`runner` has no skip path for `{leg}` — an absent environment would be scored as a pass"


def test_runner_sources_the_accounting_library() -> None:
    """The behavioural tests above prove the library; this proves `runner` uses it.

    Without this, every test in this file could pass against a `runner` that still kept its own
    copy of the accounting — which is exactly the drift that let the original defect survive.
    """
    assert "scripts/runner_verdict.sh" in RUNNER.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------------------------
# Is `runner` WIRED to the library? — M13-W1 tester BLOCKING-1
#
# Everything above proves `scripts/runner_verdict.sh`. None of it proved that `runner` uses it, and
# an independent tester killed the wave on exactly that gap: six wiring mutants survived the whole
# suite. The worst reverted one line of the exit gate and reproduced the original defect verbatim —
# `skipped : build`, then `ALL PASS`, exit 0 — with 810 tests green.
#
# The criterion (REQ-FIX-004) names `runner`, not the library it happens to call. So these tests
# execute `runner`'s OWN wrappers and its OWN gate, by extracting them and running them under bash.
# Extraction rather than invocation because running `runner` for real costs `make check`, and a
# control whose test is too slow to run is the thing this criterion is about.
# ---------------------------------------------------------------------------------------------


def _runner_harness(legs: str) -> subprocess.CompletedProcess[str]:
    """Run `runner`'s wrappers and exit gate, taken from `runner` itself, over `legs`.

    Everything between the source line and the end of `skip()` is `runner`'s accounting, and the
    tail is its verdict block. Both are lifted verbatim — a mutant that edits either is a mutant
    this harness executes.
    """
    text = RUNNER.read_text(encoding="utf-8")
    start = text.index('. "$REPO/scripts/runner_verdict.sh"')
    end = text.index("# --- 0. context", start)
    wrappers = text[start:end]
    gate_start = text.index("if runner_verdict; then")
    gate_end = text.index("exit 1", gate_start) + len("exit 1")
    gate = text[gate_start:gate_end]
    script = f"set -u\nREPO={REPO}\nFULL=/dev/null\nOUT=/dev/null\n{wrappers}\n{legs}\n{gate}\n"
    return subprocess.run(["bash", "-c", script], capture_output=True, text=True, check=False)


def test_runner_own_gate_refuses_all_pass_when_a_leg_was_skipped() -> None:
    """The mutant that survived: revert the gate to `[ -z "$FAILED" ]` and a skip goes green."""
    result = _runner_harness('record "tests" 0\nskip "build" "no Epoch bundle"')
    assert (
        result.returncode != 0
    ), f"`runner`'s own gate claimed success with an unrun leg:\n{result.stdout}"
    assert "ALL PASS" not in result.stdout


def test_runner_own_gate_passes_a_genuinely_clean_run() -> None:
    """The other direction, so the test above cannot be satisfied by a gate that always fails."""
    result = _runner_harness('record "tests" 0\nrecord "build" 0')
    assert result.returncode == 0
    assert "ALL PASS" in result.stdout


def test_runner_own_wrappers_reach_the_library() -> None:
    """Kills the mutants that keep the wrappers but stop them delegating.

    `record()` and `skip()` in `runner` are thin shims over `runner_record` / `runner_skip`. A shim
    that logs and forgets to delegate leaves the accounting empty, and an empty `SKIPPED` is
    indistinguishable from a clean run.
    """
    result = _runner_harness('skip "ios-build" "xcodebuild is not on PATH"')
    assert result.returncode != 0
    assert "ios-build" in result.stdout


def test_runner_actually_sources_the_library() -> None:
    """Kills the mutant that comments out the source line.

    The earlier version of this check grepped for the PATH, which also appears in the explanatory
    comment above the source line — so commenting the line out left the test green against a
    `runner` that had no accounting at all. Assert the executable statement.
    """
    assert '. "$REPO/scripts/runner_verdict.sh"' in RUNNER.read_text(encoding="utf-8")


@pytest.mark.parametrize("leg", ["build", "engine", "swift-tests", "ios-build"])
def test_a_skip_path_never_also_records_a_pass(leg: str) -> None:
    """Kills the realistic regression: someone keeps `skip` and re-adds `record <leg> 0` beside it.

    The presence check above cannot see that; a branch calling both would score the leg as passed
    AND as skipped, and `runner_verdict` would report INCOMPLETE while the passed list also named
    it. Scoped to the same `else` branch rather than the whole file, because `record "build" 0` has
    a legitimate use elsewhere — exit 3 (a D-128 refusal) is mapped onto a pass on purpose.
    """
    text = RUNNER.read_text(encoding="utf-8")
    branch_start = text.index(f'skip "{leg}"')
    branch = text[branch_start : text.index("fi", branch_start)]
    assert (
        f'record "{leg}"' not in branch
    ), f"the skip branch for `{leg}` also records a result: {branch!r}"
