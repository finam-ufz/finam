"""Core data tools for FINAM."""

import copy
import datetime

import numpy as np
import pandas as pd

from ...errors import FinamDataError
from .. import grid_spec
from ..grid_base import Grid
from .units import (
    UNITS,
    check_quantified,
    compatible_units,
    equivalent_units,
    get_units,
    is_quantified,
)

_BASE_DATETIME = datetime.datetime(1970, 1, 1)
_BASE_TIME = np.datetime64("1970-01-01T00:00:00")
_BASE_DELTA = np.timedelta64(1, "s")


def prepare(data, info, time_entries=1, force_copy=False, report_conversion=False):
    """
    Prepares data in FINAM's internal transmission format.

    Checks tha shape of the data.
    Checks or adds units and time dimension.

    Parameters
    ----------
    data : arraylike
        The input data.
    info : Info
        Info associated with the data.
    time_entries : int, optional
        Number of time slices in the data. Default 1.
    force_copy : bool, optional
        Forces the result to be a copy of the passed data. Default ``False``.

        If not used, the result is a view of the data if no units conversion needs to be done.
    report_conversion : bool, optional
        If true, returns a tuple with the second element indicating the unit conversion if it was required.

    Returns
    -------
    pint.Quantity or tuple(pint.Quantity, tuple(pint.Unit, pint.Unit) or None)
        The prepared data as a numpy array, wrapped into a :class:`pint.Quantity`.

        If ``report_conversion`` is ``True``, a tuple is returned with the second element
        indicating the unit conversion if it was required.

        The second element is ``None`` if no conversion was required,
        and a tuple of two :class:`pint.Unit` objects otherwise.

    Raises
    ------
    FinamDataError
        If the data doesn't match its info.
    """
    units_converted = None
    units = info.units
    if is_quantified(data):
        if not compatible_units(data.units, units):
            raise FinamDataError(
                f"Given data has incompatible units. "
                f"Got {data.units}, expected {units}."
            )
        if info.is_masked and not np.ma.isarray(data.magnitude):
            data = UNITS.Quantity(
                np.ma.array(
                    data=data.magnitude,
                    mask=info.mask,
                    shrink=False,
                    fill_value=info.fill_value,
                ),
                data.units,
            )
        if not equivalent_units(data.units, units):
            units_converted = data.units, units
            data = data.to(units)
        elif force_copy:
            data = data.copy()
    else:
        if info.is_masked and not np.ma.isarray(data):
            data = UNITS.Quantity(
                np.ma.array(
                    data=data,
                    mask=info.mask,
                    shrink=False,
                    fill_value=info.fill_value,
                    copy=force_copy,
                ),
                units,
            )
        # this covers masked arrays as well
        elif isinstance(data, np.ndarray):
            if force_copy:
                data = data.copy()
            data = UNITS.Quantity(data, units)
        else:
            if force_copy:
                data = copy.copy(data)
            data = UNITS.Quantity(np.asarray(data), units)

    data = _check_input_shape(data, info, time_entries)

    if report_conversion:
        return data, units_converted
    return data


def _check_input_shape(data, info, time_entries):
    # check correct data size
    if isinstance(info.grid, Grid):
        time_entries = (
            data.shape[0]
            if len(data.shape) == len(info.grid.data_shape) + 1
            else time_entries
        )
        data_size = data.size / time_entries
        if data_size != info.grid.data_size:
            raise FinamDataError(
                f"quantify: data size doesn't match grid size. "
                f"Got {data_size}, expected {info.grid.data_size}"
            )
        # check shape of non-flat arrays
        if len(data.shape) != 1:
            if data.shape[1:] != info.grid.data_shape:
                if data.shape == info.grid.data_shape:
                    data = np.expand_dims(data, 0)
                else:
                    raise FinamDataError(
                        f"quantify: data shape doesn't match grid shape. "
                        f"Got {data.shape}, expected {info.grid.data_shape}"
                    )
        else:
            # reshape arrays
            if time_entries <= 1:
                data = data.reshape(
                    [1] + list(info.grid.data_shape), order=info.grid.order
                )
            else:
                data = data.reshape(
                    [time_entries] + list(info.grid.data_shape), order=info.grid.order
                )
    elif isinstance(info.grid, grid_spec.NoGrid):
        data = _check_input_shape_no_grid(data, info, time_entries)
    return data


def _check_input_shape_no_grid(data, info, time_entries):
    if len(data.shape) != info.grid.dim + 1:
        if _no_grid_shape_valid(data.shape, info.grid):
            data = np.expand_dims(data, 0)
        else:
            raise FinamDataError(
                f"Data shape not valid. "
                f"Got {data.shape}, expected {info.grid.data_shape}"
            )
    else:
        if not _no_grid_shape_valid(data.shape[1:], info.grid):
            raise FinamDataError(
                f"Data shape not valid. "
                f"Got {data.shape[1:]}, expected {info.grid.data_shape}"
            )
        if data.shape[0] != time_entries:
            raise FinamDataError(
                f"Number of time entries in data doesn't match expected number. "
                f"Got {data.shape[0]}, expected {time_entries}"
            )
    return data


def _no_grid_shape_valid(data_shape, grid):
    if len(data_shape) != grid.dim:
        return False
    dshp = np.array(data_shape)
    gshp = np.array(grid.data_shape)
    fix_dims = gshp != -1
    return np.all(dshp[fix_dims] == gshp[fix_dims])


def has_time_axis(xdata, grid):
    """
    Check if the data array has a time axis.

    Parameters
    ----------
    xdata : numpy.ndarray
        The given data array.
    grid : GridBase
        The associated grid specification
    Returns
    -------
    bool
        Whether the data has a time axis.
    """
    grid_dim = None

    if isinstance(grid, Grid):
        grid_dim = len(grid.data_shape)
    elif isinstance(grid, grid_spec.NoGrid):
        grid_dim = grid.dim
    else:
        raise ValueError(
            f"Expected type Grid or NoGrid, got {grid.__class__.__name__}."
        )

    if xdata.ndim == grid_dim:
        return False

    if xdata.ndim == grid_dim + 1:
        return True

    raise FinamDataError("Data dimension must be grid dimension or grid dimension + 1.")


def to_datetime(date):
    """Converts a numpy datetime64 object to a python datetime object"""
    if np.isnan(date):
        return pd.NaT

    timestamp = (date - _BASE_TIME) / _BASE_DELTA

    if timestamp < 0:
        return _BASE_DATETIME + datetime.timedelta(seconds=timestamp)

    tz = datetime.timezone.utc
    return datetime.datetime.fromtimestamp(timestamp, tz).replace(tzinfo=None)


def strip_time(xdata, grid):
    """Returns a view of the data with the time dimension squeezed if there is only a single entry

    Parameters
    ----------
    xdata : arraylike
        Data to strip time dimension from
    grid : GridBase
        The associated grid specification

    Returns
    -------
    arraylike
        Stripped data

    Raises
    ------
    FinamDataError
        If the data has multiple time entries.
    """
    if has_time_axis(xdata, grid):
        if xdata.shape[0] > 1:
            raise FinamDataError(
                "Can't strip time of a data array with multiple time entries"
            )
        return xdata[0, ...]

    return xdata


def full_like(xdata, value):
    """
    Return a new data array with the same shape, type and units as a given object.

    Parameters
    ----------
    xdata : :class:`pint.Quantity` or :class:`numpy.ndarray`
        The reference object input.
    value : scalar
        Value to fill the new object with before returning it.

    Returns
    -------
    pint.Quantity or numpy.ndarray
        New object with the same shape and type as other,
        with the data filled with fill_value.
        Units will be taken from the input if present.
    """
    data = np.full_like(xdata, value)
    if is_quantified(xdata):
        return UNITS.Quantity(data, xdata.units)
    return data


def full(value, info):
    """
    Return a new data array with units according to the given info, filled with given value.

    Parameters
    ----------
    value : scalar
        Value to fill the new object with before returning it.
    info : Info
        Info associated with the data.

    Returns
    -------
    pint.Quantity
        The converted data.
    """
    shape = info.grid.data_shape if isinstance(info.grid, Grid) else tuple()
    return prepare(np.full([1] + list(shape), value), info)


def check(xdata, info):
    """
    Check if data matches given info.

    Parameters
    ----------
    xdata : numpy.ndarray
        The given data array.
    info : Info
        Info associated with the data.

    Raises
    ------
    FinamDataError
        If data doesn't match given info.
    """
    check_quantified(xdata, "check")

    if not has_time_axis(xdata, info.grid):
        raise FinamDataError("check: given data should have a time dimension.")

    _check_shape(xdata.shape[1:], info.grid)

    # check units
    if not compatible_units(info.units, xdata):
        raise FinamDataError(
            f"check: given data has incompatible units. "
            f"Got {get_units(xdata)}, expected {info.units}."
        )


def _check_shape(shape, grid):
    if isinstance(grid, Grid) and shape != grid.data_shape:
        raise FinamDataError(
            f"check: given data has wrong shape. "
            f"Got {shape}, expected {grid.data_shape}"
        )
    if isinstance(grid, grid_spec.NoGrid) and len(shape) != grid.dim:
        raise FinamDataError(
            f"check: given data has wrong number of dimensions. "
            f"Got {len(shape)}, expected {grid.dim}"
        )


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
