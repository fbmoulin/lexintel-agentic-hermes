"""Shared test fixtures.

The mock vector store is a module-level singleton (test-only convenience).
Reset it before every test so suites are order-independent and no indexed
chunks leak between cases. A request-scoped store is a phase-2 item for real use.
"""

import pytest

from app.services.vector_store import reset_mock_vector_store


@pytest.fixture(autouse=True)
def _reset_mock_vector_store():
    reset_mock_vector_store()
    yield
