"""REQ-APP-001/-002/-003/-005 — the client invariants, gated by reading the Swift source.

**What these tests are and are not.** This repository has no iOS test target (W-038), so nothing
executes a line of Swift. These tests parse the client's source and assert structural properties of
it. They cannot prove the app looks right or behaves correctly; they CAN prove the three things the
M8 plan calls traps, each of which is a property of the source rather than of a running screen:

* Trap 1 — the client re-deriving a number the engine already sent (REQ-APP-005). Arithmetic on a
  served value is visible in the text.
* Trap 2 — the client silently improving on the server's honesty (REQ-APP-003). A disclosure the
  client never mentions cannot be displayed, and the disclosure SET is derived from the Swift model
  rather than typed here, so adding one to the API and forgetting the view goes red.
* Ruling A being undone by an ordering the client applies for itself (REQ-APP-002).

The derivation is the point. `ContentView.disclosures(_:)` is a hand-written list of five fields --
an enumeration, which this project has repeatedly found to be a denylist wearing better clothes.
This test is what turns that list from silent into gated: it already caught `ranking_effort`, which
the API sends, the Swift model decodes, and no view mentioned.
"""

from __future__ import annotations

import pathlib
import re

CLIENT = pathlib.Path(__file__).resolve().parents[2] / "ios/ModelRanking"
MODELS = CLIENT / "Engine/Models.swift"


def _swift_sources() -> dict[str, str]:
    sources = {p.name: p.read_text(encoding="utf-8") for p in CLIENT.rglob("*.swift")}
    assert sources, f"no Swift sources under {CLIENT}; this test would pass vacuously"
    return sources


def _optional_properties(struct: str) -> set[str]:
    """Every `let name: T?` in one struct — the fields the engine may or may not send."""
    source = MODELS.read_text(encoding="utf-8")
    start = source.index(f"struct {struct}:")
    end = source.index("enum CodingKeys", start)
    return {m.group(1) for m in re.finditer(r"let\s+(\w+):\s*[\w\[\]]+\?", source[start:end])}


# --- REQ-APP-003: every disclosure the API sends is visible ------------------------------------


#: Optional `Answer` fields that are NOT sentences and are deliberately not rendered.
#: An exemption may exist only with a reason, and the reason must survive being read aloud.
NON_DISCLOSURE_ANSWER_FIELDS = {
    # A machine-readable classification ("dated" / "undated" / "mixed" / "unknown"). Its HUMAN form
    # is `evidenceDatingNote`, which IS rendered, and which the engine sets to nil in exactly the
    # cases where there is nothing to disclose (main.py:_evidence_dating). Showing the raw token
    # beside the sentence would say the same thing twice, once in a vocabulary nobody asked for.
    "evidenceDating",
}


def test_the_client_renders_every_optional_field_the_answer_carries() -> None:
    """Trap 2. An `Answer`'s optional fields are its disclosures — that is what optional means here.

    A field the engine sends only when it has something to say is, by construction, the sentence it
    wanted said. If no view names it, the payload carries it and the user never sees it, and every
    gate on both sides stays green.

    **This test was green for the wrong reason and an independent tester caught it.** It matched
    `f".{field}" in body`, so `.evidenceDating` was satisfied by the substring inside
    `.evidenceDatingNote` — zero real references, reported as covered. Any new optional whose name
    is a PREFIX of an already-rendered one was silently exempt. It matches on a word boundary now,
    which immediately exposed that the rule itself over-derived: `evidenceDating` is a
    classification, not a sentence. Exemptions are therefore named and reasoned above rather than
    granted by accident of spelling.
    """
    disclosures = _optional_properties("Answer") - NON_DISCLOSURE_ANSWER_FIELDS
    assert disclosures, "Answer declares no optional fields; the derivation is broken, not clean"

    views = {name: text for name, text in _swift_sources().items() if name != "Models.swift"}
    body = "\n".join(views.values())

    unreferenced = sorted(f for f in disclosures if not re.search(rf"\.{f}\b", body))
    assert not unreferenced, (
        f"the engine can send {unreferenced} and no view in {sorted(views)} names them; a "
        "disclosure the client never reads is one the user never sees"
    )

    stale = sorted(f for f in NON_DISCLOSURE_ANSWER_FIELDS if f not in _optional_properties("Answer"))
    assert not stale, (
        f"{stale} is exempted from the disclosure rule and no longer exists on Answer; an "
        "exemption that outlives its field silently widens the next time the name is reused"
    )


def test_the_disclosure_view_is_actually_reached_from_the_rendered_screen() -> None:
    """The attack the test above cannot see, found by an independent tester and reproduced here.

    Deleting the single call `disclosures(answer)` from the answer section removes EVERY disclosure
    from EVERY screen — and the `disclosures(_:)` function survives further down the file, so all
    the `.staleNotice` / `.closeCall` / `.effortMixNotice` references the field test greps for are
    still present. Green, with nothing disclosed. The field test's own docstring conceded that "a
    reference inside dead code would satisfy it"; this is that concession at whole-feature scale.

    So: the helper must be CALLED, not merely defined. This is still structural — it cannot prove
    the call sits on a code path a user reaches — but it closes the difference between a function
    that exists and a function that runs, which is this project's most-repeated defect class.
    """
    view = (CLIENT / "ContentView.swift").read_text(encoding="utf-8")

    definitions = re.findall(r"func\s+disclosures\s*\(", view)
    assert definitions, "the disclosure view is gone entirely"

    calls = [
        line.strip()
        for line in view.splitlines()
        if re.search(r"(?<!func )\bdisclosures\s*\(", line.split("//", 1)[0])
        and not re.search(r"func\s+disclosures", line)
    ]
    assert calls, (
        "`disclosures(_:)` is defined and never called; every notice the engine sends would be "
        "decoded, held in memory, and shown to nobody"
    )


# --- REQ-APP-005: the client computes no ranking value of its own -------------------------------


#: Numbers the ENGINE decided. Rounding, ordering and comparison of these belong to D-104/105/109.
SERVED_NUMBERS = (
    "score",
    "secondaryScore",
    "blendedPerM",
    "inputPerM",
    "outputPerM",
    "higherEffortScore",
    "eligibleCount",
    "frontierSize",
)


def test_the_client_performs_no_arithmetic_on_a_number_the_engine_sent() -> None:
    """Trap 1, and it protects three ADRs at once.

    D-109 puts rounding at the output boundary, D-105 forbids cross-scale averaging and D-104 keeps
    the scoring path deterministic. All three are engine invariants, and the cheapest way to break
    every one of them is a client that computes "just this one percentage" locally. A saving of
    "17% cheaper" that the app worked out itself is a second scoring implementation with no tests
    and no ADR.

    Fails on `pick.score - other.score`, `blendedPerM / 1000`, or a `%` computed in the view.
    """
    offenders: list[str] = []
    for name, text in _swift_sources().items():
        for lineno, line in enumerate(text.splitlines(), start=1):
            code = line.split("//", 1)[0]
            for field in SERVED_NUMBERS:
                # `x.field <op>` or `<op> x.field`, where op is real arithmetic. `.count` and
                # string interpolation are untouched; so is `.score` passed to a formatter.
                if re.search(rf"\.{field}\s*[-+*/]\s*[\w(.]", code) or re.search(
                    rf"[\w)]\s*[-+*/]\s*\w+\.{field}\b", code
                ):
                    offenders.append(f"{name}:{lineno}: {line.strip()}")
    assert not offenders, (
        "the client does arithmetic on a value the engine computed, which is a second scoring "
        "implementation with no ADR:\n  " + "\n  ".join(offenders)
    )


# --- REQ-APP-002: Ruling A survives the client -------------------------------------------------


def test_the_client_applies_no_ordering_of_its_own() -> None:
    """Ruling A's real cost, three milestones after the ruling.

    `/v1` emits two coding answers in a documented non-semantic order and states in the envelope
    that the order carries no meaning. A client that sorts them — by score, by name, by anything —
    manufactures the ranking the engine refused to publish, and it would look perfectly reasonable
    in review.

    **The limit, corrected after an independent tester walked through it twice.** This bans a list
    of SPELLINGS -- it is not, as this docstring once claimed, "deliberately blunt: ANY sort fails".
    A hand-rolled insertion sort over `answers` contains no banned identifier and passes, as does
    any comparison written out longhand. The list is widened here to cover `max(by:)`/`min(by:)`,
    which is how the tester picked a winner across the two coding surfaces, but the honest statement
    is that **this is a tripwire on the obvious spellings, not a proof of absence.** The proof would
    need a UI test asserting the two surfaces render as peers, and there is no iOS test target
    (W-038).
    """
    offenders: list[str] = []
    for name, text in _swift_sources().items():
        for lineno, line in enumerate(text.splitlines(), start=1):
            code = line.split("//", 1)[0]
            if re.search(
                r"\.(sorted|reversed|shuffled)\s*[({]|\.sort\s*\(|"
                r"\.(max|min)\s*\(\s*by\s*:|\.swapAt\s*\(",
                code,
            ):
                offenders.append(f"{name}:{lineno}: {line.strip()}")
    assert not offenders, (
        "the client orders a collection itself; if this is the answers or the ranking it "
        "undoes Ruling A, and if it is something else it needs a reason recorded here:\n  "
        + "\n  ".join(offenders)
    )


# --- REQ-APP-001: real data, no fixtures in the shipping target ---------------------------------


def test_the_shipping_client_carries_no_canned_payload() -> None:
    """A mock that ships is a screen that lies while the engine is down.

    The app is supposed to state a failure, not fall back to data that looks like an answer. This
    checks the target directory for both shapes a fixture takes: a bundled `.json` resource and a
    payload pasted into the Swift as a literal.
    """
    resources = [p.name for p in CLIENT.rglob("*.json")]
    assert not resources, f"a JSON resource ships inside the app target: {resources}"

    # The quotes may be ESCAPED. A payload pasted into Swift arrives as `"{\"api_version\": ...}"`,
    # so a search for a bare `"api_version"` finds nothing — which is how the first version of this
    # test passed while a canned payload sat in the view. Both spellings are matched now, and the
    # triple-quoted form, which escapes nothing at all.
    # `Models.swift` is NO LONGER EXCLUDED. It used to be, so its `CodingKeys` string constants
    # would not false-positive -- and an independent tester shipped a canned payload inside exactly
    # that exclusion. The hole was the size of the requirement. The check now matches a marker in
    # JSON KEY POSITION (preceded by `{` or `,`, followed by `:`), which a `case x = "api_version"`
    # declaration can never be, so every file is scanned and no exemption is needed.
    markers = ("api_version", "ordering_note", "best_value", "unavailable_reason")
    embedded = [
        f"{name} carries {marker!r} in JSON key position"
        for name, text in _swift_sources().items()
        for marker in markers
        if re.search(rf'[{{,]\s*\\?"{marker}\\?"\s*:', text)
    ]
    assert not embedded, (
        "a payload appears as a literal in a view, which is how a fixture survives into a "
        f"release build: {embedded}"
    )


# --- REQ-APP-004: the app degrades honestly -----------------------------------------------------


def test_no_failure_switch_falls_back_to_a_default_clause() -> None:
    """The compiler is the gate here, and a `default:` is what disables it.

    Swift requires a switch over an enum to be exhaustive, so adding an `EngineError` case without
    giving it a sentence is a BUILD failure — which is the strongest guarantee available in a
    repository with no iOS test target. Writing `default:` in either switch throws that away: the
    new case compiles, and the person holding the phone is told whatever the fallback says instead
    of what actually happened. That is Trap 2 with the compiler's help removed.

    This test does not check that the sentences are good. It checks that a new failure mode CANNOT
    be added silently.
    """
    client = (CLIENT / "Engine/EngineClient.swift").read_text(encoding="utf-8")
    enum_start = client.index("enum EngineError")
    enum_end = client.index("struct EngineClient")
    body = client[enum_start:enum_end]

    offenders = [
        f"line {body[:m.start()].count(chr(10)) + client[:enum_start].count(chr(10)) + 1}"
        for m in re.finditer(r"^\s*default\s*:", body, re.MULTILINE)
    ]
    assert not offenders, (
        "EngineError has a `default:` clause, so a new failure case would compile without a "
        f"message and reach the user as a generic sentence: {offenders}"
    )

    cases = set(re.findall(r"^\s*case\s+(\w+)", body, re.MULTILINE))
    assert len(cases) >= 3, f"expected the failure vocabulary to be named; found {cases}"


def test_the_client_bounds_how_long_it_will_wait() -> None:
    """"A spinner that never ends" is listed as a failure state, not as a slow success.

    `URLSession.shared` waits SIXTY seconds by default. The screen shows `ProgressView` until the
    request returns, so an engine that accepts the connection and stalls produces exactly the
    screen the plan forbids — and it does so while every test passes, because nothing here is
    wrong, only unbounded.

    Fails by removing the timeout configuration or by taking `URLSession.shared` as the default
    session again.
    """
    client = (CLIENT / "Engine/EngineClient.swift").read_text(encoding="utf-8")

    assert "timeoutIntervalForRequest" in client, (
        "the client sets no request timeout; a stalled engine leaves the spinner running"
    )
    assert "timeoutIntervalForResource" in client, (
        "only the request is bounded; a response that dribbles bytes forever is still unbounded"
    )

    # THE VALUE, not the symbol. An independent tester changed `requestTimeout` from 10 to 86_400
    # and this test stayed green: both symbols were still present, `URLSession.shared` was still
    # absent, `case timedOut` still existed. A 24-hour spinner satisfied every assertion above --
    # which is the exact failure state the docstring claims to prevent. A configuration that is
    # PRESENT is not a configuration that BOUNDS.
    declared = re.search(r"static let requestTimeout\s*=\s*([\d_]+)", client)
    assert declared, "requestTimeout is no longer a literal this test can read"
    seconds = int(declared.group(1).replace("_", ""))
    assert 0 < seconds <= 30, (
        f"the client waits {seconds} seconds before it owes the user a sentence; anything past "
        "~30 is the endless spinner wearing a number"
    )
    assert "session: URLSession = .shared" not in client, (
        "URLSession.shared is the default again, and it carries the 60-second wait this "
        "configuration exists to replace"
    )
    assert re.search(r"case\s+timedOut", client), (
        "a timeout would be reported as `unreachable`, whose recovery tells the user to start an "
        "engine that is already running"
    )


def test_every_failure_the_client_names_reaches_the_screen_with_a_sentence() -> None:
    """A named error that no view renders is the blank screen REQ-APP-004 forbids.

    The failure view must show BOTH halves: the condition (`errorDescription`) and what to do about
    it (`recovery`). Rendering only the first gives a dead end; rendering only the second gives
    advice about nothing.
    """
    # COMMENTS STRIPPED. An independent tester replaced the failure view with
    # `Text("Something went wrong.")` and left `.errorDescription` / `.recovery` surviving as a
    # comment; this test greps raw file text and stayed green. That is precisely the defect this
    # module already claimed to have fixed elsewhere -- "a test that matches an identifier rather
    # than a read is measuring spelling" -- committed again two functions later.
    views = "\n".join(
        "\n".join(line.split("//", 1)[0] for line in text.splitlines())
        for name, text in _swift_sources().items()
        if name not in {"Models.swift", "EngineClient.swift"}
    )
    # The PROPERTY ACCESS, not the word. The first version of this test asked whether "recovery"
    # appeared anywhere in the views, and a mutant that stopped reading `error.recovery` while
    # keeping `recovery` as a local binding name walked straight through it. A test that matches an
    # identifier rather than a read is measuring spelling.
    assert ".errorDescription" in views, "no view reads the condition; the screen would be blank"
    assert ".recovery" in views, (
        "no view reads the remedy; the user is told what broke and nothing about what to do"
    )
