"""
The FINAM model coupling framework.

See also these FINAM book chapters:

* :doc:`/finam-book/usage/coupling_scripts` for writing FINAM coupling scripts.
* :doc:`/finam-book/development/components` for writing FINAM components or model wrappers.
* :doc:`/finam-book/development/adapters` for writing FINAM adapters.

.. toctree::
   :hidden:

   self

Schedule
========

Driver/scheduler for creating and executing coupled model compositions.

.. autosummary::
   :toctree: generated
   :caption: Schedule

    Composition

Software development kit
========================

Implementations of FINAM interfaces for component and adapter development.

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
    TimeDelayAdapter

Grids
=====

Grid specifications for the exchange of spatial data in FINAM.

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

Utilities for grid specifications.

.. autosummary::
   :toctree: generated
   :caption: Grid tools

    CellType
    Location

Data tools
==========

Utilities for data and metadata handling.

.. autosummary::
   :toctree: generated
   :caption: Data tools

    Info
    Mask
    UNITS

Interfaces
==========

Basic interfaces of the FINAM framework.

.. autosummary::
   :toctree: generated
   :caption: Interfaces

    ComponentStatus
    IComponent
    ITimeComponent
    IAdapter
    IInput
    IOutput
    Loggable
    NoBranchAdapter
    NoDependencyAdapter
    ITimeDelayAdapter

Errors
======

FINAM-specific error types.

.. autosummary::
   :toctree: generated
   :caption: Errors

    FinamCircularCouplingError
    FinamConnectError
    FinamDataError
    FinamLogError
    FinamMetaDataError
    FinamNoDataError
    FinamStaticDataError
    FinamStatusError
    FinamTimeError

Subpackages
===========

Built-in components, adapters and tool functions.

.. autosummary::
   :toctree: generated
   :caption: Subpackages

    adapters
    data
    components
    tools

"""
from . import adapters, components, data, interfaces, schedule, sdk, tools
from .data.grid_spec import (
    EsriGrid,
    NoGrid,
    RectilinearGrid,
    UniformGrid,
    UnstructuredGrid,
    UnstructuredPoints,
)
from .data.grid_tools import CellType, Location
from .data.tools import UNITS, Info, Mask
from .errors import (
    FinamCircularCouplingError,
    FinamConnectError,
    FinamDataError,
    FinamLogError,
    FinamMetaDataError,
    FinamNoDataError,
    FinamStaticDataError,
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
    ITimeDelayAdapter,
    Loggable,
    NoBranchAdapter,
    NoDependencyAdapter,
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
    TimeDelayAdapter,
)

try:
    from ._version import __version__
except ModuleNotFoundError:  # pragma: no cover
    # package is not installed
    __version__ = "0.0.0.dev0"

tools.log_helper.add_logging_level("TRACE", 5)
tools.log_helper.add_logging_level("PROFILE", 15)


__all__ = ["__version__"]
__all__ += ["adapters", "components", "data", "interfaces", "schedule", "sdk", "tools"]
__all__ += [
    "IComponent",
    "ITimeComponent",
    "IAdapter",
    "IInput",
    "IOutput",
    "ComponentStatus",
    "Loggable",
    "NoBranchAdapter",
    "NoDependencyAdapter",
    "ITimeDelayAdapter",
]
__all__ += ["Composition"]
__all__ += [
    "Adapter",
    "Component",
    "TimeComponent",
    "TimeDelayAdapter",
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
__all__ += ["UNITS", "Info", "Mask"]
__all__ += [
    "FinamCircularCouplingError",
    "FinamConnectError",
    "FinamDataError",
    "FinamLogError",
    "FinamMetaDataError",
    "FinamNoDataError",
    "FinamStaticDataError",
    "FinamStatusError",
    "FinamTimeError",
]
