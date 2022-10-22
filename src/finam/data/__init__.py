"""
Specialized data types for exchanges between models/modules.

Grids
=====

.. autosummary::
   :toctree: generated

    :noindex: EsriGrid
    :noindex: NoGrid
    :noindex: RectilinearGrid
    :noindex: UniformGrid
    :noindex: UnstructuredGrid
    :noindex: UnstructuredPoints


Grid tools
==========

.. autosummary::
   :toctree: generated

    canonical_data
    check_axes_monotonicity
    check_axes_uniformity
    check_uniformity
    :noindex: CellType
    :noindex: Location
    GridBase
    Grid
    StructuredGrid

Data tools
==========

.. autosummary::
   :toctree: generated

    :noindex: UNITS
    :noindex: Info
    assert_type
    check
    check_quantified
    full
    full_like
    get_data
    get_dimensionality
    get_magnitude
    get_time
    get_units
    has_time
    is_quantified
    quantify
    strip_data
    strip_time
    to_units
    to_xarray
"""

from ..errors import FinamDataError
from . import grid_spec, grid_tools, tools
from .grid_spec import (
    EsriGrid,
    NoGrid,
    RectilinearGrid,
    UniformGrid,
    UnstructuredGrid,
    UnstructuredPoints,
)
from .grid_tools import (
    CellType,
    Grid,
    GridBase,
    Location,
    StructuredGrid,
    canonical_data,
    check_axes_monotonicity,
    check_axes_uniformity,
    check_uniformity,
)
from .tools import (
    UNITS,
    Info,
    assert_type,
    check,
    check_quantified,
    full,
    full_like,
    get_data,
    get_dimensionality,
    get_magnitude,
    get_time,
    get_units,
    has_time,
    is_quantified,
    quantify,
    strip_data,
    strip_time,
    to_units,
    to_xarray,
)

__all__ = ["grid_spec", "grid_tools", "tools"]
__all__ += [
    "EsriGrid",
    "NoGrid",
    "RectilinearGrid",
    "UniformGrid",
    "UnstructuredGrid",
    "UnstructuredPoints",
]
__all__ += [
    "CellType",
    "Grid",
    "GridBase",
    "Location",
    "StructuredGrid",
    "canonical_data",
    "check_axes_monotonicity",
    "check_axes_uniformity",
    "check_uniformity",
]
__all__ += [
    "UNITS",
    "FinamDataError",
    "Info",
    "assert_type",
    "check",
    "check_quantified",
    "full",
    "full_like",
    "get_data",
    "get_dimensionality",
    "get_magnitude",
    "get_time",
    "get_units",
    "has_time",
    "quantify",
    "is_quantified",
    "strip_data",
    "strip_time",
    "to_units",
    "to_xarray",
]
