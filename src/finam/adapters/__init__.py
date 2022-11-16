"""
Adapters to transform or interpolate data when passed between modules.

See also book chapter :doc:`/finam-book/usage/known_modules` for a list of
other adapters that are not included in the core package.

Base adapters
=============

.. autosummary::
   :toctree: generated

    Callback
    Scale
    ValueToGrid
    GridToValue

Probe adapters
==============

.. autosummary::
   :toctree: generated

    CallbackProbe

Regridding adapters
===================

.. autosummary::
   :toctree: generated

    RegridNearest
    RegridLinear

Statistics adapters
===================

.. autosummary::
   :toctree: generated

    Histogram

Time adapters
=============

.. autosummary::
   :toctree: generated

    IntegrateTime
    LinearTime
    NextTime
    PreviousTime
    StackTime
    OffsetFixed
    OffsetToPush
    OffsetToPull
    TimeCachingAdapter
"""

from . import base, probe, regrid, time
from .base import Callback, GridToValue, Scale, ValueToGrid
from .probe import CallbackProbe
from .regrid import RegridLinear, RegridNearest
from .stats import Histogram
from .time import (
    IntegrateTime,
    LinearTime,
    NextTime,
    OffsetFixed,
    OffsetToPull,
    OffsetToPush,
    PreviousTime,
    StackTime,
    TimeCachingAdapter,
)

__all__ = ["base", "probe", "regrid", "stats", "time"]
__all__ += [
    "Callback",
    "Scale",
    "ValueToGrid",
    "GridToValue",
]
__all__ += ["CallbackProbe"]
__all__ += [
    "RegridNearest",
    "RegridLinear",
]
__all__ += ["Histogram"]
__all__ += [
    "NextTime",
    "PreviousTime",
    "LinearTime",
    "IntegrateTime",
    "StackTime",
    "OffsetFixed",
    "OffsetToPush",
    "OffsetToPull",
    "TimeCachingAdapter",
]
