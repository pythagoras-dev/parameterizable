import importlib



def test_version_fallback_to_unknown(monkeypatch):
    # Patch importlib.metadata.version to raise PackageNotFoundError
    import importlib.metadata as md

    def _raise(_name):
        raise md.PackageNotFoundError

    monkeypatch.setattr(md, "version", _raise, raising=True)

    # Reload the _version_info module first, then the package to execute with patched metadata.version
    import mixinforge._version_info
    import mixinforge
    importlib.reload(mixinforge._version_info)
    parameterizable = importlib.reload(mixinforge)

    assert hasattr(parameterizable, "__version__")
    assert parameterizable.__version__ == "unknown"

    # Reload again after monkeypatch auto-reverts, to restore normal behavior
    importlib.reload(mixinforge._version_info)
    parameterizable = importlib.reload(parameterizable)
    assert isinstance(parameterizable.__version__, str)
