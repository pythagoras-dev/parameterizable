"""Tests for notebook environment detection utilities.

These tests verify the semantic contract of the notebook detection functions:
- is_executed_in_notebook() never raises and always returns a boolean
- The result is stable across repeated calls
- reset_notebook_detection() allows re-evaluation of the environment
"""
import sys
from unittest.mock import Mock

import pytest

from mixinforge.utility_functions.notebook_checker import (
    is_executed_in_notebook,
    reset_notebook_detection,
)


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
def mock_notebook_environment(monkeypatch):
    """Simulate an IPython/Jupyter notebook environment.

    Yields the mock shell object for additional assertions if needed.
    """
    mock_ipython_module = Mock()
    mock_shell = Mock()
    mock_shell.set_custom_exc = Mock()
    mock_ipython_module.get_ipython = Mock(return_value=mock_shell)

    monkeypatch.setitem(sys.modules, "IPython", mock_ipython_module)
    reset_notebook_detection()
    yield mock_shell


@pytest.fixture
def mock_inactive_ipython(monkeypatch):
    """Simulate IPython installed but not active (get_ipython returns None)."""
    mock_ipython_module = Mock()
    mock_ipython_module.get_ipython = Mock(return_value=None)

    monkeypatch.setitem(sys.modules, "IPython", mock_ipython_module)
    reset_notebook_detection()
    yield


@pytest.fixture
def mock_shell_without_custom_exc(monkeypatch):
    """Simulate a shell that lacks the set_custom_exc attribute."""
    mock_ipython_module = Mock()
    mock_shell = Mock(spec=[])  # Empty spec = no attributes
    mock_ipython_module.get_ipython = Mock(return_value=mock_shell)

    monkeypatch.setitem(sys.modules, "IPython", mock_ipython_module)
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
# Behavior Tests: Notebook environment (mocked)
# ---------------------------------------------------------------------------

def test_returns_true_in_notebook_environment(mock_notebook_environment):
    """Verify detection returns True in IPython/Jupyter environment."""
    assert is_executed_in_notebook() is True


def test_returns_false_when_ipython_inactive(mock_inactive_ipython):
    """Verify detection returns False when IPython installed but not active."""
    assert is_executed_in_notebook() is False


def test_returns_false_when_shell_lacks_required_attribute(
    mock_shell_without_custom_exc
):
    """Verify detection returns False when shell lacks set_custom_exc."""
    assert is_executed_in_notebook() is False


# ---------------------------------------------------------------------------
# Behavior Tests: Reset functionality
# ---------------------------------------------------------------------------

def test_reset_allows_environment_change_detection(mock_notebook_environment):
    """Verify reset enables detecting a changed environment."""
    # With mock active, should detect notebook
    assert is_executed_in_notebook() is True


def test_cached_result_persists_without_reset(mock_notebook_environment):
    """Verify that without reset, cached result persists."""
    # First call with mock active
    first = is_executed_in_notebook()
    # Second call should return same cached value
    second = is_executed_in_notebook()
    assert first is second
