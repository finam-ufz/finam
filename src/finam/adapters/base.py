"""
Basic data transformation adapters.
"""
from datetime import datetime

import numpy as np

from ..core.sdk import AAdapter
from ..data import assert_type
from ..data.grid import Grid


class Callback(AAdapter):
    """Transform data using a callback.

    Parameters
    ----------
    callback : callable
        A callback ``callback(data, time)``, returning the transformed data.
    """

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def get_data(self, time):
        """Get the output's data-set for the given time.

        Parameters
        ----------
        time : datetime
            Simulation time to get the data for.

        Returns
        -------
        array_like
            data-set for the requested time.
        """
        if not isinstance(time, datetime):
            raise ValueError("Time must be of type datetime")

        d = self.pull_data(time)
        return self.callback(d, time)


class Scale(AAdapter):
    """Scales the input.

    Parameters
    ----------
    scale : float
        Scale factor.
    """

    def __init__(self, scale):
        super().__init__()
        self.scale = scale

    def get_data(self, time):
        """Get the output's data-set for the given time.

        Parameters
        ----------
        time : datetime
            simulation time to get the data for.

        Returns
        -------
        array_like
            data-set for the requested time.
        """
        if not isinstance(time, datetime):
            raise ValueError("Time must be of type datetime")

        d = self.pull_data(time)
        return d * self.scale


class GridCellCallback(AAdapter):
    """Transform grid data using a per-cell callback.

    Parameters
    ----------
    callback : callable
        A callback ``callback(col, row, data, time)``, returning the transformed cell value.
    """

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def get_data(self, time):
        """Get the output's data-set for the given time.

        Parameters
        ----------
        time : datetime
            simulation time to get the data for.

        Returns
        -------
        array_like
            data-set for the requested time.
        """
        if not isinstance(time, datetime):
            raise ValueError("Time must be of type datetime")

        inp = self.pull_data(time)
        assert_type(self, "input", inp, [Grid])

        out = Grid.create_like(inp)

        for row in range(inp.spec.nrows):
            for col in range(inp.spec.ncols):
                out.set(col, row, self.callback(col, row, inp.get(col, row), time))

        return out


class ValueToGrid(AAdapter):
    """Convert a scalar value to a Matrix filled with that value.

    Parameters
    ----------
    grid_spec
        Grid specification.
    """

    def __init__(self, grid_spec):
        super().__init__()
        self.data = Grid(grid_spec)

    def get_data(self, time):
        """Get the output's data-set for the given time.

        Parameters
        ----------
        time : datetime
            simulation time to get the data for.

        Returns
        -------
        array_like
            data-set for the requested time.
        """
        if not isinstance(time, datetime):
            raise ValueError("Time must be of type datetime")

        value = self.pull_data(time)
        assert_type(self, "input", value, [int, float])

        self.data.fill(value)
        return self.data


class GridToValue(AAdapter):
    """Convert a matrix to a scalar value using an aggregation function, e.g. ``numpy.ma.mean``.

    Parameters
    ----------
    func : callable
        A function ``func(data)``, returning the transformed data.
    """

    def __init__(self, func):
        super().__init__()
        self.func = func

    def get_data(self, time):
        """Get the output's data-set for the given time.

        Parameters
        ----------
        time : datetime
            simulation time to get the data for.

        Returns
        -------
        array_like
            data-set for the requested time.
        """
        if not isinstance(time, datetime):
            raise ValueError("Time must be of type datetime")

        grid = self.pull_data(time)
        assert_type(self, "input", grid, [Grid])

        result = self.func(grid)

        if isinstance(result, np.ndarray):
            result = result.item()

        return result
