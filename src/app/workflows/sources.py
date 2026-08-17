"""The one place this project names its external evidence sources (REQ-ING-012).

**Why this module exists, and it is the M6 lesson applied before it could bite again.**
Building the evidence database needs a list of (client, ingest function) pairs. A smoke gate needs
a list of (client, parser) probes. Written independently those are two hand-typed enumerations of
the same five dependencies in two files, and M6 found four separate instances of exactly that shape
— a precedence guard, a YAML wiring predicate, a list of YAML inputs, and a set of smoke-test
endpoints — where every one was missing precisely the member that mattered.

So the list lives here once. `build.py` derives its work from it and `scripts/smoke_deps.py` derives
its probes from it, which means a source cannot be added to the build and forgotten in the gate.

**What this module does NOT solve, stated so nobody reads more into it than is here.** Naming the
sources in one place makes the two consumers agree with each other; it does not make either agree
with reality. That is what `test_sources.py` is for: it walks `src/app/clients/` with `ast` and
fails if a client class exists that this registry neither ingests nor declares a local bundle.
The list of things to check is produced by code, not typed.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass

from app.clients.aider import AiderClient, parse_polyglot
from app.clients.arena import ArenaClient, parse_arena
from app.clients.deepswe import DeepSWEClient
from app.clients.epoch import EpochClient
from app.clients.litellm import LiteLLMClient, parse_pricing
from app.clients.openrouter import OpenRouterClient, parse_models
from app.clients.protocols import RawSource
from app.clients.swebench import SweBenchClient, parse_verified
from app.workflows.ingest import (
    RunContext,
    SourceReport,
    ingest_aider,
    ingest_arena,
    ingest_deepswe,
    ingest_epoch,
    ingest_litellm,
    ingest_openrouter,
    ingest_swebench,
)

IngestFn = Callable[[sqlite3.Connection, RawSource, RunContext], SourceReport]
ParseFn = Callable[[str], tuple[list[object], int]]


@dataclass(frozen=True)
class RemoteSource:
    """One external dependency, named once for every consumer that needs it."""

    name: str
    client: Callable[[], RawSource]
    ingest: IngestFn
    parse: Callable[..., object]
    minimum_rows: int
    """The floor below which a technically-successful fetch is a FAILED dependency.

    A 200 carrying an empty list is the failure mode this number exists for: it passes a status
    check, passes a parser, and produces a database that answers every question with silence.
    """
    required: bool = True
    """Whether the build refuses to produce an artifact at all without this source.

    **Set False only when the artifact is still honest without it**, and understand what that
    costs: a source is the sole evidence for at least one category, so dropping it does not thin
    the answers on that surface, it empties them. An optional source that fails downgrades the
    build to exit 3 with the affected surface named in `required_operator_actions` — never to a
    silent exit 0, and never to a surface that answers with an empty list instead of saying it has
    no evidence.
    """


@dataclass(frozen=True)
class LocalBundle:
    """A source read from an owner-placed local bundle, never fetched at runtime.

    D-101 and the M5 data-boundary invariant make acquisition the operator's job: the bundle is
    downloaded and unpacked out of band, and this project only ever READS the allowlisted files
    inside it. A runtime fetch would be the violation, not the check.

    **These are ingested, not skipped.** M7-W1 found that the build produced an artifact in which
    `agentic-coding` had zero picks on every query, because the pipeline ingested the five remote
    sources and no local bundle at all — leaving M6's Ruling A (both coding answers, neither
    leading) true in the contract and hollow in the data. A bundle that is absent at build time is
    reported like a failed optional source, never omitted in silence.
    """

    name: str
    client_type: type
    ingest: IngestFn
    reason: str

    @property
    def client_class(self) -> str:
        """The class name, derived rather than restated, for the registry-coverage test."""
        return self.client_type.__name__


REMOTE_SOURCES: tuple[RemoteSource, ...] = (
    RemoteSource(
        name="litellm",
        client=LiteLLMClient,
        ingest=ingest_litellm,
        parse=parse_pricing,
        # The feed carries thousands of entries; a hundred is a shape change, not a slow day.
        minimum_rows=100,
    ),
    RemoteSource(
        name="openrouter",
        client=OpenRouterClient,
        ingest=ingest_openrouter,
        parse=parse_models,
        minimum_rows=50,
    ),
    RemoteSource(
        name="swebench",
        client=SweBenchClient,
        ingest=ingest_swebench,
        parse=parse_verified,
        minimum_rows=1,
    ),
    RemoteSource(
        name="aider",
        client=AiderClient,
        ingest=ingest_aider,
        parse=parse_polyglot,
        minimum_rows=1,
    ),
    RemoteSource(
        name="arena",
        client=ArenaClient,
        ingest=ingest_arena,
        parse=parse_arena,
        minimum_rows=1,
        # OPTIONAL by the owner's ruling at M7-W1 (W-024, ADR D-121). The HF datasets-server has
        # been returning HTTP 500 for hours, and making the whole artifact unbuildable by one
        # upstream outage would block the milestone on somebody else's incident. It is optional
        # only because the serving surface DISCLOSES a missing source rather than answering with
        # an empty list — arena is the sole evidence for `assistant`, so without it that surface
        # has nothing to say and must say so.
        required=False,
    ),
)

LOCAL_BUNDLES: tuple[LocalBundle, ...] = (
    LocalBundle(
        name="epoch_swe_bench_verified",
        client_type=EpochClient,
        ingest=ingest_epoch,
        reason="D-101: owner-placed bundle, read from disk; a runtime fetch would breach the boundary",
    ),
    LocalBundle(
        name="epoch_deepswe_external",
        client_type=DeepSWEClient,
        ingest=ingest_deepswe,
        # This one is the sole primary evidence for `agentic-coding`, which is half of the answer
        # Ruling A froze. Without it that surface has nothing to say.
        reason="M5 data boundary: an allowlisted CSV inside the same owner-placed Epoch bundle",
    ),
)
