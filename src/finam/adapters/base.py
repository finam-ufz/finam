"""
Basic data transformation adapters.
"""
from datetime import datetime

import numpy as np
import xarray as xr

from ..core.sdk import AAdapter
from ..data import NoGrid, assert_type
from ..tools.log_helper import LogError


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
        self.logger.debug("get data")
        if not isinstance(time, datetime):
            with LogError(self.logger):
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
        self.logger.debug("get data")
        if not isinstance(time, datetime):
            with LogError(self.logger):
                raise ValueError("Time must be of type datetime")

        d = self.pull_data(time)
        return d * self.scale


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
        self.logger.debug("get data")
        if not isinstance(time, datetime):
            with LogError(self.logger):
                raise ValueError("Time must be of type datetime")

        value = self.pull_data(time)
        with LogError(self.logger):
            assert_type(self, "input", value, [xr.DataArray])

        data = xr.DataArray(
            np.full(self.grid.data_shape, value.pint.magnitude, dtype=value.dtype)
        ).pint.quantify(value.pint.units)
        return data

    def get_info(self, info):
        self.logger.debug("get info")

        in_info = self.exchange_info(info)
        out_info = in_info.copy_with(grid=self.grid)

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
        self.logger.debug("get data")
        if not isinstance(time, datetime):
            with LogError(self.logger):
                raise ValueError("Time must be of type datetime")

        grid = self.pull_data(time)
        with LogError(self.logger):
            assert_type(self, "input", grid, [xr.DataArray])

        func_result = self.func(grid.pint.magnitude)
        result = xr.DataArray(func_result).pint.quantify(grid.pint.units)

        return result

    def get_info(self, info):
        self.logger.debug("get info")

        in_info = self.exchange_info(info)
        out_info = in_info.copy_with(grid=NoGrid)

        return out_info
