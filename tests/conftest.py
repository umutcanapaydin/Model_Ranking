"""Test-suite environment declaration.

`app.adapter.main` validates its security configuration at import and, since the Stage-4.0 review,
an unset or unrecognised `APP_ENV` is the STRICT branch — a process that cannot tell where it runs
assumes production. That is the correct default and it is why importing the module in a bare test
environment now raises.

So the suite declares what it is, once, here. **This is a declaration, not a suppression:** the
tests that exercise the strict branch pass `env=` explicitly (`test_api_config.py`) or spawn a real
subprocess with `APP_ENV=production` set, and neither is affected by this line. What it removes is
only the accident of collection order deciding whether the app can be imported at all.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("APP_ENV", "test")


# --- W-108: the tests that read the real artifact ------------------------------------------------
#
# Forty-five tests read `advisor.db`, the built artifact, which is gitignored and holds licensed
# upstream data this PUBLIC repository may not redistribute. On a fresh clone they failed as 45
# errors that meant nothing, so no one outside the owner's machine could tell a real failure from
# a missing file. They are marked `artifact` and SKIPPED, by name, where the file is absent -- and
# `make test` sets MODEL_RANKING_REQUIRE_ARTIFACT=1, so on the machine that must run them a missing
# artifact is a hard error rather than a quiet skip. A skip that can hide the owner's run would be
# the "skipped job reports SUCCESS" defect this project has already paid for once.
ARTIFACT = Path("advisor.db")


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "artifact: reads the built advisor.db (gitignored; W-108). Skipped where absent."
    )
    config.addinivalue_line(
        "markers", "slices: builds with Arena's category slices, through an injected fake client."
    )


def pytest_sessionstart(session: pytest.Session) -> None:
    # In the controlling process, before any worker collects: raised inside an xdist worker the
    # same refusal surfaces as an INTERNALERROR traceback that does not say what is missing.
    if os.environ.get("MODEL_RANKING_REQUIRE_ARTIFACT") == "1" and not ARTIFACT.is_file():
        pytest.exit(
            f"W-108: this run must execute the tests that read {ARTIFACT}, and it is missing "
            "(MODEL_RANKING_REQUIRE_ARTIFACT=1). Build it, or run pytest without the flag.",
            returncode=4,
        )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    needing = [item for item in items if item.get_closest_marker("artifact")]
    if not needing or ARTIFACT.is_file():
        return
    skip = pytest.mark.skip(reason=f"W-108: needs the built {ARTIFACT}, which is not in the repo")
    for item in needing:
        item.add_marker(skip)
