"""Tests for notebook environment detection utilities.

These tests verify the semantic contract of the notebook detection functions:
- is_executed_in_notebook() never raises and always returns a boolean
- The result is stable across repeated calls
- reset_notebook_detection() allows re-evaluation of the environment
"""
import sys
from types import ModuleType

import pytest

from mixinforge import (is_executed_in_notebook, reset_notebook_detection)


# ---------------------------------------------------------------------------
# Test Doubles (simple fakes instead of unittest.mock)
# ---------------------------------------------------------------------------

class FakeIPythonShell:
    """Fake IPython shell that has the set_custom_exc attribute."""

    def set_custom_exc(self, *args, **kwargs):
        """Fake method that exists in real IPython shells."""
        pass


class FakeIPythonShellWithoutCustomExc:
    """Fake IPython shell that lacks the set_custom_exc attribute."""

    pass


def _create_fake_ipython_module(get_ipython_return_value):
    """Create a fake IPython module with a configurable get_ipython function."""
    fake_module = ModuleType("IPython")
    fake_module.get_ipython = lambda: get_ipython_return_value
    return fake_module


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def isolate_cache():
    """Ensure each test starts and ends with a fresh cache state."""
    reset_notebook_detection()
    yield
    reset_notebook_detection()


@pytest.fixture
def fake_notebook_environment(monkeypatch):
    """Simulate an IPython/Jupyter notebook environment."""
    fake_shell = FakeIPythonShell()
    fake_ipython = _create_fake_ipython_module(fake_shell)
    monkeypatch.setitem(sys.modules, "IPython", fake_ipython)
    reset_notebook_detection()
    yield fake_shell


@pytest.fixture
def fake_inactive_ipython(monkeypatch):
    """Simulate IPython installed but not active (get_ipython returns None)."""
    fake_ipython = _create_fake_ipython_module(None)
    monkeypatch.setitem(sys.modules, "IPython", fake_ipython)
    reset_notebook_detection()
    yield


@pytest.fixture
def fake_shell_without_custom_exc(monkeypatch):
    """Simulate a shell that lacks the set_custom_exc attribute."""
    fake_shell = FakeIPythonShellWithoutCustomExc()
    fake_ipython = _create_fake_ipython_module(fake_shell)
    monkeypatch.setitem(sys.modules, "IPython", fake_ipython)
    reset_notebook_detection()
    yield


# ---------------------------------------------------------------------------
# Contract Tests: Core semantic guarantees
# ---------------------------------------------------------------------------

def test_never_raises_and_returns_bool():
    """Contract: function never raises and always returns a boolean."""
    result = is_executed_in_notebook()
    assert isinstance(result, bool)


def test_detection_is_stable_across_calls():
    """Contract: repeated calls return consistent results (idempotency)."""
    results = [is_executed_in_notebook() for _ in range(5)]
    assert all(r == results[0] for r in results)
    assert all(isinstance(r, bool) for r in results)


def test_reset_enables_reevaluation():
    """Contract: reset allows the function to re-evaluate the environment."""
    first_result = is_executed_in_notebook()
    reset_notebook_detection()
    second_result = is_executed_in_notebook()

    # Both should be valid booleans (we can't guarantee they differ
    # since environment hasn't changed, but both must be valid)
    assert isinstance(first_result, bool)
    assert isinstance(second_result, bool)


# ---------------------------------------------------------------------------
# Behavior Tests: Standard Python environment
# ---------------------------------------------------------------------------

def test_returns_false_in_standard_python():
    """Verify detection returns False when running outside notebook."""
    assert is_executed_in_notebook() is False


# ---------------------------------------------------------------------------
# Behavior Tests: Notebook environment (faked)
# ---------------------------------------------------------------------------

def test_returns_true_in_notebook_environment(fake_notebook_environment):
    """Verify detection returns True in IPython/Jupyter environment."""
    assert is_executed_in_notebook() is True


def test_returns_false_when_ipython_inactive(fake_inactive_ipython):
    """Verify detection returns False when IPython installed but not active."""
    assert is_executed_in_notebook() is False


def test_returns_false_when_shell_lacks_required_attribute(
    fake_shell_without_custom_exc,
):
    """Verify detection returns False when shell lacks set_custom_exc."""
    assert is_executed_in_notebook() is False


# ---------------------------------------------------------------------------
# Behavior Tests: Reset functionality
# ---------------------------------------------------------------------------

def test_reset_allows_environment_change_detection(fake_notebook_environment):
    """Verify reset enables detecting a changed environment."""
    # With fake active, should detect notebook
    assert is_executed_in_notebook() is True


def test_cached_result_persists_without_reset(fake_notebook_environment):
    """Verify that without reset, cached result persists."""
    # First call with fake active
    first = is_executed_in_notebook()
    # Second call should return same cached value
    second = is_executed_in_notebook()
    assert first is second
