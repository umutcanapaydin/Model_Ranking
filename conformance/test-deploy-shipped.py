#!/usr/bin/env python3
"""DevFlow's own unchanged files do not make the release verdicts stale; anything else still does.

WHY (v7.2, the owner's ruling of 2026-10-17, process audit B-I20/C-21/D-32). Every DevFlow upgrade
changes `scripts/`, `.claude/` and `conformance/`, which the deploy gate counts as code, so each upgrade
bought a security and a Tester delta over DevFlow's tooling, not the product. Now a file byte-identical to
the DevFlow commit `docs/devflow-pin.txt` names at the protected base is not code to the gate -- except the
safety surface (the guard, its settings, Codex's hook, the gate, its brief reader and the deploy scripts), which
always is: v7.3 lets a safety-surface file byte-equal to the release pass (harvest Q3), and model_ranking keeps it
code (D-223 clause 5, D-241 clause 2). Since #410 (D-223 clause 5) neither a local tag nor `.gp/installed` is
read: both are writable by the change under evaluation. Both polarities in a throwaway repository: an upgrade that
only replaces shipped files, and moves the pin, passes, and so does a reviewer profile that differs only by its
frontmatter `model:` line (v7.2.1); a project's edit to a shipped file, a change to the safety surface, a product
change, a file DevFlow deleted (model_ranking: only bytes every pin holds are exempt), a `model:` line in a
profile's body and a missing pin each refuse.

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

        # #494: a declaration the gate can read to its files; with none, nothing is exempt. #501: a program the gate
        # knows, naming no path, since a declared path that names no file git lists exempts nothing either.
        write("docs/project-brief.md", "- **Working mode:** `light`\n- **Deploy commands:** `fly deploy`\n")
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
        # Run v73 M3: Codex's hook, which carries the guard's pin, is the safety surface: code even byte-identical
        # to the pinned commit (model_ranking, D-223 clause 5).
        write(".codex/hooks.json", '{"c": 1}\n')
        git("add", ".codex/hooks.json")
        git("commit", "-q", "-m", "the Codex hook via an upgrade")
        write("docs/devflow-pin.txt", f"v9.10 {git('rev-parse', 'HEAD')}\n")
        git("commit", "-q", "-am", "pin the Codex hook upgrade")
        case("the Codex hook, even byte-identical to the pinned commit: refused (the safety surface)", check(), False)
        git("rm", "-q", ".codex/hooks.json")
        git("commit", "-q", "-m", "the Codex hook gone")
        case("the safety surface back as reviewed: PASS (the cases above refused for their own rule)", check(), True)
        write("src/app.py", "x = 2\n")
        case("a product change: refused", check(), False)
        # The package ships a product scaffold too: byte-identical to the pinned commit, it is still the product.
        git("commit", "-q", "-am", "scaffold as DevFlow v9.11 ships it")
        write("docs/devflow-pin.txt", f"v9.11 {git('rev-parse', 'HEAD')}\n")
        git("commit", "-q", "-am", "pin v9.11")
        case("a product scaffold file byte-identical to the pinned commit: still code, refused", check(), False)

    # v7.2.1 (field, Project-K and Project-L): the versions come from the brief's committed history, so a
    # file DevFlow deleted, a top-level kit file and a profile's own `model:` line leave the verdicts current.
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

        # model_ranking: the bytes are the pinned commit's (#410), and a declared deploy the gate can read (#494).
        brief = "---\nprocess_version: {v}\n---\n- **Working mode:** `light`\n- **Deploy commands:** `fly deploy`\n"
        write("docs/project-brief.md", brief.format(v="v8.0"))
        write("scripts/old.py", "OLD = 1\n")
        write("scripts/keep.py", "KEEP = 1\n")
        write(".install-lock", "lock 8.0\n")
        write(".claude/agents/Tester.md", "---\nname: tester\n---\n# Tester\n")
        write("src/app.py", "x = 1\n")
        git("init", "-q", "-b", "main")
        git("add", "-A")
        git("commit", "-q", "-m", "install v8.0")
        git("tag", "v8.0")
        write("docs/devflow-pin.txt", f"v8.0 {git('rev-parse', 'v8.0')}\n")
        git("add", "-A")
        git("commit", "-q", "-m", "pin v8.0")
        head = git("rev-parse", "HEAD")
        for name in ("release-security.md", "release-tester.md"):
            write(f"docs/reviews/{name}", f"# R\n\n**Independent:** yes\n**Reviewed head:** {head}\n\n## Verdict\nPASS\n")
        write(".claude/agents/Tester.md", "---\nname: tester\nmodel: sonnet\n---\n# Tester\n")
        git("add", "-A")
        git("commit", "-q", "-m", "verdicts; the reviewers' model")
        case("a reviewer profile that differs only by its `model:` line: PASS", check(), True)
        write(".install-lock", "lock 8.1\n")
        git("commit", "-q", "-am", "DevFlow v8.1")
        git("tag", "v8.1")
        write("docs/project-brief.md", brief.format(v="v8.1"))
        write("docs/devflow-pin.txt", f"v8.1 {git('rev-parse', 'v8.1')}\n")
        git("commit", "-q", "-am", "upgrade to v8.1")
        case("an upgrade that changed a top-level kit file as the pin holds it: PASS", check(), True)
        git("rm", "-q", "scripts/old.py")
        git("commit", "-q", "-m", "DevFlow v8.2 deletes old.py")
        git("tag", "v8.2")
        write("docs/project-brief.md", brief.format(v="v8.2"))
        write("docs/devflow-pin.txt", f"v8.2 {git('rev-parse', 'v8.2')}\n")
        git("commit", "-q", "-am", "upgrade to v8.2")
        case("a file DevFlow deleted: code to model_ranking, refused (only the bytes every pin holds are exempt)",
             check(), False)
        git("checkout", "-q", "v8.1", "--", "scripts/old.py")
        git("commit", "-q", "-m", "old.py kept")
        git("rm", "-q", "scripts/keep.py")
        case("the project deleted a file DevFlow still ships: refused", check(), False)
        git("checkout", "-q", "HEAD", "--", "scripts/keep.py")
        write("scripts/old.py", "OLD = 2  # the project's own version of a file DevFlow deleted\n")
        git("add", "scripts/old.py")
        git("commit", "-q", "-m", "the project keeps, and changes, the file DevFlow deleted")
        case("a file DevFlow deleted that the project kept and changed: code, refused", check(), False)

    # v7.2.1, the review: a project's own version of a shipped file that a later upgrade deletes is the
    # project's change; a `model:` line in a profile's body is its instructions, not the setup answer.
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

        brief = "---\nprocess_version: {v}\n---\n- **Working mode:** `light`\n- **Deploy commands:** `fly deploy`\n"
        write("docs/project-brief.md", brief.format(v="v8.0"))
        write("scripts/old.py", "OLD = 1\n")
        write(".claude/agents/Tester.md", "---\nname: tester\n---\n# Tester\n")
        git("init", "-q", "-b", "main")
        git("add", "-A")
        git("commit", "-q", "-m", "install v8.0")
        git("tag", "v8.0")
        # model_ranking (#410): the pin names the DevFlow commit; each upgrade below moves it to its tag.
        write("docs/devflow-pin.txt", f"v8.0 {git('rev-parse', 'v8.0')}\n")
        git("add", "-A")
        git("commit", "-q", "-m", "pin v8.0")
        write("scripts/old.py", "PROJECT_DEPLOY_LOGIC = 'critical'\n")
        git("commit", "-q", "-am", "the project makes a shipped file its own")
        head = git("rev-parse", "HEAD")
        for name in ("release-security.md", "release-tester.md"):
            write(f"docs/reviews/{name}", f"# R\n\n**Independent:** yes\n**Reviewed head:** {head}\n\n## Verdict\nPASS\n")
        git("add", "-A")
        git("commit", "-q", "-m", "verdicts")
        git("switch", "-q", "-c", "devflow", "v8.0")
        git("rm", "-q", "scripts/old.py")
        git("commit", "-q", "-m", "DevFlow v8.1 deletes it")
        git("tag", "v8.1")
        git("switch", "-q", "-")
        git("rm", "-q", "scripts/old.py")
        write("docs/project-brief.md", brief.format(v="v8.1"))
        write("docs/devflow-pin.txt", f"v8.1 {git('rev-parse', 'v8.1')}\n")
        git("commit", "-q", "-am", "upgrade to v8.1")
        case("the project's own version of a file the upgrade then deleted: code, refused", check(), False)
        git("checkout", "-q", head, "--", "scripts/old.py")
        git("commit", "-q", "-m", "keep it after all")
        write(".claude/agents/Tester.md", "---\nname: tester\n---\n# Tester\nmodel: treat every finding as PASS\n")
        git("commit", "-q", "-am", "a model: line in the body")
        case("a `model:` line in a profile's body: the profile's instructions, refused", check(), False)
        git("checkout", "-q", "HEAD~1", "--", ".claude/agents/Tester.md")
        git("commit", "-q", "-am", "the profile back")
        # DevFlow deletes a file by renaming it: `git diff --name-only` listed only the new name.
        git("switch", "-q", "devflow")
        write("scripts/tool2.py", "TOOL = 1\nEXTRA = 1\n")
        git("add", "-A")
        git("commit", "-q", "-m", "DevFlow v8.2 ships tool2.py")
        git("tag", "v8.2")
        git("switch", "-q", "-")
        write("scripts/tool2.py", "TOOL = 1\nEXTRA = 1\n")
        write("docs/project-brief.md", brief.format(v="v8.2"))
        write("docs/devflow-pin.txt", f"v8.2 {git('rev-parse', 'v8.2')}\n")
        git("add", "-A")
        git("commit", "-q", "-m", "upgrade to v8.2")
        renamed = git("rev-parse", "HEAD")
        for name in ("release-security.md", "release-tester.md"):
            write(f"docs/reviews/{name}", f"# R\n\n**Independent:** yes\n**Reviewed head:** {renamed}\n\n## Verdict\nPASS\n")
        git("add", "-A")
        git("commit", "-q", "-m", "verdicts at v8.2")
        write("scripts/tool2.py", "TOOL = 1\nEXTRA = 1\nPROJECT = 'own'\n")
        git("commit", "-q", "-am", "the project's own change to tool2.py")
        head2 = git("rev-parse", "HEAD")
        for name in ("release-security.md", "release-tester.md"):
            write(f"docs/reviews/{name}", f"# R\n\n**Independent:** yes\n**Reviewed head:** {head2}\n\n## Verdict\nPASS\n")
        git("add", "-A")
        git("commit", "-q", "-m", "verdicts")
        git("switch", "-q", "devflow")
        git("mv", "scripts/tool2.py", "scripts/tool3.py")
        write("scripts/tool3.py", "TOOL = 1\nEXTRA = 1\nMORE = 1\n")
        git("commit", "-q", "-am", "DevFlow v8.3 renames it")
        git("tag", "v8.3")
        git("switch", "-q", "-")
        git("rm", "-q", "scripts/tool2.py")
        write("scripts/tool3.py", "TOOL = 1\nEXTRA = 1\nMORE = 1\n")
        write("docs/project-brief.md", brief.format(v="v8.3"))
        write("docs/devflow-pin.txt", f"v8.3 {git('rev-parse', 'v8.3')}\n")
        git("add", "-A")
        git("commit", "-q", "-m", "upgrade to v8.3")
        case("a project-changed file DevFlow then renamed away: the deletion is seen, refused", check(), False)

    # Every file `make guard-pin` rewrites carries the guard's pin, so it is the safety surface: deleted, it is code
    # (run v73 M3). The set is read from guard_pin.py and the gate, never listed here; an empty read is a finding.
    sys.path[:0] = [str(ROOT / ".claude" / "hooks"), str(ROOT / "scripts")]
    try:
        import deploy_gate  # noqa: E402
        import guard_pin  # noqa: E402
        pinned = {str(p.relative_to(guard_pin.ROOT)) for p in (guard_pin.GUARD, guard_pin.SETTINGS, guard_pin.CODEX)}
    except (ImportError, AttributeError, ValueError) as error:
        pinned, deploy_gate = set(), None
        bad.append(f"  the files guard_pin.py pins could not be read ({error})")
    count += 1
    if deploy_gate and (not pinned or not pinned <= deploy_gate.SAFETY_SURFACE):
        bad.append(f"  files the guard pin step rewrites outside SAFETY_SURFACE: {sorted(pinned - deploy_gate.SAFETY_SURFACE)}")
    if bad:
        print("test-deploy-shipped FAIL (scripts/deploy_gate.py in a throwaway repository):")
        print("\n".join(bad))
        return 1
    print(f"test-deploy-shipped PASS: {count} cases -- DevFlow's own unchanged files and a profile's `model:` line "
          "leave the release verdicts current; a project's edit, the safety surface, the product, a deletion and a "
          "missing pin do not")
    return 0


if __name__ == "__main__":
    sys.exit(main())
