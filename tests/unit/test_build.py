"""M7-W1 — the production build entry point (REQ-ING-012, REQ-ING-013).

Every test here drives `build()` or `main()`, the real entry points, rather than re-implementing
the pipeline (V4C-50). The failure tests are the point of the wave: a builder that succeeds while
leaving a stage empty produces an artifact that answers every query 200-with-no-picks, which is the
defect M6 shipped and M7 exists to end.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from app.clients.fakes import FakeRawSource
from app.workflows import build as build_mod
from app.workflows.build import MINIMUM_MODELS_REGISTERED, BuildError, build, main
from app.workflows.ingest import ingest_aider, ingest_litellm, ingest_swebench
from app.workflows.schema import connect
from app.workflows.sources import RemoteSource

PRICING = json.dumps(
    {
        "gpt-5": {"mode": "chat", "input_cost_per_token": 1.25e-06, "output_cost_per_token": 1e-05},
        "gpt-5-nano": {
            "mode": "chat",
            "input_cost_per_token": 5e-08,
            "output_cost_per_token": 4e-07,
        },
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
AIDER = json.dumps(
    [
        {"model": "gpt-5 (high)", "pass_rate_2": 61.0, "edit_format": "diff"},
        {"model": "claude-4-5-opus", "pass_rate_2": 70.5, "edit_format": "diff"},
    ]
)

PLANS_YAML = Path("data/plans.yaml").read_text(encoding="utf-8")
ROSTERS_YAML = Path("data/rosters.yaml").read_text(encoding="utf-8")


def _sources(
    *, pricing: str | None = PRICING, swebench: str | None = SWEBENCH, aider: str | None = AIDER
) -> tuple[RemoteSource, ...]:
    """The real RemoteSource shape, carrying fakes instead of the network."""
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
            client=lambda: FakeRawSource("swebench", swebench),
            ingest=ingest_swebench,
            parse=lambda _: ([], 0),
            minimum_rows=1,
        ),
        RemoteSource(
            name="aider",
            client=lambda: FakeRawSource("aider", aider),
            ingest=ingest_aider,
            parse=lambda _: ([], 0),
            minimum_rows=1,
        ),
    )


def _build(conn: sqlite3.Connection, **kw: object) -> build_mod.BuildReport:
    params: dict[str, object] = {
        "plans_yaml": PLANS_YAML,
        "rosters_yaml": ROSTERS_YAML,
        "sources": _sources(),
        "minimum_models": 2,
    }
    params.update(kw)
    return build(conn, **params)  # type: ignore[arg-type]


# --- REQ-ING-012: the entry point builds a servable artifact -----------------------------------


def test_build_produces_an_artifact_that_can_actually_answer() -> None:
    """The criterion is not 'the build ran'; it is that the result serves.

    px_median is asserted explicitly because it is the table whose emptiness makes rank.py's JOIN
    return zero rows and the API answer 200 with no picks.
    """
    conn = connect(":memory:")
    report = _build(conn)

    assert report.price_models > 0
    assert report.verified["px_median"] > 0
    assert report.verified["models"] > 0
    assert report.verified["pricing"] > 0
    assert report.verified["scores"] > 0
    assert report.plans_stored > 0
    assert report.rosters_stored > 0


def test_counts_are_read_back_from_the_database_not_from_the_writers() -> None:
    """Trap 3: a builder that reports what it *intended* to write cannot detect a lost write."""
    conn = connect(":memory:")
    report = _build(conn)

    for table, counted in report.verified.items():
        live = conn.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
        assert counted == live, f"{table}: report said {counted}, database holds {live}"


def test_the_default_model_floor_is_not_weakened_by_tests_lowering_it() -> None:
    """These tests pass minimum_models=2; production must still refuse a collapsed registry."""
    assert MINIMUM_MODELS_REGISTERED == 20


# --- REQ-ING-013: every partial outcome fails LOUD ----------------------------------------------


def test_a_source_that_stores_nothing_fails_the_build() -> None:
    conn = connect(":memory:")
    with pytest.raises(BuildError, match="below its floor"):
        _build(conn, sources=_sources(aider=json.dumps([])))


def test_an_unreachable_source_fails_the_build_rather_than_being_skipped() -> None:
    """W-024's shape: arena is down. The build must stop, not quietly produce less evidence."""
    conn = connect(":memory:")
    with pytest.raises(BuildError, match="dependency unusable"):
        _build(conn, sources=_sources(aider=None))


def test_an_unbuilt_px_median_fails_the_build() -> None:
    """REQ-ING-013's headline failure mode, added by the Stage-3b Tester (M7-W1 fault injection).

    Trap 1 of the plan, stated exactly: `rank.py` JOINs `px_median`, so an empty table yields zero
    rows and `/v1` answers 200 with no picks. Every other test in this file builds an artifact whose
    medians happen to be non-empty, which means the guard at `build.py:303` was never executed —
    removing it left the suite fully green. This test forces the condition: no pricing source, so
    `build_price_medians` has nothing to compute, and the build must refuse rather than hand back a
    report whose `price_models` is 0.
    """
    conn = connect(":memory:")
    pricing_free = tuple(s for s in _sources() if s.name != "litellm")
    with pytest.raises(BuildError, match="price medians built 0 models"):
        _build(conn, sources=pricing_free)


def test_a_median_writer_that_reports_success_without_writing_is_caught(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The read-back floor is a control, not a comment: prove it can fire (Trap 3).

    `build.py:310-313` re-counts the artifact's tables because a writer that reports what it
    *intended* to write cannot detect a lost write. Nothing exercised it — the tuple could be
    emptied of `px_median` and the suite stayed green. Here the median stage claims 7 models and
    writes none, which is the only shape that distinguishes the read-back check from the
    `price_models <= 0` check above it.
    """
    monkeypatch.setattr(build_mod, "build_price_medians", lambda _conn: 7)
    conn = connect(":memory:")
    with pytest.raises(BuildError, match="px_median is empty in the built artifact"):
        _build(conn)


def test_a_failed_optional_source_names_the_surface_it_blinds() -> None:
    """D-121's whole mechanism, which had no citing test (build.py:243-247 was uncovered).

    A REQUIRED source that fails raises; an OPTIONAL one must instead be NAMED in
    `required_operator_actions`, in surface terms. Dropping the `missing.append` entirely — the
    optional source vanishing without trace — left the suite green, which is the exact silence
    D-121 says it is permitted only because it does not happen.
    """
    conn = connect(":memory:")
    optional_arena = RemoteSource(
        name="arena",
        client=lambda: FakeRawSource("arena", None),
        ingest=ingest_aider,
        parse=lambda _: ([], 0),
        minimum_rows=1,
        required=False,
    )
    report = _build(conn, sources=(*_sources(), optional_arena))

    actions = " ".join(report.required_operator_actions)
    assert "arena" in actions, "an optional source that failed vanished from the report"
    assert "assistant" in actions, "the blinded SURFACE must be named, not just the source"


def test_an_empty_source_list_is_refused() -> None:
    conn = connect(":memory:")
    with pytest.raises(BuildError, match="no evidence sources configured"):
        _build(conn, sources=())


def test_a_collapsed_registry_fails_the_build() -> None:
    conn = connect(":memory:")
    with pytest.raises(BuildError, match="registry drift"):
        _build(conn, minimum_models=MINIMUM_MODELS_REGISTERED)


def test_empty_plans_fail_the_build() -> None:
    conn = connect(":memory:")
    with pytest.raises(BuildError, match="plan ingest"):
        _build(conn, plans_yaml="plans: []\n")


def test_a_source_error_is_not_swallowed_into_a_success() -> None:
    """SourceError must surface as a BuildError, never as a report with fewer sources."""
    conn = connect(":memory:")
    with pytest.raises(BuildError):
        _build(conn, sources=_sources(pricing=None))


def test_build_error_names_the_operator_action_not_a_stack_trace() -> None:
    conn = connect(":memory:")
    with pytest.raises(BuildError) as exc:
        _build(conn, sources=_sources(aider=json.dumps([])))
    message = str(exc.value)
    assert "aider" in message
    assert "shape has changed" in message


# --- the CLI (REQ-ING-012's runnable half) ------------------------------------------------------


def test_cli_reports_three_when_a_surface_lost_its_evidence(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exit 3 is 'built but NOT servable' — the D-120 contract this module deliberately mirrors.

    With no --epoch-dir the artifact is real and usable for coding, and agentic-coding has no
    primary evidence. That is not a success and it is not a failure; it is exactly what 3 means.
    """
    monkeypatch.setattr(build_mod, "REMOTE_SOURCES", _sources())
    monkeypatch.setattr(build_mod, "MINIMUM_MODELS_REGISTERED", 2)
    target = tmp_path / "built.db"

    code = main(["--db", str(target)])

    assert code == 3
    assert target.is_file()
    payload = json.loads(capsys.readouterr().out)
    assert payload["built"] is True
    assert payload["verified_from_artifact"]["px_median"] > 0
    assert any("agentic-coding" in a for a in payload["required_operator_actions"])


def test_cli_reports_zero_when_nothing_is_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The 0 path must be reachable, or 3 would be the only outcome and mean nothing."""
    monkeypatch.setattr(build_mod, "REMOTE_SOURCES", _sources())
    monkeypatch.setattr(build_mod, "LOCAL_BUNDLES", ())
    monkeypatch.setattr(build_mod, "MINIMUM_MODELS_REGISTERED", 2)
    target = tmp_path / "clean.db"

    code = main(["--db", str(target)])

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["required_operator_actions"] == []


def test_cli_artifact_reopened_from_disk_holds_what_the_payload_claims(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """REQ-ING-012's acceptance sentence, taken literally: read the counts back OUT of the FILE.

    `_read_back` counts through the SAME connection the build wrote on, so every existing assertion
    about "the artifact" is really an assertion about an in-flight transaction. Deleting
    `conn.commit()` at build.py:307 — and even replacing it with `conn.rollback()` — left the whole
    suite green. This test re-opens the closed file read-only, which is the only vantage point a
    serving process ever has.
    """
    monkeypatch.setattr(build_mod, "REMOTE_SOURCES", _sources())
    monkeypatch.setattr(build_mod, "MINIMUM_MODELS_REGISTERED", 2)
    target = tmp_path / "durable.db"

    assert main(["--db", str(target)]) == 3
    claimed = json.loads(capsys.readouterr().out)["verified_from_artifact"]

    reopened = sqlite3.connect(f"file:{target}?mode=ro", uri=True)
    try:
        for table, count in claimed.items():
            live = reopened.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
            assert live == count, f"{table}: payload claimed {count}, the FILE holds {live}"
        assert claimed["px_median"] > 0
    finally:
        reopened.close()


def test_cli_exit_three_fires_on_a_single_missing_action(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """One blinded surface is already exit 3. Two is not the threshold; any is.

    Every existing exit-3 test leaves BOTH bundles missing, so a mutant demanding more than one
    action before reporting 3 stayed green — and the single-missing-source case is the one D-121
    actually describes.
    """
    monkeypatch.setattr(build_mod, "REMOTE_SOURCES", _sources())
    monkeypatch.setattr(build_mod, "LOCAL_BUNDLES", build_mod.LOCAL_BUNDLES[:1])
    monkeypatch.setattr(build_mod, "MINIMUM_MODELS_REGISTERED", 2)

    assert main(["--db", str(tmp_path / "one.db")]) == 3
    assert len(json.loads(capsys.readouterr().out)["required_operator_actions"]) == 1


def test_cli_epoch_dir_argument_actually_reaches_the_bundle_stage(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """`--epoch-dir` is a documented operator control; nothing proved it was wired.

    Replacing the argument with a hard-coded `None` left the suite green, because the only
    difference the two paths produce is WHICH sentence lands in `required_operator_actions`. The
    directory the operator named must appear in the report, or the flag is decoration.
    """
    monkeypatch.setattr(build_mod, "REMOTE_SOURCES", _sources())
    monkeypatch.setattr(build_mod, "MINIMUM_MODELS_REGISTERED", 2)
    bundle_dir = tmp_path / "epoch-bundle"
    bundle_dir.mkdir()

    assert main(["--db", str(tmp_path / "e.db"), "--epoch-dir", str(bundle_dir)]) == 3
    actions = " ".join(json.loads(capsys.readouterr().out)["required_operator_actions"])
    assert str(bundle_dir) in actions, "--epoch-dir never reached the bundle stage"


def test_cli_leaves_no_half_built_artifact_behind(tmp_path: Path,
                                                  capsys: pytest.CaptureFixture[str],
                                                  monkeypatch: pytest.MonkeyPatch) -> None:
    """A failed build that leaves a file behind is worse than one that leaves nothing.

    The file would be schema-valid, partially populated, and indistinguishable from a good artifact
    to anything that checks for existence — which is what /health did before M6's closure.
    """
    monkeypatch.setattr(build_mod, "REMOTE_SOURCES", _sources(aider=None))
    monkeypatch.setattr(build_mod, "MINIMUM_MODELS_REGISTERED", 2)
    target = tmp_path / "broken.db"

    code = main(["--db", str(target)])

    assert code == 2
    assert not target.exists(), "a failed build left a partially-populated database behind"
    assert json.loads(capsys.readouterr().out)["built"] is False


def test_cli_refuses_to_overwrite_without_force(tmp_path: Path,
                                                capsys: pytest.CaptureFixture[str]) -> None:
    """V3C-06/53: destructive defaults stay OFF."""
    target = tmp_path / "existing.db"
    target.write_text("do not clobber me", encoding="utf-8")

    code = main(["--db", str(target)])

    assert code == 2
    assert "--force" in capsys.readouterr().out
    assert target.read_text(encoding="utf-8") == "do not clobber me"


def test_cli_refuses_a_missing_input_file(tmp_path: Path,
                                          capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["--db", str(tmp_path / "x.db"), "--rosters", str(tmp_path / "nope.yaml")])
    assert code == 2
    assert "rosters file not found" in capsys.readouterr().out


def test_read_back_refuses_a_table_name_it_cannot_vouch_for() -> None:
    """The identifier guard is a control, not a comment: prove it can fire."""
    conn = connect(":memory:")
    conn.execute('CREATE TABLE "weird-name!" (a int)')
    with pytest.raises(BuildError, match="unexpected name"):
        build_mod._read_back(conn)


# --- local bundles (D-101): read, never fetched, and never silently skipped -------------------


def test_a_missing_bundle_directory_is_reported_not_skipped() -> None:
    """The defect this stage was added for: agentic-coding answered empty and nothing said why."""
    conn = connect(":memory:")
    report = _build(conn, bundle_dir=None)

    actions = " ".join(report.required_operator_actions)
    assert "epoch_deepswe_external" in actions
    assert "agentic-coding" in actions, "the blinded SURFACE must be named, not just the source"


def test_a_bundle_directory_without_the_allowlisted_files_is_reported(tmp_path: Path) -> None:
    """An empty directory is a missing bundle, not an empty ingest."""
    conn = connect(":memory:")
    report = _build(conn, bundle_dir=tmp_path)

    assert report.required_operator_actions
    assert "agentic-coding" in " ".join(report.required_operator_actions)


def test_the_blinded_surface_list_is_derived_from_categories_not_typed() -> None:
    """Change a category's primary source and the report must follow without editing build.py."""
    from app.workflows.categories import CATEGORIES

    actions = build_mod._surfaces_left_without_evidence(["arena: down"])
    expected = sorted(t for t, s in CATEGORIES.items() if s.primary_source == "arena")
    assert expected, "fixture assumption: some surface must name arena"
    for surface in expected:
        assert surface in actions[0]


def test_the_bundles_parameter_is_honoured_over_the_module_registry(tmp_path: Path) -> None:
    """The injection point this fix ADDED, which nothing proved was wired.

    Added by the Stage-3b Tester at re-review. `build()` gained `bundles=` precisely so the local
    bundle SUCCESS path could be driven through the real entry point — yet replacing the forwarded
    argument with a hard-coded `None` left the whole suite green, because every bundle test
    monkeypatches `build_mod.LOCAL_BUNDLES` instead and would pass either way. An injection point
    that cannot be shown to inject is the defect this module's own docstring calls the project's
    most-repeated one.
    """
    from app.workflows.ingest import SourceReport
    from app.workflows.sources import LocalBundle

    class _Client:
        def __init__(self, _dir: object, *, last_verified: str) -> None:
            self.last_verified = last_verified

    injected = LocalBundle(
        name="epoch_deepswe_external",
        client_type=_Client,
        ingest=lambda *_a, **_k: SourceReport(source="injected-bundle", stored=4, skipped=0),
        reason="fixture",
    )
    conn = connect(":memory:")
    report = _build(conn, bundle_dir=tmp_path, bundles=(injected,))

    assert report.required_operator_actions == [], (
        "the module registry was used instead of the injected bundles"
    )
    assert any(r.source == "injected-bundle" and r.stored == 4 for r in report.sources)


def test_an_unknown_failed_source_still_reports_rather_than_vanishing() -> None:
    """A source no category names must not produce an empty action list."""
    actions = build_mod._surfaces_left_without_evidence(["not-a-real-source: down"])
    assert len(actions) == 1
    assert "not-a-real-source" in actions[0]
