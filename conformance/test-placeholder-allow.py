#!/usr/bin/env python3
"""bootstrap-check's placeholder check: strict by default, with named exceptions in `.placeholder-allow`.

WHY (DevFlow #16, D6; two field projects carried the identical patch). `[C1]` and `[C3]` of
`scripts/bootstrap-check.sh` read `<word>` as an unfilled template field. An append-only record can
quote such text as notation (an ADR's status note naming devices `box-<checkout>-<model>`), and it
cannot be reworded in place, so the check stayed red on a filled project. Skipping inline code is NOT
the fix: the shipped templates put their own unfilled fields in backticks (`<one-line statement>`,
`<First project decision>`). The exception is therefore a named entry with a written reason, per
file and per exact text, and an entry that no longer matches is itself a failure, so the list cannot
go stale. The entries reach awk through the environment, never through `awk -v`: BSD awk refuses a
`-v` value holding a newline, and an awk that dies there prints nothing, which would read as clean.

Each case builds a throwaway tree holding a copy of the script and its own docs, runs it there (the
script grades the tree it sits in), and reads only the `[C1]` and `[C3]` sections of its output. The
"as shipped" case takes the allowlist's comment header only: an installation's own entries name its
own records, which the throwaway tree does not hold. The package's file must be that header alone.

Exit: 0 every case behaves - 1 one does not - 2 bash cannot run here.
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import runnable_bash  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "bootstrap-check.sh"

PRD = "# PRD\n\n### REQ-CAL-001 — booking\n\nThe client books inside the window.\n"
ARCH = "# Architecture\n\nOne app and one API.\n"
DECISIONS = "# Decisions\n\n## D-100 — one platform\n\n**Decision:** one platform first.\n"
# model_ranking (D-199): this project's bootstrap-check strips inline code spans as notation (W-015, kept
# through D-155, D-161 and D-199), so the notation and the unfilled field below are written outside
# backticks; every case still holds the allowlist's rules as DevFlow ships them.
NOTE = "\nDevices are named box-<checkout>-<model>.\n"
ALLOW_BOTH = ("docs/decisions.md: <checkout> -- D-100 status note, append-only, names a device\n"
              "docs/decisions.md: <model> -- D-100 status note, append-only, names a device\n")


def run(bash: str, files: dict[str, str]) -> list[str]:
    """The [C1] and [C3] lines of bootstrap-check run in a tree holding `files`."""
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / "scripts").mkdir()
        shutil.copy(SCRIPT, root / "scripts" / "bootstrap-check.sh")
        for rel, text in files.items():
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text(text, encoding="utf-8")
        out = subprocess.run([bash, "scripts/bootstrap-check.sh"], cwd=root, capture_output=True,
                             encoding="utf-8", errors="replace", timeout=120).stdout
    keep, lines = False, []
    for line in out.splitlines():
        if line.startswith("["):
            keep = line.startswith(("[C1]", "[C3]"))
        elif keep:
            lines.append(line)
    return lines


def docs(prd: str = PRD, decisions: str = DECISIONS, allow: str | None = None) -> dict[str, str]:
    files = {"docs/prd.md": prd, "docs/architecture.md": ARCH, "docs/decisions.md": decisions}
    if allow is not None:
        files[".placeholder-allow"] = allow
    return files


def shipped_header() -> str:
    """The comment lines of `.placeholder-allow` -- the file as the package ships it. In an installation
    the file also holds the project's entries, which name the project's own records and are stale in
    a throwaway tree that does not hold them (fitness_app's four, v7.1.1)."""
    p = ROOT / ".placeholder-allow"
    if not p.is_file():
        return ""
    return "".join(ln for ln in p.read_text(encoding="utf-8").splitlines(keepends=True)
                   if not ln.strip() or ln.lstrip().startswith("#"))


def fails(lines: list[str], *words: str) -> bool:
    return any("[FAIL]" in ln and all(w in ln for w in words) for ln in lines)


def clean(lines: list[str]) -> bool:
    return not any("[FAIL]" in ln for ln in lines)


CASES = [
    ("a filled tree passes", docs(), clean),
    ("quoted notation with no entry still fails (strict by default)",
     docs(decisions=DECISIONS + NOTE), lambda ls: fails(ls, "decisions.md", "<checkout>")),
    ("named entries exempt exactly that text in that file",
     docs(decisions=DECISIONS + NOTE, allow=ALLOW_BOTH), clean),
    ("an unfilled template field still fails beside an allowlist",
     docs(prd=PRD + "\n### REQ-XX-002 — <one-line statement>\n", decisions=DECISIONS + NOTE,
          allow=ALLOW_BOTH),
     lambda ls: fails(ls, "prd.md", "<one-line statement>")),
    ("an entry for one file does not exempt another",
     docs(prd=PRD + NOTE, decisions=DECISIONS + NOTE, allow=ALLOW_BOTH),
     lambda ls: fails(ls, "prd.md", "<checkout>")),
    ("an entry that matches nothing fails as stale",
     docs(allow="docs/decisions.md: <checkout> -- gone since\n"),
     lambda ls: fails(ls, "stale", "<checkout>")),
    ("an entry with no reason fails",
     docs(decisions=DECISIONS + NOTE,
          allow="docs/decisions.md: <checkout>\ndocs/decisions.md: <model> -- ok\n"),
     lambda ls: fails(ls, ".placeholder-allow", "reason")),
    ("a line that is not `<path>: <text> -- <reason>` fails",
     docs(decisions=DECISIONS + NOTE, allow=ALLOW_BOTH + "docs/decisions.md <checkout> reason\n"),
     lambda ls: fails(ls, ".placeholder-allow", "line 3")),
    ("an entry whose text is not one placeholder fails",
     docs(decisions=DECISIONS + "\nSee `notes`.\n", allow="docs/decisions.md: notes -- not a placeholder\n"),
     lambda ls: fails(ls, ".placeholder-allow", "placeholder-shaped")),
    ("entries written with CRLF line ends still exempt",
     docs(decisions=DECISIONS + NOTE, allow=ALLOW_BOTH.replace("\n", "\r\n")), clean),
    ("a .placeholder-allow that is a directory fails",
     {**docs(decisions=DECISIONS + NOTE), ".placeholder-allow/keep": ""},
     lambda ls: fails(ls, ".placeholder-allow", "regular file")),
    ("an entry for a file the check does not read fails",
     docs(allow="src/other.md: <checkout> -- not graded here\n"),
     lambda ls: fails(ls, ".placeholder-allow", "src/other.md")),
    ("a comment-only allowlist, as shipped, exempts nothing and fails nothing",
     docs(allow=shipped_header()), clean),
]


def main() -> int:
    if not SCRIPT.is_file():
        print(f"test-placeholder-allow FAIL: {SCRIPT.relative_to(ROOT)} is missing")
        return 1
    if not (ROOT / ".placeholder-allow").is_file():
        print("test-placeholder-allow FAIL: .placeholder-allow is missing -- the shipped allowlist is "
              "the named-exception file the check reads")
        return 1
    if (ROOT / ".gp-distribution").is_file() and shipped_header() != (ROOT / ".placeholder-allow").read_text(
            encoding="utf-8"):
        print("test-placeholder-allow FAIL: the package's .placeholder-allow carries entries -- it ships "
              "comment-only, and an entry here would reach every project")
        return 1
    if not shipped_header().strip():
        print("test-placeholder-allow FAIL: .placeholder-allow has no comment header -- the as-shipped case "
              "has nothing to grade (an empty derived set is a failure)")
        return 1
    bash, why = runnable_bash("run scripts/bootstrap-check.sh in throwaway trees")
    if not bash:
        print(f"test-placeholder-allow NOT-EVALUABLE: {why}")
        return 2
    bad = []
    for name, files, expect in CASES:
        lines = run(bash, files)
        if not expect(lines):
            bad.append(f"  {name}:\n" + "\n".join(f"    {ln}" for ln in lines))
    if bad:
        print("test-placeholder-allow FAIL (scripts/bootstrap-check.sh, [C1]/[C3], in throwaway trees):")
        print("\n".join(bad))
        return 1
    print(f"test-placeholder-allow PASS: {len(CASES)} cases of scripts/bootstrap-check.sh [C1]/[C3] "
          "in throwaway trees")
    return 0


if __name__ == "__main__":
    sys.exit(main())
