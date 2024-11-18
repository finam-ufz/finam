"""
Basic data transformation adapters.
"""

import numpy as np

from ..data.grid_spec import NoGrid
from ..data.tools import get_magnitude, get_units, quantify
from ..errors import FinamMetaDataError
from ..sdk import Adapter
from ..tools.log_helper import ErrorLogger

__all__ = [
    "Callback",
    "Scale",
    "ValueToGrid",
    "GridToValue",
]


class Callback(Adapter):
    """Transform data using a callback.

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        adapter = fm.adapters.Callback(
            callback=lambda data, t: data * 2,
        )

    Parameters
    ----------
    callback : callable
        A callback ``callback(data, time)``, returning the transformed data.
    """

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def _get_data(self, time, target):
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
        d = self.pull_data(time, target)
        return self.callback(d, time)


class Scale(Adapter):
    """Scales the input.

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        adapter = fm.adapters.Scale(scale=0.5)

    Parameters
    ----------
    scale : float
        Scale factor.
    """

    def __init__(self, scale):
        super().__init__()
        self.scale = scale

    def _get_data(self, time, target):
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
        d = self.pull_data(time, target)
        return d * self.scale


class ValueToGrid(Adapter):
    """Convert a scalar value to a Matrix filled with that value.

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        adapter = fm.adapters.ValueToGrid(
            grid=fm.UniformGrid(dims=(10, 20))
        )

        adapter = fm.adapters.ValueToGrid(grid=None)

    Parameters
    ----------
    grid: Grid
        Grid specification to create grid for.
        Can be ``None`` to get it from the target.
    """

    def __init__(self, grid):
        super().__init__()
        self.grid = grid

    def _get_data(self, time, target):
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
        value = self.pull_data(time, target)
        return np.full(self.info.grid_shape, get_magnitude(value))

    def _get_info(self, info):
        up_info = info.copy_with(grid=NoGrid())
        in_info = self.exchange_info(up_info)
        out_info = in_info.copy_with(grid=self.grid or info.grid, use_none=False)

        if info.grid is not None and info.grid != out_info.grid:
            with ErrorLogger(self.logger):
                raise FinamMetaDataError(
                    f"Grid specifications don't match. Target has {info.grid}, expected {out_info.grid}"
                )

        return out_info


class GridToValue(Adapter):
    """Convert a matrix to a scalar value using an aggregation function, e.g. ``numpy.mean``.

    Examples
    --------

    .. testcode:: constructor

        import numpy as np
        import finam as fm

        adapter = fm.adapters.GridToValue(func=np.mean)

    Parameters
    ----------
    func : callable
        A function ``func(data)``, returning the transformed data.
    """

    def __init__(self, func):
        super().__init__()
        self.func = func

    def _get_data(self, time, target):
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
        grid = self.pull_data(time, target)

        func_result = quantify(self.func(get_magnitude(grid)), get_units(grid))

        return func_result

    def _get_info(self, info):
        info = info.copy_with(grid=None)
        in_info = self.exchange_info(info)
        out_info = in_info.copy_with(grid=NoGrid())
        return out_info
