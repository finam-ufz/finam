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

    Nearest
    Linear

Time adapters
=============

.. autosummary::
   :toctree: generated

    NextValue
    PreviousValue
    LinearInterpolation
    LinearIntegration
"""

from . import base, probe, regrid, time
from .base import Callback, GridToValue, Scale, ValueToGrid
from .probe import CallbackProbe
from .regrid import Linear, Nearest
from .time import LinearIntegration, LinearInterpolation, NextValue, PreviousValue

__all__ = ["base", "probe", "regrid", "time"]
__all__ += [
    "Callback",
    "Scale",
    "ValueToGrid",
    "GridToValue",
]
__all__ += ["CallbackProbe"]
__all__ += [
    "Nearest",
    "Linear",
]
__all__ += [
    "NextValue",
    "PreviousValue",
    "LinearInterpolation",
    "LinearIntegration",
]
