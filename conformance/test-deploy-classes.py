#!/usr/bin/env python3
"""The deploy gate asks what each target class owes, and a test change re-opens no verdict once the brief opts in.

WHY (v7.3, harvest Q1 and Q2, the owner's ruling of 2026-10-28). One field project deployed to staging three
times while `make deploy-check` was red, unrecorded; another wrote a local ADR and three bypass rows so that
internal builds owed the Tester's delta and not the security delta. And a delta that touched only tests came
back PASS with 0 findings, after a review. So the brief's `Deploy targets:` gives each deploy a class --
`production` and `external-test` owe both release verdicts (the v7.2 rule), `internal` and `staging` owe the
Tester's, the per-change security verdict `make review-need` asks for, and an `unreleased` release-note line
naming the build -- and once the brief carries a `Security-invariant tests:` line, a test-and-CI change since a
reviewed head re-opens neither verdict while CI is green on HEAD, and a security-invariant test it names stays
code. A brief with neither line keeps the v7.2 gate.

The class of a command (the Security-Reviewer's B1 and the Code-Reviewer's M3 and M8 on this package): a
production or external-test declaration matches in any word order, `--opt=value` read as two words, so
`vercel deploy --prebuilt --prod` is the production `vercel deploy --prod`; a team-only declaration decides only
when it holds every word of each production one the command also matches, and more (`fly deploy -c
fly.staging.toml` refines `fly deploy`; `netlify deploy --dir dist` does not refine `netlify deploy --prod`);
a tie goes to the stricter class, and one production command in a call makes the call production.

Both polarities per rule, in throwaway repositories, with a `gh` on PATH that answers `run list` as each case
says: `deploy_gate.py --check [--target <class>]` and the by-hand form `deploy_gate.py "<command>"`, which judges
a command as the Bash guard does.

Every case runs the real CLI. The fixtures run side by side, each in its own temp directory with its own `gh`,
and the gate runs that read one fixture state run together: any write, commit or `gh` answer first waits for
every run started before it, so each run reads exactly the state the serial order gave it (v7.3.1, gate speed).

Exit: 0 every case behaves - 1 one does not - 2 git not installed.
"""
import concurrent.futures
import os
import pathlib
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import missing_tool, pool_jobs, scrubbed_env  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
GATE = ROOT / "scripts" / "deploy_gate.py"
PASS_LINE = "deploy-check PASS: the security verdict and the milestone Tester's verdict are current for this tree"
FAKE_GH = '#!/bin/sh\n[ "$1 $2" = "run list" ] && [ -f "$(dirname "$0")/runs.json" ] || exit 1\ncat "$(dirname "$0")/runs.json"\n'


class Repo:
    """A throwaway repository and its own `gh`. Gate runs on one state go to `pool` together; a change to the
    state first waits for them (`settle`), so no run ever reads a later state than its place in the case list."""

    def __init__(self, tmp: str, env: dict, pool: concurrent.futures.Executor):
        self.root, self.bin = pathlib.Path(tmp) / "repo", pathlib.Path(tmp) / "bin"
        self.root.mkdir()
        self.bin.mkdir()
        (self.bin / "gh").write_text(FAKE_GH, encoding="utf-8")
        (self.bin / "gh").chmod(0o755)
        self.env = {**env, "PATH": f"{self.bin}{os.pathsep}{env.get('PATH', '')}"}
        self.pool, self.running = pool, []
        self.ci("success")
        self.git("init", "-q")

    def settle(self) -> None:
        concurrent.futures.wait(self.running)
        self.running.clear()

    def ci(self, conclusion: str | None) -> None:
        """What `gh run list` says about HEAD: one finished run of this conclusion, or no answer at all."""
        self.settle()
        runs = self.bin / "runs.json"
        if conclusion is None:
            runs.unlink(missing_ok=True)
        else:
            runs.write_text(f'[{{"status": "completed", "conclusion": "{conclusion}"}}]\n', encoding="utf-8")

    def write(self, rel: str, text: str) -> None:
        self.settle()
        (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
        (self.root / rel).write_text(text, encoding="utf-8")

    def git(self, *args: str) -> str:
        self.settle()
        return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@x", *args], cwd=self.root, check=True,
                              capture_output=True, text=True, env=self.env).stdout.strip()

    def commit(self, msg: str) -> str:
        self.git("add", "-A")
        self.git("commit", "-q", "-m", msg)
        return self.git("rev-parse", "HEAD")

    def run(self, argv: list[str]) -> tuple[int, str]:
        """A command now, in this repository, once every gate run before it has ended."""
        self.settle()
        r = subprocess.run(argv, cwd=self.root, capture_output=True, text=True, env=self.env)
        return r.returncode, r.stdout + r.stderr

    def gate(self, *args: str) -> concurrent.futures.Future:
        def one() -> tuple[int, str]:
            r = subprocess.run([sys.executable, str(GATE), *args], cwd=self.root, capture_output=True, text=True,
                               env=self.env)
            return r.returncode, r.stdout + r.stderr
        self.running.append(self.pool.submit(one))
        return self.running[-1]

    def verdict(self, name: str, head: str, word: str = "PASS") -> None:
        self.write(f"docs/reviews/{name}", f"# R\n\n**Independent:** yes\n**Reviewed head:** {head}\n\n## Verdict\n{word}\n")

    def team_ready(self, brief: str) -> str:
        """A brief, a product file, the security verdict made stale by a later change, the Tester's current at
        HEAD and an `unreleased` line naming HEAD: what a team-only deploy owes, and production does not have."""
        self.write("docs/project-brief.md", brief)
        self.write("src/app.py", "x = 1\n")
        head = self.commit("base")
        self.verdict("release-security.md", head)
        self.write("src/app.py", "x = 2\n")
        head = self.commit("a change the security verdict did not see")
        self.verdict("release-tester.md", head)
        self.write("docs/releases/unreleased.md", f"- 2026-10-29, staging, {head[:7]}: x is 2 (unreleased)\n")
        return head


SCENARIOS: list = []


def scenario(fn):
    """One fixture: its own repository, run side by side with the others."""
    SCENARIOS.append(fn)
    return fn


def jobs() -> int:
    """How many gate runs at once: its share when run-all runs it, else min(8, CPUs); unreadable is 1."""
    return pool_jobs(8, inside=True)[0]


@scenario
def fixture_1(r: Repo, case) -> None:
    # A brief from before v7.3: no `Deploy targets:`, no `Security-invariant tests:` -- the v7.2 gate.
    r.write("docs/project-brief.md", "- **Working mode:** `light`\n- Deploy commands: `./deploy.sh prod`\n")
    r.write("src/app.py", "x = 1\n")
    r.write("tests/test_app.py", "def test_x():\n    assert 1\n")
    scope = "def test_scope():\n    assert scope_of('a') == 'tenant-a'\n"
    r.write("tests/test_tenant_scope.py", scope)
    h0 = r.commit("base")
    r.verdict("release-security.md", h0)
    r.verdict("release-tester.md", h0)
    r.commit("verdicts")
    r.ci("success")
    case("an older brief, the reviewed tree: PASS, the v7.2 lines", r.gate("--check"), 0, PASS_LINE)
    r.write("tests/test_app.py", "def test_x():\n    assert 2\n")
    r.commit("a test change")
    case("an older brief, a test change: refused -- tests stay code without the brief's line, CI green or not",
         r.gate("--check"), 1, "tests/test_app.py")
    case("...and the production command is refused for it", r.gate("./deploy.sh prod"), 2,
         "BLOCKED: deploy gate")

    # The brief opts in: classed targets, and the invariant tests it names.
    r.write("docs/project-brief.md", "- **Working mode:** `light`\n- Deploy commands: `./deploy.sh prod`\n"
            "- Deploy targets: `staging: ./deploy.sh staging`, `external-test: ./upload.sh beta`, "
            "`stagin: ./typo.sh`\n- **Security-invariant tests:** `tests/test_tenant_*.py`\n")
    r.commit("brief: deploy targets and invariant tests")
    case("with `Security-invariant tests:` and CI green on HEAD, a test change since the reviewed head: PASS",
         r.gate("--check"), 0, PASS_LINE)
    r.ci("failure")
    case("...CI red on HEAD: refused, the test change counts", r.gate("--check"), 1, "tests/test_app.py",
         "CI is not green")
    r.ci(None)
    case("...CI unknown (gh gives no answer): refused, unknown is not green", r.gate("--check"), 1,
         "tests/test_app.py")
    r.ci("success")
    r.write("conformance/test-extra.py", "x = 1\n")
    r.commit("a conformance test")
    case("...and a conformance change: PASS (test-and-CI)", r.gate("--check"), 0, PASS_LINE)
    r.write("tests/test_tenant_scope.py", "def test_scope():\n    assert True\n")
    r.commit("the invariant test, weakened")
    case("...a security-invariant test the brief names, weakened: refused, it is code", r.gate("--check"), 1,
         "tests/test_tenant_scope.py")
    r.write("tests/test_tenant_scope.py", scope)
    r.commit("restored")
    case("...restored byte for byte: PASS", r.gate("--check"), 0, PASS_LINE)
    r.git("rm", "-q", "tests/test_tenant_scope.py")
    r.commit("deleted")
    case("...deleted: refused, a deletion is a change", r.gate("--check"), 1, "tests/test_tenant_scope.py")
    r.write("tests/test_tenant_scope.py", scope)
    h1 = r.commit("back")
    r.verdict("release-security.md", h1)
    r.verdict("release-tester.md", h1)
    r.commit("verdicts at h1")
    case("both verdicts at the new head: PASS", r.gate("--check"), 0, PASS_LINE)

    r.write("src/app.py", "x = 2\n")
    h2 = r.commit("a product change")
    r.verdict("release-tester.md", h2)
    r.commit("the Tester's delta only")
    case("production, security stale: FAIL", r.gate("--check"), 1, "release-security.md")
    case("TARGET=production says the same", r.gate("--check", "--target", "production"), 1,
         "release-security.md")
    case("external-test owes what production owes: FAIL", r.gate("--check", "--target", "external-test"), 1,
         "release-security.md")
    case("staging, no unreleased line: FAIL, and it says what to write",
         r.gate("--check", "--target", "staging"), 1, "unreleased", "docs/releases/")
    r.write("docs/releases/unreleased.md", f"- 2026-10-28 · staging · {h1[:7]} · an older build (unreleased)\n")
    case("staging, a line naming an older build (code changed since): FAIL -- the line must name this build",
         r.gate("--check", "--target", "staging"), 1, "names this build")
    r.write("docs/releases/unreleased.md", f"- 2026-10-28 · staging · {h2[:7]} · x is 2 (unreleased)\n")
    case("staging, the Tester current and the line naming this build: PASS, no security asked",
         r.gate("--check", "--target", "staging"), 0, "deploy-check PASS", "staging")
    case("internal owes what staging owes: PASS", r.gate("--check", "--target", "internal"), 0,
         "deploy-check PASS")
    case("the guard's question: the staging command is allowed", r.gate("./deploy.sh staging"), 0)
    case("...the production command is not", r.gate("./deploy.sh prod"), 2, "BLOCKED: deploy gate")
    case("...nor the external-test one", r.gate("./upload.sh beta"), 2, "BLOCKED: deploy gate")
    case("...and a target whose class is misspelled is read as production", r.gate("./typo.sh"), 2,
         "BLOCKED: deploy gate", "stagin")
    case("an unknown TARGET cannot run", r.gate("--check", "--target", "qa"), 2, "production, external-test")
    r.commit("the unreleased line")
    r.write("src/app.py", "x = 3\n")
    r.commit("code after the line")
    case("staging after a code change: FAIL (the Tester's head and the line are stale)",
         r.gate("--check", "--target", "staging"), 1, "release-tester.md")
    r.git("rm", "-q", "docs/reviews/release-tester.md")
    h3 = r.commit("no Tester verdict")
    r.write("docs/releases/unreleased.md", f"- 2026-10-28 · staging · {h3[:7]} · x is 3 (unreleased)\n")
    case("staging with no Tester verdict at all: FAIL -- staging never skips the Tester",
         r.gate("--check", "--target", "staging"), 1, "release-tester.md")

# One program, two classes, split by an option (Security-Reviewer B1): production matches in any order.
@scenario
def fixture_2(r: Repo, case) -> None:
    r.team_ready("- **Working mode:** `light`\n- Deploy targets: `staging: vercel deploy`, "
                 "`production: vercel deploy --prod`, `staging: netlify deploy`, `production: netlify deploy --prod`\n")
    for cmd in ("vercel deploy --prod", "vercel deploy --prebuilt --prod", "vercel --prod deploy",
                "cd src && vercel deploy --token=t --prod", "vercel deploy --yes --prod",
                "netlify deploy --dir=dist --prod"):
        case(f"`{cmd}` is production in any spelling: refused for the stale security verdict", r.gate(cmd), 2,
             "BLOCKED: deploy gate", "release-security.md")
    for cmd in ("vercel deploy", "vercel deploy --prebuilt", "netlify deploy --dir=dist"):
        case(f"`{cmd}` is staging: allowed", r.gate(cmd), 0)
    case("`vercel ls` is no deploy at all", r.gate("vercel ls"), 0)

# The same program with its own config for staging (Code-Reviewer M3): the most specific declaration wins.
@scenario
def fixture_3(r: Repo, case) -> None:
    r.team_ready("- **Working mode:** `light`\n- Deploy commands: `fly deploy`\n"
                 "- Deploy targets: `staging: fly deploy -c fly.staging.toml`\n")
    case("`fly deploy -c fly.staging.toml`: the staging declaration is the more specific -- allowed",
         r.gate("fly deploy -c fly.staging.toml"), 0)
    case("`fly deploy`: production -- refused", r.gate("fly deploy"), 2, "BLOCKED: deploy gate")
    case("`fly deploy --remote-only`: production -- refused", r.gate("fly deploy --remote-only"), 2,
         "BLOCKED: deploy gate")
    case("a staging and a production deploy in one call: the call is production -- refused",
         r.gate("fly deploy -c fly.staging.toml && fly deploy"), 2, "BLOCKED: deploy gate")
    case("`fly status` is no deploy", r.gate("fly status"), 0)

# One command declared in two classes with the same words (Code-Reviewer M2): the stricter class wins.
@scenario
def fixture_4(r: Repo, case) -> None:
    r.team_ready("- **Working mode:** `light`\n- Deploy commands: `./deploy.sh`\n"
                 "- Deploy targets: `staging: ./deploy.sh`\n")
    case("a command declared as production and as staging: production -- refused", r.gate("./deploy.sh"), 2,
         "BLOCKED: deploy gate", "release-security.md")

# A team-only target owes the per-change security verdict review-need asks for (harvest Q1(b)).
@scenario
def fixture_5(r: Repo, case) -> None:
    head = r.team_ready("- **Working mode:** `light`\n- **Paths that make a change HIGH:** `src/**`\n"
                        "- Deploy targets: `staging: ./stg.sh`\n")
    case("staging after a change under a HIGH path, no security verdict current: refused",
         r.gate("--check", "--target", "staging"), 1, "review-need")
    case("...the guard says the same", r.gate("./stg.sh"), 2, "BLOCKED: deploy gate", "review-need")
    r.verdict("fix-issue-7-security.md", head, "MINOR")
    case("...a per-change security verdict at this head: allowed -- nothing since it is left to ask",
         r.gate("--check", "--target", "staging"), 0, "deploy-check PASS", "asks none")
    r.verdict("fix-issue-7-security.md", head, "BLOCKING")
    case("...the same verdict BLOCKING: refused", r.gate("--check", "--target", "staging"), 1, "review-need")

# A staging declaration with flags of its own decides only when it refines the production one: it holds
# every word of each production declaration the command also matches (Security-Reviewer B1, round 2).
@scenario
def fixture_6(r: Repo, case) -> None:
    r.team_ready("- **Working mode:** `light`\n- Deploy targets: `staging: netlify deploy --dir dist`, "
                 "`production: netlify deploy --prod`, `staging: vercel deploy --prebuilt --yes`, "
                 "`production: vercel deploy --prod`\n")
    for cmd in ("netlify deploy --dir dist --prod", "netlify deploy --prod --dir dist",
                "cd src && netlify deploy --dir dist --prod", "vercel deploy --prebuilt --yes --prod"):
        case(f"`{cmd}`: a staging declaration without `--prod` cannot claim it -- refused", r.gate(cmd), 2,
             "BLOCKED: deploy gate", "release-security.md")
    for cmd in ("netlify deploy --dir dist", "vercel deploy --prebuilt --yes"):
        case(f"`{cmd}` is staging: allowed", r.gate(cmd), 0)

# `--opt=value` and `-o=value` are the option and its value (Code-Reviewer M8).
@scenario
def fixture_7(r: Repo, case) -> None:
    r.team_ready("- **Working mode:** `light`\n- Deploy targets: `production: fly deploy -a prod-app`, "
                 "`staging: fly deploy -a staging-app`\n")
    for cmd in ("fly deploy -a prod-app", "fly deploy -a=prod-app", "fly deploy --remote-only -a=prod-app"):
        case(f"`{cmd}` is the production app: refused", r.gate(cmd), 2, "BLOCKED: deploy gate")
    for cmd in ("fly deploy -a staging-app", "fly deploy -a=staging-app"):
        case(f"`{cmd}` is the staging app: allowed", r.gate(cmd), 0)

# A word the guard left unread (`$APP`, `$(...)`) may be any option and its value (run v73, Security-Reviewer
# M1): the strictest class of the program decides, and no team-only declaration refines past it.
@scenario
def fixture_8(r: Repo, case) -> None:
    r.team_ready("- **Working mode:** `light`\n- Deploy targets: `production: fly deploy -a prod-app`, "
                 "`staging: fly deploy -a staging-app`, `staging: vercel deploy`, `production: vercel deploy --prod`\n")
    for cmd in ("fly deploy -a $APP", "fly deploy -a staging-app $EXTRA", "vercel deploy $(cat flags)"):
        case(f"`{cmd}`: an unread word may be production's -- refused", r.gate(cmd), 2, "BLOCKED: deploy gate",
             "release-security.md")
    for cmd in ("fly logs -a $APP", "vercel ls $F", "vercel deploy"):
        case(f"`{cmd}`: production's subcommand missing, or nothing unread -- allowed", r.gate(cmd), 0)

# A team-only declaration with no option drops a whole `--opt=value` word, value and all (Security-Reviewer
# M6, round 3): the command is still that deploy, and the stale Tester refuses it.
@scenario
def fixture_9(r: Repo, case) -> None:
    r.team_ready("- **Working mode:** `light`\n- Deploy targets: `staging: npm run deploy:staging`, "
                 "`internal: ./ship.sh beta`\n")
    r.write("src/app.py", "x = 9\n")
    r.commit("code the Tester has not seen")
    for cmd in ("npm --loglevel=warn run deploy:staging", "./ship.sh --channel=qa beta"):
        case(f"`{cmd}` is the team-only deploy: judged, and refused for the stale Tester", r.gate(cmd), 2,
             "BLOCKED: deploy gate", "release-tester.md")

# A program declared for staging only stays a deploy when a word is unread (re-verification M4): the unread
# word empties nothing when no production declaration matches, and the stale Tester still refuses it.
@scenario
def fixture_10(r: Repo, case) -> None:
    r.team_ready("- **Working mode:** `light`\n- Deploy targets: `staging: netlify deploy --dir dist`\n")
    r.write("src/app.py", "x = 9\n")
    r.commit("code the Tester has not seen")
    for cmd in ("netlify deploy --dir dist $X", "x=--debug; netlify deploy --dir dist $x"):
        case(f"`{cmd}`: staging only, a word unread -- still judged, refused for the stale Tester", r.gate(cmd),
             2, "BLOCKED: deploy gate", "release-tester.md")

# A security verdict that read an owner-bundle patch (`**Reviewed patch:**`) read no tree: it neither starts
# the per-change range nor answers it (Security-Reviewer M5, round 3).
bundle_review = "# R\n\n**Independent:** yes\n**Reviewed patch:** {}\n**Reviewed head:** {}\n\n## Verdict\nPASS\n"
@scenario
def fixture_11(r: Repo, case) -> None:
    head = r.team_ready("- **Working mode:** `light`\n- **Paths that make a change HIGH:** `src/**`\n"
                        "- Deploy targets: `staging: ./stg.sh`\n")
    r.write("docs/reviews/owner-bundle-security.md", bundle_review.format("a" * 64, head))
    case("an unreviewed HIGH change and a bundle review current at HEAD: refused, the bundle review read no tree",
         r.gate("--check", "--target", "staging"), 1, "review-need")
    r.commit("the bundle review")
    r.write("lib/util.py", "y = 1\n")
    h2 = r.commit("an ordinary change after it")
    r.verdict("release-tester.md", h2)
    r.write("docs/releases/unreleased.md", f"- 2026-10-29, staging, {h2[:7]}: util (unreleased)\n")
    case("...and after an ordinary change: still refused, the bundle review does not start the range",
         r.gate("--check", "--target", "staging"), 1, "review-need")

# The unreleased range starts at the newest security verdict, so one reviewed HIGH change does not make
# every later team-only build owe a fresh security review (Security-Reviewer M4, Code-Reviewer R4).
@scenario
def fixture_12(r: Repo, case) -> None:
    head = r.team_ready("- **Working mode:** `light`\n- **Paths that make a change HIGH:** `src/**`\n"
                        "- Deploy targets: `staging: ./stg.sh`\n")
    r.verdict("fix-issue-7-security.md", head)
    r.commit("the HIGH change's own security verdict")
    r.write("lib/util.py", "y = 1\n")
    h2 = r.commit("an ordinary change after it")
    r.verdict("release-tester.md", h2)
    r.write("docs/releases/unreleased.md", f"- 2026-10-29, staging, {h2[:7]}: util (unreleased)\n")
    case("staging after a reviewed HIGH change and an ordinary one: allowed, no fresh security review",
         r.gate("--check", "--target", "staging"), 0, "deploy-check PASS")
    r.write("src/app.py", "x = 3\n")
    h3 = r.commit("a second HIGH change, not reviewed")
    r.verdict("release-tester.md", h3)
    r.write("docs/releases/unreleased.md", f"- 2026-10-29, staging, {h3[:7]}: x is 3 (unreleased)\n")
    case("...then a HIGH change after that verdict: refused, it owes its own", r.gate("--check", "--target",
         "staging"), 1, "review-need")

# The gate's own review-need run (Code-Reviewer M7): it writes no bytecode into the tree it grades, and a
# run that cannot answer is named as that, not as a HIGH change.
@scenario
def fixture_13(r: Repo, case) -> None:
    for name in ("deploy_gate.py", "brief_fields.py", "review_need.py"):
        r.write(f"scripts/{name}", (ROOT / "scripts" / name).read_text(encoding="utf-8"))
    r.team_ready("- **Working mode:** `light`\n- Deploy targets: `staging: ./stg.sh`\n")
    case("the gate in the tree it grades, a staging question: PASS, and no __pycache__ written beside it",
         r.run([sys.executable, "scripts/deploy_gate.py", "--check", "--target", "staging"]), 0, "deploy-check PASS")
    case("...nothing untracked under scripts/", (len(list((r.root / "scripts").glob("__pycache__"))), ""), 0)


# Python's own "write no bytecode" switch is off here, so only the gate's `-B` keeps the tree clean.
fixture_13.env = lambda env: {k: v for k, v in env.items() if k != "PYTHONDONTWRITEBYTECODE"}


@scenario
def fixture_14(r: Repo, case) -> None:
    with tempfile.TemporaryDirectory() as tools:
        for name in ("deploy_gate.py", "brief_fields.py"):
            (pathlib.Path(tools) / name).write_text((ROOT / "scripts" / name).read_text(encoding="utf-8"),
                                                    encoding="utf-8")
        (pathlib.Path(tools) / "review_need.py").write_text("raise SystemExit(3)\n", encoding="utf-8")
        r.team_ready("- **Working mode:** `light`\n- Deploy targets: `staging: ./stg.sh`\n")
        case("a review-need that cannot run: refused, and the refusal says it could not answer",
             r.run([sys.executable, str(pathlib.Path(tools) / "deploy_gate.py"), "--check", "--target", "staging"]),
             1, "could not answer")


# A glob with no `/` names a file wherever it sits, as .gitignore reads it (Security-Reviewer R3).
@scenario
def fixture_15(r: Repo, case) -> None:
    r.write("docs/project-brief.md", "- **Working mode:** `light`\n- **Security-invariant tests:** `test_scope.py`\n")
    r.write("tests/test_scope.py", "def test_scope():\n    assert scope_of('a') == 'tenant-a'\n")
    head = r.commit("base")
    r.verdict("release-security.md", head)
    r.verdict("release-tester.md", head)
    r.commit("verdicts")
    r.write("tests/test_scope.py", "def test_scope():\n    assert True\n")
    r.commit("the invariant test, weakened")
    r.ci("success")
    case("an invariant test named by its bare file name, weakened, CI green: refused, it is code",
         r.gate("--check"), 1, "tests/test_scope.py")


def main() -> int:
    if (no_git := missing_tool("git", "build the throwaway repository the deploy gate reads")):
        print(f"test-deploy-classes NOT-EVALUABLE: {no_git}")
        return 2
    env = scrubbed_env()

    def fixture(pool: concurrent.futures.Executor, fn) -> list[tuple[str, tuple[int, str], int, tuple[str, ...]]]:
        """One fixture's cases, in order, each with its gate run's answer."""
        with tempfile.TemporaryDirectory() as tmp:
            r = Repo(tmp, getattr(fn, "env", lambda e: e)(env), pool)
            cases: list = []
            fn(r, lambda name, got, code, *want_in: cases.append((name, got, code, want_in)))
            return [(name, got.result() if isinstance(got, concurrent.futures.Future) else got, code, want_in)
                    for name, got, code, want_in in cases]

    bad: list[str] = []
    count = 0
    # The fixtures are every `def fixture_*` in this file, derived from its text: one left without `@scenario`
    # would never run, so it is a failure, as is no fixture at all (v7.3.1 review, M2).
    defined = re.findall(r"^def (fixture_\w+)\(", pathlib.Path(__file__).read_text(encoding="utf-8"), re.M)
    registered = [fn.__name__ for fn in SCENARIOS]
    if not defined or sorted(defined) != sorted(registered):
        print(f"test-deploy-classes FAIL: the fixtures defined ({len(defined)}) are not the fixtures run "
              f"({len(registered)}): {sorted(set(defined) ^ set(registered)) or 'none at all'} -- mark each "
              "`def fixture_*` with @scenario")
        return 1
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs()) as runs, \
            concurrent.futures.ThreadPoolExecutor(max_workers=jobs()) as fixtures:
        found = list(fixtures.map(lambda fn: fixture(runs, fn), SCENARIOS))
    bad += [f"  {fn.__name__} graded no case" for fn, cases in zip(SCENARIOS, found) if not cases]
    for name, got, code, want_in in (c for cases in found for c in cases):
        count += 1
        if got[0] != code or any(w not in got[1] for w in want_in):
            bad.append(f"  {name}: exit {got[0]} (wanted {code}" + (f", and {list(want_in)}" if want_in else "")
                       + ")\n" + "\n".join(f"    {ln}" for ln in got[1].splitlines()[-8:]))

    # The gate's `gh` call ends inside the Bash guard's budget (run v73, Security-Reviewer R2): a slow `gh` is then
    # not green, said as that, never the budget's "split the command". Both numbers read from the code, or a finding.
    budget = re.search(r"^DEADLINE_S = ([0-9.]+)$", (ROOT / ".claude/hooks/bash_guard.py").read_text(encoding="utf-8"), re.M)
    gate_src = GATE.read_text(encoding="utf-8")
    gh_s = re.search(r"^GH_TIMEOUT_S = ([0-9.]+)$", gate_src, re.M)
    count += 1
    if not (budget and gh_s and "timeout=GH_TIMEOUT_S" in gate_src and float(gh_s.group(1)) < float(budget.group(1))):
        bad.append(f"  the gate's `gh` timeout ({gh_s and gh_s.group(1)}) is not read, not used, or not under the "
                   f"guard's budget ({budget and budget.group(1)} s)")
    if bad:
        print("test-deploy-classes FAIL (scripts/deploy_gate.py in throwaway repositories):")
        print("\n".join(bad))
        return 1
    print(f"test-deploy-classes PASS: {count} cases -- each target class owes its verdicts, a team-only "
          "declaration decides only when it refines production, and test-and-CI re-opens none while CI is green and the brief names its "
          "security-invariant tests; an older brief keeps the v7.2 gate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
