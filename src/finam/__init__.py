"""
The FINAM model coupling framework.

Subpackages
===========

.. autosummary::

    adapters
    data
    modules
    sdk
    tools
    interfaces
    schedule

Schedule
========

.. currentmodule:: finam.schedule

.. autosummary::

    Composition

Interfaces
==========

.. currentmodule:: finam.interfaces

.. autosummary::

    ComponentStatus
    FinamLogError
    FinamMetaDataError
    FinamNoDataError
    FinamStatusError
    FinamTimeError
    Loggable
    NoBranchAdapter

Software development kit
========================

.. currentmodule:: finam.sdk

.. autosummary::

    Adapter
    CallbackInput
    CallbackOutput
    Component
    Input
    Output
    TimeComponent

Grids
=====

.. currentmodule:: finam.data

.. autosummary::

    EsriGrid
    NoGrid
    RectilinearGrid
    UniformGrid
    UnstructuredGrid
    UnstructuredPoints

Grid tools
==========

.. currentmodule:: finam.data

.. autosummary::

    CellType
    Location

Data tools
==========

.. currentmodule:: finam.data

.. autosummary::

    UNITS
    FinamDataError
    Info
"""
from . import adapters, data, interfaces, modules, schedule, sdk, tools
from .data.grid_spec import (
    EsriGrid,
    NoGrid,
    RectilinearGrid,
    UniformGrid,
    UnstructuredGrid,
    UnstructuredPoints,
)
from .data.grid_tools import CellType, Location
from .data.tools import UNITS, FinamDataError, Info
from .interfaces import (
    ComponentStatus,
    FinamLogError,
    FinamMetaDataError,
    FinamNoDataError,
    FinamStatusError,
    FinamTimeError,
    Loggable,
    NoBranchAdapter,
)
from .schedule import Composition
from .sdk import (
    Adapter,
    CallbackInput,
    CallbackOutput,
    Component,
    Input,
    Output,
    TimeComponent,
)

try:
    from ._version import __version__
except ModuleNotFoundError:  # pragma: no cover
    # package is not installed
    __version__ = "0.0.0.dev0"


__all__ = ["__version__"]
__all__ += ["adapters", "data", "interfaces", "modules", "schedule", "sdk", "tools"]
__all__ += [
    "ComponentStatus",
    "FinamLogError",
    "FinamMetaDataError",
    "FinamNoDataError",
    "FinamStatusError",
    "FinamTimeError",
    "Loggable",
    "NoBranchAdapter",
]
__all__ += ["Composition"]
__all__ += [
    "Adapter",
    "Component",
    "TimeComponent",
    "CallbackInput",
    "CallbackOutput",
    "Input",
    "Output",
]
__all__ += [
    "EsriGrid",
    "NoGrid",
    "RectilinearGrid",
    "UniformGrid",
    "UnstructuredGrid",
    "UnstructuredPoints",
]
__all__ += ["CellType", "Location"]
__all__ += ["UNITS", "FinamDataError", "Info"]
