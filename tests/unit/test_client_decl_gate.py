"""#51, #58 -- the compiler-level half of D-126 (`scripts/client_decl_gate.py`, `make client-decls`)
refuses the forms its lists name, and that is held by tests rather than by hand-run review probes.
What the client keeps on the phone is held in part by the compiled gate and the text pins: see
INV-62, INV-63, INV-64, INV-66, INV-67, INV-75, INV-76, INV-85 and INV-89 in
`docs/security-invariants.md`, whose gaps name what is not held.

- The rules, on what the compiler printed: these run everywhere, including CI, which has no Xcode.
- The whole gate on a compiled fixture (`scripts/client_decl_fixtures/`): runs where Xcode is, and
  `make client-decls` runs the same fixture before it checks the app, so the gate cannot pass the
  app while a rule `FIXTURE_RULES` names has stopped refusing (G-10).
"""

from __future__ import annotations

import importlib.util
import re
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


def test_the_listed_network_and_file_system_symbols_are_refused_outside_their_files() -> None:
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
    # #242: the network rule allows the door its decode; the engine client's own Foundation list (measured on the
    # shipping client, which decodes no URL) refuses it, which is more refused, never less.
    assert not [line for line in gate.problems({"EngineClient.swift": found["ContentView.swift"]}) if "network" in line]


@pytest.mark.needs("xcode")  # the fixture is compiled
def test_the_gate_refuses_its_compiled_fixture() -> None:
    """#51: the whole gate, compiled, on files that must be refused and files that must be allowed.

    The M21-W3 Tester (#175 R3, G-10): the self-test asks for one refusal per (file, phrase) and compares the
    committed dump with the compile by its declarations only. So a fixture shape whose body changed, while
    another shape still carried its phrase, left every test green: `keepAsked`'s `task = typed` (#188) made
    `_ = typed` passed the self-test, and the tests that count shapes read the stale dump. The compiled
    fixture is refused line for line as the committed dump is. # covers REQ-GAP-001, REQ-APP-005"""
    assert gate.self_test() == []
    _, sdk_name, flags = gate.CONFIGURATIONS[0]
    dumped = gate.dump_ast(sdk_name, flags, gate.FIXTURES)
    assert dumped is not None and dumped[1] == 0, dumped and dumped[0][-800:]
    compiled = gate.references(gate.fixture_dump(dumped[0]))
    committed = gate.references(FLOW_AST)
    assert sorted(gate.problems(compiled)) == sorted(gate.problems(committed)), (
        "the fixture as it compiles is not refused as the committed dump is; write it again with `--snapshot`")
    assert sorted(gate.release_problems(compiled)) == sorted(gate.release_problems(committed))


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
    while a rule `FIXTURE_RULES` names has stopped refusing (#51, G-10). Nothing held that: with the call unwired, every test here and
    `make client-decls` passed. A failed self-test returns before anything compiles, so this runs
    where there is no Xcode too."""
    monkeypatch.setattr(gate, "self_test", lambda: ["ContentView.swift: URL.decoded was not refused"])
    assert gate.main() == 1


def test_a_release_build_reading_its_launch_arguments_or_environment_is_refused() -> None:
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
FLOW_AST = (ROOT / "tests" / "unit" / "data" / "g2_fixture_ast.txt").read_text(encoding="utf-8")  # raw: not Swift, the compiled dump


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


def test_a_url_made_by_the_fixtures_calls_outside_its_files_is_refused() -> None:
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
def test_arithmetic_on_a_served_number_is_refused_in_the_forms_the_fixture_holds(file: str, declaration: str) -> None:
    """The W2 review's B1 (D-181, INV-76, REQ-APP-005): the review got arithmetic on a served number past
    the gate through each of these. Each is refused, on a line of its own declaration; any other form
    is not held (G-2; see INV-76)."""
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


def test_a_sink_holding_a_mutable_object_or_a_closure_is_refused_in_the_fixtures_forms() -> None:
    """The W2 review's M1, S3 (D-180 clause 2, INV-66, REQ-GAP-001): `static let probeRelay =
    NSMutableString()` on the client, set by the screen and read by the request, passed: the rule
    refused a `var`, and a `let` holding a mutable object is as shared. What a sink holds is a
    listed type; nothing else in the fixture's sinks is refused for it."""
    refused = gate.problems(gate.references(FLOW_AST))
    assert any(line.startswith("EngineClient.swift:") and "holds `relay`" in line for line in refused), refused
    # #172 adds the fixture's kept closure (`holds `make``), refused for the same reason.
    assert not [line for line in refused if "holds `" in line and "holds `relay`" not in line
                and "holds `make`" not in line], refused


def test_a_sink_calling_a_function_another_file_declares_is_refused_in_the_fixtures_forms() -> None:
    """The W2 review's M1, S2b (D-180 clause 2, INV-66, REQ-GAP-001): a sink calling a function that
    `Detail.swift` declares reads whatever that function reads, and the screen can set it. A sink
    calls only the functions listed for it, each with its reason."""
    refused = gate.problems(gate.references(FLOW_AST))
    assert any(line.startswith("EngineClient.swift:") and "calls `fixtureRelayed`" in line for line in refused), refused
    # #172 adds the fixture's stored default, reached by the sink's call to `FixtureDefaulted.init`.
    assert not [line for line in refused if "calls `" in line and "fixtureRelayed" not in line
                and "FixtureDefaulted.init" not in line], refused


def _refused_in(file: str, phrase: str) -> list[str]:
    return [line for line in gate.problems(gate.references(FLOW_AST)) if line.startswith(f"{file}:") and phrase in line]


def test_a_kept_type_extended_or_conformed_to_outside_its_file_is_refused_in_the_fixtures_forms() -> None:
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


def test_with_unsafe_mutable_pointer_in_the_fixture_is_refused() -> None:
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


def test_the_code_a_sink_runs_is_refused_the_shared_state_the_fixture_holds() -> None:
    """The second W2 review's B2, S5 and S5b (D-180, INV-66, INV-67, REQ-GAP-001): the body of
    `FetchedStandings.init(payload:)`, a call the sinks may make, and a decoding witness it reaches,
    each wrote the screen's global into the standings file, and no rule read them. These shapes of
    what a sink runs are refused; any other form is not held (G-1; see INV-66)."""
    refused = _refused_in("Models.swift", "a privacy sink runs")
    assert any("fixtureStamped" in line for line in refused), refused
    assert any("FixtureNoted" in line for line in refused), refused


def test_foundations_nsarray_sort_is_counted_as_a_sort() -> None:
    """The second W2 review's M4 (REQ-APP-002): `NSArray.sortedArray(comparator:)` was no sort to the
    compiled rule."""
    assert _refused_in("ContentView.swift", "with `sortedArray`")


#: #363: Xcode 27.1 (Swift 6.4) prints an Objective-C declaration with its header after the name
#: (measured: `sortedArray`); the others are the same terminator on a rule that reads that name's end.
_SDK = "/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneSimulator.platform/Developer/SDKs/iPhoneSimulator27.1.sdk"
WITH_HEADER = [
    ("ORDERING_CALL", "sortedArray", f'decl="Foundation.(file).NSArray extension.sortedArray(comparator:)@{_SDK}'
                                     '/System/Library/Frameworks/Foundation.framework/Headers/NSArray.h:652:1" '
                                     "function_ref=single apply"),
    ("HANDS_ELEMENTS", None, f'decl="Foundation.(file).NSArray extension.contains(_:)@{_SDK}/NSArray.h:40:1" '
                             "function_ref=single apply"),
    ("NUMERIC_METHOD", "adding", f'decl="Foundation.(file).NSDecimalNumber extension.adding(_:)@{_SDK}'
                                 '/NSDecimalNumber.h:80:1" function_ref=single apply'),
    ("OPERATOR", "Decimal", f'decl="Foundation.(file).Decimal extension.+@{_SDK}/Decimal.h:1:1" function_ref=unapplied'),
    ("COUNTING", None, f'decl="Swift.(file).Array extension.count@{_SDK}/Array.swift:1:1" function_ref=unapplied'),
]


@pytest.mark.parametrize(("rule", "name", "line"), WITH_HEADER, ids=[rule for rule, _, _ in WITH_HEADER])
def test_a_declaration_printed_with_its_header_is_read_by_every_rule_that_reads_its_name(
        rule: str, name: str | None, line: str) -> None:
    """#363: a rule that needed `"` or ` [with` straight after the name read no declaration Swift 6.4
    prints with its header, and the compiled gate stopped refusing an `NSArray` sort (REQ-APP-002)."""
    match = getattr(gate, rule).search(line)
    assert match, (rule, line)
    if name is not None:
        assert match.group(1) == name


@pytest.mark.parametrize(("offline", "dropped"), [("1", True), (None, False)])
def test_the_compilers_sandbox_is_dropped_only_inside_the_offline_run(
        monkeypatch: pytest.MonkeyPatch, offline: str | None, dropped: bool) -> None:
    """#363: inside `scripts/offline.sb` the `@State` macro's plugin cannot start its own sandbox, so
    the dump drops it there, and only there."""
    calls: list[list[str]] = []

    class _Done:
        stdout, stderr, returncode = "/sdk\n", "", 0

    def run(argv: list[str], **_: object) -> _Done:
        calls.append(argv)
        return _Done()

    if offline is None:
        monkeypatch.delenv("MODEL_RANKING_REQUIRE_OFFLINE", raising=False)
    else:
        monkeypatch.setenv("MODEL_RANKING_REQUIRE_OFFLINE", offline)
    monkeypatch.setattr(gate.shutil, "which", lambda _: "/usr/bin/xcrun")
    monkeypatch.setattr(gate.subprocess, "run", run)
    assert gate.dump_ast("iphonesimulator", []) == ("", 0)
    assert ("-disable-sandbox" in calls[-1]) is dropped


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
    for table in ("ARITHMETIC_PERMITTED", "SORTS_PERMITTED", "SINK_CALLS_PERMITTED", "NOT_SERVED",
                  "STORE_FOUNDATION_ALLOWED", "ENGINE_CLIENT_REACHABLE", "CALLED_ONLY_IN", "KEPT_ANSWER_TYPES",
                  # #242: each sink's own list, what the code a sink runs may reference, the constants it may read.
                  "SINK_FOUNDATION_ALLOWED", "SINK_RUNS_ALLOWED", "SINK_CONSTANT_TYPES", "SERVED_MAY_MEET",
                  "BY_NAME_ALLOWED", "STORE_FOLDER_MAKERS", "STORE_READS",
                  # #371: the client's own counts and searches over a served number.
                  "COUNTS_OR_SEARCHES_PERMITTED"):
        monkeypatch.setattr(gate, table, {})
    assert gate.main() == 0


def test_an_entry_of_the_stores_or_the_engine_clients_list_the_client_no_longer_uses_fails_the_gate() -> None:
    """The backlog-gates review round 2's N1: `STORE_FOUNDATION_ALLOWED` and `ENGINE_CLIENT_REACHABLE` are
    permissions too, so an entry the shipping client no longer references is reported, per file, and the
    next file to need it does not inherit it unreviewed."""
    store = {f"Foundation.{entry}" for entry in gate.STORE_FOUNDATION_ALLOWED["FrontDoor.swift"]}
    found = {"FrontDoor.swift": store - {"Foundation.URL.made"}, **ENGINE_CLIENT_SHIPPING}
    missing = gate.unseen_permissions(found)
    assert any("FrontDoor.swift" in line and "`URL.made`" in line for line in missing), missing
    found = {"FrontDoor.swift": store, **ENGINE_CLIENT_SHIPPING, "Models.swift": set()}
    missing = gate.unseen_permissions(found)
    assert any("Models.swift" in line and "`EngineClient.maxStandingsBytes`" in line for line in missing), missing
    found = {"FrontDoor.swift": store, **ENGINE_CLIENT_SHIPPING}
    assert not [line for line in gate.unseen_permissions(found) if line.endswith(("Foundation list", "engine client's list"))]


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
    # #242: what those bodies reference off `SINK_RUNS_ALLOWED` is refused too (the probe's `+`, `Data(_:)` and
    # `.utf8` in `Models.swift`); more refused, never less. The reads are the two bodies'.
    reads = [line for line in refused if "SINK_RUNS_ALLOWED" not in line]
    assert len(reads) == 2, ("the probe's sink calls nothing it may not; only the two bodies are refused", refused)


def test_the_fixtures_six_request_shapes_are_refused_and_its_own_request_is_not() -> None:
    """#174, #188 (INV-64's listed forms on the compiled module): the M19 closure seat's S2 line (the
    typed question sent as the budget) and the typed question kept as the surface are refused at their
    call and their assignment, with the review's four round-1 twins; the screen's own request, its
    routed surface and its chosen one are allowed. Other forms are gap G-11."""
    assert _refused_in("ContentView.swift", "the request's `budget` argument")
    assert _refused_in("ContentView.swift", "assigns `ContentView.task`")
    refused = _refused_in("ContentView.swift", "#174, #188")
    # The two lines above, the M21-W3 review's four twins (B2) and round two's two key paths (#244): eight,
    # and the screen's own request, `apply`'s routed surface and `select`'s chosen one are not among them.
    # #363 (owner, 2026-10-20): Swift 6.4 expands `@State` as a macro, and the four assignments its
    # accessors make to `_task` are refused too: twelve. More refused, never fewer (fails closed).
    assert len(refused) == 12, refused


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
    """#175 R3: the fixture carries a refused shape for each rule `FIXTURE_RULES` names, in each
    configuration the gate reads, so a layout change in any of them fails the self-test. The fixture is compiled once per configuration."""
    seen: list[list[str]] = []

    def dump(_sdk: str, flags: list[str], *_rest: object) -> tuple[str, int]:
        seen.append(list(flags))
        return "", 0

    monkeypatch.setattr(gate, "dump_ast", dump)
    gate.self_test()
    assert [flags for _, _, flags in gate.CONFIGURATIONS] == seen


def test_each_rule_fixture_rules_names_has_a_refused_shape() -> None:
    """#175 R3: each rule `FIXTURE_RULES` names has at least one refusal the fixture must produce, so a
    layout change that silences one of them fails the self-test. Two rules are not named there and have
    no such refusal: the budget's literal `let` and `SINK_SWIFT_REFUSED` (G-10)."""
    phrases = {phrase for _, phrase in gate.FIXTURE_REFUSALS | gate.FIXTURE_RELEASE_REFUSALS}
    assert len(gate.FIXTURE_RULES) >= 8, "the rules are not named"
    for rule, phrase in gate.FIXTURE_RULES.items():
        assert any(phrase in carried for carried in phrases), f"no fixture refusal carries the {rule} rule"


def _marked(mark: str) -> int:
    """The line of `Arithmetic.swift` in the fixture that carries `mark`."""
    lines = (ROOT / "scripts" / "client_decl_fixtures" / "Arithmetic.swift").read_text(encoding="utf-8").splitlines()  # raw: the gate's own fixture, read whole as the compiler reads it
    found = [number for number, line in enumerate(lines, start=1) if line.rstrip().endswith(mark)]
    assert len(found) == 1, f"{mark} marks {len(found)} lines"
    return found[0]


@pytest.mark.parametrize(
    "shape",
    ["prefix-minus", "shift", "shift-assign", "operator-as-value", "operator-as-value-map", "pow", "truncating",
     "quotient", "overflow", "custom-operator", "numeric-extension", "subscript", "later-line",
     "decoded-in-extension", "through-any", "through-text", "served-fact", "fact-through-any",
     # The M21-W3 review's B3 and M1.
     "nsstring-parse", "formatter-parse", "scanner-parse", "anyhashable", "anyobject", "nsnumber",
     "json-round-trip", "xor", "bitwise-not", "bitwise-and", "fact-nsnumber", "served-dollar",
     # A count of a list a served number builds (the review's M1 allowance, laundered).
     "count-of-built", "range-count", "drop-count"],
)
def test_each_shape_the_second_review_planted_is_refused(shape: str) -> None:
    """#173 (D-181, G-2): every operator, method and name the second M19-W2 review planted past the
    arithmetic rule is refused at its own line."""
    line = _marked(f"// shape: {shape}")
    refused = [found for found in gate.problems(gate.references(FLOW_AST)) if found.startswith(f"Arithmetic.swift:{line}:")]
    assert refused, f"{shape} (Arithmetic.swift:{line}) is not refused"


def test_a_count_of_served_things_is_not_arithmetic_on_a_served_number() -> None:
    """#173, the review's M5: `filter { $0.position > 0 }.count + 1` counts things; the walk read the
    closure inside the operand and refused it as `+` on a served position. It is still never arithmetic; since #371
    (D-218 clause 4) the comparison inside `filter`, a closure that counts, is refused, and only that. # covers D-218"""
    line = _marked("// shape: filter-count")
    refused = [found for found in gate.problems(gate.references(FLOW_AST)) if found.startswith(f"Arithmetic.swift:{line}:")]
    assert refused, f"Arithmetic.swift:{line} is not refused"
    assert all("inside the closure given to `filter`" in found for found in refused), refused


def test_a_labels_length_is_not_a_served_number() -> None:
    """#171: following a served number through text must not make a label's length one."""
    line = _marked("// allowed: label-length")
    assert not [found for found in gate.problems(gate.references(FLOW_AST)) if found.startswith(f"Arithmetic.swift:{line}:")]


def test_the_routes_172_names_into_a_sink_are_refused_in_the_fixtures_forms() -> None:
    """#172 (D-180, INV-66, gap G-1): a stored default (the sink's call to another file's initialiser), a
    closure the sink keeps (a sink holds only values), a static `let`'s initialiser reading the screen's
    state, and Foundation's shared state read in a sink: each refused on the fixture."""
    assert _refused_in("EngineClient.swift", "FixtureDefaulted.init")
    assert _refused_in("EngineClient.swift", "holds `make`")
    assert _refused_in("Detail.swift", "`FixtureStatics.tag`, code a privacy sink runs")
    assert _refused_in("EngineClient.swift", "uses `Thread.threadDictionary`")
    assert _refused_in("EngineClient.swift", "uses `NotificationCenter")



# --- The M21-W3 review (docs/reviews/m21-wave-3-review.md) ------------------------------------------------


@pytest.mark.parametrize("mark", ["nearby-row-numbers", "positions-count", "indices-count", "row-numbers",
                                  "keypath-count"])
def test_counts_and_row_numbers_are_not_served_numbers(mark: str) -> None:
    """The review's M1: a count of served numbers, a row number, and a closure's `$0` a few lines below a
    served one are not served numbers; the served `$0` itself still is (`served-dollar`)."""
    line = _marked(f"// allowed: {mark}")
    assert not [found for found in gate.problems(gate.references(FLOW_AST)) if found.startswith(f"Arithmetic.swift:{line}:")]


def test_a_served_fact_is_a_kind_of_its_own_and_d143_permits_only_it() -> None:
    """The review's B3: the three D-143 places restate a served fact's number out of 100; a served count
    or any other number there is arithmetic no ruling names."""
    assert gate._flow_problem("Uncertainty.swift", "<arithmetic>.fact@5 * in scoreOutOf100") is None
    assert gate._flow_problem("Uncertainty.swift", "<arithmetic>.number@5 * in scoreOutOf100") is not None
    assert gate._flow_problem("Uncertainty.swift", "<arithmetic>.number@5 * in anchoredFact") is not None
    assert gate._served_cases(gate._tree(FLOW_AST))[("ShapeValue", "number")] == "fact"


def test_round_one_process_state_and_object_constants_in_a_sink_are_refused() -> None:
    """The review's round-1 B1 (INV-66's listed forms): Foundation's process-wide state in a sink (the
    main thread's and the main queue's names, the process name, the default time zone), and a constant
    or a static another file holds whose declared type is a mutable container class `FOUNDATION_OBJECT`
    lists, are refused where the sink reads them. Behind a widened type it is not held (gap G-1)."""
    for phrase in ("Thread.main", "ProcessInfo.processName", "OperationQueue.main", "NSTimeZone.default"):
        assert _refused_in("EngineClient.swift", phrase), phrase
    assert _refused_in("EngineClient.swift", "reads `fixtureScreenBox`")
    assert _refused_in("EngineClient.swift", "reads `box`")


def test_round_one_twins_of_the_surface_are_refused() -> None:
    """The review's round-1 B2 (INV-64's listed forms): the surface set through the wrapper's storage or
    its binding, from an outcome a helper in another file builds, and the request method held as a
    value: each refused. Round 2's twins are not (gap G-11)."""
    assert _refused_in("ContentView.swift", "ContentView._task")
    assert _refused_in("ContentView.swift", "used as a value")
    assert _refused_in("Detail.swift", "builds RoutingOutcome")
    assert _refused_in("Detail.swift", "extends `RoutingOutcome`")
    assert len(_refused_in("ContentView.swift", "assigns `ContentView.task`")) >= 2


def test_the_mutable_classes_url_initialisers_and_an_expression_by_name_are_refused() -> None:
    """The review's M2 (#168's twins) and K1 (#241)."""
    assert _refused_in("ContentView.swift", "NSMutableArray.init(contentsOf")
    assert _refused_in("ContentView.swift", "NSExpression")


def test_the_fixture_carries_the_five_rules_it_lacked() -> None:
    """The review's M4 (#175 R3): the UIKit and CoreFoundation symbol lists, a path built outside its
    files, a second @AppStorage, and the Release-only hook, each refused on the fixture, and each a rule
    the self-test names."""
    assert _refused_in("Detail.swift", "UIKit.UIPasteboard")
    assert _refused_in("Detail.swift", "CoreFoundation.CFSocketCreate")
    assert _refused_in("Detail.swift", "builds a path")
    assert _refused_in("Detail.swift", "stores something outside the register")
    released = gate.release_problems(gate.references(FLOW_AST))
    assert any(line.startswith("ContentView.swift:") and "Debug-only UI test hook" in line for line in released)
    assert {"the UIKit symbol list", "the CoreFoundation symbol list", "a path built elsewhere",
            "a second @AppStorage", "the Release-only hook"} <= set(gate.FIXTURE_RULES)


def test_the_text_tripwire_names_the_compiled_served_fields_on_the_fixture() -> None:
    """The review's M3 (#169): the text derivation (`_served_numbers`, for the lanes with no Xcode) and the
    compiled gate's `served_fields` name the same fields on the fixture, a served fact's enum payload and
    a field typed as one included; and on the shipping client the text list holds the served facts."""
    from .test_ios_client_contract import _served_numbers, _swift

    compiled = {field for _, field in gate.served_fields(gate._tree(FLOW_AST))}
    fixture = {p.name: _swift(p) for p in (ROOT / "scripts" / "client_decl_fixtures").glob("*.swift")}
    text = _served_numbers(fixture)
    assert text == compiled, (sorted(compiled - text), sorted(text - compiled))
    assert {"whyFact", "tradeOffFact", "number", "number(_:)"} <= _served_numbers()


def test_reflection_and_the_runtime_by_name_are_refused() -> None:
    """Past the review's K1 (#241): `Mirror` reads any stored field by name, past the served-field flow
    (G-2); the ObjectiveC runtime's associated objects carry the reader's words from the screen to code
    a sink runs (G-1); and the runtime's class, method and selector functions reach code by name. The
    client uses none of them, so each is refused outright."""
    assert _refused_in("Arithmetic.swift", "Mirror")
    assert _refused_in("ContentView.swift", "objc_setAssociatedObject")
    assert _refused_in("Detail.swift", "objc_getAssociatedObject")
    for symbol in ("NSClassFromString(_:", "NSSelectorFromString(_:", "class_getInstanceMethod(_:_:",
                   "method_exchangeImplementations(_:_:", "Mirror.init(reflecting:"):
        problem = gate._capability_problem("ContentView.swift", symbol, symbol)
        assert problem is not None and "by name" in problem, (symbol, problem)


# --- The M21-W3 Tester (docs/reviews/m21-wave-3-tester.md) ------------------------------------------------


def test_the_self_test_requires_the_release_rule_in_each_release_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    """The M21-W3 Tester (the review's M4, G-10: "the Release configurations run their own rule on it"): with
    the self-test's Release branch removed whole, its call and its expectation, every test and the self-test
    passed, since nothing else asks for the Release-only hook's refusal. Here the rule is silenced, and the
    self-test must say so in the two Release configurations and in no other. The committed dump stands in for
    the compile, so this runs where there is no Xcode too. # covers REQ-GAP-001"""
    monkeypatch.setattr(gate, "dump_ast", lambda sdk_name, flags, folder=gate.CLIENT: (FLOW_AST, 0))
    assert gate.self_test() == []
    monkeypatch.setattr(gate, "release_problems", lambda found: [])
    broken = gate.self_test() or []
    missed = sorted(line.split(")")[0] + ")" for line in broken if "Debug-only UI test hook was not refused" in line)
    assert missed == ["(device, release)", "(simulator, release)"], broken


def test_a_mac_without_the_toolchain_fails_by_the_name_its_platform_gives(monkeypatch: pytest.MonkeyPatch) -> None:
    """The M21-W3 Tester (#175 R1, G-10): the test above replaces `_host` itself, so a `_host` that misnames
    the Mac (`platform.system().lower()`, which is "darwin") skipped the gate on the owner's Mac with every
    test green. Here only the platform's own answer is replaced. # covers REQ-GAP-001"""
    monkeypatch.setattr(gate, "dump_ast", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(gate.platform, "system", lambda: "Darwin")
    assert gate.main() == 1, "the gate skipped on a Mac without its toolchain"
    monkeypatch.setattr(gate.platform, "system", lambda: "Linux")
    assert gate.main() == 0


def test_a_sink_is_refused_the_command_lines_two_members() -> None:
    """The M21-W3 Tester (D-180, the review's B1): `SINK_SWIFT_REFUSED` has no shape in the fixture (G-10), so
    with it emptied every test passed. `CommandLine`'s arguments are process-wide state; a privacy sink reads
    none, and a file that is no sink is not refused for them. # covers REQ-GAP-001"""
    for sink in gate.SINK_FILES:
        for symbol in ("CommandLine.arguments", "CommandLine.unsafeArgv"):
            assert gate.problems({sink: {f"Swift.{symbol}"}}), (sink, symbol)
    assert gate._sink_module_problem("ContentView.swift", "Swift", "CommandLine.arguments") is None


def test_make_client_decls_runs_the_gate_and_keeps_its_status() -> None:
    """The M21-W3 Tester (#175 R1, G-10): `main()` fails on a Mac without its toolchain, and `make
    client-decls` is how `make check-fast` and `make check` reach it. With the recipe's line made
    `-$(PY) ...`, make printed "Error 1 (ignored)" and passed, and every test stayed green. The recipe runs
    the gate and nothing that could drop its status. # covers REQ-GAP-001"""
    lines = (ROOT / "Makefile").read_text(encoding="utf-8").splitlines()
    start = next(index for index, line in enumerate(lines) if line.startswith("client-decls:"))
    recipe: list[str] = []
    for line in lines[start + 1:]:
        if not line.startswith("\t"):
            break
        recipe.append(line.strip())
    assert [line for line in recipe if not line.startswith("@#")] == ["$(PY) -B scripts/client_decl_gate.py"], recipe


def _without_subtree(ast: str, opening: str) -> str:
    """The dump with the node whose line starts with `opening` removed, children and all."""
    lines = ast.splitlines(keepends=True)
    start = next(index for index, line in enumerate(lines) if line.lstrip().startswith(opening))
    depth = len(lines[start]) - len(lines[start].lstrip())
    end = start + 1
    while end < len(lines) and len(lines[end]) - len(lines[end].lstrip()) > depth:
        end += 1
    return "".join(lines[:start] + lines[end:])


def test_make_client_decls_fails_when_the_fixture_is_refused_otherwise_than_its_dump(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """The M21-W3 Tester's M2 (G-10): the self-test asked for one refusal per (file, phrase) and compared the
    committed dump with the compile by its declarations only, so `keepAsked`'s `task = typed` (#188) taken
    out of the compile left `make client-decls` green: another shape still carried its phrase. The self-test
    compares the compiled fixture's refusals with the committed dump's, line for line. The committed dump
    stands in for the compile, so this runs where there is no Xcode too. # covers REQ-GAP-001"""
    compiled = _without_subtree(FLOW_AST, "(assign_expr type=\"()\" location=/x/ContentView.swift:232:")
    assert compiled != FLOW_AST
    monkeypatch.setattr(gate, "dump_ast", lambda sdk_name, flags, folder=gate.CLIENT: (compiled, 0))
    broken = gate.self_test() or []
    assert any("refused otherwise" in line for line in broken), broken


def test_the_objective_c_runtime_module_is_refused_in_the_client() -> None:
    """The M21 closure security seat's S6: `BY_NAME` refused three families of the runtime by prefix while
    `ObjectiveC`, the module that declares all of it (`sel_registerName`, `object_*`, `ivar_*`), was on the
    allowlist. The shipping client resolves nothing there, so the module is off the list, for a sink too."""
    assert "ObjectiveC" not in gate.MODULES and "ObjectiveC" not in gate.SINK_MODULES
    refused = gate._module_problem("Detail.swift", "ObjectiveC", "sel_registerName", "ObjectiveC.(file).sel_registerName")
    assert refused and "ObjectiveC" in refused
    assert gate._module_problem("Detail.swift", "ObjectiveC", "<imported>", "ObjectiveC")


def test_the_fixture_holds_a_runtime_call_the_module_rule_refuses() -> None:
    """S6: the fixture plants one call into the runtime, under the module allowlist, and the committed dump
    holds its refusal."""
    fixture = (ROOT / "scripts" / "client_decl_fixtures" / "Imports.swift").read_text(encoding="utf-8")  # raw: the gate's own fixture, read whole as the compiler reads it
    assert "sel_registerName" in fixture
    refused = gate.problems(gate.references((ROOT / "tests" / "unit" / "data" / "g2_fixture_ast.txt").read_text(encoding="utf-8")))  # raw: not Swift, the compiled dump
    assert any("Imports.swift" in line and "ObjectiveC" in line for line in refused), refused[:5]


#: #246: every URL, file-system and resource symbol the two stores reference on the shipping client,
#: as `references` reads them (measured 2026-10-14, the simulator's Release configuration).
STORES_SHIPPING_URLS = {
    "Foundation.Data.init(contentsOf:options:", "Foundation.FileManager.urls(for:in:", "Foundation.FileManager.temporaryDirectory",
    "Foundation.URL.appendingPathComponent", "Foundation.URL.appendingPathComponent(_:isDirectory:",
    "Foundation.URL.deletingLastPathComponent(", "Foundation.URL.isFileURL", "Foundation.URL.made",
}


@pytest.mark.parametrize("store", ["FrontDoor.swift", "StandingsStore.swift"])
@pytest.mark.parametrize("maker", ["Foundation.URL.init(_:strategy:", "Foundation.URL.init(string:",
                                   "Foundation.URL.init(string:relativeTo:", "Foundation.URL.init(dataRepresentation:relativeTo:isAbsolute:",
                                   "Foundation.URL.init(resolvingBookmarkData:options:relativeTo:bookmarkDataIsStale:",
                                   "Foundation.URL.decoded", "Foundation.NSURL.init(string:"])
def test_a_store_makes_a_url_only_from_the_file_systems_folders(store: str, maker: str) -> None:
    """#246 (G-13, the M21-W3 review's round 3): the stores were allowed to make a URL by any call, and
    `Data(contentsOf:)` fetches an `https` address as readily as a file. A store now makes one only by
    a folder the file manager names, and a component appended to it or removed. Any URL initialiser or
    decode in a store is refused."""
    refused = gate.problems({store: {maker, "Foundation.Data.init(contentsOf:options:"}})
    # `StandingsStore.swift` is also a privacy sink, whose Foundation list refuses most of these first.
    reasons = ("a store makes a URL only", "not on the list of Foundation declarations a privacy sink")
    assert any(line.startswith(f"{store}:") and any(r in line for r in reasons) for line in refused), refused
    if store == "FrontDoor.swift":
        assert any("a store makes a URL only" in line for line in refused), refused
    else:
        # #242 (the backlog-gates review round 2's K1): the standings store has its own Foundation list, so it no
        # longer inherits `URL.init(string:` and `URL.decoded` from the engine client's, and that list names each.
        assert any(f"`{maker}` is not on the list of Foundation declarations a privacy sink" in line for line in refused), refused


def test_the_stores_shipping_urls_pass() -> None:
    """#246: what the stores do today is on the list, so the rule refuses nothing they ship."""
    assert gate.problems({"FrontDoor.swift": STORES_SHIPPING_URLS}) == []
    assert "a URL a store makes from text" in gate.FIXTURE_RULES


def test_the_gap_registers_file_references_only_its_listed_foundation_declarations() -> None:
    """The backlog-gates review round 1's M2: `STORE_URL_MAKERS` matched nothing the rule read, so a URL parsed by
    a strategy and loaded passed. The register's file now references only the Foundation declarations
    measured on the shipping client; a parse strategy or a format style is refused by absence."""
    assert gate.problems({"FrontDoor.swift": {f"Foundation.{d}" for d in gate.STORE_FOUNDATION_ALLOWED["FrontDoor.swift"]}}) == []
    for symbol in ("Foundation.URL.ParseStrategy.init(", "Foundation.URL.ParseStrategy.parse(",
                   "Foundation.URL.FormatStyle.parseStrategy", "Foundation.URLComponents.url"):
        refused = gate.problems({"FrontDoor.swift": {symbol}})
        assert any("a store may reference" in line and symbol in line for line in refused), refused
    assert not hasattr(gate, "STORE_URL_MAKERS")


def test_round_two_twins_of_the_surface_are_refused() -> None:
    """#244 (the M21-W3 review's round-2 B2, gap G-11): a key path to the surface bound to a name before the
    write, the same key path handed to a generic writer, and a subscript on the engine client that forwards
    to the request. Each was refused by no rule; the fixture holds each now."""
    assert len(_refused_in("ContentView.swift", "a key path to `ContentView.task`")) >= 2
    assert _refused_in("ContentView.swift", "EngineClient.subscript")


#: #244: every member of the engine client a file other than its own references on the shipping client,
#: as `references` reads them (measured 2026-10-14, the simulator's Release configuration).
ENGINE_CLIENT_SHIPPING = {
    "ContentView.swift": {"main.EngineClient.baseURL", "main.EngineClient.boards(", "main.EngineClient.categories(",
                          "main.EngineClient.init(", "main.EngineClient.recommendation(task:budget:"},
    "Models.swift": {"main.EngineClient.maxStandingsBytes"},
}


def test_a_file_reaches_only_the_engine_clients_listed_members() -> None:
    """#244: outside its own file the engine client is reached only through `ENGINE_CLIENT_REACHABLE`; a
    member added to it, or to an extension of it anywhere, is a reviewed edit, not a new door. The
    backlog-gates review round 1's M1: each member is matched whole, and per file."""
    assert gate.problems(ENGINE_CLIENT_SHIPPING) == []
    for member in ("main.EngineClient.subscript(asking:", "main.EngineClient.ask(_:", "main.EngineClient.session",
                   "main.EngineClient.init(asking:", "main.EngineClient.baseURLSender",
                   "main.EngineClient.recommendation(task:budget:asking:"):
        refused = gate.problems({"ContentView.swift": {member}})
        assert any("engine client" in line and member.removeprefix("main.") in line for line in refused), refused
    for name in ("Models.swift", "FrontDoor.swift"):
        refused = gate.problems({name: {"main.EngineClient.baseURL"}})
        assert any("engine client" in line and line.startswith(f"{name}:") for line in refused), refused
    assert gate.problems({"EngineClient.swift": {"main.EngineClient.session"}}) == []


def test_the_gap_registers_file_matches_its_foundation_list_whole_and_in_each_foundation_module() -> None:
    """#246, the gates Tester (T4). The store's list is matched as the engine client's is: a declaration
    whose name begins like a listed one is another declaration, and is refused until it is listed. With
    a prefix match, `URL.appendingPathComponent(_:conformingTo:` passed under the listed
    `URL.appendingPathComponent`. The list covers each module the privacy sink's does (`SINK_MODULES`),
    not Foundation alone."""
    for symbol in ("Foundation.URL.appendingPathComponent(_:conformingTo:", "Foundation.Date.init(timeIntervalSince1970:",
                   "_DarwinFoundation1.probe("):
        refused = gate.problems({"FrontDoor.swift": {symbol}})
        assert any(line.startswith("FrontDoor.swift:") and "a store may reference" in line for line in refused), (symbol, refused)


def test_a_store_entry_is_seen_only_by_its_own_declaration() -> None:
    """The backlog-gates review round 2's N1, the gates Tester (T4). An entry counts as used only when the
    file references that declaration. `URL.appendingPathComponent` and
    `URL.appendingPathComponent(_:isDirectory:` are two entries; with the first gone from the client and the
    second kept, the first is stale. A match by substring read it as still used."""
    store = {f"Foundation.{entry}" for entry in gate.STORE_FOUNDATION_ALLOWED["FrontDoor.swift"]}
    found = {"FrontDoor.swift": store - {"Foundation.URL.appendingPathComponent"}, **ENGINE_CLIENT_SHIPPING}
    missing = gate.unseen_permissions(found)
    assert any("FrontDoor.swift" in line and "`URL.appendingPathComponent`" in line for line in missing), missing


# --- #242 (D-214 clause 1): the deny-lists become allowlists, and nothing is loosened -----------------------------


def _pinned(release: bool = True) -> list[tuple[str, str, int, str]]:
    pinned = gate.pinned_refusals(release)
    assert pinned, f"{gate.PINNED_REFUSALS.name} is missing, empty or malformed"
    return pinned


def test_the_fixture_still_refuses_everything_it_refused_before_242() -> None:
    """#242 (D-214 clause 1): every refusal the fixture made before #242 (183, the committed dump, the simulator's
    Release configuration) is pinned, and every one is still made: an allowlist may refuse more than the deny-list
    it replaces, never less. The self-test asks the same of all four configurations. # covers D-214"""
    found = gate.references(FLOW_AST)
    made = set(gate.problems(found)) | set(gate.release_problems(found))
    pinned = _pinned()
    assert len(pinned) == 183, len(pinned)
    assert len(_pinned(release=False)) == 182, "the Debug configurations make all but the Release-only hook's"
    gone = [key for key in pinned if key not in gate.refusal_keys(sorted(made))]
    assert not gone, gone


def test_the_self_test_fails_when_a_pinned_refusal_is_gone(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """#242 (D-214 clause 1), watched failing: with one pinned refusal no longer made, the self-test names it in
    every configuration; and with the pin missing, empty or malformed it fails closed. The committed dump stands
    in for the compile, so this runs where there is no Xcode too. # covers D-214"""
    monkeypatch.setattr(gate, "dump_ast", lambda sdk_name, flags, folder=gate.CLIENT: (FLOW_AST, 0))
    assert gate.self_test() == []
    dropped = _pinned()[0]
    real = gate.problems
    monkeypatch.setattr(gate, "problems", lambda found: [line for line in real(found)
                                                         if gate.refusal_keys([line]) != {dropped}])
    gone = [line for line in gate.self_test() or [] if "is gone" in line and line.endswith(gate.pin_shown(dropped))]
    assert len(gone) == len(gate.CONFIGURATIONS), gone
    monkeypatch.setattr(gate, "problems", real)
    for name, content in (("missing.txt", None), ("empty.txt", ""), ("malformed.txt", "sometimes\tx\n"),
                          ("untabbed.txt", "all x\n")):
        pin = tmp_path / name
        if content is not None:
            pin.write_text(content, encoding="utf-8")
        monkeypatch.setattr(gate, "PINNED_REFUSALS", pin)
        broken = gate.self_test() or []
        assert len([line for line in broken if "missing, empty or malformed" in line]) == len(gate.CONFIGURATIONS), (
            name, broken)


def test_242_the_sinks_twins_are_refused() -> None:
    """#242 (G-1; the backlog-gates review round 2's K1): another file's objects behind a widened type (`Any`, an
    array, a struct holding one) and a Swift-module object (`ManagedBuffer`) held in constants a sink reads, the
    same buffer read by a static `let`'s initialiser the sink runs, the current calendar in a decoder no one
    names, and a declaration the standings store inherited from the engine client's Foundation list. Each passed
    the deny-lists. # covers D-214, D-180"""
    for constant in ("fixtureWidened", "fixtureWidenedList", "fixtureHeld", "fixtureSharedBuffer"):
        assert _refused_in("EngineClient.swift", f"reads `{constant}`, a constant"), constant
    assert _refused_in("Detail.swift", "`FixtureBuffered.tag`, code a privacy sink runs, reads `fixtureSharedBuffer`")
    assert _refused_in("Detail.swift", "references `Swift.ManagedBuffer.header`")
    assert _refused_in("Detail.swift", "references `Foundation.Calendar.current`")
    assert _refused_in("StandingsStore.swift", "`Foundation.Bundle.main` is not on the list of Foundation declarations")


def test_242_each_sink_has_its_own_lists_and_a_stale_entry_fails_the_gate() -> None:
    """#242 (the backlog-gates review round 2's K1): one Foundation list per sink file, and the list of what the
    code a sink runs may reference, each entry seen on the shipping client or reported. # covers D-214, D-180"""
    assert set(gate.SINK_FOUNDATION_ALLOWED) == set(gate.SINK_FILES)
    for sink, allowed in gate.SINK_FOUNDATION_ALLOWED.items():
        found = {sink: {f"Foundation.{entry}" for entry in allowed}}
        assert not [line for line in gate.unseen_permissions(found) if line.startswith(f"{sink}:") and "sink's own list" in line]
        dropped = sorted(allowed)[0]
        found[sink].discard(f"Foundation.{dropped}")
        assert [line for line in gate.unseen_permissions(found)
                if line.startswith(f"{sink}:") and f"`{dropped}`" in line and "sink's own list" in line]
    runs = {"Models.swift": {f"main.<sink runs uses>.{entry}" for entry in gate.SINK_RUNS_ALLOWED}}
    assert not [line for line in gate.unseen_permissions(runs) if "the code a sink runs" in line]
    dropped = sorted(gate.SINK_RUNS_ALLOWED)[0]
    runs["Models.swift"].discard(f"main.<sink runs uses>.{dropped}")
    assert [line for line in gate.unseen_permissions(runs) if f"`{dropped}`" in line and "the code a sink runs" in line]


#: #242 (G-2): the twins the reviews planted past the arithmetic rule, each marked in `Arithmetic.swift`.
SERVED_TWINS = ["abs", "min", "max", "magnitude", "rounded", "table", "bound-count", "bound-range", "bound-drop",
                "string-repeating", "data-count", "data-repeating", "repeat-element"]


@pytest.mark.parametrize("shape", SERVED_TWINS)
def test_242_what_a_served_number_meets_off_its_list_is_refused(shape: str) -> None:
    """#242 (G-2, INV-76): `abs`, `min`, `max`, `.magnitude`, `.rounded(_:)`, an app's table indexed by a served
    number, and a list a served number sizes (`Array(repeating:count:)`, a range, `dropFirst`, `String(repeating:
    count:)`, `Data(count:)`, `Data(repeating:count:)`, `repeatElement`), bound to a name before its count is read
    or not. Each passed the arithmetic rule; each is refused on its own line. # covers D-214, D-181"""
    line = _marked(f"// shape: {shape}")
    refused = [found for found in gate.problems(gate.references(FLOW_AST)) if found.startswith(f"Arithmetic.swift:{line}:")]
    assert refused, f"{shape} (Arithmetic.swift:{line}) is not refused"


@pytest.mark.parametrize("mark", ["compared", "shown"])
def test_242_a_served_number_compared_or_shown_is_not_refused(mark: str) -> None:
    """#242 (G-2): what a served number may meet includes a comparison and its display. # covers D-214"""
    line = _marked(f"// allowed: {mark}")
    assert not [found for found in gate.problems(gate.references(FLOW_AST)) if found.startswith(f"Arithmetic.swift:{line}:")]


def test_242_a_meeting_the_client_no_longer_makes_fails_the_gate() -> None:
    """#242 (G-2): each entry of `SERVED_MAY_MEET`, in each place it names, is seen on the shipping client or
    reported, so the list cannot outlive its code. # covers D-214"""
    assert gate.SERVED_MAY_MEET
    seen: dict[str, set[str]] = {}
    for (declared, role), (places, _) in gate.SERVED_MAY_MEET.items():
        for file, function in sorted(places or {("Language.swift", "-")}):
            seen.setdefault(file, set()).add(f"main.<meets listed>.{declared}|{role}|{function}")
    assert not [line for line in gate.unseen_permissions(seen) if "a served number may meet" in line]
    (declared, role), (places, _) = sorted(gate.SERVED_MAY_MEET.items(), key=str)[0]
    file, function = sorted(places or {("Language.swift", "-")})[0]
    seen[file].discard(f"main.<meets listed>.{declared}|{role}|{function}")
    assert [line for line in gate.unseen_permissions(seen) if f"`{declared}`" in line and "a served number may meet" in line]


@pytest.mark.parametrize(("which", "member"), [
    ("argument 0 (unlabelled)", "EngineClient.ask"),
    ("`asking` argument", "EngineClient.init(asking:)"),
    ("`asking` argument", "EngineClient.subscript(asking:)"),
])
def test_242_every_argument_of_a_call_into_the_engine_client_is_read(which: str, member: str) -> None:
    """#242 (G-11, INV-64; the backlog-gates review's K1): `_request_call` read only the labelled arguments of a
    method call, so an unlabelled argument, an initialiser's and a subscript's were never read; the gap was latent
    while `ENGINE_CLIENT_REACHABLE` lists no such member. Every argument of a call into the engine client from
    another file is now read, and refused unless `REQUEST_ARGUMENTS` names it with its declared source.
    # covers D-214, REQ-RTR-004"""
    assert _refused_in("ContentView.swift", f"the {which} of `{member}`")


def test_242_the_screens_own_requests_arguments_are_not_refused_by_the_argument_rule() -> None:
    """#242 (G-11): the screen's own request (`load()`: its surface and its budget) and `EngineClient()` pass the
    rule that reads every argument. # covers D-214"""
    span = _lines_of("ContentView.swift", "struct ContentView {")
    own = [line for line in gate.problems(gate.references(FLOW_AST)) if line.startswith("ContentView.swift:")
           and "#242" in line and "REQUEST_ARGUMENTS" in line and int(line.split(":")[1]) in (210, 213)]
    assert 213 in span and not own, own
    # A default the caller did not write (`session:`) is not an argument it passed.
    assert not [line for line in gate.problems(gate.references(FLOW_AST)) if "the `session` argument" in line]


@pytest.mark.parametrize("declared", [
    "Foundation.NSObject.setValuesForKeys", "Foundation.NSArray.value(forKey:", "Foundation.NSDictionary.value(forKey:",
    "Foundation.NSSet.value(forKey:", "Foundation.Bundle.classNamed", "Foundation.Bundle.principalClass",
    "Foundation.NotificationCenter.addObserver(_:selector:name:object:",
    "Foundation.Timer.init(timeInterval:target:selector:userInfo:repeats:", "Foundation.Thread.init(target:selector:object:",
])
def test_242_a_value_a_class_or_a_selector_by_name_is_refused_by_its_label(declared: str) -> None:
    """#242 (G-12, INV-62; the M21-W3 review's round 2, B3): `BY_NAME` matched by owner type and name, so key-value
    coding through the collections' overrides and `setValuesForKeys(_:)`, a class by name from the bundle, and the
    target-and-selector APIs passed. Each is refused, by its argument label or as a class-by-name entry point.
    # covers D-214, D-126"""
    assert _refused_in("ContentView.swift", f"`{declared}` reaches a value, a class or a selector by name")


def test_242_a_codable_containers_key_and_the_stores_resource_keys_are_not_refused_by_name() -> None:
    """#242 (G-12): the labels the by-name rule reads are also a Codable container's (`decode(_:forKey:)`) and the
    standings store's resource keys (#314); `BY_NAME_ALLOWED` admits those, each with its reason, and every entry
    is seen on the shipping client or reported. # covers D-214"""
    shipping = {"Models.swift": {"Swift.KeyedDecodingContainer.decode(_:forKey:", "Swift.KeyedDecodingContainer.decodeIfPresent(_:forKey:"},
                "StandingsStore.swift": {"Foundation.URL.resourceValues(forKeys:"}}
    assert not [line for line in gate.problems(shipping) if "by name" in line]
    assert not [line for line in gate.unseen_permissions(shipping) if "by-name" in line]
    shipping["Models.swift"].discard("Swift.KeyedDecodingContainer.decodeIfPresent(_:forKey:")
    assert [line for line in gate.unseen_permissions(shipping) if "by-name" in line and "decodeIfPresent" in line]
    assert gate.problems({"Models.swift": {"Swift.KeyedEncodingContainer.encode(_:forKey:"}}), "an unlisted label passed"


@pytest.mark.parametrize("phrase", [
    "makes a URL by `main.fixtureStoreHelper`",          # a generic helper of the store's own, its type given
    "makes a URL by `main.fixtureStoreInferred`",        # and inferred
    "makes a URL by a cast",                             # `value as? URL`
    "makes a URL by `Foundation.JSONDecoder.decode(_:from:`",  # through `typealias FixtureAddress = URL` (#276's shape)
    "reads with `Data.init(contentsOf:options:` from GapRegisterStore.loadShadowed(_:).url",
])
def test_242_a_stores_url_comes_only_from_the_file_managers_folders(phrase: str) -> None:
    """#242 (G-13, INV-62, INV-67; the backlog-gates review rounds 2 and 3, M1; #276): `URL.made` was on the store's
    list, so a URL its own file made by a generic helper, a `typealias` or a cast passed, and so did a read of it.
    A store now makes a URL only by the file manager's makers or a function of its own file, and reads only its
    own `url`. # covers D-214, REQ-GAP-001"""
    assert _refused_in("FrontDoor.swift", phrase)


def test_242_the_registers_store_is_built_only_in_its_own_file() -> None:
    """#242 (G-13): the screen pointed the register's store at the engine's address, a URL no store made, and
    `load()` read it. Only `FrontDoor.swift` builds a `GapRegisterStore`. # covers D-214, REQ-GAP-001"""
    assert _refused_in("ContentView.swift", "builds GapRegisterStore")


def _marked_in(file: str, text: str) -> int:
    """The one line of a fixture file that carries `text`."""
    lines = (FIXTURES / file).read_text(encoding="utf-8").splitlines()
    found = [number for number, line in enumerate(lines, start=1) if text in line]
    assert len(found) == 1, (file, text, found)
    return found[0]


def test_242_the_stores_own_reads_and_folders_pass() -> None:
    """#242 (G-13): the fixture's register store reading its own `url`, and the standings store's folder made by a
    function of its own file, are not refused by the store rules. # covers D-214"""
    load = range(_marked_in("FrontDoor.swift", "func load() -> Data?"), _marked_in("FrontDoor.swift", "func loadShadowed"))
    own = [line for line in gate.problems(gate.references(FLOW_AST)) if line.startswith("FrontDoor.swift:")
           and line.split(":")[1].isdigit() and int(line.split(":")[1]) in load]
    assert len(load) > 2 and not own, own
    assert not [line for line in gate.problems(gate.references(FLOW_AST)) if "fixtureStoreFolder" in line]


def test_242_a_store_function_takes_no_url_from_its_caller() -> None:
    """#242 (G-13): a function in a store's file that takes a URL as a parameter can build the store on it, the
    initialiser's call being in the store's own file, so another file chooses the address. A URL parameter is
    admitted there only on an initialiser `PROVENANCE` keeps to that file. # covers D-214, REQ-GAP-001"""
    assert _refused_in("FrontDoor.swift", "`GapRegisterStore.fixtureAt(_:)` takes a URL")
    assert not [line for line in gate.problems(gate.references(FLOW_AST)) if "init(url:)` takes a URL" in line]


@pytest.mark.parametrize("declared", ["ObjectiveC.Selector.init(_:", "ObjectiveC.NSObject.responds(to:"])
def test_242_a_selector_made_from_text_and_asked_of_an_object_is_refused(declared: str) -> None:
    """#242 (G-12; the M21-W3 review's round 2, B3): `Selector.init` and `responds(to:)` are declared in
    `ObjectiveC`, off the module allowlist since the M21 closure (S6); the fixture plants both. # covers D-214"""
    assert _refused_in("ContentView.swift", f"`{declared}` in `ObjectiveC`")


#: #242, the security review's B1: the G-2 twins met by reference, each marked in `Arithmetic.swift`.
BY_REFERENCE_TWINS = ["map-abs", "abs-value", "max-value", "map-magnitude", "keypath-magnitude", "map-words",
                      "map-truncating", "map-app-function", "called-literal"]


@pytest.mark.parametrize("shape", BY_REFERENCE_TWINS)
def test_242_a_served_number_meeting_a_declaration_by_reference_is_refused(shape: str) -> None:
    """#242, the security review's B1 (G-2, INV-76): `abs`, `max`, `.magnitude`, `.words` and
    `Int.init(truncatingIfNeeded:)` met by reference passed: handed to `map`, held as a value and called, or named
    in a key path. The element-passing admission's premise, a closure the flow follows, was not checked. So are an
    app function handed to `map` and a closure literal called on the spot. Each is refused on its own line.
    # covers D-214, D-181"""
    line = _marked(f"// shape: {shape}")
    refused = [found for found in gate.problems(gate.references(FLOW_AST)) if found.startswith(f"Arithmetic.swift:{line}:")]
    assert refused, f"{shape} (Arithmetic.swift:{line}) is not refused"


@pytest.mark.parametrize("table", ["SINK_CONSTANT_TYPES", "STORE_FOLDER_MAKERS", "STORE_READS"])
def test_242_an_unused_constant_type_folder_maker_or_store_read_fails_the_gate(table: str) -> None:
    """#242, the security review's M4: `unseen_permissions` reports an entry of these three tables the shipping
    client no longer uses, and no test watched it: with the three reports replaced by `pass`, every test passed.
    Each table is read here with every entry seen, then with one taken away. # covers D-214"""
    seen: dict[str, set[str]] = {"Models.swift": {f"main.<sink reads constant type>.{typed}" for typed in gate.SINK_CONSTANT_TYPES}}
    for name, makers in gate.STORE_FOLDER_MAKERS.items():
        seen.setdefault(name, set()).update(f"main.<store url listed>.{maker}" for maker in makers)
    for name, read in gate.STORE_READS.items():
        seen.setdefault(name, set()).add(f"main.<store reads listed>.{read}")
    words = {"SINK_CONSTANT_TYPES": "constant types a sink may read", "STORE_FOLDER_MAKERS": "the store's list of URL makers",
             "STORE_READS": "the store's one read"}[table]
    assert not [line for line in gate.unseen_permissions(seen) if words in line]
    if table == "SINK_CONSTANT_TYPES":
        seen["Models.swift"].discard("main.<sink reads constant type>.Int")
        dropped = "`Int`"
    elif table == "STORE_FOLDER_MAKERS":
        seen["FrontDoor.swift"].discard("main.<store url listed>.Foundation.URL.deletingLastPathComponent(")
        dropped = "`Foundation.URL.deletingLastPathComponent(`"
    else:
        seen["StandingsStore.swift"].discard("main.<store reads listed>.StandingsStore.url")
        dropped = "`StandingsStore.url`"
    assert [line for line in gate.unseen_permissions(seen) if words in line and dropped in line], (table, dropped)


@pytest.mark.parametrize("declared", ["Foundation.Thread.detachNewThreadSelector(_:toTarget:with:",
                                      "Foundation.RunLoop.perform(_:target:argument:order:modes:",
                                      "Foundation.NSSortDescriptor.init(key:ascending:"])
def test_242_a_selector_unlabelled_or_a_key_labelled_key_is_refused(declared: str) -> None:
    """#242, the security review's M3 (G-12): matching by label missed a selector passed with no label and a key
    labelled `key:`. A declaration whose type takes a `Selector`, whatever its label, and a Foundation declaration
    labelled `key:` or `keyPath:` are refused unless `BY_NAME_ALLOWED` names them. # covers D-214"""
    assert _refused_in("ContentView.swift", f"`{declared}` reaches a value, a class or a selector by name")


def test_242_a_url_a_store_reads_through_a_key_path_off_another_files_type_is_refused() -> None:
    """#242, the security review's M2 (G-13): `_store_received` read only a direct reference or a member read, so a
    URL-typed declaration of another file read through a key path (`held[keyPath: \\Holder.address]`) passed, and the
    register's store was built on it. # covers D-214, REQ-GAP-001"""
    assert _refused_in("FrontDoor.swift", "receives a URL, by `FixtureAddressHolder.address`, declared in ContentView.swift")


@pytest.mark.parametrize(("declared", "role", "place", "elsewhere"), [
    ("Swift.Set.init(_:", "argument", ("AnswerPlan.swift", "disclosures"), ("AnswerPlan.swift", "-")),
    ("Swift.String.init(_:", "argument", ("Language.swift", "number"), ("Detail.swift", "detailFacts")),
    ("Swift.ClosedRange.contains", "argument", ("Uncertainty.swift", "evidenceBreadth"), ("Notices.swift", "staleSentence")),
    ("Swift.Array.subscript(_:", "receiver", ("Notices.swift", "staleSentence"), ("Language.swift", "number")),
    ("Swift.Sequence.sorted(", "receiver", ("Notices.swift", "staleSentence"), ("Combine.swift", "combined")),
])
def test_242_a_served_numbers_listed_meeting_is_admitted_only_in_its_place(
        declared: str, role: str, place: tuple[str, str], elsewhere: tuple[str, str]) -> None:
    """#242, the security review's R1 and R2: `Set(_:)` was admitted anywhere in `AnswerPlan.swift` outside a function
    (a computed property, a closure, an initialiser's expression), and four entries were open to any file though the
    shipping client meets each in one or a few places. Each is now admitted only where it is met: `Set(_:)` in the
    computed property `disclosures`, which the place names. # covers D-214"""
    assert gate._meeting(declared, role, "position", *place, 1) == f"main.<meets listed>.{declared}|{role}|{place[1]}"
    assert (gate._meeting(declared, role, "position", *elsewhere, 1) or "").startswith("main.<meets>."), elsewhere


#: #242, the security review's round 2, B1: a key path not written in place, and a method referenced without a call.
ROUND_TWO_TWINS = ["keypath-held", "keypath-held-closure", "keypath-parameter", "method-held", "distance-held",
                   "signum-held"]


@pytest.mark.parametrize("shape", ROUND_TWO_TWINS)
def test_242_a_key_path_not_written_in_place_or_a_method_referenced_unapplied_is_refused(shape: str) -> None:
    """#242, the security review's round 2, B1 (G-2): `.magnitude` through a key path bound to a name or passed as a
    parameter, which the gate cannot read, and `advanced(by:)`, `distance(to:)` and `signum` referenced on a served
    number without a call. A key-path application on a served number is refused unless its key path is written in
    place; a method referenced on one is judged as its call is. # covers D-214, D-181"""
    line = _marked(f"// shape: {shape}")
    refused = [found for found in gate.problems(gate.references(FLOW_AST)) if found.startswith(f"Arithmetic.swift:{line}:")]
    assert refused, f"{shape} (Arithmetic.swift:{line}) is not refused"


def test_242_a_store_reads_a_url_only_through_a_key_path_written_in_place() -> None:
    """#242, the security review's round 2, M2 (G-13): the register's store built on a URL read through a key path bound
    to a name first passed, since only a key path written at the application was read. # covers D-214, REQ-GAP-001"""
    line = _marked_in("FrontDoor.swift", "return GapRegisterStore(url: held[keyPath: path])")
    assert [found for found in gate.problems(gate.references(FLOW_AST))
            if found.startswith(f"FrontDoor.swift:{line}:") and "a key path not written in place" in found]


def test_242_a_computed_property_named_like_a_permitted_function_does_not_inherit_its_permission() -> None:
    """#242, the security review's round 2, R5: since `_placed` names a computed property as a place, a property named
    `priceInPages` was read as REQ-CMP-002's permitted function and skipped `_meets`. A ruling's permission is read by
    the function alone. Watched failing: the gate at `b93470f` refuses nothing on this line. # covers D-214"""
    line = _marked_in("Router.swift", "// shape: property-named-like-a-ruling")
    assert [found for found in gate.problems(gate.references(FLOW_AST)) if found.startswith(f"Router.swift:{line}:")]



#: #373 (G-2): a served number reached through a key path walked from its struct, and a method of a served number called
#: curried on its type: each shape marked in `Arithmetic.swift`, its function, and the declaration it meets.
STRUCT_WALKED_TWINS = [
    ("struct-keypath", "shapeStructKeyPath", "Swift.Int.magnitude"),
    ("struct-map-magnitude", "shapeStructMapMagnitude", "Swift.Int.magnitude"),
    ("struct-map-words", "shapeStructMapWords", "Swift.Int.words"),
    ("curried-advanced", "shapeCurriedAdvanced", "Swift.Int.advanced(by:"),
    ("curried-signum", "shapeCurriedSignum", "Swift.Int.signum("),
]


@pytest.mark.parametrize(("shape", "function", "declared"), STRUCT_WALKED_TWINS)
def test_373_a_served_number_reached_by_a_key_path_from_its_struct_or_a_curried_call_is_refused(
        shape: str, function: str, declared: str) -> None:
    """#373 (G-2, INV-76): `s[keyPath: \\Standing.position.magnitude]`, `[s].map(\\.position.magnitude)`,
    `[s].map(\\.position.words.count)`, `Int.advanced(by:)(s.position)(1)` and `Int.signum(s.position)()` passed in
    all four configurations: a key path's members were read only when the value it is applied to is itself a number,
    and a method called curried on its type was not read at all. Each is refused on its own line as its receiver's
    meeting, and the self-test asks the same of all four configurations. # covers D-214, D-181"""
    line = _marked(f"// shape: {shape}")
    phrase = f"`{declared}` on a served position (its receiver) in `{function}`"
    refused = [found for found in gate.problems(gate.references(FLOW_AST))
               if found.startswith(f"Arithmetic.swift:{line}:") and phrase in found]
    assert refused, f"{shape} (Arithmetic.swift:{line}) is not refused as {phrase}"
    assert ("Arithmetic.swift", phrase) in gate.FIXTURE_REFUSALS, f"the self-test does not hold {shape}"


@pytest.mark.parametrize(("text", "declared"), [
    ("GapRegisterStore(url: table[0])", "FixtureAddressTable.subscript(_:)"),
    ("GapRegisterStore(url: wrapped.address)", "FixtureAddressWrapper.subscript(dynamicMember:)"),
])
def test_374_a_store_receives_a_url_through_another_files_subscript_or_dynamic_member(text: str, declared: str) -> None:
    """#374 (G-13): `_store_received` read a direct reference, a member read and a key path, not a subscript, so the
    register's store built on a URL another file's type hands out through a subscript (`table[0]`) or a
    `@dynamicMemberLookup` wrapper (`wrapped.address`) passed in all four configurations. Each is refused as received,
    and the self-test asks the same of all four configurations. # covers D-214, REQ-GAP-001"""
    line = _marked_in("FrontDoor.swift", text)
    phrase = f"receives a URL, by `{declared}`, declared in ContentView.swift"
    assert [found for found in gate.problems(gate.references(FLOW_AST))
            if found.startswith(f"FrontDoor.swift:{line}:") and phrase in found], f"FrontDoor.swift:{line} is not refused"
    assert ("FrontDoor.swift", phrase) in gate.FIXTURE_REFUSALS, f"the self-test does not hold {text}"


def _made_on_the_dump() -> list[str]:
    found = gate.references(FLOW_AST)
    return gate.problems(found) + gate.release_problems(found)


def test_375_a_fixture_line_moved_by_an_insertion_keeps_the_pin(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """#375 (D-214): the pin compared each refusal's exact text, its line number included, so a line inserted above a
    pinned shape broke the pin for no real loss, which invites regenerating it, the one move that can hide a
    loosening. A pinned refusal is keyed by its file, its planted line and its text: here every line of
    `Arithmetic.swift` moves down one, the same refusals are made on the moved lines, and the pin holds in every
    configuration. Watched failing: at `fcc8f3e` each shifted refusal is reported gone. # covers D-214"""
    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()
    for source in gate.FIXTURES.glob("*.swift"):
        text = source.read_text(encoding="utf-8")  # raw: the gate's own fixture, copied whole as the compiler reads it
        (fixtures / source.name).write_text(("// #375: one line inserted\n" + text) if source.name == "Arithmetic.swift"
                                            else text, encoding="utf-8")
    monkeypatch.setattr(gate, "FIXTURES", fixtures)
    moved = [re.sub(r"^Arithmetic\.swift:(\d+):", lambda m: f"Arithmetic.swift:{int(m.group(1)) + 1}:", line)
             for line in _made_on_the_dump()]
    assert moved != _made_on_the_dump()
    for label, _, _ in gate.CONFIGURATIONS:
        assert gate._pin_broken(label, moved) == [], label


def test_375_a_pinned_refusal_removed_or_reworded_fails_the_pin(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """#375 (D-214): keyed by its planted line rather than its line number, the pin stays at least as strict. A pinned
    refusal no longer made, or made in other words, is reported gone; and the pin itself, with a line removed, with a
    line reworded into another refusal the fixture still makes, or regenerated in another order, fails in every
    configuration, since every refusal pinned before #242 must still be there as it was. The count test caught a
    deleted line, never an edited one. Watched failing: at `fcc8f3e` the edited pins pass. # covers D-214"""
    made = _made_on_the_dump()
    label = gate.CONFIGURATIONS[0][0]
    assert gate._pin_broken(label, made) == []
    first = next(line for line in made if line.startswith("Arithmetic.swift:103: `+` on a served position"))
    assert gate._pin_broken(label, [line for line in made if line != first]), "a pinned refusal removed passed"
    reworded = [line.replace("a served position", "a served place") if line == first else line for line in made]
    assert gate._pin_broken(label, reworded), "a pinned refusal reworded passed"
    pinned = gate.PINNED_REFUSALS.read_text(encoding="utf-8").splitlines()
    for name, lines in (("removed.txt", pinned[1:]), ("duplicated.txt", [pinned[1], *pinned[1:]]),
                        ("regenerated.txt", sorted(pinned, reverse=True))):
        pin = tmp_path / name
        pin.write_text("\n".join(lines) + "\n", encoding="utf-8")
        monkeypatch.setattr(gate, "PINNED_REFUSALS", pin)
        for each, _, _ in gate.CONFIGURATIONS:
            assert gate._pin_broken(each, made), (name, each)


# --- #371 (D-218 clause 4, G-2) ----------------------------------------------------------------------------------------

#: #371: a served number handed to a generic of the app's own over a numeric protocol, each shape marked in
#: `Arithmetic.swift`, and the protocol its refusal names.
NUMERIC_GENERIC_TWINS = [
    ("generic-numeric", "Numeric"), ("generic-where", "BinaryInteger"), ("generic-own-protocol", "ShapeBumpable"),
    ("generic-some", "BinaryInteger"), ("generic-any", "Numeric"), ("generic-type", "Numeric"),
    ("generic-method", "FixedWidthInteger"),
]


@pytest.mark.parametrize(("shape", "protocol"), NUMERIC_GENERIC_TWINS)
def test_371_a_served_number_handed_to_a_numeric_generic_of_the_apps_own_is_refused(shape: str, protocol: str) -> None:
    """#371 (D-218 clause 4, G-2, INV-76): `func f<T: Numeric>(_ x: T) -> T { x + x }` called with `s.position` passed in
    all four configurations: the operand's type is `T`, which no number type the rules read names. The ruling refuses a
    served number handed to a generic parameter constrained to a numeric protocol: directly, by a `where` clause,
    through a protocol of the app's own that refines one, as `some` and as `any` of one, into a generic type and into a
    generic method. Each is refused on its own line, and the self-test asks the same of all four configurations.
    # covers D-218, D-181"""
    line = _marked(f"// shape: {shape}")
    phrase = f"over the numeric protocol `{protocol}`"
    refused = [found for found in gate.problems(gate.references(FLOW_AST))
               if found.startswith(f"Arithmetic.swift:{line}:") and phrase in found]
    assert refused, f"{shape} (Arithmetic.swift:{line}) is not refused as {phrase}"
    assert ("Arithmetic.swift", "over the numeric protocol") in gate.FIXTURE_REFUSALS, "the self-test does not hold it"


#: #371: a served number rebuilt inside a closure that counts or searches, each shape marked in `Arithmetic.swift`: one
#: for each method D-218 clause 4 names, then a test by `if`, by `contains(_:)` and by a function of the app's own
#: inside one, a predicate handed by name and one held in a constant, and two meetings in one closure.
REBUILT_TWINS = [
    ("rebuilt-filter", "filter", "Swift.Int.<="), ("rebuilt-first", "first(where:)", "Swift.Int.=="),
    ("rebuilt-first-index", "firstIndex(where:)", "Swift.Int.=="), ("rebuilt-last-index", "lastIndex(where:)", "Swift.Int.=="),
    ("rebuilt-last", "last(where:)", "Swift.Int.=="), ("rebuilt-count-where", "count(where:)", "Swift.Int.<="),
    ("rebuilt-contains", "contains(where:)", "Swift.Int.=="), ("rebuilt-all-satisfy", "allSatisfy", "Swift.Int.!="),
    ("rebuilt-drop-while", "drop(while:)", "Swift.Int.<"), ("rebuilt-prefix-while", "prefix(while:)", "Swift.Int.<="),
    ("rebuilt-reduce", "reduce", "Swift.Int.<="), ("rebuilt-in-if", "filter", "Swift.Int.<="),
    ("rebuilt-by-contains", "filter", "Swift.Sequence.contains"), ("rebuilt-by-helper", "filter", "main.shapeAtMost"),
    ("rebuilt-by-name", "filter", "Swift.Int.<="), ("rebuilt-held", "filter", "Swift.Int.<="),
    ("rebuilt-twice", "filter", "Swift.Int.<="),
]


@pytest.mark.parametrize(("shape", "method", "declared"), REBUILT_TWINS)
def test_371_a_served_number_met_inside_a_closure_that_counts_or_searches_is_refused(
        shape: str, method: str, declared: str) -> None:
    """#371 (D-218 clause 4, G-2, INV-76): `(1...100).filter { $0 <= s.position }.count + 1` and `(0..<100).first { $0 ==
    s.position }` passed in all four configurations: a comparison is admitted by rule, and the count is a fresh number.
    The ruling refuses a comparison with a served number inside the closures given to `filter`, `first`, `firstIndex`,
    `lastIndex`, `last`, `count(where:)`, `contains(where:)`, `allSatisfy`, `drop(while:)`, `prefix(while:)` and
    `reduce`; in such a closure, written in place or handed by name, a served number meets nothing, an `if`, a
    `contains(_:)` or a function of the app's own included. Each is refused on its own line, and the self-test asks the
    same of all four configurations. # covers D-218, D-181"""
    line = _marked(f"// shape: {shape}")
    phrase = f"`{declared}` meets a served position inside the closure given to `{method}`"
    refused = [found for found in gate.problems(gate.references(FLOW_AST))
               if found.startswith(f"Arithmetic.swift:{line}:") and phrase in found]
    assert refused, f"{shape} (Arithmetic.swift:{line}) is not refused as {phrase}"
    assert ("Arithmetic.swift", "which counts or searches") in gate.FIXTURE_REFUSALS, "the self-test does not hold it"


@pytest.mark.parametrize("mark", ["compared-in-if", "compared-in-map", "compared-in-sort", "compared-in-max"])
def test_371_a_comparison_in_if_a_map_a_sort_or_max_by_stays_admitted(mark: str) -> None:
    """#371 (D-218 clause 4): a comparison with a served number in `if`, in a closure that neither counts nor searches
    (`map`), in a sort and in `max(by:)` stays admitted, so the rule is no wider than the ruling. A sort is still counted
    per file by `SORTS_PERMITTED`, on no line. # covers D-218"""
    line = _marked(f"// allowed: {mark}")
    assert not [found for found in gate.problems(gate.references(FLOW_AST)) if found.startswith(f"Arithmetic.swift:{line}:")]


def test_371_a_meeting_inside_a_count_or_a_search_is_admitted_only_where_listed_and_counted(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """#371 (D-218 clause 4): the shipping client's own counts and searches over a served number (the staleness notice's
    ages, whether a source is dated) are admitted by place, counted, each with its reason; a place that makes one more
    meeting than its entry counts is refused, and an entry the client no longer makes fails the gate, as a stale
    permission does (the W2 review's R3). # covers D-218"""
    line = _marked("// shape: rebuilt-twice")
    key = ("Arithmetic.swift", "shapeRebuiltTwice", "filter", "position", "Swift.Int.<=")

    def made() -> tuple[dict[str, set[str]], list[str]]:
        found = gate.references(FLOW_AST)
        return found, [fact for fact in gate.problems(found) if fact.startswith(f"Arithmetic.swift:{line}:")]

    monkeypatch.setitem(gate.COUNTS_OR_SEARCHES_PERMITTED, key, (1, "one of the two meetings"))
    _, refused = made()
    assert refused and all("1 such meeting(s) are permitted there" in fact for fact in refused), refused
    monkeypatch.setitem(gate.COUNTS_OR_SEARCHES_PERMITTED, key, (2, "both meetings"))
    found, refused = made()
    assert not refused, refused
    listed = "main.<counts listed>.Swift.Int.<=|filter|position|shapeRebuiltTwice"
    assert listed in found["Arithmetic.swift"]
    assert not [entry for entry in gate.unseen_permissions(found) if "shapeRebuiltTwice" in entry]
    found["Arithmetic.swift"].discard(listed)
    assert [entry for entry in gate.unseen_permissions(found) if "`shapeRebuiltTwice`" in entry]
    shipping = [entry for entry in gate.COUNTS_OR_SEARCHES_PERMITTED if entry != key]
    assert len(shipping) == 6, shipping
    unseen = gate.unseen_permissions({})
    for file, where, method, _, declared in shipping:
        assert [entry for entry in unseen if entry.startswith(f"{file}: `{declared}` inside `{method}` in `{where}`")], where
