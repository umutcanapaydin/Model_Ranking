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


#: Files permitted to do arithmetic on a served score, each with the ADR that permits it. D-138:
#: a rank range compares two served scores against the engine's own published margin and prints
#: no new number. Every other file is still held to REQ-APP-005.
SCORE_ARITHMETIC_PERMITTED = {"Uncertainty.swift": "D-138"}


def test_score_arithmetic_happens_only_where_an_adr_permits_it() -> None:
    """M13-W2 re-review NEW-1: the tripwire above could not see the one crossing that shipped.

    `rankRanges` subtracts served scores held in local bindings (`other - score`), which the
    property-access patterns above were written not to match. Rather than leave the tripwire
    knowingly blind, this matches arithmetic on a LOCAL named `score` or `scores` as well, and the
    one file allowed to do it is named with its ADR. A second file doing it fails here until
    somebody writes the ADR that permits it.

    Laundering through a binding with some other name still passes. That half of REQ-APP-005 stays
    PARTIAL, as its prd row says.
    """
    pattern = re.compile(r"\bscores?\b\s*[-+*/]\s*[\w(.]|[\w)]\s*[-+*/]\s*\bscores?\b")
    offenders: list[str] = []
    used: set[str] = set()
    for name, text in _swift_sources().items():
        for lineno, line in enumerate(text.splitlines(), start=1):
            if not pattern.search(line.split("//", 1)[0]):
                continue
            if name in SCORE_ARITHMETIC_PERMITTED:
                used.add(name)
            else:
                offenders.append(f"{name}:{lineno}: {line.strip()}")

    assert not offenders, (
        "arithmetic on a served score outside the files an ADR permits:\n  " + "\n  ".join(offenders)
    )
    stale = sorted(set(SCORE_ARITHMETIC_PERMITTED) - used)
    assert not stale, (
        f"{stale} is permitted to do score arithmetic and no longer does; an exemption that outlives "
        "its reason silently widens the next time the file changes"
    )


# --- REQ-APP-002: Ruling A survives the client -------------------------------------------------


#: Sorts this client may perform, keyed on (file, the RECEIVER of the sort call), each with its
#: reason. Review m-3 (M14-W3/W4): the key used to be a substring of the LINE, so any line in
#: `FrontDoor.swift` mentioning `entries.` passed -- including one that also sorted the engine's
#: ranking. Now every sort call on a line is checked on its own, and each must be applied directly
#: to a permitted receiver (`entries`, not `x.entries` or `answer.ranking`).
SORTING_PERMITTED = {
    ("FrontDoor.swift", "entries"): (
        "M14-W3, REQ-GAP-002: the gap register orders the OWNER'S unanswered questions by how often "
        "they were asked. It is never an answer, a ranking or a model -- Ruling A is about the "
        "engine's answers, which this collection never holds."
    ),
    ("FrontDoor.swift", "entries.indices"): (
        "M14-W3, REQ-GAP-001: when the register is full, the least-asked entry makes room."
    ),
}

_SORT_CALL = re.compile(
    r"\.(sorted|reversed|shuffled)\s*[({]|\.sort\s*\(|\.(max|min)\s*\(\s*by\s*:|\.swapAt\s*\("
)


def _sort_receiver(code: str, start: int) -> str:
    """The dotted expression a sort call at `start` is applied to: `entries.indices` for
    `entries.indices.min(by:`, `answer.ranking` for `answer.ranking.sorted {`."""
    match = re.search(r"([A-Za-z_][\w]*(?:\??\.[A-Za-z_]\w*)*)$", code[:start])
    return match.group(1) if match else ""


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
    used: set[tuple[str, str]] = set()
    for name, text in _swift_sources().items():
        for lineno, line in enumerate(text.splitlines(), start=1):
            code = line.split("//", 1)[0]
            for call in _SORT_CALL.finditer(code):
                key = (name, _sort_receiver(code, call.start()))
                if key in SORTING_PERMITTED:
                    used.add(key)
                    continue
                offenders.append(f"{name}:{lineno}: {line.strip()}")
    stale = sorted(set(SORTING_PERMITTED) - used)
    assert not stale, f"{stale} is permitted to sort and no longer does; remove the exemption"
    assert not offenders, (
        "the client orders a collection itself; if this is the answers or the ranking it "
        "undoes Ruling A, and if it is something else it needs a reason recorded here:\n  "
        + "\n  ".join(offenders)
    )


#: Collections this client orders BY HAND, each with its reason — the route the tripwire above asks
#: for (M13-W3 review MINOR-2). A hand-rolled ordering is exactly what that tripwire cannot see, so
#: a sanctioned one is recorded here rather than passing quietly through its blind spot.
ORDERED_BY_HAND = {
    "Router.swift": (
        "SimilarityRouter keeps its three closest routing HINTS by insertion, to offer two "
        "alternatives. Hints are the router's own and never answers or models, so Ruling A is "
        "untouched"
    ),
}


def test_every_hand_ordering_is_recorded_and_still_exists() -> None:
    """An insertion at an index is how a hand-rolled sort is spelled; each one must be recorded."""
    offenders: list[str] = []
    used: set[str] = set()
    for name, text in _swift_sources().items():
        code = "\n".join(line.split("//", 1)[0] for line in text.splitlines())
        # `.*` and not `[^)]*`: the element inserted is often a tuple, `(hint.id, score)`, and a
        # pattern that stops at its first `)` never reaches `at:`.
        if re.search(r"\.insert\(.*\bat:", code):
            (used.add(name) if name in ORDERED_BY_HAND else offenders.append(name))
    assert not offenders, f"unrecorded hand ordering in {offenders}; say why in ORDERED_BY_HAND"
    stale = sorted(set(ORDERED_BY_HAND) - used)
    assert not stale, f"{stale} is recorded as ordering by hand and no longer does"


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


def test_the_client_refuses_a_redirect_that_leaves_its_configured_host() -> None:
    """M8 security review, M-4: the client followed server-controlled redirects.

    `URLSession` follows up to twenty redirects by default. A `302 Location:` from the engine — or
    injected on the cleartext hop — therefore chose the next host this app would contact. The
    security review before this one asserted the opposite in as many words: *"there is no path
    where a served value becomes a URL, so nothing in a response can redirect the app at another
    host."* The `Location` header is that path, and it was unmitigated.

    Dies to: dropping the delegate from the `data(from:delegate:)` call, or widening the delegate
    to accept a different host.
    """
    client = (CLIENT / "Engine/EngineClient.swift").read_text(encoding="utf-8")

    assert "willPerformHTTPRedirection" in client, (
        "no redirect delegate; the engine's Location header decides where this app goes next"
    )
    assert re.search(r"data\(\s*from:[^)]*delegate:", client, re.S), (
        "the delegate exists and is not passed to the request that needs it — an injection point "
        "that cannot inject, which is this project's most-repeated defect"
    )
    assert re.search(r"request\.url\?\.host\s*==\s*host", client), (
        "the redirect delegate no longer compares hosts; a same-host check that does not check "
        "the host follows every redirect while looking like a control"
    )


def test_the_one_moment_transport_security_fires_is_not_reported_as_a_dead_server() -> None:
    """M8 security review: `URLError -1022` fell into `default:` and became `.unreachable`.

    Whose recovery text says *"Start it with `make run` in the engine repository."* So the single
    moment the platform's cleartext protection actually works, the app tells the developer their
    server is down — and the shortest fix for a server that is not down is
    `NSAllowsArbitraryLoads`, which permits cleartext to every host. The mitigation for that risk
    is naming the condition, which is what this pins.
    """
    client = (CLIENT / "Engine/EngineClient.swift").read_text(encoding="utf-8")

    assert "appTransportSecurityRequiresSecureConnection" in client, (
        "an ATS refusal is still mapped to 'the engine is not answering'"
    )
    assert re.search(r"case\s+insecureTransport", client), "no named case for a refused cleartext load"

    # The warning must EXIST and must reach whoever would otherwise apply the one-line "fix".
    # It used to live in `recovery`, and this assertion used to look for it in the 600 characters
    # after that case. At M12-W2 the user-facing strings were rewritten for an audience that does
    # not own a repository, and the developer half moved to `diagnostic` — so a position-anchored
    # assertion failed on a change that kept every word of the mitigation.
    #
    # Pinning the PRESENCE rather than the OFFSET is the repair. A test that fails when text moves
    # teaches people to leave text where it is, which is how a user-facing string ends up
    # explaining App Transport Security to a CFO.
    assert "NSAllowsArbitraryLoads" in client, (
        "the ATS exception is no longer warned against anywhere in the client; the whole point of "
        "naming this case is to head off the one-line 'fix' that ships cleartext to every host"
    )
    # And it must NOT be in the sentence a reader sees.
    recovery = client[client.index("var recovery"):client.index("var diagnostic")]
    assert "NSAllowsArbitraryLoads" not in recovery, (
        "the person holding the phone is being told about App Transport Security"
    )


def test_the_client_says_when_the_full_ranking_is_wider_than_the_budget() -> None:
    """M8 review MAJOR-3: one payload, two accounts of the same query, and the screen was silent.

    `/v1` publishes the FULL ranking beside the three picks (D-125), which is correct and
    deliberate — but a `budget=low` answer reports 25 eligible models and then serves 58 ranking
    rows whose most expensive is $36/1M, with no per-row marker. The engine already carries both
    numbers; the screen showed only one of them, under a heading that reads as a continuation of
    the budgeted picks above it.

    The client renders the difference. It computes nothing — both values are served — so this does
    not touch REQ-APP-005, and no contract moved, which matters because D-124's single revision is
    already spent.

    Dies to: dropping the comparison, or rendering only `ranking.count`.
    """
    # Read the whole client, not one file. At M12-W4 the comparison moved out of `ContentView`
    # into `UIText.seeAll`, where it is tested directly in Swift and composed in two languages —
    # and this assertion failed on a change that kept every part of the behaviour.
    #
    # **Third time this shape has cost a wave** (the ordering note, the ATS warning, this). A test
    # that pins WHERE logic lives fails when it moves and passes when it is deleted from the place
    # it moved to. What must hold is that the client READS both numbers and COMPARES them; which
    # file does it is not the reader's concern and should not be the test's.
    code = "\n".join(
        "\n".join(line.split("//", 1)[0] for line in path.read_text(encoding="utf-8").splitlines())
        for path in sorted(CLIENT.rglob("*.swift"))
    )

    assert ".eligibleCount" in code or "eligible:" in code, (
        "the client never reads eligible_count, so it cannot tell the reader that the list below "
        "is wider than what their budget affords"
    )
    assert re.search(r"eligible\w*\s*<\s*\w*[Tt]otal|eligibleCount\s*<\s*\w+\.ranking\.count", code), (
        "the client no longer compares the eligible count against the published ranking; the "
        "'See all N' heading then reads as a continuation of the budgeted picks above it"
    )


def test_the_screen_calls_the_uncertainty_functions_it_depends_on() -> None:
    """M13-W2 Tester finding: every change to how `ContentView` calls the Engine stayed green.

    `swift test` does not compile `ContentView`, so a view that stopped passing the engine's
    published margin (and printed exact positions again), or that went back to rendering the raw
    basis, broke nothing. Structural, like every test in this file: it proves the calls exist
    outside comments WITH the arguments that carry the engine's facts, and that their results are
    the text rendered — not that a reader sees them.

    **The first version checked only that the function NAMES appeared**, and the Tester seat's
    re-run showed what that let through: `PickRow` losing `ranges: ranges` (the picks read `#2 of
    50` again — the defect REQ-UNC-001 removes), `Text(pick.confidenceBasis)` in place of the
    evidence line, a nil margin into `leaderSentence`, and the leader note never rendered.
    """
    view = "\n".join(
        line.split("//", 1)[0]
        for line in (CLIENT / "ContentView.swift").read_text(encoding="utf-8").splitlines()
    )

    assert re.search(
        r"rankRanges\(\s*answer\.ranking\.map\(\\\.score\),\s*margin:\s*info\?\.closeCallMargin",
        view,
    ), "the ranking is not ranged with the margin the engine publishes (D-138)"

    pick_row = re.search(r"\bPickRow\(\s*\n(.*?)\n\s*\)", view, re.S)
    assert pick_row, "the home screen no longer builds a PickRow"
    for argument in (
        "ranges: ranges",
        "secondaryBenchmark: info?.secondaryBenchmark",
        "secondaryAgeDays: info?.secondaryAgeDays",
        "anchor: info?.scoreAnchor",  # D-143 (M14-W4): the card reads out of 100
    ):
        assert argument in pick_row.group(1), f"the picks are built without `{argument}`"

    # Review M-4 (M14-W3/W4): the ROWS are pinned too. A mutant anchoring the preview rows and the
    # full list on `answer.ranking.map(\.score).max()` -- the board maximum REQ-SCR-003 forbids --
    # compiled and passed every test, because only the picks were checked.
    ranked_row = re.search(r"RankedRow\((.*?)\n\s*\)", view, re.S)
    assert ranked_row, "the preview rows are no longer built here"
    assert "anchor: category(for: answer)?.scoreAnchor" in ranked_row.group(1), (
        "the preview rows are not anchored on the surface's pinned anchor"
    )
    ranking_list = re.search(r"RankingList\((.*?)\n\s*\)", view, re.S)
    assert ranking_list, "the full ranking is no longer built here"
    assert "anchor: category(for: answer)?.scoreAnchor" in ranking_list.group(1), (
        "the full ranking is not anchored on the surface's pinned anchor"
    )
    assert not re.search(r"anchor:[^\n]*\.(max|min)\s*\(", view), (
        "an anchor is derived from the board itself (REQ-SCR-003)"
    )
    # M-1/M-2: the sentences speak the card's unit.
    assert re.search(r"whySentence\(cardFact\(", view), "the why line still speaks native Elo"
    assert re.search(r"tradeOffSentence\(cardFact\(", view), "the trade-off still speaks native Elo"
    assert re.search(
        r"leaderSentence\([^)]*leader:\s*answer\.ranking\.first\?\.score,\s*"
        r"anchor:\s*info\?\.scoreAnchor",
        view,
    ), (
        "the tie note is built without the surface's anchor"
    )

    assert re.search(r"\brankLabel\(", view), "the picks no longer say where they sit"
    assert re.search(r"\bshortRankLabel\(", view), "the ranking rows no longer say where they sit"
    assert re.search(r"\bevidenceLine\(", view), "the picks no longer state how they were measured"
    assert re.search(r"Text\(evidence\)", view), "the evidence line is composed and never rendered"
    assert not re.search(r"Text\(pick\.confidenceBasis\)", view), (
        "the engine's basis is rendered directly, bypassing the composer that never says "
        "'confidence' and says nothing on a self-contradicting payload"
    )
    assert re.search(
        r"leaderSentence\(\s*ranges:\s*ranges,\s*margin:\s*info\?\.closeCallMargin", view
    ), "the leader's tie is stated without the engine's margin"
    assert re.search(r"Text\(leaderNote\)", view), "the leader's tie is composed and never shown"


def test_the_front_door_is_wired_to_the_logic_it_depends_on() -> None:
    """M13-W3, REQ-ASK-001..004: the front door's rules live in `FrontDoor.swift`, where `swift
    test` runs them. This pins that `ContentView` actually goes through them.

    Written before the wave's review rather than after it, because W2's Tester seat showed what
    happens otherwise: every argument-level change to how the screen called the Engine stayed green.
    Structural, like the rest of this file.
    """
    # Split on the RAW text, then strip comments: the marker is itself a comment, so stripping first
    # erased it and made "the home screen" the whole file, the full ranking's filter included.
    raw = (CLIENT / "ContentView.swift").read_text(encoding="utf-8")
    assert "// MARK: - Rows" in raw, "the marker ending the home screen's code has moved"
    home = "\n".join(
        line.split("//", 1)[0] for line in raw[: raw.index("// MARK: - Rows")].splitlines()
    )

    # REQ-ASK-001: focusable, submittable from Return AND from a visible button, never twice.
    assert re.search(r"\.focused\(\$questionFocused\)", home), "the field has no focus binding"
    assert re.search(r"\.onSubmit\(submit\)", home), "Return does not submit"
    assert re.search(r"Button\(action:\s*submit\)", home), "there is no visible way to send"
    assert re.search(
        r"\.disabled\(!canSubmit\(question,\s*inFlight:\s*routingInFlight\)", home
    ), "the send button is not governed by the tested submission rule"
    # Every question is asked at `unlimited`: the budget control is gone, and a hidden cap would
    # narrow the ranking with nothing on screen saying so (W3 review MAJOR-3, mutant M2).
    assert re.search(r'private let budget = "unlimited"', home), "a budget cap is back, unseen"
    submit = re.search(r"func submit\(\)\s*\{(.*?)\n    \}", home, re.S)
    assert submit, "the single submission path is gone"
    assert "guard canSubmit(" in submit.group(1), "submission skips the tested rule"
    assert re.search(
        r"routingInFlight = true[\s\S]*Task \{", submit.group(1)
    ), "the in-flight flag is not set before the task starts, so a second tap can route twice"

    # REQ-ASK-002: the reader's own words, and a correction reaching every surface.
    assert re.search(
        r"echoLine\(question:\s*asked", home
    ), "the echo quotes the live field, not the question that was actually routed"
    assert re.search(r"surfaceChoices\(categories", home), "the Change sheet is not the full list"
    assert "outcome.alternatives" in home, "the one-tap alternatives are never shown"

    # REQ-ASK-002/003: a routed question LOADS the surface it was routed to — "returns a ranking"
    # (W3 review MAJOR-3, mutant M5) — and its echo appears only once that answer has loaded.
    ask = re.search(r"private func ask\(\) async \{(.*?)\n    \}", home, re.S)
    assert ask, "the question path is gone"
    body = ask.group(1)
    assert re.search(
        r"if outcome\.categoryID != task \{\s*task = outcome\.categoryID\s*await load\(\)", body
    ), "a routed question no longer loads the surface it was routed to"
    assert body.index("routing = outcome") > body.rindex(
        "await load()"
    ), "the echo is shown above the previous surface's ranking while the new one loads"

    # REQ-ASK-004 for the QUESTION (W3 review BLOCKING-2): a ticket before the router is awaited,
    # checked after it, and retired by a `Change` selection.
    assert re.search(
        r"let ticket = routingGate\.begin\(\)\s*let outcome = await router\.route", body
    ), "routing takes no ticket before it suspends"
    assert re.search(
        r"await router\.route\([^)]*\)\s*guard routingGate\.isCurrent\(ticket\) else \{ return \}",
        body,
    ), "a late routing result is applied whatever the reader chose meanwhile"
    select = re.search(r"private func select\(_ id: String\) \{(.*?)\n    \}", home, re.S)
    assert select and "routingGate.invalidate()" in select.group(
        1
    ), "a Change selection does not retire the question still routing"

    # REQ-ASK-003: the sentence above an unmeasured answer, in the colour that marks it (M6), and
    # the on-device reason whenever the model did not route (M4).
    assert re.search(
        r"Text\(routingNotice\(outcome,\s*language\)\)\s*\.font\(\.footnote\)\s*"
        r"\.foregroundStyle\(outcome\.unmeasured \? \.orange : \.secondary\)",
        home,
    ), "the routing notice is gone, or no longer marks an unmeasured answer"
    assert re.search(
        r"outcome\.tier != \.model, let help = onDevice\.help\(language\)", home
    ), "the on-device reason is not said when the model did not route"

    # REQ-ASK-004 for loads: every result is applied only DIRECTLY after its guard (W3 review
    # MAJOR-3, mutant M1 — counting guard lines let one move below the state change it protects).
    load = home[home.index("private func load() async {") :]
    assert "gate.begin()" in load, "loads take no ticket"
    before = re.findall(r"\n([^\n]*)\n[ \t]*state = \.(?:loaded|failed)\(", load)
    assert len(before) >= 3, "the load no longer applies both an answer and a failure"
    assert all(
        line.strip() == "guard gate.isCurrent(ticket) else { return }" for line in before
    ), f"a result is applied without the guard directly above it: {before}"
    assert re.search(
        r"if gate\.isCurrent\(ticket\) \{ reloading = false \}", load
    ), "an abandoned load can clear the progress of the current one"
    assert re.search(
        r"!fresh\.isEmpty,\s*gate\.isCurrent\(ticket\)", load
    ), "a stale surface list can overwrite the current one"

    # The correction path, end to end (W3 Tester WF5, WF10, WF11, WF13): `Change` opens the sheet,
    # the sheet selects, and every alternative shown selects.
    assert re.search(
        r"Button\(UIText\.change\(language\)\)\s*\{\s*choosingSurface = true\s*\}", home
    ), "Change does not open the sheet"
    assert re.search(
        r"\.sheet\(isPresented:\s*\$choosingSurface\)\s*\{\s*surfaceSheet\s*\}", home
    ), "the sheet of surfaces is never presented"
    assert re.search(
        r"Button\s*\{\s*select\(choice\.id\)\s*\}", home
    ), "choosing a surface in the sheet does nothing"
    assert re.search(
        r"ForEach\(outcome\.alternatives,\s*id:\s*\\\.self\)\s*\{\s*id in\s*"
        r"Button\(surfaceTitle\(id\)\)\s*\{\s*select\(id\)\s*\}",
        home,
    ), "an alternative is shown and does not select"

    # The echo is rendered, and it quotes what was ASKED (WF8, WF14).
    assert re.search(r"Text\(echo\)", home), "the echo is composed and never shown"
    assert "asked = typed" in body, "the echo quotes nothing the reader asked"

    # The field unlocks after every question however it ends (WF12), and a selection clears the
    # echo of the choice it overruled (WF9).
    assert re.search(
        r"defer \{ routingInFlight = false \}", body
    ), "the field stays locked after the first question"
    assert "routing = nil" in select.group(1), "a selection keeps the echo it overruled"

    # A late routing result is dropped even after its own load (W3 re-review NEW-2), and with no
    # surface list the send button and `Change` are disabled rather than silently doing nothing.
    assert re.search(
        r"await load\(\)\s*guard routingGate\.isCurrent\(ticket\) else \{ return \}", body
    ), "a routing result is applied after its load even if the reader chose meanwhile"
    assert re.search(
        r"\.disabled\(!canSubmit\(question,\s*inFlight:\s*routingInFlight\)\s*\|\|\s*"
        r"categories\.isEmpty\)",
        home,
    ), "send stays enabled with no surfaces to route to"
    assert re.search(
        r"Button\(UIText\.change\(language\)\)\s*\{\s*choosingSurface = true\s*\}\s*"
        r"\.font\(\.subheadline\)\s*\.disabled\(categories\.isEmpty\)",
        home,
    ), "Change opens an empty sheet when there are no surfaces"
    # ...and the card SAYS why (CE), and a question asked with no list re-reads it first (AK1).
    assert re.search(
        r"if categories\.isEmpty \{\s*Text\(UIText\.surfacesUnavailable\(language\)\)", home
    ), "with no surfaces the controls go dead and nothing says why"
    assert re.search(r"if categories\.isEmpty \{ await load\(\) \}", body), (
        "a question asked before the surface list arrived is dropped instead of retried"
    )

    # The controls this wave removed stay removed from the home screen.
    assert "budgetStrip" not in home and "categoryStrip" not in home
    assert ".searchable(" not in home, "a second text field is back on the home screen"


def test_every_score_on_screen_goes_through_the_figures_line() -> None:
    """REQ-CMP-004, M13-W4 review MAJOR-1: a served score reaches the screen only via `figuresLine`.

    `swift test` proves what `figuresLine` returns and cannot see whether the view calls it. The
    seat replaced each call with a hand-built `Text` -- bare `Score 161.7` on a card, `161.7 ECI` in
    every ranking row -- and both mutants passed every test. Each half below fails on one of them.
    """
    view = "\n".join(
        line.split("//", 1)[0]
        for line in (CLIENT / "ContentView.swift").read_text(encoding="utf-8").splitlines()
    )

    for struct, value, rank in (
        ("PickRow", "pick", r"rankText\s*!=\s*nil"),
        ("RankedRow", "row", r"rank\s*!=\s*nil"),
    ):
        start = view.index(f"struct {struct}: View")
        end = view.find("\nstruct ", start + 1)
        body = view[start : end if end != -1 else len(view)]
        call = (
            rf"figuresLine\(\s*score:\s*{value}\.score,\s*metric:\s*{value}\.metric,\s*"
            rf"blendedPerM:\s*{value}\.blendedPerM,\s*language,\s*ranked:\s*{rank},\s*"
            # D-143 (M14-W4): and the surface's anchor, or an Elo row prints a different kind of
            # number from the card above it.
            rf"anchor:\s*anchor\s*\)"
        )
        assert re.search(call, body), (
            f"`{struct}` no longer renders its score through `figuresLine` with its own score, "
            "metric, price and whether a rank is shown beside it"
        )

    # Nothing else turns a served score into text. A score may appear as a key path mapped into the
    # rank ranges, which never print it, or as the `score:` argument of a composer, and nowhere
    # else. The key path is held to `.map(` too (W4 re-review NEW-3): `row[keyPath: \.score]` reads
    # the same number by another door.
    for match in re.finditer(r"(\\)?\.score\b", view):
        before = view[max(0, match.start() - 40) : match.start()]
        line = view.count("\n", 0, match.start()) + 1
        if match.group(1):
            assert before.endswith(".map("), (
                f"ContentView.swift:{line} uses a `\\.score` key path outside `.map(`; only the rank "
                "ranges may read the served scores as a column"
            )
            continue
        # D-143 amendment (review M-1/M-2): the ENGINE'S leader is handed to the two composers that
        # restate a distance on the /100 scale (`anchoredFact`, `leaderSentence`). They print a
        # difference, never the leader's score, and live in `Uncertainty.swift` (D-138).
        leader_argument = re.search(r"leader:\s*(answer\.)?ranking\.first\?$", before)
        assert re.search(r"score:\s*\w+$", before) or leader_argument, (
            f"ContentView.swift:{line} reads a served score outside a composer's `score:` argument; "
            "a score printed by hand says nothing about what it is out of (D-140)"
        )


def test_the_detail_screen_is_reachable_and_composes_nothing_itself() -> None:
    """REQ-DTL-001/002 (M15-W2): the unit D-143 took off the card has somewhere to be.

    W-105: the M14 plan's mitigation for hiding the metric name was "it stays available on the
    detail screen", and the closure seat found there was no detail screen at all — so the product
    removed the unit from every card and row with nowhere for a reader to find it.

    Structural, like every test in this file, because `swift test` does not compile
    `ContentView.swift`. **Rewritten after the W2 review**, which showed the first version proving
    much less than its own message claimed: it pinned argument NAMES, so a detail screen opened
    with `anchor: nil`, with `anchor:` and `closeCallMargin:` swapped, or with `benchmark: ""`
    passed while showing the reader a different fact from the card that opened it (W-084's shape,
    one screen later). It now pins each door's whole argument list to the surface's own facts.
    """
    view = "\n".join(
        line.split("//", 1)[0]
        for line in (CLIENT / "ContentView.swift").read_text(encoding="utf-8").splitlines()
    )

    assert "struct ModelDetail: View" in view, "the detail screen is gone"

    # Both doors, and each one's arguments as a WHOLE expression: the value, not the label.
    doors = {
        "pick": (
            r"ModelDetail\(\s*subject:\s*pick,\s*benchmark:\s*benchmark,\s*"
            r"language:\s*language,\s*anchor:\s*anchor,\s*"
            r"closeCallMargin:\s*closeCallMargin,\s*"
            r"secondaryBenchmark:\s*secondaryBenchmark,\s*"
            r"secondaryAgeDays:\s*secondaryAgeDays,\s*"
            # M16-W2 (D-152, D-153): the floor and what the price leaves out, the same way.
            r"minQuality:\s*minQuality,\s*priceExcludes:\s*priceExcludes\s*\)"
        ),
        "row": (
            r"ModelDetail\(\s*subject:\s*row,\s*benchmark:\s*answer\.primaryBenchmark,\s*"
            r"language:\s*language,\s*anchor:\s*anchor,\s*"
            r"closeCallMargin:\s*closeCallMargin,\s*"
            r"secondaryBenchmark:\s*secondaryBenchmark,\s*"
            r"secondaryAgeDays:\s*secondaryAgeDays,\s*"
            # M16-W2 (D-152, D-153): the floor and what the price leaves out, the same way.
            r"minQuality:\s*minQuality,\s*priceExcludes:\s*priceExcludes\s*\)"
        ),
    }
    for opened, pattern in doors.items():
        assert re.search(pattern, view), (
            f"the {opened} does not open the detail screen with this surface's own facts, in "
            "full: a swapped, dropped or defaulted argument makes the screen contradict the card "
            "that opened it"
        )
    assert len(re.findall(r"ModelDetail\(", view)) == len(doors), (
        "a third place builds a detail screen; every door must be pinned here or the pinning is "
        "decorative"
    )

    # And the card carries what it must pass on: a `PickRow` built without the board name gave
    # every pick a detail screen reading `Measured on:` with nothing after it (review M-6).
    pick_row = re.search(r"PickRow\((.*?)\n\s*\)", view, re.S)
    assert pick_row, "the picks are no longer built here"
    for argument in ("benchmark: answer.primaryBenchmark", "closeCallMargin: info?.closeCallMargin",
                     "minQuality: info?.minQuality", "priceExcludes: info?.priceExcludes"):
        assert argument in pick_row.group(1), f"the picks are built without `{argument}`"

    # The view renders the Engine's facts and NOTHING else. Brace-matched rather than sliced to
    # the next `struct`: the review's mutant moved its helper below the last one and passed.
    start = view.index("struct ModelDetail: View")
    depth, end = 0, start
    for index in range(start, len(view)):
        if view[index] == "{":
            depth += 1
        elif view[index] == "}":
            depth -= 1
            if depth == 0:
                end = index + 1
                break
    body = view[start:end]

    assert re.search(
        r"private var facts: \[DetailFact\] \{\s*detailFacts\(\s*model:", body
    ), "the detail screen no longer asks the Engine for its facts"
    facts_property = body[body.index("private var facts"):]
    facts_property = facts_property[: facts_property.index("\n    }")]
    assert "+" not in facts_property and "DetailFact(" not in facts_property, (
        "the screen adds facts of its own to the Engine's list; a line the engine did not compose "
        "is a claim nobody measured (the review's `Verdict: Best value overall` mutant)"
    )

    # Every string this view renders is a served value or a named UIText line. An invented
    # sentence — "Independently verified", or one contradicting the D-105 caveat — fails here.
    rendered = re.findall(r"Text\(([^)]*)\)", body)
    allowed = {
        "subject.model",
        "subject.vendor",
        "fact.label",
        "fact.value",
        "note",
        "UIText.detailCaveat(language",
    }
    for text in rendered:
        assert text.strip() in allowed, (
            f"the detail screen renders `{text.strip()}`, which is neither a fact the Engine "
            "composed nor a named UIText line"
        )
    assert "UIText.detailCaveat(language" in " ".join(rendered), (
        "the screen drops D-105's caveat: a reader comparing two surfaces here gets a wrong answer"
    )


def test_every_screen_string_the_client_calls_exists() -> None:
    """A `UIText.x(...)` the client calls must be a `func x(` in `Language.swift`. M15, W-114.

    **This test exists because eleven of them were deleted and nothing noticed.** The 2026-09-22 UI
    refresh added eleven screen strings; the next wave wrote `Language.swift` from a copy that
    predated them and removed all eleven, while `ContentView.swift` went on calling every one. The
    Python suite stayed green — it greps the CALLER — and `swift test` cannot see it either,
    because `ios/Package.swift` scopes the test target to `Engine` and never compiles the view. The
    only thing in the project that could see it was the Xcode build, which runs on one machine.

    So this is the cross-file half `test_ios_visual_contract.py` cannot do: resolve every call.
    `tests/unit/test_router_hints.py` already does exactly this shape for the router's hint ids.
    """
    view = "\n".join(
        line.split("//", 1)[0]
        for line in (CLIENT / "ContentView.swift").read_text(encoding="utf-8").splitlines()
    )
    language = (CLIENT / "Engine" / "Language.swift").read_text(encoding="utf-8")

    called = set(re.findall(r"\bUIText\.([a-zA-Z]\w*)", view))
    defined = set(re.findall(r"static\s+(?:func|let|var)\s+([a-zA-Z]\w*)", language))
    missing = sorted(called - defined)

    assert called, "the client stopped using the string table entirely"
    assert not missing, (
        f"the screen calls {missing}, which `Language.swift` does not define. The app will not "
        "build, and neither `swift test` (it does not compile the view) nor a grep of the view "
        "alone can see it"
    )


def test_every_place_that_prints_a_search_price_says_what_it_leaves_out() -> None:
    """REQ-PRC-002, D-153 clause 3: wherever the app shows a price for a search surface, it says the
    search call is not in it. The M16-W2 review deleted the card's note and the list's footer and
    every suite stayed green (M18, M19), and found a third place with prices and no note at all.

    Structural, because `swift test` does not compile `ContentView.swift`. The wording itself is
    `priceExclusion` in the Engine, tested in `DetailTests`; this pins that each price-bearing view
    asks for it with the surface's own code.
    """
    view = "\n".join(
        line.split("//", 1)[0]
        for line in (CLIENT / "ContentView.swift").read_text(encoding="utf-8").splitlines()
    )

    def body_of(marker: str) -> str:
        start = view.index(marker)
        depth, seen = 0, False
        for index in range(start, len(view)):
            if view[index] == "{":
                depth, seen = depth + 1, True
            elif view[index] == "}":
                depth -= 1
                if seen and depth == 0:
                    return view[start:index + 1]
        raise AssertionError(f"{marker} has no body")

    places = {
        "the pick card": ("struct PickRow: View", r"priceExclusion\(\s*priceExcludes,"),
        "the full ranking": ("struct RankingList: View", r"priceExclusion\(\s*priceExcludes,"),
        "the home preview": (
            "private func rankingPreview(",
            r"priceExclusion\(\s*category\(for:\s*answer\)\?\.priceExcludes,",
        ),
    }
    for place, (marker, pattern) in places.items():
        assert re.search(pattern, body_of(marker)), (
            f"{place} prints a price and no longer says what a search surface's price leaves out"
        )
    assert len(re.findall(r"priceExclusion\(", view)) == len(places), (
        "a new place words the price exclusion; pin it here, or it can be deleted unnoticed"
    )



def test_every_reason_the_engine_can_give_is_one_the_app_can_word() -> None:
    """M17-W1 re-review MINOR-R2/R3: the engine and the app each held the reason codes as literals,
    and nothing tied them. A code the app does not know falls back to the engine's English on the
    Turkish screen -- MINOR-1's own symptom. Both sets are READ: the engine's from the `"reason":`
    entries `recommend.py` builds its facts with, the app's from `PickReason`'s raw values."""
    engine_source = (pathlib.Path(__file__).resolve().parents[2]
                     / "src/app/workflows/recommend.py").read_text(encoding="utf-8")
    engine = {code for expr in re.findall(r'"reason":\s*([^,}\n]+)', engine_source)
              for code in re.findall(r'"([a-z_]+)"', expr)}
    language = (CLIENT / "Engine/Language.swift").read_text(encoding="utf-8")
    body = language[language.index("enum PickReason"):]
    body = body[:body.index("}")]
    app = set(re.findall(r'case \w+ = "([a-z_]+)"', body))
    assert engine, "no reason code read from recommend.py -- this check compares nothing"
    assert app, "no PickReason case read from Language.swift -- this check compares nothing"
    assert engine == app, {"engine only": engine - app, "app only": app - engine}
