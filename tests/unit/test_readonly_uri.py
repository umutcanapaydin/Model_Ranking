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
