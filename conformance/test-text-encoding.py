#!/usr/bin/env python3
"""Every text read and write in delivered Python names its encoding.

WHY. Without `encoding=`, Python uses the locale's encoding: UTF-8 on a Mac, cp1254 on a Turkish
Windows console. On such a machine the governance self-test wrote its language probe with
`write_text()` in cp1254 and read it back as UTF-8, so the rule it proves never saw a Turkish
letter and reported that it did not fire. Everything passed with `PYTHONUTF8=1` and nothing else.
The environment variable is the second line of defence; the call that names its encoding is the
first, and it is the one this grades.

WHAT IS READ, derived: every `.py` file the PROJECT list of `INSTALL-MANIFEST.md` delivers (a
directory entry covers its tree; a GP-INTERNAL entry inside it is excluded), parsed with `ast` --
never grepped, so a comment or a string that mentions `open(` is not a call. A finding is:

  open(...) / io.open(...)  in a text mode (no `b`) without `encoding=` (or its 4th positional).
                            A mode that is not a string literal is a finding too: neither this
                            check nor a reader can tell text from binary.
  <x>.read_text(...)        without `encoding=` (or its 1st positional).
  <x>.write_text(...)       without `encoding=` (or its 2nd positional).
  <x>.open(...)             pathlib's `Path.open`, in a text mode, without `encoding=`. Only when
                            the call looks like it: no positional, or a first positional that is a
                            mode literal. `zf.open(name)`, `Image.open(fp)` and the modules below
                            have an `open` of their own and are not read.

`encoding=None` names nothing. A `**kwargs` spread is taken as naming it: the check cannot see
inside, and guessing would cry wolf.

FAILS CLOSED: no manifest, an empty delivered set, or a delivered file that does not parse is a
FAILURE. Before grading, the detector is run on a snippet it must flag and one it must not, so a
detector that stopped matching cannot report a clean tree.

Exit: 0 clean - 1 findings.
"""
import ast
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import manifest_internal, manifest_project           # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "__pycache__", ".venv", "node_modules"}
# Modules whose `open` is not a text-file open, or that `.read_text` means something else on.
OTHER_OPEN = {"os", "gzip", "bz2", "lzma", "tarfile", "zipfile", "webbrowser", "codecs", "shelve",
              "dbm", "wave", "sunau", "aifc", "resources"}
MODE_CHARS = set("rwaxbt+U")

MUST_FLAG = """\
open("a")
open("a", "w")
p.read_text()
p.write_text("x")
p.open()
p.open("w")
io.open("a")
open("a", mode)
p.read_text(encoding=None)
"""
MUST_PASS = """\
open("a", "rb")
open("a", encoding="utf-8")
open("a", "w", -1, "utf-8")
p.read_text("utf-8")
p.write_text("x", "utf-8")
p.write_bytes(b"")
p.open("rb")
p.open(encoding="utf-8")
zf.open(name)
Image.open(fp)
os.open("a", 0)
tarfile.open("a")
open("a", **kw)
"""


def _const_str(node: ast.AST | None) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _names_encoding(call: ast.Call, position: int) -> bool:
    """Does the call pass an encoding -- by keyword, by position, or through a `**` spread?"""
    for kw in call.keywords:
        if kw.arg is None:                                   # **kwargs
            return True
        if kw.arg == "encoding":
            return not (isinstance(kw.value, ast.Constant) and kw.value.value is None)
    if any(isinstance(a, ast.Starred) for a in call.args):
        return True
    if len(call.args) > position:
        arg = call.args[position]
        return not (isinstance(arg, ast.Constant) and arg.value is None)
    return False


def _mode(call: ast.Call, position: int) -> tuple[bool, str | None]:
    """(given, literal): the mode argument, if any, and its value when it is a string literal."""
    for kw in call.keywords:
        if kw.arg == "mode":
            return True, _const_str(kw.value)
    if len(call.args) > position:
        return True, _const_str(call.args[position])
    return False, "r"


def findings(source: str) -> list[tuple[int, str]]:
    """(line, what) for every text-mode read or write in `source` that names no encoding."""
    out: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        receiver = f.value if isinstance(f, ast.Attribute) else None
        recv_name = receiver.id if isinstance(receiver, ast.Name) else None
        if (isinstance(f, ast.Name) and f.id == "open") or \
                (isinstance(f, ast.Attribute) and f.attr == "open" and recv_name == "io"):
            given, mode = _mode(node, 1)
            if given and mode is None:
                out.append((node.lineno, "`open()` with a mode that is not a literal, and no "
                                         "`encoding=` -- text or binary cannot be told"))
            elif "b" not in (mode or "") and not _names_encoding(node, 3):
                out.append((node.lineno, "`open()` in text mode without `encoding=`"))
        elif isinstance(f, ast.Attribute) and recv_name not in OTHER_OPEN:
            if f.attr == "read_text" and not _names_encoding(node, 0):
                out.append((node.lineno, "`.read_text()` without `encoding=`"))
            elif f.attr == "write_text" and not _names_encoding(node, 1):
                out.append((node.lineno, "`.write_text()` without `encoding=`"))
            elif f.attr == "open":
                given, mode = _mode(node, 0)
                path_open = not given or (mode is not None and bool(mode) and set(mode) <= MODE_CHARS)
                if path_open and "b" not in (mode or "") and not _names_encoding(node, 2):
                    out.append((node.lineno, "`.open()` in text mode without `encoding=`"))
    return sorted(out)


def delivered(root: pathlib.Path) -> list[pathlib.Path] | None:
    """The delivered `.py` files, from the manifest's PROJECT list minus its GP-INTERNAL list."""
    project, internal = manifest_project(root), manifest_internal(root)
    if project is None:
        return None
    internal = {i.rstrip("/") for i in (internal or set())}
    files: set[pathlib.Path] = set()
    for entry in project:
        p = root / entry.rstrip("/")
        if p.is_dir():
            files |= set(p.rglob("*.py"))
        elif p.suffix == ".py" and p.is_file():
            files.add(p)
    out = []
    for p in sorted(files):
        rel = p.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts) or p.is_symlink():
            continue
        if rel.as_posix() in internal or any(rel.as_posix().startswith(i + "/") for i in internal):
            continue
        out.append(p)
    return out


def main() -> int:
    flagged, passed = findings(MUST_FLAG), findings(MUST_PASS)
    if [n for n, _ in flagged] != list(range(1, len(MUST_FLAG.splitlines()) + 1)) or passed:
        print(f"test-text-encoding FAIL: the detector is broken -- it flagged lines "
              f"{[n for n, _ in flagged]} of the must-flag snippet (all "
              f"{len(MUST_FLAG.splitlines())} expected) and {len(passed)} of the must-pass one "
              "(none expected). A detector that cannot tell them apart grades nothing")
        return 1
    files = delivered(ROOT)
    if files is None:
        print("test-text-encoding FAIL: INSTALL-MANIFEST.md or its PROJECT list is missing, so the "
              "delivered Python cannot be established. A guess would grade the wrong tree")
        return 1
    if not files:
        print("test-text-encoding FAIL: the manifest delivers no `.py` file. An empty derived set "
              "is a failure, never a vacuous pass")
        return 1
    bad = []
    for p in files:
        rel = p.relative_to(ROOT).as_posix()
        try:
            found = findings(p.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError) as exc:
            bad.append(f"{rel}: does not parse as UTF-8 Python ({type(exc).__name__}) -- it cannot "
                       "be graded, and it would not run either")
            continue
        bad += [f"{rel}:{n}: {what} -- the locale decides the encoding (cp1254 on a Turkish "
                "Windows console); name it: encoding=\"utf-8\"" for n, what in found]
    for b in bad:
        print(f"  FAIL {b}")
    print(f"test-text-encoding {'FAIL' if bad else 'PASS'}: {len(files)} delivered .py file(s) "
          f"parsed, {len(bad)} text read(s)/write(s) without an encoding")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
