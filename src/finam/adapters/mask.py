"""
Basic masking adapters.
"""

from ..data.tools import (
    Mask,
    filled,
    is_sub_mask,
    mask_specified,
    strip_time,
    to_masked,
)
from ..errors import FinamMetaDataError
from ..sdk import Adapter
from ..tools.log_helper import ErrorLogger

__all__ = [
    "Masking",
    "UnMasking",
]


class UnMasking(Adapter):
    """Unmask data.

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        adapter = fm.adapters.UnMasking()

    Parameters
    ----------
    fill_value : float or None, optional
        Fill value for masked data.
    """

    def __init__(self, fill_value=None):
        super().__init__()
        self.fill_value = fill_value

    def _get_data(self, time, target):
        return filled(self.pull_data(time, target), self.fill_value)

    def _get_info(self, info):
        in_info = self.exchange_info(info.copy_with(mask=None))
        return in_info.copy_with(mask=Mask.NONE)


class Masking(Adapter):
    """Mask data.

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        adapter = fm.adapters.Masking(mask=[True, False])

    Parameters
    ----------
    mask : arraylike of bool
        Mask to apply.
    fill_value : float or None, optional
        Fill value for masked data.
    """

    def __init__(self, mask, fill_value=None):
        super().__init__()
        self.mask = mask
        self.fill_value = fill_value
        self.grid = None

    def _get_data(self, time, target):
        return to_masked(
            strip_time(self.pull_data(time, target), self.grid),
            mask=self.mask,
            fill_value=self.fill_value,
        )

    def _get_info(self, info):
        in_info = self.exchange_info(info.copy_with(mask=None))
        if in_info.mask is not None and mask_specified(in_info.mask):
            if not is_sub_mask(in_info.mask, self.mask):
                with ErrorLogger(self.logger):
                    msg = "Given mask needs to be a sub-mask of the data mask."
                    raise FinamMetaDataError(msg)
        self.grid = in_info.grid
        return in_info.copy_with(mask=self.mask)
