"""Data tools for FINAM."""
import copy
import datetime

import numpy as np
import pandas as pd
import pint

from ..errors import FinamDataError, FinamMetaDataError

# pylint: disable-next=unused-import
from . import cf_units, grid_spec
from .grid_tools import Grid, GridBase

# set default format to cf-convention for pint.dequantify
# some problems with degree_Celsius and similar here
pint.application_registry.default_format = "cf"
UNITS = pint.application_registry

_UNIT_PAIRS_CACHE = {}


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
    if isinstance(data, pint.Quantity):
        if not compatible_units(data.units, units):
            raise FinamDataError(
                f"Given data has incompatible units. "
                f"Got {data.units}, expected {units}."
            )
        if not equivalent_units(data.units, units):
            units_converted = data.units, units
            data = data.to(units)
        elif force_copy:
            data = data.copy()
    else:
        if isinstance(data, np.ndarray):
            if force_copy:
                data = np.copy(data)
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
        if len(data.shape) == info.grid.dim:
            data = np.expand_dims(data, 0)
        else:
            raise FinamDataError(
                f"quantify: number of dimensions in data doesn't match expected number. "
                f"Got {len(data.shape)}, expected {info.grid.dim}"
            )
    else:
        if data.shape[0] != time_entries:
            raise FinamDataError(
                f"quantify: number of time entries in data doesn't match expected number. "
                f"Got {data.shape[0]}, expected {time_entries}"
            )
    return data


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


_BASE_DATETIME = datetime.datetime(1970, 1, 1)
_BASE_TIME = np.datetime64("1970-01-01T00:00:00")
_BASE_DELTA = np.timedelta64(1, "s")


def to_datetime(date):
    """Converts a numpy datetime64 object to a python datetime object"""
    if np.isnan(date):
        return pd.NaT

    timestamp = (date - _BASE_TIME) / _BASE_DELTA

    if timestamp < 0:
        return _BASE_DATETIME + datetime.timedelta(seconds=timestamp)

    return datetime.datetime.utcfromtimestamp(timestamp)


def get_magnitude(xdata):
    """
    Get magnitude of given data.

    Parameters
    ----------
    xdata : pint.Quantity
        The given data array.

    Returns
    -------
    numpy.ndarray
        Magnitude of given data.
    """
    check_quantified(xdata, "get_magnitude")
    return xdata.magnitude


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
    return xdata.units


def get_dimensionality(xdata):
    """
    Get dimensionality of the data.

    Parameters
    ----------
    xdata : pint.Quantity
        The given data array.

    Returns
    -------
    pint.UnitsContainer
        Dimensionality of the data.
    """
    return xdata.dimensionality


def to_units(xdata, units, check_equivalent=False, report_conversion=False):
    """
    Convert data to given units.

    Parameters
    ----------
    xdata : pint.Quantity
        The given data array.
    units : str or pint.Unit
        Desired units.
    check_equivalent : bool, optional
        Checks for equivalent units and simply re-assigns if possible.
    report_conversion : bool, optional
        If true, returns a tuple with the second element indicating the unit conversion if it was required.

    Returns
    -------
    pint.Quantity or tuple(pint.Quantity, tuple(pint.Unit, pint.Unit) or None)
        The converted data.

        If ``report_conversion`` is ``True``, a tuple is returned with the second element
        indicating the unit conversion if it was required.

        The second element is ``None`` if no conversion was required,
        and a tuple of two :class:`pint.Unit` objects otherwise.
    """
    check_quantified(xdata, "to_units")
    units = _get_pint_units(units)
    units2 = xdata.units
    conversion = None
    if units != units2:
        if check_equivalent and equivalent_units(units, units2):
            xdata = UNITS.Quantity(xdata.magnitude, units)
        else:
            xdata = xdata.to(units)
            conversion = units2, units

    if report_conversion:
        return xdata, conversion
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
    d = np.full_like(xdata, value)
    if is_quantified(xdata):
        return UNITS.Quantity(d, xdata.units)

    return d


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


def check(
    xdata,
    info,
):
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

    _check_shape(xdata, info.grid)

    # check units
    if not compatible_units(info.units, xdata):
        raise FinamDataError(
            f"check: given data has incompatible units. "
            f"Got {get_units(xdata)}, expected {info.units}."
        )


def _check_shape(xdata, grid):
    in_shape = xdata.shape[1:]
    if isinstance(grid, Grid) and in_shape != grid.data_shape:
        raise FinamDataError(
            f"check: given data has wrong shape. "
            f"Got {in_shape}, expected {grid.data_shape}"
        )
    if isinstance(grid, grid_spec.NoGrid) and len(in_shape) != grid.dim:
        raise FinamDataError(
            f"check: given data has wrong number of dimensions. "
            f"Got {len(in_shape)}, expected {grid.dim}"
        )


def is_quantified(xdata):
    """
    Check if data is a quantified DataArray.

    Parameters
    ----------
    xdata : Any
        The given data array.

    Returns
    -------
    bool
        Whether the data is a quantified DataArray.
    """
    return isinstance(xdata, pint.Quantity)


def quantify(xdata, units=None):
    """
    Quantifies data.

    Parameters
    ----------
    xdata : Any
        The given data array.
    units :

    Returns
    -------
    pint.Quantity
        The quantified array.
    """
    if is_quantified(xdata):
        raise FinamDataError(f"Data is already quantified with units '{xdata.units}'")
    return UNITS.Quantity(xdata, _get_pint_units(units or UNITS.dimensionless))


def check_quantified(xdata, routine="check_quantified"):
    """
    Check if data is a quantified DataArray.

    Parameters
    ----------
    xdata : numpy.ndarray
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


def _get_pint_units(var):
    if var is None:
        raise FinamDataError("Can't extract units from 'None'.")

    if isinstance(var, pint.Unit):
        return var

    if isinstance(var, pint.Quantity):
        return var.units or UNITS.dimensionless

    return UNITS.Unit(var)


def compatible_units(unit1, unit2):
    """
    Checks if two units are compatible/convertible.

    Parameters
    ----------
    unit1 : UnitLike or Quantified
        First unit to compare.
    unit2 : UnitLike or Quantified
        Second unit to compare.

    Returns
    -------
    bool
        Unit compatibility.
    """
    unit1, unit2 = _get_pint_units(unit1), _get_pint_units(unit2)
    comp_equiv = _UNIT_PAIRS_CACHE.get((unit1, unit2))
    if comp_equiv is None:
        comp_equiv = _cache_units(unit1, unit2)

    return comp_equiv[0]


def equivalent_units(unit1, unit2):
    """
    Check if two given units are equivalent.

    Parameters
    ----------
    unit1 : UnitLike or Quantified
        First unit to compare.
    unit2 : UnitLike or Quantified
        Second unit to compare.

    Returns
    -------
    bool
        Unit equivalence.
    """
    unit1, unit2 = _get_pint_units(unit1), _get_pint_units(unit2)
    comp_equiv = _UNIT_PAIRS_CACHE.get((unit1, unit2))
    if comp_equiv is None:
        comp_equiv = _cache_units(unit1, unit2)

    return comp_equiv[1]


def _cache_units(unit1, unit2):
    equiv = False
    compat = False
    try:
        equiv = np.isclose((1.0 * unit1).to(unit2).magnitude, 1.0)
        compat = True
    except pint.errors.DimensionalityError:
        pass

    _UNIT_PAIRS_CACHE[(unit1, unit2)] = compat, equiv
    return compat, equiv


def clear_units_cache():
    """Clears the units cache"""
    _UNIT_PAIRS_CACHE.clear()


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

        units = self.meta.get("units", "")
        units = None if units is None else UNITS.Unit(units)
        self.meta["units"] = units

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
            elif k == "units":
                if v is not None or use_none:
                    other.meta[k] = v if v is None else UNITS.Unit(v)
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
                    if not (ignore_none and in_value is None) and not compatible_units(
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
