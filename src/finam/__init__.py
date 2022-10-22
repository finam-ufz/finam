"""
The FINAM model coupling framework.

.. toctree::
   :hidden:

   self

Schedule
========

.. autosummary::
   :toctree: generated
   :caption: Schedule

    Composition

Software development kit
========================

.. autosummary::
   :toctree: generated
   :caption: Software development kit

    Adapter
    CallbackInput
    CallbackOutput
    Component
    Input
    Output
    TimeComponent

Grids
=====

.. autosummary::
   :toctree: generated
   :caption: Grids

    EsriGrid
    NoGrid
    RectilinearGrid
    UniformGrid
    UnstructuredGrid
    UnstructuredPoints

Grid tools
==========

.. autosummary::
   :toctree: generated
   :caption: Grid tools

    CellType
    Location

Data tools
==========

.. autosummary::
   :toctree: generated
   :caption: Data tools

    Info
    UNITS

Interfaces
==========

.. autosummary::
   :toctree: generated
   :caption: Interfaces

    ComponentStatus
    Loggable
    IComponent
    ITimeComponent
    IAdapter
    IInput
    IOutput
    NoBranchAdapter

Errors
======

.. autosummary::
   :toctree: generated
   :caption: Errors

    FinamDataError
    FinamLogError
    FinamMetaDataError
    FinamNoDataError
    FinamStatusError
    FinamTimeError

Subpackages
===========

.. autosummary::
   :toctree: generated
   :caption: Subpackages

    adapters
    data
    modules
    tools

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
from .data.tools import UNITS, Info
from .errors import (
    FinamDataError,
    FinamLogError,
    FinamMetaDataError,
    FinamNoDataError,
    FinamStatusError,
    FinamTimeError,
)
from .interfaces import (
    ComponentStatus,
    IAdapter,
    IComponent,
    IInput,
    IOutput,
    ITimeComponent,
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
    "IComponent",
    "ITimeComponent",
    "IAdapter",
    "IInput",
    "IOutput",
    "ComponentStatus",
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
__all__ += ["UNITS", "Info"]
__all__ += [
    "FinamDataError",
    "FinamLogError",
    "FinamMetaDataError",
    "FinamNoDataError",
    "FinamStatusError",
    "FinamTimeError",
]
