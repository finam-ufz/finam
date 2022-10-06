"""
Specialized data types for exchanges between models/modules.
"""
from .grid_spec import (
    EsriGrid,
    NoGrid,
    RectilinearGrid,
    UniformGrid,
    UnstructuredGrid,
    UnstructuredPoints,
)

__all__ = [
    "assert_type",
    "EsriGrid",
    "NoGrid",
    "RectilinearGrid",
    "UniformGrid",
    "UnstructuredGrid",
    "UnstructuredPoints",
]


class Info:
    """Data info containing grid specification and metadata"""

    def __init__(self, grid=None, meta=None):
        """Creates a data info object.

        Parameters
        ----------
        grid : Grid
            grid specification
        meta : dict
            dictionary of metadata
        """
        self.grid = grid
        self.meta = meta or {}

    def __copy__(self):
        return Info(grid=self.grid, meta=self.meta)

    def __eq__(self, other):
        if not isinstance(other, Info):
            return False

        return self.grid == other.grid and self.meta == other.meta


def assert_type(cls, slot, obj, types):
    """Type assertion."""
    for t in types:
        if isinstance(obj, t):
            return
    raise TypeError(
        f"Unsupported data type for {slot} in {cls.__class__.__name__}: {obj.__class__.__name__}. "
        f"Expected one of [{', '.join([tp.__name__ for tp in types])}]"
    )
