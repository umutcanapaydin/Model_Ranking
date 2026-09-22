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
   refused by absence, so an API nobody has thought of yet is refused too. `UIKit` reaches the app
   through SwiftUI's re-export, so it is allowlisted SYMBOL by symbol.
2. **Capability rules inside the allowed modules.** Foundation and SwiftUI carry the ways text
   leaves a phone, so those are named: the network is EngineClient's alone, the file system is the
   gap register's alone, and sharing, hand-off, shared storage and logging belong to nobody.

The text gate in `tests/unit/test_router_hints.py` stays: it runs in every lane, including the ones
with no Xcode, and this one runs where the toolchain is. Neither is the whole check.
"""

from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import sys

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
    "CoreFoundation",
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

#: Declarations that reach the network, or build an address that could. A `URL` MADE FROM A STRING
#: is the network's first step; a `URL` that names a file on this device is the file system's, and
#: the two are told apart here by which initialiser the compiler chose.
NETWORK = ("URLSession", "URLRequest", "URLComponents", "URLQueryItem", "NSURL", "CFURL",
           "NSMutableURLRequest", "NSURLRequest", "NSURLSession", "NSURLConnection",
           "URL.init(string", "URL.init(dataRepresentation", "URL.lines", "URL.resourceBytes")
NETWORK_FILE = "EngineClient.swift"

#: Declarations that touch the file system, including the local-file half of `URL`. Only the gap
#: register's store may name them: it is the one thing this app writes.
FILESYSTEM = ("FileManager", "FileHandle", "Data.init(contentsOf", "Data.write", "String.write",
              "StringProtocol.write(toFile", "String.write(toFile", "write(to:",
              "URL.init(fileURLWithPath", "URL.init(filePath",
              "URL.deleting", "URL.setResourceValues", "URL.resourceValues", "URLResourceValues")
FILESYSTEM_FILE = "FrontDoor.swift"

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
    "View.userActivity",
    "View.fileExporter",
    "View.fileMover",
    "View.draggable",
    "View.onDrag",
    "View.shareable",
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

#: `@AppStorage("language")` is the one piece of app storage the client keeps, and it holds a
#: `Language`, never text a reader typed. The text gate pins its declaration; here the SwiftUI
#: property wrapper itself is allowed only in the file that declares it.
APPSTORAGE_FILE = "ContentView.swift"

#: `decl="Module.(file).Symbol"`. A member declared in an extension prints as
#: `Module.(file).Type extension.member`, with a SPACE, which hid `.draggable` and
#: `String.write(toFile:)` from the first version of this gate: the space ended the match.
DECL = re.compile(r'decl="?([A-Za-z_][\w]*)\.\(file\)\.((?:[\w.]+ extension\.)?[^ )"@]*)')
IMPORT = re.compile(r'\(import_decl[^)]*module="([^"]+)"')
SOURCE = re.compile(r'^\(source_file "([^"]+)"', re.MULTILINE)


def dump_ast(sdk_name: str, flags: list[str]) -> tuple[str, int] | None:
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
    sources = sorted(str(path) for path in CLIENT.rglob("*.swift"))
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
        for module, symbol in DECL.findall(ast[start:end]):
            # A member added in an extension prints as `Module.(file).extension.name`, which hid
            # `.draggable` and `String.write(toFile:)` from the first version of this gate.
            symbol = re.sub(r"([\w.]+) extension\.", r"\1.", symbol)
            symbol = re.sub(r"(^|\.)extension\.", r"\1", symbol)
            found[name].add(f"{module}.{symbol.rstrip('.')}")
    return found


def _module_problem(name: str, module: str, symbol: str, decl: str) -> str | None:
    """The module allowlist, including `import` lines, and UIKit's per-symbol exception."""
    if symbol == "<imported>":
        if module not in MODULES | {"UIKit"}:
            return (f"{name}: imports `{module}`, which is not on the client's module allowlist; "
                    "a new framework is a reviewed edit, not an import")
        return None
    if module == "UIKit":
        if symbol.split(".")[0] not in UIKIT_ALLOWED:
            return (f"{name}: UIKit.{symbol} is not one of the re-exported types the design layer "
                    f"may use ({', '.join(sorted(UIKIT_ALLOWED))})")
        return None
    if module not in MODULES:
        return (f"{name}: resolves `{decl}` in `{module}`, which is not a module the client may "
                "reach; the reader's words pass through every client file")
    return None


def _capability_problem(name: str, symbol: str, decl: str) -> str | None:
    """Network, file system and the ways text leaves a phone, inside the allowed modules."""
    head = symbol.split("(")[0]
    if any(symbol.startswith(p) or head == p for p in FORBIDDEN):
        return f"{name}: `{decl}` carries text off the device or into shared storage"
    if any(symbol.startswith(p) for p in PATH_BUILDING):
        if name in {FILESYSTEM_FILE, NETWORK_FILE}:
            return None
        return (f"{name}: `{decl}` builds a path, and the only paths here are the register's "
                "folder and the engine's request")
    if any(symbol.startswith(p) for p in FILESYSTEM) and name != FILESYSTEM_FILE:
        return (f"{name}: `{decl}` reaches the file system, and only {FILESYSTEM_FILE}'s register "
                "writes a file (REQ-GAP-001)")
    if any(symbol.startswith(p) or head == p for p in NETWORK) and name != NETWORK_FILE:
        return (f"{name}: `{decl}` is the network, and {NETWORK_FILE} is the one door (D-126); "
                "its arguments are pinned in EngineClientTests.swift")
    if head.split(".")[0] == "AppStorage" and name != APPSTORAGE_FILE:
        return (f"{name}: `{decl}` stores something outside the register; the one @AppStorage "
                "holds the language choice")
    return None


def problems(found: dict[str, set[str]]) -> list[str]:
    bad: list[str] = []
    for name, decls in sorted(found.items()):
        for decl in sorted(decls):
            module, _, symbol = decl.partition(".")
            problem = _module_problem(name, module, symbol, decl)
            if problem is None and symbol != "<imported>" and module not in {"main", "UIKit"}:
                problem = _capability_problem(name, symbol, decl)
            if problem is not None:
                bad.append(problem)
    return bad


def main() -> int:
    expected = {path.name for path in CLIENT.rglob("*.swift")}
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
