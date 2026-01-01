"""Version information for the mixinforge package."""

from importlib import metadata as _md

try:
    __version__ = _md.version("mixinforge")
except _md.PackageNotFoundError:
    __version__ = "unknown"
