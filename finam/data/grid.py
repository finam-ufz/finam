import numpy as np
import copy


class GridSpec:
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


class Grid:
    @classmethod
    def create_like(cls, other):
        return Grid(copy.copy(other.spec), no_data=other.no_data)

    def __init__(self, grid_spec, no_data=-9999.0):
        self.spec = grid_spec
        self.no_data = no_data
        self.data = np.zeros(self.spec.nrows * self.spec.ncols, dtype=self.spec.dtype)

    def contains(self, col, row):
        return 0 <= row < self.spec.nrows and 0 <= col < self.spec.ncols

    def get(self, col, row):
        return self.data[col + row * self.spec.ncols]

    def set(self, col, row, value):
        self.data[col + row * self.spec.ncols] = value

    def to_cell(self, x, y):
        spec = self.spec
        col = int((x - spec.xll) / spec.cell_size)
        row = int((y - spec.yll) / spec.cell_size)
        return col, row

    def to_xy(self, col, row):
        spec = self.spec
        x = spec.xll + spec.cell_size * (col + 0.5)
        y = spec.yll + spec.cell_size * (row + 0.5)
        return x, y

    def fill(self, value):
        self.data.fill(value)

    def __eq__(self, other):
        return (
            self.spec == other.spec
            and self.no_data == other.no_data
            and np.array_equal(self.data, other.data)
        )
