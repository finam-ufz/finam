"""
Adapters to transform or interpolate data when passed between modules.

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

    NextTime
    PreviousTime
    LinearTime
    IntegrateTime
"""

from . import base, probe, regrid, time
from .base import Callback, GridToValue, Scale, ValueToGrid
from .probe import CallbackProbe
from .regrid import RegridLinear, RegridNearest
from .time import IntegrateTime, LinearTime, NextTime, PreviousTime

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
    "NextTime",
    "PreviousTime",
    "LinearTime",
    "IntegrateTime",
]
