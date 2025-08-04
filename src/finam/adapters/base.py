"""
Basic data transformation adapters.
"""

import numpy as np

from ..data.grid_spec import NoGrid
from ..data.tools import Mask, get_magnitude, is_quantified, mask_specified, strip_time
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
    units : UnitLike or None, optional
        Units of the transformed data. Default: None (same as input).
    """

    def __init__(self, callback, units=None):
        super().__init__()
        self.callback = callback
        self.units = units

    def _get_data(self, time, target):
        return self.callback(self.pull_data(time, target), time)

    def _get_info(self, info):
        if self.units is None:
            return self.exchange_info(info)
        in_info = self.exchange_info(info.copy_with(units=None))
        return in_info.copy_with(units=self.units)


class Scale(Adapter):
    """
    Scales the input.

    If given scale is a quantity with units, the output units will be adjusted.

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        adapter = fm.adapters.Scale(scale=0.5)

    Parameters
    ----------
    scale : Numerical or pint.Quantity
        Scale factor.
    """

    def __init__(self, scale):
        super().__init__()
        self.scale_units = scale.units if is_quantified(scale) else None
        self.scale = scale
        self.grid = None

    def _get_data(self, time, target):
        return (
            get_magnitude(strip_time(self.pull_data(time, target), self.grid))
            * self.scale
        )

    def _get_info(self, info):
        if self.scale_units is None:
            in_info = self.exchange_info(info)
            self.grid = in_info.grid or info.grid
            return in_info
        req_units = None if info.units is None else info.units / self.scale_units
        in_info = self.exchange_info(info.copy_with(units=req_units))
        units = None if in_info.units is None else in_info.units * self.scale_units
        self.grid = in_info.grid or info.grid
        return in_info.copy_with(units=units)


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
    grid: :any:`Grid`, optional
        Grid specification to create grid for.
        Will be ``None`` by default to get it from the target.
    mask : :any:`Mask` value or valid boolean mask for :any:`MaskedArray`, optional
        masking specification of the data. Options:
            * :any:`Mask.FLEX`: data can be masked or unmasked
            * :any:`Mask.NONE`: data is unmasked and given as plain numpy array
            * valid boolean mask for MaskedArray

        Will be ``None`` by default to get it from the target.
    """

    def __init__(self, grid=None, mask=None):
        super().__init__()
        self.grid = grid
        self.mask = mask

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
        data = np.full(self.info.grid_shape, get_magnitude(value))
        if mask_specified(self.info.mask):
            return np.ma.array(data, mask=self.info.mask)
        return data

    def _get_info(self, info):
        request = info.copy_with(grid=NoGrid(), mask=None)
        in_info = self.exchange_info(request)
        self.mask = info.mask if self.mask is None else self.mask
        self.grid = info.grid if self.grid is None else self.grid
        out_info = in_info.copy_with(grid=self.grid, mask=self.mask, use_none=False)
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
        return self.func(get_magnitude(grid))

    def _get_info(self, info):
        request = info.copy_with(grid=None, mask=None)
        in_info = self.exchange_info(request)
        out_info = in_info.copy_with(grid=NoGrid(), mask=Mask.NONE)
        return out_info
