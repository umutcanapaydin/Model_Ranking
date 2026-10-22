"""#392: no workflow restores a dependency cache, and every `pip install` in one is hash-checked.

The nightly refresh job parses fetched data on a GitHub-hosted runner, where its code has `sudo` and the job's
runtime token, which can write Actions caches scoped to main. `ci.yml` restored the pip cache and installed
`pip-audit` (and PyYAML, and pip itself) with no hash, so a poisoned cache or a bad release could reach a later
run on main. Now:

- every `pip install` in a workflow is `--require-hashes` from locks under `requirements/` (D-177, `make lock`),
  or the project itself with `--no-deps` (`pip install --no-deps --no-build-isolation -e .`);
- no `actions/setup-python` step sets `cache:`, and no step uses an action that restores an Actions cache:
  every action a workflow uses is a named entry in `ACTIONS` with the reason it restores none (the bundle's
  security review, M5: `gitleaks/gitleaks-action` restored one, and downloaded its binary with no checksum);
- a run step that downloads a file with `curl` or `wget` checks that very file with `sha256sum -c`, on a later
  line (round 2's N5: one checked download in a block once vouched for every other in it).

The file set is derived: every `*.yml`/`*.yaml` under `.github/workflows/` (the installed workflows) and under
`scripts/ci/` (the proposals the owner installs). An empty set, a file PyYAML cannot read, and a set with no
`pip install` at all are failures, never a pass. The installed workflows are the owner's (`.github/workflows/**`):
the change is in `build/owner-run-queue-1021.patch`, and this test is red until the owner applies it.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_DIRS = (ROOT / ".github" / "workflows", ROOT / "scripts" / "ci")
#: pip's options that take a value, so the value is not read as what is installed.
VALUED = {"-r", "--requirement", "-c", "--constraint", "-i", "--index-url", "--extra-index-url", "-f",
          "--find-links", "-t", "--target", "--prefix", "--root", "--python-version", "--platform",
          "--implementation", "--abi", "--src", "--upgrade-strategy", "--progress-bar", "--log", "--cache-dir",
          "--trusted-host", "--proxy", "--retries", "--timeout", "--exists-action", "--config-settings", "-C",
          "--global-option", "--report", "--only-binary", "--no-binary", "--python"}
WRAPPERS = {"sudo", "env", "command", "time", "nice", "nohup"}
#: Every action a workflow may use, each with the reason it restores no Actions cache another workflow's run can
#: write (#392). A NAMED ENUMERATION, kept by hand for a written reason (AGENTS.md section 3.5): whether an action
#: restores a cache is in its source, which no test here can read, so each entry was read at the version it
#: names. GitHub's own actions are keyed by name; a third-party action by its pinned commit, so a bump is read again.
ACTIONS = {
    "actions/checkout": "clones the repository; restores no cache",
    "actions/setup-python": "restores a cache only with `cache:`, which this test refuses",
    "actions/upload-artifact": "an artifact of this run, not a cache",
    "actions/download-artifact": "reads an artifact by name from this run, not a cache (D-217)",
    "anthropics/claude-code-action@9d7150bc8a3dae8149739a88019d192b579ad90c":
        "sets `no-cache: true` on its setup-bun step (the bundle's security review, round 1)",
    "superfly/flyctl-actions/setup-flyctl@fc53c09e1bc3be6f54706524e3b82c4f462f77be":
        "uses only the runner's local tool cache, not an Actions cache (the bundle's security review, R3)",
}
#: Actions refused by name, with why.
REFUSED_ACTIONS = {
    "actions/cache": "restores a cache another workflow's run on main can write",
    "gitleaks/gitleaks-action": "restores `gitleaks-cache-<version>`, and downloads gitleaks with no checksum",
}
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def workflow_files() -> list[Path]:
    return sorted(p for d in WORKFLOW_DIRS if d.is_dir() for p in d.iterdir()
                  if p.suffix in (".yml", ".yaml") and p.is_file())


def _commands(run: str) -> list[list[str]]:
    """A `run:` block as simple commands: continuation lines joined, split at `;`, `&&`, `||`, `|`."""
    out: list[list[str]] = []
    for line in run.replace("\\\n", " ").splitlines():
        try:
            lexer = shlex.shlex(line, posix=True, punctuation_chars=";&|()")
            lexer.whitespace_split = True
            lexer.commenters = "#"
            tokens = list(lexer)
        except ValueError:
            tokens = line.split()
        cur: list[str] = []
        for token in tokens:
            if token and all(ch in ";&|()" for ch in token):
                if cur:
                    out.append(cur)
                cur = []
            else:
                cur.append(token)
        if cur:
            out.append(cur)
    return out


def pip_install_args(words: list[str]) -> list[str] | None:
    """The arguments after `install` when these words run pip's install, or None when they do not."""
    i = 0
    while i < len(words) and (ASSIGNMENT.match(words[i]) or words[i] in WRAPPERS):
        i += 1
    words = words[i:]
    if not words:
        return None
    program = Path(words[0]).name
    rest = words[1:]
    if re.fullmatch(r"python[0-9.]*", program):
        if "-m" not in rest:
            return None
        rest = rest[rest.index("-m") + 1:]
        if not rest or rest[0] not in ("pip", "pip3"):
            return None
        rest = rest[1:]
    elif program == "uv":
        if rest[:1] != ["pip"]:
            return None
        rest = rest[1:]
    elif not re.fullmatch(r"pip[0-9.]*", program):
        return None
    # pip's own options may come before the command (`pip --disable-pip-version-check install x`).
    at = next((k for k, w in enumerate(rest) if not w.startswith("-")), None)
    if at is None or rest[at] != "install":
        return None
    return rest[:at] + rest[at + 1:]


def install_problem(args: list[str]) -> str | None:
    """Why this `pip install` is not hash-checked, or None. Hash-checked: `--require-hashes` with every
    requirement file a lock under requirements/; or `--no-deps` of the project itself (`.`) and nothing else."""
    files: list[str] = []
    targets: list[str] = []
    i = 0
    while i < len(args):
        a = args[i]
        name, eq, value = a.partition("=")
        if a in ("-e", "--editable") and i + 1 < len(args):
            targets.append(args[i + 1])
            i += 2
            continue
        if a.startswith("-"):
            if name in ("-r", "--requirement"):
                files.append(value if eq else (args[i + 1] if i + 1 < len(args) else ""))
            i += 2 if (not eq and name in VALUED) else 1
            continue
        targets.append(a)
        i += 1
    if "--require-hashes" in args:
        if not files:
            return "`--require-hashes` with no requirement file"
        stray = [f for f in files if not (re.fullmatch(r"requirements/[\w.-]+\.lock", f) and (ROOT / f).is_file())]
        if stray:
            return f"`--require-hashes` from {stray}, which is not a lock under requirements/ (`make lock`)"
        if targets:
            return f"`--require-hashes` beside unhashed targets {targets}"
        return None
    if "--no-deps" in args and targets and all(t in (".", "./") for t in targets) and not files:
        return None
    return "neither `--require-hashes` from a lock nor `--no-deps` of the project itself"


def problems_in(doc: Any, where: str) -> tuple[list[str], int]:
    """(each cache or unhashed install in one parsed workflow, the number of `pip install`s it holds)."""
    bad: list[str] = []
    installs = 0
    jobs = doc.get("jobs") if isinstance(doc, dict) else None
    for job_name, job in (jobs or {}).items():
        for n, step in enumerate((job or {}).get("steps") or []):
            label = f"{where}: job `{job_name}` step {n + 1} ({step.get('name') or step.get('uses') or 'run'})"
            uses = str(step.get("uses") or "")
            if uses.startswith("actions/setup-python") and (step.get("with") or {}).get("cache"):
                bad.append(f"{label}: setup-python restores a `cache: {step['with']['cache']}` (#392)")
            if uses and (why := action_problem(uses)):
                bad.append(f"{label}: {why} (#392)")
            run = step.get("run")
            if not isinstance(run, str):
                continue
            bad += [f"{label}: {why} (#392)" for why in download_problems(run)]
            for words in _commands(run):
                args = pip_install_args(words)
                if args is None:
                    continue
                installs += 1
                if (why := install_problem(args)):
                    bad.append(f"{label}: `{' '.join(words)}` -- {why} (#392)")
    return bad, installs


#: The options that name where `curl` and `wget` write what they download.
OUTPUT = {"curl": ("-o", "--output"), "wget": ("-O", "--output-document")}


def _output_of(program: str, args: list[str]) -> str | None:
    """The file a `curl` or `wget` writes, as written in the step, or None when it writes to stdout."""
    short, long = OUTPUT[program]
    for i, a in enumerate(args):
        if a in (short, long) and i + 1 < len(args):
            return args[i + 1]
        if a.startswith(long + "="):
            return a.split("=", 1)[1]
        if a.startswith(short) and len(a) > 2 and not a.startswith("--"):
            return a[2:]
    return None


def _words_of(line: str) -> set[str]:
    """Every whitespace-separated word of a line, inside its quoted strings too (`echo "<sha>  $f"` names `$f`), so
    a file is matched whole: a check of `aa.tgz` does not vouch for `a.tgz` (round 3's N7)."""
    try:
        tokens = shlex.split(line, comments=True)
    except ValueError:
        tokens = line.split()
    return {part for token in tokens for part in token.split()}


def download_problems(run: str) -> list[str]:
    """Each `curl` or `wget` in a run block that no later `sha256sum -c` line checks by the file it wrote."""
    lines = run.replace("\\\n", " ").splitlines()
    out: list[str] = []
    for n, line in enumerate(lines):
        for words in _commands(line):
            i = 0
            while i < len(words) and (ASSIGNMENT.match(words[i]) or words[i] in WRAPPERS):
                i += 1
            program = Path(words[i]).name if i < len(words) else ""
            if program not in OUTPUT:
                continue
            target = _output_of(program, words[i + 1:])
            if target is None:
                out.append(f"`{' '.join(words)}` downloads to no file a checksum can check")
            elif not any("sha256sum -c" in later and target in _words_of(later) for later in lines[n + 1:]):
                out.append(f"`{' '.join(words)}` writes `{target}`, which no later `sha256sum -c` line checks")
    return out


def action_problem(uses: str) -> str | None:
    """Why a step's `uses:` may restore a cache, or None: a refused action, or one `ACTIONS` does not name."""
    name, _, ref = uses.partition("@")
    if uses.startswith(("./", "docker://")):
        return f"`{uses}` is a local or container action, which no entry here has read"
    for refused, why in REFUSED_ACTIONS.items():
        if name == refused or name.startswith(refused + "/"):
            return f"`{uses}` {why}"
    if name in ACTIONS or f"{name}@{ref}" in ACTIONS:
        return None
    return f"`{uses}` is not in ACTIONS, so nothing says it restores no Actions cache"


def _parse(text: str) -> Any:
    return yaml.safe_load(text)


def test_the_workflows_are_found() -> None:
    files = workflow_files()
    installed = [p for p in files if p.parent == WORKFLOW_DIRS[0]]
    assert installed, f"no workflow under {WORKFLOW_DIRS[0]}: nothing to grade is a failure, not a pass"
    assert any(p.name == "ci.yml" for p in installed), [p.name for p in installed]


def test_no_workflow_restores_a_cache_and_every_pip_install_is_hash_checked() -> None:
    files = workflow_files()
    assert files, "no workflow file found"
    bad: list[str] = []
    installs = 0
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        doc = _parse(path.read_text(encoding="utf-8"))   # a file PyYAML cannot read fails here, loudly
        found, n = problems_in(doc, rel)
        bad += found
        installs += n
    graded = ", ".join(p.relative_to(ROOT).as_posix() for p in files)
    assert installs > 0, f"no `pip install` found in {graded}: the reader reads nothing"
    assert not bad, f"graded {graded} (the working tree):\n" + "\n".join(bad)


def _one_step(run: str = "", uses: str = "", with_: dict[str, str] | None = None) -> Any:
    step: dict[str, Any] = {"name": "s"}
    if run:
        step["run"] = run
    if uses:
        step["uses"] = uses
    if with_:
        step["with"] = with_
    return {"jobs": {"j": {"steps": [step]}}}


@pytest.mark.parametrize("run", [
    "pip install pip-audit",
    "python -m pip install --upgrade pip",
    'python -m pip install "PyYAML>=6.0"',
    "pip3 install -r requirements.txt",
    "pip install --require-hashes -r requirements/nowhere.lock",
    "pip install --require-hashes -r requirements/dev.lock pip-audit",
    "pip install --no-deps requests",
    "pip install --no-deps -e . requests",
    "uv pip install pip-audit",
    "sudo pip install x",
    "X=1 python3.12 -m pip install x",
    ".venv/bin/python -I -m pip install x",
    "pip install \\\n  pip-audit",
    "true && pip install x",
    "pip --disable-pip-version-check install x",
])
def test_a_planted_unhashed_install_is_found(run: str) -> None:
    bad, installs = problems_in(_one_step(run=run), "planted")
    assert installs == 1 and len(bad) == 1, (run, bad)


@pytest.mark.parametrize("with_", [{"cache": "pip"}, {"cache": "'pip'"}, {"cache": "pipenv"}])
def test_a_planted_cache_is_found(with_: dict[str, str]) -> None:
    uses = "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065"
    bad, _ = problems_in(_one_step(uses=uses, with_={"python-version": "3.12", **with_}), "planted")
    assert len(bad) == 1, bad
    assert problems_in(_one_step(uses="actions/cache@v4"), "planted")[0]


@pytest.mark.parametrize("uses", [
    "gitleaks/gitleaks-action@ff98106e4c7b2bc287b24eaf42907196329070c7",
    "actions/cache@1bd1e32a3bdc45362d1e726936510720a7c30a57",
    "actions/cache/restore@v4",
    "someone/new-action@0123456789012345678901234567890123456789",
    "anthropics/claude-code-action@0000000000000000000000000000000000000000",
    "./.github/actions/local",
])
def test_an_action_that_restores_a_cache_or_is_not_named_is_found(uses: str) -> None:
    """The bundle's security review, M5: a cache restored inside an action is as reachable as setup-python's."""
    assert problems_in(_one_step(uses=uses), "planted")[0], uses


@pytest.mark.parametrize("uses", [
    "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
    "anthropics/claude-code-action@9d7150bc8a3dae8149739a88019d192b579ad90c",
    "superfly/flyctl-actions/setup-flyctl@fc53c09e1bc3be6f54706524e3b82c4f462f77be",
])
def test_a_named_action_is_quiet(uses: str) -> None:
    assert not problems_in(_one_step(uses=uses), "planted")[0], uses


def test_a_download_with_no_checksum_is_found_and_a_checked_one_is_quiet() -> None:
    plain = "curl -fsSL -o x.tgz https://example.invalid/x.tgz\ntar -xzf x.tgz"
    assert problems_in(_one_step(run=plain), "planted")[0]
    assert problems_in(_one_step(run="wget -q https://example.invalid/x"), "planted")[0]
    checked = plain + '\necho "00  x.tgz" | sha256sum -c -'
    assert not problems_in(_one_step(run=checked), "planted")[0]
    assert not problems_in(_one_step(run='curl -fsSL --output="$f" https://e.invalid/a\necho "00  $f" | sha256sum -c -'),
                           "planted")[0]


@pytest.mark.parametrize("run", [
    # Round 2's N5: a second download in a block that checks only the first.
    'curl -o a.tgz https://e.invalid/a\ncurl -o b.tgz https://e.invalid/b\necho "00  a.tgz" | sha256sum -c -',
    # The check comes before the download, so it checked another copy.
    'echo "00  a.tgz" | sha256sum -c -\ncurl -o a.tgz https://e.invalid/a',
    # Straight into a pipe: there is no file to check.
    "curl -fsSL https://e.invalid/a.tgz | tar -xz",
    'wget -Oa.tgz https://e.invalid/a\necho "00  b.tgz" | sha256sum -c -',
    # Round 3's N7: a check of `aa.tgz` named `a.tgz` only as a substring.
    'curl -o a.tgz https://e.invalid/a\necho "00  aa.tgz" | sha256sum -c -',
    'curl -o "$t" https://e.invalid/a\necho "00  ${t}x" | sha256sum -c -',
])
def test_every_download_is_checked_by_the_file_it_wrote(run: str) -> None:
    assert problems_in(_one_step(run=run), "planted")[0], run


def test_the_secret_scan_runs_gitleaks_from_a_checked_release() -> None:
    """M5: the scanner CI trusts is the one its release published, never a cached or unchecked copy."""
    doc = _parse((WORKFLOW_DIRS[0] / "ci.yml").read_text(encoding="utf-8"))
    runs = "\n".join(str(s.get("run") or "") for s in doc["jobs"]["secret-scan"]["steps"])
    assert "gitleaks detect" in runs or '"$RUNNER_TEMP/gitleaks"' in runs, runs
    assert re.search(r"gitleaks_[\d.]+_linux_x64\.tar\.gz", runs), runs
    assert re.search(r'echo "[0-9a-f]{64}  \S+" \| sha256sum -c', runs), runs


def test_yaml_spellings_of_cache_pip_all_read_as_pip() -> None:
    for spelling in ("cache: pip", "cache: 'pip'", 'cache: "pip"'):
        doc = _parse("jobs:\n  j:\n    steps:\n      - uses: actions/setup-python@x\n        with:\n"
                     f"          {spelling}\n")
        assert problems_in(doc, "planted")[0], spelling


@pytest.mark.parametrize("run", [
    "pip install --require-hashes -r requirements/dev.lock -r requirements/build.lock",
    "pip install --no-deps --no-build-isolation -e .",
    ".venv/bin/python -m pip install -q --require-hashes -r requirements/ingest.lock -r requirements/build.lock",
    "python -m pip install --require-hashes -r requirements/dev.lock",
    "pip-audit --strict --disable-pip -r requirements/dev.lock",
    "echo 'pip install x'",
    "pip list",
])
def test_a_hash_checked_install_or_no_install_is_quiet(run: str) -> None:
    bad, _ = problems_in(_one_step(run=run), "planted")
    assert not bad, (run, bad)
