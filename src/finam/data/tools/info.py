"""Data info tools for FINAM."""

import copy
import datetime

import numpy as np

from ...errors import FinamMetaDataError
from ..grid_base import GridBase
from .mask import MASK_INDICATORS, Mask, mask_specified, masks_compatible, masks_equal
from .units import UNITS, compatible_units


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
        self._time = self._grid = self._mask = None
        self.time = time
        self.grid = grid
        self.mask = mask
        # set meta last (see __setattr__)
        self.meta = meta or {}
        self.meta.update(meta_kwargs)
        # handle units
        units = self.meta.get("units", "")
        units = None if units is None else UNITS.Unit(units)
        self.meta["units"] = units

    @property
    def time(self):
        """datetime: current time."""
        return self._time

    @time.setter
    def time(self, time):
        if time is not None and not isinstance(time, datetime.datetime):
            msg = "Time in Info must be either None or a datetime"
            raise FinamMetaDataError(msg)
        self._time = time

    @property
    def grid(self):
        """Grid: data grid."""
        return self._grid

    @grid.setter
    def grid(self, grid):
        if grid is not None and not isinstance(grid, GridBase):
            msg = "Grid in Info must be either None or of a sub-class of GridBase"
            raise FinamMetaDataError(msg)
        self._grid = grid

    @property
    def mask(self):
        """Mask or ndarray: data mask."""
        return self._mask

    @mask.setter
    def mask(self, mask):
        if mask_specified(mask) and mask is not None:
            mask = np.ma.make_mask(mask, shrink=False)
            if (
                self.grid is not None
                and mask is not np.ma.nomask
                and not np.array_equal(self.grid_shape, np.shape(mask))
            ):
                msg = "Mask in Info not compatible with given grid."
                raise FinamMetaDataError(msg)
        self._mask = mask

    @property
    def grid_shape(self):
        """tuple: shape of the data grid."""
        return None if self.grid is None else self.grid.data_shape

    @property
    def is_masked(self):
        """bool: whether data is set to be masked."""
        return mask_specified(self.mask)

    @property
    def fill_value(self):
        """Fill value for masked data."""
        return self.meta.get(
            MASK_INDICATORS[0], self.meta.get(MASK_INDICATORS[1], None)
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
            self.mask, incoming.mask, incoming_donwstream, self.grid, incoming.grid
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
            and masks_equal(self.mask, other.mask, self.grid, other.grid)
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
