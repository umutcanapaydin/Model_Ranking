#!/usr/bin/env python3
"""DevFlow's own unchanged files do not make the release verdicts stale; anything else still does.

WHY (v7.2, the owner's ruling of 2026-10-17, process audit B-I20/C-21/D-32). Every DevFlow upgrade
changes `scripts/`, `.claude/` and `conformance/`, which the deploy gate counts as code, so each upgrade
bought a security and a Tester delta over DevFlow's tooling, not the product. Now a file byte-identical to
the DevFlow commit `docs/devflow-pin.txt` names at the protected base is not code to the gate -- except the
safety surface (the guard, its settings, the gate, its brief reader and the deploy scripts), which always is.
Since #410 (D-223 clause 5) neither a local tag nor `.gp/installed` is read: both are writable by the change
under evaluation. Both polarities in a throwaway repository: an upgrade that only replaces shipped files, and
moves the pin, passes; a project's edit to a shipped file, a change to the safety surface, a product change,
and a missing pin each refuse.

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
GATE = ROOT / "scripts" / "deploy_gate.py"


def main() -> int:
    if (no_git := missing_tool("git", "build the throwaway repository the deploy gate reads")):
        print(f"test-deploy-shipped NOT-EVALUABLE: {no_git}")
        return 2
    bad: list[str] = []
    count = 0
    env = scrubbed_env()
    with tempfile.TemporaryDirectory() as tmp:
        repo = pathlib.Path(tmp)

        def write(rel: str, text: str) -> None:
            (repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (repo / rel).write_text(text, encoding="utf-8")

        def git(*args: str) -> str:
            return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@x", *args], cwd=repo, check=True,
                                  capture_output=True, text=True, env=env).stdout.strip()

        def check() -> tuple[int, str]:
            r = subprocess.run([sys.executable, str(GATE), "--check"], cwd=repo, capture_output=True, text=True,
                               env=env)
            return r.returncode, r.stdout + r.stderr

        def case(name: str, got: tuple[int, str], ok: bool) -> None:
            nonlocal count
            count += 1
            if (got[0] == 0) != ok:
                bad.append(f"  {name}: exit {got[0]}\n" + "\n".join(f"    {ln}" for ln in got[1].splitlines()[-5:]))

        # #494: a declaration the gate can read to its files; with none, nothing is exempt.
        write("docs/project-brief.md", "- **Working mode:** `light`\n- **Deploy commands:** `scripts/deploy.sh`\n")
        write("scripts/tool.py", "VERSION = 1\n")
        write(".claude/settings.json", "{}\n")
        write("src/app.py", "x = 1\n")
        write(".gp/installed", "gp_version: v9.9\n")
        git("init", "-q", "-b", "main")
        git("add", "-A")
        git("commit", "-q", "-m", "install v9.9")
        git("tag", "v9.9")
        write("docs/devflow-pin.txt", f"v9.9 {git('rev-parse', 'HEAD')}\n")
        git("add", "-A")
        git("commit", "-q", "-m", "pin v9.9")
        head = git("rev-parse", "HEAD")
        for name in ("release-security.md", "release-tester.md"):
            write(f"docs/reviews/{name}", f"# R\n\n**Independent:** yes\n**Reviewed head:** {head}\n\n## Verdict\nPASS\n")
        git("add", "-A")
        git("commit", "-q", "-m", "verdicts")
        case("the reviewed tree: PASS", check(), True)
        # An upgrade: the shipped tool changes, and the new tag holds it byte for byte.
        # DevFlow's tag holds the new tool; the project's upgrade commit takes it and `make install`
        # rewrites the marker, which no tag holds.
        write("scripts/tool.py", "VERSION = 2\n")
        git("commit", "-q", "-am", "DevFlow v9.10")
        git("tag", "v9.10")
        write(".gp/installed", "gp_version: v9.10\n")
        write("docs/devflow-pin.txt", f"v9.10 {git('rev-parse', 'v9.10')}\n")
        git("commit", "-q", "-am", "upgrade to v9.10")
        case("an upgrade that only replaced shipped files: PASS, no delta owed", check(), True)
        write("scripts/tool.py", "VERSION = 2  # the project's own change\n")
        case("the project changed a shipped file: refused", check(), False)
        git("checkout", "-q", "--", "scripts/tool.py")
        pin = (repo / "docs" / "devflow-pin.txt").read_text(encoding="utf-8")
        git("rm", "-q", "docs/devflow-pin.txt")
        git("commit", "-q", "-m", "no pin")
        case("no pin at the protected base: refused (cannot show it is DevFlow's)", check(), False)
        write("docs/devflow-pin.txt", pin)
        git("add", "-A")
        git("commit", "-q", "-m", "pin back")
        # #410 round 1's B2: each case below moves the pin to the commit that holds the change, so the only thing
        # that can refuse it is the rule the case names (the safety surface; tooling only), not a missing match.
        write(".claude/settings.json", '{"x": 1}\n')
        git("commit", "-q", "-am", "settings via an upgrade")
        write("docs/devflow-pin.txt", f"v9.10 {git('rev-parse', 'HEAD')}\n")
        git("commit", "-q", "-am", "pin the settings upgrade")
        case("the safety surface changed, even byte-identical to the pinned commit: refused", check(), False)
        write(".claude/settings.json", "{}\n")
        git("commit", "-q", "-am", "settings back")
        write("src/app.py", "x = 2\n")
        case("a product change: refused", check(), False)
        # The package ships a product scaffold too: byte-identical to the pinned commit, it is still the product.
        git("commit", "-q", "-am", "scaffold as DevFlow v9.11 ships it")
        write("docs/devflow-pin.txt", f"v9.11 {git('rev-parse', 'HEAD')}\n")
        git("commit", "-q", "-am", "pin v9.11")
        case("a product scaffold file byte-identical to the pinned commit: still code, refused", check(), False)

    if bad:
        print("test-deploy-shipped FAIL (scripts/deploy_gate.py in a throwaway repository):")
        print("\n".join(bad))
        return 1
    print(f"test-deploy-shipped PASS: {count} cases -- DevFlow's own unchanged files leave the release verdicts "
          "current; a project's edit, the safety surface, the product and a missing pin do not")
    return 0


if __name__ == "__main__":
    sys.exit(main())
