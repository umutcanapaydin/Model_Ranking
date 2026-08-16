"""Epoch bundle acquisition-clock staleness command (REQ-ING-010).

This clock records when the local bundle was acquired and verified. It never
becomes a benchmark evaluation date; selected evidence age remains row-owned.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

from app.clients.epoch import EPOCH_BUNDLE_URL, validate_last_verified
from app.clients.protocols import SourceError

SOURCE_ID = "epoch-benchmark-data"
SCHEMA_VERSION = 1
# The ONE committed acquisition clock. W4 review BLOCKING-3: the ingest path carried a
# hardcoded `--last-verified` default while CI checked this file, so re-acquiring the
# bundle and updating the file left the data stamped with the old date and CI green.
# Anything that stamps Epoch data reads the clock from here.
EPOCH_SOURCE_PATH = Path(__file__).resolve().parents[3] / "data" / "epoch-source.yaml"


@dataclass(frozen=True)
class EpochSourceDoc:
    """Committed acquisition clock and cadence window for the local Epoch bundle."""

    staleness_days: int
    source_url: str
    last_verified: str


def parse_epoch_source_doc(raw: str) -> EpochSourceDoc:
    """Parse authored source metadata; malformed configuration fails loudly."""
    try:
        doc = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise SourceError(f"{SOURCE_ID}: unparseable YAML: {exc}") from exc
    if not isinstance(doc, dict) or set(doc) != {"schema", "staleness_days", "source"}:
        raise SourceError(f"{SOURCE_ID}: expected schema/staleness_days/source")
    if doc["schema"] != SCHEMA_VERSION:
        raise SourceError(f"{SOURCE_ID}: schema must be {SCHEMA_VERSION}")
    window = doc["staleness_days"]
    if isinstance(window, bool) or not isinstance(window, int) or window <= 0:
        raise SourceError(f"{SOURCE_ID}: staleness_days must be a positive integer")
    source = doc["source"]
    if not isinstance(source, dict) or set(source) != {"id", "source_url", "last_verified"}:
        raise SourceError(f"{SOURCE_ID}: source metadata is incomplete")
    if source["id"] != SOURCE_ID:
        raise SourceError(f"{SOURCE_ID}: source id must be {SOURCE_ID!r}")
    if source["source_url"] != EPOCH_BUNDLE_URL:
        raise SourceError(f"{SOURCE_ID}: source_url must be the documented Epoch bundle")
    raw_verified = source["last_verified"]
    verified_value = raw_verified.isoformat() if isinstance(raw_verified, dt.date) else raw_verified
    verified = validate_last_verified(verified_value, source_name=SOURCE_ID)
    return EpochSourceDoc(window, source["source_url"], verified)


def check_staleness(raw: str, today: dt.date) -> list[str]:
    """Return one CI message when the acquisition clock exceeds its data-owned window."""
    doc = parse_epoch_source_doc(raw)
    age = (today - dt.date.fromisoformat(doc.last_verified)).days
    if age <= doc.staleness_days:
        return []
    return [
        f"{SOURCE_ID}: last_verified {doc.last_verified} is {age} days old "
        f"(window {doc.staleness_days}) — re-acquire {doc.source_url}"
    ]


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Exit codes match the source-staleness contract: 0/1/2."""
    parser = argparse.ArgumentParser(prog="epoch", description=__doc__)
    parser.add_argument("--check-staleness", metavar="EPOCH_SOURCE_YAML", required=True)
    parser.add_argument("--today", default=None, help="YYYY-MM-DD (tests/CI determinism)")
    args = parser.parse_args(argv)
    path = Path(args.check_staleness)
    if not path.is_file():
        print(f"error: no such file: {path}", file=sys.stderr)
        return 2
    try:
        today = (
            dt.date.fromisoformat(args.today) if args.today else dt.datetime.now(tz=dt.UTC).date()
        )
    except ValueError:
        print(f"error: --today is not YYYY-MM-DD: {args.today!r}", file=sys.stderr)
        return 2
    try:
        messages = check_staleness(path.read_text(encoding="utf-8"), today)
    except (OSError, UnicodeError, SourceError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    for message in messages:
        print(f"STALE: {message}")
    if messages:
        print("Epoch bundle acquisition is stale — re-acquire and verify it before ingestion.")
        return 1
    print("Epoch bundle acquisition is within the staleness window")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


def committed_last_verified(path: Path = EPOCH_SOURCE_PATH) -> str:
    """The acquisition date the repository commits to, for anything that stamps data.

    Fails loud if the committed record is missing or malformed — a stamp invented by a
    default argument is exactly the drift BLOCKING-3 found.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SourceError(f"{SOURCE_ID}: committed acquisition record unreadable: {exc}") from exc
    return parse_epoch_source_doc(raw).last_verified
