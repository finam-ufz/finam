"""Grid definitions."""
# pylint: disable=W0201
import copy

import numpy as np
import numpy.ma as ma


class GridSpec:
    """Spatial and element type specification of a grid."""

    def __init__(self, ncols, nrows, cell_size=1.0, xll=0.0, yll=0.0, dtype=np.float64):
        self.ncols = ncols
        self.nrows = nrows
        self.cell_size = cell_size
        self.xll = xll
        self.yll = yll
        self.dtype = dtype

    def __eq__(self, other):
        return (
            self.nrows == other.nrows
            and self.ncols == other.ncols
            and self.cell_size == other.cell_size
            and self.xll == other.xll
            and self.yll == other.yll
        )


class Grid(ma.MaskedArray):
    """Grid data structure for exchange between models.
    Can be used in numpy calculations in combination with scalars. E.g.:

    .. code-block:: python

        new_grid = grid_1 + grid_2 * 0.5

    Parameters
    ----------
    spec : GridSpec
        Grid specification.
    no_data : float or int, optional
        No data value.
    data : array_like, optional
        The data of the grid.
    """

    def __new__(cls, spec, no_data=-9999, data=None):
        if data is not None and len(data) != spec.nrows * spec.ncols:
            raise Exception(
                f"Incompatible array length for Grid construction. Expected {spec.nrows * spec.ncols}, got {len(data)}"
            )

        obj = (
            ma.masked_values(data, no_data)
            if data is not None
            else ma.masked_values(np.zeros(spec.nrows * spec.ncols, dtype=spec.dtype), no_data)
        )

        obj.spec = spec
        obj.no_data = no_data

        return obj.view(cls)

    def __array_finalize__(self, obj):
        if obj is None:
            return

        ma.MaskedArray.__array_finalize__(self, obj)
        print("__array_finalize__ in: ", type(obj))
        self.spec = copy.copy(getattr(obj, "spec", None))
        self.no_data = getattr(obj, "no_data", None)
        print("__array_finalize__ ", self.spec, self.no_data)

    @classmethod
    def create_like(cls, other):
        """Create grid from other grid.

        Parameters
        ----------
        other : Grid
            Grid to create the new one.

        Returns
        -------
        Grid
            New grid.
        """
        return Grid(copy.copy(other.spec), no_data=other.no_data)

    def contains(self, col, row):
        """Check if given cell is in the grid.

        Parameters
        ----------
        col : int
            Column.
        row : int
            Row.

        Returns
        -------
        bool
            True if cell is in grid.
        """
        return 0 <= row < self.spec.nrows and 0 <= col < self.spec.ncols

    def get(self, col, row):
        """Get value from cell.

        Parameters
        ----------
        col : int
            Column.
        row : int
            Row.

        Returns
        -------
        float or int
            Value.
        """
        return self[col + row * self.spec.ncols]

    def is_masked(self, col, row):
        """Is the cell masked?

        Parameters
        ----------
        col : int
            Column.
        row : int
            Row.

        Returns
        -------
        bool
            Value.
        """
        return self.mask[col + row * self.spec.ncols]

    def set(self, col, row, value):
        """Set value to cell.

        Parameters
        ----------
        col : int
            Column.
        row : int
            Row.
        value : float or int
            Value.
        """
        self[col + row * self.spec.ncols] = value

    def set_masked(self, col, row):
        """Masks a cell.

        Parameters
        ----------
        col : int
            Column.
        row : int
            Row.
        """
        self[col + row * self.spec.ncols] = ma.masked

    def to_cell(self, x, y):
        """Convert coordinates to cell.

        Parameters
        ----------
        x : float
            x coordinate.
        y : float
            y coordinate.

        Returns
        -------
        tuple of int
            Cell.
        """
        spec = self.spec
        col = int((x - spec.xll) / spec.cell_size)
        row = self.spec.nrows - 1 - int((y - spec.yll) / spec.cell_size)
        return col, row

    def to_xy(self, col, row):
        """Convert cell to coordinates.

        Parameters
        ----------
        col : int
            Column.
        row : int
            Row.

        Returns
        -------
        tuple of float
            Coordinates.
        """
        spec = self.spec
        r = self.spec.nrows - 1 - row
        x = spec.xll + spec.cell_size * (col + 0.5)
        y = spec.yll + spec.cell_size * (r + 0.5)
        return x, y

    def __eq__(self, other):
        return (
            self.spec == other.spec
            and self.no_data == other.no_data
            and np.array_equal(self, other)
        )
