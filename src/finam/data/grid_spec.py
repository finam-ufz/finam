"""Grid specifications to handle spatial data with FINAM."""
import numpy as np

from .grid_tools import (
    Grid,
    Location,
    StructuredGrid,
    check_axes_monotonicity,
    gen_axes,
)


class EsriGrid(StructuredGrid):
    """
    Esri grid raster specification.

    Parameters
    ----------
    ncols : int
        Number of columns.
    nrows : int
        Number of rows.
    cellsize : float, optional
        Cell size, by default 1.0
    xllcorner : float, optional
        x value of lower left corner, by default 0.0
    yllcorner : float, optional
        y value of lower left corner, by default 0.0
    axes_attributes : list of dict or None, optional
        Axes attributes following the CF convention (xyz order), by default None
    crs : str or None, optional
        The coordinate reference system, by default None
    """

    def __init__(
        self,
        ncols,
        nrows,
        cellsize=1.0,
        xllcorner=0.0,
        yllcorner=0.0,
        axes_attributes=None,
        crs=None,
    ):
        self.ncols = int(ncols)
        self.nrows = int(nrows)
        self.cellsize = float(cellsize)
        self.xllcorner = float(xllcorner)
        self.yllcorner = float(yllcorner)
        self._axes_attributes = axes_attributes or (self.dim * [{}])
        if len(self.axes_attributes) != self.dim:
            raise ValueError("EsriGrid: wrong length of 'axes_attributes'")
        self._crs = crs

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
        header = np.loadtxt(file, dtype=str, max_rows=5)
        kwargs = {name: (float(v) if "." in v else int(v)) for (name, v) in header}
        if "xllcenter" in kwargs:
            kwargs["xllcorner"] = kwargs["xllcenter"] - 0.5 * kwargs["cellsize"]
            del kwargs["xllcenter"]
        if "yllcenter" in kwargs:
            kwargs["yllcorner"] = kwargs["yllcenter"] - 0.5 * kwargs["cellsize"]
            del kwargs["yllcenter"]
        kwargs["crs"] = crs
        kwargs["axes_attributes"] = axes_attributes
        return cls(**kwargs)

    @property
    def dims(self):
        """tuple: Axes lengths (xyz order)."""
        return (self.ncols + 1, self.nrows + 1)

    @property
    def axes(self):
        """list of np.ndarray: Axes of the structured grid in standard xyz order."""
        return gen_axes(
            dims=self.dims,
            spacing=(self.cellsize, self.cellsize),
            origin=(self.xllcorner, self.yllcorner),
        )

    @property
    def axes_reversed(self):
        """bool: Indicate reversed axes order for the associated data."""
        # esri grid data given for y/x axes
        return True

    @property
    def axes_increase(self):
        """list of bool: False to indicate a bottom axis for y."""
        # gdal and rioxarray convert esri grids to netcdf this way
        return np.array([True, False], dtype=bool)

    @property
    def axes_attributes(self):
        """list of dict: Axes attributes following the CF convention (xyz order)."""
        return self._axes_attributes

    @property
    def order(self):
        """str: Point, cell and data order (C-like)."""
        return "C"

    @property
    def dim(self):
        """int: Dimension of the grid."""
        return 2

    @property
    def crs(self):
        """The coordinate reference system."""
        return self._crs

    @property
    def data_location(self):
        """Location of the associated data."""
        return Location.CELLS


class UniformGrid(StructuredGrid):
    """Regular grid with uniform spacing in up to three coordinate directions.

    Parameters
    ----------
    dims : iterable
        Dimensions of the uniform grid for each direction.
        Spatial dimension will be determined by ``len(dims)``.
    spacing : iterable, optional
        Spacing of the uniform in each dimension.  Defaults to
        ``(1.0, 1.0, 1.0)``. Must be positive.
    origin : iterable, optional
        Origin of the uniform grid.  Defaults to ``(0.0, 0.0, 0.0)``.
    data_location : Location, optional
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
        crs=None,
    ):
        # at most 3 axes
        self._dims = tuple(dims)[:3]
        self._dim = len(self.dims)
        self.spacing = tuple(spacing)[: self.dim]
        if len(self.spacing) < self.dim:
            raise ValueError("UniformGrid: wrong length of 'spacing'")
        self.origin = tuple(origin)[: self.dim]
        if len(self.origin) < self.dim:
            raise ValueError("UniformGrid: wrong length of 'origin'")

        self._order = order
        self._axes_reversed = bool(axes_reversed)
        if axes_increase is not None:
            self._axes_increase = np.asarray(axes_increase, dtype=bool)
        else:
            self._axes_increase = np.full(self.dim, True, dtype=bool)
        if len(self.axes_increase) != self.dim:
            raise ValueError("UniformGrid: wrong length of 'axes_increase'")

        self._axes_attributes = axes_attributes or (self.dim * [{}])
        if len(self.axes_attributes) != self.dim:
            raise ValueError("UniformGrid: wrong length of 'axes_attributes'")
        self._crs = crs
        self._data_location = data_location

    @property
    def dims(self):
        """tuple: Axes lengths (xyz order)."""
        return self._dims

    @property
    def axes(self):
        """list of np.ndarray: Grid points."""
        return gen_axes(self.dims, self.spacing, self.origin)

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


class RectilinearGrid(StructuredGrid):
    """Regular grid with variable spacing in up to three coordinate directions.

    Parameters
    ----------
    axes : list of np.ndarray
        Axes defining the coordinates in each direction (xyz order).
    data_location : Location, optional
        Data location in the grid, by default Location.CELLS
    order : str, optional
        Point and cell ordering.
        Either Fortran-like ("F") or C-like ("C"), by default "F"
    axes_reversed : bool, optional
        Indicate reversed axes order for the associated data, by default False
    axes_attributes : list of dict or None, optional
        Axes attributes following the CF convention (in xyz order), by default None
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
        crs=None,
    ):
        # at most 3 axes
        self._axes = [np.asarray(np.atleast_1d(ax), dtype=float) for ax in axes[:3]]
        self._axes_increase = check_axes_monotonicity(self.axes)
        self._dim = len(self.dims)
        self._data_location = data_location
        self._order = order
        self._axes_reversed = bool(axes_reversed)
        self._axes_attributes = axes_attributes or (self.dim * [{}])
        if len(self.axes_attributes) != self.dim:
            raise ValueError("RectilinearGrid: wrong length of 'axes_attributes'")
        self._crs = crs

    @property
    def dims(self):
        """tuple: Axes lengths (xyz order)."""
        return tuple(map(len, self.axes))

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
        Cell types given as integer.
    data_location : Location, optional
        Data location in the grid, by default Location.CELLS
    crs : str or None, optional
        The coordinate reference system, by default None
    """

    def __init__(
        self,
        points,
        cells,
        cell_types,
        data_location=Location.CELLS,
        crs=None,
    ):
        # at most 3 axes
        self._points = np.asarray(np.atleast_2d(points), dtype=float)[:, :3]
        self._cells = np.asarray(np.atleast_2d(cells), dtype=int)
        self._cell_types = np.asarray(np.atleast_1d(cell_types), dtype=int)
        self._data_location = data_location
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


class UnstructuredPoints(UnstructuredGrid):
    """
    Unstructured points without cells.

    Parameters
    ----------
    points : arraylike
        Points (n, dim) defining the grid.
    crs : str or None, optional
        The coordinate reference system, by default None
    """

    def __init__(
        self,
        points,
        crs=None,
    ):
        # at most 3 axes
        pnt_cnt = len(points)
        super().__init__(
            points=points,
            cells=np.asarray([range(pnt_cnt)], dtype=int).T,
            cell_types=np.full(pnt_cnt, 0, dtype=int),
            data_location=Location.POINTS,
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
