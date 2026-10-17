#!/usr/bin/env python3
"""The three-skips rule of `docs/control-events.csv`: a `review` row that cites a decision restarts it, and every row's kind and wave are validated against the legend.

WHY (DevFlow #16, D4, the owner's ruling of 2026-10-13). `scripts/wave_check.py` turned red at
three skip/bypass rows of one control and stayed red forever: it counted every row the ledger ever
held, with no way to record that the control had been reviewed. Three projects answered with three
different remedies (`review`, `ruling`, `within-scope` rows; a `rejected` kind; free-form waves),
and the script counted none of them. The rule's own text says the control "goes under review (fix
it, re-scope it, or refuse it)": the clearing act is a DECISION. So the review is one row of kind
`review` whose reason cites the ADR or the refusal, and a row that cites nothing counts nothing.

The legend is the `| kind |` table in `docs/warnings.ledger.md` -- read by the script, and
read here too, so the kinds this test uses are the kinds the legend declares (one source). The
cases call `wave_check.ledger_findings(text, legend)` directly, in both directions: three skips
fail; a cited review clears them; an uncited review clears nothing and is itself a finding; three
new skips after a review fail again; a review of another control clears nothing; a bypass counts
like a skip; an unknown kind and a free-form wave are findings; a missing legend fails closed.

Exit: 0 every case behaves - 1 one does not.
"""
import importlib.util
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "wave_check.py"
LEGEND = ROOT / "docs" / "warnings.ledger.md"
HEAD = "control,wave,kind,reason,date\n"
SKIP = 'session-check,issue-{0},skip,"NO-ENVIRONMENT: a reason, with a comma",2026-10-0{0}\n'
REVIEW = 'session-check,issue-9,review,"REVIEWED: the control is right; the cause is fixed -- D-120",2026-10-06\n'
UNCITED = 'session-check,issue-9,review,"REVIEWED: the control is right; the cause is fixed",2026-10-06\n'


def main() -> int:
    spec = importlib.util.spec_from_file_location("wave_check", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for name in ("ledger_findings", "ledger_kinds"):
        if not hasattr(mod, name):
            print(f"test-ledger-kinds FAIL: wave_check has no {name}(); the ledger rules cannot be checked")
            return 1
    kinds = mod.ledger_kinds(LEGEND)
    if not kinds or {"skip", "bypass", "review"} - set(kinds):
        print(f"test-ledger-kinds FAIL: the legend in {LEGEND.relative_to(ROOT)} does not declare "
              f"skip, bypass and review (got {sorted(kinds or [])})")
        return 1

    three = HEAD + "".join(SKIP.format(i) for i in range(1, 4))
    cases = [
        ("two skips pass", HEAD + SKIP.format(1) + SKIP.format(2), None),
        ("three skips fail", three, "review threshold"),
        ("three skips and a review citing an ADR pass", three + REVIEW, None),
        ("a review citing a refusals row passes too", three + REVIEW.replace("D-120", "R-3"), None),
        ("an uncited review clears nothing, and is a finding", three + UNCITED, "cites no decision"),
        ("...the three skips stay red beside it", three + UNCITED, "review threshold"),
        ("three new skips after the review fail again",
         three + REVIEW + "".join(SKIP.format(i) for i in range(4, 7)), "review threshold"),
        ("a review of another control clears nothing", three + REVIEW.replace("session-check", "secrets"),
         "review threshold"),
        ("a bypass counts like a skip",
         HEAD + SKIP.format(1) + SKIP.format(2) + SKIP.format(3).replace(",skip,", ",bypass,"), "review threshold"),
        ("a kind outside the legend is a finding", HEAD + SKIP.format(1).replace(",skip,", ",rejected,"),
         "not in the legend"),
        ("a free-form wave is a finding", HEAD + SKIP.format(1).replace("issue-1", "fix-43"), "is not one of"),
        ("the shapes the legend lists pass",
         HEAD + "".join(SKIP.format(1).replace("issue-1", w).replace("session-check", "ctl-" + w) for w in ("m3-w2", "release", "upgrade-v7.1", "setup")),
         None),
        ("a row too short to be a row is a finding", HEAD + "session-check,issue-1\n", "not a `control,wave,kind"),
    ]
    bad = []
    for name, text, want in cases:
        found = mod.ledger_findings(text, LEGEND)
        ok = (not found) if want is None else any(want in f for f in found)
        if not ok:
            bad.append(f"  {name}: wanted {'green' if want is None else repr(want)}, got {found or 'green'}")
    with tempfile.TemporaryDirectory() as tmp:
        found = mod.ledger_findings(three, pathlib.Path(tmp) / "no-legend.md")
        if not any("fail closed" in f for f in found):
            bad.append(f"  a missing legend must fail closed, got {found or 'green'}")
        stub = pathlib.Path(tmp) / "no-table.md"
        stub.write_text("# ledger\n\nno kind table here\n", encoding="utf-8")
        found = mod.ledger_findings(three, stub)
        if not any("fail closed" in f for f in found):
            bad.append(f"  a legend with no kind table must fail closed, got {found or 'green'}")
    if bad:
        print("test-ledger-kinds FAIL (scripts/wave_check.py ledger_findings):")
        print("\n".join(bad))
        return 1
    print(f"test-ledger-kinds PASS: {len(cases) + 2} cases of the three-skips rule, the review row, "
          f"the kind legend ({', '.join(sorted(kinds))}) and the wave shapes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
