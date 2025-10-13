import re

import pytest

import parameterizable


def test_version_exists():
    """
    Test that __version__ attribute exists and is accessible.
    """
    assert hasattr(parameterizable, '__version__')
    assert parameterizable.__version__ is not None


def test_version_is_string():
    """
    Test that __version__ is a string.
    """
    assert isinstance(parameterizable.__version__, str)
    assert len(parameterizable.__version__) > 0


def test_version_follows_semantic_versioning():
    """
    Test that __version__ follows semantic versioning format (X.Y.Z).
    """
    # Basic semantic versioning pattern: major.minor.patch
    # May also include pre-release identifiers (alpha, beta, rc)
    semver_pattern = r'^\d+\.\d+\.\d+(?:[-.]?(?:a|alpha|b|beta|rc|dev)\d*)?$'
    assert re.match(semver_pattern, parameterizable.__version__)


def test_version_accessible_from_metadata():
    """
    Test that __version__ can be accessed and is consistent with importlib.metadata.
    """
    from importlib import metadata
    
    # Test that we can get version from metadata (this is how it's implemented)
    try:
        metadata_version = metadata.version("parameterizable")
        # The __version__ should match what metadata reports
        assert parameterizable.__version__ == metadata_version
    except Exception as e:
        # If metadata lookup fails, at least ensure __version__ exists and is valid
        pytest.fail(f"Could not retrieve version from metadata: {e}")


def test_version_format_compatibility():
    """
    Test that __version__ can be compared and parsed as a version string.
    """
    from packaging import version
    
    # This should not raise an exception
    parsed_version = version.parse(parameterizable.__version__)
    assert parsed_version is not None
    
    # Should be a valid version object
    assert hasattr(parsed_version, 'major')
    assert hasattr(parsed_version, 'minor')
    assert hasattr(parsed_version, 'micro')


def test_version_in_all():
    """
    Test that __version__ is included in the __all__ list.
    """
    assert '__version__' in parameterizable.__all__