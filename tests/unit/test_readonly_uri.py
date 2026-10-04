"""M10 Stage 4.0 — `f"file:{path}?mode=ro"` does not open a database read-only.

The string form opens whatever URI the PATH happens to spell. A path ending in `?` or `#`, or one
carrying its own `mode=`, takes over the query string, and the connection comes back WRITABLE
against the real file. Four shapes were measured; all four wrote into the artifact.

This was already fixed once. `adapter.main.open_readonly` has carried the derived construction and
a docstring naming this exact defect since M6 — and `workflows.refresh`, written three milestones
later, string-built the URI anyway, with a comment explaining that doing so was "not a second
definition of any project behaviour". It was, and it was the broken one.

So the tests here are in two halves, because only the second one stops it recurring:
  * the construction holds against each measured shape;
  * NOTHING in the repository builds such a URI by hand any more, checked by reading the source.
"""

from __future__ import annotations

import ast
import sqlite3
import sys
from pathlib import Path

import pytest

from app.workflows.schema import open_readonly

# Each of these is a real path SUFFIX that defeated `f"file:{path}?mode=ro"`.
HOSTILE_SUFFIXES = ["a.db?mode=rwc&z=", "a.db#", "a.db?", "a.db?vfs=unix&mode=rwc&j="]


@pytest.mark.parametrize("suffix", HOSTILE_SUFFIXES)
def test_read_only_holds_against_a_path_that_rewrites_the_query_string(
    tmp_path: Path, suffix: str
) -> None:
    """The citing test, one case per measured bypass.

    `open_readonly` resolves the path and derives the URI, so the whole path — `?`, `#` and all —
    becomes the FILE part and cannot reach the query string. The file will not exist, which is the
    correct outcome: a path that is not an artifact must fail to open, not open something else
    writable.
    """
    real = tmp_path / "a.db"
    sqlite3.connect(real).executescript("CREATE TABLE t(x);")
    before = real.read_bytes()

    with pytest.raises(sqlite3.Error):
        conn = open_readonly(tmp_path / suffix)
        conn.execute("CREATE TABLE injected(x)")
        conn.commit()

    assert real.read_bytes() == before, (
        f"a connection opened with mode=ro wrote into the artifact via the path {suffix!r}; "
        "read-only is the contract on this path, not a precaution"
    )


def test_read_only_still_refuses_a_write_on_an_ordinary_path(tmp_path: Path) -> None:
    """Fixture blindness check: the parametrised test must not pass because EVERYTHING raises.

    Without this, `open_readonly` could be a function that always throws and the four cases above
    would all read GREEN.
    """
    db = tmp_path / "plain.db"
    sqlite3.connect(db).executescript("CREATE TABLE t(x);")

    conn = open_readonly(db)
    try:
        assert conn.execute("SELECT count(*) FROM t").fetchone()[0] == 0, "it must READ"
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("CREATE TABLE injected(x)")
    finally:
        conn.close()


def test_nothing_in_the_repository_builds_a_read_only_uri_by_hand() -> None:
    """V4C-49 — the rule ships with its gate, because prose is what failed here.

    The correct construction existed and was documented for three milestones while a second module
    rebuilt the bug. What was missing was not knowledge; it was a check. Any f-string whose value
    starts with `file:` is refused wherever it appears in `src/` or `scripts/`.
    """
    offenders: list[str] = []
    for path in sorted([*Path("src").rglob("*.py"), *Path("scripts").glob("*.py")]):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.JoinedStr) or not node.values:
                continue
            head = node.values[0]
            if isinstance(head, ast.Constant) and str(head.value).startswith("file:"):
                offenders.append(f"{path.as_posix()}:{node.lineno}")

    assert not offenders, (
        "these build a sqlite `file:` URI by string interpolation, which does not open read-only "
        f"for four measured path shapes — call `app.workflows.schema.open_readonly`: {offenders}"
    )


#: The only places a database may be opened without `open_readonly`, each with its reason. An
#: argument of `":memory:"` needs no entry. M16's closure proposed this gate and adopted one reader's
#: test instead; M17 then added three readers and changed three more, and a `/v1/boards` that wrote
#: the served artifact on every GET passed all 1515 tests (M17 closure security seat MINOR-1).
WRITABLE_OPENS: dict[tuple[str, str], str] = {
    ("src/app/workflows/schema.py", "open_readonly"): "the read-only opener itself (INV-23)",
    ("src/app/workflows/schema.py", "connect"): "creates and migrates a database its caller owns: the "
    "build's workspace and the tests",
    ("src/app/workflows/schema.py", "main"): "the explicit operator migration command (W-004), read-write "
    "by design",
    ("scripts/calibrate_board.py", "main"): "a scratch copy the script makes, never the artifact",
    ("scripts/survey_boards.py", "measure"): "a scratch copy the script makes, never the artifact",
    ("scripts/survey_boards.py", "measure_slices"): "a scratch copy the script makes, never the artifact",
}


def _connect_calls() -> dict[tuple[str, str], int]:
    root = Path(__file__).resolve().parents[2]
    found: dict[tuple[str, str], int] = {}
    for path in sorted([*(root / "src").rglob("*.py"), *(root / "scripts").rglob("*.py")]):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "connect" and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "sqlite3"):
                continue
            first = node.args[0] if node.args else None
            if isinstance(first, ast.Constant) and first.value == ":memory:":
                continue
            owner: ast.AST = node
            while owner in parents and not isinstance(owner, ast.FunctionDef | ast.AsyncFunctionDef):
                owner = parents[owner]
            name = owner.name if isinstance(owner, ast.FunctionDef | ast.AsyncFunctionDef) else "<module>"
            key = (path.relative_to(root).as_posix(), name)
            found[key] = found.get(key, 0) + 1
    return found


def test_nothing_opens_a_database_but_the_named_writers_and_the_read_only_opener() -> None:
    """INV-23 held from the source: every reader opens through `open_readonly`."""
    found = _connect_calls()
    assert found, "no sqlite3.connect call found at all: this gate reads the wrong tree"
    unnamed = sorted(set(found) - set(WRITABLE_OPENS))
    assert not unnamed, (
        "these open a database with a plain sqlite3.connect; a reader must call "
        f"`app.workflows.schema.open_readonly`, a writer needs a named entry with its reason: {unnamed}"
    )
    stale = sorted(set(WRITABLE_OPENS) - set(found))
    assert not stale, f"entries that no longer open anything; remove them: {stale}"



# --- #92 (the M17 closure Tester's T1, T2): what the gate above cannot see ---------------------------

#: T2: each named writer opens exactly this many times. The gate above keys by file and function,
#: so a second writable open inside an allowed function passed.
WRITABLE_OPEN_COUNTS = {key: 1 for key in WRITABLE_OPENS}


def test_each_named_writer_opens_as_many_times_as_it_is_allowed() -> None:
    assert _connect_calls() == WRITABLE_OPEN_COUNTS


#: T1: every `sqlite3.connect` the process makes while `_WATCHING` is on, by the audit event the
#: interpreter raises for it. An aliased import, or a writable opener under another name
#: (`schema.connect` on the serving path passed every test), still raises the same event.
_SEEN: list[str] = []
_WATCHING: list[bool] = [False]


def _audit(event: str, args: tuple[object, ...]) -> None:
    if _WATCHING[0] and event == "sqlite3.connect":
        _SEEN.append(str(args[0]))


sys.addaudithook(_audit)


def test_every_reader_opens_the_artifact_read_only_at_run_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """T1: the paths that read the served artifact, run for real, with every connection they make to
    it recorded: `/v1/boards`, `/v1/categories`, the boot check, the refresh's fingerprint and its
    expiry-night baseline. Each must be the read-only URI form (INV-23)."""
    from fastapi.testclient import TestClient

    from app.adapter import main as adapter
    from app.workflows import refresh

    from .test_api_v1 import _seeded_db

    db = tmp_path / "advisor.db"
    _seeded_db(db)
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    _SEEN.clear()
    _WATCHING[0] = True
    try:
        client = TestClient(adapter.app)
        assert client.get("/v1/boards").status_code == 200
        assert client.get("/v1/categories").status_code == 200
        # W5 review M5: the answer itself, the route an aliased writable open got past.
        assert client.get("/v1/recommendations?task=coding").status_code == 200
        adapter.validate_startup_config(env="test")
        assert refresh.fingerprint_of(db) is not None
        refresh._served_without(db, {"swebench"})
    finally:
        _WATCHING[0] = False
    on_artifact = [seen for seen in _SEEN if Path(seen.removeprefix("file:").split("?", 1)[0]).name == db.name
                   and str(tmp_path) in seen]
    assert on_artifact, "the watcher saw no connection to the artifact; it is watching nothing"
    writable = [seen for seen in on_artifact if not (seen.startswith("file:") and "mode=ro" in seen)]
    assert writable == [], f"opened the served artifact writable: {writable}"
