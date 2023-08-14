"""
Masking adapters.
"""
# pylint: disable=E1101
import numpy as np

from ..data import tools
from ..errors import FinamMetaDataError
from ..sdk import Adapter
from ..tools.log_helper import ErrorLogger

__all__ = ["Masking"]


class Masking(Adapter):
    """
    Adapter for compatible grids with output on a sub-grid.

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        adapter = fm.adapters.Masking()

    Parameters
    ----------
    nodata : numeric, optional
        Value to set at masked positions. Default: np.nan
    """

    def __init__(self, nodata=np.nan):
        super().__init__()
        self.nodata = nodata
        self._canonical_mask = None
        self._sup_grid = None
        self._sub_grid = None

    def _get_data(self, time, target):
        """Get the output's data-set for the given time.

        Parameters
        ----------
        time : datetime
            Simulation time to get the data for.

        Returns
        -------
        array_like
            data-set for the requested time.
        """
        return self._transform(
            tools.strip_time(self.pull_data(time, target), self._sup_grid)
        )

    def _get_info(self, info):
        # info coming from output, set grid None to get the input grid
        request = info.copy_with(grid=None)
        in_info = self.exchange_info(request)

        if info.grid is None:
            with ErrorLogger(self.logger):
                raise FinamMetaDataError("Missing target grid specification")
        if in_info.grid is None:
            with ErrorLogger(self.logger):
                raise FinamMetaDataError("Missing source grid specification")

        if not in_info.grid.compatible_with(info.grid, check_mask=False):
            with ErrorLogger(self.logger):
                raise FinamMetaDataError("Grid specifications not compatible.")

        if not self._masks_compatible(sup_grid=in_info.grid, sub_grid=info.grid):
            with ErrorLogger(self.logger):
                raise FinamMetaDataError("Grid masks not compatible.")

        self._sup_grid = in_info.grid
        self._sub_grid = info.grid

        # create_selection
        if self._sub_grid.mask is not None:
            self._canonical_mask = self._sub_grid.to_canonical(self._sub_grid.mask)
        else:
            self._canonical_mask = None

        # return output info
        return in_info.copy_with(grid=info.grid)

    def _masks_compatible(self, sup_grid, sub_grid):
        if sup_grid.mask is None:
            return True
        if sub_grid.mask is None:
            return np.all(~sup_grid.mask)
        sup_mask = sup_grid.to_canonical(sup_grid.mask)
        sub_mask = sub_grid.to_canonical(sub_grid.mask)
        # everything masked by the super-mask needs to be also masked by the sub-mask
        return np.all(sub_mask[sup_mask])

    def _transform(self, data):
        if self._canonical_mask is not None:
            data = np.copy(self._sup_grid.to_canonical(data))
            data[self._canonical_mask] = tools.UNITS.Quantity(self.nodata, data.units)
            return self._sub_grid.from_canonical(data)
        return self._sub_grid.from_canonical(self._sup_grid.to_canonical(data))
