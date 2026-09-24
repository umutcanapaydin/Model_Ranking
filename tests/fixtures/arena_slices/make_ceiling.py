"""Writes `ceiling.parquet`: 96 distinct 1 MiB model names in one plain-encoded column chunk.

pyarrow decodes a whole column chunk before any check in Python runs, so reading this file needs
about 96 MiB whatever the batch size, while the file itself is a few kilobytes. The memory-ceiling
test reads it (M17-W2, D-165). It is committed rather than built in the test because building it
takes the test process past 600 MB, and on Linux a child's `ru_maxrss` starts from its parent's
peak (re-review 2, BLOCKING-R2-1). Run once from the repository root with the project's venv:

    .venv/bin/python tests/fixtures/arena_slices/make_ceiling.py
"""

import pathlib

import pyarrow as pa
import pyarrow.parquet as pq

body = "a" * (2**20 - 8)
rows = 96
pq.write_table(
    pa.table({
        "model_name": pa.array([f"{i:08d}{body}" for i in range(rows)]),
        "rating": [1200.0] * rows,
        "category": ["multi_turn"] * rows,
        "leaderboard_publish_date": ["2026-09-13"] * rows,
    }),
    pathlib.Path(__file__).with_name("ceiling.parquet"),
    compression="zstd",
    use_dictionary=False,
)
