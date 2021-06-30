"""
Basic data transformation adapters.
"""

from core.sdk import AAdapter
from data import assert_type
from data.grid import Grid


class Callback(AAdapter):
    """
    Transform data using a callback.
    """

    def __init__(self, callback):
        """
        Create a new Callback generator.

        :param callback: A callback ``callback(data, time)``, returning the transformed date.
        """
        super().__init__()
        self.callback = callback

    def get_data(self, time):
        return self.callback(self.pull_data(time), time)


class GridCellCallback(AAdapter):
    """
    Transform grid data using a per-cell callback.
    """

    def __init__(self, callback):
        """
        Create a new Callback generator.

        :param callback: A callback ``callback(col, row, data, time)``, returning the transformed cell value.
        """
        super().__init__()
        self.callback = callback

    def get_data(self, time):
        inp = self.pull_data(time)
        assert_type(self, "input", inp, [Grid])

        out = Grid.create_like(inp)

        for row in range(inp.spec.nrows):
            for col in range(inp.spec.ncols):
                out.set(col, row, self.callback(col, row, inp.get(col, row), time))

        return out


class ValueToGrid(AAdapter):
    """
    Convert a scalar value to a Matrix filled with that value.
    """

    def __init__(self, grid_spec):
        super().__init__()
        self.data = Grid(grid_spec)

    def get_data(self, time):
        value = self.pull_data(time)
        assert_type(self, "input", value, [int, float])

        self.data.fill(value)
        return self.data


class GridToValue(AAdapter):
    """
    Convert a matrix to a scalar value using an aggregation function, e.g. ``numpy.mean``.
    """

    def __init__(self, func):
        super().__init__()
        self.func = func

    def get_data(self, time):
        grid = self.pull_data(time)
        assert_type(self, "grid", grid, [Grid])

        return self.func(grid.data)
