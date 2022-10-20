"""
Basic linear and nearest neighbour regridding adapters.
"""
from abc import ABC, abstractmethod

import numpy as np
from pyproj import Transformer, crs
from scipy.interpolate import LinearNDInterpolator, RegularGridInterpolator
from scipy.spatial import KDTree

from finam.interfaces import FinamMetaDataError

from ..data import tools as dtools
from ..data.grid_spec import StructuredGrid
from ..sdk import AAdapter
from ..tools.log_helper import ErrorLogger


class ARegridding(AAdapter, ABC):
    """Abstract regridding class for handling data info"""

    def __init__(self, in_grid=None, out_grid=None):
        super().__init__()
        self.input_grid = in_grid
        self.output_grid = out_grid
        self.input_meta = None
        self.transformer = None

        self._is_initialized = False

    @abstractmethod
    def _update_grid_specs(self):
        """set up interpolator"""

    def _get_info(self, info):

        request = (
            info.copy_with(grid=self.input_grid)
            if self.input_grid is not None
            else info
        )
        in_info = self.exchange_info(request)

        if self.output_grid is None and info.grid is None:
            with ErrorLogger(self.logger):
                raise FinamMetaDataError("Missing target grid specification")
        if self.input_grid is None and in_info.grid is None:
            with ErrorLogger(self.logger):
                raise FinamMetaDataError("Missing source grid specification")

        if (
            self.output_grid is not None
            and info.grid is not None
            and self.output_grid != info.grid
        ):
            with ErrorLogger(self.logger):
                raise FinamMetaDataError(
                    "Target grid specification is already set, new specs differ"
                )

        self.input_grid = self.input_grid or in_info.grid
        self.output_grid = self.output_grid or info.grid

        if self.input_grid.crs is None and self.output_grid.crs is not None:
            raise FinamMetaDataError("Input grid has a CRS, but output grid does not")
        if self.output_grid.crs is None and self.input_grid.crs is not None:
            raise FinamMetaDataError("output grid has a CRS, but input grid does not")

        out_info = in_info.copy_with(grid=self.output_grid)

        if not self._is_initialized:
            self._update_grid_specs()
            self._is_initialized = True

        self.input_meta = in_info.meta

        return out_info

    def _transform(self, points):
        if self.transformer is None:
            return points
        return np.asarray(list(self.transformer.itransform(points)))


class Nearest(ARegridding):
    """Regrid data between two grid specifications with nearest neighbor interpolation"""

    def __init__(self, in_grid=None, out_grid=None, tree_options=None):
        super().__init__(in_grid, out_grid)
        self.tree_options = tree_options
        self.ids = None

    def _update_grid_specs(self):
        self.transformer = _create_transformer(self.input_grid, self.output_grid)
        # generate IDs to select data
        kw = self.tree_options or {}
        tree = KDTree(self.input_grid.data_points, **kw)
        # only store IDs, since they will be constant
        self.ids = tree.query(self._transform(self.output_grid.data_points))[1]

    def _get_data(self, time):
        in_data = self.pull_data(time)

        res = (
            dtools.get_data(in_data)
            .reshape(-1, order=self.input_grid.order)[self.ids]
            .reshape(self.output_grid.data_shape, order=self.output_grid.order)
        )
        return res


class Linear(ARegridding):
    """
    Regrid data between two grid specifications with linear interpolation.

    Uses ``scipy.interpolate.RegularGridInterpolator`` for structured grids.
    For unstructured grids, ``scipy.interpolate.LinearNDInterpolator`` is used,
    which performs triangulation internally.
    So the actual topology of the grid is not taken into account.
    """

    def __init__(
        self, in_grid=None, out_grid=None, fill_with_nearest=False, tree_options=None
    ):
        super().__init__(in_grid, out_grid)
        self.tree_options = tree_options
        self.fill_with_nearest = bool(fill_with_nearest)
        self.ids = None
        self.inter = None
        self.out_ids = None
        self.fill_ids = None

    def _update_grid_specs(self):
        self.transformer = _create_transformer(self.input_grid, self.output_grid)

        if isinstance(self.input_grid, StructuredGrid):
            self.inter = RegularGridInterpolator(
                points=self.input_grid.data_axes,
                values=np.zeros(self.input_grid.data_shape, dtype=np.double),
                bounds_error=False,
            )
        else:
            self.inter = LinearNDInterpolator(
                points=self.input_grid.data_points,
                values=np.zeros(np.prod(self.input_grid.data_shape), dtype=np.double),
            )
        if self.fill_with_nearest:
            # check for outliers once
            points = self._transform(self.output_grid.data_points)
            res = self.inter(points)
            self.out_ids = np.isnan(res)
            out_points = points[self.out_ids]
            kw = self.tree_options or {}
            tree = KDTree(self.input_grid.data_points, **kw)
            self.fill_ids = tree.query(out_points)[1]

    def _get_data(self, time):
        in_data = self.pull_data(time)

        if isinstance(self.input_grid, StructuredGrid):
            self.inter.values = dtools.get_magnitude(dtools.strip_time(in_data))
            res = self.inter(self._transform(self.output_grid.data_points))
            if self.fill_with_nearest:
                res[self.out_ids] = self.inter.values.flatten(
                    order=self.input_grid.order
                )[self.fill_ids]
        else:
            self.inter.values = np.ascontiguousarray(
                dtools.get_magnitude(in_data).reshape(
                    (-1, 1), order=self.input_grid.order
                ),
                dtype=np.double,
            )
            res = self.inter(self._transform(self.output_grid.data_points))
            if self.fill_with_nearest:
                res[self.out_ids] = self.inter.values[self.fill_ids, 0]

        return res * dtools.get_units(in_data)


def _create_transformer(input_grid, output_grid):
    in_crs = None if input_grid.crs is None else crs.CRS(input_grid.crs)
    out_crs = None if output_grid.crs is None else crs.CRS(output_grid.crs)
    transformer = (
        None
        if (in_crs is None and out_crs is None) or in_crs == out_crs
        else Transformer.from_crs(in_crs, out_crs)
    )
    return transformer
