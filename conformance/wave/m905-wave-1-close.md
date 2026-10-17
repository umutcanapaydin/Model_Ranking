---
record_type: wave
id: m905-wave-1-close
status: ratified
date: 2026-08-10
---
# Milestone 905 — Wave 1 close

UNVERSIONED fixture: a close written before records declared `process_version`, in the shape of a
field project's oldest closes. `test-wave-unversioned.py` grades it as history when it predates the
installation (`.gp/installed`'s `installed_on`) or when no marker exists, and requires a refusal
when it is dated on or after the installation, or undated beside a marker.

| # | Check | Evidence | ✅/WAIVED |
|---|---|---|---|
| 1 | Tests green for this wave | `tests/unit/test_quota_read.py:14` run on commit a1b2c3d | ✅ |
| 2 | Reviewed before the close | `docs/reviews/m905-wave-1-review.md` | ✅ |

Filled by: `lead agent` · Date: `2026-08-10` · Wave commit range: `a1b2c3d..f4e5d6c`
