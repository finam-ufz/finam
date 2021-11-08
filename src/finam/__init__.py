"""
A prototype for model coupling - interfaces and driver.
"""

from . import core
from . import adapters
from . import models
from . import modules
from . import data

try:
    from ._version import __version__
except ModuleNotFoundError:  # pragma: nocover
    # package is not installed
    __version__ = "0.0.0.dev0"
