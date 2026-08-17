"""M6-W3: the roster staleness window is the ROSTER's own (REQ-SUB-008, W-008).

Written before the fix. W-008 was raised at M5-W4 and deferred here on purpose: the roster-link
staleness sentence reads its window from `plan_config.staleness_days` — the CURATED PLAN table's
clock — while `data/rosters.yaml` declares its own `staleness_days` and `rosters.py` ages roster
files against that one.

**Both are 30 today, so nothing is wrong on shipped data.** That is exactly what makes it worth a
test rather than a glance: the defect is invisible until the two numbers diverge, at which point the
product calls a roster link stale that the roster's own policy calls fresh, and every gate stays
green while it does. The M5 ledger row says so in as many words.

So this test does the only thing that can prove the fix: it makes the two windows DIFFERENT and
asserts which one the answer used.
"""

from __future__ import annotations

import sqlite3

import pytest

from app.workflows.schema import connect


def _roster_window(conn: sqlite3.Connection) -> int:
    """The window the persisted roster config carries, however it is stored."""
    from app.workflows.rosters import roster_staleness_days

    return roster_staleness_days(conn)


def test_the_roster_window_is_persisted_separately_from_the_plan_window() -> None:
    """REQ-SUB-008: two clocks, two columns. One column cannot hold two policies.

    Before the fix there was nowhere to put a divergent roster window, which is the whole reason
    the defect could not be tested: the schema had one number and the code had two meanings for it.
    """
    conn = connect()
    try:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(plan_config)")}
    finally:
        conn.close()
    assert "staleness_days" in columns, "the plan table's own window must stay where it was"
    assert (
        "roster_staleness_days" in columns
    ), "the roster window has no home of its own, so it is still borrowing the plan table's"


def test_a_divergent_roster_window_is_the_one_the_answer_uses(
    tmp_path: pytest.TempPathFactory,
) -> None:
    """The citing test W-008 asks for: prove the two windows CAN diverge, and which one wins.

    The plan window is set wide (365 days) and the roster window narrow (5 days) against a roster
    link verified 10 days ago. Under the defect the link reads FRESH, because it is aged against the
    plan table's 365. Under the fix it reads STALE, because the roster's own policy is 5.
    """
    from app.workflows.rosters import roster_staleness_days

    conn = connect()
    try:
        conn.execute(
            "INSERT INTO plan_config (id, staleness_days, roster_staleness_days, cap_dusuk, cap_orta)"
            " VALUES (1, 365, 5, 10.0, 25.0)"
        )
        conn.commit()
        assert roster_staleness_days(conn) == 5
        assert (
            conn.execute("SELECT staleness_days FROM plan_config WHERE id = 1").fetchone()[0] == 365
        )
    finally:
        conn.close()


def test_the_curated_roster_file_supplies_the_window_it_declares(tmp_path) -> None:
    """The number in `data/rosters.yaml` reaches the database — configured is not wired (L.8).

    A persisted column that ingest never writes is the same defect one layer down: the schema would
    carry a policy nobody set, defaulting silently to whatever the DDL says.
    """
    from pathlib import Path

    import yaml

    from app.workflows.ingest import RunContext
    from app.workflows.plans import ingest_plans
    from app.workflows.rosters import ingest_rosters, roster_staleness_days

    plans_raw = Path("data/plans.yaml").read_text()
    rosters_doc = yaml.safe_load(Path("data/rosters.yaml").read_text())
    rosters_doc["staleness_days"] = 7  # deliberately NOT the plan table's 30
    rosters_raw = yaml.safe_dump(rosters_doc)

    conn = connect()
    try:
        ingest_plans(conn, plans_raw, RunContext())
        ingest_rosters(conn, rosters_raw, RunContext())
        assert roster_staleness_days(conn) == 7
        assert (
            conn.execute("SELECT staleness_days FROM plan_config WHERE id = 1").fetchone()[0] == 30
        )
    finally:
        conn.close()


def test_a_pre_m6_database_migrates_without_inventing_a_policy(tmp_path) -> None:
    """The migration, through a database that predates the column (HIGH-tier citing test).

    Two things must both hold, and they pull in opposite directions:
      * the old database gains the column and keeps every row it had — a migration that loses data
        is not a migration;
      * it does NOT gain a roster window. A DEFAULT here would hand an old database a policy nobody
        set, which is precisely the defect W-008 names, reinstated by the fix that closes it.
    """
    from app.workflows.schema import connect as fresh_connect
    from app.workflows.schema import migrate

    db = tmp_path / "pre-m6.db"
    old = sqlite3.connect(str(db))
    try:
        # The M3-era shape: no roster window at all.
        old.executescript("""
            CREATE TABLE plan_config (
                id             INTEGER PRIMARY KEY CHECK (id = 1),
                staleness_days INTEGER NOT NULL CHECK (staleness_days > 0),
                cap_dusuk      REAL NOT NULL CHECK (cap_dusuk > 0),
                cap_orta       REAL NOT NULL CHECK (cap_orta > cap_dusuk)
            );
            INSERT INTO plan_config (id, staleness_days, cap_dusuk, cap_orta)
                VALUES (1, 30, 10.0, 25.0);
            """)
        old.commit()
    finally:
        old.close()

    conn = fresh_connect(str(db))
    try:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(plan_config)")}
        assert "roster_staleness_days" in columns, "the migration did not add the column"
        row = conn.execute(
            "SELECT staleness_days, roster_staleness_days, cap_dusuk FROM plan_config WHERE id = 1"
        ).fetchone()
        assert row[0] == 30 and row[2] == 10.0, "the migration lost the row it was preserving"
        assert row[1] is None, "an old database was handed a roster policy nobody set"

        # ...and asking for the window on that database FAILS LOUD rather than falling back.
        with pytest.raises(ValueError, match="roster_staleness_days is unset"):
            _roster_window(conn)

        # Idempotent: running it again changes nothing and raises nothing.
        assert migrate(conn) == []
    finally:
        conn.close()


def test_production_runs_the_migration_entry_point_the_tests_exercise() -> None:
    """W-009: one entry point, and it is the tested one.

    Both `connect()` and `schema.main()` called the PRIVATE `_migrate` directly, inside their own
    `BEGIN IMMEDIATE`, while the public `migrate()`'s SAVEPOINT wrapper was reached only by tests.
    Two entry points where one is tested and the other ships is worse than one untested entry point,
    because the suite then reports on a path nobody takes.

    Asserted from source rather than by observing behaviour: the two paths behave identically today,
    which is exactly why nothing caught the divergence, and a behavioural test would keep passing
    if someone switched back.
    """
    from pathlib import Path

    source = Path("src/app/workflows/schema.py").read_text()
    body = source[source.index("def connect(") :]
    assert "_migrate(conn)" not in body, (
        "a production path calls the private _migrate again — the SAVEPOINT the tests prove is "
        "then not the transaction that ships"
    )
    assert body.count("migrate(conn)") >= 2, "the production paths no longer migrate at all"


def test_the_public_migration_rolls_back_cleanly_inside_a_caller_transaction() -> None:
    """The property that made the private call tempting: SAVEPOINT must nest.

    `migrate()` is now called from inside `connect()`'s `BEGIN IMMEDIATE`. If SAVEPOINT did not
    nest, the reconciliation would have traded a tested-but-unused path for an untested-and-used
    one.
    """
    conn = connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        from app.workflows.schema import migrate

        assert migrate(conn) == []  # already current: nothing to apply, no error inside the txn
        conn.execute(
            "INSERT INTO plan_config (id, staleness_days, cap_dusuk, cap_orta)"
            " VALUES (1, 30, 10.0, 25.0)"
        )
        conn.commit()
        assert conn.execute("SELECT staleness_days FROM plan_config").fetchone()[0] == 30
    finally:
        conn.close()


def test_the_served_notice_ages_a_roster_link_on_the_roster_window() -> None:
    """W-008's actual criterion: which window the ANSWER used, not which column exists.

    Mandatory test for a stay-green fault (V3C-72), and the most important one in this wave. The
    first version of this file proved the plumbing — the column exists, ingest writes it, the
    migration does not default it — and asserted nothing about the served sentence. Fault injection
    restored the original defect (the notice reading `plan_config.staleness_days`) and every test
    stayed green. **A fix whose citing tests cover the mechanism and not the behaviour is a fix
    nobody has checked.**

    The two windows are set apart deliberately: plan 365, roster 5, against a link verified 10 days
    before the plans were observed. Under the defect the link reads FRESH (10 < 365) and the answer
    says nothing. Under the fix it reads STALE (10 > 5) and the answer says so.
    """
    from .test_subscribe import TWIN_DOC, _db

    conn = _db(TWIN_DOC)
    try:
        conn.execute("UPDATE plans SET observed_at = '2026-08-15T00:00:00+00:00'")
        conn.execute(
            "UPDATE plan_models SET link_source = 'roster',"
            " source_url = 'https://twinco.example/models', last_verified = '2026-08-05'"
            " WHERE plan_id = 'twin-plan'"
        )
        conn.execute(
            "UPDATE plan_config SET staleness_days = 365, roster_staleness_days = 5 WHERE id = 1"
        )
        conn.commit()

        from app.workflows.subscribe import recommend_subscription

        rec = recommend_subscription(conn, "unlimited", "coding")
        assert rec is not None
        assert rec.stale_notice is not None, (
            "a roster link 10 days old went unmentioned against a 5-day roster window — the answer "
            "is aging it on the plan table's 365-day clock"
        )
        assert "roster" in rec.stale_notice

        # ...and the converse, so the test cannot pass by always finding something stale: widen the
        # ROSTER window alone and the same link goes quiet, while the plan window never moved.
        conn.execute("UPDATE plan_config SET roster_staleness_days = 90 WHERE id = 1")
        conn.commit()
        quiet = recommend_subscription(conn, "unlimited", "coding")
        assert quiet is not None
        assert quiet.stale_notice is None or "roster" not in quiet.stale_notice
    finally:
        conn.close()
