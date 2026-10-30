"""The one reader of the refresh's status record, `<artifact>.refresh.json` (REQ-REF-004, #496).

The refresh reads it to carry its counters and arrival clocks forward, and the server's nightly
schedule reads it to decide a catch-up, so it lives here, importing nothing from a client:
`tests/unit/test_nightly_refresh.py` holds that the server loads none (W-125).
"""

from __future__ import annotations

import json
from pathlib import Path


def read_status(path: Path) -> dict[str, object]:
    """The record at `path`, or `{}` when there is none to read: a missing or unreadable file,
    torn JSON, valid JSON that is not an object (#466), or JSON nested past the recursion limit
    (#496). Every one of those is no previous record; a cycle that raised on it instead crashed on
    every night after, and never wrote the record that would have recovered it."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError):
        return {}
    return data if isinstance(data, dict) else {}
