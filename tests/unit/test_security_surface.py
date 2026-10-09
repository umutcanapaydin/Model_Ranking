"""M18-W6 (#89): three security invariants that had no negative test (`docs/security-invariants.md`).

- **INV-10:** every CI workflow reads only, but the issue agent, whose write scope is its job, and no
  secret is written into a `run:` body.
- **INV-11:** nothing in the repository turns TLS verification off, tests included. Ruff's `S`
  rules do not run over `tests/`.
- **INV-77:** the engine has no model in its scoring path (D-104): no module imports a model SDK,
  and no declared dependency is one.

Each check is a function over text, so each is also watched failing on a planted violation.
"""

from __future__ import annotations

import ast
import re
import subprocess
import tomllib
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


def tracked(*suffixes: str) -> list[Path]:
    """The tracked files under `src`, `scripts`, `tests` and `ios` with these suffixes: the tree git
    holds, not a build directory beside it (`ios/.build` holds thousands of third-party files)."""
    listed = subprocess.run(["git", "ls-files", "src", "scripts", "tests", "ios"], cwd=ROOT,
                            capture_output=True, text=True, check=True).stdout.split()
    return [ROOT / name for name in listed if name.endswith(suffixes)]

# --- INV-10: CI least privilege --------------------------------------------------------------------

#: The one workflow allowed to write, and why. A second needs its own entry and its reason.
WRITERS = {"issue-agent.yml": "opens a draft PR from a triaged issue; branch protection keeps main"}


def workflow_problems(name: str, text: str) -> list[str]:
    doc = yaml.safe_load(text) or {}
    problems = []
    scopes = [("the workflow", doc.get("permissions"))] + [
        (f"job {job}", spec.get("permissions")) for job, spec in (doc.get("jobs") or {}).items()
        if isinstance(spec, dict) and "permissions" in spec]
    if doc.get("permissions") is None:
        problems.append(f"{name}: no top-level `permissions:`, so it gets the repository's default")
    for where, scope in scopes:
        writes = scope == "write-all" or (isinstance(scope, dict) and "write" in scope.values())
        if writes and name not in WRITERS:
            problems.append(f"{name}: {where} can write")
    for job in (doc.get("jobs") or {}).values():
        for step in (job or {}).get("steps") or []:
            if "secrets." in str(step.get("run", "")):
                problems.append(f"{name}: a secret is written into the run body of {step.get('name')!r}")
    return problems


def test_every_workflow_reads_only_but_the_issue_agent() -> None:
    workflows = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
    assert workflows, "no workflow was read"
    problems = [p for path in workflows for p in workflow_problems(path.name, path.read_text(encoding="utf-8"))]
    assert not problems, problems


def test_the_workflow_check_fails_on_a_planted_writer_and_a_secret_in_a_run() -> None:
    planted = (
        "on: push\npermissions:\n  contents: write\njobs:\n  build:\n    runs-on: x\n    steps:\n"
        "      - name: leak\n        run: echo ${{ secrets.TOKEN }}\n"
    )
    assert len(workflow_problems("planted.yml", planted)) == 2
    assert workflow_problems("planted.yml", "on: push\njobs: {}\n")  # no permissions at all
    assert not workflow_problems("planted.yml", "on: push\npermissions:\n  contents: read\njobs: {}\n")


# --- INV-11: TLS verification is never turned off --------------------------------------------------

#: Python's ways, and Swift's: answering a server-trust challenge with a credential made from the
#: server's own trust accepts any certificate (the W6 review's M6; `.performDefaultHandling` is the
#: safe default, not a bypass).
TLS_OFF = re.compile(r"verify\s*=\s*False|_create_unverified_context|CERT_NONE|check_hostname\s*=\s*False"
                     r"|allowsExpiredCertificates|URLCredential\(\s*trust:|\.useCredential"
                     r"""|["']verify["']\s*:\s*False""")  # keyword unpacking (the W6 Tester's T4)


def tls_off(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if TLS_OFF.search(line)]


@pytest.mark.needs("git")
def test_nothing_turns_tls_verification_off() -> None:
    files = [path for path in tracked(".py", ".swift") if path != Path(__file__)]
    assert len(files) > 100, "the scan read almost nothing"
    found = {str(path.relative_to(ROOT)): hits for path in files
             if (hits := tls_off(path.read_text(encoding="utf-8", errors="replace")))}
    assert not found, found


def test_the_tls_check_fails_on_a_planted_verify_false() -> None:
    assert tls_off("client = httpx.Client(verify=False)")
    assert tls_off("ctx = ssl._create_unverified_context()")
    # The review's probe, in EngineClient.swift: a delegate that trusts any server.
    assert tls_off("completionHandler(.useCredential, challenge.protectionSpace.serverTrust.map { URLCredential(trust: $0) })")
    assert not tls_off("client = httpx.Client(timeout=5.0)")
    assert not tls_off("completionHandler(.performDefaultHandling, nil)")


# --- INV-77: no model in the engine's scoring path (D-104) -----------------------------------------

#: Model SDKs and runtimes. `litellm` is the package; the engine's `app.clients.litellm` reads a
#: price list over HTTP and imports no model, which is why the check reads top-level names.
MODEL_PACKAGES = {"openai", "anthropic", "litellm", "transformers", "torch", "tensorflow", "cohere",
                  "mistralai", "ollama", "llama_cpp", "vllm", "google.generativeai", "groq", "replicate"}


def model_imports(source: str) -> list[str]:
    """Model packages a module imports: statically, or by name through `importlib.import_module` or
    `__import__` (the W6 review's M6)."""
    found = []
    for node in ast.walk(ast.parse(source)):
        names = ([alias.name for alias in node.names] if isinstance(node, ast.Import)
                 # `from google import generativeai` imports `google.generativeai` (the Tester's T4)
                 else [node.module or "", *(f"{node.module}.{a.name}" for a in node.names)]
                 if isinstance(node, ast.ImportFrom) and node.level == 0 else [])
        if isinstance(node, ast.Call) and node.args and isinstance(node.args[0], ast.Constant):
            called = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
            if called in {"import_module", "__import__"} and isinstance(node.args[0].value, str):
                names.append(node.args[0].value)
        for name in names:
            if name.split(".")[0] in MODEL_PACKAGES or name in MODEL_PACKAGES:
                found.append(name)
    return found


def test_the_engine_imports_no_model_and_declares_none() -> None:
    sources = sorted((ROOT / "src").rglob("*.py"))
    assert len(sources) > 20
    found = {str(p.relative_to(ROOT)): hits for p in sources if (hits := model_imports(p.read_text(encoding="utf-8")))}
    assert not found, found
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    declared = project["dependencies"] + [d for extra in project["optional-dependencies"].values() for d in extra]
    named = {re.split(r"[<>=!~\[; ]", d, maxsplit=1)[0].lower().replace("-", "_") for d in declared}
    assert not named & MODEL_PACKAGES, sorted(named & MODEL_PACKAGES)
    # ...nor does any install pull one in by a dependency of a dependency: every lock is read too.
    locked = {re.split(r"[=\[ ]", line, maxsplit=1)[0].lower().replace("-", "_")
              for lock in (ROOT / "requirements").glob("*.lock")
              for line in lock.read_text(encoding="utf-8").splitlines() if line[:1].isalnum()}
    assert len(locked) > 20, "the locks were not read"
    assert not locked & MODEL_PACKAGES, sorted(locked & MODEL_PACKAGES)


@pytest.mark.parametrize("planted", ["import openai", "from anthropic import Anthropic", "import litellm",
                                     "importlib.import_module('openai')", "__import__('anthropic')"])
def test_the_model_check_fails_on_a_planted_import(planted: str) -> None:
    assert model_imports(planted)
    assert not model_imports("from app.clients.litellm import parse_pricing")


# --- the Tester's pins (M18-W6) --------------------------------------------------------------------


@pytest.mark.parametrize("planted", [
    "ctx.verify_mode = ssl.CERT_NONE",
    "ctx.check_hostname = False",
    "configuration.allowsExpiredCertificates = true",
    "let credential = URLCredential(trust: serverTrust)",
    "completionHandler(.useCredential, credential)",
])
def test_each_way_of_turning_tls_off_is_refused_on_its_own(planted: str) -> None:
    """The M18-W6 Tester's survivors: five of the seven TLS patterns could each be deleted with every
    test green, since the planted lines held two at once or none. Each is planted alone here."""
    assert tls_off(planted)


def test_the_workflow_check_reads_a_jobs_scope_and_write_all() -> None:
    """The M18-W6 Tester's survivors: the check of a job's own `permissions:` and of `write-all`
    could each be deleted with every test green, since the planted writer was workflow-wide."""
    job_writer = ("on: push\npermissions:\n  contents: read\njobs:\n  build:\n    runs-on: x\n"
                  "    permissions:\n      contents: write\n    steps: []\n")
    assert any("job build can write" in p for p in workflow_problems("planted.yml", job_writer))
    everything = "on: push\npermissions: write-all\njobs: {}\n"
    assert any("the workflow can write" in p for p in workflow_problems("planted.yml", everything))
    job_everything = ("on: push\npermissions:\n  contents: read\njobs:\n  build:\n"
                      "    permissions: write-all\n    steps: []\n")
    assert any("job build can write" in p for p in workflow_problems("planted.yml", job_everything))
    assert not workflow_problems("issue-agent.yml", job_writer), "the one allowed writer was refused"


def test_the_testers_two_spellings_are_refused() -> None:
    """The W6 Tester's T4: keyword unpacking turns TLS off as surely as `verify=False`, and
    `from google import generativeai` imports the package the list names."""
    assert tls_off('client = httpx.Client(**{"verify": False})')
    assert model_imports("from google import generativeai")
    assert not model_imports("from google import protobuf")


# --- The W5 Tester seat (docs/reviews/m19-wave-5-tester.md) ------------------------------------------------

#: #147: tests and docs name a Mac and a home network only by placeholder (RFC 6762's `.local` names
#: chosen for the purpose, and the probe values the launcher tests feed). Anything else could be a real
#: machine's name or address.
PLACEHOLDER_LOCAL_NAMES = {"my-mac", "probe-mac", "a"}
PLACEHOLDER_PRIVATE_ADDRESSES = {"192.168.9.9", "192.168.1.10"}
#: A `.local` host name: followed by a port, a path, a quote, a bracket, a comma, a space or the end,
#: so a file name such as `Engine.local.xcconfig` is not read as one.
LOCAL_NAME = re.compile(r"(?i)(?<![\w.-])([a-z0-9][a-z0-9-]*)\.local(?=[:/\s\"'`)\],]|$)", re.MULTILINE)
#: An RFC 1918 address, a regex-escaped one (`192\.168\.…`) included.
PRIVATE_ADDRESS = re.compile(r"(?<![\d.])((?:10|172\\?\.(?:1[6-9]|2\d|3[01])|192\\?\.168)(?:\\?\.\d{1,3}){1,3})(?![\d])")
#: macOS names a computer after its owner and its model, joined by hyphens, with `-2` and so on after
#: it: a hyphenated token holding the word "MacBook".
MAC_COMPUTER_NAME = re.compile(r"(?i)[a-z0-9-]*(?:[a-z0-9]-macbook|macbook-[a-z0-9])[a-z0-9-]*")


def owner_network_names(text: str) -> list[str]:
    """Each `.local` name, private address or Mac computer name in `text` that is not a placeholder."""
    lower = text.lower()
    found = [m.group(1) for m in LOCAL_NAME.finditer(text) if m.group(1).lower() not in PLACEHOLDER_LOCAL_NAMES]
    found += [m.group(1) for m in PRIVATE_ADDRESS.finditer(text)
              if m.group(1).replace("\\", "") not in PLACEHOLDER_PRIVATE_ADDRESSES
              and m.group(1).replace("\\", "").count(".") == 3]
    if "macbook" in lower:  # the pattern is slow; most files never say the word
        found += [m.group(0) for m in MAC_COMPUTER_NAME.finditer(text)]
    return found


@pytest.mark.needs("git")
def test_no_tracked_file_names_a_mac_or_home_address_beyond_the_placeholders() -> None:
    """#147 (wave plan P1): "No tracked file names the owner's Mac or home address: tests and docs use
    `my-mac.local` and `192.0.2.x`". No test held it, and the wave's own round-1 review record spelled
    both again in a search pattern (the second W5 review's M7), found only by reading. The scan reads
    every tracked text file, review records included, and names neither."""
    listed = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    problems = []
    for name in filter(None, listed.decode("utf-8").split("\0")):
        path = ROOT / name
        if not path.is_file():
            continue
        data = path.read_bytes()
        if b"\0" in data[:8192]:
            continue
        problems += [f"{name}: {hit}" for hit in owner_network_names(data.decode("utf-8", "replace"))]
    assert not problems, problems


def test_the_network_name_scan_reads_each_spelling() -> None:
    """The scan above, on planted lines: each real-looking name or address is found, a placeholder, a
    documentation address (RFC 5737) and a file name are not. Each planted value is written in two
    pieces (`|` removed), so the scan of this file does not find it."""
    def planted(text: str) -> str:
        return text.replace("|", "")

    name, address = planted("Someones-Mac|Book-Pro-2"), planted("192.168.|4.31")
    assert set(owner_network_names(f"http:/$()/{name}.local:8080")) == {name}
    assert owner_network_names(planted("git grep -i 'someones-mac|book'")) == [planted("someones-mac|book")]
    assert owner_network_names(f"ENGINE_LAN_IP={address}") == [address]
    escaped = address.replace(".", "\\.")
    assert owner_network_names(f"git grep 'pro-2\\|{escaped}'") == [escaped]
    assert owner_network_names(planted("10.0.|0.7 and 172.20.|1.2")) == [planted("10.0.|0.7"), planted("172.20.|1.2")]
    assert owner_network_names(planted("the-office-imac.lo|cal")) == ["the-office-imac"]
    assert owner_network_names("http:/$()/My-Mac.local:8080, 192.0.2.26, probe-mac.local, 192.168.9.9") == []
    assert owner_network_names("Engine.local.xcconfig, settings.local.json, the MacBook joins, macOS 10.15.7") == []
