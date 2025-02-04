"""Units tools for FINAM."""

import numpy as np
import pint

from ...errors import FinamDataError

# pylint: disable-next=unused-import
from . import cf_units

# set default format to cf-convention for pint.dequantify
# some problems with degree_Celsius and similar here
pint.application_registry.default_format = "cf"
UNITS = pint.application_registry

_UNIT_PAIRS_CACHE = {}


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
    check_quantified(xdata, "get_dimensionality")
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
    units : UnitLike or Quantified or None, optional
        units to use, dimensionless by default

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
