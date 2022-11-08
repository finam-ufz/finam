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

Time adapters
=============

.. autosummary::
   :toctree: generated

    ExtrapolateTime
    IntegrateTime
    LinearTime
    NextTime
    PreviousTime
    StackTime
    TimeCachingAdapter
"""

from . import base, probe, regrid, time
from .base import Callback, GridToValue, Scale, ValueToGrid
from .probe import CallbackProbe
from .regrid import RegridLinear, RegridNearest
from .time import (
    ExtrapolateTime,
    IntegrateTime,
    LinearTime,
    NextTime,
    PreviousTime,
    StackTime,
    TimeCachingAdapter,
)

__all__ = ["base", "probe", "regrid", "time"]
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
__all__ += [
    "ExtrapolateTime",
    "NextTime",
    "PreviousTime",
    "LinearTime",
    "IntegrateTime",
    "StackTime",
    "TimeCachingAdapter",
]
