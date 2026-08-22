"""REQ-IOS-003 / W-039 — the 503 the client must render honestly, produced on demand.

W-039 has stood since M8-W3 saying this branch **has no live path**: `/v1` returns 503 on
`UnbuiltEvidenceError`, and M7's startup probe refuses to boot the process on an unbuilt artifact,
so by the time anything can answer a request the condition has already stopped the process. The
conclusion drawn was that two individually-correct controls had made a required failure state
unreachable, and REQ-APP-004 named a screen the app could never show.

**The premise was wrong, and M9 is what made it wrong.** The probe guards BOOT. The request path
re-opens the artifact per request, so an artifact that becomes unservable AFTER boot produces the
503 on the very next request — and M9 shipped a refresh that REPLACES that exact file on a
twelve-hour schedule. The state W-039 called unreachable is a state this product now enters by
design, every time a publish lands, for as long as it takes the new file to become readable.

That reframes what these tests are for. They are not a way to reach a dead branch for coverage;
they pin the behaviour of a running engine whose artifact moves underneath it.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.adapter import main as adapter
from app.workflows.schema import connect


@pytest.fixture
def serving(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[TestClient, Path]:
    """A booted engine on a servable copy of the repository's own artifact."""
    artifact = tmp_path / "advisor.db"
    shutil.copy(Path("advisor.db"), artifact)
    monkeypatch.setenv("MODEL_RANKING_DB", str(artifact))
    monkeypatch.setenv("APP_ENV", "test")
    return TestClient(adapter.app), artifact


def test_an_artifact_that_stops_being_servable_after_boot_answers_503(
    serving: tuple[TestClient, Path],
) -> None:
    """The citing test W-039 said could not be written."""
    client, artifact = serving

    healthy = client.get("/v1/recommendations", params={"task": "coding", "budget": "unlimited"})
    assert healthy.status_code == 200, (
        "fixture assumption: the engine must be answering before the artifact is replaced, or "
        "this test proves only that a broken fixture returns 503"
    )

    # Exactly what a refresh publish does to the file the process is serving.
    artifact.unlink()
    connect(str(artifact)).close()  # schema present, no price medians — the W-023 shape

    response = client.get("/v1/recommendations", params={"task": "coding", "budget": "unlimited"})

    assert response.status_code == 503, (
        "the engine answered 200 on an artifact it can no longer rank from; a confident wrong "
        "answer is the failure this whole class of guard exists to prevent"
    )
    assert response.json()["error"]["code"] == "evidence_unavailable"


def test_the_503_says_the_evidence_is_unavailable_rather_than_naming_the_query(
    serving: tuple[TestClient, Path],
) -> None:
    """REQ-APP-004: the client renders this state, so the sentence is part of the contract.

    "No model fits your budget" and "the evidence is unavailable" send a reader to two different
    places, and only one of them is true here.
    """
    client, artifact = serving
    artifact.unlink()
    connect(str(artifact)).close()

    body = client.get(
        "/v1/recommendations", params={"task": "everyday", "budget": "low"}
    ).json()["error"]

    assert "not available" in body["message"].lower()
    assert "budget" not in body["message"].lower(), (
        f"an unavailable artifact blamed the reader's budget: {body['message']}"
    )


def test_a_corrupt_artifact_answers_200_and_says_it_could_not_read_the_evidence(
    serving: tuple[TestClient, Path],
) -> None:
    """The other half of the same swap, and it behaves DIFFERENTLY from the unbuilt case on purpose.

    This assertion was written the other way round first — `status_code >= 500`, on the assumption
    that a file of random bytes must be a 503 like an unbuilt one. It is not, and the measurement
    said so: `/v1` answers **200** with `unavailable_reason: "This surface's evidence could not be
    read."` and no picks.

    That is a design, not an oversight, and the test now pins the design rather than a preference:
    `_answer_for` degrades PER SURFACE, so one unreadable board never takes the other eight down
    with it. The unbuilt case is whole-artifact by definition and answers 503. Conflating them is
    what `test_a_corrupt_database_is_not_reported_as_unbuilt` exists to prevent one layer down.

    What matters at this boundary is that the body is HONEST, and it is: no picks, and a reason
    that names the read rather than blaming the reader.
    """
    client, artifact = serving
    artifact.write_bytes(b"not a database at all" * 128)

    response = client.get("/v1/recommendations", params={"task": "coding", "budget": "unlimited"})

    assert response.status_code == 200
    answers = response.json()["answers"]
    # `coding` opens onto TWO surfaces (CODING_INTENT), and asserting over both is the stronger
    # claim: per-surface degradation must not leave one of them speaking for the other.
    assert len(answers) == 2, f"fixture assumption about CODING_INTENT changed: {len(answers)}"
    for answer in answers:
        assert answer["picks"] == [], "a file of random bytes produced a recommendation"
        reason = str(answer["unavailable_reason"]).lower()
        assert "could not be read" in reason
        assert "budget" not in reason, f"an unreadable file blamed the reader's budget: {reason}"


def test_health_reports_that_the_evidence_became_unservable(
    serving: tuple[TestClient, Path],
) -> None:
    """Stage 4.3 verifies a deploy with `curl /health`. Measured at M11-W3: `/health` answered
    `{"status": "ok"}` while every `/v1` query answered 503 — the deploy check was measuring the
    PROCESS rather than the product, which is the W-023 shape the project has already paid for.

    `status` is deliberately left alone. Its docstring pins it as liveness and promises additive
    fields only, and re-defining a liveness probe's verdict is a contract change that belongs to
    the owner (W-058). What is added is the thing a deploy check can actually read.
    """
    client, artifact = serving
    assert client.get("/health").json()["evidence"] == "servable", (
        "fixture assumption: health must report servable while the artifact still works"
    )

    artifact.unlink()
    connect(str(artifact)).close()

    health = client.get("/health").json()

    assert health["evidence"] == "unavailable", (
        f"`/health` reported nothing wrong while `/v1` could not answer anything. Got: {health}"
    )
    assert health["status"] == "ok", "liveness is unchanged by contract; only the new field moves"
