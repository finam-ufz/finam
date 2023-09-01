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

    check_axes_monotonicity
    check_axes_uniformity
    check_uniformity
    :noindex: CellType
    :noindex: Location


Grid abstract base classes
==========================

.. autosummary::
   :toctree: generated

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
    is_masked_array
    has_masked_values
    filled
    to_masked
    to_compressed
    from_compressed
    check_data_covers_domain
"""

from ..errors import FinamDataError
from . import grid_base, grid_spec, grid_tools, tools
from .grid_base import Grid, GridBase, StructuredGrid
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
    Location,
    check_axes_monotonicity,
    check_axes_uniformity,
    check_uniformity,
)
from .tools import (
    UNITS,
    Info,
    assert_type,
    check,
    check_data_covers_domain,
    check_quantified,
    filled,
    from_compressed,
    full,
    full_like,
    get_dimensionality,
    get_magnitude,
    get_units,
    has_masked_values,
    has_time_axis,
    is_masked_array,
    is_quantified,
    prepare,
    quantify,
    strip_time,
    to_compressed,
    to_datetime,
    to_masked,
    to_units,
)

__all__ = ["grid_base", "grid_spec", "grid_tools", "tools"]
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
__all__ += [
    "is_masked_array",
    "has_masked_values",
    "filled",
    "to_masked",
    "to_compressed",
    "from_compressed",
    "check_data_covers_domain",
]
