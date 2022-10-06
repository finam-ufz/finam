"""
Basic linear and nearest neighbour regridding adapters.
"""
from abc import ABC, abstractmethod

import numpy as np
import xarray as xr
from scipy.interpolate import LinearNDInterpolator, RegularGridInterpolator
from scipy.spatial import KDTree

from ..core.interfaces import FinamMetaDataError
from ..core.sdk import AAdapter
from ..data.grid_spec import StructuredGrid
from ..tools.log_helper import LogError


class ARegridding(AAdapter, ABC):
    """Abstract regridding class for handling data info"""

    def __init__(self):
        super().__init__()
        self.input_grid = None
        self.output_grid = None

    @abstractmethod
    def _update_grid_specs(self):
        """set up interpolator"""

    def get_info(self, info):
        self.logger.debug("get info")

        in_info = self.exchange_info(info)

        if "grid_spec" not in info:
            with LogError(self.logger):
                raise FinamMetaDataError("Missing target grid specification")
        if "grid_spec" not in in_info:
            with LogError(self.logger):
                raise FinamMetaDataError("Missing source grid specification")

        if (
            self.output_grid is not None
            and self.output_grid != info["grid_spec"]
        ):
            with LogError(self.logger):
                raise FinamMetaDataError(
                    "Target grid specification is already set, new specs differ"
                )

        needs_update = self.output_grid is None

        self.input_grid = in_info["grid_spec"]
        self.output_grid = info["grid_spec"]

        out_info = dict(in_info)
        out_info["grid_spec"] = self.output_grid

        if needs_update:
            self._update_grid_specs()

        return out_info


class Nearest(ARegridding):
    """Regrid data between two grid specifications with nearest neighbor interpolation"""

    def __init__(self, tree_options=None):
        super().__init__()
        self.tree_options = tree_options
        self.ids = None

    def _update_grid_specs(self):
        # generate IDs to select data
        kw = self.tree_options or {}
        tree = KDTree(self.input_grid.data_points, **kw)
        # only store IDs, since they will be constant
        self.ids = tree.query(self.output_grid.data_points)[1]

    def get_data(self, time):
        in_data = self.pull_data(time)

        res = in_data.pint.magnitude.reshape(-1, order=self.input_grid.order)[
            self.ids
        ].reshape(self.output_grid.data_shape, order=self.output_grid.order)

        return xr.DataArray(res).pint.quantify(in_data.pint.units)


class Linear(ARegridding):
    """
    Regrid data between two grid specifications with linear interpolation.

    Uses ``scipy.interpolate.RegularGridInterpolator`` for structured grids.
    For unstructured grids, ``scipy.interpolate.LinearNDInterpolator`` is used,
    which performs triangulation internally.
    So the actual topology of the grid is not taken into account.
    """

    def __init__(self, fill_with_nearest=False, tree_options=None):
        super().__init__()
        self.tree_options = tree_options
        self.fill_with_nearest = bool(fill_with_nearest)
        self.ids = None
        self.inter = None
        self.out_ids = None
        self.fill_ids = None

    def _update_grid_specs(self):
        if isinstance(self.input_grid, StructuredGrid):
            self.inter = RegularGridInterpolator(
                points=self.input_grid.data_axes,
                values=np.zeros(self.input_grid.data_shape, dtype=np.double),
            )
        else:
            self.inter = LinearNDInterpolator(
                points=self.input_grid.data_points,
                values=np.zeros(np.prod(self.input_grid.data_shape), dtype=np.double),
            )
        if self.fill_with_nearest:
            # check for outliers once
            res = self.inter(self.output_grid.data_points)
            self.out_ids = np.isnan(res)
            out_points = self.output_grid.data_points[self.out_ids]
            kw = self.tree_options or {}
            tree = KDTree(self.input_grid.data_points, **kw)
            self.fill_ids = tree.query(out_points)[1]

    def get_data(self, time):
        in_data = self.pull_data(time)

        if isinstance(self.input_grid, StructuredGrid):
            self.inter.values = in_data.pint.magnitude
        else:
            self.inter.values = np.ascontiguousarray(
                in_data.pint.magnitude.reshape((-1, 1), order=self.input_grid.order),
                dtype=np.double,
            )

        res = self.inter(self.output_grid.data_points)
        if self.fill_with_nearest:
            res[self.out_ids] = self.inter.values[self.fill_ids, 0]

        res = res.reshape(self.output_grid.data_shape, order=self.output_grid.order)
        return xr.DataArray(res).pint.quantify(in_data.pint.units)
