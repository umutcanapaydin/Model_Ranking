#!/usr/bin/env python3
"""An ADR's status is derived: it waits for the owner's merge until the default branch holds it, Status line or none.

WHY (v7.3, harvest Q5, the owner's ruling of 2026-10-28). In three field projects the `**Status:**` field
carried no signal: 22 of 22 window ADRs, 71 of 91 and 40 of 53 still said `proposed` after their merge, and no
check read the field. So an ADR is accepted when the commit that added it is on the default branch; new ADRs
carry no Status line, and older ones keep theirs. `make standup` is the tool that reads it: its list of ADRs
awaiting the owner's merge must name every ADR the default branch does not hold yet -- one with no Status line,
and an old one whose line says `accepted` -- and none that it holds, whatever their line says.

In a throwaway clone of a throwaway origin: `scripts/standup.sh`, before and after the owner's merge.

Exit: 0 every case behaves - 1 one does not - 2 git or bash cannot run here.
"""
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import missing_tool, runnable_bash, scrubbed_env  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
STANDUP = ROOT / "scripts" / "standup.sh"
DECISIONS = ("# Decisions\n\n## D-001 — universal\n\n**Status:** accepted\n\n**Decision:** a.\n\n"
             "## D-100 — merged long ago, still saying proposed\n\n**Status:** proposed\n\n**Decision:** b.\n")
NEW = "\n## D-101 — a new ADR, no Status line\n\n**Decision:** c.\n"
OLD_STYLE = "\n## D-102 — written the old way, saying accepted\n\n**Status:** accepted\n\n**Decision:** d.\n"


def main() -> int:
    if (no_git := missing_tool("git", "build the repositories standup reads")):
        print(f"test-adr-status NOT-EVALUABLE: {no_git}")
        return 2
    bash, no_bash = runnable_bash("run scripts/standup.sh")
    if not bash:
        print(f"test-adr-status NOT-EVALUABLE: {no_bash}")
        return 2
    bad: list[str] = []
    env = scrubbed_env()
    with tempfile.TemporaryDirectory() as tmp:
        origin, clone = pathlib.Path(tmp) / "origin", pathlib.Path(tmp) / "clone"

        def git(where: pathlib.Path, *args: str) -> str:
            return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@x", *args], cwd=where, check=True,
                                  capture_output=True, text=True, env=env).stdout.strip()

        origin.mkdir()
        git(origin, "init", "-q", "--bare", "-b", "main")
        git(pathlib.Path(tmp), "clone", "-q", str(origin), str(clone))
        git(clone, "switch", "-q", "-c", "main")
        (clone / "docs").mkdir()
        (clone / "docs" / "decisions.md").write_text(DECISIONS, encoding="utf-8")
        git(clone, "add", "-A")
        git(clone, "commit", "-q", "-m", "decisions")
        git(clone, "push", "-q", "-u", "origin", "main")
        git(clone, "remote", "set-head", "origin", "main")
        (clone / "scripts").mkdir()
        shutil.copyfile(STANDUP, clone / "scripts" / "standup.sh")
        git(clone, "switch", "-q", "-c", "fix/issue-1-x")
        with (clone / "docs" / "decisions.md").open("a", encoding="utf-8") as f:
            f.write(NEW + OLD_STYLE)
        git(clone, "commit", "-q", "-am", "two ADRs on a branch")

        def awaiting() -> tuple[list[str], str]:
            r = subprocess.run([bash, str(clone / "scripts" / "standup.sh")], cwd=clone, capture_output=True,
                               text=True, env=env)
            out = r.stdout + r.stderr
            m = re.search(r"^-+ ADRs awaiting[^\n]*\n(.*?)^-----", out, re.M | re.S)
            return (re.findall(r"^## ([DP]-\d+)", m.group(1), re.M) if m else ["<no ADR section>"]), out

        def case(name: str, got: tuple[list[str], str], want: list[str]) -> None:
            if got[0] != want:
                bad.append(f"  {name}: listed {got[0]}, wanted {want}\n"
                           + "\n".join(f"    {ln}" for ln in got[1].splitlines()[:40]))

        case("before the merge: both branch ADRs await it, with or without a Status line; the merged ones do not",
             awaiting(), ["D-101", "D-102"])
        git(clone, "push", "-q", "origin", "HEAD:main")
        git(clone, "fetch", "-q", "origin")
        case("after the owner's merge: none awaits it, whatever its Status line says", awaiting(), [])

    if bad:
        print("test-adr-status FAIL (scripts/standup.sh in a throwaway clone):")
        print("\n".join(bad))
        return 1
    print("test-adr-status PASS: 2 cases -- an ADR awaits the owner's merge exactly while the default branch does "
          "not hold it, with or without a Status line")
    return 0


if __name__ == "__main__":
    sys.exit(main())
