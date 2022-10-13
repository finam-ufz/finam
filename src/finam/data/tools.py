"""Data tools for FINAM."""
import copy

import numpy as np
import pandas as pd

# isort: off
import xarray as xr

# to be able to read unit attributes following the CF conventions
# pylint: disable-next=W0611
import cf_xarray.units  # must be imported before pint_xarray
import pint_xarray
import pint

# isort: on

from ..core.interfaces import FinamMetaDataError
from .grid_spec import GridBase, NoGrid
from .grid_tools import Grid, StructuredGrid

# set default format to cf-convention for pint.dequantify
# some problems with degree_Celsius and similar here
pint_xarray.unit_registry.default_format = "~cf"

UNITS = pint_xarray.unit_registry


class FinamDataError(Exception):
    """Error for wrong data in FINAM."""


def _extract_units(xdata):
    """
    extract the units of an array

    If ``xdata.data`` is not a quantity, the units are ``None``
    """
    try:
        return xdata.data.units
    except AttributeError:
        return None


def _gen_dims(ndim, info, time=None):
    """
    Generate dimension names.

    Parameters
    ----------
    ndim : int
        Number of dimensions.
    info : Info
        Info associated with the data.
    time : datetime or None, optional
        Timestamp for the data, by default None

    Returns
    -------
    list
        Dimension names.
    """
    # create correct dims (time always first)
    dims = ["time"] if time else []
    if isinstance(info.grid, NoGrid):
        # xarray has dim_0, dim_1 ... as default names
        dims += [f"dim_{i}" for i in range(ndim)]
    elif isinstance(info.grid, StructuredGrid):
        dims += (
            list(reversed(info.grid.axes_names))
            if info.grid.axes_reversed
            else list(info.grid.axes_names)
        )
    else:
        dims += ["id"]
    return dims


def to_xarray(data, name, info, time=None):
    """
    Convert data to a xarray.DataArray.

    Parameters
    ----------
    data : arraylike
        The input data.
    name : str
        Name of the data.
    info : Info
        Info associated with the data.
    time : datetime or None, optional
        Timestamp for the data, by default None

    Returns
    -------
    DataArray
        The converted data.

    Raises
    ------
    FinamDataError
        If the data doesn't match its info.
    """
    if isinstance(data, xr.DataArray):
        check(data, name, info, time)
        return data
    data = np.asarray(data)
    # check correct data size
    if isinstance(info.grid, Grid):
        if data.size != info.grid.data_size:
            raise FinamDataError("to_xarray: data size doesn't match grid size.")
        # reshape flat arrays
        data = data.reshape(info.grid.data_shape, order=info.grid.order)
    # generate quantified DataArray
    out_array = xr.DataArray(
        name=name,
        data=data[np.newaxis, ...] if time else data,
        dims=_gen_dims(np.ndim(data), info, time),
        coords=dict(time=[pd.Timestamp(time)]) if time else None,
        attrs=info.meta,
    )
    return (
        out_array.pint.quantify()
        if "units" in info.meta
        else out_array.pint.quantify("")
    )


def has_time(xdata):
    """
    Check if the data array has a timestamp.

    Parameters
    ----------
    xdata : DataArray
        The given data array.

    Returns
    -------
    bool
        Wether the data has a timestamp.
    """
    check_quantified(xdata, "has_time")
    return "time" in xdata.coords


def get_time(xdata):
    """
    Get the timestamps of a data array.

    Parameters
    ----------
    xdata : DataArray
        The given data array.

    Returns
    -------
    list of datetime or None
        timestamps of the data array.
    """
    if has_time(xdata):
        return list(pd.to_datetime(xdata["time"]).to_pydatetime())
    return None


def get_magnitude(xdata):
    """
    Get magnitude of given data.

    Parameters
    ----------
    xdata : DataArray
        The given data array.

    Returns
    -------
    numpy.ndarray
        Magnitude of given data.
    """
    check_quantified(xdata, "get_magnitude")
    return xdata.data.magnitude


def get_data(xdata):
    """
    Get quantified data.

    Parameters
    ----------
    xdata : DataArray
        The given data array.

    Returns
    -------
    pint.Quantity
        Quantified data.
    """
    check_quantified(xdata, "get_data")
    return xdata.data


def get_units(xdata):
    """
    Get units of the data.

    Parameters
    ----------
    xdata : DataArray
        The given data array.

    Returns
    -------
    pint.Unit
        Units of the data.
    """
    check_quantified(xdata, "get_units")
    return xdata.pint.units


def get_dimensionality(xdata):
    """
    Get dimensionality of the data.

    Parameters
    ----------
    xdata : DataArray
        The given data array.

    Returns
    -------
    pint.UnitsContainer
        Dimensionality of the data.
    """
    check_quantified(xdata, "get_dimensionality")
    return xdata.pint.dimensionality


def to_units(xdata, units):
    """
    Convert data to given units.

    Parameters
    ----------
    xdata : DataArray
        The given data array.
    units : str or pint.Unit
        Desired units.

    Returns
    -------
    DataArray
        Converted data.
    """
    check_quantified(xdata, "to_units")
    return xdata.pint.to(pint.Unit(units))


def full_like(xdata, value):
    """
    Return a new DataArray with the same shape and type as a given object.

    Parameters
    ----------
    xdata : DataArray
        The reference object in input.
    value : scalar
        Value to fill the new object with before returning it.

    Returns
    -------
    DataArray
        New object with the same shape and type as other,
        with the data filled with fill_value.
        Coords will be copied from other.
    """
    check_quantified(xdata, "full_like")
    return xr.full_like(xdata.pint.dequantify(), value).pint.quantify()


def full(value, name, info, time=None):
    """
    Return a new DataArray of given info, filled with given value.

    Parameters
    ----------
    value : scalar
        Value to fill the new object with before returning it.
    name : str
        Name of the data.
    info : Info
        Info associated with the data.
    time : datetime or None, optional
        Timestamp for the data, by default None

    Returns
    -------
    DataArray
        The converted data.
    """
    shape = info.grid.data_shape if isinstance(info.grid, Grid) else tuple()
    return to_xarray(np.full(shape, value), name, info, time)


def check(xdata, name, info, time=None):
    """
    Check if data matches given info.

    Parameters
    ----------
    xdata : DataArray
        The given data array.
    name : str
        Name of the data.
    info : Info
        Info associated with the data.
    time : datetime or None, optional
        Timestamp for the data, by default None

    Raises
    ------
    FinamDataError
        If data doesn't match given info.
    """
    if not isinstance(xdata, xr.DataArray):
        raise FinamDataError("check: given data is not a xarray.DataArray.")
    check_quantified(xdata, "check")
    if name != xdata.name:
        raise FinamDataError("check: given data has wrong name.")
    if time is not None:
        if not has_time(xdata):
            raise FinamDataError("check: given data should hold a time.")
        if time != get_time(xdata)[0]:
            raise FinamDataError("check: given data has wrong time.")
        if isinstance(info.grid, Grid) and xdata.shape[1:] != info.grid.data_shape:
            raise FinamDataError("check: given data has wrong shape.")
    elif has_time(xdata):
        raise FinamDataError("check: given data shouldn't hold a time.")
    elif isinstance(info.grid, Grid) and xdata.shape != info.grid.data_shape:
        raise FinamDataError("check: given data has wrong shape.")
    dims = _gen_dims(len(xdata.dims) - (1 if time else 0), info, time)
    if dims != list(xdata.dims):
        raise FinamDataError("check: given data has wrong dimensions.")
    # pint_xarray will remove the "units" entry in the data attributes
    meta = copy.copy(info.meta)
    meta.pop("units", None)
    if meta != xdata.attrs:
        raise FinamDataError(
            f"check: given data has wrong meta data.\nData: {xdata.attrs}\nMeta: {meta}"
        )
    # check units
    if "units" in info.meta and UNITS.Unit(info.units) != get_units(xdata):
        raise FinamDataError("check: given data has wrong units.")


def is_quantified(xdata):
    """
    Check if data is a quantified DataArray.

    Parameters
    ----------
    xdata : DataArray
        The given data array.

    Returns
    -------
    bool
        Wether the data is a quantified DataArray.
    """
    return isinstance(xdata, xr.DataArray) and _extract_units(xdata) is not None


def check_quantified(xdata, routine="check_quantified"):
    """
    Check if data is a quantified DataArray.

    Parameters
    ----------
    xdata : DataArray
        The given data array.
    routine : str, optional
        Name of the routine to show in the Error, by default "check_quantified"

    Raises
    ------
    FinamDataError
        If the array is not a quantified DataArray.
    """
    if not is_quantified(xdata):
        raise FinamDataError(f"{routine}: given data is not quantified.")


def assert_type(cls, slot, obj, types):
    """Type assertion."""
    for t in types:
        if isinstance(obj, t):
            return
    raise TypeError(
        f"Unsupported data type for {slot} in "
        f"{cls.__class__.__name__}: {obj.__class__.__name__}. "
        f"Expected one of [{', '.join([tp.__name__ for tp in types])}]"
    )


class Info:
    """Data info containing grid specification and metadata"""

    def __init__(self, grid=None, meta=None, **meta_kwargs):
        """Creates a data info object.

        Parameters
        ----------
        grid : Grid
            grid specification
        meta : dict
            dictionary of metadata
        **meta_kwargs
            additional metadata by name, will overwrite entries in ``meta``
        """
        if grid is not None and not isinstance(grid, GridBase):
            raise FinamMetaDataError(
                "Grid in Info must be either None or of a sub-class of GridBase"
            )

        self.grid = grid
        self.meta = meta or {}
        self.meta.update(meta_kwargs)

    def copy(self):
        """Copies the info object"""
        return copy.copy(self)

    def copy_with(self, **kwargs):
        """Copies the info object and sets variables and meta values according to the kwargs"""
        other = Info(grid=self.grid, meta=copy.copy(self.meta))
        for k, v in kwargs.items():
            if k == "grid":
                other.grid = v
            else:
                other.meta[k] = v

        return other

    def accepts(self, incoming, fail_info):
        """Tests whether this info can accept/is compatible with an incoming info

        Parameters
        ----------
        incoming : Info
            Incoming/source info to check. This is the info from upstream.
        fail_info : dict
            Dictionary that will be filled with failed properties; name: (source, target).

        Returns
        -------
        bool
            Whether the incoming info is accepted
        """
        if not isinstance(incoming, Info):
            fail_info["type"] = (incoming.__class__, self.__class__)
            return False

        success = True
        if self.grid is not None and self.grid != incoming.grid:
            fail_info["grid"] = (incoming.grid, self.grid)
            success = False

        for k, v in self.meta.items():
            if v is not None and k in incoming.meta:
                if incoming.meta[k] != v:
                    fail_info["meta." + k] = (incoming.meta[k], v)
                    success = False

        return success

    def __copy__(self):
        """Shallow copy of the info"""
        return Info(grid=self.grid, meta=self.meta)

    def __eq__(self, other):
        """Equality check for two infos"""
        if not isinstance(other, Info):
            return False
        return self.grid == other.grid and self.meta == other.meta

    def __getattr__(self, name):
        # only called if attribute is not present in class
        if "meta" in self.__dict__ and name in self.meta:
            return self.meta[name]
        raise AttributeError(f"'Info' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        # first check if attribute present or meta not yet present (e.g. grid)
        if name in self.__dir__() or "meta" not in self.__dict__:
            super().__setattr__(name, value)
        else:
            self.__dict__["meta"][name] = value

    def __repr__(self):
        grid = self.grid.name if self.grid is not None else "None"
        meta = ", " * bool(self.meta)
        meta += ", ".join(
            f"{k}=" + ("None" if v is None else f"'{v}'") for k, v in self.meta.items()
        )
        return f"Info(grid={grid}{meta})"
