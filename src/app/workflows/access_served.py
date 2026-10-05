"""What the served artifact says about each model's accessibility (W-125, the W6 review's M8).

`app.workflows.access` parses Epoch's `model_metadata.csv` at build time. The serving process needs
only this reader, so it lives here, with no parser beside it, and the server never loads the parser
(`tests/unit/test_nightly_refresh.py`).
"""

from __future__ import annotations

import sqlite3


def served(conn: sqlite3.Connection) -> dict[str, str]:
    """model id -> accessibility, for the models whose names agree.

    An artifact built before this table existed (every one before M17-W3) serves none: the refresh
    fingerprints the LIVE artifact too, and one that raised would read as unreadable and fail every
    night (measured, before merge, on the served artifact).
    """
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'access'").fetchone():
        return {}
    return dict(conn.execute(
        "SELECT model_id, MIN(accessibility) FROM access WHERE model_id IS NOT NULL "
        "GROUP BY model_id HAVING COUNT(DISTINCT accessibility) = 1 ORDER BY model_id").fetchall())
