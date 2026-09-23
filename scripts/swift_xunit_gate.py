"""Judge a parallel `swift test` run from its xUnit report (`make check-fast`'s Swift leg).

`swift test --parallel` does not print the `Executed N tests, with ...` line `make swift-test` counts,
and in serial mode `--xunit-output` writes nothing, so the two legs read different evidence for the
same facts. This one fails on everything the serial gate fails on: a failure or error, a SKIPPED test
(M16-W1 review M-3: a skip left the count and the manifest intact), and a set of tests that is not
the manifest (D-150). It compares the tests that EXECUTED, not the ones discovered, which is the
stronger reading. A report that is missing, empty or unreadable is a failure (fail closed), and so
is an empty manifest: a comparison with nothing on one side proves nothing.

    python3 scripts/swift_xunit_gate.py <xunit.xml> <manifest.txt> <test-sources-dir>
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def _parse(report: Path) -> ET.Element:
    # The report is the one `swift test` just wrote on this machine from this repository's tests,
    # not data from a network, and the project carries no defusedxml for one local file.
    return ET.parse(report).getroot()  # noqa: S314


#: The calls that let a test end without asserting. Measured 2026-09-23: `swift test --parallel`
#: reports a skipped test as PASSED -- no marker in the output, none in the xUnit report -- so this
#: leg cannot see a skip at run time and reads the sources instead. A text scan can be evaded (an
#: alias, a wrapper); `make check`, serial, sees a skip at run time and stays the merge gate.
SKIP_CALLS: tuple[str, ...] = ("XCTSkip", "XCTExpectFailure")


def skip_calls(sources: Path) -> list[str]:
    """`file:line: call` for every skip-like call in the Swift sources under `sources`."""
    found = []
    for path in sorted(sources.rglob("*.swift")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for call in SKIP_CALLS:
                if call in line.split("//")[0]:
                    found.append(f"{path}:{number}: {call}")
    return found


def _source_problems(sources: Path) -> list[str]:
    if not sources.is_dir():
        return [f"the test sources {sources} are missing; a skip there could not be seen"]
    return [f"{hit} -- the parallel run reports a skip as a pass" for hit in skip_calls(sources)]


def _cases(root: ET.Element) -> tuple[list[str], set[str], int]:
    """(problems, the tests that executed, how many failed) from the report's test cases."""
    found: list[str] = []
    executed: set[str] = set()
    failed = 0
    for case in root.iter("testcase"):
        name = f"{case.get('classname', '')}/{case.get('name', '')}"
        executed.add(name)
        if case.find("failure") is not None or case.find("error") is not None:
            failed += 1
        if case.find("skipped") is not None:
            found.append(f"SKIPPED: {name} -- a skipped test counts as executed (M16-W1 review M-3)")
    for suite in root.iter("testsuite"):
        failed = max(failed, int(suite.get("failures", 0) or 0) + int(suite.get("errors", 0) or 0))
    return found, executed, failed


def problems(report: Path, manifest: Path, sources: Path | None = None) -> list[str]:
    """Everything wrong with this run; empty means it passes."""
    try:
        root = _parse(report)
    except (OSError, ET.ParseError) as exc:
        return [f"the xUnit report is missing or unreadable: {report}: {exc}"]
    try:
        expected = {line.strip() for line in manifest.read_text(encoding="utf-8").splitlines()
                    if line.strip()}
    except OSError as exc:
        return [f"the manifest is unreadable: {manifest}: {exc}"]
    if not expected:
        return [f"the manifest {manifest} is empty; a suite that ran nothing would match it"]

    found, executed, failed = _cases(root)
    if not executed:
        found.append("the report holds no test cases")
    if failed:
        found.append(f"{failed} test(s) failed")
    found += [f"did not run: {name}" for name in sorted(expected - executed)]
    found += [f"ran but is not in the manifest: {name}" for name in sorted(executed - expected)]
    if sources is not None:
        found += _source_problems(sources)
    return found


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__.strip().splitlines()[-1].strip())
        return 2
    report, manifest, sources = Path(argv[0]), Path(argv[1]), Path(argv[2])
    found = problems(report, manifest, sources)
    if found:
        print("swift-test (parallel) FAIL:")
        for line in found[:30]:
            print(f"  {line}")
        return 1
    count = sum(1 for _ in _parse(report).iter("testcase"))
    print(f"swift-test (parallel) PASS: {count} test(s), exactly the ones named in {manifest}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
