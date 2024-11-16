"""Core data tools for FINAM."""

import copy
import datetime
from enum import Enum

import numpy as np
import pandas as pd

from ...errors import FinamDataError, FinamMetaDataError
from .. import grid_spec
from ..grid_base import Grid, GridBase
from .units import (
    UNITS,
    check_quantified,
    compatible_units,
    equivalent_units,
    get_units,
    is_quantified,
    quantify,
)

_MASK_INDICATORS = ["_FillValue", "missing_value"]


class Mask(Enum):
    """Mask settings for Info."""

    FLEX = 0
    """Data can be masked or unmasked."""
    NONE = 1
    """Data is expected to be unmasked and given as plain numpy arrays."""


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


def is_masked_array(data):
    """
    Check if data is a masked array.

    Parameters
    ----------
    data : Any
        The given data array.

    Returns
    -------
    bool
        Whether the data is a MaskedArray.
    """
    if is_quantified(data):
        return np.ma.isMaskedArray(data.magnitude)
    return np.ma.isMaskedArray(data)


def has_masked_values(data):
    """
    Determine whether the data has masked values.

    Parameters
    ----------
    data : Any
        The given data array.

    Returns
    -------
    bool
        Whether the data is a MaskedArray and has any masked values.
    """
    return np.ma.is_masked(data)


def filled(data, fill_value=None):
    """
    Return input as an array with masked data replaced by a fill value.

    This routine respects quantified and un-quantified data.

    Parameters
    ----------
    data : :class:`pint.Quantity` or :class:`numpy.ndarray` or :class:`numpy.ma.MaskedArray`
        The reference object input.
    fill_value : array_like, optional
        The value to use for invalid entries. Can be scalar or non-scalar.
        If non-scalar, the resulting ndarray must be broadcastable over
        input array. Default is None, in which case, the `fill_value`
        attribute of the array is used instead.

    Returns
    -------
    pint.Quantity or numpy.ndarray
        New object with the same shape and type as other,
        with the data filled with fill_value.
        Units will be taken from the input if present.

    See also
    --------
    :func:`numpy.ma.filled`:
        Numpy routine doing the same.
    """
    if not is_masked_array(data):
        return data
    if is_quantified(data):
        return UNITS.Quantity(data.magnitude.filled(fill_value), data.units)
    return data.filled(fill_value)


def to_masked(data, **kwargs):
    """
    Return a masked version of the data.

    Parameters
    ----------
    data : :class:`pint.Quantity` or :class:`numpy.ndarray` or :class:`numpy.ma.MaskedArray`
        The reference object input.
    **kwargs
        keyword arguments forwarded to :any:`numpy.ma.array`

    Returns
    -------
    pint.Quantity or numpy.ma.MaskedArray
        New object with the same shape and type but as a masked array.
        Units will be taken from the input if present.
    """
    if is_masked_array(data) and not kwargs:
        return data
    if is_quantified(data):
        return UNITS.Quantity(np.ma.array(data.magnitude, **kwargs), data.units)
    return np.ma.array(data, **kwargs)


def to_compressed(xdata, order="C", mask=None):
    """
    Return all the non-masked data as a 1-D array respecting the given array order.

    Parameters
    ----------
    data : :class:`pint.Quantity` or :class:`numpy.ndarray` or :class:`numpy.ma.MaskedArray`
        The reference object input.
    order : str
        order argument for :any:`numpy.ravel`
    mask : :any:`Mask` value or valid boolean mask for :any:`MaskedArray`, optional
        mask to use when data is not masked already

    Returns
    -------
    :class:`pint.Quantity` or :class:`numpy.ndarray` or :class:`numpy.ma.MaskedArray`
        New object with the flat shape and only unmasked data but and same type as input.
        Units will be taken from the input if present.

    See also
    --------
    :func:`numpy.ma.compressed`:
        Numpy routine doing the same but only for C-order.
    """
    is_masked = is_masked_array(xdata)
    if is_masked or (mask is not None and mask_specified(mask)):
        data = np.ravel(xdata.data if is_masked else xdata, order)
        mask = xdata.mask if is_masked else mask
        if mask is not np.ma.nomask:
            data = data.compress(np.logical_not(np.ravel(mask, order)))
        return quantify(data, xdata.units) if is_quantified(xdata) else data
    return np.reshape(xdata, -1, order=order)


def from_compressed(xdata, shape, order="C", mask=None, **kwargs):
    """
    Fill a (masked) array following a given mask or shape with the provided data.

    This will only create a masked array if kwargs are given (especially a mask).
    Otherwise this is simply reshaping the given data.
    Filling is performed in the given array order.

    Parameters
    ----------
    data : :class:`pint.Quantity` or :class:`numpy.ndarray` or :class:`numpy.ma.MaskedArray`
        The reference object input.
    shape : str
        shape argument for :any:`numpy.reshape`
    order : str
        order argument for :any:`numpy.reshape`
    mask : :any:`Mask` value or valid boolean mask for :any:`MaskedArray`
        mask to use
    **kwargs
        keyword arguments forwarded to :any:`numpy.ma.array`

    Returns
    -------
    :class:`pint.Quantity` or :class:`numpy.ndarray` or :class:`numpy.ma.MaskedArray`
        New object with the desired shape and same type as input.
        Units will be taken from the input if present.
        Will only be a masked array if kwargs are given.

    See also
    --------
    to_compressed:
        Inverse operation.
    :any:`numpy.ma.array`:
        Routine consuming kwargs to create a masked array.
    :any:`numpy.reshape`:
        Equivalent routine if no mask is provided.

    Notes
    -----
    If both `mask` and `shape` are given, they need to match in size.
    """
    if mask is None or mask is np.ma.nomask or not mask_specified(mask):
        if kwargs and mask is Mask.NONE:
            msg = "from_compressed: Can't create masked array with mask=Mask.NONE"
            raise FinamDataError(msg)
        data = np.reshape(xdata, shape, order=order)
        return to_masked(data, **kwargs) if kwargs or mask is np.ma.nomask else data
    if is_quantified(xdata):
        # pylint: disable-next=unexpected-keyword-arg
        data = quantify(np.empty_like(xdata, shape=np.prod(shape)), xdata.units)
    else:
        # pylint: disable-next=unexpected-keyword-arg
        data = np.empty_like(xdata, shape=np.prod(shape))
    data[np.logical_not(np.ravel(mask, order=order))] = xdata
    return to_masked(np.reshape(data, shape, order=order), mask=mask, **kwargs)


def check_data_covers_domain(data, mask=None):
    """
    Check if the given data covers a domain defined by a mask on the same grid.

    Parameters
    ----------
    data : Any
        The given data array for a single time-step.
    mask : None or bool or array of bool, optional
        Mask defining the target domain on the same grid as the data,
        by default None

    Returns
    -------
    bool
        Whether the data covers the desired domain.

    Raises
    ------
    ValueError
        When mask is given and mask and data don't share the same shape.
    """
    if not _is_single_mask_value(mask) and np.shape(mask) != np.shape(data):
        raise ValueError("check_data_covers_domain: mask and data shape differ.")
    if not has_masked_values(data):
        return True
    if _is_single_mask_value(mask):
        return bool(mask)
    return np.all(mask[data.mask])


def _is_single_mask_value(mask):
    return mask is None or mask is np.ma.nomask or mask is False or mask is True


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


def masks_compatible(this, incoming, incoming_donwstream):
    """
    Check if an incoming mask is compatible with a given mask.

    Parameters
    ----------
    this : :any:`Mask` value or valid boolean mask for :any:`MaskedArray` or None
        mask specification to check against
    incoming : :any:`Mask` value or valid boolean mask for :any:`MaskedArray` or None
        incoming mask to check for compatibility
    incoming_donwstream : bool
        Whether the incoming mask is from downstream data

    Returns
    -------
    bool
        mask compatibility
    """
    if incoming_donwstream:
        upstream, downstream = this, incoming
    else:
        upstream, downstream = incoming, this
    # None is incompatible
    if upstream is None:
        return False
    # Mask.FLEX accepts anything, Mask.NONE only Mask.NONE
    if not mask_specified(downstream):
        if not mask_specified(upstream):
            return downstream == Mask.FLEX or upstream == Mask.NONE
        return downstream == Mask.FLEX
    # if mask is specified, upstream mask must also be specified
    if not mask_specified(upstream):
        return False
    # if both mask given, compare them
    return masks_equal(downstream, upstream)


def masks_equal(this, other):
    """
    Check two masks for equality.

    Parameters
    ----------
    this : :any:`Mask` value or valid boolean mask for :any:`MaskedArray` or None
        first mask
    incoming : :any:`Mask` value or valid boolean mask for :any:`MaskedArray` or None
        second mask


    Returns
    -------
    bool
        mask equality
    """
    if this is None and other is None:
        return True
    if not mask_specified(this) and not mask_specified(other):
        return this == other
    # need a valid mask at this point
    if not np.ma.is_mask(this) or not np.ma.is_mask(other):
        return False
    # special treatment of "nomask"
    if this is np.ma.nomask:
        if other is np.ma.nomask:
            return True
        return not np.any(other)
    if other is np.ma.nomask:
        return not np.any(this)
    # compare masks
    if not np.ndim(this) == np.ndim(other):
        return False
    if not np.all(np.shape(this) == np.shape(other)):
        return False
    return np.all(this == other)


def is_sub_mask(mask, submask):
    """
    Check for a sub-mask.

    Parameters
    ----------
    mask : arraylike
        The original mask.
    submask : arraylike
        The potential submask.

    Returns
    -------
    bool
        Whether 'submask' is a sub-mask of 'mask'.
    """
    if not np.ma.is_mask(mask) or not np.ma.is_mask(submask):
        return False
    if mask is np.ma.nomask:
        return True
    if submask is np.ma.nomask:
        return not np.any(mask)
    if not np.ndim(mask) == np.ndim(submask):
        return False
    if not np.all(np.shape(mask) == np.shape(submask)):
        return False
    return np.all(submask[mask])


def mask_specified(mask):
    """
    Determine whether given mask selection indicates a masked array.

    Parameters
    ----------
    mask : :any:`Mask` value or valid boolean mask for :any:`MaskedArray`
        mask to check

    Returns
    -------
    bool
        False if mask is Mask.FLEX or Mask.NONE, True otherwise
    """
    return not any(mask is val for val in list(Mask))


def _format_mask(mask):
    if mask_specified(mask) and mask is not np.ma.nomask:
        return "<ndarray>"
    if mask is np.ma.nomask:
        return "nomask"
    return str(mask)


class Info:
    """Data info containing grid specification and metadata

    Parameters
    ----------
    time : datetime or None, optional
        time specification, default: None
    grid : Grid or NoGrid or None, optional
        grid specification, default: None
    meta : dict, optional
        dictionary of metadata, default: None
    mask : :any:`Mask` value or valid boolean mask for :any:`MaskedArray`, optional
        masking specification of the data. Options:
            * :any:`Mask.FLEX`: data can be masked or unmasked (default)
            * :any:`Mask.NONE`: data is unmasked and given as plain numpy array
            * valid boolean mask for MaskedArray
    **meta_kwargs
        additional metadata by name, will overwrite entries in ``meta``

    Attributes
    ----------
    grid : Grid or NoGrid or None
        grid specification
    meta : dict
        dictionary of metadata
    """

    def __init__(self, time=None, grid=None, meta=None, mask=Mask.FLEX, **meta_kwargs):
        if time is not None and not isinstance(time, datetime.datetime):
            raise FinamMetaDataError("Time in Info must be either None or a datetime")
        if grid is not None and not isinstance(grid, GridBase):
            raise FinamMetaDataError(
                "Grid in Info must be either None or of a sub-class of GridBase"
            )

        self.time = time
        self.grid = grid
        if mask_specified(mask) and mask is not None:
            mask = np.ma.make_mask(mask, shrink=False)
        self.mask = mask
        self.meta = meta or {}
        self.meta.update(meta_kwargs)

        units = self.meta.get("units", "")
        units = None if units is None else UNITS.Unit(units)
        self.meta["units"] = units

    @property
    def is_masked(self):
        """bool: whether data is set to be masked."""
        return mask_specified(self.mask)

    @property
    def fill_value(self):
        """Fill value for masked data."""
        return self.meta.get(
            _MASK_INDICATORS[0], self.meta.get(_MASK_INDICATORS[1], None)
        )

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
        other = Info(
            time=self.time, grid=self.grid, meta=copy.copy(self.meta), mask=self.mask
        )
        for k, v in kwargs.items():
            if k == "time":
                if v is not None or use_none:
                    other.time = v
            elif k == "grid":
                if v is not None or use_none:
                    other.grid = v
            elif k == "mask":
                if v is not None or use_none:
                    other.mask = v
            elif k == "units":
                if v is not None or use_none:
                    other.meta[k] = v if v is None else UNITS.Unit(v)
            else:
                if v is not None or use_none:
                    other.meta[k] = v

        return other

    def accepts(self, incoming, fail_info, incoming_donwstream=False):
        """
        Tests whether this info can accept/is compatible with an incoming info.

        Tested attributes are: "grid", "mask" and "units"

        Parameters
        ----------
        incoming : Info
            Incoming/source info to check. This is the info from upstream.
        fail_info : dict
            Dictionary that will be filled with failed properties; name: (source, target).
        incoming_donwstream : bool, optional
            Whether the incoming info is from downstream data. Default: False

        Returns
        -------
        bool
            Whether the incoming info is accepted
        """
        if not isinstance(incoming, Info):
            fail_info["type"] = (incoming.__class__, self.__class__)
            return False

        success = True
        if self.grid is not None and not self.grid.compatible_with(incoming.grid):
            if not (incoming_donwstream and incoming.grid is None):
                fail_info["grid"] = (incoming.grid, self.grid)
                success = False

        if self.mask is not None and not masks_compatible(
            self.mask, incoming.mask, incoming_donwstream
        ):
            if not (incoming_donwstream and incoming.mask is None):
                fail_info["mask"] = (incoming.mask, self.mask)
                success = False

        u1_none = (u1 := self.units) is None
        u2_none = (u2 := incoming.units) is None
        if not u1_none and (u2_none or not compatible_units(u1, u2)):
            if not (incoming_donwstream and u2_none):
                fail_info["units"] = (u2, u1)
                success = False

        return success

    def __copy__(self):
        """Shallow copy of the info"""
        return Info(time=self.time, grid=self.grid, meta=self.meta, mask=self.mask)

    def __eq__(self, other):
        """Equality check for two infos

        Ignores time.
        """
        if not isinstance(other, Info):
            return False
        return (
            self.grid == other.grid
            and self.meta == other.meta
            and masks_equal(self.mask, other.mask)
        )

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
        return f"Info(grid={grid}, mask={_format_mask(self.mask)}{meta})"

    def as_dict(self):
        """Returns a ``dict`` containing all metadata in this Info."""
        return {
            **self.meta,
            "mask": _format_mask(self.mask),
            "grid": f"{self.grid}",
            "units": f"{self.units:~}",
        }
