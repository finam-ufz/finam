"""
A prototype for model coupling - interfaces and driver.
"""

from . import adapters, core, data, modules

try:
    from ._version import __version__
except ModuleNotFoundError:  # pragma: nocover
    # package is not installed
    __version__ = "0.0.0.dev0"
