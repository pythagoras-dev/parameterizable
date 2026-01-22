"""Tests for _extract_params_dict edge cases in json_processor."""
import pytest

from mixinforge.utility_functions.json_processor import (
    _extract_params_dict,
    _Markers,
)


def test_extract_params_dict_missing_dict_in_params():
    """Test that _extract_params_dict raises KeyError when PARAMS lacks DICT mapping."""
    # Create a container with PARAMS that doesn't have DICT
    container = {
        _Markers.PARAMS: {"something_else": 123}
    }

    with pytest.raises(KeyError):
        _extract_params_dict(container)


def test_extract_params_dict_params_dict_not_a_dict():
    """Test that _extract_params_dict raises KeyError when PARAMS.DICT is not a dict."""
    # Create a container with PARAMS.DICT that's not a dict
    container = {
        _Markers.PARAMS: {
            _Markers.DICT: "not_a_dict"
        }
    }

    with pytest.raises(KeyError):
        _extract_params_dict(container)


def test_extract_params_dict_missing_dict_at_root():
    """Test that _extract_params_dict raises KeyError when root has no DICT mapping."""
    # Create a container without PARAMS and without DICT
    container = {"some_key": "some_value"}

    with pytest.raises(KeyError):
        _extract_params_dict(container)


def test_extract_params_dict_root_dict_not_a_dict():
    """Test that _extract_params_dict raises KeyError when root DICT is not a dict."""
    # Create a container with root DICT that's not a dict
    container = {
        _Markers.DICT: ["not", "a", "dict"]
    }

    with pytest.raises(KeyError):
        _extract_params_dict(container)


def test_extract_params_dict_valid_params_path():
    """Test successful extraction via PARAMS -> DICT path."""
    container = {
        _Markers.PARAMS: {
            _Markers.DICT: {"x": 1, "y": 2}
        }
    }

    result = _extract_params_dict(container)
    assert result == {"x": 1, "y": 2}


def test_extract_params_dict_valid_root_path():
    """Test successful extraction via root DICT path."""
    container = {
        _Markers.DICT: {"a": 10, "b": 20}
    }

    result = _extract_params_dict(container)
    assert result == {"a": 10, "b": 20}
