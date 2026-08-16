#!/usr/bin/env python3
"""Assert every CI step actually runs what its name says.

WHY THIS EXISTS. A repair removed two steps from `dep-audit` and left one `run:` key behind. YAML is
permissive: the orphan folded into the preceding step. The result was a step named "Run pip-audit"
whose command was `python3 scripts/check_records.py`. **The dependency audit did not run for an entire
release, and the job was green.** Nobody reads a workflow by parsing it; an external reviewer did.

Stdlib-only except PyYAML, which CI already has. Exit 0 clean, 1 findings, 2 usage error.
"""
import sys, pathlib, re

try:
    import yaml
except ImportError:                                    # noqa: F401
    yaml = None

# STDLIB FALLBACK, and the reason is structural rather than convenient. PyYAML is a dev dependency, dev
# dependencies live in `.venv`, and **the distribution package cannot create one** -- `pyproject.toml`
# ships `name = "<PROJECT_NAME>"`, which is not a PEP-508 identifier (TB-051). So a governance control
# that needs PyYAML cannot run in the package that declares it, and `make conformance` reported
# CANNOT RUN forever. Exiting 0 there would have been the old disease; exiting 2 forever is a gate
# nobody can pass. **The third option is to not need the dependency.**
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
    for wf in wfs:
        doc = _load(wf.read_text(encoding="utf-8"))
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
    # v4.3.2 (audit S7). Name<->command agreement misses the two easiest evasions: DELETE the step,
    # or RENAME it and change the command. An auditor did both and got PASS. A required-command set
    # closes that: whatever the steps are called, these must appear somewhere in the workflows.
    REQUIRED = {
        # NOT the bare string "pip-audit" -- that is also present in `pip install pip-audit`, so
        # deleting the step that actually AUDITS still passed. The required fragment has to be the
        # invocation, not the name.
        "pip-audit --strict":        "the dependency CVE audit",
        "check_records.py --install": "install completeness (M1/M2/M3)",
        "check_records.py --self-test": "the validator-is-not-a-no-op proof (V4C-32)",
        "conformance/run-all.py":    "the conformance suite",
    }
    for frag, why in REQUIRED.items():
        if frag not in commands:
            bad.append(f"no workflow step anywhere runs `{frag}` -- {why} is not in CI at all. "
                       "Renaming or deleting a step is the easiest way to remove a gate and the "
                       "hardest to notice in a diff")

    # v5.0 (DevOps D-3). Three documents named required checks, no two agreed, and none named
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
            for n in sorted(named - jobs - {"governance-contract"}):
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
    print(f"test-ci-yaml {'FAIL' if bad else 'PASS'}: {seen} step(s) checked, {len(bad)} mismatch(es)")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
