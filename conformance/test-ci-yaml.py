#!/usr/bin/env python3
"""Assert every CI step actually runs what its name says.

WHY THIS EXISTS. A repair removed two steps from `dep-audit` and left one `run:` key behind. YAML is
permissive: the orphan folded into the preceding step. The result was a step named "Run pip-audit"
whose command was `python3 scripts/check_records.py`. **The dependency audit did not run for an entire
release, and the job was green.** Nobody reads a workflow by parsing it; an external reviewer did.

DUPLICATE KEYS. That orphan was a second `run:` in one step, and YAML resolves a key written twice
by keeping the LAST value without a word -- the first is dead config that still reads as live.
Every mapping in every workflow is checked for a key it holds twice: by PyYAML's loader where
PyYAML is installed, by a line reader otherwise -- the GP root's gate runs this with a system
`python3` that has no PyYAML, and a half that is NOT-EVALUABLE there is a half nobody grades. Both
readers prove themselves on a must-fire and a must-pass sample on every run, and where PyYAML is
present they must agree on every workflow, so the reader a machine without it uses cannot drift.

Stdlib-only except PyYAML, which CI already has. Exit 0 clean, 1 findings, 2 not evaluable here.
"""
import sys, pathlib, re

try:
    import yaml
except ImportError:                                    # noqa: F401
    yaml = None

# STDLIB FALLBACK, and the reason is structural rather than convenient. PyYAML is a dev dependency, dev
# dependencies live in `.venv`, and **an unnamed starter cannot create one** -- `pyproject.toml`
# ships `name = "<PROJECT_NAME>"`, which is not a PEP-508 identifier. So a governance control that
# needs PyYAML could not run in the tree that declares it. Exiting 0 there is a silent pass; exiting
# 2 forever is a gate nobody can pass. **The third option is to not need the dependency.**
#
# This parser handles ONLY the shape GitHub workflows actually use: block mappings, block sequences,
# `|`/`>` scalars. It REFUSES (exit 2) on anchors, flow collections or multi-document files rather
# than guessing -- a parser that quietly mis-reads is worse than one that is absent. Checked against
# PyYAML on every workflow in this tree; the two agree on jobs, step names and step commands.
def _minimal_parse(text: str) -> dict:
    # Refuse only on constructs inside the region actually parsed. The first version of this guard
    # scanned the whole file and tripped on `branches: [main]` in the `on:` block -- a flow sequence
    # this parser never reads. **A guard wider than the thing it guards refuses correct input**, which
    # is how a fallback gets deleted the first week.
    region = text[text.index("\njobs:"):] if "\njobs:" in text else ""
    if re.search(r"^\s*(?:<<:|&\w|\*\w)", region, re.M) or re.search(r"^\s*\w[\w-]*:\s*[\[{]", region, re.M):
        raise ValueError("construct this minimal parser does not handle")
    jobs: dict = {}
    in_jobs = False
    job = None
    step = None
    step_ind = None
    blk = None                      # indent of an open block scalar, or None
    for raw in text.splitlines():
        if blk is not None:
            if raw.strip() and (len(raw) - len(raw.lstrip())) > blk:
                step["run"] += raw.strip() + "\n"
                continue
            blk = None
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        ind = len(raw) - len(raw.lstrip())
        line = raw.strip()
        if ind == 0:
            in_jobs = line.rstrip(":") == "jobs"
            job = step = None
            continue
        if not in_jobs:
            continue
        if ind == 2 and line.endswith(":"):
            job = line[:-1].strip()
            jobs[job] = {"steps": []}
            step = None
            step_ind = None
            continue
        if job is None:
            continue
        # A `- ` only starts a step at the STEP indent. The `prompt: |` block in `issue-agent.yml`
        # contains bullet lines, and treating those as steps invented twelve empty ones -- the parser
        # reading prose as structure, which is the same mistake `wave_check` and the ADR-band check
        # each made once. Anchor on indentation.
        if line.startswith("- ") or line == "-":
            if step_ind is None:
                step_ind = ind
            if ind != step_ind:
                continue
            step = {}
            jobs[job]["steps"].append(step)
            line = line[2:].strip()
            if not line:
                continue
        if ind <= 4 and not line.startswith("- ") and ":" in line and step is not None:
            k = line.split(":", 1)[0].strip()
            if k not in ("name", "run", "uses", "if"):
                step = None                     # left the steps list (e.g. `env:`, `permissions:`)
        if step is None or ":" not in line:
            continue
        k, _, v = line.partition(":")
        k, v = k.strip(), v.strip()
        if k not in ("name", "run", "uses", "if"):
            continue
        if v in ("|", ">", "|-", ">-"):
            step["run"] = ""
            blk = ind
        else:
            # strip an inline comment: `uses: x@sha  # v4` is `x@sha` to YAML.
            if "  #" in v:
                v = v.split("  #")[0].rstrip()
            step[k] = v.strip("'\"")
    return {"jobs": jobs}


def _load(text: str) -> dict:
    if yaml is not None:
        return yaml.safe_load(text)
    return _minimal_parse(text)


DUPLICATE = "duplicate key `{key}` -- YAML keeps the last one silently, so the first is dead config"

if yaml is not None:
    class _UniqueKeyLoader(yaml.SafeLoader):
        """SafeLoader that records (line, key) for every key a mapping holds twice.

        Checked while each mapping is constructed, before PyYAML folds it into a dict and the
        first value is gone. A merge key (`<<: *anchor`) is how YAML overrides on purpose, so the
        keys it brings in are not counted -- only the keys written in the mapping itself.
        """

        def __init__(self, stream: str) -> None:
            super().__init__(stream)
            self.duplicates: list[tuple[int, str]] = []

        def construct_mapping(self, node, deep=False):          # noqa: ANN001, ANN201
            if isinstance(node, yaml.MappingNode):
                seen: set = set()
                for key_node, _value in node.value:
                    if key_node.tag == "tag:yaml.org,2002:merge":
                        continue
                    key = self.construct_object(key_node, deep=deep)
                    try:
                        if key in seen:
                            self.duplicates.append((key_node.start_mark.line + 1,
                                                    str(getattr(key_node, "value", key))))
                        seen.add(key)
                    except TypeError:          # an unhashable key: PyYAML refuses it below
                        pass
            return super().construct_mapping(node, deep=deep)


# The line reader, for where PyYAML is absent. It reads block mappings by indentation: a stack of
# (indent, keys) for the mappings open at the current line; a key at an indent deeper than the top
# opens a nested mapping, one at a shallower indent closes every mapping deeper than it, and each
# `- ` closes the mappings of the item before it, so every sequence item starts a mapping of its own
# (an indentless sequence -- `- ` at its parent key's indent -- included). Comments, blank lines and
# block-scalar bodies (after `|` or `>`) are not read as keys.
# NOT read: the content of flow collections (`{a: 1}`, `[a, b]`; one spanning several lines is
# skipped until its brackets close), explicit `?` keys, a plain scalar continued over several lines,
# and keys YAML equates by type (`on` and `true` are one key to PyYAML, two here). The merge key `<<` is not counted, as in the loader.
_KEY = re.compile(r"""("(?:[^"\\]|\\.)*"|'(?:[^']|'')*'|[^\s#'"\[\]{},&*!|>%@`-][^#]*?|-[^\s#][^#]*?)"""
                  r"\s*:(?:\s+|$)(.*)$")
_QUOTED = re.compile(r""""(?:[^"\\]|\\.)*"|'(?:[^']|'')*'""")
_BLOCK_SCALAR = re.compile(r"^[|>][0-9+-]*\s*(?:#.*)?$")


def _flow_depth(value: str) -> int:
    """How many flow brackets `value` leaves open, quoted text left out."""
    bare = _QUOTED.sub("", value.split(" #")[0])
    return bare.count("[") + bare.count("{") - bare.count("]") - bare.count("}")


def duplicate_keys_by_line(text: str) -> list[tuple[int, str]]:
    """(line, key) for every key written twice in one block mapping of `text`. Stdlib only."""
    found: list[tuple[int, str]] = []
    stack: list[tuple[int, set]] = []          # open mappings, innermost last
    block = None                               # a block scalar's parent column, while in its body
    flow = 0                                   # open flow brackets carried from earlier lines
    for n, raw in enumerate(text.splitlines(), 1):
        ind = len(raw) - len(raw.lstrip(" "))
        if block is not None:
            if not raw.strip() or ind > block:
                continue
            block = None
        if flow > 0:
            flow = max(0, flow + _flow_depth(raw))
            continue
        line = raw.strip()
        if not line:                          # a comment is never a key: `_KEY` refuses `#`
            continue
        if line in ("---", "...") or line.startswith("--- ") or line.startswith("%"):
            stack.clear()
            continue
        col, rest, dash = ind, raw[ind:], None
        while rest == "-" or rest.startswith("- "):   # each `- ` ends the item before it
            dash = col
            while stack and stack[-1][0] > col:
                stack.pop()
            step = len(rest) - len(rest[1:].lstrip(" ")) if rest != "-" else 1
            col, rest = col + step, rest[step:]
        m = _KEY.match(rest)
        if not m:
            value = rest
        else:
            key, value = m.group(1).strip(), m.group(2).strip()
            if key[:1] in "\"'":
                key = key[1:-1]
            while stack and stack[-1][0] > col:
                stack.pop()
            if not stack or stack[-1][0] < col:
                stack.append((col, set()))
            if key != "<<":
                if key in stack[-1][1]:
                    found.append((n, key))
                stack[-1][1].add(key)
        if _BLOCK_SCALAR.match(value):
            # its body is what is indented past its parent: the key, or the `-` of an item that is
            # itself a block scalar (`- |`)
            block = col if m or dash is None else dash
        elif value[:1] in "[{":
            flow = max(0, _flow_depth(value))
    return found


def duplicate_keys(text: str) -> list[tuple[int, str]]:
    """(line, key) for every key written twice in one mapping of `text`: PyYAML where it is
    installed, the line reader otherwise."""
    return duplicate_keys_by_yaml(text) if yaml is not None else duplicate_keys_by_line(text)


def duplicate_keys_by_yaml(text: str) -> list[tuple[int, str]]:
    """(line, key) for every key written twice in one mapping of `text`. Needs PyYAML."""
    loader = _UniqueKeyLoader(text)
    try:
        loader.get_single_data()
    finally:
        loader.dispose()
    return sorted(loader.duplicates)          # in line order, whatever order PyYAML builds in


# Both readers are proven on every run, both ways, before their silence over the workflows means
# anything: the founding shape (a second `run:` in one step), a job id written twice and a key
# repeated in an indentless sequence item must fire; keys shared by sibling mappings and sequence
# items, merge keys and a merge-key override, `key:` lines inside a block scalar (a `- |` item's
# too) or a comment, and a flow mapping spanning lines must not.
MUST_FIRE = ("jobs:\n  audit:\n    runs-on: ubuntu-latest\n    steps:\n"
             "      - name: Run pip-audit\n        run: pip-audit --strict .\n"
             "        run: python3 scripts/check_records.py\n"
             "  audit:\n    runs-on: ubuntu-latest\n    steps:\n    - name: a\n      name: b\n",
             [(7, "run"), (8, "audit"), (12, "name")])
MUST_PASS = ("defaults: &d\n  runs-on: ubuntu-latest\n  timeout-minutes: 5\njobs:\n  a:\n"
             "    <<: *d\n    timeout-minutes: 10\n    steps:\n      - name: one\n        run: |\n"
             "          name: not a key\n          name: nor this\n\n          echo 1\n"
             "      - name: two  # name: a comment\n        run: echo 2\n  b:\n    <<: *d\n"
             "    steps:\n    - name: x\n      with: {a: 1,\n      name: z}\n    - name: y\n"
             "    # name: a comment\n  c:\n    <<: *d\n    <<: *d\n    args:\n      - |\n"
             "        name: p\n        name: q\n      - z\n", [])

# name fragment -> command fragment that MUST appear in that step's run block
# Anchored on the START of the step name, because a substring matcher is how this file first produced
# a false positive: the fragment "test (" matched "Validator self-test (conformance fixtures...)" and
# demanded pytest of a step that correctly runs the validator. A check that cries wolf gets disabled.
EXPECT = {
    "run pip-audit":        "pip-audit",
    "install completeness": "--install",
    "governance records":   "check_records.py",
    "validator self-test":  "--self-test",
    "validator is not a no-op": "--self-test",
    "lint":                 "ruff",
    "type check":           "mypy",
    "test (pytest":         "pytest",
}

def main() -> int:
    root = pathlib.Path(__file__).resolve().parent.parent
    bad, seen = [], 0
    wfs = sorted(list((root / ".github" / "workflows").glob("*.yml"))
                 + list((root / ".github" / "workflows").glob("*.yaml")))
    commands = ""
    readers = [("the line reader", duplicate_keys_by_line)]
    if yaml is not None:
        readers.append(("PyYAML", duplicate_keys_by_yaml))
    for reader, find in readers:
        for sample, want in (MUST_FIRE, MUST_PASS):
            got = find(sample)
            if got != want:
                bad.append(f"the duplicate-key check ({reader}) found {got} in a sample holding "
                           f"{want} -- a checker that cannot tell the two apart says nothing about "
                           "the workflows")
    for wf in wfs:
        # Without PyYAML the fallback parser REFUSES constructs it does not handle -- a test
        # matrix, the most common thing a project adds. A refusal is not a finding: the check
        # could not read the file, so it says which file and exits NOT-EVALUABLE (a traceback
        # would read as "[FAIL] (no output)").
        try:
            doc = _load(wf.read_text(encoding="utf-8"))
        except ValueError as exc:
            print(f"test-ci-yaml NOT-EVALUABLE: {wf.name} uses a construct the stdlib fallback "
                  f"parser does not read ({exc}); install PyYAML (`pip install pyyaml`) to grade it")
            return 2
        rel = wf.relative_to(root).as_posix()
        text = wf.read_text(encoding="utf-8")
        bad += [f"{rel}:{line}: " + DUPLICATE.format(key=key) for line, key in duplicate_keys(text)]
        if yaml is not None and duplicate_keys_by_line(text) != duplicate_keys_by_yaml(text):
            bad.append(f"{rel}: the line reader finds {duplicate_keys_by_line(text)} duplicate "
                       f"key(s) where PyYAML finds {duplicate_keys_by_yaml(text)}. The line reader "
                       "is what grades this file on a machine without PyYAML")
        for job_name, job in (doc.get("jobs") or {}).items():
            for step in job.get("steps") or []:
                name, run = str(step.get("name", "")).lower(), step.get("run")
                if not run:
                    continue
                seen += 1
                commands += run + "\n"
                for frag, must in EXPECT.items():
                    if name.startswith(frag) and must not in run:
                        bad.append(f"{wf.name}: job `{job_name}` step \"{step['name']}\" does not run "
                                   f"`{must}` -- it runs `{run.strip().splitlines()[0][:60]}`")
    # Name<->command agreement misses the two easiest evasions: DELETE the step, or RENAME it and
    # change the command. A required-command set closes that: whatever the steps are called, these
    # must appear somewhere in the workflows.
    REQUIRED = {
        # NOT the bare string "pip-audit" -- that is also present in `pip install pip-audit`, so
        # deleting the step that actually AUDITS still passed. The required fragment has to be the
        # invocation, not the name.
        "pip-audit --strict":        "the dependency CVE audit",
        "check_records.py --install": "install completeness (M0/M1/M2/M4)",
        "check_records.py --self-test": "the validator-is-not-a-no-op proof",
        "conformance/run-all.py":    "the conformance suite",
    }
    for frag, why in REQUIRED.items():
        if frag not in commands:
            bad.append(f"no workflow step anywhere runs `{frag}` -- {why} is not in CI at all. "
                       "Renaming or deleting a step is the easiest way to remove a gate and the "
                       "hardest to notice in a diff")

    # Three documents once named required checks, no two agreed, and none named
    # `install-and-governance` -- so a PR could fail the install and governance gates and merge. One of
    # them required a check called `lint`, which is a STEP inside `test`, not a job: **a required check
    # by a name that never reports blocks nothing while looking like protection.**
    # Branch protection itself lives in GitHub's settings and no shipped test can read it. What CAN be
    # checked is that the documented list and the workflows agree in both directions.
    bp = root / "docs" / "branch-protection.md"
    if not bp.is_file():
        bad.append("no docs/branch-protection.md -- required checks are undocumented, which is how "
                   "three disagreeing lists happened")
    else:
        text = bp.read_text(encoding="utf-8", errors="replace")
        named = set(re.findall(r"^\|\s*\**`([a-z][a-z0-9-]*)`\**\s*\|", text, re.M))
        ci = root / ".github" / "workflows" / "ci.yml"
        if ci.is_file():
            jobs = set((_load(ci.read_text(encoding="utf-8")).get("jobs") or {}).keys())
            for j in sorted(jobs - named):
                bad.append(f"job `{j}` runs in ci.yml but is not in docs/branch-protection.md -- an "
                           "unlisted job is one nobody will mark required")
            for n in sorted(named - jobs):
                bad.append(f"docs/branch-protection.md requires `{n}`, which is not a job in ci.yml. "
                           "A required check that never reports blocks nothing")

    # The fallback parser must agree with PyYAML wherever PyYAML exists. Without this it could drift
    # silently and nobody would know until it ran alone on a machine that had no PyYAML -- a control
    # whose behaviour depends on which interpreter happened to start it.
    if yaml is not None:
        for wf in wfs:
            txt = wf.read_text(encoding="utf-8")
            try:
                mini = _minimal_parse(txt)
            except ValueError:
                continue                       # refused on purpose; that is its contract
            real = yaml.safe_load(txt)
            for jn, jv in (real.get("jobs") or {}).items():
                a = [(x.get("name"), x.get("uses")) for x in (jv.get("steps") or [])]
                b = [(x.get("name"), x.get("uses")) for x in (mini.get("jobs", {}).get(jn, {}).get("steps") or [])]
                if a != b:
                    bad.append(f"{wf.name}: the stdlib fallback parser disagrees with PyYAML on job "
                               f"`{jn}`. The fallback is what runs when PyYAML is absent, so a "
                               "disagreement means this check reports differently on two machines")

    for line in bad:
        print(f"  FAIL {line}")
    print(f"test-ci-yaml {'FAIL' if bad else 'PASS'}: {seen} step(s) checked, {len(bad)} finding(s), "
          f"{len(wfs)} workflow(s) checked for duplicate keys by "
          + ("PyYAML (the line reader agreeing)" if yaml is not None else "the line reader (no PyYAML)"))
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
