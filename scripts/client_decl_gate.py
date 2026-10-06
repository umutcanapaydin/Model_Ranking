"""D-126 checked against what the COMPILER resolves, not against how the source spells it (W-122).

Six rounds of a word list over `ios/ModelRanking` each closed the spellings somebody had thought
of, and each independent seat found more: backticks (`` `URL`(string:) ``), a comment between two
tokens (`URL/**/(`), a `typealias`, `NSMutableURLRequest`, a markdown link, Handoff. A gate over
text cannot see through any of those, because the text is not what compiles.

This gate type-checks the client with the iOS SDK and reads the DECLARATIONS the compiler bound
each reference to. `` `URL`(string:) ``, `Address(string:)` after a typealias and `URL(string:)`
all resolve to `Foundation.(file).URL.init(string:)`, so all three are one entry here.

**Two rules, in this order.**

1. **Module allowlist.** A client file may reference declarations only from the modules below, plus
   the app's own. `Network`, `WebKit`, `CloudKit`, `Photos`, `Contacts` and everything else are
   refused by absence, so an API nobody has thought of yet is refused too. `UIKit` and
   `CoreFoundation` are allowlisted SYMBOL by symbol: both arrive through a re-export, and
   `CoreFoundation` whole carries sockets.
2. **Capability rules inside the allowed modules.** Foundation and SwiftUI carry the ways text
   leaves a phone, so those are named: the network is EngineClient's alone, the file system is the
   gap register's alone, and sharing, hand-off, shared storage and logging belong to nobody.

The text gate in `tests/unit/test_router_hints.py` stays: it runs in every lane, including the ones
with no Xcode, and this one runs where the toolchain is. Neither is the whole check.

**What this gate does NOT do** (M16-W1 review, measured):

- It scopes by FILE, not by data, with one exception. A function declared in `EngineClient.swift`
  resolves in `main`, and `main` is not capability-checked, so a relay there that any file can call
  passes (B19); the file system is whole inside `FrontDoor.swift`, so a write to the temporary
  directory from there passes too (B31). What a file does with a capability it owns is for review
  and the tests. The exception is the two privacy sinks (#85, D-180): neither may hold or read
  mutable state another file can set, and only they build standings, so a relay through shared
  state or standings made on the screen is refused (`SINK_FILES`, `PROVENANCE`).
- It does not see arguments, and some of the check lives in the text gate for that reason:
  `Text("[report](https://…)")` is a `LocalizedStringKey` literal, not an `AttributedString`, so a
  markdown link written as a literal passes here and dies there (B10); a key built at run time is
  refused here instead. `try!` on an error that carries the reader's words puts them in the crash
  report, and has no declaration for either gate to refuse (re-review, X06).
- `.textSelection(.enabled)` is allowed: the detail screen uses it on model facts, and what it
  hands the pasteboard is what the reader chose to copy (B22).
- One known false positive: `URL.appending…` is file-scoped, so building a path to a bundle
  resource outside the two owning files fails (FP3). `Bundle.main.url(forResource:withExtension:)`
  builds no path and passes.
"""

from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import sys
from collections.abc import Iterator

ROOT = pathlib.Path(__file__).resolve().parents[1]
CLIENT = ROOT / "ios" / "ModelRanking"
#: Every configuration the app ships in. One was not enough: the M16-W1 seat put a `URLSession`
#: exfiltration inside `#if !targetEnvironment(simulator)` and inside `#if DEBUG`, and a gate that
#: type-checks the simulator Release build never saw either branch. Each configuration is dumped
#: and every one must be clean.
CONFIGURATIONS = (
    ("simulator, release", "iphonesimulator", ["-target", "arm64-apple-ios18.0-simulator"]),
    ("simulator, debug", "iphonesimulator",
     ["-target", "arm64-apple-ios18.0-simulator", "-D", "DEBUG"]),
    ("device, release", "iphoneos", ["-target", "arm64-apple-ios18.0"]),
    ("device, debug", "iphoneos", ["-target", "arm64-apple-ios18.0", "-D", "DEBUG"]),
)

#: Modules a client file may resolve a declaration in. `main` is the app's own module.
MODULES = {
    "main",
    "Swift",
    "SwiftUI",
    "SwiftUICore",
    "Foundation",
    "NaturalLanguage",
    "FoundationModels",
    "_Concurrency",
    "ObjectiveC",
    "Observation",
    "Combine",
    "_DarwinFoundation1",  # `pow`, through Foundation's re-export
}
# `Darwin` is NOT here, deliberately (M16-W1 review, B-3): it carries BSD sockets, `getaddrinfo`
# and `dlopen`, so allowlisting the module handed every client file its own way onto the network.
# Measured on the shipping client: the only declaration it resolves in that family is
# `_DarwinFoundation1.pow`, so the removal costs nothing.

#: UIKit arrives through SwiftUI's re-export, so it is allowed one symbol at a time: these are the
#: colour and trait types the design layer reads. `UIPasteboard`, `UIApplication`,
#: `UIActivityViewController`, `UIPrintInteractionController` and `UIDocumentPickerViewController`
#: are all UIKit, and all refused by not being here.
UIKIT_ALLOWED = {"UIColor", "UITraitCollection", "UIUserInterfaceStyle", "UIFont", "UIScreen"}

#: CoreFoundation is allowed the same way, and for B-3's reason: allowlisted whole it handed every
#: client file a TCP socket (`CFSocketCreate` / `CFSocketConnectToAddress` / `CFSocketSendData`,
#: measured delivering the typed text to a listener), Darwin notifications and `CFShow` (M16-W1
#: re-review, R-B1, B11, X14). The shipping client resolves nothing there but `CGFloat`.
COREFOUNDATION_ALLOWED = {"CGFloat"}

#: Declarations that reach the network, or build an address that could. A `URL` MADE FROM A STRING
#: is the network's first step; a `URL` that names a file on this device is the file system's, and
#: the two are told apart here by which initialiser the compiler chose.
NETWORK = ("URLSession", "URLRequest", "URLComponents", "URLQueryItem", "NSURL", "CFURL",
           "NSMutableURLRequest", "NSURLRequest", "NSURLSession", "NSURLConnection",
           "URL.init(string", "URL.init(dataRepresentation", "URL.lines", "URL.resourceBytes",
           # A socket pair to a host. It lived under `Stream` in the file-system list, which gave
           # it to the register's file (M16-W1 re-review, X02).
           "Stream.getStreamsToHost",
           # #58: a URL made by DECODING is neither a spelling nor an initialiser; `references`
           # records it under this name, from the decode's own type substitution.
           "URL.decoded",
           # #107: a link detector finds URLs in text; and any CALL whose result is a URL, whatever
           # it is called (`URL(_:strategy:)`, a decode wrapper in another file), is recorded under
           # `URL.made` by `url_facts`.
           "NSDataDetector", "NSTextCheckingResult.url", "URL.made")
NETWORK_FILE = "EngineClient.swift"

#: Declarations that touch the file system, including the local-file half of `URL`. Only the files in
#: `FILESYSTEM_FILES` may name them: the two things this app writes.
FILESYSTEM = ("FileManager", "FileHandle", "Data.init(contentsOf", "Data.write", "String.write",
              "StringProtocol.write(toFile", "String.write(toFile", "write(to:",
              "URL.init(fileURLWithPath", "URL.init(filePath",
              "URL.deleting", "URL.setResourceValues", "URL.resourceValues", "URLResourceValues",
              # The Objective-C twins and the stream APIs write a file just as well, and the first
              # version of this list named only the Swift spellings (M16-W1 review, B04/B05/B28).
              "NSString.write", "NSData.write", "NSArray.write", "NSDictionary.write",
              "OutputStream", "InputStream.init(fileAtPath", "InputStream.init(url",
              "NSTemporaryDirectory", "StringProtocol.write(to", "FileWrapper",
              "URL.init(fileURLWithFileSystemRepresentation")
#: Each file allowed the file system, with what it keeps and the ruling that allows it. The gap
#: register (REQ-GAP-001) and, since M17-W4, the standings the engine sent (D-167 clause 4).
FILESYSTEM_FILES = {
    "FrontDoor.swift": "the gap register (REQ-GAP-001)",
    "StandingsStore.swift": "the standings the engine sent (D-167)",
}

#: Appending a path component builds a route inside a URL that already exists, so it belongs to
#: whoever owns that URL: the register's folder in one file, the engine's request path in the other.
#: It cannot turn a local URL into a remote one, which is what the two lists above are about.
PATH_BUILDING = ("URL.appending",)

#: Declarations that carry text off the device or into storage nothing else can see, whoever names
#: them. Matched as a prefix of the symbol path inside its module.
FORBIDDEN = (
    "UserDefaults",
    "NetService",
    # A markdown link renders as a tappable link, so the reader's words leave through the browser
    # with no URL type anywhere in the source (M15-W4 re-review, BLOCKING-1).
    "AttributedString",
    "View.draggable",
    "View.userActivity",
    "View.fileExporter",
    "View.fileMover",
    "View.onDrag",
    "View.shareable",
    "View.exportsItemProviders",
    "View.dropDestination",
    "NSUbiquitousKeyValueStore",
    "NSUserActivity",
    "UIActivityViewController",
    "UIPasteboard",
    "UIApplication",
    "UIPrintInteractionController",
    "UIDocumentPickerViewController",
    "ShareLink",
    "AsyncImage",
    "Link",
    "OpenURLAction",
    "EnvironmentValues.openURL",
    # State restoration writes a scene's storage to disk, so `@SceneStorage` holding what a reader
    # typed is a second store beside the register (M16-W1 review, B23). The client uses none.
    "SceneStorage",
    # An App Group container is shared with other apps and extensions, so not even the register
    # may write there (B08).
    "FileManager.containerURL",
    # iCloud Drive (M16-W1 re-review, X09).
    "FileManager.url(forUbiquityContainerIdentifier",
    # A markdown link built at RUN time: the literal form is checked by the text gate, but a key
    # made from a runtime string is not a literal, and neither gate saw it (re-review, R-M1). The
    # client builds its keys only by interpolation.
    "LocalizedStringKey.init(_:",
    "LocalizedStringKey.init(stringLiteral",
    # Credentials with `.synchronizable` go to iCloud Keychain, and cookies to a store the system
    # writes to disk; refused for the reason `SecItemAdd` and `UserDefaults` are (re-review, R-M2).
    "URLCredentialStorage",
    "URLCredential",
    "URLProtectionSpace",
    "HTTPCookieStorage",
    "HTTPCookie",
    # A crash message lands in the crash report, which leaves the phone. This gate sees the call,
    # not the argument, so it cannot tell `fatalError("\(typed)")` (B09) from a constant one; the
    # client calls none of these, so all of them are refused. The text gate also refuses
    # interpolation into them (W-121).
    "fatalError",
    "precondition",
    "assert",
    "NSException",
    "print",
    "debugPrint",
    "dump",
    "NSLog",
    "Logger",
    "OSLog",
    "SecItemAdd",
    "CFPreferences",
    "NSKeyedArchiver",
)

#: #85 (D-180): the two privacy sinks. Each sends or keeps only what its parameters, its immutable
#: configuration and the engine's answer give it, so nothing derived from the question can reach
#: them through state another file sets. The file scope above cannot see that (the M17 closure's P2).
SINK_FILES = {
    "EngineClient.swift": "every request to the engine, the boards request among them (INV-66)",
    "StandingsStore.swift": "the standings file on this device (INV-66)",
}
#: Declarations only the listed files may call. Standings come from the engine's answer or the
#: store's own file, never from what the screen builds (the M17 closure's P3).
PROVENANCE = {"FetchedStandings.init(payload:)": {"EngineClient.swift", "StandingsStore.swift"}}

#: #60 (G-2): the numbers the engine sends, by the field `Models.swift` decodes each into, and what
#: each one is. Arithmetic on one, reached directly or through any local, parameter or loop element
#: it flowed into, is a second scoring implementation unless a ruling names the file (REQ-APP-005).
SERVED_NUMBERS = {
    "score": "score", "secondaryScore": "score", "higherEffortScore": "score", "position": "position",
    "blendedPerM": "price", "inputPerM": "price", "outputPerM": "price",
    "eligibleCount": "count", "frontierSize": "count",
}
#: (file, what) -> the ruling that lets that file do arithmetic on it.
ARITHMETIC_PERMITTED = {
    ("Uncertainty.swift", "score"): "D-138: a rank range compares served scores against the engine's margin",
    ("Combine.swift", "position"): "D-167: the combination ranks served positions",
    ("Router.swift", "price"): "REQ-CMP-002: the price in pages, beside the exact figure",
    ("Language.swift", "price"): "REQ-CMP-002: the price in pages, in its Turkish sentence",
}
#: (file, call, the receiver the compiler resolved) -> how many such sorts the file may make (Ruling
#: A, REQ-APP-002). Counted, so a second sort under a permitted name fails (the M17-W4 Tester's M7).
SORTS_PERMITTED = {
    ("Combine.swift", "sorted", "common"): 1,
    ("Combine.swift", "sorted", "placed"): 1,
    ("FrontDoor.swift", "sorted", "entries"): 1,
    ("FrontDoor.swift", "min", "entries"): 1,
    ("Notices.swift", "sorted", "ages"): 1,
    ("Notices.swift", "sorted", "distinct"): 1,
    ("Reading.swift", "reversed", "row"): 1,
}

#: (file, symbol) a forbidden family's member is allowed as, each with its reason. Exact, never a
#: prefix: the family stays refused everywhere else.
FORBIDDEN_EXCEPT = {
    ("EngineClient.swift", "HTTPCookie.AcceptPolicy.never"): "#144: the session refuses every cookie",
}

#: `@AppStorage("language")` is the one piece of app storage the client keeps, and it holds a
#: `Language`, never text a reader typed. The text gate pins its declaration; here the SwiftUI
#: property wrapper itself is allowed only in the file that declares it.
APPSTORAGE_FILE = "ContentView.swift"

#: `decl="Module.(file).Symbol"`. A member declared in an extension prints as
#: `Module.(file).Type extension.member`, with a SPACE, which hid `.draggable` and
#: `String.write(toFile:)` from the first version of this gate: the space ended the match.
DECL = re.compile(r'decl="?([A-Za-z_][\w]*)\.\(file\)\.((?:[\w.]+ extension\.)?[^ )"@]*)')
IMPORT = re.compile(r'\(import_decl[^)]*module="([^"]+)"')
#: #58: a `decode` whose generic substitution produces a `URL` (`JSONDecoder.decode([URL].self, ...)`,
#: or a container's `decode(URL.self, forKey:)` inside a synthesised `Decodable`). The substitution
#: is printed after the declaration's path, which `DECL` stops before.
DECODES_URL = re.compile(r'decl="[^"]*\.decode(?:IfPresent)?\([^"]*\[with \(substitution_map[^"]*->[^"]*\bURL\b')
#: The fixture `self_test` compiles: files the gate must refuse and files it must allow (#51).
FIXTURES = ROOT / "scripts" / "client_decl_fixtures"
#: What the fixture must produce, as (file, a phrase the refusal carries).
FIXTURE_REFUSALS = {
    ("ContentView.swift", "URLSession"), ("ContentView.swift", "URL.decoded"),
    ("Detail.swift", "FileManager"), ("Detail.swift", "URL.decoded"),
    # #85 (D-180): the M17 relay through shared state, both halves, and P3's standings.
    ("EngineClient.swift", "mutable stored state"),
    ("EngineClient.swift", "mutable state declared in ContentView.swift"),
    ("ContentView.swift", "builds FetchedStandings"),
    # #60 (G-2): arithmetic on a served position through another name, and a second sort under a
    # permitted receiver's name.
    ("ContentView.swift", "served position"),
    ("Combine.swift", "sorts `common`"),
    # #107: a URL made by the parse strategy, by a decode wrapper and by a link detector.
    ("ContentView.swift", "makes a URL"),
    ("ContentView.swift", "NSDataDetector"), ("ContentView.swift", "NSTextCheckingResult.url"),
}
SOURCE = re.compile(r'^\(source_file "([^"]+)"', re.MULTILINE)
#: One node of the dump: its indentation (the tree's depth) and its kind.
NODE = re.compile(r"^( *)\((\w+)")
VAR_NAME = re.compile(r'^ *\(var_decl [^"]*"([^"]+)"')
RANGE_START = re.compile(r"range=\[([^\]:]+):(\d+):(\d+)")
#: A reference into the app's own module, with the place its declaration starts.
MAIN_REF = re.compile(r'decl="main\.\(file\)\.([^"@]+)@([^":]+):(\d+):(\d+)"')
#: The scopes a declaration can live in: shared (a type or the file) or a body's own (a local).
#: #60: a node with an optional label (`processed_init=binary_expr`); an `original_init` subtree is the
#: unresolved copy of a binding's expression, so it is skipped.
LABELLED_NODE = re.compile(r"^( *)\((?:(\w+)=)?(\w+)")
SERVED_REF = re.compile(r'decl="main\.\(file\)\.\w+\.(\w+)@[^"]*/Models\.swift:')
NUMERIC_OPERATOR = re.compile(
    r'decl="Swift\.\(file\)\.(?:Int|Int64|UInt|Double|Float|CGFloat|BinaryInteger|BinaryFloatingPoint|'
    r'FloatingPoint|Numeric|AdditiveArithmetic|SignedNumeric|SignedInteger) extension\.([-+*/%]=?)"')
ORDERING_CALL = re.compile(r'decl="Swift\.\(file\)\.\w+ extension\.(sorted|sort|max|min|reversed|shuffled|swapAt)\(([^)]*)\)')
LOCAL_VAR = re.compile(r'^ *\(var_decl [^\[]*range=\[([^\]:]+):(\d+):(\d+)')
PATTERN_NAME = re.compile(r'^ *\(pattern_named [^"]*"([^"]+)"')
PARAMETER = re.compile(r'^ *\(parameter "([^"]+)"')
FUNCTION = re.compile(r'^ *\(func_decl [^\[]*range=\[[^\]:]+:(\d+):\d+[^"]*"(\w+)')
CALLEE = re.compile(r'decl="main\.\(file\)\.(?:[\w.]+\.)?(\w+)(?:\([^)"]*\))?@([^":]+):(\d+):\d+" function_ref=single apply')
LOCATION_LINE = re.compile(r"location=[^ ]*?(\w+\.swift):(\d+)")
SHARED_SCOPES = {"source_file", "struct_decl", "class_decl", "enum_decl", "extension_decl",
                 "protocol_decl", "actor_decl"}
LOCAL_SCOPES = {"func_decl", "constructor_decl", "destructor_decl", "accessor_decl", "closure_expr"}


def dump_ast(sdk_name: str, flags: list[str], folder: pathlib.Path = CLIENT) -> tuple[str, int] | None:
    """`(AST, exit code)` for one configuration, or None where there is no toolchain."""
    xcrun = shutil.which("xcrun")
    if xcrun is None:
        return None
    try:
        # S603: the executable is resolved from PATH above and every argument is a literal or a
        # path inside this repository; nothing here comes from outside the tree.
        sdk = subprocess.run(  # noqa: S603
            [xcrun, "--sdk", sdk_name, "--show-sdk-path"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    sources = sorted(str(path) for path in folder.rglob("*.swift"))
    result = subprocess.run(  # noqa: S603
        [xcrun, "swiftc", "-typecheck", "-dump-ast", *flags, "-sdk", sdk, *sources],
        capture_output=True, text=True, cwd=ROOT,
    )
    # `-dump-ast` writes the tree to stderr and type errors land there too. A type error STOPS the
    # dump, so every later file silently leaves the check -- the M16-W1 seat shipped a pasteboard
    # write that way and this gate said PASS on 8 of 11 files. The exit code comes back with the
    # tree and `main` refuses anything but 0.
    return result.stderr, result.returncode


def references(ast: str) -> dict[str, set[str]]:
    """`{file name: {"Module.symbol", ...}}` for every declaration the compiler resolved."""
    marks = [(m.start(), pathlib.Path(m.group(1)).name) for m in SOURCE.finditer(ast)]
    found: dict[str, set[str]] = {name: set() for _, name in marks}
    for index, (start, name) in enumerate(marks):
        end = marks[index + 1][0] if index + 1 < len(marks) else len(ast)
        # `import \`Network\`` and `import/**/WebKit` are one thing to the compiler, and this is
        # where the compiler says so. An import of a module nothing uses still fails the gate: the
        # point of the allowlist is that reaching the framework at all is a reviewed change.
        for module in IMPORT.findall(ast[start:end]):
            found[name].add(f"{module}.<imported>")
        if DECODES_URL.search(ast[start:end]):
            found[name].add("Foundation.URL.decoded")
        for module, symbol in DECL.findall(ast[start:end]):
            # A member added in an extension prints as `Module.(file).extension.name`, which hid
            # `.draggable` and `String.write(toFile:)` from the first version of this gate.
            symbol = re.sub(r"([\w.]+) extension\.", r"\1.", symbol)
            symbol = re.sub(r"(^|\.)extension\.", r"\1", symbol)
            found[name].add(f"{module}.{symbol.rstrip('.')}")
    for name, facts in (*sink_facts(ast).items(), *flow_facts(ast).items(), *url_facts(ast).items()):
        found.setdefault(name, set()).update(facts)
    return found


def _shared_state(ast: str) -> tuple[dict[tuple[str, int, int], str], list[tuple[str, str, tuple[str, int, int]]]]:
    """Every `var` the client shares, by where its declaration starts, and every reference into the
    app's own module, as `(file, symbol, where its declaration starts)`.

    Shared state is a `var` whose storage the compiler marks `writeImpl=stored`, declared in a type or
    at file scope: a `let`, a computed property and a function's local are not shared.
    """
    shared: dict[tuple[str, int, int], str] = {}
    refs: list[tuple[str, str, tuple[str, int, int]]] = []
    stack: list[tuple[int, str]] = []
    current = ""
    for line in ast.splitlines():
        node = NODE.match(line)
        if node:
            depth, kind = len(node.group(1)), node.group(2)
            while stack and stack[-1][0] >= depth:
                stack.pop()
            if kind == "source_file":
                current = pathlib.Path(line.split('"')[1]).name
            elif kind == "var_decl" and "writeImpl=stored" in line:
                scope = next((k for _, k in reversed(stack) if k in SHARED_SCOPES | LOCAL_SCOPES), "source_file")
                start, named = RANGE_START.search(line), VAR_NAME.match(line)
                if scope in SHARED_SCOPES and start and named:
                    shared[(pathlib.Path(start.group(1)).name, int(start.group(2)), int(start.group(3)))] = named.group(1)
            stack.append((depth, kind))
        refs += [(current, symbol, (pathlib.Path(path).name, int(row), int(column)))
                 for symbol, path, row, column in MAIN_REF.findall(line)]
    return shared, refs


#: #107: a call, or a constructor's, whose result is a URL (`URL`, `URL?`, `[URL]`).
MAKES_URL = re.compile(r'^ *\((?:\w+=)?(?:call_expr|constructor_ref_call_expr) [^\n]*?\btype="(?:Foundation\.)?'
                       r'(?:URL\??|\[URL\]\??|Optional<URL>)"[^\n]*?location=[^ ]*?(\w+\.swift):(\d+)')


def url_facts(ast: str) -> dict[str, set[str]]:
    """#107: `{file name: {"Foundation.URL.made", ...}}` for every call that makes a URL, so the
    network rule judges it as it judges `URL.init(string:)`, whatever the call is named."""
    facts: dict[str, set[str]] = {}
    current = ""
    for line in ast.splitlines():
        if line.startswith("(source_file"):
            current = pathlib.Path(line.split('"')[1]).name
        elif MAKES_URL.match(line):
            facts.setdefault(current, set()).add("Foundation.URL.made")
    return facts


def sink_facts(ast: str) -> dict[str, set[str]]:
    """#85 (D-180): `{file name: {"main.<...>", ...}}`, the facts `problems` judges about the sinks: a
    sink's own shared state, its reads of another file's, and who calls a `PROVENANCE` declaration."""
    shared, refs = _shared_state(ast)
    facts: dict[str, set[str]] = {}
    for (file, _, _), name in shared.items():
        if file in SINK_FILES:
            facts.setdefault(file, set()).add(f"main.<mutable stored state>.{name}")
    for file, symbol, declared in refs:
        if file in SINK_FILES and declared in shared and declared[0] != file:
            facts.setdefault(file, set()).add(f"main.<reads mutable state>.{shared[declared]}@{declared[0]}")
        if symbol in PROVENANCE:
            facts.setdefault(file, set()).add(f"main.<builds>.{symbol}")
    return facts


class _Node:
    """One node of the dump: its depth, its kind, its first line, and its children."""

    __slots__ = ("depth", "kids", "kind", "line")

    def __init__(self, depth: int, kind: str, line: str) -> None:
        self.depth, self.kind, self.line = depth, kind, line
        self.kids: list[_Node] = []

    def walk(self) -> Iterator[_Node]:
        yield self
        for kid in self.kids:
            yield from kid.walk()


def _tree(ast: str) -> list[_Node]:
    """The dump as a tree, one root per source file, without the unresolved `original_init` copies."""
    roots: list[_Node] = []
    stack: list[_Node] = []
    skip: int | None = None
    for line in ast.splitlines():
        match = LABELLED_NODE.match(line)
        if not match:
            continue
        depth, label, kind = len(match.group(1)), match.group(2), match.group(3)
        if skip is not None and depth > skip:
            continue
        skip = depth if label == "original_init" else None
        if skip is not None:
            continue
        while stack and stack[-1].depth >= depth:
            stack.pop()
        node = _Node(depth, kind, line)
        (stack[-1].kids if stack else roots).append(node)
        stack.append(node)
    return roots


def _file_of(root: _Node) -> str:
    return pathlib.Path(root.line.split('"')[1]).name


#: What carries a served number: a declaration's start `(file, line, column)`, or `(file, name)` for
#: a parameter or a loop element, whose declarations print no place of their own.
_Carriers = dict[tuple[object, ...], set[str]]


def _carried(node: _Node, carriers: _Carriers) -> set[str]:
    """What served numbers an expression reaches: a served field, or anything they flowed into."""
    found: set[str] = set()
    for item in node.walk():
        if served := SERVED_REF.search(item.line):
            found.add(SERVED_NUMBERS.get(served.group(1), ""))
        for symbol, path, row, column in MAIN_REF.findall(item.line):
            file = pathlib.Path(path).name
            found |= carriers.get((file, int(row), int(column)), set())
            found |= carriers.get((file, symbol.split(".")[-1]), set())
    return found - {""}


def _mark(carriers: _Carriers, key: tuple[object, ...], kinds: set[str]) -> bool:
    if not kinds or kinds <= carriers.get(key, set()):
        return False
    carriers.setdefault(key, set()).update(kinds)
    return True


def _parameters(roots: list[_Node]) -> dict[tuple[str, str, int], list[str]]:
    """`(file, function name, line) -> its parameter names`, in order."""
    found: dict[tuple[str, str, int], list[str]] = {}
    for root in roots:
        for node in root.walk():
            if function := FUNCTION.match(node.line):
                listed = next((kid for kid in node.kids if kid.kind == "parameter_list"), None)
                names = [m.group(1) for kid in (listed.kids if listed else []) if (m := PARAMETER.match(kid.line))]
                found[(_file_of(root), function.group(2), int(function.group(1)))] = names
    return found


def _flow_once(node: _Node, file: str, carriers: _Carriers, parameters: dict[tuple[str, str, int], list[str]]) -> bool:
    """One step of the flow at one node: into a binding's locals, a loop's element, a call's parameters."""
    changed = False
    for index, kid in enumerate(node.kids):
        if kid.kind == "pattern_binding_decl" and (kinds := _carried(kid, carriers)):
            for sibling in node.kids[index + 1:]:
                if sibling.kind != "var_decl" or not (place := LOCAL_VAR.match(sibling.line)):
                    break
                changed |= _mark(carriers, (pathlib.Path(place.group(1)).name, int(place.group(2)), int(place.group(3))), kinds)
    if node.kind == "for_each_stmt":
        named = next((m for kid in node.kids if (m := PATTERN_NAME.match(kid.line))), None)
        sequence = next((kid for kid in node.kids if kid.kind in ("declref_expr", "member_ref_expr", "call_expr")), None)
        if named and sequence is not None:
            changed |= _mark(carriers, (file, named.group(1)), _carried(sequence, carriers))
    if node.kind == "call_expr" and len(node.kids) > 1 and (callee := CALLEE.search(node.kids[0].line)):
        target = pathlib.Path(callee.group(2)).name
        arguments = [kid for kid in node.kids[1].kids if kid.kind == "argument"]
        # Not strict: a parameter with a default takes no argument.
        names = parameters.get((target, callee.group(1), int(callee.group(3))), [])
        for name, argument in zip(names, arguments, strict=False):
            changed |= _mark(carriers, (target, name), _carried(argument, carriers))
    return changed


def flow_facts(ast: str) -> dict[str, set[str]]:
    """#60 (G-2): `{file name: {"main.<...>", ...}}`, the arithmetic on served numbers and the sorts
    each file makes, resolved by the compiler and followed to a fixed point, for `problems` to judge."""
    roots = _tree(ast)
    parameters = _parameters(roots)
    carriers: _Carriers = {}
    changed = True
    while changed:
        changed = False
        for root in roots:
            for node in root.walk():
                changed |= _flow_once(node, _file_of(root), carriers, parameters)
    facts: dict[str, set[str]] = {}
    sorts: dict[tuple[str, str, str], int] = {}
    for root in roots:
        file = _file_of(root)
        for node in root.walk():
            for fact in _arithmetic(node, carriers):
                facts.setdefault(file, set()).add(fact)
            if (ordering := _ordering(node)) is not None:
                sorts[(file, *ordering)] = sorts.get((file, *ordering), 0) + 1
    for (file, method, receiver), count in sorts.items():
        facts.setdefault(file, set()).add(f"main.<sorts>.{method}.{receiver}={count}")
    return facts


def _arithmetic(node: _Node, carriers: _Carriers) -> list[str]:
    """`main.<arithmetic>.<what>@<line> <operator>` for an arithmetic operator on a served number."""
    if node.kind != "binary_expr" or len(node.kids) < 2:
        return []
    operator = next((m for item in node.kids[0].walk() if (m := NUMERIC_OPERATOR.search(item.line))), None)
    if operator is None:
        return []
    place = LOCATION_LINE.search(node.line)
    line = place.group(2) if place else "?"
    return [f"main.<arithmetic>.{kind}@{line} {operator.group(1)}" for kind in sorted(_carried(node.kids[1], carriers))]


def _ordering(node: _Node) -> tuple[str, str] | None:
    """`(call, receiver)` for a sort, a reversal, a shuffle or a `max(by:)`/`min(by:)` on a resolved receiver."""
    if node.kind != "dot_syntax_call_expr" or len(node.kids) < 2:
        return None
    call = ORDERING_CALL.search(node.kids[0].line)
    if call is None or (call.group(1) in ("max", "min") and call.group(2) != "by:"):
        return None
    receiver = next((m for item in node.kids[1].walk() if (m := MAIN_REF.search(item.line))), None)
    return call.group(1), receiver.group(1).split(".")[-1] if receiver else "?"


def _flow_problem(name: str, symbol: str) -> str | None:
    """#60 (G-2): arithmetic on a served number outside its ruling's file, or a sort past its count."""
    fact, _, subject = symbol.partition(">.")
    if fact == "<arithmetic":
        what, _, where = subject.partition("@")
        if (name, what) in ARITHMETIC_PERMITTED:
            return None
        line, _, operator = where.partition(" ")
        return (f"{name}:{line}: `{operator}` on a served {what}, a second scoring implementation; only the "
                f"files a ruling names do arithmetic on one (REQ-APP-005; D-138, D-167, REQ-CMP-002)")
    if fact == "<sorts":
        call_receiver, _, count = subject.rpartition("=")
        call, _, receiver = call_receiver.partition(".")
        allowed = SORTS_PERMITTED.get((name, call, receiver), 0)
        if int(count) > allowed:
            return (f"{name}: sorts `{receiver}` with `{call}` {count} time(s), and {allowed} is permitted; the "
                    "client orders nothing itself but where a ruling says why (Ruling A, REQ-APP-002)")
    return None


def _sink_problem(name: str, symbol: str) -> str | None:
    """#85 (D-180): a sink's shared state, a sink reading another file's, standings built elsewhere."""
    fact, _, subject = symbol.partition(">.")
    if fact == "<mutable stored state":
        return (f"{name}: `{subject}` is mutable stored state in a privacy sink ({SINK_FILES[name]}); "
                "any file can set it, so it can relay the question (D-180)")
    if fact == "<reads mutable state":
        variable, _, declared = subject.partition("@")
        return (f"{name}: reads `{variable}`, mutable state declared in {declared}, so whatever sets it "
                f"reaches {SINK_FILES[name]} (D-180)")
    if fact == "<builds" and name not in PROVENANCE.get(subject, set()):
        return (f"{name}: builds {subject.split('.')[0]} (`{subject}`); only the engine's answer and "
                "the store's own file become standings (D-180)")
    return None


def _module_problem(name: str, module: str, symbol: str, decl: str) -> str | None:
    """The module allowlist, including `import` lines, and UIKit's per-symbol exception."""
    if symbol == "<imported>":
        if module not in MODULES | {"UIKit", "CoreFoundation"}:
            return (f"{name}: imports `{module}`, which is not on the client's module allowlist; "
                    "a new framework is a reviewed edit, not an import")
        return None
    if module == "UIKit":
        if symbol.split(".")[0] not in UIKIT_ALLOWED:
            return (f"{name}: UIKit.{symbol} is not one of the re-exported types the design layer "
                    f"may use ({', '.join(sorted(UIKIT_ALLOWED))})")
        return None
    if module == "CoreFoundation":
        if symbol.split(".")[0] not in COREFOUNDATION_ALLOWED:
            return (f"{name}: CoreFoundation.{symbol} is not one the client may use "
                    f"({', '.join(sorted(COREFOUNDATION_ALLOWED))}); the module carries sockets")
        return None
    if module not in MODULES:
        return (f"{name}: resolves `{decl}` in `{module}`, which is not a module the client may "
                "reach; the reader's words pass through every client file")
    return None


def _capability_problem(name: str, symbol: str, decl: str) -> str | None:
    """Network, file system and the ways text leaves a phone, inside the allowed modules."""
    head = symbol.split("(")[0]
    if (name, symbol) in FORBIDDEN_EXCEPT:
        return None
    if any(symbol.startswith(p) or head == p for p in FORBIDDEN):
        return f"{name}: `{decl}` carries text off the device or into shared storage"
    if any(symbol.startswith(p) for p in PATH_BUILDING):
        if name in {*FILESYSTEM_FILES, NETWORK_FILE}:
            return None
        return (f"{name}: `{decl}` builds a path, and the only paths here are the two stores' "
                "folders and the engine's request")
    if any(symbol.startswith(p) for p in FILESYSTEM) and name not in FILESYSTEM_FILES:
        allowed = "; ".join(f"{file}: {what}" for file, what in FILESYSTEM_FILES.items())
        return (f"{name}: `{decl}` reaches the file system, and only these files write one: {allowed}")
    if symbol == "URL.made" and name not in {NETWORK_FILE, *FILESYSTEM_FILES}:
        return (f"{name}: makes a URL (a call whose result is a URL, whatever it is named), and only "
                f"{NETWORK_FILE} and the two stores make one (D-126, #107)")
    if any(symbol.startswith(p) or head == p for p in NETWORK) and symbol != "URL.made" and name != NETWORK_FILE:
        return (f"{name}: `{decl}` is the network, and {NETWORK_FILE} is the one door (D-126); "
                "its arguments are pinned in EngineClientTests.swift")
    if head.split(".")[0] == "AppStorage" and name != APPSTORAGE_FILE:
        return (f"{name}: `{decl}` stores something outside the register; the one @AppStorage "
                "holds the language choice")
    return None


#: D-175 clause 3: the UI tests' hook exists in Debug builds only. A Release build that reads its
#: launch arguments ships a way to steer the app from outside it. (The scripted router itself is in
#: the Engine, which is never compiled on DEBUG, and is inert unless handed the arguments.) The launch
#: environment is the same door (M18-W2 review M5); `getenv` is refused already, by the module list.
DEBUG_ONLY = ("ProcessInfo.arguments", "ProcessInfo.environment", "CommandLine.arguments",
              "CommandLine.unsafeArgv")


def release_problems(found: dict[str, set[str]]) -> list[str]:
    """What a RELEASE configuration must not contain: the Debug-only UI test hooks (D-175)."""
    return [f"{name}: `{decl}` is a Debug-only UI test hook (D-175), compiled into a Release build"
            for name, decls in sorted(found.items()) for decl in sorted(decls)
            if any(hook in decl for hook in DEBUG_ONLY)]


def problems(found: dict[str, set[str]]) -> list[str]:
    bad: list[str] = []
    for name, decls in sorted(found.items()):
        for decl in sorted(decls):
            module, _, symbol = decl.partition(".")
            if module == "main" and symbol.startswith("<"):
                if (problem := _sink_problem(name, symbol) or _flow_problem(name, symbol)) is not None:
                    bad.append(problem)
                continue
            problem = _module_problem(name, module, symbol, decl)
            if problem is None and symbol != "<imported>" and module not in {"main", "UIKit", "CoreFoundation"}:
                problem = _capability_problem(name, symbol, decl)
            if problem is not None:
                bad.append(problem)
    return bad


def self_test() -> list[str] | None:
    """#51: the gate on its compiled fixture. What it failed to refuse, or allowed wrongly; empty
    when it behaves; None where there is no toolchain."""
    _, sdk_name, flags = CONFIGURATIONS[0]
    dumped = dump_ast(sdk_name, flags, FIXTURES)
    if dumped is None:
        return None
    ast, code = dumped
    if code != 0:
        return [f"the fixture does not type-check: {ast[-500:]}"]
    refused = problems(references(ast))
    missed = [f"{file}: {phrase} was not refused" for file, phrase in sorted(FIXTURE_REFUSALS)
              if not any(line.startswith(f"{file}:") and phrase in line for line in refused)]
    wrong = [line for line in refused
             if not any(line.startswith(f"{file}:") and phrase in line for file, phrase in FIXTURE_REFUSALS)]
    return missed + [f"refused what it must allow: {line}" for line in wrong]


def main() -> int:
    expected = {path.name for path in CLIENT.rglob("*.swift")}
    broken = self_test()
    if broken:
        for line in broken:
            print(f"client-decls FAIL (self-test, scripts/client_decl_fixtures): {line}")
        print("  The gate no longer refuses what it exists to refuse (#51); its PASS below would mean nothing.")
        return 1
    bad: list[str] = []
    totals: list[str] = []
    for label, sdk_name, flags in CONFIGURATIONS:
        dumped = dump_ast(sdk_name, flags)
        if dumped is None:
            print("client-decls SKIPPED NO-ENVIRONMENT: no Xcode toolchain (xcrun) on PATH")
            return 0
        ast, code = dumped
        if code != 0:
            print(f"client-decls FAIL: the client does not type-check ({label}), so this gate "
                  "cannot see what it would compile to")
            print(ast[-2000:])
            return 1
        found = references(ast)
        missing = expected - set(found)
        if missing:
            print(f"client-decls FAIL ({label}): {sorted(missing)} produced no tree. A dump that "
                  "stops early leaves files unchecked while everything else still passes")
            return 1
        bad += [f"({label}) {line}" for line in problems(found)]
        if "release" in label:
            bad += [f"({label}) {line}" for line in release_problems(found)]
        totals.append(f"{label}: {sum(len(v) for v in found.values())}")
    for line in bad:
        print(f"client-decls FAIL: {line}")
    if bad:
        print("  D-126: what the compiler binds, not what the source spells (W-122).")
        return 1
    print(f"client-decls PASS: {len(expected)} client file(s) in {len(CONFIGURATIONS)} "
          f"configuration(s) -- {'; '.join(totals)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
