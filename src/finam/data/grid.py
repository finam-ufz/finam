import numpy as np
import copy


class GridSpec:
    """
    Spatial and element type specification of a grid.
    """

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


class Grid(np.ndarray):
    """
    Grid data structure for exchange between models.
    Can be used in numpy calculations in combination with scalars. E.g.:

    .. code-block:: python

        new_grid = grid_1 + grid_2 * 0.5
    """

    def __new__(cls, spec, no_data=-9999, data=None):
        if data is not None and len(data) != spec.nrows * spec.ncols:
            raise Exception(
                f"Incompatible array length for Grid construction. Expected {spec.nrows * spec.ncols}, got {len(data)}"
            )

        obj = (
            np.asarray(data).view(cls)
            if data is not None
            else np.zeros(spec.nrows * spec.ncols, dtype=spec.dtype).view(cls)
        )

        obj.spec = spec
        obj.no_data = no_data
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return
        self.spec = copy.copy(getattr(obj, "spec", None))
        self.no_data = getattr(obj, "no_data", None)

    @classmethod
    def create_like(cls, other):
        return Grid(copy.copy(other.spec), no_data=other.no_data)

    def contains(self, col, row):
        return 0 <= row < self.spec.nrows and 0 <= col < self.spec.ncols

    def get(self, col, row):
        return self[col + row * self.spec.ncols]

    def set(self, col, row, value):
        self[col + row * self.spec.ncols] = value

    def to_cell(self, x, y):
        spec = self.spec
        col = int((x - spec.xll) / spec.cell_size)
        row = self.spec.nrows - 1 - int((y - spec.yll) / spec.cell_size)
        return col, row

    def to_xy(self, col, row):
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
