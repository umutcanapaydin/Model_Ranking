"""M6-W2: one serializer, three renderings, and a test that fails when they drift.

REQ-API-003. Written BEFORE the extraction, against today's behaviour, so it can be shown RED on
the disagreement that exists right now (E.4 + the red-then-green rule).

**Why this file exists.** M5's closure security review found the single highest-value defect of that
milestone by reading two artifacts of ONE run against each other: the JSON payload published the
effort POLICY while the CSV export of the same run published the effort EVIDENCE. They disagreed and
every gate was green. M6 adds a third rendering. The W1 code review then measured the same hazard in
the new one: deleting `"stale_notice"` from the adapter's hand-written mirror left all thirteen tests
passing.

So the rule this file enforces is not "the renderings look similar". It is:

    every field the engine produces reaches every rendering, and no rendering
    invents or drops one, because they all derive from one function.

A parity test that only passes after the extraction proves nothing. Its mutants are named in
`docs/plans/m6-wave-2-close.md` row 5 and each must be shown RED.
"""

from __future__ import annotations

import json
from dataclasses import fields
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.workflows.ingest import RunContext
from app.workflows.rank import export_ranking, read_export_csv
from app.workflows.recommend import Pick, Recommendation, recommend
from app.workflows.schema import connect

from .test_api_v1 import _seeded_db

#: `Recommendation` fields the /v1 envelope deliberately relocates rather than drops. `task` becomes
#: the answer's `surface`; `budget` moves to the envelope's `query`, because it is one query for all
#: the answers and repeating it per answer would let two copies disagree.
RELOCATED = {"task", "budget"}


def _live_answer(client: TestClient, surface: str) -> dict[str, object]:
    body = client.get("/v1/recommendations", params={"task": "coding"}).json()
    return next(a for a in body["answers"] if a["surface"] == surface)


# ---------------------------------------------------------------- REQ-API-003 (parity)


def test_every_recommendation_field_reaches_the_v1_answer(client: TestClient) -> None:
    """A field added to the engine cannot silently fail to reach the API.

    Derived from the dataclass, not from a hand-written list — a hand-written list is the same
    mirror this test exists to catch, one level up.
    """
    answer = _live_answer(client, "coding")
    expected = {f.name for f in fields(Recommendation)} - RELOCATED
    missing = sorted(expected - set(answer))
    assert missing == [], f"engine fields absent from the /v1 answer: {missing}"


def test_every_pick_field_reaches_the_v1_answer(client: TestClient) -> None:
    """Same rule, one level down. `Pick` gained `effort` in M5 and it had to be published."""
    answer = _live_answer(client, "coding")
    assert answer["picks"], "no picks to check parity against"
    expected = {f.name for f in fields(Pick)}
    for pick in answer["picks"]:
        missing = sorted(expected - set(pick))
        assert missing == [], f"engine pick fields absent from the /v1 payload: {missing}"


def test_the_cli_and_the_api_render_the_same_run_identically(
    client: TestClient, tmp_path: Path
) -> None:
    """The two renderings of one run agree field for field — the M5 defect, asserted.

    The CLI prints `asdict(rec)`; the API builds an answer. Both must carry the same values for
    every field they share, or one of them is lying about the same database.
    """
    db = tmp_path / "pipeline.db"
    conn = connect(str(db))
    try:
        rec = recommend(conn, budget="unlimited", task="coding")
    finally:
        conn.close()
    assert rec is not None

    answer = _live_answer(client, "coding")
    for field in (f.name for f in fields(Recommendation)):
        if field in RELOCATED or field == "picks":
            continue
        cli_value = getattr(rec, field)
        api_value = answer[field]
        if isinstance(cli_value, tuple):
            cli_value = list(cli_value)
        assert api_value == cli_value, f"{field}: API {api_value!r} != CLI {cli_value!r}"

    for cli_pick, api_pick in zip(rec.picks, answer["picks"], strict=True):
        for field in (f.name for f in fields(Pick)):
            assert api_pick[field] == getattr(cli_pick, field), f"pick.{field} disagrees"


# ---------------------------------------------------------------- REQ-LIC-002 (CSV attribution)


def _export(tmp_path: Path) -> tuple[Path, Path]:
    from app.workflows.categories import CATEGORIES
    from app.workflows.rank import build_price_medians, category_ranking

    db = tmp_path / "export.db"
    _seeded_db(db)
    conn = connect(str(db))
    try:
        build_price_medians(conn)
        ranking = category_ranking(conn, CATEGORIES["coding"])
    finally:
        conn.close()
    assert ranking, "the fixture produced no ranking to export"
    return export_ranking(ranking, tmp_path / "out", generated_from=[], category="coding")


def test_the_csv_export_carries_the_same_attribution_as_the_json(tmp_path: Path) -> None:
    """REQ-LIC-002: a licence obligation ships WHERE THE DATA IS SERVED, in both halves.

    M5's security review left this open: the JSON half cites its sources, the CSV half of the same
    run cites nothing. A CC-BY dataset does not stop being CC-BY because the reader opened the other
    file, and this is the export an analyst actually loads.
    """
    csv_path, json_path = _export(tmp_path)
    payload = json.loads(json_path.read_text())
    csv_text = csv_path.read_text()

    for attribution in payload["attribution"]:
        assert attribution in csv_text, f"CSV export omits the attribution: {attribution[:60]}"
    assert payload["note"] in csv_text, "CSV export omits the blend note the JSON half carries"


def test_the_csv_metadata_does_not_corrupt_the_table(tmp_path: Path) -> None:
    """The attribution must not cost a machine consumer its data.

    Metadata rides as `#`-prefixed lines above the header, so a reader that skips comment lines gets
    exactly the rows it got before — and the header is still the first non-comment line.
    """
    csv_path, json_path = _export(tmp_path)
    rows_json = json.loads(json_path.read_text())["rows"]

    parsed = read_export_csv(csv_path)
    assert len(parsed) == len(rows_json)
    assert parsed[0]["model"] == rows_json[0]["model"]
    assert set(parsed[0]) == set(rows_json[0]), "CSV columns drifted from the JSON row shape"


def test_the_two_export_halves_carry_the_same_rows(tmp_path: Path) -> None:
    """Trap 1, at the export boundary: same run, same numbers, both files."""
    csv_path, json_path = _export(tmp_path)
    rows_json = json.loads(json_path.read_text())["rows"]
    parsed = read_export_csv(csv_path)

    for csv_row, json_row in zip(parsed, rows_json, strict=True):
        for key, value in json_row.items():
            rendered = "" if value is None else str(value)
            assert csv_row[key] == rendered, f"{key}: CSV {csv_row[key]!r} != JSON {rendered!r}"


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db = tmp_path / "pipeline.db"
    _seeded_db(db)
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    from app.adapter import main as adapter

    return TestClient(adapter.app)


# ---------------------------------------------------------------- REQ-REC-014 (W-002)


def test_equivalent_plans_carries_group_structure(tmp_path: Path) -> None:
    """REQ-REC-014 / W-002: a machine consumer can tell WHICH pick each plan is equivalent to.

    Deferred at M4 with the reason that the fix is a CONTRACT shape to decide once, alongside the
    HTTP API — which is this milestone. The flat name list loses the structure the prose already
    carries: with two equivalence groups, `("A", "B", "C")` cannot say that A is equivalent to the
    quality pick and B and C to the budget pick, nor at what price. Prose is not a contract; a
    client cannot render from it, and an iOS view that groups plans has to re-derive what the
    engine already knew.
    """
    from app.workflows.subscribe import EquivalenceGroup, SubscriptionRecommendation

    # The shape is the contract: one entry per group, each naming its pick and its members.
    assert {f.name for f in fields(EquivalenceGroup)} >= {
        "equivalent_to",
        "model",
        "score",
        "members",
    }
    field_types = {f.name: f.type for f in fields(SubscriptionRecommendation)}
    assert "equivalent_plans" in field_types, "the contract field must keep its name"


def test_equivalence_members_name_their_plan_and_price(tmp_path: Path) -> None:
    """Each member carries what a client needs to render it without a second query."""
    from app.workflows.subscribe import EquivalenceMember

    assert {f.name for f in fields(EquivalenceMember)} >= {"plan", "plan_id", "monthly_usd"}


# ---------------------------------------------------------------- W-010 (effort counter)


def test_an_unclassifiable_effort_suffix_is_counted_not_silently_defaulted() -> None:
    """W-010 intake — a defect against REQ-CAN-005, reproduced before it is fixed.

    REQ-CAN-005: "a row whose effort cannot be determined is counted and disclosed, never
    defaulted". `_store_scores` defaults an unresolved effort to `unspecified` and counts nothing,
    so a row carrying a literal `_high` suffix whose model has no registry rule is stored as
    `unspecified` while the ingest reports `effort_unknown=0`.

    Measured on live data at M5 closure: four Epoch rows. No shipped answer was affected — those
    rows are registry-dropped and never reach a ranking — which is exactly why nobody noticed that
    the counter was silent. A counter that under-reports is worse than no counter, because a zero
    reads as "checked, none found".
    """
    from app.clients.fakes import FakeRawSource
    from app.workflows.ingest import RunContext, ingest_swebench

    payload = json.dumps(
        {
            "leaderboards": [
                {
                    "name": "Verified",
                    "results": [
                        # No registry rule exists for this family, so the `_high` suffix cannot be
                        # confirmed as an effort and the row is stored `unspecified`.
                        {
                            "name": "totally-unknown-model_high",
                            "resolved": 50.0,
                            "date": "2026-02-26",
                        },
                        {"name": "Claude 4.5 Opus", "resolved": 74.5, "date": "2026-02-26"},
                    ],
                }
            ]
        }
    )
    conn = connect()
    try:
        report = ingest_swebench(conn, FakeRawSource("swebench", payload), RunContext())
        stored = dict(conn.execute("SELECT raw_name, effort FROM scores"))
    finally:
        conn.close()

    assert stored["totally-unknown-model_high"] == "unspecified"
    assert (
        report.effort_unknown == 1
    ), "a suffix-bearing row the parser could not classify was defaulted without being counted"


# ------------------------------------------------- mandatory tests for stay-green faults (V3C-72)


def test_the_csv_cites_exactly_what_the_json_cites_no_more(tmp_path: Path) -> None:
    """A superset is not attribution — it is a false provenance claim, in the other direction.

    Mandatory test for a stay-green fault: swapping the CSV's per-run citations for the whole
    ATTRIBUTIONS catalogue left the first version green, because "every JSON attribution appears in
    the CSV" is satisfied by printing everything. W4's BLOCKING-2 established the rule for the JSON
    half — an export cites the sources IT carries, not the catalogue — and the CSV half owes the
    same discipline.
    """
    csv_path, json_path = _export(tmp_path)
    from app.workflows.rank import ATTRIBUTIONS, EXPORT_COMMENT_PREFIX

    payload = json.loads(json_path.read_text())
    commented = [
        line.lstrip(EXPORT_COMMENT_PREFIX).strip()
        for line in csv_path.read_text().splitlines()
        if line.startswith(EXPORT_COMMENT_PREFIX)
    ]
    cited = [line for line in commented if line in ATTRIBUTIONS]
    assert cited == list(
        payload["attribution"]
    ), "the CSV cites a different source set from the JSON half of the same run"

    # ...and both halves are checked against the citations the run actually OWES, computed here
    # independently. Comparing the two halves to EACH OTHER cannot catch a change that corrupts
    # them both the same way — which is exactly what swapping in the full catalogue does, and it
    # is why the first version of this test stayed green against that mutant.
    from app.workflows.rank import attributions_for

    owed = attributions_for({row["evidence_source"] for row in payload["rows"]}, priced=True)
    assert tuple(payload["attribution"]) == owed, "the export cites the catalogue, not its sources"
    assert tuple(cited) == owed


def test_a_present_disclosure_survives_serialization(client: TestClient, tmp_path: Path) -> None:
    """A disclosure that EXISTS must arrive — asserted on a non-null value, not on a null one.

    Mandatory test for a stay-green fault: deleting `close_call` and `effort_mix_notice` from the
    serializer stayed green because both are null on this fixture, and null is what a missing key
    also looks like once anything supplies a default. A parity test that only ever sees `None`
    cannot tell "carried" from "dropped".
    """
    db = tmp_path / "pipeline.db"
    conn = connect(str(db))
    try:
        rec = recommend(conn, budget="unlimited", task="agentic-coding")
    finally:
        conn.close()
    assert rec is not None
    # `agentic-coding` names a ranking effort, so this disclosure is genuinely non-null.
    assert rec.picks[0].effort_note, "fixture no longer produces a non-null disclosure"

    body = client.get("/v1/recommendations", params={"task": "coding"}).json()
    answer = next(a for a in body["answers"] if a["surface"] == "agentic-coding")
    assert answer["picks"][0]["effort_note"] == rec.picks[0].effort_note
    assert answer["ranking_effort"] == rec.ranking_effort == "high"


def test_each_equivalence_group_names_the_pick_it_belongs_to(tmp_path: Path) -> None:
    """REQ-REC-014 is about STRUCTURE CARRYING MEANING, so the meaning is asserted.

    Mandatory test for a stay-green fault: setting `equivalent_to=""` left the first version green,
    because the contract test only checked that the field exists. A field that exists and says
    nothing is exactly the flat name list W-002 was raised about.
    """
    from app.workflows.subscribe import PLAN_PICK_LABELS, recommend_subscription

    # The canonical curated-plan fixture, on the document that produces an equivalence
    # group (V3C-44: one canonical fixture per integration, not a bespoke stub).
    from .test_subscribe import TWIN_DOC, _db

    conn = _db(TWIN_DOC)
    try:
        rec = recommend_subscription(conn, "unlimited", "coding")
    finally:
        conn.close()
    assert rec is not None
    assert rec.equivalent_plans, "the canonical fixture no longer produces an equivalence group"

    for group in rec.equivalent_plans:
        assert group.equivalent_to in PLAN_PICK_LABELS, group.equivalent_to
        assert group.model
        assert group.members
        for member in group.members:
            assert member.plan and member.plan_id and member.monthly_usd > 0


def test_the_subscription_cli_rendering_carries_every_engine_field(tmp_path: Path, capsys) -> None:
    """REQ-API-003 + REQ-REC-014, through the LIVE subscription entry point.

    Mandatory test for a stay-green fault the W2 review found (V3C-72). Deleting
    `equivalent_plans` from the printed subscription JSON left 308 tests green, because all three
    REQ-REC-014 tests inspected the in-memory dataclass and two of them were `dataclasses.fields`
    reflection that would pass against an empty implementation. The subscription rendering was the
    one path this wave had not routed through the shared serializer — the identical defect the W1
    review found in the adapter, reproduced one wave later in the sibling path, inside the wave
    whose purpose was to make it impossible.

    So this asserts the SHIPPED TEXT, not the object: what a caller of the CLI actually receives.
    """
    from dataclasses import fields as dc_fields

    from app.workflows.plans import ingest_plans
    from app.workflows.recommend import main as recommend_main
    from app.workflows.registry import reconcile_plans
    from app.workflows.subscribe import SubscriptionRecommendation

    from .test_subscribe import SCORES, TWIN_DOC

    db = tmp_path / "subs.db"
    conn = connect(str(db))
    try:
        ingest_plans(conn, TWIN_DOC, RunContext())
        reconcile_plans(conn)
        for model_id, raw, score in SCORES:
            conn.execute(
                "INSERT INTO scores (model_id, raw_name, benchmark, metric, score, harness,"
                " run_date, source, source_url, observed_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    model_id,
                    raw,
                    "SWE-bench Verified",
                    "% resolved",
                    score,
                    "test-agent",
                    "2026-08-01",
                    "swebench",
                    "https://x",
                    "2026-08-15T00:00:00+00:00",
                ),
            )
        conn.commit()
    finally:
        conn.close()

    assert (
        recommend_main(
            ["--db", str(db), "--budget", "unlimited", "--task", "coding", "--subscription"]
        )
        == 0
    )
    printed = json.loads(capsys.readouterr().out)

    missing = sorted({f.name for f in dc_fields(SubscriptionRecommendation)} - set(printed))
    assert missing == [], f"engine fields absent from the subscription CLI output: {missing}"

    # ...and the REQ-REC-014 structure survives the round trip as DATA, not as prose.
    assert printed["equivalent_plans"], "the contract field is empty in the shipped rendering"
    group = printed["equivalent_plans"][0]
    assert group["equivalent_to"] and group["model"] and group["members"]
    assert group["members"][0]["plan"] and group["members"][0]["monthly_usd"] > 0


def test_the_export_reader_does_not_drop_a_row_named_like_a_comment(tmp_path: Path) -> None:
    """A reader that silently drops data is worse than one that fails.

    Found by review, not by test: `read_export_csv` filtered EVERY line starting with `#`, so a
    model whose name begins with `#` would have vanished from the table while the file, the row
    count in the JSON half and every existing assertion stayed plausible.
    """
    from app.workflows.rank import RankingRow, read_export_csv

    row = RankingRow(
        model="#1 Model",
        vendor="Test",
        score=70.0,
        harness="test-agent",
        evidence_source="swebench",
        effort="unspecified",
        higher_effort=None,
        higher_effort_score=None,
        evidence_date="2026-02-26",
        secondary_score=None,
        secondary_cost=None,
        input_per_m=1.0,
        output_per_m=2.0,
        blended_per_m=1.25,
    )
    csv_path, _ = export_ranking([row], tmp_path / "out", generated_from=[], category="coding")
    parsed = read_export_csv(csv_path)
    assert [r["model"] for r in parsed] == ["#1 Model"]


def test_the_serializer_imports_no_engine_module() -> None:
    """The one serializer must not depend on what it serializes.

    The first version named both recommendation classes in its signature, creating
    `serialize -> subscribe -> recommend`. That made a deferred import inside `recommend.main`
    load-bearing while the comment above it explained something else entirely — so a later import
    tidy would have broken the CLI at runtime rather than at lint. The W2 review measured it. The
    function only needs a dataclass instance, so it asks for one structurally.

    This asserts the property rather than the import line, because the import line is what a tidy
    would move.
    """
    import ast

    source = Path("src/app/workflows/serialize.py").read_text()
    imported = {
        node.module
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.ImportFrom) and node.module
    } | {
        alias.name
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    engine = sorted(m for m in imported if m.startswith("app."))
    assert engine == [], f"the serializer imports engine modules: {engine}"


def test_nested_tuples_become_lists_at_every_depth() -> None:
    """The docstring's claim, asserted — it was true only at the top level.

    `equivalent_plans[0]["members"]` came back a tuple while the sentence a later reader would
    trust said tuples become lists. Harmless in `json.dumps`; wrong as a definition.
    """
    from app.workflows.serialize import recommendation_json
    from app.workflows.subscribe import EquivalenceGroup, EquivalenceMember

    group = EquivalenceGroup(
        equivalent_to="best_value",
        model="gpt-5",
        score=70.0,
        members=(EquivalenceMember(plan="Twin Plan", plan_id="twin", monthly_usd=12.0),),
    )
    rendered = recommendation_json(group)
    assert isinstance(rendered["members"], list)
    assert isinstance(rendered["members"][0], dict)


def test_the_serializer_refuses_a_non_dataclass() -> None:
    """Fail loud rather than return a plausible empty dict."""
    from app.workflows.serialize import recommendation_json

    with pytest.raises(TypeError):
        recommendation_json({"not": "a dataclass"})  # type: ignore[arg-type]
