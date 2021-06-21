from core.sdk import AAdapter
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


class GridCallback(AAdapter):
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

        if not isinstance(inp, Grid):
            raise Exception(
                f"Unsupported data type in GridCallback: {inp.__class__.__name__}"
            )

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
        if not (isinstance(value, float) or isinstance(value, int)):
            raise Exception(
                f"Unsupported data type in ValueToMatrix: {value.__class__.__name__}"
            )

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
        if not isinstance(grid, Grid):
            raise Exception(
                f"Unsupported data type in MatrixToValue: {grid.__class__.__name__}"
            )

        return self.func(grid.data)
