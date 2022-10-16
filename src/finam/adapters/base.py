"""
Basic data transformation adapters.
"""
import numpy as np

from .. import AAdapter, NoGrid
from .. import data as fmdata


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

    def _get_data(self, time):
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

    def _get_data(self, time):
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
        d = self.pull_data(time)
        return fmdata.get_data(fmdata.strip_time(d)) * self.scale


class ValueToGrid(AAdapter):
    """Convert a scalar value to a Matrix filled with that value.

    Parameters
    ----------
    grid_spec
        Grid specification.
    """

    def __init__(self, grid):
        super().__init__()
        self.grid = grid
        self._info = None

    def _get_data(self, time):
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
        value = self.pull_data(time)
        return np.full(
            self.grid.data_shape, fmdata.get_magnitude(value), dtype=value.dtype
        ) * fmdata.get_units(value)

    def _get_info(self, info):
        in_info = self.exchange_info(info)
        out_info = in_info.copy_with(grid=self.grid)

        self._info = out_info
        return out_info


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

    def _get_data(self, time):
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
        grid = self.pull_data(time)

        func_result = self.func(fmdata.get_magnitude(grid)) * fmdata.get_units(grid)

        return func_result

    def _get_info(self, info):
        in_info = self.exchange_info(info)
        out_info = in_info.copy_with(grid=NoGrid())
        return out_info
