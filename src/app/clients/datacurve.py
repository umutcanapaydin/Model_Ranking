"""DeepSWE from Datacurve's own dataset: client + parser (REQ-SRC-012, D-216).

Datacurve publishes the DeepSWE runs as `datacurve/deep-swe-leaderboard` on Hugging Face, under CC BY 4.0. The
dataset is gated, so every read carries the owner's Hugging Face read token. It replaces Epoch's copy of the board
(`epoch_deepswe_external`), which publishes no licence (#265).

The board is one job directory under `raw/jobs/`. The client lists them through the hub's tree API and reads the
newest (a name that starts with its date), so a later job is read without a code change. From that job it reads two
files: the result file, whose `stats.evals` holds one entry a run keyed `<agent>__<model>[__<effort>]__deep-swe`,
with its Pass@1; and the config file, whose `agents` list gives each run the `reasoning_effort` it ran at, if any.
The key names an effort only for a model run at several, so the config is where the others' efforts are stated.
It hands the parser one JSON object holding the job's name and both files, so the build's one-string `RawSource`
holds.

**The token** comes from `HF_TOKEN`, or else from the owner's file (`TOKEN_FILE`, mode 600). It is sent only to
`huggingface.co`: the fetch refuses any other host, on the first URL and on every redirect. It is never logged, put
in an error, stored in the artifact or written to the repository. Without it the source fails, saying where the token
goes; the build then carries the last good rows or says the surface has no evidence (D-216 clause 4).
"""

from __future__ import annotations

import json
import math
import os
import re
import stat
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from app.clients.protocols import SourceError, fetch_bounded
from app.workflows.schema import EFFORT_LEVELS, ScoreRow

SOURCE_NAME = "datacurve_deepswe"
BENCHMARK = "DeepSWE"
METRIC = "% resolved"
DATASET_URL = "https://huggingface.co/datasets/datacurve/deep-swe-leaderboard"
JOBS_URL = "https://huggingface.co/api/datasets/datacurve/deep-swe-leaderboard/tree/main/raw/jobs"
_FILE_URL = "https://huggingface.co/datasets/datacurve/deep-swe-leaderboard/resolve/main/raw/jobs/{job}/{file}"
_TIMEOUT_S = 60.0
#: Where the token is read from, in this order (D-216 clause 3): the variable, else the owner's file.
ENV_VARIABLE = "HF_TOKEN"
TOKEN_FILE = ("Library", "Application Support", "model-ranking", "hf-token")
#: A token as Hugging Face issues one: letters, digits, `_` and `-`. Anything else is refused unread, so a
#: stray line break can never reach a request header, and nothing that is not a token is ever sent.
_TOKEN = re.compile(r"[A-Za-z0-9_-]{8,256}")
#: A job directory: its date first, then a name of path-safe characters (never a `/`).
_JOB = re.compile(r"\d{8}-[A-Za-z0-9._-]+")
#: One part of a run's key, `<agent>__<model>[__<effort>]__deep-swe`: the key is split on `__`.
_PART = re.compile(r"[A-Za-z0-9.-]+(?:_[A-Za-z0-9.-]+)*")
_BENCHMARK_PART = "deep-swe"
#: D-216 clause 2: a run given no effort ran at its model's default setting, and stands at `agentic-coding`'s
#: ranking level (D-194 clause 1), as Epoch's copy of this board recorded Gemini 3.1 Pro's default run.
DEFAULT_EFFORT = "high"


def token_file() -> Path:
    """The owner's token file, under the home directory of the process that reads it."""
    return Path.home().joinpath(*TOKEN_FILE)


def token_available(environ: Mapping[str, str] | None = None, path: Path | None = None) -> bool:
    """Whether a token is set or its file exists, without reading it: the contract test's need (`tests/skips.py`)."""
    environ = os.environ if environ is None else environ
    return bool(environ.get(ENV_VARIABLE)) or (token_file() if path is None else path).exists()


def read_token(environ: Mapping[str, str] | None = None, path: Path | None = None) -> str:
    """The owner's Hugging Face read token, from `HF_TOKEN` or else the owner's file; never echoed."""
    environ = os.environ if environ is None else environ
    path = token_file() if path is None else path
    value = environ.get(ENV_VARIABLE)
    if value is None:
        try:
            held = path.lstat()
        except OSError:
            msg = (f"{SOURCE_NAME}: no Hugging Face read token. The dataset is gated: set {ENV_VARIABLE}, or put the "
                   f"token in {path} (mode 600). D-216")
            raise SourceError(msg) from None
        if not stat.S_ISREG(held.st_mode):
            msg = f"{SOURCE_NAME}: the token file {path} is not a regular file; refused"
            raise SourceError(msg)
        if held.st_mode & (stat.S_IRWXG | stat.S_IRWXO):
            msg = f"{SOURCE_NAME}: the token file {path} can be read by others; refused (chmod 600 {path})"
            raise SourceError(msg)
        try:
            value = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            msg = f"{SOURCE_NAME}: the token file {path} is unreadable"
            raise SourceError(msg) from None
    token = value.strip()
    if _TOKEN.fullmatch(token) is None:
        msg = f"{SOURCE_NAME}: the Hugging Face token in {ENV_VARIABLE} or {path} is not a token; refused"
        raise SourceError(msg)
    return token


class DatacurveClient:
    """Production RawSource for Datacurve's DeepSWE dataset (D-001); the token is read at each fetch."""

    name = SOURCE_NAME
    url = JOBS_URL
    hosts: tuple[str, ...] = ("huggingface.co",)

    def __init__(self, *, token_file: Path | None = None, environ: Mapping[str, str] | None = None) -> None:
        self._token_file = token_file
        self._environ = environ

    def _get(self, url: str, headers: Mapping[str, str]) -> str:
        return fetch_bounded(url, self.name, _TIMEOUT_S, hosts=self.hosts, headers=headers)

    def fetch_raw(self) -> str:
        headers = {"Authorization": f"Bearer {read_token(self._environ, self._token_file)}"}
        try:
            listing: Any = json.loads(self._get(JOBS_URL, headers))
        except json.JSONDecodeError as exc:
            msg = f"{self.name}: the job listing is not JSON: {exc}"
            raise SourceError(msg) from exc
        if not isinstance(listing, list):
            msg = f"{self.name}: the job listing is not a list"
            raise SourceError(msg)
        jobs = [str(entry["path"]).rsplit("/", 1)[-1] for entry in listing
                if isinstance(entry, dict) and entry.get("type") == "directory"
                and str(entry.get("path", "")).startswith("raw/jobs/")]
        dated = [job for job in jobs if _JOB.fullmatch(job)]
        if not dated:
            msg = f"{self.name}: the dataset lists no dated job under raw/jobs/"
            raise SourceError(msg)
        job = max(dated)
        files = {name: self._get(_FILE_URL.format(job=job, file=f"{name}.json"), headers)
                 for name in ("result", "config")}
        return json.dumps({"job": job, **files})


def _object(text: object, what: str, source: str) -> dict[str, Any]:
    try:
        value = json.loads(text) if isinstance(text, str) else None
    except json.JSONDecodeError as exc:
        msg = f"{source}: the {what} is not valid JSON: {exc}"
        raise SourceError(msg) from exc
    if not isinstance(value, dict):
        msg = f"{source}: the {what} is not an object"
        raise SourceError(msg)
    return value


def _stated_efforts(config: dict[str, Any], source: str) -> dict[tuple[str, str], list[str | None]]:
    """(agent, model) -> the effort each of its runs was given; `None` where it was given none."""
    agents = config.get("agents")
    if not isinstance(agents, list):
        msg = f"{source}: the config lists no runs"
        raise SourceError(msg)
    stated: dict[tuple[str, str], list[str | None]] = {}
    for agent in agents:
        if not isinstance(agent, dict):
            continue
        kwargs = agent.get("kwargs")
        effort = kwargs.get("reasoning_effort") if isinstance(kwargs, dict) else None
        key = (str(agent.get("name")), str(agent.get("model_name")))
        stated.setdefault(key, []).append(effort if isinstance(effort, str) else None)
    return stated


def _run(key: object) -> tuple[str, str, str | None] | None:
    """(agent, model, the effort the key names) for a DeepSWE run's key, or None for any other key."""
    parts = key.split("__") if isinstance(key, str) else []
    if len(parts) not in (3, 4) or parts[-1] != _BENCHMARK_PART or not all(_PART.fullmatch(p) for p in parts):
        return None
    return parts[0], parts[1], parts[2] if len(parts) == 4 else None


def _effort(named: str | None, stated: list[str | None] | None) -> str | None:
    """The run's effort: the key's, or else the one its config states, or `high` for a default run (D-216
    clause 2). None when it cannot be known: no run in the config, several and no key, or a word the schema
    does not hold."""
    if named is not None:
        return named if named in EFFORT_LEVELS else None
    if stated is None or len(stated) != 1:
        return None
    (given,) = stated
    if given is None:
        return DEFAULT_EFFORT
    return given if given in EFFORT_LEVELS else None


def _pass_at_1(entry: object) -> float | None:
    if not isinstance(entry, dict):
        return None
    trials, metrics = entry.get("n_trials"), entry.get("metrics")
    if not isinstance(trials, int) or isinstance(trials, bool) or trials <= 0:
        return None
    if not isinstance(metrics, list) or not metrics or not isinstance(metrics[0], dict):
        return None
    mean = metrics[0].get("mean")
    if not isinstance(mean, int | float) or isinstance(mean, bool) or not math.isfinite(mean):
        return None
    return float(mean) * 100.0 if 0.0 <= mean <= 1.0 else None


def parse_datacurve(raw: str, *, source: str = SOURCE_NAME) -> tuple[list[ScoreRow], int]:
    """Parse the client's envelope into one row a run; returns (rows, skipped).

    A run whose Pass@1 is unusable, or whose effort cannot be known, is skipped and counted; a payload that is not
    the board fails the source. Each row links the job's public page, which opens without a token's help.
    """
    envelope = _object(raw, "payload", source)
    job = envelope.get("job")
    if not isinstance(job, str) or _JOB.fullmatch(job) is None:
        msg = f"{source}: the payload names no dated job"
        raise SourceError(msg)
    result = _object(envelope.get("result"), "result file", source)
    stated = _stated_efforts(_object(envelope.get("config"), "config file", source), source)
    stats = result.get("stats")
    evals = stats.get("evals") if isinstance(stats, dict) else None
    if not isinstance(evals, dict) or not evals:
        msg = f"{source}: the result file holds no runs"
        raise SourceError(msg)
    finished = result.get("finished_at")
    run_date = finished[:10] if isinstance(finished, str) and re.match(r"\d{4}-\d{2}-\d{2}", finished) else None
    source_url = f"{DATASET_URL}/tree/main/raw/jobs/{job}"
    best: dict[tuple[str, str, str], ScoreRow] = {}
    skipped = 0
    for key, entry in evals.items():
        run = _run(key)
        score = _pass_at_1(entry)
        if run is None or score is None:
            skipped += 1
            continue
        agent, model, named = run
        effort = _effort(named, stated.get((agent, model)))
        if effort is None:
            skipped += 1
            continue
        row = ScoreRow(
            raw_name=model,
            benchmark=BENCHMARK,
            metric=METRIC,
            score=score,
            harness=agent,
            run_date=run_date,
            cost_total=None,
            source=source,
            source_url=source_url,
            effort=effort,
        )
        if (model, agent, effort) in best:
            skipped += 1
            if row.score <= best[(model, agent, effort)].score:
                continue
        best[(model, agent, effort)] = row
    return list(best.values()), skipped
