"""App Store submission (D-248): the privacy policy App Store Connect asks for, at the hosted engine's own `/privacy`, and
an engine whose request log names no client.

The app sends the engine two ids per question (`task`, `budget`), never the question (D-160), and keeps on the device
its language, a standings cache and the questions it could not answer (REQ-GAP-001). The policy says so, names the hosting provider, and gives a contact. uvicorn's access log wrote every
request line with a client address, so the image starts it with `--no-access-log`, and the policy's "keeps no log of
who asked" is true.
# covers D-248
"""

from __future__ import annotations

import re
from pathlib import Path

from fastapi.testclient import TestClient

from app.adapter import main

REPO = Path(__file__).resolve().parents[2]


def test_the_engine_serves_its_privacy_policy() -> None:
    answer = TestClient(main.app).get("/privacy")
    assert answer.status_code == 200, answer.text
    assert answer.headers["content-type"].startswith("text/html")
    text = answer.text
    for claim in ("Privacy Policy", "Model Ranking", "never leaves your device", "no account",
                  "no tracking", "Apple Intelligence", "Fly.io", "github.com/umutcanapaydin/Model_Ranking/issues"):
        assert claim in text, claim


def test_the_policy_names_what_a_question_sends_and_nothing_more() -> None:
    text = TestClient(main.app).get("/privacy").text
    assert "task" in text and "budget" in text
    assert "could not answer" in text and "clear them" in text  # the gap register is named, not hidden
    assert not re.search(r"\b(analytics|advertis\w*|third-party SDK)\b", text.replace("no analytics", "")), text


def test_the_engine_image_keeps_no_request_log() -> None:
    """The policy's 'no log of who asked': uvicorn's access log is off in the image every stage inherits."""
    commands = re.findall(r"^CMD \[(.*)\]$", (REPO / "Dockerfile").read_text(encoding="utf-8"), re.M)
    assert commands and all('"--no-access-log"' in c for c in commands if '"uvicorn"' in c), commands


def test_the_policy_lists_every_request_the_app_makes() -> None:
    """The D-248 Tester's M4: the app asks for three things (`EngineClient.swift`), and the page names each."""
    text = TestClient(main.app).get("/privacy").text
    for request in ("list of task kinds", "standings of every board", "<code>task</code>", "<code>budget</code>"):
        assert request in text, request


def test_the_policy_says_what_the_limiter_holds_and_for_how_long() -> None:
    """The D-248 Tester's M5: the limiter's count resets each minute, but its address key stays in memory until the
    table fills or the engine restarts (`RATE_WINDOW_KEYS`), so the page says that and not "forgets"."""
    text = TestClient(main.app).get("/privacy").text
    assert "forgets" not in text, text
    assert "in memory only" in text and "restarts" in text


def test_the_page_runs_no_script_and_loads_nothing_from_elsewhere() -> None:
    """The D-248 Tester's M3: the page's Content-Security-Policy is held, not only set."""
    answer = TestClient(main.app).get("/privacy")
    policy = answer.headers.get("content-security-policy", "")
    assert "default-src 'none'" in policy and "frame-ancestors 'none'" in policy, policy
    assert "script-src" not in policy and "<script" not in answer.text.lower()
