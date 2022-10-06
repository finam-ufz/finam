"""
Specialized data types for exchanges between models/modules.
"""
import copy
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

    def copy(self):
        """Copies the info object"""
        return copy.copy(self)

    def copy_with(self, **kwargs):
        """Copies the info object and sets variables and meta values according to the kwargs"""
        other = copy.copy(self)
        for k, v in kwargs.items():
            if k == "grid":
                other.grid = v
            else:
                other.meta[k] = v

        return other

    def accepts(self, incoming):
        """Tests whether this info can accept/is compatible with an incoming info"""
        if not isinstance(incoming, Info):
            return False

        if self.grid != incoming.grid:
            return False

        for k, v in self.meta.items():
            if k in incoming.meta:
                if incoming.meta[k] != v:
                    return False

        return True

    def __copy__(self):
        """Shallow copy of the info"""
        return Info(grid=self.grid, meta=self.meta)

    def __eq__(self, other):
        """Equality check for two infos"""
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
