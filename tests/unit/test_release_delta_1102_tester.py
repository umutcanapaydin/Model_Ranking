"""The release delta Tester's tests for run 1102 (`1a5fec0..970ffea`): faults injected into the range's code that the
range's own tests left green. Each case below is red when the named line is changed (the fault is in the docstring).

covers #563, #553, #551, #552, #555, #566, D-239, D-242, D-243
"""

from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from app.workflows import refresh as refresh_mod
from tests.unit.test_deploy_gate_522 import STEP
from tests.unit.test_deploy_gate_549 import _deploy, _dispatched
from tests.unit.test_deploy_gate_551 import _planted
from tests.unit.test_deploy_gate_563 import _gate, _repo, _stub_gh
from tests.unit.test_standup_566 import _awaiting, _clone
from tests.unit.test_wave_check_546 import _rule_beside_code
from tests.unit.test_wave_check_m21_rules import _commit, _git, _module

ROOT = Path(__file__).resolve().parents[2]


# --- #563: `_GITHUB_URL` names github.com over https or ssh, and only that --------------------------------------

@pytest.mark.parametrize("origin", ["http://github.com/o/r.git", "https://evilgithub.com/o/r.git",
                                    "https://sub.github.com/o/r.git", "ssh://git@evilgithub.com/o/r.git"])
def test_563_a_plain_http_or_other_host_origin_is_not_green(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                                            origin: str) -> None:
    """Fault: the host pattern widened to `https?://[^/]*github\\.com/`. Only github.com over https, ssh:// or scp
    names the repository the gate may ask; anything else is not green and `gh` is not asked."""
    log = _stub_gh(tmp_path, monkeypatch)
    assert _gate().ci_green(_repo(tmp_path, origin)) is False
    assert not log.exists()


# --- #553: YAML double-quoted escapes are decoded as YAML decodes them ------------------------------------------

def test_553_a_quoted_newline_escape_starts_a_second_command(tmp_path: Path) -> None:
    """Fault: `\\n` decoded to the letter `n`, so `echo hi` + `bash $SCRIPT` read as one echo and the start was lost."""
    code, out = _deploy(_dispatched(tmp_path, '      - run: "echo hi\\nbash $SCRIPT"\n'))
    assert code == 2 and "release.yml" in out, out


def test_553_a_quoted_escape_the_reader_knows_does_not_refuse_a_named_file(tmp_path: Path) -> None:
    """Fault: `\\e` dropped from the escape table, so an ANSI escape in a quoted value refused a named file."""
    code, out = _deploy(_dispatched(tmp_path, '      - run: "scripts/ship_it.sh \\e[0m"\n'))
    assert code == 0, out


# --- #551 (D-242): the shapes the range's own cases left unread -------------------------------------------------

def test_551_pushd_before_make_changes_the_directory_the_makefile_is_read_in(tmp_path: Path) -> None:
    """Fault: `pushd` dropped from CHDIRS -- `pushd deploy && make ship` read the wrong Makefile."""
    step = "      - run: pushd deploy && make ship\n"
    files = {"Makefile": "ship:\n\tscripts/ship_it.sh\n", "deploy/Makefile": "ship:\n\t$$X\n"}
    code, out = _deploy(_planted(tmp_path, STEP.format(step), files))
    assert code == 2 and "release.yml" in out, out


def test_551_a_step_working_directory_moves_the_makefile_read(tmp_path: Path) -> None:
    """Fault: `working-directory:` ignored -- `make ship` was read in the checkout's root, not the step's directory."""
    step = "      - working-directory: deploy\n        run: make ship\n"
    files = {"Makefile": "ship:\n\tscripts/ship_it.sh\n", "deploy/Makefile": "ship:\n\t$$X\n"}
    code, out = _deploy(_planted(tmp_path, STEP.format(step), files))
    assert code == 2 and "release.yml" in out, out


def test_551_a_make_chain_deeper_than_the_reader_follows_refuses(tmp_path: Path) -> None:
    """Fault: `_MAKE_DEPTH` raised from 8 to 800 -- a ten-deep `$(MAKE) tN` chain was followed to a named file and
    passed; the reader's limit is part of the fail-closed rule."""
    chain = "".join(f"t{i}:\n\t$(MAKE) t{i + 1}\n" for i in range(12)) + "t12:\n\tscripts/ship_it.sh\n"
    code, out = _deploy(_planted(tmp_path, STEP.format("      - run: make t0\n"), {"Makefile": chain}))
    assert code == 2 and "release.yml" in out, out


@pytest.mark.parametrize("step", ["      - run: bash --help\n", "      - run: python3 --version\n"])
def test_551_an_information_option_starts_no_file(tmp_path: Path, step: str) -> None:
    """Fault: `--help` dropped from INFO_OPTIONS -- `bash --help` read `--help` as the file it starts."""
    code, out = _deploy(_dispatched(tmp_path, step))
    assert code == 0, out


@pytest.mark.parametrize("step", ['      - run: deno compile "$SCRIPT"\n', '      - run: bun x "$TOOL"\n'])
def test_551_a_runtime_subcommand_that_takes_a_file_is_read(tmp_path: Path, step: str) -> None:
    """Fault: `compile` dropped from the deno subcommands that name a file."""
    code, out = _deploy(_dispatched(tmp_path, step))
    assert code == 2 and "release.yml" in out, out


# --- #552 (D-243): the rule at its edges, and the script's refusals ---------------------------------------------

AT = dt.datetime(2026, 11, 2, 21, 30, tzinfo=dt.UTC).timestamp()


def _iso(days: float, naive: bool = False) -> str:
    then = dt.datetime.fromtimestamp(AT - days * 86400, tz=dt.UTC)
    return (then.replace(tzinfo=None) if naive else then).isoformat(timespec="seconds")


def test_552_a_stamp_in_the_future_is_named_only_beyond_a_day() -> None:
    """Faults: the future bound made 0 (every clock-skewed stamp named) or removed (an impossible stamp trusted)."""
    assert refresh_mod.silent_sources({"a": _iso(-2 / 24)}, AT) == {}
    assert refresh_mod.silent_sources({"a": _iso(-25 / 24)}, AT) == {"a": _iso(-25 / 24)}


def test_552_a_stamp_with_no_zone_is_read_as_utc() -> None:
    """Fault: a naive stamp skipped instead of read as UTC, so an old naive arrival was never named."""
    assert refresh_mod.silent_sources({"a": _iso(8, naive=True), "b": _iso(6, naive=True)}, AT) == {
        "a": _iso(8, naive=True)}


def test_552_the_rule_takes_its_days_and_returns_the_names_sorted() -> None:
    """Faults: the `days` argument ignored; the result left in the record's order."""
    last_ok = {"zeta": _iso(3), "alpha": _iso(3), "mid": _iso(1)}
    assert list(refresh_mod.silent_sources(last_ok, AT, days=2)) == ["alpha", "zeta"]
    assert refresh_mod.silent_sources(last_ok, AT, days=4) == {}


def _script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "silent_sources.py"), *args], capture_output=True,
                          text=True, timeout=60, check=False)


@pytest.mark.parametrize("content", ["[]", '{"silent": {"arena": 5}}', '{"silent": {"arena": null}}',
                                     "[" * 200000, None])
def test_552_the_script_refuses_what_is_not_a_map_of_strings(tmp_path: Path, content: str | None) -> None:
    """Faults: a non-object record taken for "no silent source"; a non-string arrival accepted; the recursion error
    of a deeply nested file left as a traceback; an undecodable file left as a traceback."""
    record = tmp_path / "advisor.db.refresh.json"
    if content is None:
        record.write_bytes(b'{"silent": {"a": "\xff\xfe"}}')
    else:
        record.write_text(content, encoding="utf-8")
    done = _script("--issue", str(record))
    assert done.returncode == 2 and done.stdout == "", (done.returncode, done.stdout, done.stderr[-300:])
    assert done.stderr.startswith("silent sources:") and "Traceback" not in done.stderr, done.stderr[-300:]


def test_552_the_issue_quotes_each_name_and_arrival_and_lists_them_sorted(tmp_path: Path) -> None:
    """Faults: a name or an arrival left bare (an @mention would notify); a backtick left to break the quoting; the
    names left in the record's order."""
    record = tmp_path / "advisor.db.refresh.json"
    record.write_text(json.dumps({"silent": {"zeta": "2026-10-01T00:00:00+00:00", "@owner`x": "2026-09-01"}}),
                      encoding="utf-8")
    body = json.loads(_script("--issue", str(record)).stdout)["body"]
    rows = [line for line in body.splitlines() if line.startswith("| `")]
    assert rows == ["| `@owner'x` | `2026-09-01` |", "| `zeta` | `2026-10-01T00:00:00+00:00` |"], body
    plain = _script(str(record)).stdout.splitlines()
    assert [line.split()[0] for line in plain] == ["@owner`x", "zeta"]


# --- #566: standup.sh reads each default-branch candidate, `refs/remotes/origin/master` included ----------------

def test_566_a_clone_whose_default_branch_is_origin_master_still_compares(tmp_path: Path) -> None:
    """Fault: `refs/remotes/origin/master` dropped from the candidates -- with no other default ref, "ADRs awaiting"
    listed nothing."""
    clone, env = _clone(tmp_path)

    def git(*args: str) -> None:
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@x", *args], cwd=clone, check=True,
                       capture_output=True, env=env)

    git("push", "-q", "origin", "main:refs/heads/master")
    git("fetch", "-q", "origin")
    git("remote", "set-head", "origin", "-d")
    git("update-ref", "-d", "refs/remotes/origin/main")
    git("switch", "-q", "fix/issue-1-x")
    git("branch", "-D", "main")
    assert _awaiting(clone, env) == ["D-101"]


# --- #555: a closure counts through any of its records, the closure-review glob included ------------------------

def test_555_a_closure_review_record_counts_as_the_closure(tmp_path: Path) -> None:
    """Fault: the `docs/reviews/m<N-1>-closure*.md` glob dropped from the records -- a closure that wrote only that
    record was not a closure, and the wave started at main."""
    root = _rule_beside_code(tmp_path)
    record = _git(root, "rev-parse", _commit(root, "m1 closes", "2026-10-11T12:00:00",
                                             {"docs/reviews/m1-closure-review.md": "# m1 closure review\n"}))
    _commit(root, "m2's first wave", "2026-10-12T12:00:00", {"src/app/later.py": "y = 1\n"})
    _git(root, "branch", "closure/m1", _git(root, "rev-parse", "HEAD"))
    ids = re.match(r"m(\d+)-w(\d+)", "m2-w1")
    assert _module("wave_check")._wave_base(root, ids, "HEAD") == record

