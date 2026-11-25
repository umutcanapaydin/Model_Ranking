"""D-256 (#633): the subscription plan table is frozen.

`/v1` and the app never show a plan (`src/app/workflows/public.py` deletes them from the public
artifact), so the table is no longer re-verified by hand. A `frozen:` date in `data/plans.yaml`
and `data/rosters.yaml` turns their staleness checks into a warning that exits 0, and the
`recommend --subscription` CLI says first that its plan data is not current.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.workflows import plans, rosters
from app.workflows.ingest import RunContext
from app.workflows.plans import ingest_plans
from app.workflows.recommend import main as recommend_main
from app.workflows.schema import connect

REPO_ROOT = Path(__file__).resolve().parents[2]
FROZEN_ON = "2026-11-25"
LONG_AFTER = "2030-01-01"

PLANS = """
schema: 1
staleness_days: 30
budget_caps_usd: {low: 10, medium: 25, unlimited: null}
plans:
  - id: old-plan
    provider: B
    name: Old Plan
    monthly_usd: 10
    currency: USD
    region: US
    limits: x
    source_url: https://b.example/pricing
    last_verified: 2026-06-01
"""

ROSTERS = """
schema: 1
staleness_days: 30
rosters:
  - plan_id: old-plan
    provider: B
    source_url: https://b.example/models
    last_verified: 2026-06-01
    scope: search-models
    note: x
    models: [Some Model]
"""


def _frozen(doc: str, value: str = FROZEN_ON) -> str:
    return doc.replace("staleness_days: 30\n", f"staleness_days: 30\nfrozen: {value}\n", 1)


def _write(tmp_path: Path, name: str, text: str) -> str:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return str(path)


@pytest.mark.parametrize(("module", "doc"), [(plans, PLANS), (rosters, ROSTERS)], ids=["plans", "rosters"])
def test_a_frozen_table_warns_and_passes_its_staleness_check(module, doc, tmp_path, capsys) -> None:
    path = _write(tmp_path, "table.yaml", _frozen(doc))
    assert module.main(["--check-staleness", path, "--today", LONG_AFTER]) == 0
    out = capsys.readouterr().out
    assert f"FROZEN on {FROZEN_ON}" in out
    assert "D-256" in out
    assert "STALE:" not in out


@pytest.mark.parametrize(("module", "doc"), [(plans, PLANS), (rosters, ROSTERS)], ids=["plans", "rosters"])
def test_a_table_that_is_not_frozen_still_fails_when_stale(module, doc, tmp_path) -> None:
    path = _write(tmp_path, "table.yaml", doc)
    assert module.main(["--check-staleness", path, "--today", LONG_AFTER]) == 1


@pytest.mark.parametrize(("module", "doc"), [(plans, PLANS), (rosters, ROSTERS)], ids=["plans", "rosters"])
@pytest.mark.parametrize("value", ["soon", "'2026-13-01'", "true", "20261125", "''"])
def test_a_frozen_value_that_is_not_a_date_is_refused(module, doc, value, tmp_path) -> None:
    path = _write(tmp_path, "table.yaml", _frozen(doc, value))
    assert module.main(["--check-staleness", path, "--today", LONG_AFTER]) == 2


@pytest.mark.parametrize(("module", "name"), [(plans, "plans.yaml"), (rosters, "rosters.yaml")], ids=["plans", "rosters"])
def test_the_shipped_plan_and_roster_files_are_frozen(module, name, capsys) -> None:
    path = str(REPO_ROOT / "data" / name)
    assert module.main(["--check-staleness", path, "--today", LONG_AFTER]) == 0
    assert "FROZEN on " in capsys.readouterr().out


def _plans_db(tmp_path: Path, doc: str) -> str:
    db = tmp_path / "advisor.db"
    conn = connect(str(db))
    ingest_plans(conn, doc, RunContext())
    conn.commit()
    conn.close()
    return str(db)


def test_the_subscription_answer_says_first_that_its_plans_are_frozen(tmp_path, capsys) -> None:
    db = _plans_db(tmp_path, _frozen(PLANS))
    recommend_main(["--db", db, "--budget", "unlimited", "--task", "coding", "--subscription"])
    err = capsys.readouterr().err
    assert err.splitlines()[0] == f"plan data frozen on {FROZEN_ON}, not current (D-256)"


def test_an_unfrozen_subscription_answer_carries_no_frozen_line(tmp_path, capsys) -> None:
    db = _plans_db(tmp_path, PLANS)
    recommend_main(["--db", db, "--budget", "unlimited", "--task", "coding", "--subscription"])
    assert "frozen" not in capsys.readouterr().err


def test_a_model_answer_carries_no_frozen_line(tmp_path, capsys) -> None:
    db = _plans_db(tmp_path, _frozen(PLANS))
    recommend_main(["--db", db, "--budget", "unlimited", "--task", "coding"])
    assert "frozen" not in capsys.readouterr().err


def test_a_database_built_before_the_freeze_still_answers(tmp_path, capsys) -> None:
    """An advisor.db whose plan_config has no frozen column is read, not refused."""
    db = _plans_db(tmp_path, PLANS)
    conn = sqlite3.connect(db)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(plan_config)")}
    if "frozen_on" in columns:
        conn.execute("ALTER TABLE plan_config DROP COLUMN frozen_on")
    conn.commit()
    conn.close()
    code = recommend_main(["--db", db, "--budget", "unlimited", "--task", "coding", "--subscription"])
    assert code in (0, 1)
    assert "frozen" not in capsys.readouterr().err
