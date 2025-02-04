"""Grid specifications to handle spatial data with FINAM."""

from pathlib import Path

import numpy as np
from pyevtk.hl import imageToVTK

from ..tools.enum_helper import get_enum_value
from .esri_tools import read_header
from .grid_base import Grid, GridBase, StructuredGrid
from .grid_tools import (
    CellType,
    Location,
    check_axes_monotonicity,
    gen_axes,
    prepare_vtk_data,
    prepare_vtk_kwargs,
)


def _check_location(grid, data_location):
    # need to define this here to prevent circular imports
    location = get_enum_value(data_location, Location)
    if location not in grid.valid_locations:
        msg = f"{grid.name}: data location {location} not valid."
        raise ValueError(msg)
    return location


class NoGrid(GridBase):
    """
    Indicator for data without a spatial grid.

    Parameters
    ----------
    dim : int or None, optional
        Data dimensionality. Should match the length of data_shape.
    data_shape : tuple of int or None, optional
        Data shape. Can contain -1 to indicate flexible axis.

    Raises
    ------
    ValueError
        If dim does not match the length of data_shape.
    """

    def __init__(self, dim=None, data_shape=None):
        if dim is None and data_shape is None:
            dim, data_shape = 0, tuple()
        if data_shape is None:
            data_shape = (-1,) * dim
        if dim is None:
            dim = len(data_shape)
        if dim != len(data_shape):
            msg = "NoGrid: dim needs to match the length of data_shape."
            raise ValueError(msg)
        self._dim = dim
        self._data_shape = data_shape

    @property
    def dim(self):
        """int: Dimension of the grid or data."""
        return self._dim

    @property
    def data_shape(self):
        """tuple: Shape of the associated data."""
        return self._data_shape

    # pylint: disable-next=unused-argument
    def compatible_with(self, other, check_location=True):
        """
        Check for compatibility with other Grid.

        Parameters
        ----------
        other : instance of Grid
            Other grid to compatibility with.
        check_location : bool, optional
            Whether to check location for equality, by default True

        Returns
        -------
        bool
            compatibility
        """
        return isinstance(other, NoGrid) and self.data_shape == other.data_shape

    def __eq__(self, other):
        return self.compatible_with(other)


class RectilinearGrid(StructuredGrid):
    """Regular grid with variable spacing in up to three coordinate directions.

    Parameters
    ----------
    axes : list of np.ndarray
        Axes defining the point coordinates in each direction (xyz order).
    data_location : Location, str, int, optional
        Data location in the grid, by default Location.CELLS
    order : str, optional
        Point and cell ordering.
        Either Fortran-like ("F") or C-like ("C"), by default "F"
    axes_reversed : bool, optional
        Indicate reversed axes order for the associated data, by default False
    axes_attributes : list of dict or None, optional
        Axes attributes following the CF convention (in xyz order), by default None
    axes_names : list of str or None, optional
        Axes names (in xyz order), by default ["x", "y", "z"]
    crs : str or None, optional
        The coordinate reference system, by default None
    """

    def __init__(
        self,
        axes,
        data_location=Location.CELLS,
        order="F",
        axes_reversed=False,
        axes_attributes=None,
        axes_names=None,
        crs=None,
    ):
        # at most 3 axes
        self._axes = [np.asarray(np.atleast_1d(ax), dtype=float) for ax in axes[:3]]
        # all axes made increasing
        self._axes_increase = check_axes_monotonicity(self.axes)
        self._dim = len(self.dims)
        self._data_location = None
        self.data_location = data_location
        self._order = order
        self._axes_reversed = bool(axes_reversed)
        self._axes_attributes = axes_attributes or (self.dim * [{}])
        if len(self.axes_attributes) != self.dim:
            raise ValueError("RectilinearGrid: wrong length of 'axes_attributes'")
        self._axes_names = axes_names or ["x", "y", "z"][: self.dim]
        if len(self.axes_names) != self.dim:
            raise ValueError("RectilinearGrid: wrong length of 'axes_names'")
        self._crs = crs

        self._data_shape = None
        self._data_size = None

    def to_unstructured(self):
        """
        Cast grid to an unstructured grid.

        Returns
        -------
        UnstructuredGrid
            Grid as unstructured grid.
        """
        return UnstructuredGrid(
            points=self.points,
            cells=self.cells,
            cell_types=self.cell_types,
            data_location=self.data_location,
            order=self.order,
            axes_attributes=self.axes_attributes,
            axes_names=self.axes_names,
            crs=self.crs,
        )

    @property
    def dims(self):
        """tuple: Axes lengths (xyz order)."""
        return tuple(map(len, self.axes))

    @property
    def data_shape(self):
        """tuple: Shape of the associated data."""
        if self._data_shape is None:
            self._data_shape = super().data_shape
        return self._data_shape

    @property
    def data_size(self):
        """int: Size of the associated data."""
        if self._data_size is None:
            self._data_size = super().data_size
        return self._data_size

    @property
    def axes(self):
        """list of np.ndarray: Grid points."""
        return self._axes

    @property
    def axes_reversed(self):
        """bool: Indicate reversed axes order for the associated data."""
        return self._axes_reversed

    @property
    def axes_increase(self):
        """list of bool: False to indicate a bottom up axis (xyz order)."""
        return self._axes_increase

    @property
    def axes_attributes(self):
        """list of dict: Axes attributes following the CF convention (xyz order)."""
        return self._axes_attributes

    @property
    def axes_names(self):
        """list of str: Axes names (xyz order)."""
        return self._axes_names

    @property
    def order(self):
        """str: Point, cell and data order (C- or Fortran-like)."""
        # vtk files use Fortran-like data ordering for structured grids
        return self._order

    @property
    def dim(self):
        """int: Dimension of the grid."""
        return self._dim

    @property
    def crs(self):
        """The coordinate reference system."""
        return self._crs

    @property
    def data_location(self):
        """Location of the associated data (either CELLS or POINTS)."""
        return self._data_location

    @data_location.setter
    def data_location(self, data_location):
        """Set location of the associated data (either CELLS or POINTS)."""
        self._data_location = _check_location(self, data_location)


class UniformGrid(RectilinearGrid):
    """Regular grid with uniform spacing in up to three coordinate directions.

    Parameters
    ----------
    dims : iterable
        Dimensions of the uniform grid for each direction.
        Spatial dimension will be determined by ``len(dims)``.
        Dimensions refer to the number of points, independent of ``data_location``.
    spacing : iterable, optional
        Spacing of the uniform in each dimension.  Defaults to
        ``(1.0, 1.0, 1.0)``. Must be positive.
    origin : iterable, optional
        Origin of the uniform grid.  Defaults to ``(0.0, 0.0, 0.0)``.
    data_location : Location, str, int, optional
        Data location in the grid, by default Location.CELLS
    order : str, optional
        Point and cell ordering.
        Either Fortran-like ("F") or C-like ("C"), by default "F"
    axes_reversed : bool, optional
        Indicate reversed axes order for the associated data, by default False
    axes_increase : arraylike or None, optional
        False to indicate a bottom up axis (xyz order), by default None
    axes_attributes : list of dict or None, optional
        Axes attributes following the CF convention (xyz order), by default None
    axes_names : list of str or None, optional
        Axes names (in xyz order), by default ["x", "y", "z"]
    crs : str or None, optional
        The coordinate reference system, by default None
    """

    def __init__(
        self,
        dims,
        spacing=(1.0, 1.0, 1.0),
        origin=(0.0, 0.0, 0.0),
        data_location=Location.CELLS,
        order="F",
        axes_reversed=False,
        axes_increase=None,
        axes_attributes=None,
        axes_names=None,
        crs=None,
    ):
        # at most 3 axes
        dims = tuple(dims)[:3]
        self.spacing = tuple(spacing)[: len(dims)]
        if len(self.spacing) < len(dims):
            raise ValueError("UniformGrid: wrong length of 'spacing'")
        self.origin = tuple(origin)[: len(dims)]
        if len(self.origin) < len(dims):
            raise ValueError("UniformGrid: wrong length of 'origin'")
        super().__init__(
            axes=gen_axes(dims, self.spacing, self.origin, axes_increase),
            data_location=data_location,
            order=order,
            axes_reversed=axes_reversed,
            axes_attributes=axes_attributes,
            axes_names=axes_names,
            crs=crs,
        )

    def export_vtk(
        self,
        path,
        data=None,
        cell_data=None,
        point_data=None,
        field_data=None,
        mesh_type="uniform",
    ):
        """
        Export grid and data to a VTK file.

        Parameters
        ----------
        path : pathlike
            File path.
            Suffix will be replaced according to mesh type (.vti, .vtr, .vtu)
        data : dict or None, optional
            Data in the corresponding shape given by name, by default None
        cell_data : dict or None, optional
            Additional cell data, by default None
        point_data : dict or None, optional
            Additional point data, by default None
        field_data : dict or None, optional
            Additional field data, by default None
        mesh_type : str, optional
            Mesh type ("uniform"/"structured"/"unstructured"),
            by default "structured"

        Raises
        ------
        ValueError
            If mesh type is not supported.
        """
        if mesh_type != "uniform":
            super().export_vtk(path, data, cell_data, point_data, field_data, mesh_type)
        else:
            data = prepare_vtk_data(data, self.axes_reversed, self.axes_increase)
            kw = prepare_vtk_kwargs(
                self.data_location, data, cell_data, point_data, field_data
            )
            path = str(Path(path).with_suffix(""))
            origin = self.origin + (0.0,) * (3 - self.dim)
            spacing = self.spacing + (0.0,) * (3 - self.dim)
            imageToVTK(path, origin, spacing, **kw)

    def to_rectilinear(self):
        """
        Cast grid to a rectilinear grid.

        Returns
        -------
        UniformGrid
            Grid as rectilinear grid.
        """
        grid = RectilinearGrid(
            axes=self.axes,
            data_location=self.data_location,
            order=self.order,
            axes_reversed=self.axes_reversed,
            axes_attributes=self.axes_attributes,
            axes_names=self.axes_names,
            crs=self.crs,
        )
        # pylint: disable-next=protected-access
        grid._axes_increase = self.axes_increase
        return grid


class EsriGrid(UniformGrid):
    """
    Esri grid raster specification.

    Parameters
    ----------
    ncols : int
        Number of grid columns, in cells.
    nrows : int
        Number of grid rows, in cells.
    cellsize : float, optional
        Cell size, by default 1.0
    xllcorner : float, optional
        x value of lower left corner, by default 0.0
    yllcorner : float, optional
        y value of lower left corner, by default 0.0
    order : str, optional
        Point and cell ordering.
        Either Fortran-like ("F") or C-like ("C"), by default "C"
    axes_attributes : list of dict or None, optional
        Axes attributes following the CF convention (xyz order), by default None
    axes_names : list of str or None, optional
        Axes names (in xyz order), by default ["x", "y", "z"]
    crs : str or None, optional
        The coordinate reference system, by default None
    """

    valid_locations = (Location.CELLS,)
    """tuple: Valid locations for the grid."""

    def __init__(
        self,
        ncols,
        nrows,
        cellsize=1.0,
        xllcorner=0.0,
        yllcorner=0.0,
        order="C",
        axes_attributes=None,
        axes_names=None,
        crs=None,
    ):
        self.ncols = int(ncols)
        self.nrows = int(nrows)
        self.cellsize = float(cellsize)
        self.xllcorner = float(xllcorner)
        self.yllcorner = float(yllcorner)
        super().__init__(
            dims=(self.ncols + 1, self.nrows + 1),
            spacing=(self.cellsize, self.cellsize),
            origin=(self.xllcorner, self.yllcorner),
            order=order,
            axes_reversed=True,
            axes_increase=(True, False),
            axes_attributes=axes_attributes,
            axes_names=axes_names,
            crs=crs,
        )

    @classmethod
    def from_file(cls, file, axes_attributes=None, crs=None):
        """
        Generate EsriGrid from given file.

        Parameters
        ----------
        file : pathlike
            Path to the esri grid file
        axes_attributes : list of dict or None, optional
            Axes attributes following the CF convention (xyz order), by default None
        crs : str or None, optional
            The coordinate reference system, by default None

        Returns
        -------
        EsriGrid
            The grid specified in the file.
        """
        header = read_header(file)
        header.pop("nodata_value", None)
        header["crs"] = crs
        header["axes_attributes"] = axes_attributes
        return cls(**header)

    def to_uniform(self):
        """
        Cast grid to an uniform grid.

        Returns
        -------
        UniformGrid
            Grid as uniform grid.
        """
        return UniformGrid(
            dims=self.dims,
            spacing=self.spacing,
            origin=self.origin,
            data_location=self.data_location,
            order=self.order,
            axes_reversed=self.axes_reversed,
            axes_increase=self.axes_increase,
            axes_attributes=self.axes_attributes,
            axes_names=self.axes_names,
            crs=self.crs,
        )


class UnstructuredGrid(Grid):
    """
    Unstructured grid specification.

    Parameters
    ----------
    points : arraylike
        Points (n, dim) defining the grid.
    cells : arraylike
        Cells given by set list of point IDs defining the grid.
    cell_types : arraylike
        Cell types given as integer, e.g. CellType.TRI.
    data_location : Location, str, int, optional
        Data location in the grid, by default Location.CELLS
    order : str, optional
        Data ordering.
        Either Fortran-like ("F") or C-like ("C"), by default "C"
    axes_attributes : list of dict or None, optional
        Axes attributes following the CF convention (in xyz order), by default None
    axes_names : list of str or None, optional
        Axes names (in xyz order), by default ["x", "y", "z"]
    crs : str or None, optional
        The coordinate reference system, by default None
    """

    def __init__(
        self,
        points,
        cells,
        cell_types,
        data_location=Location.CELLS,
        order="C",
        axes_attributes=None,
        axes_names=None,
        crs=None,
    ):
        # at most 3 axes
        self._points = np.asarray(np.atleast_2d(points), dtype=float)[:, :3]
        self._cells = np.asarray(np.atleast_2d(cells), dtype=int)
        self._cell_types = np.asarray(np.atleast_1d(cell_types), dtype=int)
        self._data_location = None
        self.data_location = data_location
        self._order = order
        self._axes_attributes = axes_attributes or (self.dim * [{}])
        if len(self.axes_attributes) != self.dim:
            raise ValueError("UnstructuredGrid: wrong length of 'axes_attributes'")
        self._axes_names = axes_names or ["x", "y", "z"][: self.dim]
        if len(self.axes_names) != self.dim:
            raise ValueError("UnstructuredGrid: wrong length of 'axes_names'")

        self._crs = crs

    @property
    def dim(self):
        """int: Dimension of the grid."""
        return self.points.shape[1]

    @property
    def crs(self):
        """The coordinate reference system."""
        return self._crs

    @property
    def point_count(self):
        """int: Number of grid points."""
        return len(self.points)

    @property
    def cell_count(self):
        """int: Number of grid cells."""
        return len(self.cells)

    @property
    def points(self):
        """np.ndarray: Grid points."""
        return self._points

    @property
    def data_shape(self):
        """np.ndarray: Grid points."""
        return (
            (len(self.points),)
            if self.data_location == Location.POINTS
            else (len(self.cells),)
        )

    @property
    def data_size(self):
        """int: Size of the associated data."""
        return (
            len(self.points)
            if self.data_location == Location.POINTS
            else len(self.cells)
        )

    @property
    def cells(self):
        """np.ndarray: Cell nodes in ESMF format."""
        return self._cells

    @property
    def cell_types(self):
        """np.ndarray: Cell types."""
        return self._cell_types

    @property
    def data_location(self):
        """Location of the associated data (either CELLS or POINTS)."""
        return self._data_location

    @data_location.setter
    def data_location(self, data_location):
        """Set location of the associated data (either CELLS or POINTS)."""
        self._data_location = _check_location(self, data_location)

    @property
    def order(self):
        """str: Point, cell and data order (C-like or F-like for flatten)."""
        return self._order

    @property
    def axes_attributes(self):
        """list of dict: Axes attributes following the CF convention (xyz order)."""
        return self._axes_attributes

    @property
    def axes_names(self):
        """list of str: Axes names (xyz order)."""
        return self._axes_names


class UnstructuredPoints(UnstructuredGrid):
    """
    Unstructured points without cells.

    Parameters
    ----------
    points : arraylike
        Points (n, dim) defining the grid.
    order : str, optional
        Data ordering.
        Either Fortran-like ("F") or C-like ("C"), by default "C"
    axes_attributes : list of dict or None, optional
        Axes attributes following the CF convention (in xyz order), by default None
    axes_names : list of str or None, optional
        Axes names (in xyz order), by default ["x", "y", "z"]
    crs : str or None, optional
        The coordinate reference system, by default None
    """

    valid_locations = (Location.POINTS,)
    """tuple: Valid locations for the grid."""

    def __init__(
        self,
        points,
        order="C",
        axes_attributes=None,
        axes_names=None,
        crs=None,
    ):
        # at most 3 axes
        pnt_cnt = len(points)
        super().__init__(
            points=points,
            cells=np.asarray([range(pnt_cnt)], dtype=int).T,
            cell_types=np.full(pnt_cnt, CellType.VERTEX, dtype=int),
            data_location=Location.POINTS,
            order=order,
            axes_attributes=axes_attributes,
            axes_names=axes_names,
            crs=crs,
        )

    @property
    def cell_centers(self):
        """np.ndarray: Grid cell centers."""
        return self.points

    @property
    def cell_node_counts(self):
        """np.ndarray: Node count for each cell."""
        return np.full(self.point_count, 1, dtype=int)

    @property
    def mesh_dim(self):
        """int: Maximal cell dimension."""
        return 0
