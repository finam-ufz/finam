"""
Basic linear and nearest neighbour regridding adapters.

See package `finam-regrid <https://finam.pages.ufz.de/finam-regrid/>`_ for more advanced regridding.
"""

from abc import ABC, abstractmethod

import numpy as np
import pyproj
from scipy.interpolate import LinearNDInterpolator, RegularGridInterpolator
from scipy.spatial import KDTree

from ..data import tools as dtools
from ..data.grid_spec import Grid, StructuredGrid, UnstructuredGrid
from ..errors import FinamDataError, FinamMetaDataError
from ..sdk import Adapter
from ..tools.log_helper import ErrorLogger

__all__ = [
    "ARegridding",
    "RegridNearest",
    "RegridLinear",
    "ToCRS",
    "ToUnstructured",
]


class ARegridding(Adapter, ABC):
    """Abstract regridding class for handling data info"""

    def __init__(self, in_grid=None, out_grid=None, out_mask=None):
        super().__init__()
        self.input_grid = in_grid
        self.output_grid = out_grid
        if dtools.mask_specified(out_mask) and out_mask is not None:
            out_mask = np.ma.make_mask(out_mask, shrink=False)
        self.output_mask = out_mask
        self.downstream_mask = None
        self.input_mask = None
        self.transformer = None
        self._is_initialized = False
        self._out_mask_checked = False

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
        if self.input_mask is None and in_info.mask is None:
            with ErrorLogger(self.logger):
                raise FinamMetaDataError("Missing source mask specification")
        if (
            self.output_grid is not None
            and info.grid is not None
            and self.output_grid != info.grid
        ):
            with ErrorLogger(self.logger):
                msg = "Target grid specification is already set, new specs differ"
                raise FinamMetaDataError(msg)

        self.input_grid = self.input_grid or in_info.grid
        self.input_mask = in_info.mask if self.input_mask is None else self.input_mask
        self.output_grid = self.output_grid or info.grid

        if self.input_grid.crs is None and self.output_grid.crs is not None:
            raise FinamMetaDataError("Input grid has a CRS, but output grid does not")
        if self.output_grid.crs is None and self.input_grid.crs is not None:
            raise FinamMetaDataError("output grid has a CRS, but input grid does not")

        if not self._is_initialized:
            self.downstream_mask = info.mask
            self.transformer = _create_transformer(
                self.output_grid.crs, self.input_grid.crs
            )
            self._update_grid_specs()
            # self.output_mask may be determined by "_update_grid_specs"
            self._check_and_set_out_mask()
            self._is_initialized = True

        return in_info.copy_with(grid=self.output_grid, mask=self.output_mask)

    def _check_and_set_out_mask(self):
        if self._out_mask_checked:
            return  # already done
        if (
            self.output_mask is not None
            and self.downstream_mask is not None
            and not dtools.masks_compatible(
                self.output_mask, self.downstream_mask, True
            )
        ):
            with ErrorLogger(self.logger):
                msg = (
                    "Regrid: Target mask specification is already set, new specs differ"
                )
                raise FinamMetaDataError(msg)
        self.output_mask = (
            self.output_mask if self.output_mask is not None else self.downstream_mask
        )
        # we set it to FLEX by default if no mask info is given otherwise
        if self.output_mask is None:
            self.output_mask = dtools.Mask.FLEX
        self._out_mask_checked = True

    def _need_mask(self, mask):
        return dtools.mask_specified(mask) and mask is not np.ma.nomask

    def _get_in_coords(self):
        if self._need_mask(self.input_mask):
            return self.input_grid.data_points[
                np.logical_not(self.input_mask.ravel(order=self.input_grid.order))
            ]
        return self.input_grid.data_points

    def _get_out_coords(self):
        if not self._out_mask_checked:
            with ErrorLogger(self.logger):
                msg = (
                    "Regrid: Output coordinates weren't checked for mask compatibility"
                )
                raise FinamMetaDataError(msg)
        if self._need_mask(self.output_mask):
            out_data_points = self.output_grid.data_points[
                np.logical_not(self.output_mask.ravel(order=self.output_grid.order))
            ]
        else:
            out_data_points = self.output_grid.data_points
        return _transform_points(self.transformer, out_data_points)

    def _check_in_data(self, in_data):
        if dtools.is_masked_array(in_data) and not dtools.mask_specified(
            self.input_mask
        ):
            with ErrorLogger(self.logger):
                msg = "For regridding masked input data, you need to explicitly set the mask in the input info."
                raise FinamDataError(msg)


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
    out_mask : :any:`Mask` value or valid boolean mask for :any:`MaskedArray` or None, optional
        masking specification of the regridding output. Options:
            * :any:`Mask.FLEX`: data will be unmasked
            * :any:`Mask.NONE`: data will be unmasked and given as plain numpy array
            * valid boolean mask for MaskedArray
            * None: will be determined by connected target
    tree_options : dict
        kwargs for :class:`scipy.spatial.KDTree`
    """

    def __init__(self, in_grid=None, out_grid=None, out_mask=None, tree_options=None):
        super().__init__(in_grid, out_grid, out_mask)
        self.tree_options = tree_options
        self.ids = None

    def _update_grid_specs(self):
        if self.input_grid.dim != self.output_grid.dim:
            msg = "Input grid and output grid have different dimensions"
            raise FinamMetaDataError(msg)
        # out mask not restricted by nearest interpolation
        self._check_and_set_out_mask()
        # generate IDs to select data
        kw = self.tree_options or {}
        tree = KDTree(self._get_in_coords(), **kw)
        # only store IDs, since they will be constant
        self.ids = tree.query(self._get_out_coords())[1]

    def _get_data(self, time, target):
        in_data = dtools.get_magnitude(
            dtools.strip_time(self.pull_data(time, target), self.input_grid)
        )
        self._check_in_data(in_data)
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
    out_mask : :any:`Mask` value or valid boolean mask for :any:`MaskedArray` or None, optional
        masking specification of the regridding output. Options:
            * :any:`Mask.FLEX`: data will be unmasked
            * :any:`Mask.NONE`: data will be unmasked and given as plain numpy array
            * valid boolean mask for MaskedArray
            * None: will be determined by connected target
    fill_with_nearest : bool
        Whether out of bounds points should be filled with the nearest value. Default ``False``.
    tree_options : dict
        kwargs for :class:`scipy.spatial.KDTree`
    """

    def __init__(
        self,
        in_grid=None,
        out_grid=None,
        out_mask=None,
        fill_with_nearest=False,
        tree_options=None,
    ):
        super().__init__(in_grid, out_grid, out_mask)
        self.tree_options = tree_options
        self.fill_with_nearest = bool(fill_with_nearest)
        self.ids = None
        self.inter = None
        self.out_ids = None
        self.fill_ids = None
        self.out_coords = None
        self.structured = False

    def _update_grid_specs(self):
        if isinstance(self.input_grid, StructuredGrid) and not self._need_mask(
            self.input_mask
        ):
            self.structured = True
            self.inter = RegularGridInterpolator(
                points=self.input_grid.data_axes,
                values=np.zeros(self.input_grid.data_shape, dtype=np.double),
                bounds_error=False,
            )
        else:
            in_coords = self._get_in_coords()
            self.inter = LinearNDInterpolator(
                points=in_coords,
                values=np.zeros(len(in_coords), dtype=np.double),
            )
        if self.fill_with_nearest:
            # out mask not restricted when filled with nearest
            self._check_and_set_out_mask()
            self.out_coords = self._get_out_coords()
            # check for outliers once
            res = self.inter(self.out_coords)
            self.out_ids = np.isnan(res)
            out_points = self.out_coords[self.out_ids]
            kw = self.tree_options or {}
            tree = KDTree(self._get_in_coords(), **kw)
            self.fill_ids = tree.query(out_points)[1]
        else:
            mask_save = self.output_mask
            # temporarily unmask
            self._out_mask_checked = True
            self.output_mask = np.ma.nomask
            # check for outliers once
            res = self.inter(self._get_out_coords())
            # create mask from outliers
            outlier_mask = np.ma.make_mask(
                dtools.from_compressed(
                    np.isnan(res), self.output_grid.data_shape, self.output_grid.order
                )
            )
            # determine mask from outliers
            if mask_save is None or mask_save is dtools.Mask.FLEX:
                self.output_mask = outlier_mask
            elif mask_save is dtools.Mask.NONE:
                if np.any(outlier_mask):
                    msg = "RegridLinear: interpolation is not covering desired domain."
                    raise FinamDataError(msg)
                self.output_mask = mask_save
            else:
                if not dtools.is_sub_mask(outlier_mask, mask_save):
                    msg = "RegridLinear: interpolation is not covering desired masked domain."
                    raise FinamDataError(msg)
                self.output_mask = mask_save
            self._out_mask_checked = False
            self._check_and_set_out_mask()
            self.out_coords = self._get_out_coords()

    def _get_data(self, time, target):
        in_data = dtools.get_magnitude(
            dtools.strip_time(self.pull_data(time, target), self.input_grid)
        )
        self._check_in_data(in_data)

        if self.structured:
            self.inter.values[...] = in_data
            res = self.inter(self.out_coords)
            if self.fill_with_nearest:
                res[self.out_ids] = self.inter.values.flatten(
                    order=self.input_grid.order
                )[self.fill_ids]
        else:
            in_data = dtools.to_compressed(in_data, order=self.input_grid.order)
            self.inter.values = np.ascontiguousarray(
                in_data.reshape((-1, 1)),
                dtype=np.double,
            )
            res = self.inter(self.out_coords)
            if self.fill_with_nearest:
                res[self.out_ids] = self.inter.values[self.fill_ids, 0]
        return dtools.from_compressed(
            res,
            shape=self.output_grid.data_shape,
            order=self.output_grid.order,
            mask=self.output_mask,
        )


class ToCRS(Adapter):
    """
    Convert Grid to another CRS.

    This Adapter will always create an unstructured Grid.

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        adapter = fm.adapters.ToCRS(crs="WGS84")

    Parameters
    ----------
    crs : str
        A valid crs specifier for pyproj.
    axes_attributes : list of dict or None, optional
        Axes attributes following the CF convention (in xyz order), by default None
    axes_names : list of str or None, optional
        Axes names (in xyz order), by default ["x", "y", "z"]
    assume_source_crs : str or None, optional
        If input CRS is not specified, this one will be assumed if given, by default None
    """

    def __init__(
        self, crs, axes_attributes=None, axes_names=None, assume_source_crs=None
    ):
        super().__init__()
        self.output_crs = crs
        self.input_crs = None
        self.axes_attributes = axes_attributes
        self.axes_names = axes_names
        self.assume_source_crs = assume_source_crs
        self.input_grid = None
        self.output_grid = None
        self.input_mask = None
        self.output_mask = None

    def _get_data(self, time, target):
        in_data = dtools.get_magnitude(
            dtools.strip_time(self.pull_data(time, target), self.input_grid)
        )
        return np.reshape(in_data, -1, order=self.input_grid.order)

    def _get_info(self, info):
        request = info.copy_with(grid=None, mask=None)
        in_info = self.exchange_info(request)
        if self.input_grid is None and in_info.grid is None:
            with ErrorLogger(self.logger):
                raise FinamMetaDataError("Missing source grid specification")
        self.input_grid = in_info.grid
        self.input_crs = self.input_grid.crs
        if self.input_crs is None:
            self.input_crs = self.assume_source_crs
        if self.input_crs is None:
            with ErrorLogger(self.logger):
                raise FinamMetaDataError("Input grid has no CRS")
        if self.input_mask is None and in_info.mask is None:
            with ErrorLogger(self.logger):
                raise FinamMetaDataError("Missing source mask specification")
        self.input_mask = in_info.mask
        if (
            self.output_grid is not None
            and info.grid is not None
            and self.output_grid != info.grid
        ):
            with ErrorLogger(self.logger):
                msg = "Target grid specification is already set, new specs differ"
                raise FinamMetaDataError(msg)
        if (
            dtools.mask_specified(self.input_mask)
            and self.input_mask is not np.ma.nomask
        ):
            self.output_mask = np.reshape(self.input_mask, -1, self.input_grid.order)
        else:
            self.output_mask = self.input_mask
        self.output_grid = self._create_unstructured()
        out_info = in_info.copy_with(grid=self.output_grid, mask=self.output_mask)
        return out_info

    def _create_unstructured(self):
        if not isinstance(self.input_grid, Grid):
            with ErrorLogger(self.logger):
                msg = "Given grid is not of type Grid"
                raise FinamMetaDataError(msg)
        transformer = _create_transformer(self.input_crs, self.output_crs)
        return UnstructuredGrid(
            points=_transform_points(transformer, self.input_grid.points),
            cells=self.input_grid.cells,
            cell_types=self.input_grid.cell_types,
            data_location=self.input_grid.data_location,
            order=self.input_grid.order,
            axes_attributes=self.axes_attributes,
            axes_names=self.axes_names,
            crs=self.output_crs,
        )


class ToUnstructured(Adapter):
    """
    Convert Grid to an unstructured one.

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        adapter = fm.adapters.ToUnstructured()
    """

    def __init__(self):
        super().__init__()
        self.input_grid = None
        self.output_grid = None
        self.input_mask = None
        self.output_mask = None

    def _get_data(self, time, target):
        in_data = dtools.get_magnitude(
            dtools.strip_time(self.pull_data(time, target), self.input_grid)
        )
        return np.reshape(in_data, -1, order=self.input_grid.order)

    def _get_info(self, info):
        request = info.copy_with(grid=None, mask=None)
        in_info = self.exchange_info(request)
        if self.input_grid is None and in_info.grid is None:
            with ErrorLogger(self.logger):
                raise FinamMetaDataError("Missing source grid specification")
        self.input_grid = in_info.grid
        if self.input_mask is None and in_info.mask is None:
            with ErrorLogger(self.logger):
                raise FinamMetaDataError("Missing source mask specification")
        self.input_mask = in_info.mask
        if (
            self.output_grid is not None
            and info.grid is not None
            and self.output_grid != info.grid
        ):
            with ErrorLogger(self.logger):
                msg = "Target grid specification is already set, new specs differ"
                raise FinamMetaDataError(msg)
        if (
            dtools.mask_specified(self.input_mask)
            and self.input_mask is not np.ma.nomask
        ):
            self.output_mask = np.reshape(self.input_mask, -1, self.input_grid.order)
        else:
            self.output_mask = self.input_mask
        self.output_grid = self._create_unstructured()
        out_info = in_info.copy_with(grid=self.output_grid, mask=self.output_mask)
        return out_info

    def _create_unstructured(self):
        if not isinstance(self.input_grid, Grid):
            with ErrorLogger(self.logger):
                msg = "Given grid is not of type Grid"
                raise FinamMetaDataError(msg)
        return UnstructuredGrid(
            points=self.input_grid.points,
            cells=self.input_grid.cells,
            cell_types=self.input_grid.cell_types,
            data_location=self.input_grid.data_location,
            order=self.input_grid.order,
            axes_attributes=self.input_grid.axes_attributes,
            axes_names=self.input_grid.axes_names,
            crs=self.input_grid.crs,
        )


def _create_transformer(in_crs, out_crs):
    in_crs = None if in_crs is None else pyproj.crs.CRS(in_crs)
    out_crs = None if out_crs is None else pyproj.crs.CRS(out_crs)
    return (
        None
        if (in_crs is None and out_crs is None) or in_crs == out_crs
        else pyproj.Transformer.from_crs(in_crs, out_crs, always_xy=True)
    )


def _transform_points(transformer, points):
    if transformer is None:
        return points
    return np.asarray(transformer.transform(*points.T)).T
