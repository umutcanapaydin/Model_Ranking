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

- It scopes by FILE, never by data. A function declared in `EngineClient.swift` resolves in `main`,
  and `main` is not capability-checked, so a relay there that any file can call passes (B19); the
  file system is whole inside `FrontDoor.swift`, so a write to the temporary directory from there
  passes too (B31). What a file does with a capability it owns is for review and the tests.
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
           "Stream.getStreamsToHost")
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
            if problem is None and symbol != "<imported>" and module not in {"main", "UIKit", "CoreFoundation"}:
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
