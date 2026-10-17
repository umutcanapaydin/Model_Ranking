#!/usr/bin/env python3
"""The post-edit hook runs `make check-fast` where the edited file lives, and only the records leg after
a document edit.

WHY (v7.2, the owner's ruling of 2026-10-17). Two field projects replaced the hook with their own script
because it graded `$CLAUDE_PROJECT_DIR` while the edit was in a worktree, and every Markdown edit ran
the whole suite (process audit E-34, B-I12). `scripts/post_edit_scope.py` answers `<dir>|<args>`;
`check_fast.py --only-records` runs the records leg alone. Both polarities: a code edit keeps every leg;
a document edit drops the code legs; an edit in a worktree that carries the kit is graded there, one in a
tree that does not, where the hook always ran; an unreadable payload changes nothing.

Exit: 0 every case behaves - 1 one does not - 2 git not installed.
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import missing_tool, scrubbed_env  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCOPE = ROOT / "scripts" / "post_edit_scope.py"


def scope(payload: str) -> str:
    r = subprocess.run([sys.executable, str(SCOPE)], input=payload, capture_output=True, text=True,
                       env=scrubbed_env())
    return r.stdout.strip()


def payload(path: pathlib.Path | str) -> str:
    import json
    return json.dumps({"tool_input": {"file_path": str(path)}})


def main() -> int:
    if (no_git := missing_tool("git", "build the throwaway work trees the scope is read in")):
        print(f"test-post-edit-scope NOT-EVALUABLE: {no_git}")
        return 2
    bad: list[str] = []
    count = 0

    def case(name: str, got: str, want: str) -> None:
        nonlocal count
        count += 1
        if got != want:
            bad.append(f"  {name}: got `{got}`, want `{want}`")

    with tempfile.TemporaryDirectory() as tmp:
        kit = pathlib.Path(tmp).resolve() / "proj"
        (kit / "scripts").mkdir(parents=True)
        (kit / "docs").mkdir()
        (kit / "src").mkdir()
        (kit / "Makefile").write_text("x:\n", encoding="utf-8")
        shutil.copy(ROOT / "scripts" / "check_fast.py", kit / "scripts" / "check_fast.py")
        subprocess.run(["git", "init", "-q", str(kit)], check=True, capture_output=True, env=scrubbed_env())
        plain = pathlib.Path(tmp).resolve() / "plain"
        plain.mkdir()
        subprocess.run(["git", "init", "-q", str(plain)], check=True, capture_output=True, env=scrubbed_env())

        case("a code edit in a tree with the kit: graded there, every leg", scope(payload(kit / "src" / "a.py")),
             f"{kit}|")
        case("a Markdown edit: the records leg only", scope(payload(kit / "README.md")), f"{kit}|--only-records")
        case("anything under docs/: the records leg only", scope(payload(kit / "docs" / "notes.txt")),
             f"{kit}|--only-records")
        case("a file not yet written, in a new directory: its nearest existing parent decides",
             scope(payload(kit / "src" / "new" / "b.py")), f"{kit}|")
        case("an edit in a tree without the kit: where the hook always ran", scope(payload(plain / "a.py")), "|")
        case("a payload that is not JSON: nothing changes", scope("not json {"), "|")
        case("a payload with no path: nothing changes", scope("{}"), "|")

    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_fast.py"), "--plan", "--only-records"],
                       cwd=ROOT, capture_output=True, text=True, env=scrubbed_env())
    legs = [ln.split(":", 1)[0] for ln in r.stdout.splitlines() if ":" in ln]
    count += 1
    if r.returncode != 0 or legs != ["records"]:
        bad.append(f"  check_fast --plan --only-records: exit {r.returncode}, legs {legs} (want only `records`)")

    if bad:
        print("test-post-edit-scope FAIL (scripts/post_edit_scope.py, check_fast.py --only-records):")
        print("\n".join(bad))
        return 1
    print(f"test-post-edit-scope PASS: {count} cases -- the post-edit check runs where the edited file lives, "
          "and only the records leg after a document edit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
