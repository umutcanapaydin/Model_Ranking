"""REQ-RTR-002/-005 — the router's boundary, gated where a gate can actually run.

D-126 ruled this at M8: **the router picks the QUESTION; the engine answers it, and the router may
never say a model is good.** The boundary is enforced in Swift, and no Swift is executed by any
gate in this repository (W-038). So these tests hold the half that IS visible from here — the
relationship between what the engine advertises and what the client can do with it — and say
plainly what they do not cover.

The routing hints live in the client rather than in `/v1`, and that is a consequence rather than a
preference: the payload is frozen (D-115), D-124's single revision window was spent by D-125, and
the owner ruled on 2026-08-22 that this milestone finishes with what exists. A hint is not evidence,
so keeping it out of the contract is defensible — but a hand-maintained list keyed to ids the engine
owns is this project's most-repeated defect shape, and it has bitten here five times. This is the
gate that stops it being silent.
"""

from __future__ import annotations

import pathlib
import re

from fastapi.testclient import TestClient

from app.adapter import main as adapter

ROUTER = pathlib.Path(__file__).resolve().parents[2] / "ios/ModelRanking/Engine/Router.swift"
#: The whole client: the egress ban below is on the INVARIANT, not on a list of paths (W-099).
CLIENT = ROUTER.parent.parent


def _hint_ids() -> set[str]:
    """The category ids the client has a routing hint for, parsed from the Swift."""
    source = ROUTER.read_text(encoding="utf-8")
    block = source[source.index("static let byID:") : source.index("unmeasuredFallback")]
    # `[a-z-]` missed `search_factuality` when M15-W3 added it -- a surface id may carry an
    # underscore (the engine's own ids do), and a hint the pattern cannot see reads here as a hint
    # that does not exist. The test would have failed loudly; a narrower pattern in the OTHER
    # direction would have passed silently, which is the version of this bug worth fearing.
    return set(re.findall(r'^\s*"([a-z_-]+)":', block, re.MULTILINE))


def test_every_surface_the_engine_advertises_has_a_routing_hint() -> None:
    """A surface with no hint is one the router can never choose.

    The engine owns the id list and the client owns the descriptions, so they drift the moment a
    category is added — and the failure is silent in the worst way: the new surface is still
    reachable by tapping a chip, so nothing looks broken, while the front door quietly cannot send
    anyone there.
    """
    from app.workflows.categories import CATEGORIES

    hints = _hint_ids()
    assert hints, "no routing hints could be parsed; the derivation is broken, not clean"

    missing = sorted(set(CATEGORIES) - hints)
    assert not missing, (
        f"the engine ranks {missing} and the router has no description for them, so it can never "
        "route a question there"
    )

    stale = sorted(hints - set(CATEGORIES))
    assert not stale, (
        f"the router describes {stale}, which the engine does not serve; a hint outliving its "
        "surface is how the closed set stops being closed"
    )


def _example_counts() -> dict[str, int]:
    """How many example questions the WORDING tier holds per surface, parsed from the Swift."""
    source = ROUTER.read_text(encoding="utf-8")
    start = source.index("static let examples:")
    block = source[start : source.index("\n    ]\n", start)]
    return {
        match.group(1): len(re.findall(r'"[^"]*"', match.group(2)))
        for match in re.finditer(r'^\s*"([a-z_-]+)":\s*\[(.*?)\]', block, re.MULTILINE | re.DOTALL)
    }


def test_every_described_surface_has_example_questions_for_the_wording_tier() -> None:
    """M15-W3 re-calibration: the wording tier routes on EXAMPLES, the model tier on `byID`.

    A surface with a description and no examples is one the model tier can choose and the wording
    tier -- the one most devices run -- silently cannot. Two examples is the floor because a surface
    scores as the mean of its two closest; the shipped set has six each, as measured.
    """
    counts = _example_counts()
    assert counts, "no example questions could be parsed; the derivation is broken, not clean"

    assert set(counts) == _hint_ids(), (
        f"examples cover {sorted(counts)} and descriptions cover {sorted(_hint_ids())}; the two "
        "tiers of one router would be choosing from different lists"
    )
    thin = sorted(surface for surface, count in counts.items() if count < 2)
    assert not thin, f"{thin} have fewer than two examples, so their score is one stray sentence"


def test_the_unmeasured_fallback_is_a_surface_the_engine_actually_serves() -> None:
    """REQ-RTR-005, and the owner's ruling that an unmeasured question goes to general chat.

    That is only honest because `assistant` is a MEASURED surface — a general-purpose chat model
    genuinely is the tool for a question nothing here measures specifically. Pointing the fallback
    at an id the engine does not serve would turn the front door into a dead end.
    """
    source = ROUTER.read_text(encoding="utf-8")
    match = re.search(r'unmeasuredFallback\s*=\s*"([a-z-]+)"', source)
    assert match, "the router has no fallback for a question the catalogue does not measure"

    served = {c["id"] for c in TestClient(adapter.app).get("/v1/categories").json()["categories"]}
    assert match.group(1) in served, (
        f"the unmeasured fallback is {match.group(1)!r} and the engine does not serve it"
    )


def test_the_router_validates_against_the_ids_the_engine_serves() -> None:
    """REQ-RTR-002's structural half: the closed set is the ENGINE's list, not a second copy.

    Where the platform allows it the set is a generation schema, so a recommendation is not
    expressible; everywhere else the outcome is checked against the same fetched list. Either way
    the ids come from `/v1/categories` at runtime. A router that validated against its own hint
    table would be checking itself.
    """
    source = ROUTER.read_text(encoding="utf-8")
    assert "within known: [String]" in source, "the router no longer takes the engine's id list"
    assert re.search(r"anyOf:\s*known", source), (
        "the on-device model's closed set is no longer built from the ids the engine serves"
    )
    assert re.search(r"known\.contains\(id\)", source), (
        "the model's answer is no longer checked against the engine's list; the schema should make "
        "that unreachable and an unreachable guard on a model's output is worth its two lines"
    )


def test_the_router_never_produces_anything_but_a_category_id() -> None:
    """D-126's absolute boundary, asserted on the TYPE the router can return.

    `RoutingOutcome` carries a category id, a tier and a flag. There is no field a recommendation,
    a model name or a sentence of praise could travel in — which is the only version of this
    guarantee that does not depend on a prompt being obeyed.

    **Every STORED field, `var` as well as `let` (M13 Stage 4.0 MINOR-2).** The first version matched
    `let` only; W3 added `var alternatives`, the set was never updated, and the seat's mutant `var
    praise: String = "the best model is X"` passed. A computed property carries a `{` on its line
    and stores nothing, so it is not a field.
    """
    source = ROUTER.read_text(encoding="utf-8")
    block = source[source.index("struct RoutingOutcome") : source.index("var explanation")]
    fields = set(
        re.findall(r"^\s*(?:public\s+)?(?:let|var)\s+(\w+)\s*:[^{\n]*$", block, re.MULTILINE)
    )
    assert fields == {"categoryID", "tier", "unmeasured", "alternatives"}, (
        f"RoutingOutcome carries {sorted(fields)}; anything beyond a surface id, how it was chosen, "
        "whether it is measured and the other surface ids it came close to is a channel for an "
        "opinion the router may not have"
    )
    assert re.search(r"var alternatives:\s*\[String\]", block), (
        "`alternatives` must stay a list of surface ids; any other type can carry a sentence"
    )


def test_nothing_typed_by_the_reader_reaches_the_engine() -> None:
    """REQ-RTR-004. The engine is asked for a SURFACE, never for a question.

    `/v1` takes `task` and `budget` and nothing else, and the router's only contribution to a
    request is which of nine ids the task is. The scoring path is untouched (D-104) because the
    typed text never enters it.

    **Asserted as data flow, not vocabulary (M13 Stage 4.0 MAJOR-2).** The first version looked for
    the word `question` beside `URLQueryItem`. W3 rewrote this path around `asked` and `typed`, and
    the seat's mutant `client.recommendation(task: asked.isEmpty ? task : asked, budget: budget)`
    compiled, sent the reader's words to the engine on every reload, and passed. So: every argument
    of every engine call is the bare `task` or `budget`, and `task` is only ever assigned the
    router's surface id or the id the reader tapped.
    """
    view = (ROUTER.parent.parent / "ContentView.swift").read_text(encoding="utf-8")
    code = "\n".join(line.split("//", 1)[0] for line in view.splitlines())

    calls = re.findall(r"\bclient\.(\w+)\(([^)]*)\)", code)
    assert calls, "no engine call found in ContentView; this test would pass vacuously"
    for name, arguments in calls:
        for argument in filter(None, (a.strip() for a in arguments.split(","))):
            label, _, value = (part.strip() for part in argument.partition(":"))
            assert label in {"task", "budget"} and value == label, (
                f"`client.{name}` is sent `{argument}`; the engine may only be sent the selected "
                "surface and the budget, never anything derived from what the reader typed"
            )

    assigned = re.findall(r"(?<!\w)(?:self\.)?task\s*=(?!=)\s*([^\n]+)", code)
    declared = [value for value in assigned if value.strip().startswith('"')]
    assert len(declared) == 1 and re.fullmatch(r'"[a-z-]+"', declared[0].strip()), (
        f"`task` must start as one literal surface id, got {declared}"
    )
    for value in assigned:
        if value in declared:
            continue
        assert value.strip() in {"outcome.categoryID", "id"}, (
            f"`task` is assigned `{value.strip()}`; only the router's surface id or the id the "
            "reader tapped may select what the engine is asked"
        )
    assert "outcome.categoryID" in [value.strip() for value in assigned], (
        "the router's choice does not select the surface"
    )
    assert "$task" not in code, "`task` is bound to a control, so a reader can type into it"

    # The other doors into `task` (Stage 4.0 re-verification MINOR-4). Four mutants carried the typed
    # text past the rules above: `select(typed)`, `task += typed`, a second `EngineClient` called
    # directly, and a `RoutingOutcome` built in the view with the typed text as its id.
    for argument in re.findall(r"\bselect\(([^)]*)\)", code):
        if argument.strip().startswith("_ "):
            continue  # the declaration, `func select(_ id: String)`
        assert argument.strip() in {"id", "choice.id"}, (
            f"`select({argument.strip()})`: only a surface id the reader tapped may select what the "
            "engine is asked"
        )
    assert "RoutingOutcome(" not in code, (
        "the view builds its own routing outcome; only the router may choose a surface"
    )
    assert not re.search(
        r"(?<!\w)(?:self\.)?task\s*[-+*/%&|^]=|\btask\.(?:append|insert|remove|replace)", code
    ), "`task` is changed in place; it may only be replaced by a surface id"
    assert code.count("EngineClient(") == 1, (
        "a second engine client in the view would escape the argument check on `client.`"
    )
    assert not re.search(r"question[^\n]*URLQueryItem|URLQueryItem[^\n]*question", code), (
        "the reader's typed question is being put into a request to the engine"
    )

    client = (ROUTER.parent / "EngineClient.swift").read_text(encoding="utf-8")
    assert not re.search(r"\bquestion\b", client), (
        "the engine client mentions the reader's question; it must only ever send task and budget"
    )


def test_the_gap_register_stays_on_the_device() -> None:
    """REQ-GAP-001 (M14-W3): what the reader typed is recorded locally and nowhere else.

    The register is the one place the app keeps the reader's words, so it is the most likely place
    for them to leak. Held structurally: it is saved only through `GapRegisterStore`, whose file is
    excluded from iCloud backup; the register code opens no network connection; and no engine call
    is ever handed the register (the data-flow test above already pins every `client.` argument).
    """
    front = (ROUTER.parent / "FrontDoor.swift").read_text(encoding="utf-8")
    view = (ROUTER.parent.parent / "ContentView.swift").read_text(encoding="utf-8")
    register = front[front.index("// MARK: - The gap register") :]
    code = "\n".join(line.split("//", 1)[0] for line in register.splitlines())

    assert "isExcludedFromBackup = true" in code, "the register would be uploaded with the backup"
    # Review S-1: on the phone the register is unreadable while the device is locked.
    assert re.search(r"writeOptions:\s*\[\.atomic,\s*\.completeFileProtection\]", code), (
        "the on-device register is written without file protection"
    )
    for network in ("URLSession", "URLRequest", "EngineClient", "http"):
        assert network not in code, f"the gap register reaches for `{network}`"
    view_code = "\n".join(line.split("//", 1)[0] for line in view.splitlines())
    # Review m-1: through the tested predicate, so a router failure (manual tier) is not a gap.
    assert re.search(r"if recordsGap\(outcome\) \{\s*gaps\.record\(typed\)", view_code), (
        "the register is not fed by the routed unmeasured outcome, or is fed something else"
    )
    assert not re.search(r"client\.\w+\([^)]*gaps", view_code), (
        "an engine call is handed the register"
    )

    # M14 closure seat, BLOCKING-1. The three asserts above search the REGISTER's own section of
    # `FrontDoor.swift`. The reader's words are recorded from `ContentView.ask`, so a mutant that
    # POSTs `typed` to a remote host from the view -- four lines, immediately after `gaps.record` --
    # survived every gate in this repository, `swift test` included (the Engine target does not
    # compile `ContentView.swift`, which is why these source-contract tests exist at all).
    #
    # So the ban is on the WHOLE view, not on one section of one file: the view has exactly one way
    # to reach the network, `EngineClient`, and `test_the_client_sends_only_the_surface_and_budget`
    # above pins every argument that may go through it. A view that opens its own connection is the
    # D-126 defect whatever it sends -- `URLSession`, `URLRequest`, a socket or a raw URL string.
    # M15-W2 review, BLOCKING-1. The ban used to name two files, so it did not reach
    # `Detail.swift` — a new Engine file in the reader's path, written the day after W-099 closed.
    # The seat's mutant (a `URLSession` POST inside `detailFacts`) survived every gate, which is
    # W-099's own finding recurring in the next wave: **a ban on two paths is not a ban on the
    # invariant.** It now covers EVERY client file, with the one sanctioned door named here, the
    # shape `SCORE_ARITHMETIC_PERMITTED` uses for D-138.
    #
    # `EngineClient.swift` is the exemption: it IS the network layer, and what it may send is
    # pinned argument by argument in `ios/EngineTests/EngineClientTests.swift`
    # (`testTheSurfaceAndTheBudgetAreBothSentAndNothingElseIs`, `testNothingTheReaderTypedIsEverSent`).
    #
    # M15 closure security seat, MAJOR-1: the six-word list above let 10 of 12 privacy mutants
    # through -- `URL.init(string:)`, `URLComponents` + `UIApplication.open`, a web view, the
    # pasteboard, iCloud key-value storage, `UserDefaults`, `NSLog`, `Data(contentsOf:)` on a remote
    # URL -- and cut every line at its first `//`, so a URL literal hid a call after it. Since this
    # milestone the SCREEN promises "This app never sends what you type anywhere", so the gate is now four
    # layers: an import ALLOWLIST, a comment stripper that respects string literals, a ban on every
    # API that can carry text off the device or into shared storage, and no non-Swift sources.
    _assert_the_client_has_no_way_off_the_device()


#: Frameworks the client may import. `Network`, `WebKit`, `CloudKit`, `UIKit`, `os`, `SafariServices`
#: and the rest are refused by their absence here: a new one is a reviewed edit to this set.
CLIENT_IMPORTS = {"Foundation", "SwiftUI", "NaturalLanguage", "FoundationModels"}

# M15-W4 review, MAJOR-1 (the sixth recurrence of this shape). The gate used to strip comments
# first, and a hand-written stripper that does not model string interpolation, raw strings or
# regex literals could be made to eat the real code after them -- three bypasses, each a literal
# `URLSession` upload `swift test` compiled. **So nothing is stripped any more.** The gate reads
# the RAW text of every client file, comments and strings included. The cost is that a comment
# may not name a banned API either; the gain is that there is no parser to fool.

#: Every spelling that reaches the network, opens a URL or a share sheet, builds a URL, or writes
#: text anywhere other than the gap register's own backup-excluded file. Matched on raw source.
EGRESS = (
    # the network, under any class name (a leading `\b` would miss `NSMutableURLRequest`)
    r"URLSession", r"URLRequest", r"\bURLComponents\b", r"QueryItem", r"\bNSURL\b", r"\bCFURL",
    r"\bNW[A-Z]\w*", r"\bCFStream", r"\bNetwork\.", r"\bNetService", r"\bsocket\s*\(", r"\bsockaddr",
    # building a URL, any spelling; and a URL-typed value, which a decoder can fill from anywhere
    r"\bURL\s*\(", r"\bURL\s*\.", r":\s*\[?\s*URL\b", r"(?<!self)(?<!super)\.init\s*\(",
    r"\binit\s*\(\s*string\s*:", r"(?i)\b(?:https?|ftp|wss?)://", r"(?i)\bmailto:",
    r"\bresourceBytes\b", r"\.lines\b",
    # opening, sharing, handing off -- every system surface that carries text somewhere else
    r"\bopenURL\b", r"\.open\s*\(", r"\bUIApplication\b", r"\bUIScene\b",
    r"(?<!Navigation)Link\s*\(", r"\bShareLink\b", r"\bUIActivity", r"\bAsyncImage\b",
    r"WebView\b", r"\bSFSafari", r"\bmarkdown\s*:", r"\bAttributedString\s*\(\s*markdown",
    r"\buserActivity\b", r"\bNSUserActivity\b", r"\bfileExporter\b", r"\bfileMover\b",
    r"\bdraggable\b", r"\bonDrag\b", r"\bUIPrint", r"\bUIDocument", r"Pasteboard\b",
    # storage outside the register, and anything that syncs
    r"Ubiquit", r"\bCKContainer\b", r"\bCloudKit\b", r"\bUserDefaults\b", r"\bSceneStorage\b",
    r"\bCFPreferences", r"\bSecItem", r"\bNSKeyedArchiver\b", r"\bcontentsOf\s*:", r"\btoFile\s*:",
    r"\bwrite\s*\(", r"\bFileManager\b", r"\bFileHandle\b", r"\bOutputStream\b", r"\bcreateFile\b",
    r"\bfopen\s*\(", r"\bfwrite\s*\(",
    # logs and crash reports
    r"\bNSLog\b", r"\bos_log\b", r"\bLogger\b", r"\bprint\s*\(", r"\bdebugPrint\s*\(",
    r"\bdump\s*\(", r"\bf?puts\s*\(", r"\bstderr\b",
    r"\b(?:fatalError|preconditionFailure|precondition|assertionFailure|assert)\s*\([^\n]*\\\(",
    # indirection a text gate cannot follow, refused outright
    r"\btypealias\b", r"\bNSClassFromString\b", r"\bNSSelectorFromString\b", r"\bdlopen\b",
    r"\bdlsym\b", r"@_silgen_name", r"\bperform\s*\(\s*(?:#selector|Selector)",
)

#: The door, permitted by pattern for the whole file: `EngineClient.swift` IS the network layer,
#: and what it may send is pinned argument by argument in `ios/EngineTests/EngineClientTests.swift`
#: (`testTheSurfaceAndTheBudgetAreBothSentAndNothingElseIs`, `testNothingTheReaderTypedIsEverSent`).
EGRESS_PERMITTED = {
    ("EngineClient.swift", r"\bURL\s*\("): "D-126: the engine's base URL",
    ("EngineClient.swift", r":\s*\[?\s*URL\b"): "D-126: the engine's base URL, typed",
    ("EngineClient.swift", r"(?i)\b(?:https?|ftp|wss?)://"): "D-126: the engine's address",
    ("EngineClient.swift", r"\bURLComponents\b"): "D-126: the request; its arguments are pinned",
    ("EngineClient.swift", r"QueryItem"): "D-126: the request's two pinned arguments",
    ("EngineClient.swift", r"URLSession"): "D-126: the one sanctioned door",
    ("EngineClient.swift", r"URLRequest"): "D-126: the one sanctioned door",
}

#: Everything else is permitted as an EXACT expression, each occurring exactly once, removed before
#: the scan -- never a pattern over a whole file. The W4 seat sent the register itself off the
#: device with a second `Data(contentsOf:)` inside `save()`, which a file-wide permission let through.
EGRESS_EXACT = {
    ("FrontDoor.swift", "FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)"): "REQ-GAP-001: where the register lives",
    ("FrontDoor.swift", "FileManager.default.temporaryDirectory"): "REQ-GAP-001: the fallback folder",
    ("FrontDoor.swift", "FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)"): "REQ-GAP-001: the register's folder",
    ("FrontDoor.swift", "Data(contentsOf: url)"): "REQ-GAP-001: the register reads its own file",
    ("FrontDoor.swift", "data.write(to: url, options: writeOptions)"): "REQ-GAP-001: the register writes its own file",
    ("FrontDoor.swift", "public let url: URL"): "REQ-GAP-001: the register's own file",
    ("FrontDoor.swift", "public init(url: URL,"): "REQ-GAP-001: the register's own file",
    # M17-W4, D-167 clause 4: the standings the engine sent, kept for a day in the caches folder.
    ("StandingsStore.swift", "FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask)"): "D-167: where the standings live",
    ("StandingsStore.swift", "FileManager.default.temporaryDirectory"): "D-167: the fallback folder",
    ("StandingsStore.swift", "try? FileManager.default.createDirectory(\n            at: url.deletingLastPathComponent(), withIntermediateDirectories: true\n        )"): "D-167: the standings' folder",
    ("StandingsStore.swift", "Data(contentsOf: url)"): "D-167: the store reads its own file",
    ("StandingsStore.swift", "data.write(to: url, options: .atomic)"): "D-167: the store writes its own file",
    ("StandingsStore.swift", "public let url: URL"): "D-167: the store's own file",
    ("StandingsStore.swift", "public init(url: URL)"): "D-167: the store's own file",
}

#: The one piece of app storage the client keeps: the language choice, typed as `Language`, so it
#: cannot hold a string the reader typed. A second `@AppStorage`, whatever its key, is refused.
APP_STORAGE = r'@AppStorage\("language"\)\s*private\s+var\s+language\s*:\s*Language\s*='

IMPORT = re.compile(
    r"\bimport\b(?:\s|/\*[\s\S]*?\*/|//[^\n]*\n)*"
    r"(?:(?:struct|class|enum|protocol|typealias|func|var|let)\b(?:\s|/\*[\s\S]*?\*/)*)?"
    r"([A-Za-z_]\w*)"
)


def _assert_the_client_has_no_way_off_the_device() -> None:
    used: set[tuple[str, str]] = set()
    storage = 0
    for path in sorted(p for p in CLIENT.rglob("*") if p.is_file()):
        if ".xcassets" in path.parts or path.name == ".DS_Store":
            continue
        assert path.suffix in {".swift", ".plist", ".json", ".strings"}, (
            f"{path.relative_to(CLIENT)} is a source this gate cannot read; the Xcode target "
            "compiles every file in the folder, so a non-Swift file is an unguarded door"
        )
        if path.suffix != ".swift":
            continue
        code = path.read_text(encoding="utf-8")
        # Every `import`, anywhere -- not only at the start of a line, and through comments.
        for module in IMPORT.findall(code.replace("`", "")):
            assert module in CLIENT_IMPORTS, (
                f"{path.name} imports `{module}`, which is not on the client's allowlist; the "
                "reader's words reach every client file, so a new framework is a reviewed edit"
            )
        for (name, snippet), _reason in EGRESS_EXACT.items():
            if name != path.name:
                continue
            assert code.count(snippet) == 1, (
                f"{name} must contain `{snippet}` exactly once; it is permitted as that expression"
            )
            code = code.replace(snippet, " ")
            used.add((name, snippet))
        storage += len(re.findall(r"\bAppStorage\s*\(", code.replace("`", "")))
        code = re.sub(APP_STORAGE, " ", code)
        # the backup exclusion is only ever `= true` and the statement ends there
        assert len(re.findall(r"isExcludedFromBackup", code)) == len(
            re.findall(r"\bisExcludedFromBackup = true[ \t]*(?:\n|;)", code)
        ), f"{path.name} sets isExcludedFromBackup to something other than a plain true"
        # M15-W4 re-review MAJOR-1: backticks (`` `URL`( ``) and inline comments (`URL/**/(`) split
        # a banned spelling without changing what compiles. Every pattern is matched against the
        # raw text AND against a view with both removed. Removing is only ever an EXTRA view, never
        # the only one, so nothing a stripper eats can hide from the raw scan.
        joined = re.sub(r"/\*[\s\S]*?\*/", "", code.replace("`", ""))
        for pattern in (*EGRESS, r"\bAppStorage\s*\("):
            if not (re.search(pattern, code) or re.search(pattern, joined)):
                continue
            if (path.name, pattern) in EGRESS_PERMITTED:
                used.add((path.name, pattern))
                continue
            raise AssertionError(
                f"{path.name} matches `{pattern}`: a way for text to leave the device or reach "
                "shared storage; the only sanctioned egress is EngineClient with its arguments pinned"
            )
    assert storage == 1, f"{storage} `@AppStorage` declarations; the client keeps exactly one"
    stale = (set(EGRESS_PERMITTED) | set(EGRESS_EXACT)) - used
    assert not stale, (
        f"{sorted(stale)} is permitted and no longer used; an exemption that outlives its use "
        "silently widens the next time the same call is added"
    )
    # The Xcode target compiles the synchronized `ModelRanking` folder. A source file referenced
    # from anywhere else would be compiled and never read by this gate (W4 review, N10's note).
    project = (CLIENT.parent / "ModelRanking.xcodeproj" / "project.pbxproj").read_text(encoding="utf-8")
    assert "sourcecode." not in project, "the project references a source file outside the folder"
    assert re.findall(r"isa = PBXFileSystemSynchronizedRootGroup;\s*path = (\w+);", project) == [
        "ModelRanking"
    ], "the target compiles a folder this gate does not read"
