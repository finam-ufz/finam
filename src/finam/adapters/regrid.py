"""
Basic linear and nearest neighbour regridding adapters.

See package `finam-regrid <https://finam.pages.ufz.de/finam-regrid/>`_ for more advanced regridding.
"""

from abc import ABC, abstractmethod

import numpy as np
from pyproj import Transformer, crs
from scipy.interpolate import LinearNDInterpolator, RegularGridInterpolator
from scipy.spatial import KDTree

from ..data import tools as dtools
from ..data.grid_spec import StructuredGrid
from ..errors import FinamDataError, FinamMetaDataError
from ..sdk import Adapter
from ..tools.log_helper import ErrorLogger

__all__ = [
    "ARegridding",
    "RegridNearest",
    "RegridLinear",
]


class ARegridding(Adapter, ABC):
    """Abstract regridding class for handling data info"""

    def __init__(self, in_grid=None, out_grid=None, out_mask=None):
        super().__init__()
        self.input_grid = in_grid
        self.output_grid = out_grid
        self.output_mask = out_mask
        self.input_mask = None
        self.input_meta = None
        self.transformer = None
        self._is_initialized = False

    @abstractmethod
    def _update_grid_specs(self):
        """set up interpolator"""

    def _get_info(self, info):
        request = info.copy_with(grid=self.input_grid, mask=None)
        in_info = self.exchange_info(request)

        if self.output_grid is None and info.grid is None:
            with ErrorLogger(self.logger):
                raise FinamMetaDataError("Missing target grid specification")
        if self.input_grid is None and in_info.grid is None:
            with ErrorLogger(self.logger):
                raise FinamMetaDataError("Missing source grid specification")

        if self.output_mask is None and info.mask is None:
            with ErrorLogger(self.logger):
                raise FinamMetaDataError("Missing target mask specification")
        if self.input_mask is None and in_info.mask is None:
            with ErrorLogger(self.logger):
                raise FinamMetaDataError("Missing source mask specification")

        if (
            self.output_grid is not None
            and info.grid is not None
            and self.output_grid != info.grid
        ):
            with ErrorLogger(self.logger):
                raise FinamMetaDataError(
                    "Target grid specification is already set, new specs differ"
                )

        if (
            self.output_mask is not None
            and info.mask is not None
            and not dtools.masks_equal(self.output_mask, info.mask)
        ):
            with ErrorLogger(self.logger):
                raise FinamMetaDataError(
                    "Target mask specification is already set, new specs differ"
                )

        self.input_grid = self.input_grid or in_info.grid
        self.input_mask = self.input_mask or in_info.mask
        self.output_grid = self.output_grid or info.grid
        self.output_mask = self.output_mask or info.mask

        if self.input_grid.crs is None and self.output_grid.crs is not None:
            raise FinamMetaDataError("Input grid has a CRS, but output grid does not")
        if self.output_grid.crs is None and self.input_grid.crs is not None:
            raise FinamMetaDataError("output grid has a CRS, but input grid does not")

        out_info = in_info.copy_with(grid=self.output_grid, mask=self.output_mask)

        if not self._is_initialized:
            self._update_grid_specs()
            self._is_initialized = True

        self.input_meta = in_info.meta

        return out_info

    def _do_transform(self, points):
        if self.transformer is None:
            return points
        return np.asarray(list(self.transformer.itransform(points)))


class RegridNearest(ARegridding):
    """Regrid data between two grid specifications with nearest neighbour interpolation.

    See package `finam-regrid <https://finam.pages.ufz.de/finam-regrid/>`_ for more advanced regridding
    using `ESMPy <https://earthsystemmodeling.org/esmpy/>`_.

    .. warning::
        Does currently not support masked input data. Raises a ``NotImplementedError`` in that case.

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        adapter = fm.adapters.RegridNearest()

        adapter = fm.adapters.RegridNearest(
            in_grid=fm.UniformGrid(dims=(20, 10)),
            out_grid=fm.UniformGrid(dims=(10, 5), spacing=(2.0, 2.0, 2.0)),
        )

    Parameters
    ----------
    in_grid : Grid or None (optional)
        Input grid specification. Will be taken from source component if not specified.
    out_grid : Grid or None (optional)
        Output grid specification. Will be taken from target component if not specified.
    tree_options : dict
        kwargs for :class:`scipy.spatial.KDTree`
    """

    def __init__(self, in_grid=None, out_grid=None, out_mask=None, tree_options=None):
        super().__init__(in_grid, out_grid, out_mask)
        self.tree_options = tree_options
        self.ids = None

    def _update_grid_specs(self):
        self.transformer = _create_transformer(self.output_grid, self.input_grid)
        if (
            dtools.mask_specified(self.output_mask)
            and self.output_mask is not np.ma.nomask
        ):
            out_data_points = self.output_grid.data_points[
                self.output_mask.ravel(order=self.output_grid.order)
            ]
        else:
            out_data_points = self.output_grid.data_points
        out_coords = self._do_transform(out_data_points)

        # generate IDs to select data
        kw = self.tree_options or {}
        if (
            dtools.mask_specified(self.input_mask)
            and self.input_mask is not np.ma.nomask
        ):
            in_data_points = self.input_grid.data_points[
                self.input_mask.ravel(order=self.input_grid.order)
            ]
        else:
            in_data_points = self.input_grid.data_points
        tree = KDTree(in_data_points, **kw)

        # only store IDs, since they will be constant
        self.ids = tree.query(out_coords)[1]

    def _get_data(self, time, target):
        in_data = self.pull_data(time, target)

        if dtools.is_masked_array(in_data) and not dtools.mask_specified(
            self.input_mask
        ):
            with ErrorLogger(self.logger):
                msg = "For regridding masked input data, you need to explicitly set the mask in the input info."
                raise FinamDataError(msg)

        return dtools.from_compressed(
            dtools.to_compressed(in_data, order=self.input_grid.order)[self.ids],
            shape=self.output_grid.data_shape,
            order=self.output_grid.order,
            mask=self.output_mask,
        )


class RegridLinear(ARegridding):
    """
    Regrid data between two grid specifications with linear interpolation.

    Uses :class:`scipy.interpolate.RegularGridInterpolator` for structured grids.
    For unstructured grids, :class:`scipy.interpolate.LinearNDInterpolator` is used,
    which performs triangulation internally.
    So the actual topology of the grid is not taken into account.

    See package `finam-regrid <https://finam.pages.ufz.de/finam-regrid/>`_ for more advanced regridding
    using `ESMPy <https://earthsystemmodeling.org/esmpy/>`_.

    .. warning::
        Does currently not support masked input data. Raises a ``NotImplementedError`` in that case.

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        adapter = fm.adapters.RegridLinear()

        adapter = fm.adapters.RegridLinear(
            in_grid=fm.UniformGrid(dims=(20, 10)),
            out_grid=fm.UniformGrid(dims=(10, 5), spacing=(2.0, 2.0, 2.0)),
        )

    Parameters
    ----------
    in_grid : Grid or None (optional)
        Input grid specification. Will be taken from source component if not specified.
    out_grid : Grid or None (optional)
        Output grid specification. Will be taken from target component if not specified.
    fill_with_nearest : bool
        Whether out of bounds points should be filled with the nearest value. Default ``False``.
    tree_options : dict
        kwargs for :class:`scipy.spatial.KDTree`
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
        self.out_coords = None

    def _update_grid_specs(self):
        self.transformer = _create_transformer(self.output_grid, self.input_grid)
        self.out_coords = self._do_transform(self.output_grid.data_points)

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
            points = self.out_coords
            res = self.inter(points)
            self.out_ids = np.isnan(res)
            out_points = points[self.out_ids]
            kw = self.tree_options or {}
            tree = KDTree(self.input_grid.data_points, **kw)
            self.fill_ids = tree.query(out_points)[1]

    def _get_data(self, time, target):
        in_data = self.pull_data(time, target)

        if dtools.is_masked_array(in_data):
            with ErrorLogger(self.logger):
                msg = "Regridding is currently not implemented for masked data"
                raise NotImplementedError(msg)

        if isinstance(self.input_grid, StructuredGrid):
            self.inter.values = in_data[0, ...].magnitude
            res = self.inter(self.out_coords)
            if self.fill_with_nearest:
                res[self.out_ids] = self.inter.values.flatten(
                    order=self.input_grid.order
                )[self.fill_ids]
        else:
            self.inter.values = np.ascontiguousarray(
                in_data[0, ...].magnitude.reshape((-1, 1), order=self.input_grid.order),
                dtype=np.double,
            )
            res = self.inter(self.out_coords)
            if self.fill_with_nearest:
                res[self.out_ids] = self.inter.values[self.fill_ids, 0]

        return dtools.quantify(res, dtools.get_units(in_data))


def _create_transformer(input_grid, output_grid):
    in_crs = None if input_grid.crs is None else crs.CRS(input_grid.crs)
    out_crs = None if output_grid.crs is None else crs.CRS(output_grid.crs)
    transformer = (
        None
        if (in_crs is None and out_crs is None) or in_crs == out_crs
        else Transformer.from_crs(in_crs, out_crs)
    )
    return transformer
