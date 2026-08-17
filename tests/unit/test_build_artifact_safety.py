"""M7-W1 — the artifact is never destroyed and never half-written (REQ-ING-013).

These guard the two BLOCKING findings the security seat measured, and they exist as their own file
because a fix inherits the risk class of the bug it fixes (V4C-50) — both bugs destroyed or
fabricated the artifact this milestone exists to produce, so their tests get the same weight as the
feature's.

  * BLOCKING-1: `--force` deleted the target BEFORE any work, so any mid-build failure left the
    operator with nothing, having had a working 970 KB artifact seconds earlier.
  * BLOCKING-2: an `AttributeError` from an upstream payload escaped every except clause and left
    a schema-valid, `px_median`-empty database at the target — Trap 1's artifact, produced by the
    builder written to prevent it.

Both had one root: the target WAS the workspace. The tests below pin the property that replaced it
— the target is only ever swapped in for a database that finished.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from app.clients.fakes import FakeRawSource
from app.clients.protocols import SourceError
from app.workflows import build as build_mod
from app.workflows.build import main
from app.workflows.ingest import ingest_aider, ingest_litellm, ingest_swebench
from app.workflows.sources import LocalBundle, RemoteSource

PRICING = json.dumps(
    {
        "gpt-5": {"mode": "chat", "input_cost_per_token": 1.25e-06, "output_cost_per_token": 1e-05},
        "claude-4-5-opus": {
            "mode": "chat",
            "input_cost_per_token": 5e-06,
            "output_cost_per_token": 2.5e-05,
        },
    }
)
SWEBENCH = json.dumps(
    {
        "leaderboards": [
            {
                "name": "Verified",
                "results": [
                    {
                        "name": "live-SWE-agent + GPT-5",
                        "resolved": 74.1,
                        "date": "2025-12-01",
                        "logs": True,
                        "trajs": True,
                    },
                    {
                        "name": "live-SWE-agent + Claude 4.5 Opus",
                        "resolved": 79.2,
                        "date": "2025-12-15",
                        "logs": True,
                        "trajs": True,
                    },
                ],
            }
        ]
    }
)
AIDER = json.dumps([{"model": "gpt-5 (high)", "pass_rate_2": 61.0, "edit_format": "diff"}])


def _sources(*, pricing: str | None = PRICING) -> tuple[RemoteSource, ...]:
    return (
        RemoteSource(
            name="litellm",
            client=lambda: FakeRawSource("litellm", pricing),
            ingest=ingest_litellm,
            parse=lambda _: ([], 0),
            minimum_rows=1,
        ),
        RemoteSource(
            name="swebench",
            client=lambda: FakeRawSource("swebench", SWEBENCH),
            ingest=ingest_swebench,
            parse=lambda _: ([], 0),
            minimum_rows=1,
        ),
        RemoteSource(
            name="aider",
            client=lambda: FakeRawSource("aider", AIDER),
            ingest=ingest_aider,
            parse=lambda _: ([], 0),
            minimum_rows=1,
        ),
    )


@pytest.fixture(autouse=True)
def _offline(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test here drives main(); none of them may touch the network."""
    monkeypatch.setattr(build_mod, "REMOTE_SOURCES", _sources())
    monkeypatch.setattr(build_mod, "LOCAL_BUNDLES", ())
    monkeypatch.setattr(build_mod, "MINIMUM_MODELS_REGISTERED", 2)


def _good_artifact(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> Path:
    target = tmp_path / "advisor.db"
    assert main(["--db", str(target)]) == 0
    capsys.readouterr()
    return target


# --- BLOCKING-1: a failed rebuild must not cost the operator the artifact they had ---------------


def test_a_failed_rebuild_leaves_the_previous_artifact_untouched(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The measured scenario: 970 KB working database, --force, one failure, nothing left."""
    target = _good_artifact(tmp_path, capsys)
    before_bytes = target.read_bytes()
    before_mtime = target.stat().st_mtime

    monkeypatch.setattr(build_mod, "REMOTE_SOURCES", _sources(pricing=None))
    code = main(["--db", str(target), "--force"])

    assert code == 2
    assert target.exists(), "a failed rebuild destroyed the artifact it was replacing"
    assert target.read_bytes() == before_bytes, "the artifact was modified by a failed build"
    assert target.stat().st_mtime == before_mtime


def test_a_failed_first_build_leaves_no_file_at_the_target(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The other direction: nothing partial may be mistaken for a finished artifact."""
    monkeypatch.setattr(build_mod, "REMOTE_SOURCES", _sources(pricing=None))
    target = tmp_path / "never.db"

    assert main(["--db", str(target)]) == 2
    assert not target.exists()
    assert json.loads(capsys.readouterr().out)["built"] is False


def test_no_workspace_file_survives_either_outcome(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The temp file is an implementation detail and must not become operator litter."""
    target = _good_artifact(tmp_path, capsys)
    monkeypatch.setattr(build_mod, "REMOTE_SOURCES", _sources(pricing=None))
    main(["--db", str(target), "--force"])
    capsys.readouterr()

    leftovers = [p.name for p in tmp_path.iterdir() if p.name != target.name]
    assert not leftovers, f"build left temporary files behind: {leftovers}"


def test_a_successful_rebuild_replaces_the_artifact_and_leaves_nothing_behind(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The other half of the temp-then-rename property, which had no test at re-review.

    Added by the Stage-3b Tester. Every test above proves the OLD artifact SURVIVES a failure.
    None proved the new one is actually INSTALLED on success, so three mutants stayed green:
    keeping the stale artifact and discarding the fresh workspace, copying instead of renaming
    (leaving a 970 KB `.building` file behind on every successful run), and reporting the
    workspace path to the operator as if it were the artifact.

    `test_no_workspace_file_survives_either_outcome` cannot see the leak because it runs a
    success and then a FAILURE, and the failure path unlinks the workspace the success left.
    """
    target = _good_artifact(tmp_path, capsys)
    first = sqlite3.connect(f"file:{target}?mode=ro", uri=True)
    try:
        before_rows = first.execute("SELECT count(*) FROM scores").fetchone()[0]
    finally:
        first.close()

    richer = json.dumps(
        [
            {"model": "gpt-5 (high)", "pass_rate_2": 61.0, "edit_format": "diff"},
            {"model": "claude-4-5-opus", "pass_rate_2": 70.5, "edit_format": "diff"},
        ]
    )
    monkeypatch.setattr(
        build_mod,
        "REMOTE_SOURCES",
        (
            *_sources()[:2],
            RemoteSource(
                name="aider",
                client=lambda: FakeRawSource("aider", richer),
                ingest=ingest_aider,
                parse=lambda _: ([], 0),
                minimum_rows=1,
            ),
        ),
    )

    assert main(["--db", str(target), "--force"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["path"] == str(target), "the operator was told the workspace path, not the target"
    assert [p.name for p in tmp_path.iterdir()] == [target.name], (
        "a SUCCESSFUL build left a workspace file behind"
    )

    after = sqlite3.connect(f"file:{target}?mode=ro", uri=True)
    try:
        after_rows = after.execute("SELECT count(*) FROM scores").fetchone()[0]
    finally:
        after.close()
    assert after_rows > before_rows, (
        "the --force rebuild reported success but the artifact still holds the OLD evidence"
    )


def test_a_stale_workspace_from_a_killed_run_is_never_reused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`except BaseException` cannot catch SIGKILL, so a stale workspace IS reachable.

    Added by the Stage-3b Tester: deleting the pre-build `workspace.unlink(missing_ok=True)` left
    the suite green, and the consequence is precise — `connect()` applies the DDL idempotently, so
    a previous run's half-written file is opened, built ON TOP of, and then renamed onto the
    target. That is a partially-populated artifact reaching the operator through a door the
    temp-then-rename fix opened itself.
    """
    target = tmp_path / "resumed.db"
    stale = target.with_name(target.name + ".building")
    poisoned = sqlite3.connect(stale)
    try:
        poisoned.execute("CREATE TABLE poison_marker (a int)")
        poisoned.execute("INSERT INTO poison_marker VALUES (1)")
        poisoned.commit()
    finally:
        poisoned.close()

    assert main(["--db", str(target)]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert "poison_marker" not in payload["verified_from_artifact"], (
        "the build resumed inside a stale workspace instead of starting clean"
    )

    # AMENDED by the lead agent after the security seat's BLOCKING-4, with the change flagged back
    # to the Tester seat rather than made quietly. This test originally also asserted the stale
    # file was DELETED, which was the right assertion against a deterministic `<target>.building`
    # workspace — there, the stale file and this run's workspace were the same path.
    #
    # The workspace name is now unique per run (`tempfile.mkstemp`), because the deterministic name
    # let two overlapping builds share one path: build A published build B's truncated database
    # while reporting "built": true with 73 models read back. Under unique names this run cannot
    # know whether `resumed.db.building` is a dead run's litter or a LIVE sibling build's
    # workspace, and deleting it would reintroduce exactly the race that was just closed.
    #
    # So the property this test pins is the safety one, which is unchanged and is what its name
    # says: a stale workspace is never built inside. The litter is real, minor, and recorded as
    # W-028 rather than traded for a corruption bug.
    assert stale.exists(), (
        "the build deleted a workspace path it does not own; under unique per-run names that file "
        "may belong to a live sibling build (see W-028)"
    )
    reopened = sqlite3.connect(f"file:{target}?mode=ro", uri=True)
    try:
        tables = {r[0] for r in reopened.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        reopened.close()
    assert "poison_marker" not in tables, "a killed run's leftovers shipped inside the artifact"


# --- BLOCKING-2: an exception nobody declared must not produce an artifact ----------------------


def test_an_undeclared_exception_leaves_no_artifact_behind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The exact escape the security seat reproduced, generalised.

    `AttributeError` was one instance; the class is 'anything outside the except tuple'. The
    builder now cleans up under BaseException, so the artifact is safe even from a bug in itself.
    """

    def _explode(*_args: object, **_kwargs: object) -> None:
        raise AttributeError("'list' object has no attribute 'items'")

    monkeypatch.setattr(build_mod, "reconcile", _explode)
    target = tmp_path / "poisoned.db"

    with pytest.raises(AttributeError):
        main(["--db", str(target)])

    assert not target.exists(), "an undeclared exception left a half-built database at the target"
    assert not list(tmp_path.iterdir()), "an undeclared exception left a workspace file behind"


def test_a_keyboard_interrupt_leaves_no_artifact_behind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """BaseException, not Exception: an interrupted build must not ship either."""

    def _interrupt(*_args: object, **_kwargs: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(build_mod, "reconcile", _interrupt)
    target = tmp_path / "interrupted.db"

    with pytest.raises(KeyboardInterrupt):
        main(["--db", str(target)])

    assert not target.exists()
    assert not list(tmp_path.iterdir())


# --- the remaining uncovered floors the Tester's mutants walked through -------------------------


def test_a_curated_stage_that_stores_zero_fails_the_build(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """M13 stayed green: the `stored <= 0` floor in `_ingest_curated` had never executed.

    The existing test reached the SourceError branch instead, so the floor beside it was decoration.
    """
    from app.workflows.ingest import SourceReport

    monkeypatch.setattr(
        build_mod,
        "ingest_rosters",
        lambda *_a, **_k: SourceReport(source="rosters", stored=0, skipped=0),
    )
    target = tmp_path / "hollow.db"

    assert main(["--db", str(target)]) == 2
    assert not target.exists()


def test_a_bundle_that_stores_zero_rows_is_a_missing_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """M18/M47 stayed green: a bundle reporting success with nothing in it counted as ingested."""
    from app.workflows.ingest import SourceReport

    class _EmptyClient:
        def __init__(self, _dir: object, *, last_verified: str) -> None:
            self.last_verified = last_verified

    monkeypatch.setattr(
        build_mod,
        "LOCAL_BUNDLES",
        (
            LocalBundle(
                name="epoch_deepswe_external",
                client_type=_EmptyClient,
                ingest=lambda *_a, **_k: SourceReport(source="x", stored=0, skipped=0),
                reason="fixture",
            ),
        ),
    )
    target = tmp_path / "emptybundle.db"

    assert main(["--db", str(target), "--epoch-dir", str(tmp_path)]) == 3
    actions = json.loads(capsys.readouterr().out)["required_operator_actions"]
    assert any("agentic-coding" in a for a in actions)


def test_a_bundle_that_ingests_successfully_is_counted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """M21 stayed green: the bundle SUCCESS path executed in no test at all.

    Dropping `results.append(result)` silently discarded both Epoch sources, returned exit 0 with
    an empty action list, and put agentic-coding back to zero picks — the state this wave's third
    commit exists to have fixed.
    """
    from app.workflows.ingest import SourceReport

    class _Client:
        def __init__(self, _dir: object, *, last_verified: str) -> None:
            self.last_verified = last_verified

    monkeypatch.setattr(
        build_mod,
        "LOCAL_BUNDLES",
        (
            LocalBundle(
                name="epoch_deepswe_external",
                client_type=_Client,
                ingest=lambda *_a, **_k: SourceReport(source="deepswe", stored=7, skipped=0),
                reason="fixture",
            ),
        ),
    )
    target = tmp_path / "withbundle.db"

    assert main(["--db", str(target), "--epoch-dir", str(tmp_path)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["required_operator_actions"] == []
    assert any(s["source"] == "deepswe" and s["stored"] == 7 for s in payload["sources"]), (
        "a successful bundle ingest is missing from the report"
    )


def test_a_source_error_from_a_bundle_does_not_kill_the_build(tmp_path: Path,
                                                              monkeypatch: pytest.MonkeyPatch,
                                                              capsys: pytest.CaptureFixture[str]) -> None:
    """A bundle is degradable like an optional source, not fatal like a required one."""

    class _Broken:
        def __init__(self, _dir: object, *, last_verified: str) -> None:
            msg = "missing CSV in local unpacked bundle"
            raise SourceError(msg)

    monkeypatch.setattr(
        build_mod,
        "LOCAL_BUNDLES",
        (
            LocalBundle(
                name="epoch_deepswe_external",
                client_type=_Broken,
                ingest=lambda *_a, **_k: None,
                reason="fixture",
            ),
        ),
    )
    target = tmp_path / "brokenbundle.db"

    assert main(["--db", str(target), "--epoch-dir", str(tmp_path)]) == 3
    assert target.exists(), "a degradable bundle failure destroyed the artifact"
    assert any(
        "agentic-coding" in a
        for a in json.loads(capsys.readouterr().out)["required_operator_actions"]
    )


def test_the_read_back_floor_rejects_an_empty_core_table(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Trap 3's floor: the read-back check itself had no citing test and its mutant survived."""
    monkeypatch.setattr(build_mod, "_read_back", lambda _conn: {"models": 0, "px_median": 5})
    target = tmp_path / "lying.db"

    assert main(["--db", str(target)]) == 2
    assert not target.exists()


def test_source_floors_are_pinned_by_value_not_only_by_sign() -> None:
    """M41 stayed green: raising swebench's floor to 10 000 changed nothing that any test saw."""
    from app.workflows.sources import REMOTE_SOURCES

    floors = {s.name: s.minimum_rows for s in REMOTE_SOURCES}
    assert floors["litellm"] == 100
    assert floors["openrouter"] == 50
    assert floors["swebench"] == 1
    assert floors["aider"] == 1
    assert floors["arena"] == 1


def test_building_over_a_directory_fails_cleanly(tmp_path: Path,
                                                 capsys: pytest.CaptureFixture[str]) -> None:
    """MINOR-3: `--db <a directory> --force` raised PermissionError and exited 1, undeclared."""
    directory = tmp_path / "adirectory"
    directory.mkdir()

    code = main(["--db", str(directory), "--force"])

    assert code == 2, "a directory target must fail with the declared code, not a traceback"
    assert "error" in json.loads(capsys.readouterr().out)


def test_a_rejected_optional_source_leaves_none_of_its_rows_behind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """MINOR-1: a source we REJECT must not still be present in the artifact.

    `ingest` writes before the floor is evaluated. For an optional source the failure is swallowed,
    so without a savepoint the partial rows were committed anyway — and then the serving path sees
    the source as PRESENT and never fires the "no evidence source" disclosure, answering
    confidently from truncated evidence. That defeats the very branch D-121 stakes itself on.
    """
    # The rejected source is named `deepswe`, NOT `aider`. The first version of this test
    # registered a SECOND source called `aider` alongside the healthy one, and `reset_source`
    # deletes by name — so a rollback and a "destroyed the healthy source's rows" bug produced
    # identical output and the assertion could not tell them apart. Caught by the code-review seat.
    hollow = json.dumps(
        {
            "leaderboards": [
                {
                    "name": "Verified",
                    "results": [
                        {
                            "name": "live-SWE-agent + GPT-5",
                            "resolved": 40.0,
                            "date": "2025-11-01",
                            "logs": True,
                            "trajs": True,
                        }
                    ],
                }
            ]
        }
    )
    monkeypatch.setattr(
        build_mod,
        "REMOTE_SOURCES",
        (
            *_sources(),
            RemoteSource(
                name="rejected-probe",
                client=lambda: FakeRawSource("rejected-probe", hollow),
                ingest=ingest_swebench,
                parse=lambda _: ([], 0),
                minimum_rows=10_000,  # forces rejection AFTER the rows are written
                required=False,
            ),
        ),
    )
    target = tmp_path / "rolled_back.db"

    assert main(["--db", str(target)]) == 3
    assert "below its floor" in json.dumps(
        json.loads(capsys.readouterr().out)["required_operator_actions"]
    )

    conn = sqlite3.connect(f"file:{target}?mode=ro", uri=True)
    try:
        rejected = conn.execute(
            "SELECT count(*) FROM scores WHERE source = 'rejected-probe'"
        ).fetchone()[0]
        healthy = conn.execute("SELECT count(*) FROM scores WHERE source = 'aider'").fetchone()[0]
    finally:
        conn.close()
    assert rejected == 0, f"a rejected source left {rejected} rows in the artifact"
    assert healthy > 0, "the rollback destroyed a HEALTHY source's rows, which is the other bug"


def test_a_rejected_source_leaves_none_of_its_PRICING_rows_behind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The other table the rollback clears, and the half no test reached.

    Added by the Stage-3b Tester: narrowing the rollback to `("scores",)` alone left the suite
    green, because the only rollback test rejects `aider`, which writes scores and never pricing.
    Pricing is the more consequential half — `build_price_medians` reads it, so a rejected feed's
    prices go on to set the median reference price for every model the artifact ranks. The rows
    are invisible to `source_health` (which reads `scores`), so nothing downstream discloses them.
    """
    monkeypatch.setattr(
        build_mod,
        "REMOTE_SOURCES",
        (
            *_sources(),
            RemoteSource(
                name="litellm_beta",
                client=lambda: FakeRawSource("litellm_beta", PRICING),
                ingest=ingest_litellm,
                parse=lambda _: ([], 0),
                minimum_rows=10_000,  # forces rejection AFTER the pricing rows are written
                required=False,
            ),
        ),
    )
    target = tmp_path / "priced.db"

    assert main(["--db", str(target)]) == 3
    capsys.readouterr()

    conn = sqlite3.connect(f"file:{target}?mode=ro", uri=True)
    try:
        rejected = conn.execute(
            "SELECT count(*) FROM pricing WHERE source = 'litellm_beta'"
        ).fetchone()[0]
        kept = conn.execute("SELECT count(*) FROM pricing WHERE source = 'litellm'").fetchone()[0]
    finally:
        conn.close()

    assert rejected == 0, f"a rejected source left {rejected} pricing rows feeding px_median"
    assert kept > 0, "the rollback took the accepted source's rows with it"


def test_a_rejected_source_leaves_no_pricing_rows_either(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """MR3: narrowing the rollback to `("scores",)` stayed green — pricing had no test.

    A rejected PRICING source's rows would survive into `build_price_medians`, so the artifact's
    reference prices (REQ-CAN-003) would be computed partly from a feed the build declared
    unusable. Different table, same defect as MINOR-1, and it needed its own citing test.
    """
    thin = json.dumps(
        {"solo-model": {"mode": "chat", "input_cost_per_token": 1e-06, "output_cost_per_token": 2e-06}}
    )
    monkeypatch.setattr(
        build_mod,
        "REMOTE_SOURCES",
        (
            *_sources(),
            RemoteSource(
                name="thin-pricing",
                client=lambda: FakeRawSource("thin-pricing", thin),
                ingest=ingest_litellm,
                parse=lambda _: ([], 0),
                minimum_rows=10_000,
                required=False,
            ),
        ),
    )
    target = tmp_path / "pricing_rollback.db"

    assert main(["--db", str(target)]) == 3
    capsys.readouterr()

    conn = sqlite3.connect(f"file:{target}?mode=ro", uri=True)
    try:
        rejected = conn.execute(
            "SELECT count(*) FROM pricing WHERE source = 'thin-pricing'"
        ).fetchone()[0]
        healthy = conn.execute("SELECT count(*) FROM pricing WHERE source = 'litellm'").fetchone()[0]
    finally:
        conn.close()
    assert rejected == 0, f"a rejected pricing source left {rejected} rows for the medians to use"
    assert healthy > 0, "the rollback destroyed the healthy pricing source"
