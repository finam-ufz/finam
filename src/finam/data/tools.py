"""Data tools for FINAM."""
import copy
import datetime

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

from ..errors import FinamDataError, FinamMetaDataError
from .grid_spec import NoGrid
from .grid_tools import Grid, GridBase

# set default format to cf-convention for pint.dequantify
# some problems with degree_Celsius and similar here
pint_xarray.unit_registry.default_format = "cf"
UNITS = pint_xarray.unit_registry


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
    time : datetime.datatime or None, optional
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
    else:
        dims += info.grid.data_axes_names
    return dims


def to_xarray(data, name, info, time=None, no_time_check=False):
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
    time : datetime.datatime or None, optional
        Timestamp for the data, by default None
    no_time_check : bool
        Skips the time check for xarray input data. Used internally in adapter outputs.

    Returns
    -------
    xarray.DataArray
        The converted data.

    Raises
    ------
    FinamDataError
        If the data doesn't match its info.
    """
    if isinstance(data, xr.DataArray):
        check(data, name, info, time, overwrite_name=True, ignore_time=no_time_check)
        return data

    units = None
    if isinstance(data, pint.Quantity):
        units = data.units
        data = np.asarray(data.magnitude)
    else:
        data = np.asarray(data)

    # check correct data size
    if isinstance(info.grid, Grid):
        if data.size != info.grid.data_size:
            raise FinamDataError(
                f"to_xarray: data size doesn't match grid size. "
                f"Got {data.size}, expected {info.grid.data_size}"
            )
        # reshape flat arrays
        if len(data.shape) == 1:
            data = data.reshape(info.grid.data_shape, order=info.grid.order)
        else:
            if data.shape != info.grid.data_shape:
                raise FinamDataError(
                    f"to_xarray: data shape doesn't match grid shape. "
                    f"Got {data.shape}, expected {info.grid.data_shape}"
                )
    elif isinstance(info.grid, NoGrid):
        if len(data.shape) != info.grid.dim:
            raise FinamDataError(
                f"to_xarray: number of dimensions in data doesn't match expected number. "
                f"Got {len(data.shape)}, expected {info.grid.dim}"
            )

    if units is not None:
        if "units" not in info.meta and units != UNITS.dimensionless:
            raise FinamDataError("Given data has units, but metadata has none.")
        if "units" in info.meta and UNITS.Unit(info.units) != units:
            raise FinamDataError(
                f"Given data has wrong units. Got {str(units)}, expected {str(info.units)}"
            )

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
    xdata : xarray.DataArray
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
    xdata : xarray.DataArray
        The given data array.

    Returns
    -------
    list of datetime.datetime or None
        timestamps of the data array.
    """
    if has_time(xdata):
        time = xdata["time"]
        if time.size == 1:
            time = [time.item()]
        return list(pd.to_datetime(time).to_pydatetime())
    return None


def get_magnitude(xdata):
    """
    Get magnitude of given data.

    Parameters
    ----------
    xdata : xarray.DataArray
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
    xdata : xarray.DataArray
        The given data array.

    Returns
    -------
    pint.Quantity
        Quantified data.
    """
    check_quantified(xdata, "get_data")
    return xdata.data


def strip_time(xdata):
    """Returns a view of the xarray data with the time dimension squeezed if there is only a single entry

    Returns
    -------
    xarray.DataArray
        Stripped data

    Raises
    ------
    FinamDataError
        If the data is not an xarray, or has multiple time entries.
    """
    if not isinstance(xdata, xr.DataArray):
        raise FinamDataError("Can strip time of xarray DataArray only")

    if has_time(xdata):
        if xdata.shape[0] > 1:
            raise FinamDataError(
                "Can't strip time of a data array with multiple time entries"
            )
        return xdata[0, ...]

    return xdata


def strip_data(xdata):
    """Unwraps the xarray data, with the time dimension squeezed if there is only a single entry.

    Equivalent to calling :func:`.strip_time` and :func:`.get_data` on the data.

    Returns
    -------
    numpy.ndarray
        Stripped data
    """
    return get_data(strip_time(xdata))


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
    xdata : xarray.DataArray
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
    xdata : xarray.DataArray
        The given data array.
    units : str or pint.Unit
        Desired units.

    Returns
    -------
    xarray.DataArray
        Converted data.
    """
    check_quantified(xdata, "to_units")
    return xdata.pint.to(pint.Unit(units))


def full_like(xdata, value):
    """
    Return a new DataArray with the same shape and type as a given object.

    Parameters
    ----------
    xdata : xarray.DataArray
        The reference object in input.
    value : scalar
        Value to fill the new object with before returning it.

    Returns
    -------
    xarray.DataArray
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
    time : datetime.datatime or None, optional
        Timestamp for the data, by default None

    Returns
    -------
    xarray.DataArray
        The converted data.
    """
    shape = info.grid.data_shape if isinstance(info.grid, Grid) else tuple()
    return to_xarray(np.full(shape, value), name, info, time)


def check(xdata, name, info, time=None, ignore_time=False, overwrite_name=False):
    """
    Check if data matches given info.

    Parameters
    ----------
    xdata : xarray.DataArray
        The given data array.
    name : str
        Name of the data.
    info : Info
        Info associated with the data.
    time : datetime.datatime or None, optional
        Timestamp for the data, by default None
    ignore_time : bool
        Allows to ignore the time value; still checks presence of time
    overwrite_name : bool
        Overwrites the name in the data instead of comparing both names

    Raises
    ------
    FinamDataError
        If data doesn't match given info.
    """
    if not isinstance(xdata, xr.DataArray):
        raise FinamDataError("check: given data is not a xarray.DataArray.")
    check_quantified(xdata, "check")
    if name != xdata.name:
        if overwrite_name:
            xdata.name = name
        else:
            raise FinamDataError(
                f"check: given data has wrong name. Got {xdata.name}, expected {name}"
            )
    if time is not None:
        if not has_time(xdata):
            raise FinamDataError("check: given data should hold a time.")
        if not ignore_time and time != get_time(xdata)[0]:
            raise FinamDataError(
                f"check: given data has wrong time. Got {get_time(xdata)[0]}, expected {time}"
            )

        _check_shape(xdata, info.grid, True)

    elif has_time(xdata):
        raise FinamDataError("check: given data shouldn't hold a time.")
    else:
        _check_shape(xdata, info.grid, False)

    dims = _gen_dims(len(xdata.dims) - (1 if time else 0), info, time)
    if dims != list(xdata.dims):
        raise FinamDataError(
            f"check: given data has wrong dimensions. Got {list(xdata.dims)}, expected {dims}."
        )
    # pint_xarray will remove the "units" entry in the data attributes
    # time should not be checked, as it is for the connect phase only
    meta = copy.copy(info.meta)
    meta.pop("units", None)
    meta.pop("time", None)
    if meta != xdata.attrs:
        raise FinamDataError(
            f"check: given data has wrong meta data.\nData: {xdata.attrs}\nMeta: {meta}"
        )
    # check units
    if "units" in info.meta and UNITS.Unit(info.units) != get_units(xdata):
        raise FinamDataError(
            f"check: given data has wrong units. "
            f"Got {get_units(xdata)}, expected {UNITS.Unit(info.units)}."
        )


def _check_shape(xdata, grid, with_time):
    in_shape = xdata.shape[1:] if with_time else xdata.shape
    if isinstance(grid, Grid) and in_shape != grid.data_shape:
        raise FinamDataError(
            f"check: given data has wrong shape. "
            f"Got {in_shape}, expected {grid.data_shape}"
        )
    if isinstance(grid, NoGrid) and len(in_shape) != grid.dim:
        raise FinamDataError(
            f"check: given data has wrong number of dimensions. "
            f"Got {len(in_shape)}, expected {grid.dim}"
        )


def is_quantified(xdata):
    """
    Check if data is a quantified DataArray.

    Parameters
    ----------
    xdata : xarray.DataArray
        The given data array.

    Returns
    -------
    bool
        Wether the data is a quantified DataArray.
    """
    return isinstance(xdata, xr.DataArray) and _extract_units(xdata) is not None


def quantify(xdata):
    """
    Quantifies data from its metadata.

    Parameters
    ----------
    xdata : xarray.DataArray
        The given data array.

    Returns
    -------
    xarray.DataArray
        The quantified array.
    """
    return (
        xdata.pint.quantify(unit_registry=UNITS)
        if "units" in xdata.attrs
        else xdata.pint.quantify("", unit_registry=UNITS)
    )


def check_units(lhs, rhs):
    """Checks if two units are compatible/convertible

    Returns
    -------
    bool
        If the units are compatible.
    """
    return UNITS.Unit(lhs).is_compatible_with(rhs)


def check_quantified(xdata, routine="check_quantified"):
    """
    Check if data is a quantified DataArray.

    Parameters
    ----------
    xdata : xarray.DataArray
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
    """Data info containing grid specification and metadata

    Parameters
    ----------
    grid : Grid or NoGrid or None
        grid specification
    meta : dict
        dictionary of metadata
    **meta_kwargs
        additional metadata by name, will overwrite entries in ``meta``

    Attributes
    ----------
    grid : Grid or NoGrid or None
        grid specification
    meta : dict
        dictionary of metadata

    """

    def __init__(self, time, grid, meta=None, **meta_kwargs):
        if time is not None and not isinstance(time, datetime.datetime):
            raise FinamMetaDataError("Time in Info must be either None or a datetime")
        if grid is not None and not isinstance(grid, GridBase):
            raise FinamMetaDataError(
                "Grid in Info must be either None or of a sub-class of GridBase"
            )

        self.time = time
        self.grid = grid
        self.meta = meta or {}
        self.meta.update(meta_kwargs)

    def copy(self):
        """Copies the info object"""
        return copy.copy(self)

    def copy_with(self, use_none=True, **kwargs):
        """Copies the info object and sets variables and meta values according to the kwargs

        Parameters
        ----------
        use_none : bool
            whether properties with None value should also be transferred
        **kwargs
            key values pairs for properties to change
        """
        other = Info(time=self.time, grid=self.grid, meta=copy.copy(self.meta))
        for k, v in kwargs.items():
            if k == "time":
                if v is not None or use_none:
                    other.time = v
            elif k == "grid":
                if v is not None or use_none:
                    other.grid = v
            else:
                if v is not None or use_none:
                    other.meta[k] = v

        return other

    def accepts(self, incoming, fail_info, ignore_none=False):
        """Tests whether this info can accept/is compatible with an incoming info

        Parameters
        ----------
        incoming : Info
            Incoming/source info to check. This is the info from upstream.
        fail_info : dict
            Dictionary that will be filled with failed properties; name: (source, target).
        ignore_none : bool
            Ignores ``None`` values in the incoming info.

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
            if not (ignore_none and incoming.grid is None):
                fail_info["grid"] = (incoming.grid, self.grid)
                success = False

        for k, v in self.meta.items():
            if v is not None and k in incoming.meta:
                in_value = incoming.meta[k]
                if k == "units":
                    if not (ignore_none and in_value is None) and not check_units(
                        v, in_value
                    ):
                        fail_info["meta." + k] = (in_value, v)
                        success = False
                else:
                    if not (ignore_none and in_value is None) and in_value != v:
                        fail_info["meta." + k] = (in_value, v)
                        success = False

        return success

    def __copy__(self):
        """Shallow copy of the info"""
        return Info(time=self.time, grid=self.grid, meta=self.meta)

    def __eq__(self, other):
        """Equality check for two infos

        Ignores time.
        """
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
