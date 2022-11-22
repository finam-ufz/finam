"""
Components that are no simulation models.
Like IO, visualization, pre- and post-processing, etc.

See also book chapter :doc:`/finam-book/usage/known_modules` for a list of
other components that are not included in the core package.

Modules
=======

.. autosummary::
   :toctree: generated

    CallbackComponent
    CallbackGenerator
    CsvReader
    CsvWriter
    DebugConsumer
    DebugPushConsumer
    ParametricGrid
    ScheduleLogger
    SimplexNoise
    StaticCallbackGenerator
    StaticParametricGrid
    StaticSimplexNoise
    TimeTrigger
    UserControl
    WeightedSum
"""

from . import callback, control, debug, generators, mergers, noise, readers, writers
from .callback import CallbackComponent
from .control import TimeTrigger, UserControl
from .debug import DebugConsumer, DebugPushConsumer, ScheduleLogger
from .generators import CallbackGenerator, StaticCallbackGenerator
from .mergers import WeightedSum
from .noise import SimplexNoise, StaticSimplexNoise
from .parametric import ParametricGrid, StaticParametricGrid
from .readers import CsvReader
from .writers import CsvWriter

__all__ = [
    "callback",
    "control",
    "debug",
    "generators",
    "mergers",
    "noise",
    "readers",
    "writers",
]
__all__ += [
    "CallbackComponent",
    "CallbackGenerator",
    "CsvReader",
    "CsvWriter",
    "DebugConsumer",
    "DebugPushConsumer",
    "ParametricGrid",
    "ScheduleLogger",
    "SimplexNoise",
    "StaticCallbackGenerator",
    "StaticParametricGrid",
    "StaticSimplexNoise",
    "TimeTrigger",
    "UserControl",
    "WeightedSum",
]
