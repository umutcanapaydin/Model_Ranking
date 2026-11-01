#!/usr/bin/env python3
"""`make leak-scan` reports what the tracked tree holds that looks like data, and never fails: report only.

WHY (the 2026-10-27 field harvest, 6e; v7.3 A36). An adopted codebase can arrive with a database file, a dump, a
large blob or a CSV of people in its history. `make secrets` looks for credentials; nothing looked for data, and
committing personal data is an Escalate-NOW item (AGENTS.md §3). The adoption audit now records what
`scripts/leak_scan.py` finds. The owner ruled it report only: it never fails a gate and never blocks adoption, so
it exits 0 with findings, with none, and when it cannot read the tree -- which it says, never as "0 findings".

The cases run in throwaway repositories: one finding of each kind (a name, a size, a header in a CSV and in
JSON), the same shapes left untracked or harmless, a clean tree, a directory git cannot read, and `make leak-scan`
through the Makefile.

Exit: 0 every case behaves - 1 one does not - 2 git not installed.
"""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import QUIET_GIT, missing_tool, scrubbed_env  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "leak_scan.py"
CASES = [0]


def git(cwd: pathlib.Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, capture_output=True, check=True, env=scrubbed_env())


def scan(cwd: pathlib.Path, *cmd: str) -> tuple[int, str]:
    r = subprocess.run(list(cmd) or [sys.executable, str(SCRIPT)], cwd=cwd, capture_output=True, encoding="utf-8",
                       errors="replace", env=scrubbed_env())
    return r.returncode, r.stdout + r.stderr


def repo(base: pathlib.Path, name: str, files: dict[str, bytes]) -> pathlib.Path:
    d = base / name
    d.mkdir()
    git(d, "init", "-q")
    for key, value in QUIET_GIT:
        git(d, "config", key, value)
    for rel, data in files.items():
        (d / rel).parent.mkdir(parents=True, exist_ok=True)
        (d / rel).write_bytes(data)
    git(d, "add", "-A")
    git(d, "-c", "user.name=f", "-c", "user.email=f@x", "commit", "-qm", "base")
    return d


def main() -> int:
    missing = missing_tool("git", "build the throwaway repositories the scan reads")
    if missing:
        print(f"test-leak-scan NOT-EVALUABLE: {missing}")
        return 2
    bad: list[str] = []

    def case(name: str, ok: bool, out: str) -> None:
        CASES[0] += 1
        if not ok:
            bad.append(f"  {name}\n" + "\n".join(f"    {ln}" for ln in out.splitlines()))

    people = json.dumps([{"id": 1, "full_name": "A. Person", "Email": "a@example.invalid"}]).encode()
    with tempfile.TemporaryDirectory() as tmp:
        base = pathlib.Path(tmp).resolve()
        d = repo(base, "adopted", {
            "src/app.py": b"print('hello')\n",
            "data/app.sqlite3": b"SQLite format 3\0",
            "backup/prod.dump": b"-- a dump\n",
            "assets/blob.bin": b"\0" * (300 * 1024),
            "exports/users.csv": b"id,E-mail,Phone Number,city\n1,a@example.invalid,0,x\n",
            "fixtures/people.json": people,
            "notes/titles.csv": b"id,title,done\n1,buy milk,0\n",
            "config/settings.json": b'{"timeout": 5, "retries": 2}\n',
        })
        (d / "local.db").write_bytes(b"untracked")
        rc, out = scan(d)
        lines = out.splitlines()
        case("findings: exit 0 -- report only, never a gate", rc == 0, out)
        for kind, path in (("name", "data/app.sqlite3"), ("name", "backup/prod.dump"), ("size", "assets/blob.bin"),
                           ("header", "exports/users.csv"), ("header", "fixtures/people.json")):
            case(f"reports {kind} {path}", any(ln.split()[:2] == [kind, path] for ln in lines), out)
        case("a CSV header names the fields it matched", any("users.csv" in ln and "e_mail" in ln and "phone_number"
                                                             in ln for ln in lines), out)
        for path in ("notes/titles.csv", "config/settings.json", "src/app.py", "local.db"):
            case(f"no line for {path} (harmless, or not tracked)", not any(path in ln for ln in lines), out)
        case("the last line counts them and says report only", "5 finding(s)" in lines[-1] and "report only"
             in lines[-1], out)

        clean = repo(base, "clean", {"src/app.py": b"print('hello')\n", "tests/test_app.py": b"def test(): pass\n"})
        rc, out = scan(clean)
        case("a clean tree: exit 0, one line, 0 findings", rc == 0 and len(out.strip().splitlines()) == 1
             and "0 finding(s)" in out, out)

        nowhere = base / "not-a-repo"
        nowhere.mkdir()
        rc, out = scan(nowhere)
        case("not a git work tree: exit 0, CANNOT RUN, never 0 findings",
             rc == 0 and "CANNOT RUN" in out and "finding(s)" not in out, out)

        env = scrubbed_env({"PATH": str(base / "no-git")})       # git absent: the same answer, never a traceback
        (base / "no-git").mkdir()
        r = subprocess.run([sys.executable, str(SCRIPT)], cwd=d, capture_output=True, encoding="utf-8",
                           errors="replace", env=env)
        case("git not installed: exit 0, CANNOT RUN, no traceback", r.returncode == 0 and "CANNOT RUN" in r.stdout
             and "Traceback" not in r.stdout + r.stderr, r.stdout + r.stderr)

        if not missing_tool("make", "run `make leak-scan`"):
            shutil.copy2(ROOT / "Makefile", d / "Makefile")
            (d / "scripts").mkdir()
            if SCRIPT.is_file():
                shutil.copy2(SCRIPT, d / "scripts" / "leak_scan.py")
            rc, out = scan(d, "make", "leak-scan")
            case("make leak-scan, through the Makefile: exit 0 with its findings", rc == 0 and "5 finding(s)" in out,
                 out)

    if bad:
        print("test-leak-scan FAIL (scripts/leak_scan.py in throwaway repositories):")
        print("\n".join(bad))
        return 1
    print(f"test-leak-scan PASS: {CASES[0]} cases -- names, sizes and personal-data headers found in tracked files "
          "only, exit 0 every time, a tree it cannot read said so")
    return 0


if __name__ == "__main__":
    sys.exit(main())
