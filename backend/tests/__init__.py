"""Backend test suite runner."""

import pytest


def test_imports():
    """Verify all test modules can be imported."""
    import backend.tests.test_health
    import backend.tests.test_auth
    import backend.tests.test_providers
    assert True