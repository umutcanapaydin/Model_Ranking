"""Client Protocol boundaries (D-001 / K.1).

All external SDK / API calls live behind a typed Protocol. Production
implementation goes in its own module; a fake implementation lives alongside
for tests.

Example pattern:

    from typing import Protocol

    class ExampleClient(Protocol):
        async def fetch(self, key: str) -> dict[str, str]: ...

    class FakeExampleClient:
        async def fetch(self, key: str) -> dict[str, str]:
            return {"key": key, "source": "fake"}

    class HuaweiExampleClient:
        async def fetch(self, key: str) -> dict[str, str]:
            # real SDK call here
            raise NotImplementedError

When the cloud / vendor changes, swap only the implementation, not the
Protocol. Adapter / workflows never import vendor SDKs directly.
"""
