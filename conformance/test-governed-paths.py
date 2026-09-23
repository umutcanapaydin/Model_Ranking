#!/usr/bin/env python3
"""Every glob in `.governed-records` must correspond to a path the project actually produces.

WHY THIS EXISTS. `.governed-records` once shipped globbing `docs/wave-checklist-*.md`, while the wave
checklist is written to `docs/plans/m{N}-wave-{W}-close.md` -- the Makefile's own help string says
so. The glob was written from memory. **It matched nothing, and the file looked like a working
control.** A declaration nobody checks against the tree is a guess.

A glob is accepted if it matches a real file OR if its shape appears in the Makefile, AGENTS.md or
README.md as a path the workflow writes. Exit 0 clean, 1 findings.
"""
import sys, pathlib, re, fnmatch

def main() -> int:
    root = pathlib.Path(__file__).resolve().parent.parent
    gr = root / ".governed-records"
    if not gr.is_file():
        print("test-governed-paths FAIL: .governed-records missing -- the paths it adds to the "
              "governed set (records a project writes before they carry frontmatter) go ungraded")
        return 1

    corpus = ""
    for f in ("Makefile", "AGENTS.md", "README.md"):
        p = root / f
        if p.is_file():
            corpus += p.read_text(encoding="utf-8", errors="replace")

    bad, n = [], 0
    for raw in gr.read_text(encoding="utf-8").splitlines():
        g = raw.split("#")[0].strip()
        if not g:
            continue
        n += 1
        # A glob must name a FILE SHAPE, not a directory sweep: a bare `docs/*` would govern
        # whatever happens to be there. Note WHERE this sits -- BEFORE the real-file check, or
        # `docs/*` matches real files, hits `continue` and never reaches this test. **A guard placed
        # downstream of the thing it guards is not a guard.**
        stem = g.split("/")[-1]
        if stem in ("*", "*.md", "*.*") or g.rstrip("/").endswith("*") and len(stem) < 4:
            bad.append(f"`{g}` is a directory sweep, not a record shape -- it would govern whatever "
                       "happens to be there and prove nothing")
            continue
        if list(root.glob(g)):
            continue                                   # matches a real file today
        # Otherwise the workflow must DOCUMENT a concrete path of this shape. Turn the glob into a
        # regex and look for a literal path in the Makefile / AGENTS.md.
        #
        # Not a substring heuristic: one was wrong in BOTH directions -- it rejected the real
        # `docs/plans/m*-wave-*-close.md` and accepted an invented `docs/imaginary-thing-*.md`
        # because "imagin" occurs inside "imagination" in the README. **A fuzzy matcher inside a
        # correctness check is a coin flip wearing a lab coat.**
        rx = re.compile("".join(r"[A-Za-z0-9._{}<>-]*" if ch == "*" else re.escape(ch) for ch in g))
        if rx.search(corpus):
            continue
        bad.append(f"`{g}` matches no file and no Makefile/AGENTS/README path -- written from memory?")

    for b in bad:
        print(f"  FAIL {b}")
    print(f"test-governed-paths {'FAIL' if bad else 'PASS'}: {n} glob(s), {len(bad)} unbacked")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
