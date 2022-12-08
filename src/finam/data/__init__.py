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
    get_dimensionality
    get_magnitude
    get_units
    has_time_axis
    is_quantified
    prepare
    quantify
    strip_time
    to_datetime
    to_units
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
    get_dimensionality,
    get_magnitude,
    get_units,
    has_time_axis,
    is_quantified,
    prepare,
    quantify,
    strip_time,
    to_datetime,
    to_units,
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
    "get_dimensionality",
    "get_magnitude",
    "get_units",
    "has_time_axis",
    "prepare",
    "quantify",
    "is_quantified",
    "strip_time",
    "to_datetime",
    "to_units",
]
