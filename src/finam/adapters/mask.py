"""
Basic masking adapters.
"""

import numpy as np

from ..data.grid_spec import (
    Grid,
    Location,
    RectilinearGrid,
    StructuredGrid,
    UnstructuredGrid,
)
from ..data.tools import (
    Mask,
    filled,
    is_sub_mask,
    mask_specified,
    strip_time,
    to_masked,
)
from ..errors import FinamDataError, FinamMetaDataError
from ..sdk import Adapter
from ..tools.log_helper import ErrorLogger

__all__ = [
    "Masking",
    "UnMasking",
    "Clip",
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
    """
    Mask data.

    If mask is given as :attr:`Mask.NONE` this will act like the
    :class:`UnMasking` adapter.

    If the input data has flexible masking, we recommend applying
    an :class:`UnMasking` adapter first.

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        adapter = fm.adapters.Masking(mask=[True, False])

    Parameters
    ----------
    mask : :any:`Mask` value or valid boolean mask for :any:`MaskedArray`, optional
        masking specification of the data. By default the upstream mask value.

        Options:
            * valid boolean mask for MaskedArray
            * :any:`Mask.NONE`: data will be unmasked
            * :any:`Mask.FLEX`: data is unchanged but converted to a masked array

    fill_value : float or None, optional
        Fill value for masked data.
    """

    def __init__(self, mask=None, fill_value=None):
        super().__init__()
        if mask_specified(mask) and mask is not None:
            mask = np.ma.make_mask(mask, shrink=False)
        self.mask = mask
        self.fill_value = fill_value
        self.grid = None

    def _get_data(self, time, target):
        if mask_specified(self.mask):
            return to_masked(
                strip_time(self.pull_data(time, target), self.grid),
                mask=self.mask,
                fill_value=self.fill_value,
            )
        if self.mask == Mask.NONE:
            return filled(self.pull_data(time, target), self.fill_value)
        # Mask.FLEX
        return to_masked(self.pull_data(time, target), fill_value=self.fill_value)

    def _get_info(self, info):
        in_info = self.exchange_info(info.copy_with(mask=None))
        self.mask = info.mask if self.mask is None else self.mask
        if self.mask is None:
            with ErrorLogger(self.logger):
                msg = "Output mask not given."
                raise FinamMetaDataError(msg)
        if in_info.mask is not None and mask_specified(in_info.mask):
            if mask_specified(self.mask) and not is_sub_mask(in_info.mask, self.mask):
                with ErrorLogger(self.logger):
                    msg = "Given mask needs to be a sub-mask of the data mask."
                    raise FinamDataError(msg)
        self.grid = in_info.grid
        return in_info.copy_with(mask=self.mask)


class Clip(Adapter):
    """
    Clip grid to bounds.

    Node locations will be used for clipping.

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        adapter = fm.adapters.Clip(xlim=(0, 45))

    Parameters
    ----------
    xlim : tuple of float or None, optional
        Lower and Upper bound for x-axis.
    ylim : tuple of float or None, optional
        Lower and Upper bound for y-axis.
    zlim : tuple of float or None, optional
        Lower and Upper bound for z-axis.
    """

    def __init__(self, xlim=None, ylim=None, zlim=None):
        super().__init__()
        self.bounds = [xlim, ylim, zlim]
        self.input_grid = None
        self.output_grid = None
        self.input_mask = None
        self.output_mask = None
        self.select = None

    def _get_data(self, time, target):
        return strip_time(self.pull_data(time, target), self.input_grid)[self.select]

    def _get_info(self, info):
        in_info = self.exchange_info(info.copy_with(grid=None, mask=None))
        self.input_grid = in_info.grid
        self.input_mask = in_info.mask
        if self.input_grid is None:  # we need a source grid
            with ErrorLogger(self.logger):
                raise FinamMetaDataError("Missing source grid specification")
        if self.input_mask is None:  # we need a source mask
            with ErrorLogger(self.logger):
                raise FinamMetaDataError("Missing source mask specification")
        if self.output_grid is None:
            self._get_output_specs()
        return in_info.copy_with(grid=self.output_grid, mask=self.output_mask)

    def _check_sel(self, sel, axis):
        shrink = int(self.input_grid.data_location == Location.CELLS)
        if not (np.sum(sel) - shrink) > 0:
            with ErrorLogger(self.logger):
                msg = f"Empty selection along {axis=} with given clipping limits."
                raise FinamDataError(msg)

    def _mask_to_slice(self, sel):
        shrink = int(self.input_grid.data_location == Location.CELLS)
        where = np.where(sel)[0]
        return slice(where[0], where[-1] - shrink)

    def _get_output_specs(self):
        if not isinstance(self.input_grid, Grid):
            with ErrorLogger(self.logger):
                msg = "Given grid is not of type Grid"
                raise FinamDataError(msg)
        dim = self.input_grid.dim
        if isinstance(self.input_grid, StructuredGrid):
            select = dim * [slice(None)]
            axes = []
            for i in range(dim):
                if self.bounds[i] is None:
                    continue
                ax = self.input_grid.axes[i]
                sel = (ax >= self.bounds[i][0]) & (ax <= self.bounds[i][1])
                self._check_sel(sel, ("x", "y", "z")[i])
                axes.append(ax[sel])
                if not self.input_grid.axes_increase[i]:
                    sel = sel[::-1]
                select[i] = self._mask_to_slice(sel)
            rev = -1 if self.input_grid.axes_reversed else 1
            self.select = tuple(select[::rev])
            self.output_grid = RectilinearGrid(
                axes=axes,
                data_location=self.input_grid.data_location,
                order=self.input_grid.order,
                axes_reversed=self.input_grid.axes_reversed,
                axes_attributes=self.input_grid.axes_attributes,
                axes_names=self.input_grid.axes_names,
                crs=self.input_grid.crs,
            )
        else:
            # make pnt_select one item bigger
            # in cells definition -1 is a fill value
            # so we can use -1 to index pnt_select and we always get True (last entry)
            pnt_select = np.full(self.input_grid.point_count + 1, True, dtype=bool)
            for i in range(dim):
                if self.bounds[i] is None:
                    continue
                ax = self.input_grid.points[:, i]
                pnt_select[:-1] &= (ax >= self.bounds[i][0]) & (ax <= self.bounds[i][1])
            # select cells where all nodes are inside the selection
            # -1 will select last entry in pnt_select that is set to true
            cel_select = np.all(pnt_select[self.input_grid.cells], axis=1)
            if self.input_grid.data_location == Location.POINTS:
                self.select = pnt_select[:-1]
            else:
                self.select = cel_select
            if not np.any(self.select):
                with ErrorLogger(self.logger):
                    msg = "Empty selection for clipping limits."
                    raise FinamDataError(msg)
            # need a mapping of new point ids in cells definition
            pnt_map = np.full_like(pnt_select, -1, dtype=int)
            pnt_map[pnt_select] = np.arange(np.sum(pnt_select), dtype=int)
            pnt_map[-1] = -1  # map -1 in cells again to -1
            cells = pnt_map[self.input_grid.cells[cel_select]]
            self.output_grid = UnstructuredGrid(
                points=self.input_grid.points[pnt_select[:-1]],
                cells=cells,
                cell_types=self.input_grid.cell_types[cel_select],
                data_location=self.input_grid.data_location,
                order=self.input_grid.order,
                axes_attributes=self.input_grid.axes_attributes,
                axes_names=self.input_grid.axes_names,
                crs=self.input_grid.crs,
            )
        # handle mask
        if mask_specified(self.input_mask) and self.input_mask is not np.ma.nomask:
            self.output_mask = self.input_mask[self.select]
        else:
            self.output_mask = self.input_mask
