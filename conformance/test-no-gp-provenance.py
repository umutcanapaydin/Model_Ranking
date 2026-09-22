#!/usr/bin/env python3
"""A delivery carries no GP council minute. Measured on the tree a project actually receives.

THE OWNER'S RULING (2026-09-22, translated from Turkish): *"keep the provenance -- when experience
arrives from another project later, how else will we know which rule it matches? GP keeps it, but
DevFlow never."* `INSTALL-MANIFEST.md` already withholds GP-INTERNAL FILES. That was never enough:
the files a project does receive carried GP's minutes inside their prose. Measured before the split
existed, on the delivered tree: **676 control-id tokens, 301 version stamps, 46 increment
references and 16 `NEW in vX` markers, across 77 documents.**

A reader with no councils, no cuts and no increments cannot look any of them up. They are noise
with the shape of meaning, which is worse than noise -- it reads like something you were supposed
to know.

WHAT THIS GRADES: the output of `export_project.py`, which now runs `strip_provenance.py` over the
copy. Not the package. The package keeps every citation, because that is how a finding arriving
from the next field harvest is matched to the rule it re-derived.

Conformance fixtures are exempt and they are the only exemption: they carry record frontmatter --
increment numbers included -- ON PURPOSE, because a validator's test input has to look like the
thing it must reject.

Exit: 0 clean · 1 provenance reached the delivery · 2 cannot run (not the distribution package).
"""
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
PKG = HERE.parent
sys.path.insert(0, str(PKG / "scripts"))


def main() -> int:
    if not (PKG / ".gp-distribution").is_file():
        print("test-no-gp-provenance NOT-EVALUABLE: this is an installation, not the distribution "
              "package. There is nothing here to export, and a project's own prose is its own "
              "business.")
        return 2
    try:
        from strip_provenance import TOKEN, FENCE, PRODUCT_VERSION
    except ImportError:
        print("test-no-gp-provenance CANNOT RUN: scripts/strip_provenance.py is missing -- the "
              "control that produces the clean delivery is gone, which is not a pass.")
        return 2

    with tempfile.TemporaryDirectory() as tmp:
        dest = pathlib.Path(tmp) / "delivery"
        r = subprocess.run([sys.executable, str(PKG / "scripts" / "export_project.py"), str(dest)],
                           capture_output=True, text=True, timeout=180)
        if r.returncode != 0:
            print("test-no-gp-provenance CANNOT RUN: the export refused.\n" + r.stdout[-800:])
            return 2

        # v6.0: markdown AND html. The delivered `pipeline-schema.html` carried 118 GP citations
        # and every control globbed `*.md`, so nothing had ever read it. The rewriter does NOT
        # touch HTML -- editing markup with prose rules is how a diagram gets silently mangled --
        # so here the control guards and a human edits. That division is deliberate.
        docs = [p for p in sorted(dest.rglob("*"))
                if p.is_file() and not p.is_symlink()
                and p.suffix in {".md", ".html"}
                and not p.relative_to(dest).as_posix().startswith("conformance/")]
        if not docs:
            print("test-no-gp-provenance FAIL: the delivery holds no documents. An empty derived "
                  "set is a failure, never a vacuous pass.")
            return 1

        # A fenced block is data, not prose -- a worked example may legitimately show a rule id,
        # and the rewriter's edit stops at the fence, so the check must read the same boundary it
        # does. Counting them reported 32 tokens on a clean delivery, every one inside a code
        # sample: a number that would have sent someone editing diagrams.
        findings = []
        for doc in docs:
            fenced = False
            for n, line in enumerate(doc.read_text(errors="replace").split("\n"), 1):
                if FENCE.match(line):
                    fenced = not fenced
                    continue
                if fenced or PRODUCT_VERSION.match(line):   # the product's version, not a citation
                    continue
                for m in TOKEN.finditer(line):
                    findings.append(f"{doc.relative_to(dest)}:{n}: `{m.group(0)}`")
        for f in findings[:20]:
            print(f"  FAIL {f} -- a GP council citation reached the delivery")
        print(f"test-no-gp-provenance {'FAIL' if findings else 'PASS'}: {len(docs)} delivered "
              f"document(s), {len(findings)} GP provenance token(s)")
        return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
