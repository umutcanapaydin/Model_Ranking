"""#411 (D-121): a source's bad JSON fails that source, never the night.

`json.loads` raises `RecursionError` on deep nesting and a plain `ValueError` (not a `JSONDecodeError`) on an
integer of more than 4,300 digits. A client that caught only `JSONDecodeError` let both out of `build._ingest_sources`,
whose `except` reads only `SourceError` and `BuildError`: one upstream file aborted every source's night (the v0.1.0
release security review's M2). Every `json.loads` a client makes on what it fetched now sits in a `try` that catches
both, and the scan below fails when a new one does not.
"""

from __future__ import annotations

import ast
import dataclasses
from pathlib import Path

import pytest

CLIENTS = Path(__file__).resolve().parents[2] / "src" / "app" / "clients"
#: A `json.loads` here reads no upstream bytes, so it needs no handler: named, with the reason.
NOT_UPSTREAM = {
    ("parquet_reader.py", "sys.argv"): "the reader's limits, which the parent process wrote to argv as JSON",
}
DEEP = "[" * 100_000 + "]" * 100_000
HUGE = '{"rows": [{"x": ' + "9" * 4_400 + "}]}"


def _handled(names: set[str]) -> bool:
    return {"ValueError", "RecursionError"} <= names or "Exception" in names


def _caught_names(handler: ast.ExceptHandler) -> set[str]:
    kinds = handler.type.elts if isinstance(handler.type, ast.Tuple) else [handler.type]
    return {k.attr if isinstance(k, ast.Attribute) else k.id for k in kinds if isinstance(k, ast.Attribute | ast.Name)}


def _unguarded() -> list[str]:
    found: list[str] = []
    for path in sorted(CLIENTS.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        guarded: set[int] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Try) and _handled({n for h in node.handlers for n in _caught_names(h)}):
                guarded |= {id(inner) for stmt in node.body for inner in ast.walk(stmt)}
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "loads"
                    and isinstance(node.func.value, ast.Name) and node.func.value.id == "json"
                    and id(node) not in guarded):
                target = ast.unparse(node.args[0]) if node.args else ""
                if not any(path.name == f and name in target for f, name in NOT_UPSTREAM):
                    found.append(f"{path.name}:{node.lineno}: json.loads({target})")
    return found


def test_the_scan_reads_every_client() -> None:
    """Fails closed: a scan that finds no `json.loads` at all has read nothing."""
    calls = sum(path.read_text(encoding="utf-8").count("json.loads(") for path in CLIENTS.glob("*.py"))
    assert calls >= 10, calls


def test_every_json_loads_on_fetched_bytes_catches_value_and_recursion_errors() -> None:
    assert _unguarded() == []


@pytest.mark.parametrize("raw", [DEEP, HUGE], ids=["nested-past-the-recursion-limit", "a-4400-digit-integer"])
def test_datacurves_bad_file_fails_datacurve_and_the_night_goes_on(raw: str) -> None:
    """The review's reproduction, through `_ingest_sources`: Datacurve fails as a missing optional source and
    SimpleBench, declared after it, is still read and stored."""
    from app.clients.fakes import FakeRawSource
    from app.workflows import build, sources
    from app.workflows.ingest import RunContext
    from app.workflows.schema import connect

    simplebench_file = Path(__file__).resolve().parents[1] / "fixtures" / "simplebench" / "leaderboard-data.js"
    declared = {s.name: s for s in sources.REMOTE_SOURCES}
    chain = (
        dataclasses.replace(declared["datacurve_deepswe"], client=lambda: FakeRawSource("datacurve_deepswe", raw)),
        dataclasses.replace(declared["simplebench"], client=lambda: FakeRawSource(
            "simplebench", simplebench_file.read_text(encoding="utf-8"))),
    )
    conn = connect(":memory:")
    reports, missing = build._ingest_sources(conn, chain, RunContext(observed_at="2026-10-24T00:00:00Z"))
    assert [line.split(":")[0] for line in missing] == ["datacurve_deepswe"]
    assert [(report.source, report.stored) for report in reports] == [("simplebench", 106)]
