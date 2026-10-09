"""#51, #58 -- the compiler-level half of D-126 (`scripts/client_decl_gate.py`, `make client-decls`)
refuses what it is for, and that is held by tests rather than by hand-run review probes.

- The rules, on what the compiler printed: these run everywhere, including CI, which has no Xcode.
- The whole gate on a compiled fixture (`scripts/client_decl_fixtures/`): runs where Xcode is, and
  `make client-decls` runs the same fixture before it checks the app, so the gate cannot pass the
  app while it has stopped refusing.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("client_decl_gate", ROOT / "scripts" / "client_decl_gate.py")
assert _spec is not None and _spec.loader is not None
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)

#: What `swiftc -dump-ast` printed for `JSONDecoder().decode([URL].self, from:)` (Xcode 26, measured).
DECODED_URL = (
    '(source_file "/x/ContentView.swift"\n'
    '  (declref_expr type="(JSONDecoder) -> ([URL].Type, Data) throws -> [URL]" '
    'decl="Foundation.(file).JSONDecoder.decode(_:from:) [with (substitution_map '
    'generic_signature=<T where T : Decodable> T -> [URL])]" function_ref=single apply)\n'
)


def test_the_network_and_the_file_system_are_refused_outside_their_files() -> None:
    """#51: `URLSession` outside `EngineClient.swift`, `FileManager` outside `FILESYSTEM_FILES`."""
    found = {
        "ContentView.swift": {"Foundation.URLSession"},
        "Detail.swift": {"Foundation.FileManager"},
        "EngineClient.swift": {"Foundation.URLSession"},
        "StandingsStore.swift": {"Foundation.FileManager"},
    }
    refused = gate.problems(found)
    assert len(refused) == 2, refused
    assert any(line.startswith("ContentView.swift:") and "network" in line for line in refused)
    assert any(line.startswith("Detail.swift:") and "file system" in line for line in refused)


def test_a_url_decoded_outside_the_engine_client_is_the_network() -> None:
    """#58: a URL made by decoding was neither a spelling nor an initialiser, so both gates missed it."""
    found = gate.references(DECODED_URL)
    assert "Foundation.URL.decoded" in found["ContentView.swift"], found
    refused = gate.problems(found)
    assert any("ContentView.swift" in line and "network" in line for line in refused), refused
    assert gate.problems({"EngineClient.swift": found["ContentView.swift"]}) == []


@pytest.mark.needs("xcode")  # the fixture is compiled
def test_the_gate_refuses_its_compiled_fixture() -> None:
    """#51: the whole gate, compiled, on files that must be refused and files that must be allowed."""
    assert gate.self_test() == []


#: What `swiftc -dump-ast` prints for a synthesised `Decodable` with an `Optional<URL>` property.
DECODED_OPTIONAL_URL = (
    '(source_file "/x/ContentView.swift"\n'
    '  (declref_expr decl="Swift.(file).KeyedDecodingContainer.decodeIfPresent(_:forKey:) [with '
    '(substitution_map generic_signature=<T where T : Decodable> T -> URL)]" function_ref=single apply)\n'
)


def test_a_url_decoded_if_present_is_the_network_too() -> None:
    """W5 review B1 (#58): `decodeIfPresent`, which Swift generates for every optional property, was
    not matched; `struct B: Decodable { let u: URL? }` passed the gate in all four configurations."""
    assert "Foundation.URL.decoded" in gate.references(DECODED_OPTIONAL_URL)["ContentView.swift"]


def test_make_client_decls_fails_when_its_self_test_does(monkeypatch: pytest.MonkeyPatch) -> None:
    """W5 Tester: `main()` runs the self-test before it checks the app, so the gate cannot pass the app
    while it has stopped refusing (#51). Nothing held that: with the call unwired, every test here and
    `make client-decls` passed. A failed self-test returns before anything compiles, so this runs
    where there is no Xcode too."""
    monkeypatch.setattr(gate, "self_test", lambda: ["ContentView.swift: URL.decoded was not refused"])
    assert gate.main() == 1


def test_a_release_build_carries_no_ui_test_hook() -> None:
    """D-175 clause 3: the launch arguments the scripted router is handed are read in Debug only."""
    found = {"LaunchRouting.swift": {"Foundation.ProcessInfo.arguments", "Swift.CommandLine.arguments"}}
    assert len(gate.release_problems(found)) == 2
    # Review M5: the launch environment is as easy to set from a UI test as the arguments.
    assert len(gate.release_problems({"LaunchRouting.swift": {"Foundation.ProcessInfo.environment"}})) == 1
    inert = {"LaunchRouting.swift": {"Foundation.ProcessInfo.processInfo", "main.ScriptedModelRouter"}}
    assert gate.release_problems(inert) == []


def test_main_refuses_a_release_dump_that_carries_a_ui_test_hook(monkeypatch: pytest.MonkeyPatch) -> None:
    """W2 Tester (D-175 clause 3, review M5): the test above holds `release_problems`; nothing held
    that `main()` calls it, or calls it on the Release configurations. With the call removed, every
    test and `make client-decls` passed. Canned dumps stand in for the compiler, so this runs on CI."""
    names = {path.name for path in gate.CLIENT.rglob("*.swift")}

    def dumps(hooked: str, decl: str) -> None:
        monkeypatch.setattr(gate, "dump_ast", lambda sdk_name, flags, folder=gate.CLIENT: (
            "debug" if "DEBUG" in flags else "release", 0))
        monkeypatch.setattr(gate, "references", lambda ast: {
            name: ({decl} if name == "LaunchRouting.swift" and ast == hooked else set()) for name in names})

    monkeypatch.setattr(gate, "self_test", lambda: [])
    monkeypatch.setattr(gate, "problems", lambda found: [])
    monkeypatch.setattr(gate, "unseen_permissions", lambda found: [])
    dumps("release", "Foundation.ProcessInfo.environment")
    assert gate.main() == 1, "a Release build that reads its launch environment passed"
    dumps("debug", "Foundation.ProcessInfo.arguments")
    assert gate.main() == 0, "the Debug-only hook was refused in a Debug build"


#: #85 (D-180): what `swiftc -dump-ast` prints for the M17 relays and P3, trimmed from the compiled
#: fixture (`scripts/client_decl_fixtures/`, Xcode 26). A sink file's static `var`, a global `var` the
#: screen sets and the sink reads, and standings built from typed text; beside them, what the gate
#: must allow: a `let`, a computed property, a function's local, a non-sink reading the global, and
#: the standings initialiser's own parameter.
SINK_AST = (
    '(source_file "/x/EngineClient.swift"\n'
    '  (struct_decl range=[/x/EngineClient.swift:1:1 - line:9:1] "Relay" interface_type="Relay.Type" access=internal\n'
    '    (var_decl decl_context=0x1 range=[/x/EngineClient.swift:2:36 - line:2:36] "tag" interface_type="String" '
    'access=internal static readImpl=stored writeImpl=stored readWriteImpl=stored nonisolated(unsafe)\n'
    '    (var_decl decl_context=0x1 range=[/x/EngineClient.swift:3:16 - line:3:16] "limit" interface_type="Int" '
    'access=internal let static readImpl=stored immutable\n'
    '    (var_decl decl_context=0x1 range=[/x/EngineClient.swift:4:16 - line:4:16] "computed" interface_type="Int" '
    'access=internal static readImpl=getter immutable\n'
    '    (func_decl range=[/x/EngineClient.swift:5:5 - line:8:5] "build()" interface_type="(Relay) -> () -> String" access=internal\n'
    '      (brace_stmt range=[/x/EngineClient.swift:5:20 - line:8:5]\n'
    '        (var_decl decl_context=0x2 range=[/x/EngineClient.swift:6:13 - line:6:13] "parts" interface_type="[String]" '
    'access=private readImpl=stored writeImpl=stored readWriteImpl=stored\n'
    '        (member_ref_expr type="@lvalue String" location=/x/EngineClient.swift:7:20 '
    'decl="main.(file).Relay.tag@/x/EngineClient.swift:2:36")\n'
    '        (declref_expr type="@lvalue String" location=/x/EngineClient.swift:7:30 '
    'decl="main.(file).screenRelay@/x/ContentView.swift:3:25" function_ref=unapplied)))))\n'
    '(source_file "/x/ContentView.swift"\n'
    '  (var_decl decl_context=0x3 range=[/x/ContentView.swift:3:25 - line:3:25] "screenRelay" interface_type="String" '
    'access=internal readImpl=stored writeImpl=stored readWriteImpl=stored nonisolated(unsafe)\n'
    '  (func_decl range=[/x/ContentView.swift:5:1 - line:7:1] "keep(_:)" interface_type="(String) -> FetchedStandings?" access=internal\n'
    '    (brace_stmt range=[/x/ContentView.swift:5:40 - line:7:1]\n'
    '      (declref_expr implicit type="(FetchedStandings.Type) -> (Data) throws -> FetchedStandings" '
    'location=/x/ContentView.swift:6:10 decl="main.(file).FetchedStandings.init(payload:)@/x/Models.swift:9:5" '
    'function_ref=single apply))))\n'
    '(source_file "/x/Detail.swift"\n'
    '  (declref_expr type="String" location=/x/Detail.swift:2:5 decl="main.(file).screenRelay@/x/ContentView.swift:3:25" '
    'function_ref=unapplied)\n'
    '(source_file "/x/Models.swift"\n'
    '  (declref_expr type="Data" location=/x/Models.swift:9:15 '
    'decl="main.(file).FetchedStandings.init(payload:).data@/x/Models.swift:9:15" function_ref=unapplied)\n'
)


def test_a_sink_holding_or_reading_shared_mutable_state_is_refused() -> None:
    """#85 (D-180 clause 2): the M17 relay P2 kept a refinement in a `static var` on `EngineClient`, and
    a variant kept it in a global `var` the screen sets; both passed every gate, which scoped by file.
    A sink file's mutable stored state, and its reads of any other file's, are refused. REQ-GAP-001."""
    refused = gate.problems(gate.references(SINK_AST))
    assert any(line.startswith("EngineClient.swift:") and "`tag`" in line and "mutable stored state" in line
               for line in refused), refused
    assert any(line.startswith("EngineClient.swift:") and "`screenRelay`" in line
               and "mutable state declared in ContentView.swift" in line for line in refused), refused


def test_standings_built_outside_the_two_sinks_are_refused() -> None:
    """#85 (D-180 clause 2): P3 made the typed question into `FetchedStandings` on the screen and saved
    it into the device's caches. Only the engine's answer and the store's own file build standings. REQ-GAP-001."""
    refused = gate.problems(gate.references(SINK_AST))
    assert any(line.startswith("ContentView.swift:") and "builds FetchedStandings" in line for line in refused), refused


def test_what_the_sinks_may_hold_and_others_may_read_passes() -> None:
    """#85 (D-180): a `let`, a computed property and a function's local are not shared state; a file
    that is not a sink may read a global; the standings initialiser's own parameter is not a call. REQ-GAP-001."""
    refused = gate.problems(gate.references(SINK_AST))
    allowed = ("`limit`", "`computed`", "`parts`")
    assert not [line for line in refused if any(name in line for name in allowed)], refused
    assert not [line for line in refused if line.startswith(("Detail.swift:", "Models.swift:"))], refused


#: #60 (G-2): what `swiftc -dump-ast` printed for the whole compiled fixture (Xcode 26), paths made
#: `/x/`: `Combine.swift`'s permitted position arithmetic and its two sorts of a list named `common`,
#: `ContentView.swift` adding to a served position through another name, and since the W2 review's B1
#: every shape that review got past the gate.
FLOW_AST = (ROOT / "tests" / "unit" / "data" / "g2_fixture_ast.txt").read_text(encoding="utf-8")


def _without(ast: str, function: str) -> str:
    """`ast` with one top-level function's subtree removed."""
    out, skipping = [], False
    for line in ast.splitlines():
        if line.startswith("  (func_decl"):
            skipping = f'"{function}"' in line
        elif line.startswith("(source_file"):
            skipping = False
        if not skipping:
            out.append(line)
    return "\n".join(out) + "\n"


def test_arithmetic_on_a_served_position_through_another_name_is_refused() -> None:
    """#60 (the M17-W4 review's R4): `let place = standing.position; place + 1` passed the text
    tripwire, which matches the words around the operator. The compiler follows the value. REQ-APP-005."""
    refused = gate.problems(gate.references(FLOW_AST))
    assert any(line.startswith("ContentView.swift:") and "served position" in line for line in refused), refused
    # M19-W2 Tester: the fixture's other shapes refuse a served position in this file too, so the line
    # above held nothing of R4's own; with the binding rule off it stayed green. The refusal must be on
    # R4's own lines. # covers REQ-APP-005, D-181 clause 2 (a binding)
    span = _lines_of("ContentView.swift", "func fixtureViewRanksByHand")
    own = [line for line in refused if line.startswith("ContentView.swift:") and "served position" in line
           and int(line.split(":")[1]) in span]
    assert own, ("R4's own `let place = standing.position; place + 1` is not refused", refused)


def test_a_second_sort_under_a_permitted_name_is_refused() -> None:
    """#60 (the M17-W4 Tester's M7): a second `common.sorted()` in `Combine.swift` passed, because the
    permission was keyed by the receiver's name. Each permitted sort is counted. REQ-APP-002."""
    refused = gate.problems(gate.references(FLOW_AST))
    assert any(line.startswith("Combine.swift:") and "sorts `common`" in line for line in refused), refused
    once = gate.problems(gate.references(_without(FLOW_AST, "fixtureCombinesTwice(_:)")))
    assert not [line for line in once if "sorts `common`" in line], once


def test_permitted_arithmetic_passes_where_its_ruling_names_the_file() -> None:
    """#60: D-167 lets `Combine.swift` rank positions; the gate refuses nothing there for it. REQ-APP-005."""
    refused = gate.problems(gate.references(FLOW_AST))
    assert not [line for line in refused if line.startswith("Combine.swift:") and "served position" in line], refused


#: #107: what `swiftc -dump-ast` prints for a URL made by a call whose name is no initialiser: a
#: generic decode wrapper declared in another file and called with `URL`. Beside it, what must pass:
#: the screen reading the engine's address, and the one door making its URL.
MADE_URL_AST = (
    '(source_file "/x/ContentView.swift"\n'
    '  (call_expr type="URL?" location=/x/ContentView.swift:3:5 nothrow isolation_crossing="none"\n'
    '    (declref_expr type="(URL.Type, Data) -> URL?" location=/x/ContentView.swift:3:5 '
    'decl="main.(file).fixtureDecode(_:from:)@/x/Detail.swift:3:6 [with (substitution_map '
    'generic_signature=<T where T : Decodable> T -> URL)]" function_ref=single apply))\n'
    '  (member_ref_expr type="URL" location=/x/ContentView.swift:5:20 '
    'decl="main.(file).EngineClient.baseURL@/x/EngineClient.swift:2:9")\n'
    '(source_file "/x/EngineClient.swift"\n'
    '  (call_expr type="URL?" location=/x/EngineClient.swift:4:10 nothrow isolation_crossing="none"\n'
    '    (declref_expr type="(String) -> URL?" location=/x/EngineClient.swift:4:10 '
    'decl="Foundation.(file).URL.init(string:)" function_ref=single apply))\n'
)


def test_a_url_made_by_any_call_outside_its_files_is_refused() -> None:
    """#107: `URL(_:strategy:)` and a generic decode wrapper make a URL from text with no initialiser
    or decode the gate listed. A call whose result is a URL is refused outside the network door and
    the two stores, whatever it is called; reading a URL that exists is not making one. REQ-GAP-001."""
    refused = gate.problems(gate.references(MADE_URL_AST))
    assert any(line.startswith("ContentView.swift:") and "makes a URL" in line for line in refused), refused
    assert not [line for line in refused if line.startswith("EngineClient.swift:")], refused
    assert len([line for line in refused if "makes a URL" in line]) == 1, refused


def test_a_link_detector_is_the_network() -> None:
    """#107: `NSDataDetector` with the `.link` type finds URLs in text, so it is the network's first
    step, as a URL made from a string is. REQ-GAP-001."""
    refused = gate.problems({"ContentView.swift": {"Foundation.NSDataDetector"}})
    assert any("NSDataDetector" in line and "network" in line for line in refused), refused


def test_turning_cookies_off_is_the_one_cookie_symbol_allowed_and_only_in_the_door() -> None:
    """#144: the session sets `HTTPCookie.AcceptPolicy.never`, a member of a family the gate refuses
    (cookies go to a store the system writes). That one value is allowed in the network door only. REQ-GAP-001."""
    assert gate.problems({"EngineClient.swift": {"Foundation.HTTPCookie.AcceptPolicy.never"}}) == []
    assert gate.problems({"ContentView.swift": {"Foundation.HTTPCookie.AcceptPolicy.never"}})
    assert gate.problems({"EngineClient.swift": {"Foundation.HTTPCookieStorage.shared"}})


#: The W2 review's B2: what `swiftc -dump-ast` prints for its two routes onto the boards request. A
#: client built on an address of a file's own (U5, U3b), an address made from text by the engine
#: client's helper (U3b), and a URL inside a dictionary (U5). Beside them, what must pass: the app's
#: `EngineClient()` and the engine client building itself.
CLIENT_AST = (
    '(source_file "/x/Detail.swift"\n'
    '  (call_expr type="[String : URL]?" location=/x/Detail.swift:9:21 nothrow isolation_crossing="none"\n'
    '    (declref_expr type="(URL, Data) -> [String : URL]?" location=/x/Detail.swift:9:21 '
    'decl="main.(file).fixtureReadLike(_:from:)@/x/Detail.swift:3:6 [with (substitution_map '
    'generic_signature=<T where T : Decodable> T -> URL)]" function_ref=single apply))\n'
    '  (declref_expr type="(EngineClient.Type) -> (URL, URLSession?) -> EngineClient" location=/x/Detail.swift:10:12 '
    'decl="main.(file).EngineClient.init(baseURL:session:)@/x/EngineClient.swift:30:5" function_ref=single apply)\n'
    '(source_file "/x/StandingsStore.swift"\n'
    '  (declref_expr type="(String) -> URL" location=/x/StandingsStore.swift:20:40 '
    'decl="main.(file).EngineClient.engineURL(from:)@/x/EngineClient.swift:36:17" function_ref=single apply)\n'
    '(source_file "/x/ContentView.swift"\n'
    '  (declref_expr type="(EngineClient.Type) -> () -> EngineClient" location=/x/ContentView.swift:85:30 '
    'decl="main.(file).EngineClient.init()@/x/EngineClient.swift:26:5" function_ref=single apply)\n'
    '(source_file "/x/EngineClient.swift"\n'
    '  (declref_expr type="(EngineClient.Type) -> (URL, URLSession?) -> EngineClient" location=/x/EngineClient.swift:27:9 '
    'decl="main.(file).EngineClient.init(baseURL:session:)@/x/EngineClient.swift:30:5" function_ref=single apply)\n'
)


def test_only_the_engine_client_builds_a_client_on_an_address_of_its_own() -> None:
    """The W2 review's B2 (D-180, INV-66, REQ-GAP-001): the typed question reached the boards request
    with every gate green, through a client another file built on its own address (U5 from
    `Detail.swift`, U3b from `FrontDoor.swift`). Only `EngineClient.swift` builds a client with an
    address, or makes one from text; the app builds `EngineClient()`."""
    refused = gate.problems(gate.references(CLIENT_AST))
    assert any(line.startswith("Detail.swift:") and "EngineClient.init(baseURL:session:)" in line
               for line in refused), refused
    assert any(line.startswith("StandingsStore.swift:") and "EngineClient.engineURL(from:)" in line
               for line in refused), refused
    assert not [line for line in refused if line.startswith(("ContentView.swift:", "EngineClient.swift:"))], refused


def test_a_url_inside_another_type_is_made_all_the_same() -> None:
    """The W2 review's B2 (INV-63): a generic decode returning `[String: URL]` made a URL the rule,
    which matched `URL`, `URL?` and `[URL]` only, never saw. REQ-GAP-001."""
    refused = gate.problems(gate.references(CLIENT_AST))
    assert any(line.startswith("Detail.swift:") and "makes a URL" in line for line in refused), refused


def _constructed(type_: str) -> str:
    return ('(source_file "/x/ContentView.swift"\n'
            f'  (constructor_ref_call_expr type="{type_}" location=/x/ContentView.swift:3:5 '
            'range=[/x/ContentView.swift:3:5 - line:3:5] nothrow isolation_crossing="none"\n')


def test_a_call_that_takes_a_url_is_not_one_that_makes_one() -> None:
    """Found replaying the review's K1 on the B2 fix: `XMLParser(contentsOf:)` was refused as making
    a URL, because the rule read the constructor's whole type, `(URL) -> XMLParser?`. What a call
    makes is what it returns, after its last arrow. REQ-GAP-001."""
    assert gate.url_facts(_constructed("(URL) -> XMLParser?")) == {}
    assert gate.url_facts(_constructed("(__shared String) -> URL?")) == {"ContentView.swift": {"Foundation.URL.made"}}
    assert gate.url_facts(_constructed("(Data) -> [String : URL]?")) == {"ContentView.swift": {"Foundation.URL.made"}}


FIXTURES = ROOT / "scripts" / "client_decl_fixtures"


def _lines_of(file: str, declaration: str) -> range:
    """The lines a fixture declaration spans: from its line to the next `}` in column one."""
    lines = (FIXTURES / file).read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines, start=1) if declaration in line)
    end = next(i for i, line in enumerate(lines, start=1) if i > start and line.startswith("}"))
    return range(start, end + 1)


@pytest.mark.parametrize(("file", "declaration"), [
    ("ContentView.swift", "func fixtureA1Reassigned"),       # a reassigned local
    ("ContentView.swift", "func fixtureA2Returned"),         # a function's return value
    ("ContentView.swift", "var fixtureA3Next"),              # a computed property on a decoded type
    ("ContentView.swift", "func fixtureA5Wrapping"),         # `&+`
    ("ContentView.swift", "func fixtureA6Advanced"),         # `.advanced(by:)`
    ("ContentView.swift", "func fixtureA7Converted"),        # `Int32(...)`, then `+`
    ("ContentView.swift", "func fixtureA8Unlisted"),         # a decoded field no table listed
    ("ContentView.swift", "func fixtureA10Literal"),         # a loop over a literal
    ("ContentView.swift", "func fixtureA11Tuple"),           # a loop's tuple pattern
    ("ContentView.swift", "struct FixtureRanker"),           # a method's parameter
    ("ContentView.swift", "func fixtureClosure"),            # a closure's `$0`
    ("Router.swift", "func fixtureRouterDiscounts"),         # the review's M5: outside `priceInPages`
    ("ContentView.swift", "func fixtureIfLet"),              # a condition's binding
    ("ContentView.swift", "func fixtureGuardLet"),           # `guard let`
    ("ContentView.swift", "func fixtureCase"),               # a case's binding
    ("ContentView.swift", "func fixtureThroughABox"),        # a memberwise initialiser, then the field
    ("ContentView.swift", "func fixtureAsAValue"),           # a function as a value
    ("ContentView.swift", "func fixtureAppended"),           # a mutating method's argument
    ("ContentView.swift", "func fixtureByProtocol"),         # a protocol requirement's witness
    ("ContentView.swift", "func fixtureCompound"),           # `-=`
])
def test_arithmetic_on_a_served_number_is_refused_whatever_carries_it(file: str, declaration: str) -> None:
    """The W2 review's B1 (D-181, INV-76, REQ-APP-005): the review got arithmetic on a served number past
    the gate through each of these. Each is refused, on a line of its own declaration."""
    span = _lines_of(file, declaration)
    refused = gate.problems(gate.references(FLOW_AST))
    hits = [line for line in refused if line.startswith(f"{file}:") and "served" in line
            and int(line.split(":")[1]) in span]
    assert hits, (declaration, [line for line in refused if line.startswith(f"{file}:")])


def test_foundations_sort_is_counted_as_a_sort() -> None:
    """The W2 review's M4: `sorted(using:)` (Foundation) passed the compiled sort rule, which read the
    standard library's sorts only. REQ-APP-002."""
    refused = gate.problems(gate.references(FLOW_AST))
    assert any(line.startswith("ContentView.swift:") and "sorts `standings`" in line for line in refused), refused


def test_the_price_in_pages_is_permitted_where_it_is_computed() -> None:
    """The W2 review's M5: the price permission is `priceInPages`'s, not the whole file's. REQ-APP-005."""
    refused = gate.problems(gate.references(FLOW_AST))
    span = _lines_of("Router.swift", "func priceInPages")
    assert not [line for line in refused if line.startswith("Router.swift:") and int(line.split(":")[1]) in span], refused


def test_a_sink_holds_nothing_another_file_can_change() -> None:
    """The W2 review's M1, S3 (D-180 clause 2, INV-66, REQ-GAP-001): `static let probeRelay =
    NSMutableString()` on the client, set by the screen and read by the request, passed: the rule
    refused a `var`, and a `let` holding a mutable object is as shared. What a sink holds is a
    listed type; nothing else in the fixture's sinks is refused for it."""
    refused = gate.problems(gate.references(FLOW_AST))
    assert any(line.startswith("EngineClient.swift:") and "holds `relay`" in line for line in refused), refused
    assert not [line for line in refused if "holds `" in line and "holds `relay`" not in line], refused


def test_a_sink_calls_nothing_another_file_declares_but_what_is_listed() -> None:
    """The W2 review's M1, S2b (D-180 clause 2, INV-66, REQ-GAP-001): a sink calling a function that
    `Detail.swift` declares reads whatever that function reads, and the screen can set it. A sink
    calls only the functions listed for it, each with its reason."""
    refused = gate.problems(gate.references(FLOW_AST))
    assert any(line.startswith("EngineClient.swift:") and "calls `fixtureRelayed`" in line for line in refused), refused
    assert not [line for line in refused if "calls `" in line and "fixtureRelayed" not in line], refused


def _refused_in(file: str, phrase: str) -> list[str]:
    return [line for line in gate.problems(gate.references(FLOW_AST)) if line.startswith(f"{file}:") and phrase in line]


def test_a_kept_type_is_extended_only_in_its_own_file_and_conforms_to_no_protocol_the_app_declares() -> None:
    """The second W2 review's B1, P3w (D-180, INV-66, REQ-GAP-001): the M17 mutant P3 again, through a
    protocol requirement `FetchedStandings.init(payload:)` satisfies, passed `make check-fast`: the
    provenance rule reads references to the initialiser by name, and a requirement is another name."""
    assert _refused_in("Detail.swift", "conforms to `FixtureMadeFromBytes`")
    assert _refused_in("Detail.swift", "extends `FetchedStandings`")


def test_only_the_store_builds_a_store_or_saves_to_one() -> None:
    """The second W2 review's U10 and P3w (D-180, INV-66, REQ-GAP-001): a store built on a path made
    from the question, and standings saved from another file, each passed every compiled check."""
    assert _refused_in("Detail.swift", "StandingsStore.init(url:)")
    assert _refused_in("Detail.swift", "StandingsStore.save(_:at:)")
    assert not _refused_in("StandingsStore.swift", "`StandingsStore.")


def test_no_file_touches_memory_unsafely() -> None:
    """The second W2 review's U9 (INV-66, REQ-GAP-001): the client's address rewritten in place through
    `withUnsafeMutablePointer` passed. The client uses no unsafe memory, so all of it is refused."""
    assert _refused_in("Detail.swift", "withUnsafeMutablePointer")


def test_a_url_out_of_any_by_a_cast_is_made() -> None:
    """The second W2 review's U11 and M6 (INV-63, REQ-GAP-001): `value as? URL` makes a URL no call
    returns, so `url_facts` never saw it; nor a `case let u as URL` pattern."""
    cast = ('(source_file "/x/Detail.swift"\n'
            '  (conditional_checked_cast_expr type="URL?" location=/x/Detail.swift:3:5 '
            'range=[/x/Detail.swift:3:5 - line:3:9] value_cast written_type="URL"\n')
    pattern = ('(source_file "/x/Detail.swift"\n'
               '  (pattern_is type="Any" cast_kind=value_cast cast_to="URL"\n')
    assert gate.url_facts(cast) == {"Detail.swift": {"Foundation.URL.made"}}
    assert gate.url_facts(pattern) == {"Detail.swift": {"Foundation.URL.made"}}


def test_the_code_a_sink_runs_reads_no_shared_mutable_state() -> None:
    """The second W2 review's B2, S5 and S5b (D-180, INV-66, INV-67, REQ-GAP-001): the body of
    `FetchedStandings.init(payload:)`, a call the sinks may make, and a decoding witness it reaches,
    each wrote the screen's global into the standings file, and no rule read them. What a sink runs,
    followed through the calls it makes and every coding witness, reads no shared `var`."""
    refused = _refused_in("Models.swift", "a privacy sink runs")
    assert any("fixtureStamped" in line for line in refused), refused
    assert any("FixtureNoted" in line for line in refused), refused


def test_foundations_nsarray_sort_is_counted_as_a_sort() -> None:
    """The second W2 review's M4 (REQ-APP-002): `NSArray.sortedArray(comparator:)` was no sort to the
    compiled rule."""
    assert _refused_in("ContentView.swift", "with `sortedArray`")


def test_the_committed_dump_is_the_fixture_as_it_compiles(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The second W2 review's K1: `g2_fixture_ast.txt` is a second copy of the fixture's compile, and
    nothing compared the two where Xcode runs. The self-test now does, and fails when they differ. The
    committed dump stands in for the compile, so this runs where there is no Xcode too."""
    monkeypatch.setattr(gate, "dump_ast", lambda sdk_name, flags, folder=gate.CLIENT: (FLOW_AST, 0))
    assert gate.self_test() == [], "the committed dump is not the fixture as the gate reads it"
    stale = tmp_path / "g2_fixture_ast.txt"
    stale.write_text(FLOW_AST.replace("fixtureStamped", "fixtureStampedLongAgo"), encoding="utf-8")
    monkeypatch.setattr(gate, "SNAPSHOT", stale)
    broken = gate.self_test() or []
    assert any("g2_fixture_ast.txt" in line for line in broken), broken


def test_a_permission_the_client_no_longer_uses_fails_the_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    """M19-W2 Tester (D-181 clause 5; D-180 clause 2's listed calls; the W2 review's R3): "a permission
    the shipping client no longer uses fails the gate, so a ruling cannot outlive its code and a change
    in the compiler's printed layout cannot silence a rule unnoticed". Nothing held it: with
    `unseen_permissions` returning nothing, or `main()` not calling it, every test passed. Here each
    kind of permission is judged on the compiled fixture's own facts (seen where the fixture uses it,
    reported where it does not), and `main()` fails a client that shows none of them.
    # covers REQ-APP-005, REQ-GAP-001, D-180, D-181"""
    missing = gate.unseen_permissions(gate.references(FLOW_AST))
    for seen in ("Combine.swift: position arithmetic", "Combine.swift: `sorted` on `common`",
                 "StandingsStore.swift: a call to `FetchedStandings.init`"):
        assert seen not in missing, ("the fixture uses this permission", seen, missing)
    for unseen in ("Uncertainty.swift: score arithmetic", "Router.swift: price arithmetic in priceInPages",
                   "FrontDoor.swift: `sorted` on `entries`", "EngineClient.swift: a call to `UIText.engineAddress`",
                   "`GapEntry`, which no type decodes"):
        assert unseen in missing, ("the fixture does not use this permission", unseen, missing)

    names = {path.name for path in gate.CLIENT.rglob("*.swift")}
    monkeypatch.setattr(gate, "self_test", lambda: [])
    monkeypatch.setattr(gate, "dump_ast", lambda sdk_name, flags, folder=gate.CLIENT: ("", 0))
    monkeypatch.setattr(gate, "problems", lambda found: [])
    monkeypatch.setattr(gate, "references", lambda ast: {name: set() for name in names})
    assert gate.main() == 1, "a client that uses none of the permissions passed the gate"
    # The control: with no permission granted, the same client passes, so the failure above is theirs.
    for table in ("ARITHMETIC_PERMITTED", "SORTS_PERMITTED", "SINK_CALLS_PERMITTED", "NOT_SERVED"):
        monkeypatch.setattr(gate, table, {})
    assert gate.main() == 0


#: M19-W2 Tester: two routes D-180 clause 2 names for the code a sink runs elsewhere, which no fixture
#: planted: a computed property (here read inside `FetchedStandings.init`, a call the sink may make),
#: and a protocol requirement the sink's own file declares, answered by a conformance in another file.
#: Each body reads the screen's global. The sink calls nothing it may not, so only `_SinkReach` sees them.
SINK_REACH_PROBE = {
    "EngineClient.swift": (
        "import Foundation\n\n"
        "protocol ProbeTagging {\n    func tag() -> String\n}\n\n"
        "struct ProbeClient {\n"
        "    func tagged(_ tagger: any ProbeTagging) -> String { tagger.tag() }\n"
        "    func kept(_ data: Data) -> FetchedStandings? { try? FetchedStandings(payload: data) }\n"
        "}\n"),
    "Models.swift": (
        "import Foundation\n\n"
        "nonisolated(unsafe) var probeNote = \"\"\n\n"
        "struct FetchedStandings {\n    let payload: Data\n\n"
        "    init(payload: Data) throws {\n        self.payload = payload + Data(ProbeHolder.suffix.utf8)\n    }\n}\n"),
    "Detail.swift": (
        "import Foundation\n\n"
        "struct ProbeHolder {\n    static var suffix: String { probeNote }\n}\n\n"
        "struct ProbeTagger: ProbeTagging {\n    func tag() -> String { probeNote }\n}\n"),
}


@pytest.mark.needs("xcode")  # the probe is compiled
def test_the_code_a_sink_runs_is_followed_into_computed_properties_and_protocol_witnesses(tmp_path: Path) -> None:
    """M19-W2 Tester (D-180 clause 2, INV-66): `_SinkReach` follows "the functions, initialisers and
    computed properties it calls ... every member a protocol requirement may dispatch to". Only the
    function route was planted (the fixture's `fixtureStamped`), so with the computed-property or the
    protocol branch of `_SinkReach.reached` removed every test passed. Compiled, as the gate compiles.
    # covers REQ-GAP-001, D-180"""
    for name, source in SINK_REACH_PROBE.items():
        (tmp_path / name).write_text(source, encoding="utf-8")
    _, sdk_name, flags = gate.CONFIGURATIONS[0]
    dumped = gate.dump_ast(sdk_name, flags, tmp_path)
    assert dumped is not None and dumped[1] == 0, dumped and dumped[0][-800:]
    refused = gate.problems(gate.references(dumped[0]))
    runs = [line for line in refused if line.startswith("Detail.swift:") and "code a privacy sink runs" in line]
    assert any("`ProbeHolder.suffix`" in line and "`probeNote`" in line for line in runs), refused
    assert any("`ProbeTagger.tag()`" in line and "`probeNote`" in line for line in runs), refused
    assert len(refused) == 2, ("the probe's sink calls nothing it may not; only the two bodies are refused", refused)


def test_the_readers_text_reaches_no_argument_of_a_request() -> None:
    """#174, #188 (INV-64 on the compiled module): the M19 closure seat's S2 line (the typed question
    sent as the budget) and the typed question kept as the surface are refused at their call and their
    assignment; the screen's own request, its routed surface and its chosen one are allowed."""
    assert _refused_in("ContentView.swift", "the request's `budget` argument")
    assert _refused_in("ContentView.swift", "assigns `ContentView.task`")
    refused = _refused_in("ContentView.swift", "#174, #188")
    assert len(refused) == 2, refused


def test_a_request_argument_the_gate_does_not_know_is_refused() -> None:
    """#174: a new request parameter is a reviewed change, so an argument not in REQUEST_ARGUMENTS is
    refused whatever it names."""
    assert ("EngineClient.recommendation(task:budget:)", "task") in gate.REQUEST_ARGUMENTS
    assert gate._request_problem("ContentView.swift", "<request argument>.EngineClient.search(text:)|text|a value@9")


def test_a_mac_without_the_toolchain_fails_the_gate_rather_than_skipping(monkeypatch: pytest.MonkeyPatch) -> None:
    """#175 R1: a Mac with Xcode is the gate's authoritative host (`docs/security-invariants.md`, gap
    G-10); a skip there would pass the routes D-180 and D-181 moved onto the compiled module unread. On
    another host the gate still says it skipped."""
    monkeypatch.setattr(gate, "dump_ast", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(gate, "_host", lambda: "Darwin")
    assert gate.main() == 1
    monkeypatch.setattr(gate, "_host", lambda: "Linux")
    assert gate.main() == 0


def test_the_self_test_compiles_the_fixture_in_every_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    """#175 R3: the fixture carries a refused shape per rule in each configuration the gate reads, so a
    layout change in any of them fails the self-test. The fixture is compiled once per configuration."""
    seen: list[list[str]] = []

    def dump(_sdk: str, flags: list[str], *_rest: object) -> tuple[str, int]:
        seen.append(list(flags))
        return "", 0

    monkeypatch.setattr(gate, "dump_ast", dump)
    gate.self_test()
    assert [flags for _, _, flags in gate.CONFIGURATIONS] == seen


def test_every_rule_has_a_refused_shape_in_the_fixture() -> None:
    """#175 R3: each rule the gate applies has at least one refusal the fixture must produce, so a layout
    change that silences one rule fails the self-test."""
    phrases = {phrase for _, phrase in gate.FIXTURE_REFUSALS}
    assert len(gate.FIXTURE_RULES) >= 8, "the rules are not named"
    for rule, phrase in gate.FIXTURE_RULES.items():
        assert any(phrase in carried for carried in phrases), f"no fixture refusal carries the {rule} rule"
