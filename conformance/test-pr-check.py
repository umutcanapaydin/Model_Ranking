#!/usr/bin/env python3
"""`make findings-check` accounts for every finding id of a fix or enhancement verdict; `make closing-keywords` names a commit message that closes an issue its PR does not.

WHY (v7.3, A26 and A29; the owner's rulings of 2026-10-28).
  * findings-check: since v6.6 `make wave-check` accounts for every finding id of a wave's verdicts -- one field
    project wrote 99 review files and filed no issue from them -- while the verdicts of a fix and of an
    enhancement were read by no gate (`/pre-merge` §5 said "you do"). The verdicts the branch's range adds or
    changes (`docs/reviews/fix-issue-*`, `enhancement-*`) must each be PASS or MINOR and declare
    `**Independent:** yes`, and every id in their BLOCKING, MINOR, K.9 and queued-risk sections must be a row
    of the PR body's findings table in wave-check's grammar: `fixed <sha>` (a commit), `#<n>`, or
    `refused — <why>`. A verdict dated on or before `.gp/installed`'s `installed_on` is history for its ids: one
    NOTE line, never a failure for them (a v7.2.2 PR body held no table; P5 review, B2) -- its verdict line and
    its independence are graded on every date (P7 delta security review, M2). Since then a finding with no id
    fails; with no readable marker it is a NOTE. Other verdicts -- a wave's, a release's -- are not this check's.
  * closing-keywords (Project-J #255): commit subjects such as `fix: #194's ...` closed two open issues when
    their PR merged. A keyword in a commit message closes its issue when the commit reaches the default
    branch, and GitHub lists no such link on the pull request, so `/pre-merge` §2's field cannot show it.
    Each spelling GitHub reads is caught (a colon, any case, `owner/repo#n`, an issue URL, in the body of the
    message too); the shapes that close nothing (`fix(#12)`, `hotfix #12`, `Refs #12`) pass.

Each case runs scripts/pr_check.py on a branch of a throwaway repository, with a fake `gh` that answers
`gh pr view` from a file and logs every call: the project's records and GitHub are never read (this test runs
in every project). Both checks ask gh only when there is something to compare, so a range with no finding id
and no keyword passes without a gh call; when there is, a gh that fails or is missing is CANNOT RUN (exit 2).

Exit: 0 every case behaves - 1 one does not - 2 git not installed.
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import QUIET_GIT, missing_tool, scrubbed_env  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "pr_check.py"
GH = ('#!/bin/sh\necho "$*" >> "$FAKE_GH_DIR/calls.log"\n'
      '[ "$1 $2" = "pr view" ] && [ -f "$FAKE_GH_DIR/pr.json" ] && exec cat "$FAKE_GH_DIR/pr.json"\n'
      'echo "no pull requests found for branch" >&2\nexit 1\n')
GIT = '#!/bin/sh\nexec "{git}" "$@"\n'
REPO = "https://github.com/o/r"


def verdict(status: str, findings: str, independent: bool = True, title: str = "fix-issue-12",
            date: str = "2026-10-29") -> str:
    return (f"# Security Review — {title}\n\n**Reviewer:** Security-Reviewer subagent\n"
            + ("**Independent:** yes\n" if independent else "") + f"**Date:** {date}\n\n"
            f"## Verdict\n{status}\n\n## Findings\n\n{findings}\n")


FULL = ("### BLOCKING\n- **B1** src/a.py:3 — the token is logged — A09 — exploitable\n  Evidence: `log.info(token)`\n\n"
        "### MINOR\n- **M1** src/a.py:9 — a broad except — hygiene\n\n"
        "### PASS\n- the new route checks the session\n\n## Risks queued\n- **R1** the rate limit is per process\n")


def main() -> int:
    no_git = missing_tool("git", "build the throwaway repositories pr_check.py reads")
    if no_git:
        print(f"test-pr-check NOT-EVALUABLE: {no_git}")
        return 2
    bad: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        base = pathlib.Path(tmp)
        proj, fake, only_git = base / "proj", base / "bin", base / "only-git"
        for d in (proj, fake, only_git):
            d.mkdir()
        (fake / "gh").write_text(GH, encoding="utf-8")
        (only_git / "git").write_text(GIT.format(git=shutil.which("git")), encoding="utf-8")
        for f in (fake / "gh", only_git / "git"):
            f.chmod(0o755)
        calls = base / "calls.log"
        env = scrubbed_env({"FAKE_GH_DIR": str(base), "PATH": os.pathsep.join([str(fake), os.environ.get("PATH", "")])})

        def git(*args: str) -> str:
            return subprocess.run(["git", *args], cwd=proj, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True,
                                  env=scrubbed_env()).stdout.strip()

        def commit(msg: str, files: dict[str, str] | None = None) -> str:
            for rel, text in (files or {}).items():
                p = proj / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(text, encoding="utf-8")
                git("add", rel)
            git("-c", "user.name=f", "-c", "user.email=f@x", "commit", "-q", "--allow-empty", "-m", msg)
            return git("rev-parse", "HEAD")

        def branch(name: str) -> None:
            git("checkout", "-q", "-B", name, "main")

        def pr(body: str = "", closes: tuple = (), number: int = 34) -> None:
            refs = [{"number": int(str(c).rsplit("#", 1)[-1]),
                     "url": (f"https://github.com/{c.rsplit('#', 1)[0]}/issues/{c.rsplit('#', 1)[-1]}"
                             if isinstance(c, str) else f"{REPO}/issues/{c}")} for c in closes]
            (base / "pr.json").write_text(json.dumps({"number": number, "url": f"{REPO}/pull/{number}", "body": body,
                                                      "closingIssuesReferences": refs}), encoding="utf-8")

        def no_pr() -> None:
            (base / "pr.json").unlink(missing_ok=True)

        def run(sub: str, *args: str, path: str | None = None) -> tuple[int, str]:
            calls.unlink(missing_ok=True)
            e = dict(env, PATH=path) if path else env
            r = subprocess.run([sys.executable, str(SCRIPT), sub, *args], cwd=proj, capture_output=True, text=True, encoding="utf-8", errors="replace", env=e)
            return r.returncode, r.stdout + r.stderr

        def expect(name: str, got: tuple[int, str], rc: int, *want: str, absent: tuple[str, ...] = (),
                   gh_called: bool | None = None, notes: int | None = None) -> None:
            code, out = got
            called = calls.is_file() and bool(calls.read_text(encoding="utf-8").strip())
            n_notes = sum(1 for ln in out.splitlines() if ln.startswith("NOTE [findings-check]"))
            why = [w for w in want if w not in out] + [f"not {a}" for a in absent if a in out]
            if code != rc or why or (gh_called is not None and called != gh_called) \
                    or (notes is not None and n_notes != notes):
                bad.append(f"  {name}: exit {code} (wanted {rc}); missing {why}; gh called: {called} (wanted "
                           f"{gh_called}); NOTE lines: {n_notes} (wanted {notes}); output:\n    "
                           + out.strip().replace("\n", "\n    ")[:1500])

        git("init", "-q", "-b", "main")
        for key, value in QUIET_GIT:
            git("config", key, value)
        commit("base", {"src/a.py": "x = 1\n"})
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(base / "origin.git")], capture_output=True,
                       check=True, env=scrubbed_env())
        git("remote", "add", "origin", str(base / "origin.git"))
        git("push", "-q", "-u", "origin", "main")
        security = "docs/reviews/fix-issue-12-security.md"

        # ---- findings-check
        branch("fix/issue-12-a")
        commit("fix: guard the empty input", {"src/a.py": "x = 2\n"})
        pr()
        expect("findings: no verdict in the range", run("findings"), 0, "findings-check PASS", "nothing to account for",
               gh_called=False)
        fixed = commit("security review", {security: verdict("MINOR", FULL)})
        table = ("Fixes the crash.\n\n| finding | disposition |\n|---|---|\n"
                 f"| security B1 | fixed {fixed[:7]} |\n| security M1 | #45 |\n"
                 "| security R1 | refused — the limit is enforced at the proxy, not here |\n")
        pr(table)
        expect("findings: every id a row", run("findings"), 0, "findings-check PASS", "3 finding id(s)", gh_called=True,
               notes=0)
        pr(table.replace("| security R1 | refused — the limit is enforced at the proxy, not here |\n", ""))
        expect("findings: an id with no row", run("findings"), 1, "FAIL [findings-check]", "R1", "no row",
               absent=("finding B1", "finding M1"))
        pr(table.replace("| security M1 | #45 |", "| security M1 | later |"))
        expect("findings: a disposition outside the grammar", run("findings"), 1, "`security M1`", "later")
        pr(table.replace(f"fixed {fixed[:7]}", "fixed 1234567"))
        expect("findings: fixed by a sha that is no commit", run("findings"), 1, "`security B1`", "1234567",
               "not a commit")
        pr(table.replace("| security M1 | #45 |", "| review M1 | #45 |"))
        expect("findings: a row for the wrong verdict kind", run("findings"), 1, "M1", "no row")
        pr(table)
        expect("findings: a PR given by number", run("findings", "--pr", "34"), 0, "findings-check PASS")
        expect("findings: the --opt=value spelling", run("findings", "--pr=34"), 0, "findings-check PASS")
        expect("findings: an unknown argument", run("findings", "--bogus"), 2, "usage")
        expect("findings: a PR that is not a number", run("findings", "--pr", "fix/issue-12-a"), 2, "usage")
        no_pr()
        expect("findings: ids, and gh cannot read the PR", run("findings"), 2, "findings-check CANNOT RUN")
        expect("findings: ids, and no gh at all", run("findings", path=str(only_git)), 2, "findings-check CANNOT RUN",
               "gh")
        pr(table)
        commit("re-review", {security: verdict("BLOCKING", FULL)})
        expect("findings: a BLOCKING verdict", run("findings"), 1, "BLOCKING")
        commit("re-review", {security: verdict("PASS | MINOR | BLOCKING", FULL)})
        expect("findings: an unfilled verdict", run("findings"), 1, "no `## Verdict`")
        commit("re-review", {security: verdict("MINOR", FULL, independent=False)})
        expect("findings: a verdict not independent", run("findings"), 1, "Independent")

        # Two kinds of verdict on one branch: `review M1` and `security M1` are two findings.
        branch("fix/issue-12-b")
        fixed = commit("reviews", {security: verdict("MINOR", "### MINOR\n- **M1** a.py:1 — x — y\n"),
                                   "docs/reviews/fix-issue-12-review.md": verdict("MINOR", "### MINOR\n- **M1** a.py:2 — x — y\n")})
        pr("| finding | disposition |\n|---|---|\n| security M1 | #45 |\n")
        expect("findings: review M1 and security M1 are two", run("findings"), 1, "fix-issue-12-review.md", "M1",
               absent=("fix-issue-12-security.md finding M1",))

        # No install marker: nothing dates the installation, so a finding with no id is one NOTE line for the whole
        # range, never a failure, and no gh call.
        branch("fix/issue-12-c")
        old = ("### BLOCKING\n- src/a.py:3 — the token is logged\n\n### MINOR\n- src/a.py:9 — a broad except\n"
               "- none\n\n## Risks queued\n- none\n")
        commit("older reviews", {security: verdict("PASS", old), "docs/reviews/enhancement-x-security.md":
                                 verdict("PASS", "### MINOR\n- a.py:1 — x\n", title="enhancement-x")})
        no_pr()
        expect("findings: no install marker, findings without ids", run("findings"), 0, "findings-check PASS",
               gh_called=False, notes=1)

        # P5 review, B2: a fix PR opened under v7.2.2 and still open at the upgrade. v7.2.2's verdict gave its MINOR
        # and queued-risk findings ids (only BLOCKING lacked them) and its PR body listed them in prose, no table. A
        # verdict dated before `.gp/installed`'s `installed_on` is history -- wave-check's rule for a close -- one NOTE
        # line, never a failure; one dated since is graded, and there a finding with no id fails too.
        marker = proj / ".gp" / "installed"
        marker.parent.mkdir()
        marker.write_text("gp_version: v7.3\ninstalled_on: 2026-10-25\n", encoding="utf-8")
        branch("fix/issue-12-h")
        v722 = ("### BLOCKING\n- none\n\n### MINOR\n- **M1** src/a.py:9 — a broad except — hygiene\n\n"
                "### PASS\n- the route checks the session\n\n## Risks queued\n- **R1** the rate limit is per process\n")
        commit("v7.2.2 review", {security: verdict("MINOR", v722, date="2026-10-20")})
        pr("Fixes the crash. Findings: M1 filed as #45; R1 refused, the proxy limits it.")
        expect("findings: a v7.2.2 verdict dated before the install", run("findings"), 0, "findings-check PASS",
               "history", "2026-10-25", gh_called=False, notes=1)
        commit("re-review", {security: verdict("MINOR", v722, date="2026-10-25")})
        expect("findings: the same verdict dated on the install day is history too", run("findings"), 0,
               "findings-check PASS", "history", gh_called=False, notes=1)
        # Delta security review M2: history skips the finding-id accounting only. A verdict's status and its
        # independence were v7.2.2's fields too (both reviewer profiles wrote them), so they are graded on every day.
        commit("re-review", {security: verdict("BLOCKING", v722, date="2026-10-25")})
        expect("findings: a BLOCKING verdict dated on the install day still fails", run("findings"), 1,
               "FAIL [findings-check]", "is BLOCKING", absent=("findings-check PASS",), gh_called=False)
        commit("re-review", {security: verdict("BLOCKING", v722, date="2026-10-20")})
        expect("findings: a BLOCKING verdict dated before the install still fails", run("findings"), 1,
               "FAIL [findings-check]", "is BLOCKING", absent=("findings-check PASS",), gh_called=False)
        commit("re-review", {security: verdict("MINOR", v722, independent=False, date="2026-10-25")})
        expect("findings: a verdict on the install day that declares no independence still fails", run("findings"), 1,
               "FAIL [findings-check]", "`**Independent:** yes`", absent=("findings-check PASS",), gh_called=False)
        commit("re-review", {security: verdict("PASS", "### MINOR\n- src/a.py:9 — a broad except\n", date="2026-10-25")})
        expect("findings: an install-day PASS with a finding with no id is history", run("findings"), 0,
               "findings-check PASS", "history", absent=("no id",), gh_called=False, notes=1)
        commit("re-review", {security: verdict("MINOR", v722, date="2026-10-26")})
        expect("findings: the same verdict dated the day after the install", run("findings"), 1, "finding M1",
               "finding R1", "no row")
        commit("re-review", {security: verdict("MINOR", v722, date="")})
        expect("findings: an undated verdict is graded", run("findings"), 1, "finding M1")
        commit("re-review", {security: verdict("PASS", "### MINOR\n- src/a.py:9 — a broad except\n")})
        expect("findings: since the install, a finding with no id fails", run("findings"), 1, "FAIL [findings-check]",
               "no id", gh_called=False)
        commit("re-review", {security: verdict("MINOR", v722, date="2026-10-20")})
        marker.write_text("gp_version: v7.3\n", encoding="utf-8")
        expect("findings: a marker with no readable installed_on dates nothing", run("findings"), 1, "finding M1")
        marker.unlink()
        expect("findings: no marker, ids are graded", run("findings"), 1, "finding M1")
        marker.parent.rmdir()

        # Not this check's: a wave's verdict, a release's, an integration's.
        branch("fix/issue-12-d")
        commit("other verdicts", {name: verdict("MINOR", "### MINOR\n- **M1** a.py:1 — x — y\n")
                                  for name in ("docs/reviews/m1-wave-1-review.md", "docs/reviews/release-security.md",
                                               "docs/reviews/integration-run-x-security.md")})
        expect("findings: a wave's, a release's and an integration's verdicts", run("findings"), 0,
               "nothing to account for", gh_called=False)

        # An enhancement's verdict is graded the same way.
        branch("enhancement/issue-9-y")
        commit("security review", {"docs/reviews/enhancement-issue-9-y-security.md":
                                   verdict("MINOR", "### MINOR\n- **M1** a.py:1 — x — y\n", title="enhancement-issue-9-y")})
        pr("no table here")
        expect("findings: an enhancement's id with no row", run("findings"), 1, "enhancement-issue-9-y-security.md", "M1")

        # RANGE: a branch cut from another (inside a run, from the integration branch) grades its own commits only.
        branch("fix/issue-12-e")
        lower = commit("a lower branch's verdict", {"docs/reviews/fix-issue-7-security.md":
                                                    verdict("MINOR", "### MINOR\n- **M1** a.py:1 — x — y\n", title="fix-issue-7")})
        fixed = commit("this branch's verdict", {security: verdict("PASS", "### MINOR\n- **M1** a.py:4 — x — y\n")})
        pr(f"| finding | disposition |\n|---|---|\n| security M1 | fixed {fixed[:7]} |\n")
        expect("findings: the default range holds the lower branch's verdict", run("findings"), 1, "fix-issue-7-security.md")
        expect("findings: RANGE= from the lower branch", run("findings", "--range", f"{lower}..HEAD"), 0,
               "findings-check PASS", "1 finding id(s)")
        expect("findings: a range that is not two commits", run("findings", "--range", "..HEAD"), 2, "CANNOT RUN")

        # ---- closing-keywords
        branch("fix/issue-12-k")
        for msg in ("test: reproduce #12 (red)", "fix: guard the empty input", "docs: hotfix #12 notes",
                    "fix(#12): the parser", "Refs #12", "chore: prefixes #3 and suffix #4"):
            commit(msg)
        pr(closes=(12,))
        expect("keywords: shapes that close nothing", run("closing-keywords"), 0, "closing-keywords PASS",
               "no closing keyword", gh_called=False)
        commit("fix: #12 empty input crashes")
        expect("keywords: one for the issue the PR closes", run("closing-keywords"), 0, "closing-keywords PASS",
               "PR #34", gh_called=True)
        sha = commit("fix: the date parser\n\nThis also Fixes #13.")
        expect("keywords: one in a message body, for an issue the PR does not close", run("closing-keywords"), 1,
               "FAIL [closing-keywords]", sha[:7], "#13", "PR #34", absent=("#12 ",))
        branch("fix/issue-12-v")
        for msg in ("Closes: #14", "RESOLVED #15", "closed o/r#16", "fixes https://github.com/o/r/issues/17",
                    "resolves other/repo#18"):
            commit(msg)
        pr(closes=())
        expect("keywords: every spelling", run("closing-keywords"), 1, "#14", "#15", "#16", "#17", "other/repo#18")
        pr(closes=(14, 15, 16, 17))
        expect("keywords: only the other repository's", run("closing-keywords"), 1, "other/repo#18",
               absent=("#14 ", "#15 ", "#16 ", "#17 "))
        pr(closes=(14, 15, 16, 17, "other/repo#18"))
        expect("keywords: each one the PR closes", run("closing-keywords"), 0, "closing-keywords PASS")
        no_pr()
        expect("keywords: a keyword, and gh cannot read the PR", run("closing-keywords"), 2,
               "closing-keywords CANNOT RUN", "#14")
        branch("fix/issue-12-r")
        lower = commit("fixes #20 in the lower branch")
        commit("test: reproduce #12 (red)")
        pr(closes=(12,))
        expect("keywords: the default range holds the lower commit", run("closing-keywords"), 1, "#20")
        expect("keywords: RANGE= from the lower commit", run("closing-keywords", "--range", f"{lower}..HEAD"), 0,
               "closing-keywords PASS", gh_called=False)
        expect("keywords: no subcommand", run("bogus"), 2, "usage")

    print("\n".join(bad))
    print(f"test-pr-check {'FAIL' if bad else 'PASS'}: findings-check and closing-keywords, each refusal for its "
          "reason and each quiet case quiet" + (f" -- {len(bad)} finding(s)" if bad else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
