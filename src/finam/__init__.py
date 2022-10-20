"""
The FINAM model coupling framework.
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
    AAdapter,
    AComponent,
    ATimeComponent,
    CallbackInput,
    CallbackOutput,
    Input,
    Output,
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
    "AAdapter",
    "AComponent",
    "ATimeComponent",
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
