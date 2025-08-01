"""
Adapters to transform or interpolate data when passed between components.

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

Mask adapters
=============

.. autosummary::
   :toctree: generated

    Masking
    UnMasking

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
    ToCRS
    ToUnstructured

Statistics adapters
===================

.. autosummary::
   :toctree: generated

    Histogram

Time adapters
=============

.. autosummary::
   :toctree: generated

    LinearTime
    NextTime
    PreviousTime
    StackTime
    StepTime
    AvgOverTime
    SumOverTime
    DelayFixed
    DelayToPush
    DelayToPull
    TimeCachingAdapter
"""

from . import base, probe, regrid, time
from .base import Callback, GridToValue, Scale, ValueToGrid
from .mask import Masking, UnMasking
from .probe import CallbackProbe
from .regrid import RegridLinear, RegridNearest, ToCRS, ToUnstructured
from .stats import Histogram
from .time import (
    DelayFixed,
    DelayToPull,
    DelayToPush,
    LinearTime,
    NextTime,
    PreviousTime,
    StackTime,
    StepTime,
    TimeCachingAdapter,
)
from .time_integration import AvgOverTime, SumOverTime

__all__ = ["base", "probe", "regrid", "stats", "time"]
__all__ += [
    "Callback",
    "Scale",
    "ValueToGrid",
    "GridToValue",
]
__all__ += ["Masking", "UnMasking"]
__all__ += ["CallbackProbe"]
__all__ += [
    "RegridNearest",
    "RegridLinear",
    "ToCRS",
    "ToUnstructured",
]
__all__ += ["Histogram"]
__all__ += [
    "NextTime",
    "PreviousTime",
    "LinearTime",
    "IntegrateTime",
    "StackTime",
    "StepTime",
    "DelayFixed",
    "DelayToPush",
    "DelayToPull",
    "TimeCachingAdapter",
]
__all__ += [
    "AvgOverTime",
    "SumOverTime",
]
