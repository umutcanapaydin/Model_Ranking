#!/usr/bin/env python3
"""The network legs: a PyPI outage on another stack warns and leaves a ledger row, and `.deps-accept` waives an advisory only while its entry is whole and current.

WHY. #51 (Project-K, a swift stack): `slopsquat CANNOT RUN: PyPI unreachable (HTTP 502)` refused a push whose
product has no Python dependency at all -- the leg grades DevFlow's own tooling there. On a stack other than
python, outside CI, an outage now passes `slopsquat` and `deps` with a WARN and a `skip` row in
`docs/control-events.csv` (once per leg, wave and day), so three of them put the control under review. On
python, in CI, or where no row can be written (no ledger, a branch that names no wave), it stays CANNOT RUN.

v7.3 A20: `make deps` had no sanctioned waiver. `.deps-accept` names an advisory with its issue, an expiry at
most 90 days out and a reason; `make deps` passes it to pip-audit as `--ignore-vuln`. An entry past its expiry,
too far out, or missing a field turns the leg red, before the twelve-hour memory is asked.

#72: the macOS sandbox's proxy cut ruff's 6.2 MB PyPI JSON short, so `slopsquat` asks for it compressed
(1.1 MB) and reads either form; a truncated gzip stream is unreachable, never a pass.

The outage is a proxy that refuses every connection (`HTTPS_PROXY` at a closed local port): no network needed.
A sandbox that refuses a local bind (Claude Code's, `allowLocalBinding` off) leaves no port to close: there the
outage cases are not judged, every other case is, and the verdict is NOT-EVALUABLE (#72, sandboxed run).

Exit: 0 every case behaves - 1 one does not - 2 git not installed, or no local port to close.
"""
import datetime
import gzip
import importlib.util
import io
import os
import pathlib
import shutil
import socket
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import lib_record  # noqa: E402
from lib_record import missing_tool, scrubbed_env  # noqa: E402


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(ROOT / "scripts"))
    spec.loader.exec_module(mod)
    return mod


def closed_port() -> int | None:
    """A local port nothing listens on, or None where this process may not bind one (a sandbox)."""
    try:
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]
    except PermissionError:
        return None


def outage(case, port: int) -> None:
    """A18: a PyPI outage, a proxy at a closed local port, on a scratch project."""
    wave_check = load("wave_check")
    proxy = f"http://127.0.0.1:{port}"
    with tempfile.TemporaryDirectory() as tmp:
        t = pathlib.Path(tmp)
        (t / "scripts").mkdir()
        (t / "docs").mkdir()
        for s in ("net_cache.py", "slopsquat_check.py"):
            shutil.copy(ROOT / "scripts" / s, t / "scripts" / s)
        # The ledger's header as this project writes it, and none of its rows: the cases count the rows the outage
        # adds (model_ranking's ledger holds rows of its own).
        header = [ln for ln in (ROOT / "docs" / "control-events.csv").read_text(encoding="utf-8").splitlines()
                  if ln.startswith(("#", "control,")) or not ln.strip()]
        (t / "docs" / "control-events.csv").write_text("\n".join(header) + "\n", encoding="utf-8")
        (t / "pyproject.toml").write_text('[project]\nname = "x"\ndependencies = ["ruff>=0.7"]\n', encoding="utf-8")
        (t / ".devflow-stack").write_text("swift\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=t, check=True, env=scrubbed_env())
        subprocess.run(["git", "symbolic-ref", "HEAD", "refs/heads/fix/issue-7-outage"], cwd=t, check=True,
                       env=scrubbed_env())
        ledger = t / "docs" / "control-events.csv"

        def run(script: str, *args: str, **extra: str) -> tuple[int, str]:
            env = {k: v for k, v in scrubbed_env().items()
                   if k.lower() not in ("no_proxy", "ci", "github_actions", "https_proxy", "http_proxy")}
            env.update(HTTPS_PROXY=proxy, https_proxy=proxy, **extra)
            r = subprocess.run([sys.executable, str(t / "scripts" / script), *args], cwd=t, env=env,
                               capture_output=True, encoding="utf-8", errors="replace", timeout=120)
            return r.returncode, r.stdout + r.stderr

        def rows() -> list[str]:
            return [ln for ln in ledger.read_text(encoding="utf-8").splitlines()
                    if ln.strip() and not ln.startswith("#") and not ln.startswith("control,")]

        rc, out = run("slopsquat_check.py")
        case("swift, PyPI unreachable: slopsquat warns and passes", rc == 0 and "WARN" in out, f"exit {rc}: {out[-200:]}")
        got = rows()
        case("... and leaves one skip row for issue-7", len(got) == 1 and got[0].startswith("slopsquat,issue-7,skip,")
             and "NO-ENVIRONMENT" in got[0], f"{got}")
        case("... which the ledger's own check reads as well formed",
             not wave_check.ledger_findings(ledger.read_text(encoding="utf-8"), ROOT / "docs" / "warnings.ledger.md"))
        rc, out = run("slopsquat_check.py")
        case("the same outage again the same day: still one row", rc == 0 and len(rows()) == 1, f"{rows()}")
        rc, out = run("net_cache.py", "outage", "deps")
        case("`net_cache.py outage deps`, PyPI unreachable: passes with a deps row", rc == 0 and len(rows()) == 2
             and rows()[1].startswith("deps,issue-7,skip,"), f"exit {rc}: {out[-200:]}")
        rc, out = run("slopsquat_check.py", CI="true")
        case("in CI it stays CANNOT RUN, no row", rc == 2 and "CANNOT RUN" in out and len(rows()) == 2, f"exit {rc}")
        subprocess.run(["git", "symbolic-ref", "HEAD", "refs/heads/plan/m3"], cwd=t, check=True, env=scrubbed_env())
        rc, out = run("slopsquat_check.py")
        case("a branch that names no wave: CANNOT RUN, no row", rc == 2 and len(rows()) == 2, f"exit {rc}: {out[-200:]}")
        subprocess.run(["git", "symbolic-ref", "HEAD", "refs/heads/wave/m3-w2"], cwd=t, check=True, env=scrubbed_env())
        rc, out = run("net_cache.py", "outage", "deps")
        case("a wave branch: the row names m3-w2", rc == 0 and rows()[-1].startswith("deps,m3-w2,skip,"), f"{rows()[-1:]}")
        (t / ".devflow-stack").write_text("python\n", encoding="utf-8")
        rc, out = run("slopsquat_check.py")
        case("python, PyPI unreachable: CANNOT RUN, no row", rc == 2 and "CANNOT RUN" in out and len(rows()) == 3,
             f"exit {rc}")
        rc, out = run("net_cache.py", "outage", "deps")
        case("python: `outage deps` never excuses the audit", rc == 1 and len(rows()) == 3, f"exit {rc}")
        (t / ".devflow-stack").write_text("swift\n", encoding="utf-8")
        # R1 (the security review): a certificate PyPI's answer did not verify with is no outage. Every answer
        # fails that way here (urlopen replaced in the child), and on a swift stack both legs stay CANNOT RUN.
        driver = ("import runpy,ssl,sys,urllib.error,urllib.request\n"
                  "def refuse(*a, **k):\n"
                  "    raise urllib.error.URLError(ssl.SSLCertVerificationError(1, 'certificate verify failed'))\n"
                  "urllib.request.urlopen = refuse\n"
                  "sys.argv = sys.argv[1:]\n"
                  "runpy.run_path(sys.argv[0], run_name='__main__')\n")
        for script, args, want in (("slopsquat_check.py", (), 2), ("net_cache.py", ("outage", "deps"), 1)):
            r = subprocess.run([sys.executable, "-c", driver, str(t / "scripts" / script), *args], cwd=t,
                               env={k: v for k, v in scrubbed_env().items() if k not in ("CI", "GITHUB_ACTIONS")},
                               capture_output=True, encoding="utf-8", errors="replace", timeout=120)
            case(f"swift, a certificate that does not verify: {script} {' '.join(args)} stays CANNOT RUN, no row",
                 r.returncode == want and len(rows()) == 3, f"exit {r.returncode}: {(r.stdout + r.stderr)[-200:]}")
        ledger.unlink()
        rc, out = run("slopsquat_check.py")
        case("no ledger to write the row in: CANNOT RUN", rc == 2 and not ledger.exists(), f"exit {rc}")


def main() -> int:
    if (no_git := missing_tool("git", "build the throwaway repository the outage row names its wave from")):
        print(f"test-network-legs NOT-EVALUABLE: {no_git}")
        return 2
    bad: list[str] = []
    count = 0

    def case(name: str, ok: bool, detail: str = "") -> None:
        nonlocal count
        count += 1
        if not ok:
            bad.append(f"{name}{': ' + detail if detail else ''}")

    # --- A18: the outage, on a scratch project -------------------------------------------------------------
    port = closed_port()
    if port is None:
        unjudged = ("this sandbox refuses a local bind, so no port could be closed for the outage proxy: "
                    "the A18 outage cases were not judged here -- CI's required `install-and-governance` job judges "
                    "them on Linux, where a bind works; every other case passed")
    else:
        unjudged = ""
        outage(case, port)

    # --- R1: what counts as an outage -- the network's failure, and nothing else -------------------------------
    import http.client
    import ssl
    import urllib.error
    net = load("net_cache")
    for name, exc, want in (
            ("HTTP 502", urllib.error.HTTPError("u", 502, "Bad Gateway", {}, None), True),
            ("a refused connection", urllib.error.URLError(ConnectionRefusedError(61, "refused")), True),
            ("a name that does not resolve", urllib.error.URLError(socket.gaierror(8, "nodename")), True),
            ("a timeout", TimeoutError("timed out"), True),
            ("an answer cut off", http.client.IncompleteRead(b"", 10), True),
            ("a certificate that does not verify",
             urllib.error.URLError(ssl.SSLCertVerificationError(1, "certificate verify failed")), False),
            ("another TLS failure", ssl.SSLError(1, "tls"), False),
            ("HTTP 403", urllib.error.HTTPError("u", 403, "Forbidden", {}, None), False),
            ("an answer that is not JSON", ValueError("not JSON"), False)):
        case(f"R1: {name} {'is' if want else 'is not'} an outage", net.is_outage(exc) is want)

    # --- #72: the compressed answer ------------------------------------------------------------------------
    slop = load("slopsquat_check")
    body = b'{"releases": {"1.0": [{"upload_time_iso_8601": "2020-01-01T00:00:00Z"}]}}'

    class Answer(io.BytesIO):
        def __init__(self, data: bytes, encoding: str | None):
            super().__init__(data)
            self.headers = {"Content-Encoding": encoding} if encoding else {}

    case("#72: a gzip answer is read", slop.read_json(Answer(gzip.compress(body), "gzip")).get("releases") is not None)
    case("#72: a plain answer is read", slop.read_json(Answer(body, None)).get("releases") is not None)
    try:
        slop.read_json(Answer(gzip.compress(body)[:-12], "gzip"))
        case("#72: a gzip answer cut short is never read as JSON", False)
    except Exception:  # noqa: BLE001 -- any failure is unreachable to pypi(), which is the point
        case("#72: a gzip answer cut short is never read as JSON", True)

    # The other half of #72 (run v73, Tester M1): PyPI is asked for gzip, or the proxy's cut-off comes back.
    seen = []

    def fake_urlopen(req, timeout=None):
        seen.append(req.get_header("Accept-encoding"))
        return Answer(gzip.compress(body), "gzip")
    real = slop.urllib.request.urlopen
    slop.urllib.request.urlopen = fake_urlopen
    try:
        verdict = slop.pypi("ruff")[0]
    finally:
        slop.urllib.request.urlopen = real
    case("#72: PyPI is asked for gzip", seen == ["gzip"] and verdict == "ok")

    # --- A20: .deps-accept -------------------------------------------------------------------------------
    acc = load("deps_accept")
    today = datetime.date(2026, 10, 29)
    for name, text, ids, problems in (
            ("a whole, current entry", "# c\n\nPYSEC-2021-66 #12 2026-11-30 no fixed release yet\n", ["PYSEC-2021-66"], 0),
            ("an expiry exactly 90 days out", "GHSA-abcd-1234-wxyz #3 2027-01-27 upstream fix pending\n",
             ["GHSA-abcd-1234-wxyz"], 0),
            ("an expired entry", "PYSEC-2021-66 #12 2026-10-28 no fix\n", [], 1),
            ("an expiry 91 days out", "PYSEC-2021-66 #12 2027-01-28 no fix\n", [], 1),
            ("no reason", "PYSEC-2021-66 #12 2026-11-30\n", [], 1),
            ("an issue without its #", "PYSEC-2021-66 12 2026-11-30 no fix\n", [], 1),
            ("a date that is not one", "PYSEC-2021-66 #12 2026-02-30 no fix\n", [], 1),
            ("a date in another ISO shape", "PYSEC-2021-66 #12 20261130 no fix\nCVE-2024-2 #1 2026-W48-1 b\n", [], 2),
            ("an id a shell would read", "PYSEC-1;rm #12 2026-11-30 no fix\n", [], 1),
            ("the same id twice", "CVE-2024-1 #1 2026-11-30 a\nCVE-2024-1 #2 2026-11-30 b\n", ["CVE-2024-1"], 1)):
        got_ids, got_problems = acc.entries(text, today)
        case(f".deps-accept, {name}", got_ids == ids and len(got_problems) == problems, f"{got_ids} {got_problems}")
    # M1 (the security review): a line is what git shows as one line. A character Python also breaks lines on
    # (FS 0x1c in the reviewer's example, VT, FF, GS, RS, NEL, U+2028, U+2029, a lone CR) once hid an active entry
    # inside a comment; such a line is refused, comment or not. A CRLF line end is only a line end.
    for sep in ("\x1c", "\x0b", "\x0c", "\x1d", "\x1e", "\x85", " ", " ", "\r"):
        hidden = f"# Only the owner adds an entry{sep}PYSEC-2026-1 #1 2026-11-28 looks like a comment\n"
        got_ids, got_problems = acc.entries(hidden, today)
        case(f".deps-accept, an entry hidden in a comment behind U+{ord(sep):04X}: refused", not got_ids
             and len(got_problems) == 1, f"{got_ids} {got_problems}")
    got_ids, got_problems = acc.entries("# c\r\nPYSEC-2021-66 #12 2026-11-30 no fix yet\r\n", today)
    case(".deps-accept, CRLF line ends: read as plain lines", got_ids == ["PYSEC-2021-66"] and not got_problems,
         f"{got_ids} {got_problems}")
    got_ids, got_problems = acc.entries("PYSEC-2021-66\t#12\t2026-11-30\ttabs between fields\n", today)
    case(".deps-accept, tabs between fields: accepted", got_ids == ["PYSEC-2021-66"] and not got_problems,
         f"{got_ids} {got_problems}")
    with tempfile.TemporaryDirectory() as tmp:
        t = pathlib.Path(tmp)
        for f in ("Makefile", ".devflow-stack", "pyproject.toml"):
            shutil.copy(ROOT / f, t / f)
        lib_record.copy_repo(ROOT / "scripts", t / "scripts")
        env = {k: v for k, v in scrubbed_env().items() if k not in ("CI", "GITHUB_ACTIONS")}
        r = subprocess.run([sys.executable, str(t / "scripts" / "deps_accept.py")], cwd=t, env=env,
                           capture_output=True, encoding="utf-8", errors="replace", timeout=60)
        case("no .deps-accept: nothing accepted, nothing printed", r.returncode == 0 and not r.stdout.strip(),
             f"exit {r.returncode}: {r.stdout}{r.stderr}")
        (t / ".deps-accept").write_text(f"﻿# saved with a BOM\nPYSEC-2021-66 #12 "
                                        f"{datetime.date.today() + datetime.timedelta(days=30)} no fix yet\n",
                                        encoding="utf-8")
        r = subprocess.run([sys.executable, str(t / "scripts" / "deps_accept.py")], cwd=t, env=env,
                           capture_output=True, encoding="utf-8", errors="replace", timeout=60)
        case("a current entry, the file saved with a BOM: pip-audit is told to ignore it", r.returncode == 0
             and r.stdout.split() == ["--ignore-vuln", "PYSEC-2021-66"], f"{r.stdout}{r.stderr}")
        # The re-review's M3: through the script, as `make deps` reads the file. A lone CR is a newline to
        # read_text, which would split the comment in two before the line check ever saw it.
        (t / ".deps-accept").write_bytes(f"# only the owner adds an entry\rPYSEC-2021-66 #12 "
                                         f"{datetime.date.today() + datetime.timedelta(days=30)} hidden\n".encode())
        r = subprocess.run([sys.executable, str(t / "scripts" / "deps_accept.py")], cwd=t, env=env,
                           capture_output=True, encoding="utf-8", errors="replace", timeout=60)
        case("an entry behind a lone CR, read by the script itself: refused, nothing ignored", r.returncode == 1
             and not r.stdout.strip() and "U+000D" in r.stderr, f"exit {r.returncode}: {r.stdout}{r.stderr}")
        if not (no_make := missing_tool("make", "run `make deps` with an expired entry")):
            (t / ".deps-accept").write_text("PYSEC-2021-66 #12 2020-01-01 no fix yet\n", encoding="utf-8")
            r = subprocess.run(["make", "-o", "install", "deps"], cwd=t, env=env, capture_output=True,
                               encoding="utf-8", errors="replace", timeout=120)
            case("`make deps` with an expired entry: red before any network, naming it", r.returncode != 0
                 and "expired" in r.stdout + r.stderr and "pip_audit" not in r.stdout,
                 f"exit {r.returncode}: {(r.stdout + r.stderr)[-300:]}")
        else:
            print(f"  NOT-EVALUABLE {no_make}")

    if bad:
        print("test-network-legs FAIL (scripts/net_cache.py, slopsquat_check.py, deps_accept.py):")
        print("\n".join(f"  {b}" for b in bad))
        return 1
    if unjudged:
        print(f"test-network-legs NOT-EVALUABLE: {unjudged}")
        return 2
    print(f"test-network-legs PASS: {count} cases -- an outage on another stack warns with one ledger row a day and "
          "stays CANNOT RUN on python or in CI; .deps-accept waives only whole, current entries; gzip is asked for and read")
    return 0


if __name__ == "__main__":
    sys.exit(main())
