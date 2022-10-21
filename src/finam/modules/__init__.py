"""
Modules that are no simulation models. Like IO, visualization, pre- and post-processing, etc.

Modules
=======

.. autosummary::
   :toctree: generated

    CallbackComponent
    DebugConsumer
    CallbackGenerator
    WeightedSum
    CsvReader
    ScheduleView
    TimeSeriesView
    CsvWriter
"""

from . import callback, debug, generators, mergers, readers, visual, writers
from .callback import CallbackComponent
from .debug import DebugConsumer
from .generators import CallbackGenerator
from .mergers import WeightedSum
from .readers import CsvReader
from .visual import ScheduleView, TimeSeriesView
from .writers import CsvWriter

__all__ = ["callback", "debug", "generators", "mergers", "readers", "visual", "writers"]
__all__ += [
    "CallbackComponent",
    "DebugConsumer",
    "CallbackGenerator",
    "WeightedSum",
    "CsvReader",
    "ScheduleView",
    "TimeSeriesView",
    "CsvWriter",
]
