"""REQ-REF-001/-002/-006 — one refresh cycle.

The cycle is the thing that will run unattended, so every test here asks the question that only
matters once nobody is watching: **what does the live artifact look like afterwards?** A refresh
that fails is fine. A refresh that fails and leaves the product worse than it found it is the
failure this milestone exists to make impossible.

`builder` is injected everywhere and read at call time. Three separate defects in this project have
been an injection point that could not inject — the last one a parameter that existed and never
reached its caller — so these tests genuinely control the build rather than believing they do.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.workflows.refresh import (
    EXIT_FAILED,
    EXIT_PUBLISHED,
    EXIT_REFUSED,
    EXIT_UNCHANGED,
    fingerprint_of,
    refresh,
    serving_summary,
)

from .test_api_v1 import _seeded_db


def _artifact(path: Path, *, top_score: float = 74.5, stamp: str = "t0") -> Path:
    """A servable artifact whose SERVED content is controlled by `top_score`."""
    _seeded_db(path)
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "UPDATE scores SET score = ? WHERE score = (SELECT max(score) FROM scores)",
            (top_score,),
        )
        # `observed_at` moves on every real build and must never reach the fingerprint.
        conn.execute("UPDATE scores SET observed_at = ?", (stamp,))
        conn.commit()
    finally:
        conn.close()
    return path


def _builder(**kwargs):
    """A build that writes a controlled artifact wherever it is told, and reports success."""

    def build(argv: list[str]) -> int:
        target = Path(argv[argv.index("--db") + 1])
        _artifact(target, **kwargs)
        return 0

    return build


# --- REQ-REF-002: "changed" means the content that would be SERVED ------------------------------


def test_two_cycles_against_an_unchanged_upstream_publish_once(tmp_path: Path) -> None:
    """The criterion, taken literally. Without it every cycle is a publish and the comparison is
    decorative — twelve hours apart, forever, swapping a file for an identical one."""
    live = tmp_path / "advisor.db"

    first, code = refresh(live, builder=_builder(top_score=74.5, stamp="t0"))
    assert code == EXIT_PUBLISHED and first.published

    second, code = refresh(live, builder=_builder(top_score=74.5, stamp="LATER"))
    assert code == EXIT_UNCHANGED, f"a second identical cycle published again: {second.reason}"
    assert not second.published
    assert second.live_fingerprint == second.candidate_fingerprint


def test_a_moved_timestamp_is_not_a_change(tmp_path: Path) -> None:
    """`observed_at` moves on EVERY build. A fingerprint that included it would report a change
    every single cycle, which is the same as having no comparison at all."""
    a = _artifact(tmp_path / "a.db", stamp="2026-01-01")
    b = _artifact(tmp_path / "b.db", stamp="2026-12-31")
    assert fingerprint_of(a) == fingerprint_of(b)


def test_a_moved_score_is_a_change(tmp_path: Path) -> None:
    """The other direction, so the fingerprint cannot be satisfied by hashing a constant."""
    a = _artifact(tmp_path / "a.db", top_score=74.5)
    b = _artifact(tmp_path / "b.db", top_score=75.5)
    assert fingerprint_of(a) != fingerprint_of(b)


def test_rounding_noise_below_the_published_precision_is_not_a_change(tmp_path: Path) -> None:
    """D-109 rounds at the output boundary, so a difference nobody can SEE is not a change.

    Without this the cycle would publish on float noise in a price median — a swap of the served
    artifact for one that renders identically.
    """
    a = _artifact(tmp_path / "a.db", top_score=74.5)
    b = _artifact(tmp_path / "b.db", top_score=74.500000001)
    assert fingerprint_of(a) == fingerprint_of(b)


def test_a_surface_going_blind_changes_the_fingerprint(tmp_path: Path) -> None:
    """The single most important thing a refresh could fail to notice.

    W2's refusal rule is built on this: a category that answered an hour ago and answers nothing
    now must be VISIBLE to the comparison, or an unattended cycle will publish the degradation
    quietly and every gate will stay green.
    """
    full = _artifact(tmp_path / "full.db")
    blinded = _artifact(tmp_path / "blind.db")
    conn = sqlite3.connect(blinded)
    try:
        conn.execute("DELETE FROM scores WHERE benchmark = 'SWE-bench Verified'")
        conn.commit()
    finally:
        conn.close()

    before = fingerprint_of(full)
    after = fingerprint_of(blinded)
    assert before is not None and after is not None
    assert before.digest != after.digest, (
        "a surface lost all its evidence and the fingerprint did not move"
    )
    assert after.answering < before.answering, (
        "the answering-surface count must fall when a surface goes blind"
    )


# --- REQ-REF-001: the live artifact is never left worse ------------------------------------------


def test_a_failed_build_leaves_the_live_artifact_untouched(tmp_path: Path) -> None:
    live = _artifact(tmp_path / "advisor.db", top_score=74.5)
    before = live.read_bytes()

    def failing(argv: list[str]) -> int:
        return 2

    outcome, code = refresh(live, builder=failing)

    assert code == EXIT_FAILED
    assert not outcome.published
    assert live.read_bytes() == before, "a failed build changed the artifact it was refreshing"
    assert "untouched" in outcome.reason


def test_a_builder_that_raises_leaves_the_live_artifact_untouched(tmp_path: Path) -> None:
    """A crash is not a return code. The `finally` that removes the candidate must run anyway."""
    live = _artifact(tmp_path / "advisor.db")
    before = live.read_bytes()

    def exploding(argv: list[str]) -> int:
        raise RuntimeError("upstream parser bug")

    with pytest.raises(RuntimeError):
        refresh(live, builder=exploding)

    assert live.read_bytes() == before
    assert not list(tmp_path.glob("*.candidate")), "a crash left a candidate on disk"


def test_no_candidate_file_survives_any_outcome(tmp_path: Path) -> None:
    """Litter the next cycle cannot tell from a live sibling's work is how W-028 happened."""
    live = tmp_path / "advisor.db"
    refresh(live, builder=_builder())
    refresh(live, builder=_builder())
    refresh(live, builder=lambda argv: 2)
    assert not list(tmp_path.glob("*.candidate"))


def test_a_candidate_that_cannot_be_read_back_is_not_published(tmp_path: Path) -> None:
    """A build that reports success and produces something unreadable must not replace a working
    artifact on the strength of its own exit code."""
    live = _artifact(tmp_path / "advisor.db", top_score=74.5)
    before = live.read_bytes()

    def junk(argv: list[str]) -> int:
        Path(argv[argv.index("--db") + 1]).write_bytes(b"not a database" * 100)
        return 0

    outcome, code = refresh(live, builder=junk)

    assert code == EXIT_FAILED
    assert live.read_bytes() == before
    assert "cannot be read back" in outcome.reason


def test_the_first_refresh_on_a_machine_with_no_artifact_publishes(tmp_path: Path) -> None:
    """An absent live artifact is not a failure to compare against; it is the reason to publish."""
    live = tmp_path / "advisor.db"
    outcome, code = refresh(live, builder=_builder())

    assert code == EXIT_PUBLISHED
    assert outcome.live_fingerprint is None
    assert outcome.reason == "first artifact"
    assert live.is_file()


def test_the_candidate_is_built_beside_the_target_so_publishing_is_a_rename(tmp_path: Path) -> None:
    """An atomic rename is only atomic within one filesystem.

    A candidate in the system temp directory would publish by COPY on a machine where /tmp is a
    separate mount, and a copy is exactly the partially-written artifact every guard in `build.py`
    exists to prevent. Asserted on the path the builder is HANDED, because that is what decides it.
    """
    seen: list[Path] = []

    def watching(argv: list[str]) -> int:
        target = Path(argv[argv.index("--db") + 1])
        seen.append(target)
        _artifact(target)
        return 0

    live = tmp_path / "nested" / "advisor.db"
    live.parent.mkdir()
    refresh(live, builder=watching)

    assert seen and seen[0].parent == live.parent, (
        f"the candidate was built in {seen[0].parent} and the target lives in {live.parent}; "
        "publishing across a filesystem boundary is a copy, not a rename"
    )


def test_a_build_that_reports_a_blind_surface_still_publishes(tmp_path: Path) -> None:
    """Exit 3 is D-121 working — an optional source is down and the artifact SAYS so. Treating it
    as a failure would freeze the product for as long as any optional source is unavailable, which
    for this project has been most of a milestone."""
    live = tmp_path / "advisor.db"

    def blind(argv: list[str]) -> int:
        _artifact(Path(argv[argv.index("--db") + 1]))
        return 3

    outcome, code = refresh(live, builder=blind)
    assert code == EXIT_PUBLISHED and outcome.published


# --- REQ-REF-006: the running engine picks up a swap ---------------------------------------------


def test_the_engine_serves_a_replaced_artifact_without_a_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pins behaviour that ALREADY WORKS, which is why this milestone is smaller than it looked.

    Measured by hand on 2026-08-21 before M9 was planned: `advisor.db` was atomically replaced under
    a live engine and the next request returned the new data. The adapter opens a read-only
    connection per request, so a swap lands immediately.

    It is pinned because the whole refresh depends on it and nothing asserted it. Making the adapter
    hold one long-lived connection would be a reasonable-looking optimisation that silently breaks
    every future refresh: the process would keep the replaced file's inode and serve yesterday's
    answer behind a healthy `/health`, which is this project's "restart is not rebuild" defect
    arriving through the front door.
    """
    from fastapi.testclient import TestClient

    from app.adapter import main as adapter

    live = _artifact(tmp_path / "advisor.db", top_score=74.5)
    monkeypatch.setenv("MODEL_RANKING_DB", str(live))
    monkeypatch.setenv("APP_ENV", "test")
    client = TestClient(adapter.app)

    def leader() -> float:
        body = client.get("/v1/recommendations?task=coding&budget=unlimited").json()
        answer = next(a for a in body["answers"] if a["surface"] == "coding")
        return float(answer["picks"][0]["score"])

    assert leader() == pytest.approx(74.5)

    replacement = _artifact(tmp_path / "next.db", top_score=81.25)
    replacement.replace(live)

    assert leader() == pytest.approx(81.2), (
        "the engine kept serving the replaced artifact's data; a refresh would publish into a "
        "process that never reads it"
    )


def test_the_refresh_never_imports_the_serving_adapter() -> None:
    """REQ-REF-007's structural half, asserted at W1 because the boundary is easiest to hold now.

    D-116 keeps ingestion off the serving host. A refresh that imports the adapter — even to borrow
    a two-line helper, which was the actual temptation while writing this module — has reached into
    the serving process, and the separation would then exist only in prose.
    """
    import ast

    source = Path("src/app/workflows/refresh.py").read_text(encoding="utf-8")
    imported: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)

    adapter_imports = sorted(name for name in imported if name.startswith("app.adapter"))
    assert not adapter_imports, (
        f"the refresh imports {adapter_imports}; D-116 keeps ingestion off the serving host and "
        "this is where that boundary is actually enforced"
    )


# --- the five holes my own fault injection found in the tests above ------------------------------


def test_asking_a_corrupt_artifact_what_it_serves_raises_rather_than_answering_empty(
    tmp_path: Path,
) -> None:
    """The layer test. `fingerprint_of` has a second guard, so neither is defended by outcome alone.

    A mutant restoring `except sqlite3.DatabaseError: rows = []` inside `serving_fingerprint`
    survived every outcome-level test, because the probe in `fingerprint_of` caught the junk first.
    Two guards covering each other is good engineering and it is also how both of them get deleted
    one day, each because "the other one handles it". This pins the inner one directly.

    "Every surface is empty" is a perfectly plausible answer, which is exactly what makes it
    dangerous: a corrupt candidate that produces one compares unequal to the live artifact and gets
    PUBLISHED over it.
    """
    junk = tmp_path / "junk.db"
    junk.write_bytes(b"this is definitely not a database" * 200)
    conn = sqlite3.connect(f"file:{junk}?mode=ro", uri=True)
    try:
        with pytest.raises(sqlite3.DatabaseError):
            serving_summary(conn)
    finally:
        conn.close()


def test_a_price_moving_below_the_published_precision_is_not_a_change(tmp_path: Path) -> None:
    """The score half of this was tested and the PRICE half was not.

    A mutant removing the rounding from `blended_per_m` survived, and a price median carries far
    more float noise than a benchmark score does — it is a computed median over live pricing feeds.
    Unrounded, this cycle would publish on a difference no user could ever see.
    """
    def priced(path: Path, in_m: float) -> Path:
        _artifact(path)
        conn = sqlite3.connect(path)
        try:
            conn.execute("UPDATE px_median SET in_m = ?", (in_m,))
            conn.commit()
        finally:
            conn.close()
        return path

    a = priced(tmp_path / "a.db", 3.0)
    b = priced(tmp_path / "b.db", 3.000000001)
    assert fingerprint_of(a) == fingerprint_of(b)

    # And the correction this test produced: the price is published to TWO decimals, so a move of
    # one cent is visible on the screen and MUST be a change. The fingerprint was re-rounding it to
    # one decimal and would have swallowed exactly that.
    # These two values were CHOSEN BY MEASUREMENT, not by arithmetic in my head: they produce
    # blended prices of 8.50 and 8.52 — different at the two decimals the product prints, identical
    # at the one decimal the fingerprint was re-rounding to. An earlier pair (3.0 / 3.08) differed
    # at BOTH precisions, so the test passed and the mutant lived.
    cheap = priced(tmp_path / "cent.db", 3.0)
    dearer = priced(tmp_path / "cent2.db", 3.02)
    assert fingerprint_of(cheap) != fingerprint_of(dearer), (
        "a one-cent move in the published price was fingerprinted as unchanged; the refresh would "
        "never publish a price change a user can read"
    )

    c = priced(tmp_path / "c.db", 9.0)
    assert fingerprint_of(a) != fingerprint_of(c), "a real price move must still be a change"


def test_the_same_rows_under_a_different_surface_are_a_different_fingerprint(
    tmp_path: Path,
) -> None:
    """Why the surface NAME is hashed and not only its rows.

    Without the `surface:<name>:<count>` line the digest is just every row in sorted-surface order,
    so moving a model's evidence from one surface to another — same model, same score, same price —
    produces the identical hash. That is a category silently swapping its content while the refresh
    reports nothing changed, and a mutant deleting that line walked through every other test here.
    """
    def one_row_under(path: Path, benchmark: str) -> Path:
        """Exactly ONE score row in the whole artifact, under the named benchmark.

        The construction has to be this austere to produce a real collision. An earlier version
        moved every SWE-bench row to DeepSWE, which also reorders the surviving rows by score — so
        the digests differed for an incidental reason and the test passed while the mutant lived.
        With a single row and both surfaces otherwise empty, the row-only digest is IDENTICAL in
        both artifacts and only the surface line can tell them apart.
        """
        _artifact(path)
        conn = sqlite3.connect(path)
        try:
            conn.execute("DELETE FROM scores")
            # `effort='high'` on BOTH, because `agentic-coding` ranks at a named effort level and
            # `coding` has no effort policy — so this one row is rankable on either surface and the
            # two artifacts differ ONLY in which surface claims it. Without that the DeepSWE
            # artifact ranked nothing at all, the digests differed for the wrong reason, and the
            # test passed over a live mutant.
            conn.execute(
                "INSERT INTO scores (model_id, raw_name, source, benchmark, metric, score,"
                " harness, effort, source_url, observed_at) VALUES ('claude-4.5-opus',"
                " 'Claude 4.5 Opus', 'swebench', ?, '% resolved', 74.5, 'none', 'high',"
                " 'fixture://x', 't')",
                (benchmark,),
            )
            conn.commit()
        finally:
            conn.close()
        return path

    coding = one_row_under(tmp_path / "coding.db", "SWE-bench Verified")
    agentic = one_row_under(tmp_path / "agentic.db", "DeepSWE")

    # Fixture assumption, asserted: BOTH artifacts must actually rank their one row, or this is
    # "something versus nothing" and proves nothing about surface identity.
    coding_summary = fingerprint_of(coding)
    agentic_summary = fingerprint_of(agentic)
    assert coding_summary is not None and agentic_summary is not None
    assert coding_summary.answering == 1 and agentic_summary.answering == 1, (
        f"the construction is wrong: {coding_summary.answering} and "
        f"{agentic_summary.answering} surfaces answer, and both must be 1"
    )

    assert coding_summary.digest != agentic_summary.digest, (
        "the same evidence under a different surface produced the same fingerprint; a category "
        "could swap its entire content and the refresh would report nothing changed"
    )


def test_a_failed_build_that_leaves_a_READABLE_artifact_is_still_not_published(
    tmp_path: Path,
) -> None:
    """The dangerous shape of a failed build, which the obvious test misses.

    The obvious test uses a builder that returns non-zero and writes nothing — so even without the
    exit-code check the candidate is unreadable and nothing publishes. A build that fails AFTER
    producing something servable is the case that matters, and a mutant deleting the exit-code
    check survived because no test produced one.

    The build's own contract is that a non-zero exit means the artifact must not be trusted, whether
    or not it happens to open.
    """
    live = _artifact(tmp_path / "advisor.db", top_score=74.5)
    before = live.read_bytes()

    def failed_but_readable(argv: list[str]) -> int:
        _artifact(Path(argv[argv.index("--db") + 1]), top_score=99.0)
        return 2

    outcome, code = refresh(live, builder=failed_but_readable)

    assert code == EXIT_FAILED, "a build that reported failure had its artifact published"
    assert not outcome.published
    assert live.read_bytes() == before


@pytest.mark.parametrize(
    ("table", "column", "value"),
    [
        # The displayed model name lives in `models.display`, NOT in `scores.raw_name`. The first
        # version of this test renamed the raw name and failed, which was the test being wrong
        # about where the published value comes from rather than the fingerprint being wrong.
        ("models", "display", "Claude 4.5 Opus RENAMED"),
        ("scores", "harness", "some-other-agent"),
        ("scores", "effort", "low"),
    ],
)
def test_every_published_field_moves_the_fingerprint(
    tmp_path: Path, table: str, column: str, value: str
) -> None:
    """Each field the payload publishes, changed ALONE.

    Fault injection found that dropping `model`, or `harness` and `effort`, from the digest survived
    every other test here — because every other test moves a SCORE, and a score change hides
    whatever else moved with it. A model renamed upstream, or the same score suddenly measured
    under a different harness or at a different effort, is a change a reader sees on the screen and
    the refresh would have published nothing.

    `harness` and `effort` are not decoration: they are what makes a score comparable, and this
    product ranks `agentic-coding` at a named effort level precisely because the number means
    something different without it.
    """
    before = _artifact(tmp_path / "before.db")
    after = _artifact(tmp_path / "after.db")
    conn = sqlite3.connect(after)
    try:
        # The table and column come from this test's own parametrize list, never from input.
        conn.execute(f"UPDATE {table} SET {column} = ?", (value,))
        conn.commit()
    finally:
        conn.close()

    assert fingerprint_of(before) != fingerprint_of(after), (
        f"{column} changed on every row and the fingerprint did not move"
    )


# --- the CLI, which nothing exercised until its coverage said so ---------------------------------


def test_the_cli_prints_exactly_one_json_document(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The outcome is the RESULT and must be parseable on its own.

    The build prints its own report to stdout and so does this command, so the first real run
    produced two concatenated JSON documents and `json.load` failed with "Extra data: line 115".
    A scheduler reading stdout would have got nothing it could act on — from a command whose whole
    purpose is to run unattended.

    The build's report is diagnostics and now goes to stderr, where a log still keeps it.
    """
    import json

    from app.workflows import refresh as refresh_mod

    def noisy(argv: list[str]) -> int:
        print(json.dumps({"built": True, "sources": ["this is the BUILD's report"]}))
        _artifact(Path(argv[argv.index("--db") + 1]))
        return 0

    monkeypatch.setattr(refresh_mod, "build_main", noisy)
    code = refresh_mod.main(["--db", str(tmp_path / "advisor.db")])

    captured = capsys.readouterr()
    assert code == EXIT_PUBLISHED
    parsed = json.loads(captured.out)  # raises if anything else reached stdout
    assert parsed["published"] is True
    assert "BUILD's report" in captured.err, "the build's diagnostics were lost rather than moved"


def test_the_cli_passes_its_build_flags_through(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`--epoch-dir` is required for six of the nine surfaces to have any evidence at all.

    A refresh that silently dropped it would build a candidate missing most of the product and —
    until W2's refusal rule exists — publish it.
    """
    from app.workflows import refresh as refresh_mod

    seen: list[list[str]] = []

    def watching(argv: list[str]) -> int:
        seen.append(list(argv))
        _artifact(Path(argv[argv.index("--db") + 1]))
        return 0

    monkeypatch.setattr(refresh_mod, "build_main", watching)
    refresh_mod.main(
        ["--db", str(tmp_path / "advisor.db"), "--epoch-dir", "/bundles/epoch", "--plans", "p.yaml"]
    )

    assert seen, "the builder was never called"
    assert "--epoch-dir" in seen[0] and "/bundles/epoch" in seen[0]
    assert "--plans" in seen[0] and "p.yaml" in seen[0]
    assert "--rosters" not in seen[0], "an unset flag must not be passed through as empty"


def test_the_cli_exit_codes_distinguish_published_unchanged_and_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A scheduler acts on the exit code, so the three outcomes must not collapse.

    `unchanged` is a RESULT and not an error — the same shape as the recommendation CLI's exit 1
    for "no model fits this budget". A scheduler that treats it as failure would page somebody
    every twelve hours for working correctly, which is how an alert channel gets muted.
    """
    from app.workflows import refresh as refresh_mod

    live = tmp_path / "advisor.db"

    monkeypatch.setattr(refresh_mod, "build_main", _builder(top_score=74.5))
    assert refresh_mod.main(["--db", str(live)]) == EXIT_PUBLISHED

    monkeypatch.setattr(refresh_mod, "build_main", _builder(top_score=74.5))
    assert refresh_mod.main(["--db", str(live)]) == EXIT_UNCHANGED

    monkeypatch.setattr(refresh_mod, "build_main", lambda argv: 2)
    assert refresh_mod.main(["--db", str(live)]) == EXIT_FAILED


# --- REQ-REF-003: a refresh may not publish something WORSE (D-128) ------------------------------


def _wide(path: Path, *, models: int = 12, keep: int | None = None) -> Path:
    """A `coding` surface with exactly `keep` of `models` ranked models.

    Twelve, because the fixture used elsewhere has THREE — and with three, "loses more than a
    quarter" and "loses everything" are the same event, so a threshold of 0%, 25% or 100% behaves
    identically and three mutants on it survived. Twelve lets one lost model (8%) and four lost
    models (33%) fall on opposite sides of the line.
    """
    _artifact(path)
    conn = sqlite3.connect(path)
    try:
        conn.execute("DELETE FROM scores WHERE benchmark = 'SWE-bench Verified'")
        surviving = models if keep is None else keep
        for index in range(models):
            model = f"probe-{index:02d}"
            conn.execute(
                "INSERT OR IGNORE INTO models (id, display, vendor) VALUES (?, ?, 'Probe')",
                (model, f"Probe {index:02d}"),
            )
            conn.execute(
                "INSERT OR IGNORE INTO px_median (model_id, in_m, out_m) VALUES (?, 2.0, 6.0)",
                (model,),
            )
            if index < surviving:
                conn.execute(
                    "INSERT INTO scores (model_id, raw_name, source, benchmark, metric, score,"
                    " harness, source_url, observed_at) VALUES (?, ?, 'swebench',"
                    " 'SWE-bench Verified', '% resolved', ?, 'none', 'fixture://x', 't')",
                    (model, f"Probe {index:02d}", 70.0 + index),
                )
        conn.commit()
    finally:
        conn.close()
    return path


def _sized(path: Path, *, drop_models: int = 0, blind: bool = False) -> Path:
    """An artifact whose `coding` surface can be shrunk or blinded on purpose."""
    _artifact(path)
    conn = sqlite3.connect(path)
    try:
        if blind:
            conn.execute("DELETE FROM scores WHERE benchmark = 'SWE-bench Verified'")
        elif drop_models:
            conn.execute(
                "DELETE FROM scores WHERE benchmark = 'SWE-bench Verified' AND model_id IN "
                "(SELECT model_id FROM scores WHERE benchmark = 'SWE-bench Verified' "
                "ORDER BY score ASC LIMIT ?)",
                (drop_models,),
            )
        conn.commit()
    finally:
        conn.close()
    return path


def test_a_candidate_that_blinds_a_surface_is_refused(tmp_path: Path) -> None:
    """The condition that made unattended operation dangerous in the first place.

    A source blips for an hour; the build succeeds and reports the blind surface honestly per
    D-121; and without this rule the cycle publishes an artifact where a category that was
    answering an hour ago now says it has no evidence. Every gate green, every disclosure correct,
    product degraded, nobody told.
    """
    live = _sized(tmp_path / "advisor.db")
    before = live.read_bytes()

    def blinding(argv: list[str]) -> int:
        _sized(Path(argv[argv.index("--db") + 1]), blind=True)
        return 0

    outcome, code = refresh(live, builder=blinding)

    assert code == EXIT_REFUSED, f"a blinded surface was published: {outcome.reason}"
    assert not outcome.published
    assert live.read_bytes() == before
    assert "would now answer nothing" in outcome.reason
    assert "coding" in outcome.reason, "the refusal must name WHICH surface"


def test_a_candidate_losing_more_than_a_quarter_of_a_surface_is_refused(tmp_path: Path) -> None:
    """D-128's threshold, exercised JUST PAST it and not by wiping the surface.

    The first version of this test dropped every model, which trips the blinded-surface branch
    instead — so the threshold itself was never executed and three mutants on it survived,
    including one setting it to 100% (refuse nothing) and one setting it to 0% (refuse everything).
    A test that reaches the wrong branch proves the wrong rule.
    """
    live = _wide(tmp_path / "advisor.db", models=12)
    summary = fingerprint_of(live)
    assert summary is not None and summary.surfaces["coding"] == 12

    def shrinking(argv: list[str]) -> int:
        _wide(Path(argv[argv.index("--db") + 1]), models=12, keep=8)  # 33% lost, over the line
        return 0

    outcome, code = refresh(live, builder=shrinking)
    assert code == EXIT_REFUSED, f"a third of a surface vanished and was published: {outcome.reason}"
    assert not outcome.published
    assert "coding" in outcome.reason and "33%" in outcome.reason


def test_a_candidate_losing_less_than_a_quarter_is_published(tmp_path: Path) -> None:
    """The side of the line that keeps the product alive.

    Boards drop a model routinely. If that refused, the product would freeze at whatever artifact
    happened to be current while every gate reported healthy and every cycle exited cleanly — the
    failure that looks like success, and the one D-128 exists to avoid. One of twelve is 8%.
    """
    live = _wide(tmp_path / "advisor.db", models=12)

    def slightly_smaller(argv: list[str]) -> int:
        _wide(Path(argv[argv.index("--db") + 1]), models=12, keep=11)
        return 0

    outcome, code = refresh(live, builder=slightly_smaller)
    assert code == EXIT_PUBLISHED, f"routine churn was refused: {outcome.reason}"


def test_a_candidate_losing_a_little_is_published(tmp_path: Path) -> None:
    """The other direction, and the one that matters more.

    A rule that refuses on ANY loss freezes the product at whatever artifact happened to be
    current, while every gate reports healthy and every cycle exits cleanly — the failure that
    looks like success. Boards drop a model routinely; that must still publish.
    """
    live = _sized(tmp_path / "advisor.db")
    summary = fingerprint_of(live)
    assert summary is not None and summary.surfaces["coding"] >= 3

    def slightly_smaller(argv: list[str]) -> int:
        _sized(Path(argv[argv.index("--db") + 1]), drop_models=0)
        conn = sqlite3.connect(Path(argv[argv.index("--db") + 1]))
        try:  # a change that is not a loss: one score moves
            conn.execute("UPDATE scores SET score = 71.5 WHERE score = 71.0")
            conn.commit()
        finally:
            conn.close()
        return 0

    outcome, code = refresh(live, builder=slightly_smaller)
    assert code == EXIT_PUBLISHED, f"an ordinary change was refused: {outcome.reason}"


def test_a_surface_getting_BIGGER_or_scores_falling_is_not_a_refusal(tmp_path: Path) -> None:
    """A model getting worse is NEWS, not damage.

    This product reports what the measurements say. Refusing to publish a decline would be the one
    thing worse than publishing it — the engine would quietly hold the last flattering artifact.
    """
    live = _sized(tmp_path / "advisor.db")

    def worse_scores(argv: list[str]) -> int:
        target = Path(argv[argv.index("--db") + 1])
        _sized(target)
        conn = sqlite3.connect(target)
        try:
            conn.execute("UPDATE scores SET score = score / 2")
            conn.commit()
        finally:
            conn.close()
        return 0

    outcome, code = refresh(live, builder=worse_scores)
    assert code == EXIT_PUBLISHED, f"a decline in the measurements was refused: {outcome.reason}"


# --- REQ-REF-004: the record ---------------------------------------------------------------------


def test_every_cycle_records_what_it_did(tmp_path: Path) -> None:
    """Including — especially — the ones that did not publish.

    A record that only exists when things went well cannot tell "nothing needed doing" from "this
    stopped running three days ago", and that distinction is the entire reason to keep one (D-129).
    """
    import json

    from app.workflows.refresh import status_path

    live = tmp_path / "advisor.db"
    record = status_path(live)

    refresh(live, builder=_builder(top_score=74.5), clock=lambda: 1_000.0)
    assert json.loads(record.read_text())["outcome"] == "published"

    refresh(live, builder=_builder(top_score=74.5), clock=lambda: 2_000.0)
    unchanged = json.loads(record.read_text())
    assert unchanged["outcome"] == "unchanged"
    assert unchanged["at"] == 2_000.0, "the record did not move; staleness would be unreadable"

    refresh(live, builder=lambda argv: 2, clock=lambda: 3_000.0)
    failed = json.loads(record.read_text())
    assert failed["outcome"] == "failed"
    assert failed["exit_code"] == EXIT_FAILED
    assert "untouched" in failed["reason"]


def test_the_record_names_the_surface_that_caused_a_refusal(tmp_path: Path) -> None:
    """"Worse how" is the operator's first question, and a rule that cannot answer it gets
    disabled the second time it fires."""
    import json

    from app.workflows.refresh import status_path

    live = _sized(tmp_path / "advisor.db")

    def blinding(argv: list[str]) -> int:
        _sized(Path(argv[argv.index("--db") + 1]), blind=True)
        return 0

    refresh(live, builder=blinding, clock=lambda: 5_000.0)
    written = json.loads(status_path(live).read_text())

    assert written["outcome"] == "refused"
    assert written["exit_code"] == EXIT_REFUSED
    assert "coding" in written["reason"]


def test_the_record_is_never_left_half_written(tmp_path: Path) -> None:
    """A reader catching a truncated file would conclude the refresh is broken, which is the
    opposite of what the record exists to say. Written to a scratch file and renamed."""
    from app.workflows.refresh import status_path

    live = tmp_path / "advisor.db"
    refresh(live, builder=_builder(), clock=lambda: 1.0)

    assert status_path(live).is_file()
    assert not list(tmp_path.glob("*.writing")), "a scratch record survived the write"


def test_the_record_is_written_atomically_rather_than_in_place() -> None:
    """W8: a reader catching a half-written record concludes the refresh is broken.

    Asserted structurally, because observing a torn write reliably would mean racing the
    filesystem. The property IS the scratch-then-rename, and it is the kind that decays silently
    during a "simplify this" pass — `path.write_text(...)` looks tidier and is wrong for the same
    reason the artifact is never written in place.
    """
    import ast

    source = Path("src/app/workflows/refresh.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "write_status"
    )
    body = ast.dump(function)
    assert "replace" in body, "the record is no longer renamed into place"
    assert "scratch" in body, "the record is written straight to its final path"
