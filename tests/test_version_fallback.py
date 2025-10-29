import importlib
import types

import pytest


def test_version_fallback_to_unknown(monkeypatch):
    # Patch importlib.metadata.version to raise PackageNotFoundError
    import importlib.metadata as md

    def _raise(_name):
        raise md.PackageNotFoundError

    monkeypatch.setattr(md, "version", _raise, raising=True)

    # Reload the package to execute __init__ with patched metadata.version
    import parameterizable
    parameterizable = importlib.reload(parameterizable)

    assert hasattr(parameterizable, "__version__")
    assert parameterizable.__version__ == "unknown"

    # Reload again after monkeypatch auto-reverts, to restore normal behavior
    parameterizable = importlib.reload(parameterizable)
    assert isinstance(parameterizable.__version__, str)
