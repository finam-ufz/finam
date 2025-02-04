"""Mask tools for FINAM."""

from enum import Enum

import numpy as np

from ...errors import FinamDataError
from .units import UNITS, is_quantified, quantify

MASK_INDICATORS = ["_FillValue", "missing_value"]


class Mask(Enum):
    """Mask settings for Info."""

    FLEX = 0
    """Data can be masked or unmasked."""
    NONE = 1
    """Data is expected to be unmasked and given as plain numpy arrays."""


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


def masks_compatible(
    this, incoming, incoming_donwstream, this_grid=None, incoming_grid=None
):
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
    this_grid : Grid or NoGrid or None, optional
        grid for first mask (to check shape and value equality)
    incoming_grid : Grid or NoGrid or None, optional
        grid for second mask (to check shape and value equality)

    Returns
    -------
    bool
        mask compatibility
    """
    if incoming_donwstream:
        upstream, downstream = this, incoming
        up_grid, down_grid = this_grid, incoming_grid
    else:
        upstream, downstream = incoming, this
        up_grid, down_grid = incoming_grid, this_grid
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
    return masks_equal(downstream, upstream, down_grid, up_grid)


def masks_equal(this, other, this_grid=None, other_grid=None):
    """
    Check two masks for equality.

    Parameters
    ----------
    this : :any:`Mask` value or valid boolean mask for :any:`MaskedArray` or None
        first mask
    other : :any:`Mask` value or valid boolean mask for :any:`MaskedArray` or None
        second mask
    this_grid : Grid or NoGrid or None, optional
        grid for first mask (to check shape and value equality)
    other_grid : Grid or NoGrid or None, optional
        grid for second mask (to check shape and value equality)

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
    # mask shape is grid specific (reversed axes, decreasing axis)
    if this_grid is None or other_grid is None:
        return True
    this = this_grid.to_canonical(this)
    other = other_grid.to_canonical(other)
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
