"""Data tools for FINAM."""
import numpy as np
import pandas as pd

# isort: off
import xarray as xr

# to be able to read unit attributes following the CF conventions
import cf_xarray.units  # must be imported before pint_xarray
import pint_xarray
import pint

# isort: on

from . import NoGrid
from .grid_tools import Grid, StructuredGrid

# set default format to cf-convention for pint.dequantify
# some problems with degree_Celsius and similar here
pint_xarray.unit_registry.default_format = "~cf"


class FinamDataError(Exception):
    """Error for wrong data in FINAM."""


def _gen_dims(ndim, info, time=None):
    """
    _summary_

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
    return xr.DataArray(
        name=name,
        data=data[np.newaxis, ...] if time else data,
        dims=_gen_dims(np.ndim(data), info, time),
        coords=dict(time=[pd.Timestamp(time)]) if time else None,
        attrs=info.meta,
    ).pint.quantify()


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


def get_magnitued(xdata):
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
    if name != xdata.name:
        raise FinamDataError("check: given data has wrong name.")
    if time is not None:
        if not has_time(xdata):
            raise FinamDataError("check: given data should hold a time.")
        if pd.Timestamp(time) != pd.Timestamp(xdata[time][0]):
            raise FinamDataError("check: given data has wrong time.")
    elif has_time(xdata):
        raise FinamDataError("check: given data shouldn't hold a time.")
    dims = _gen_dims(len(xdata.dims) - (1 if time else 0), info, time)
    if dims != list(xdata.dims):
        raise FinamDataError("check: given data has wrong dimensions.")
    if info.meta != xdata.attrs:
        raise FinamDataError("check: given data has wrong meta data.")
