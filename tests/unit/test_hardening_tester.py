"""The hardening wave's Tester (`docs/reviews/backlog-hardening-tester.md`): each fault the wave's suites let
through, where D-198 says the behaviour holds.

Every plant goes into a copy under `tmp_path` or a scratch repository; the app's files are never written.
Every question is made up, never a held-out one."""

from __future__ import annotations

import shutil
import subprocess
import types
from pathlib import Path

import pytest

from tests import skips
from tests.unit import test_ios_client_contract as contract
from tests.unit import test_router_hints as hints
from tests.unit.test_language_rule_escapes import _flagged
from tests.unit.test_swift_reads import pin_files, swift_reads
from tests.unit.test_wave_check_backlog_order import DECISIONS, WITH_D2, _branch
from tests.unit.test_wave_check_m21_rules import _commit, _git, _module

# --- D-198 clause 1 (#271): L1 decodes escapes ------------------------------------------------------------


def test_l1_reads_an_escape_in_either_case_and_an_escaped_backslash_as_text(tmp_path: Path) -> None:
    """T1 (faults A04, A07, A08): JSON's `\\uXXXX` and Swift's `\\u{...}` take hex digits in either case,
    and the wave's tests wrote JSON's in lower case and Swift's in upper case only. Swift's escaped
    backslash is text, as JSON's is."""
    flagged = _flagged(tmp_path, {
        "upper.json": '["bu bir \\u015Fey"]\n',
        "Lower.swift": 'let line = "bu bir \\u{15f}ey"\n',
        "Literal.swift": 'let text = "a backslash then u{15F}: \\\\u{15F}"\n',
    })
    assert flagged == {"upper.json", "Lower.swift"}, flagged


# --- D-198 clause 2 (#272): the record scan and the age of an overlap ---------------------------------------


def test_a_held_question_is_found_whatever_its_own_spacing() -> None:
    """T2 (fault B06): the record's white space is collapsed, and so is the question's, so a question kept
    with a doubled space or a trailing newline is still found. Made up."""
    question = "which model would best plan  a three day hike in the alps\n"
    record = "The probe asked: which model would best plan a three day hike in the alps."
    assert contract._record_matches({question}, {"docs/a.md": record}) == {"docs/a.md": 1}


def test_a_record_first_committed_after_its_set_is_not_excused(tmp_path: Path) -> None:
    """T3 (faults B09, B10, B13): the age check named only records older than the set, and its comparison
    lived inside the test, so no plant could show it fail. A record first committed after the set is
    named; a record older than the set, deleted and added again later, is still older."""
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    _commit(root, "older records", "2026-10-01T12:00:00", {"docs/old.md": "old\n", "docs/kept.md": "kept\n"})
    _commit(root, "the set", "2026-10-02T12:00:00", {"scripts/router_probe/probe_set.json": "[]\n"})
    _commit(root, "a newer record", "2026-10-03T12:00:00", {"docs/new.md": "new\n"})
    (root / "docs" / "kept.md").unlink()
    _commit(root, "drop one", "2026-10-04T12:00:00", {})
    _commit(root, "and add it back", "2026-10-05T12:00:00", {"docs/kept.md": "kept\n"})
    overlap = {"probe_set.json": {"docs/old.md": 1, "docs/kept.md": 1, "docs/new.md": 1}}
    assert contract._records_not_older_than_their_set(root, overlap) == ["docs/new.md (probe_set.json)"]
    assert contract._records_not_older_than_their_set(root, {"probe_set.json": {"docs/old.md": 1}}) == []


def test_the_git_history_need_holds_only_in_a_whole_history(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """T4 (faults H01, H02): the age test needs the history, and the need's probe was held by no test, so a
    probe that never held skipped it everywhere in silence. Whole: held. Shallow, or no repository: not."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    whole = tmp_path / "whole"
    whole.mkdir()
    _git(whole, "init", "-q", "-b", "main")
    _commit(whole, "one", "2026-10-01T12:00:00", {"a.txt": "1\n"})
    _commit(whole, "two", "2026-10-02T12:00:00", {"a.txt": "2\n"})
    subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{whole}", str(tmp_path / "shallow")],
                   capture_output=True, check=True, timeout=30)
    (tmp_path / "none").mkdir()
    held = {}
    for name in ("whole", "shallow", "none"):
        monkeypatch.setattr(skips, "ROOT", tmp_path / name)
        held[name] = skips.NEEDS["git_history"].here()
    assert held == {"whole": True, "shallow": False, "none": False}, held


# --- D-198 clause 3 (#274): a backlog wave's decision comes before its code --------------------------------


@pytest.mark.parametrize("rel", ["runner/run.sh", "requirements/main.txt", "schemas/record.json", "stack.mk"])
def test_a_backlog_adr_beside_any_backlog_code_path_is_refused(tmp_path: Path, rel: str) -> None:
    """T5 (faults D02 to D05): `BACKLOG_CODE` names nine paths, and the wave's tests planted five of them."""
    root = _branch(tmp_path)
    _commit(root, "rule and build", "2026-10-10T13:00:00", {"docs/decisions.md": WITH_D2, rel: "x\n"})
    problems, _ = _module("wave_check").branch_adr_problems(root)
    assert any("D-2" in p for p in problems), (rel, problems)


def test_a_backlog_branch_that_adds_a_record_or_edits_an_old_close_is_still_read(tmp_path: Path) -> None:
    """T6 (faults D08, D09): the rule leaves a range to the close only when it ADDS a milestone close. A
    backlog wave adds its review records, and may edit a close already merged; neither is a close of its own."""
    root = _branch(tmp_path / "record")
    _commit(root, "rule, code and a review", "2026-10-10T13:00:00",
            {"docs/decisions.md": WITH_D2, "src/app/other.py": "x = 2\n", "docs/reviews/backlog-x-review.md": "r\n"})
    assert any("D-2" in p for p in _module("wave_check").branch_adr_problems(root)[0])

    root = tmp_path / "close" / "repo"
    root.mkdir(parents=True)
    _git(root, "init", "-q", "-b", "main")
    _commit(root, "base", "2026-10-01T12:00:00", {"docs/decisions.md": DECISIONS, "src/app/other.py": "x = 1\n",
                                                  "docs/plans/m30-wave-1-close.md": "close\n"})
    _git(root, "update-ref", "refs/remotes/origin/main", "main")
    _git(root, "checkout", "-q", "-b", "wave/backlog-y")
    _commit(root, "rule and code, and a fix to an old close", "2026-10-10T13:00:00",
            {"docs/decisions.md": WITH_D2, "src/app/other.py": "x = 2\n", "docs/plans/m30-wave-1-close.md": "fixed\n"})
    assert any("D-2" in p for p in _module("wave_check").branch_adr_problems(root)[0])


def test_a_backlog_adr_after_a_test_commit_that_cites_it_is_refused(tmp_path: Path) -> None:
    """T7 (fault D10): a commit that cites the decision is too early if it changes any backlog code path,
    tests included, not only the code a milestone close reads."""
    root = _branch(tmp_path)
    _commit(root, "test under D-2", "2026-10-10T13:00:00", {"tests/unit/test_two.py": "def test_two():\n    pass\n"})
    _commit(root, "docs: the rule", "2026-10-10T14:00:00", {"docs/decisions.md": WITH_D2})
    problems, _ = _module("wave_check").branch_adr_problems(root)
    assert any("D-2" in p for p in problems), problems


def test_a_backlog_adr_after_unrelated_code_passes(tmp_path: Path) -> None:
    """T8 (fault D12): a backlog wave has no plan, so only a code commit that cites its decision comes too
    early. Another fix's commit before it does not."""
    root = _branch(tmp_path)
    _commit(root, "an unrelated fix", "2026-10-10T13:00:00", {"src/app/other.py": "x = 2\n"})
    _commit(root, "docs: the rule", "2026-10-10T14:00:00", {"docs/decisions.md": WITH_D2})
    _commit(root, "code under D-2", "2026-10-10T15:00:00", {"src/app/other.py": "x = 3\n"})
    assert _module("wave_check").branch_adr_problems(root) == ([], None)


def test_a_branch_with_no_merge_base_says_the_rule_read_nothing(tmp_path: Path) -> None:
    """T14 (fault D16): with no merge base, the rule reads nothing and must say so (D-192 clause 2); the wave's
    tests held only the skip with no `origin/main`. Here `origin/main` is a history unrelated to the branch."""
    root = _branch(tmp_path)
    _commit(root, "rule and code", "2026-10-10T13:00:00", {"docs/decisions.md": WITH_D2, "src/app/other.py": "x = 2\n"})
    _git(root, "checkout", "-q", "--orphan", "elsewhere")
    _git(root, "rm", "-rfq", ".")
    _commit(root, "an unrelated history", "2026-10-10T14:00:00", {"a.txt": "a\n"})
    _git(root, "update-ref", "refs/remotes/origin/main", "elsewhere")
    _git(root, "checkout", "-q", "wave/backlog-x")
    problems, skipped = _module("wave_check").branch_adr_problems(root)
    assert problems == [] and skipped and "#274" in skipped, (problems, skipped)


def test_wave_check_all_fails_on_the_backlog_rules_findings_and_prints_its_skips(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """T9 (faults E01 to E04): the wiring was held by a search for the rule's name in the script's text. Its
    findings could be dropped, its skip left unsaid, or another folder read, and every test passed."""
    every = _module("wave_check_all")
    monkeypatch.setattr(every, "_run", lambda check, records: ([], []))
    monkeypatch.setattr(every, "missing_closes", lambda root: [])
    monkeypatch.setattr(every, "headless_waves", lambda root: [])
    read: list[Path] = []

    def rule(found: list[str], skipped: str | None):
        def branch_adr_problems(root: Path) -> tuple[list[str], str | None]:
            read.append(root)
            return found, skipped
        return types.SimpleNamespace(branch_adr_problems=branch_adr_problems)

    monkeypatch.setattr(every, "_load_wave_check", lambda: rule(["D-9 first appears in `abc1234` (#274)"], None))
    assert every.main() == 1
    assert "wave-check-all: D-9 first appears" in capsys.readouterr().out
    assert read == [every.ROOT]

    monkeypatch.setattr(every, "_load_wave_check", lambda: rule([], "the decision order read nothing: shallow"))
    assert every.main() == 0
    assert "SKIPPED [wave-check-all]: the decision order read nothing: shallow" in capsys.readouterr().out

    monkeypatch.setattr(every, "_load_wave_check", lambda: types.SimpleNamespace())
    assert every.main() == 0
    assert "SKIPPED [wave-check-all]: a backlog wave's decision order (#274) read nothing: wave_check has no such rule" \
        in capsys.readouterr().out


# --- D-198 clause 4 (#275): the guard's detector --------------------------------------------------------------


def test_the_detector_finds_a_read_through_a_chained_constant_a_far_constant_and_a_near_local() -> None:
    """T12 (faults G04, G05, G07, G09, G12): the wave's planted module bound its constant two lines above
    its read, so the local-window rule found it, and no case needed a constant chained through another, a
    constant bound to a `.swift` path outside `ios/`, or a local two lines up."""
    planted = (
        'APP = ROOT / "ios"\n'                                          # 1
        'ENGINE = APP / "Engine"\n'                                     # 2
        'FIXTURE = ROOT / "scripts" / "Fixture.swift"\n'                # 3
        "\n\n\n"                                                        # 4 to 6
        "def test_y():\n"                                               # 7
        '    a = (ENGINE / name).read_text(encoding="utf-8")\n'         # 8: through a chained constant
        '    b = FIXTURE.read_text(encoding="utf-8")\n'                 # 9: a far constant bound to a Swift file
        '    path = HERE / "Local.swift"\n'                             # 10
        "    other = 1\n"                                               # 11
        '    c = path.read_text(encoding="utf-8")\n'                    # 12: a local two lines up
        '    d = (ROOT / "docs" / "x.md").read_text(encoding="utf-8")\n'  # 13: not the app's
    )
    assert [number for number, _ in swift_reads(planted)] == [8, 9, 12]


def test_the_guard_reads_each_pin_file_275_named_and_sees_its_reads() -> None:
    """T13 (fault G10): D-198 clause 4's guard reads every pin file under `tests/unit/`, and its file list was
    its own loop's, so a narrowed list passed both the guard and its floor. Each file #275 named is read, and
    the detector sees a read of the app's Swift in it."""
    named = {"test_engine_address.py", "test_families.py", "test_ios_platform_drift.py",
             "test_ios_visual_contract.py", "test_screen_paths.py", "test_uitext_sentence_rows.py"}
    files = {path.name: path for path in pin_files()}
    assert named <= set(files), sorted(named - set(files))
    blind = sorted(name for name in named
                   if not swift_reads(files[name].read_text(encoding="utf-8")))  # raw: this folder's Python
    assert not blind, f"the detector sees no read of the app's Swift in {blind}"


# --- D-198 clause 5 (#276): the egress pin --------------------------------------------------------------------


def _store_copy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, store: str) -> Path:
    copy = tmp_path / "ios"
    shutil.copytree(hints.CLIENT, copy / hints.CLIENT.name)
    shutil.copytree(hints.CLIENT.parent / "ModelRanking.xcodeproj", copy / "ModelRanking.xcodeproj")
    monkeypatch.setattr(hints, "CLIENT", copy / hints.CLIENT.name)
    return next((copy / hints.CLIENT.name).rglob(store))


def _plant_before_init(path: Path, text: str) -> None:
    code = path.read_text(encoding="utf-8")  # raw: a plant in a copy
    anchor = "    public init(url: URL"
    assert code.count(anchor) == 1, f"{path.name} no longer has one `{anchor}`"
    path.write_text(code.replace(anchor, text + anchor), encoding="utf-8")


def test_a_url_typed_through_its_module_across_white_space_is_refused(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """T10 (fault F03): Swift compiles `Foundation .URL` and `Foundation` with `.URL` on the next line (the
    Tester checked both with `swiftc -typecheck`); the wave's test read only `Foundation.URL`."""
    path = _store_copy(tmp_path, monkeypatch, "StandingsStore.swift")
    _plant_before_init(path, "    var probe: Foundation\n        .URL? { nil }\n\n")
    with pytest.raises(AssertionError, match=r"StandingsStore\.swift matches `\\bFoundation"):
        hints._assert_the_client_has_no_way_off_the_device()


@pytest.mark.parametrize("store", ["FrontDoor.swift", "StandingsStore.swift"])
def test_a_second_copy_of_a_stores_one_read_is_refused(
        store: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """T11 (fault F06): D-198 clause 5 permits the guard and its read as ONE expression in each store, and the
    pin's own rule is "each occurring exactly once"; a second, live copy was planted by no test."""
    path = _store_copy(tmp_path, monkeypatch, store)
    guard = "guard url.isFileURL,\n              let data = try? Data(contentsOf: url),"
    _plant_before_init(path, f"    func probe() -> Data? {{\n        {guard}\n              !data.isEmpty\n"
                             "        else { return nil }\n        return data\n    }\n\n")
    with pytest.raises(AssertionError, match="exactly once"):
        hints._assert_the_client_has_no_way_off_the_device()
