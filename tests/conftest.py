"""Test-suite environment declaration.

`app.adapter.main` validates its security configuration at import and, since the Stage-4.0 review,
an unset or unrecognised `APP_ENV` is the STRICT branch — a process that cannot tell where it runs
assumes production. That is the correct default and it is why importing the module in a bare test
environment now raises.

So the suite declares what it is, once, here. **This is a declaration, not a suppression:** the
tests that exercise the strict branch pass `env=` explicitly (`test_api_config.py`) or spawn a real
subprocess with `APP_ENV=production` set, and neither is affected by this line. What it removes is
only the accident of collection order deciding whether the app can be imported at all.
"""

from __future__ import annotations

import os

os.environ.setdefault("APP_ENV", "test")
