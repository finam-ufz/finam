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
    "Info",
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

    def accepts(self, incoming, fail_info):
        """Tests whether this info can accept/is compatible with an incoming info

        Parameters
        ----------
        incoming : Info
            Incoming/source info to check. This is the info from upstream.
        fail_info : dict
            Dictionary that will be filled with failed properties; name: (source, target).

        Returns
        -------
        bool
            Whether the incoming info is accepted
        """
        if not isinstance(incoming, Info):
            fail_info["type"] = (incoming.__class__, self.__class__)
            return False

        success = True
        if self.grid is not None and self.grid != incoming.grid:
            fail_info["grid"] = (incoming.grid, self.grid)
            success = False

        for k, v in self.meta.items():
            if v is not None and k in incoming.meta:
                if incoming.meta[k] != v:
                    fail_info["meta." + k] = (incoming.meta[k], v)
                    success = False

        return success

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
