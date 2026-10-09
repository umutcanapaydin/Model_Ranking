"""The owner's judgement sheet (#226, M21-W2): D-188's revisit, read from the owner's own judgement.

D-188 makes our family list the default answer. No board says whether it is the better answer, so the
owner judges a sample: per question, two lists, A and B, one our family list's first five and one the
primary board's own first five, in an order a coin chose and the sheet does not show (its seed is drawn
at random and kept only in the key). He writes A, B or "same" in `choice`. The key, kept apart, says which side was ours; the scorer counts.

D-188 is revisited when the owner prefers the primary board's answer on more questions than ours.

    .venv/bin/python scripts/judgement_sheet.py make --probe rows.json --sheet sheet.csv --key ~/judgement-key.json
    .venv/bin/python scripts/judgement_sheet.py score --sheet sheet.csv --key ~/judgement-key.json

`rows.json` is `scripts/router_probe/JudgementProbe.swift`'s output (`docs/judgement-sheet.md`).
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import random
import secrets

#: The repository: the key is never written inside it (the M21-W2 review's M7).
ROOT = pathlib.Path(__file__).resolve().parents[1]
FIELDS = ["n", "question", "surface", "A", "B", "choice", "note"]


def _inside(path: pathlib.Path, root: pathlib.Path) -> bool:
    """Whether `path` lies inside `root`, by the real files (the second review's M7): the nearest existing
    folder of `path`, or any of its parents, is `root` itself, so a spelling in other letters on a volume
    that ignores case, a `..` or a link is caught."""
    folder = path.resolve().parent
    while not folder.exists():
        folder = folder.parent
    return root.exists() and any(candidate.samefile(root) for candidate in [folder, *folder.parents])


def make(probe: pathlib.Path, out: pathlib.Path, key: pathlib.Path, seed: int | None = None) -> None:
    """Write the blinded sheet and its key. A question the screen answers with cards (no family list) is
    left out: there is nothing to compare. The seed is drawn at random unless one is given, and written
    only into the key, so the sheet and the steps cannot rebuild it (the second review's M7)."""
    if _inside(key, ROOT):
        raise ValueError(f"the key {key} is inside the repository, where it could be committed beside the sheet "
                         "and seen before the owner judges; write it outside (for example ~/judgement-key.json)")
    if seed is None:
        seed = secrets.randbits(32)
    rows = [row for row in json.loads(probe.read_text(encoding="utf-8")) if row.get("family")]
    coin = random.Random(seed)  # noqa: S311 -- the coin's seed is the secret, drawn by `secrets` and kept in the key
    sheet_rows, sides = [], []
    for n, row in enumerate(rows, 1):
        ours_first = coin.random() < 0.5
        first, second = (row["family"], row["primary"]) if ours_first else (row["primary"], row["family"])
        sheet_rows.append({"n": n, "question": row["q"], "surface": row["surface"], "A": " / ".join(first),
                           "B": " / ".join(second), "choice": "", "note": ""})
        sides.append({"question": row["q"], "family": "A" if ours_first else "B",
                      "primary": "B" if ours_first else "A"})
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(sheet_rows)
    key.parent.mkdir(parents=True, exist_ok=True)
    key.write_text(json.dumps({"seed": seed, "sides": sides}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def score(sheet: pathlib.Path, key: pathlib.Path) -> dict[str, object]:
    """Count the owner's choices against the key. A choice is A, B or "same" (any case); a blank one is
    unjudged. `revisit` is D-188's condition: the primary board preferred on more questions than ours."""
    rows = list(csv.DictReader(sheet.open(encoding="utf-8")))
    sides = json.loads(key.read_text(encoding="utf-8"))["sides"]
    if [row["question"] for row in rows] != [side["question"] for side in sides]:
        raise ValueError("the key is for another sheet: its questions differ")
    counts = {"family": 0, "primary": 0, "same": 0, "unjudged": 0}
    for row, side in zip(rows, sides, strict=True):
        choice = row["choice"].strip().upper()
        if not choice:
            counts["unjudged"] += 1
        elif choice in ("SAME", "="):
            counts["same"] += 1
        elif choice == side["family"]:
            counts["family"] += 1
        elif choice == side["primary"]:
            counts["primary"] += 1
        else:
            raise ValueError(f"row {row['n']}: a choice is A, B or same, not {row['choice']!r}")
    return {**counts, "revisit": counts["primary"] > counts["family"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    making = commands.add_parser("make")
    making.add_argument("--probe", type=pathlib.Path, required=True)
    making.add_argument("--sheet", type=pathlib.Path, required=True)
    making.add_argument("--key", type=pathlib.Path, required=True)
    making.add_argument("--seed", type=int, default=None, help="for a test only; the default is drawn at random")
    scoring = commands.add_parser("score")
    scoring.add_argument("--sheet", type=pathlib.Path, required=True)
    scoring.add_argument("--key", type=pathlib.Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "make":
        make(args.probe, args.sheet, args.key, seed=args.seed)
        print(f"wrote {args.sheet} and {args.key}; keep the key out of sight until the sheet is filled")
    else:
        print(json.dumps(score(args.sheet, args.key)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
