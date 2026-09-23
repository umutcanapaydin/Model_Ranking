#!/usr/bin/env python3
"""M15-W1: measure EVERY board of the dataset we already license, on one footing.

    PYTHONPATH=src .venv/bin/python scripts/survey_boards.py --db advisor.db --out survey.json

**Why a survey and not eleven guesses.** The product reads 3 of the 22 boards in
`lmarena-ai/leaderboard-dataset`. Which of the other 19 could carry a surface is a question with a
numeric answer -- how many models on it can this engine actually recommend -- and the project has
answered that kind of question from memory three times and been wrong three times (W-037). So this
prints one row per board from the same data every time, and writes a JSON record beside it.

**It writes NOTHING to the real database.** Every board is ingested into a THROWAWAY copy, because
the population accessor this survey must use (`ranked_population`, REQ-EVI-002) reads rows from a
database, and inventing a second query instead would be the exact mistake W-037 records. The copy
is deleted when the run ends.

**It answers W-094 in the same pass.** Each board's floor is printed under BOTH candidate rules --
the top third of the whole board over distinct models (D-145, what the two M14 surfaces ship) and
the top third of the ranked population (what `categories.py` says every threshold is sized on) --
so the owner can rule once, on eleven surfaces' worth of evidence, instead of per board.

Network: the documented Hugging Face datasets-server API, the same endpoints
`src/app/clients/arena.py` uses and cites. Neither agent lane can reach it; this runs on the
owner's machine.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import statistics
import sys
import tempfile
from pathlib import Path
from typing import Any

from app.clients.arena import (
    HARNESS,
    METRIC,
    ROWS_API,
    ArenaBoard,
    ArenaClient,
    arena_source_url,
    parse_arena,
)
from app.workflows.categories import CATEGORIES, CategorySpec
from app.workflows.floors import derived_floor, top_third
from app.workflows.ingest import RunContext, _store_scores
from app.workflows.rank import ranked_population
from app.workflows.registry import canonicalize, reconcile, resolve_effort
from app.workflows.schema import ScoreRow, open_readonly

#: Every config of the dataset, from its own config list (2026-09-18 research record). The three
#: the product reads are marked in the output rather than skipped: a survey that cannot reproduce
#: the boards already shipped has not earned the right to recommend a new one.
DATASET = "lmarena-ai/leaderboard-dataset"
SHIPPED = {"text": "assistant", "document": "document", "text_factuality": "factuality"}
CONFIGS = [
    "agent",
    "agent_bash_recovery_steps",
    "agent_praise_complaint",
    "agent_steerability",
    "agent_task_outcome_explicit",
    "agent_tool_hallucination",
    "document",
    "document_style_control",
    "image_edit",
    "image_to_video",
    "search",
    "search_factuality",
    "search_style_control",
    "text",
    "text_factuality",
    "text_style_control",
    "text_to_image",
    "text_to_video",
    "video_edit",
    "vision",
    "vision_style_control",
    "webdev",
]


def survey_client(config: str) -> ArenaClient:
    """An `ArenaClient` pointed at a board nothing is registered for, and nothing else changed.

    `ArenaClient.__init__` REFUSES an unregistered config, deliberately (REQ-SRC-011), because
    defaulting one would ingest a strange board under an existing surface's source id. That refusal
    guards INGEST into the real artifact, which this survey never does. So the object is built
    around the constructor rather than the class being loosened, and every guard that matters here
    -- the page cap, the merged-row cap, the 429 backoff, the byte cap, the overall-category prefix
    -- is the client's own, because re-implementing pagination beside it is how two accounts of one
    upstream start disagreeing.
    """
    client = ArenaClient.__new__(ArenaClient)
    client.board = ArenaBoard(
        id=f"survey_{config}", config=config, benchmark=f"(survey) {config}", minimum_rows=1
    )
    client.name = client.board.id
    client.benchmark = client.board.benchmark
    client.config = config
    client.split = "latest"
    client.url = arena_source_url(config, "latest")
    return client


#: The metric the six `agent_*` boards publish, which is NOT the Elo every other board publishes.
#: Discovered by the diagnosis above: they carry `score` (a rate between 0 and 1, with a 95%
#: interval and an observation count) where the rest carry `rating`. `parse_arena` is right to drop
#: them -- an Elo parser must not read a rate as a rating -- so the survey parses them HERE, in a
#: read-only script, and the question of whether the product should read them is the owner's.
SURVEY_RATE_METRIC = "rate"


def parse_rate_board(raw: str, *, source: str, benchmark: str) -> tuple[list[ScoreRow], int]:
    """A board of RATES, for counting only. Deliberately not in `src/`.

    Two things make these boards different in kind, and both are decisions rather than code:

    * **A rate is already out of 100** once multiplied, which is exactly the shape D-143 wants --
      no anchor, no conversion, identity.
    * **Direction is per board.** A high `agent_steerability` is good; a high
      `agent_tool_hallucination` is a model that invents tool calls more often. Every ranking this
      engine computes assumes higher is better, so a lower-is-better board cannot be served until
      that assumption is made explicit. This function does not guess: it reports the numbers as
      published, and the survey prints the board's own leader so the direction is visible.
    """
    payload = json.loads(raw)
    records = [
        wrapper.get("row")
        for wrapper in payload.get("rows", [])
        if isinstance(wrapper, dict) and isinstance(wrapper.get("row"), dict)
    ]
    overall = [r for r in records if r.get("category") == "overall"] or records
    dates = [
        str(r.get("leaderboard_publish_date"))[:10]
        for r in overall
        if isinstance(r.get("leaderboard_publish_date"), str)
    ]
    newest = max(dates) if dates else None
    current = (
        [r for r in overall if str(r.get("leaderboard_publish_date", ""))[:10] == newest]
        if newest
        else overall
    )

    best: dict[str, ScoreRow] = {}
    skipped = len(records) - len(current)
    for entry in current:
        name, score = entry.get("model_name"), entry.get("score")
        if not isinstance(name, str) or not isinstance(score, int | float) or isinstance(score, bool):
            skipped += 1
            continue
        row = ScoreRow(
            raw_name=name,
            benchmark=benchmark,
            metric=SURVEY_RATE_METRIC,
            score=round(float(score) * 100, 2),
            harness=HARNESS,
            run_date=newest,
            cost_total=None,
            source=source,
            source_url="",
        )
        if name in best:
            skipped += 1
            # The Elo path keeps each model's BEST score (`parse_arena`); keeping whichever duplicate
            # came last would make the two paths disagree on the same board (W1 review m-4).
            if best[name].score >= row.score:
                continue
        best[name] = row
    return list(best.values()), skipped


def floors(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Every surface's floor under D-148's rule (the one the engine serves, D-159), beside the two
    populations the rule did not choose.

    M16-W3 (M15-W1 review M-2): reproducible, offline, from the artifact the product serves. The
    BOARD is the surface's primary source and benchmark as stored -- one row per raw name, harness
    and effort, exactly as the parser emitted it. That is D-148 clause 1's population ("every row in
    the list", owner, translated from Turkish). The distinct-model column is D-145's count and the
    ranked column is the population `categories.py` once said it sized on; both are printed so the
    owner rules with the alternatives in view, never to be chosen here.
    """
    table: list[dict[str, Any]] = []
    for surface, spec in CATEGORIES.items():
        rows = conn.execute(
            "SELECT raw_name, COALESCE(model_id, raw_name), score, effort FROM scores "
            "WHERE source = ? AND benchmark = ? AND metric = ?",
            (spec.primary_source, spec.primary_benchmark, spec.metric),
        ).fetchall()
        best: dict[str, float] = {}
        for _raw, model, score, _effort in rows:
            best[model] = max(best.get(model, score), score)
        ranked = [r.score for r in ranked_population(conn, spec)]
        floor_rows = derived_floor(conn, spec)  # D-159: the engine's own function
        table.append({
            "surface": surface,
            "board": f"{spec.primary_source} / {spec.primary_benchmark}",
            "board_rows": len(rows),
            "distinct_models": len(best),
            "ranked_population": len(ranked),
            "efforts": sorted({effort for *_, effort in rows}),
            "floor_rows": floor_rows,
            "floor_distinct": top_third(list(best.values())),
            "floor_ranked": top_third(ranked),
        })
    return table


def _print_floors(table: list[dict[str, Any]]) -> None:
    header = (f"{'surface':18s} {'rows':>5s} {'models':>7s} {'ranked':>7s} "
              f"{'rows⅓':>8s} {'models⅓':>8s} {'ranked⅓':>8s}  efforts")
    print(header)
    print("-" * len(header))

    def cell(value: object, width: int) -> str:
        return f"{'-' if value is None else value:>{width}}"

    for r in table:
        print(f"{r['surface']:18s} {r['board_rows']:5d} {r['distinct_models']:7d} "
              f"{r['ranked_population']:7d} {cell(r['floor_rows'], 8)} "
              f"{cell(r['floor_distinct'], 8)} {cell(r['floor_ranked'], 8)}  "
              f"{','.join(r['efforts'])}")
    print("\nrows⅓ is D-148's floor (top third of every row on the board), the one the engine serves (D-159).")
    print("models⅓ (D-145's count) and ranked⅓ are shown for comparison, not for choosing.")


def measure(config: str, db: Path, workspace: Path) -> dict[str, Any]:
    client = survey_client(config)
    source, benchmark = client.name, client.benchmark
    raw = client.fetch_raw()
    rows, skipped = parse_arena(raw, source=source, source_url=client.url, benchmark=benchmark)
    metric = METRIC
    if not rows:
        rows, skipped = parse_rate_board(raw, source=source, benchmark=benchmark)
        metric = SURVEY_RATE_METRIC if rows else METRIC

    scratch = workspace / f"{config}.db"
    shutil.copy(db, scratch)
    conn = sqlite3.connect(str(scratch))
    _store_scores(conn, source, rows, RunContext(observed_at="2026-09-21T00:00:00Z"))
    # **The step the first run of this script forgot, and the whole table read zero because of it.**
    # `_store_scores` writes the board's rows; NOTHING joins them to a priced model until the
    # registry reconciles raw names to canonical ids, which is what `build.py` does next in
    # production. Without it `ranked_population` correctly reports that no row belongs to a model
    # the engine knows -- a true answer to a question nobody asked. The price medians are already
    # built in the database this copy came from, so reconcile is the only missing stage.
    reconcile(conn)
    conn.commit()

    spec = CategorySpec(
        id=f"survey-{config}",
        title=benchmark,
        primary_benchmark=benchmark,
        metric=metric,
        score_unit="Elo" if metric == METRIC else "%",
        secondary_benchmark=None,
        primary_source=source,
        value_window=0.0,
        close_call=0.0,
    )
    population = ranked_population(conn, spec)
    conn.close()

    board_best: dict[str, float] = {}
    for row in rows:
        rule = canonicalize(resolve_effort(row.raw_name).model_name)
        key = rule.canonical_id if rule is not None else row.raw_name
        board_best[key] = max(board_best.get(key, row.score), row.score)

    ratings = [r.score for r in population]

    # A board that yields NO rows is a result, not a crash -- but an unexplained zero is useless, so
    # the first page is read back raw and its own `category` values are reported. The client trims
    # every board to the rows whose category is `overall` (D-001's shape for the text board); a
    # board that names its categories differently disappears silently without this.
    sample_categories: list[str] = []
    sample_columns: list[str] = []
    sample_row: dict[str, Any] = {}
    if not rows:
        try:
            payload = client._get_page(ROWS_API, 0, {})  # a diagnostic read of the client's own page
            records = [
                wrapper.get("row")
                for wrapper in payload.get("rows", [])
                if isinstance(wrapper, dict) and isinstance(wrapper.get("row"), dict)
            ]
            seen = {record.get("category") for record in records}
            sample_categories = sorted(str(value) for value in seen if value is not None)
            if records:
                # The first run of this diagnosis asked only about `category`, and every empty board
                # answered "overall" -- a true answer to the wrong question. The parser needs
                # `model_name` and a numeric `rating`; a board that names those columns differently
                # parses to nothing with the category filter perfectly satisfied. So report the
                # COLUMNS, and one row small enough to read.
                sample_columns = sorted(records[0])
                sample_row = {
                    key: value
                    for key, value in list(records[0].items())[:12]
                    if not isinstance(value, dict | list)
                }
        except Exception as error:  # the diagnosis failing must not lose the measurement
            sample_categories = [f"(unreadable: {type(error).__name__})"]

    return {
        "metric": metric,
        "sample_categories": sample_categories,
        "sample_columns": sample_columns,
        "sample_row": sample_row,
        "config": config,
        "shipped_as": SHIPPED.get(config),
        "board_rows": len(rows),
        "skipped": skipped,
        "board_distinct_models": len(board_best),
        "ranked_population": len(ratings),
        "leader": round(max(ratings), 1) if ratings else None,
        "last": round(min(ratings), 1) if ratings else None,
        "spread": round(max(ratings) - min(ratings), 1) if ratings else None,
        "median_neighbour_gap": round(
            statistics.median(
                [
                    a - b
                    for a, b in zip(
                        sorted(ratings, reverse=True), sorted(ratings, reverse=True)[1:], strict=False
                    )
                ]
            ),
            1,
        )
        if len(ratings) > 1
        else None,
        # W-094, both rules, same quantile, different population.
        "floor_board_third_D145": top_third(list(board_best.values())),
        "floor_ranked_third": top_third(ratings),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="survey_boards")
    parser.add_argument("--db", default="advisor.db", help="read-only; every write goes to a copy")
    parser.add_argument("--out", default=None, help="write the JSON record here")
    parser.add_argument("--only", nargs="*", default=None, help="measure just these configs")
    parser.add_argument(
        "--floors", action="store_true",
        help="D-148: every surface's floor from the artifact itself (no network), beside today's",
    )
    args = parser.parse_args(argv)

    db = Path(args.db)
    if not db.is_file():
        print(f"{db} is not there; run a build first", file=sys.stderr)
        return 2

    if args.floors:
        conn = open_readonly(db)  # INV-23: never a hand-built read-only URI
        try:
            table = floors(conn)
        finally:
            conn.close()
        _print_floors(table)
        if args.out:
            Path(args.out).write_text(json.dumps({"floors": table}, indent=2), encoding="utf-8")
        return 0

    configs = args.only or CONFIGS
    records: list[dict[str, Any]] = []
    header = (
        f"{'config':30s} {'rows':>6s} {'models':>7s} {'ranked':>7s} "
        f"{'leader':>8s} {'spread':>7s} {'D145':>8s} {'ranked⅓':>8s}"
    )
    print(header)
    print("-" * len(header))
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        for config in configs:
            try:
                record = measure(config, db, workspace)
            except Exception as error:  # a board that cannot be read is a RESULT, not a crash
                record = {"config": config, "error": f"{type(error).__name__}: {error}"}
                print(f"{config:30s} {'-':>6s}  {record['error'][:60]}")
                records.append(record)
                continue
            if record["board_rows"] == 0:
                print(f"{record['config']:29s}  {'0':>6} rows parsed")
                print(f"{'':31s}categories: {', '.join(record['sample_categories'][:4]) or '(none)'}")
                print(f"{'':31s}columns:    {', '.join(record['sample_columns']) or '(none)'}")
                if record["sample_row"]:
                    print(f"{'':31s}first row:  {json.dumps(record['sample_row'], ensure_ascii=False)[:240]}")
                records.append(record)
                continue
            mark = "*" if record["shipped_as"] else " "
            print(
                f"{config:29s}{mark} {record['board_rows']:6d} "
                f"{record['board_distinct_models']:7d} {record['ranked_population']:7d} "
                f"{record['leader'] if record['leader'] is not None else '-':>8} "
                f"{record['spread'] if record['spread'] is not None else '-':>7} "
                f"{record['floor_board_third_D145'] if record['floor_board_third_D145'] is not None else '-':>8} "
                f"{record['floor_ranked_third'] if record['floor_ranked_third'] is not None else '-':>8}"
            )
            records.append(record)

    print("\n* = a board the product already reads. `ranked` is the only column that decides")
    print("  whether a board can carry a surface: models this engine could actually recommend.")
    print("  D145 and ranked⅓ are the two candidate floor rules (W-094), same quantile.")
    if args.out:
        Path(args.out).write_text(
            json.dumps({"dataset": DATASET, "boards": records}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"\nwritten: {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
