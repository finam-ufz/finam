"""Grid tools for FINAM."""
from abc import ABC, abstractmethod
from enum import Enum, IntEnum
from math import isclose, nan
from pathlib import Path

import numpy as np
from pyevtk.hl import gridToVTK, unstructuredGridToVTK


def point_order(order, axes_reversed=False):
    """
    Determine apparent point order incorporating axes order reversion.

    Parameters
    ----------
    order : str
        Point and cell ordering.
        Either Fortran-like ("F") or C-like ("C"), by default "F"
    axes_reversed : arraylike or None, optional
        Indicate reversed axes order for the associated data, by default False

    Returns
    -------
    str
        Apparent point ordering.
    """
    reverse_order = {"C": "F", "F": "C"}
    return reverse_order[order] if axes_reversed else order


def order_map(shape, of="F", to="C"):
    """
    Generate order mapping.

    Parameters
    ----------
    shape : tuple
        Array shape of interest.
    of : str, optional
        Starting ordering.
        Either Fortran-like ("F") or C-like ("C"), by default "F"
    to : str, optional
        Target ordering.
        Either Fortran-like ("F") or C-like ("C"), by default "C"

    Returns
    -------
    np.ndarray
        Mapping indices.
    """
    size = np.prod(shape)
    return np.arange(size, dtype=int).reshape(shape, order=of).reshape(-1, order=to)


def gen_node_centers(grid):
    """
    Calculate the node centers of the given grid cells.

    Parameters
    ----------
    grid : Grid
        Grid to take the cells from.

    Returns
    -------
    np.ndarray
        Centroids for all cells.
    """
    if not isinstance(grid, Grid):
        raise ValueError("gen_node_centers: given grid is not a grid specification.")
    unique_cell_types = np.unique(grid.cell_types)
    result = np.empty((grid.cell_count, grid.dim), dtype=float)
    for ctype in unique_cell_types:
        # select current cell type
        sel = grid.cell_types == ctype
        points = grid.points[grid.cells[sel][:, : NODE_COUNT[ctype]]]
        result[sel] = np.mean(points, axis=1)
    return result


def gen_axes(dims, spacing, origin, axes_increase=None):
    """
    Generate uniform axes.

    Parameters
    ----------
    dims : iterable
        Dimensions of the uniform grid for each direction.
    spacing : iterable
        Spacing of the uniform in each dimension. Must be positive.
    origin : iterable
        Origin of the uniform grid.
    axes_increase : arraylike or None, optional
        False to indicate a bottom up axis (in xyz order), by default None

    Returns
    -------
    list of np.ndarray
        Axes of the uniform grid.
    """
    if axes_increase is None:
        axes_increase = np.full(len(dims), True, dtype=bool)
    if len(axes_increase) != len(dims):
        raise ValueError("gen_axes: wrong length of 'axes_increase'")
    axes = []
    for i, d in enumerate(dims):
        axes.append(np.arange(d) * spacing[i] + origin[i])
        if not axes_increase[i]:
            axes[i] = axes[i][::-1]
    return axes


def gen_points(axes, order="F", axes_increase=None):
    """
    Generate points from axes of a rectilinear grid.

    Parameters
    ----------
    axes : list of np.ndarray
        Axes defining the coordinates in each direction (xyz order).
    order : str, optional
        Point and cell ordering.
        Either Fortran-like ("F") or C-like ("C"), by default "F"
    axes_increase : arraylike or None, optional
        False to indicate a bottom up axis (in xyz order), by default None

    Returns
    -------
    np.ndarray
        Points of the grid in given order and orientation.
    """
    if axes_increase is None:
        axes_increase = np.full(len(axes), True, dtype=bool)
    axes = list(axes)
    for i, inc in enumerate(axes_increase):
        if not inc:
            axes[i] = axes[i][::-1]
    dim = len(axes)
    # append empty dimensions
    for _ in range(dim, 3):
        axes.append(np.zeros(1, dtype=float))
    x_dim = len(axes[0])
    y_dim = len(axes[1])
    z_dim = len(axes[2])
    pnt_cnt = x_dim * y_dim * z_dim
    x_id, y_id, z_id = np.mgrid[0:x_dim, 0:y_dim, 0:z_dim]
    points = np.empty((pnt_cnt, 3), dtype=float)
    # VTK sorts points and cells in Fortran order
    points[:, 0] = axes[0][x_id.reshape(-1, order=order)]
    points[:, 1] = axes[1][y_id.reshape(-1, order=order)]
    points[:, 2] = axes[2][z_id.reshape(-1, order=order)]
    return points[:, :dim]


def gen_cells(dims, order="F"):
    """
    Generate cells from dimensions of a structured grid.

    Parameters
    ----------
    dims : iterable
        Dimensions of the structured grid for each direction.
    order : str, optional
        Point and cell ordering.
        Either Fortran-like ("F") or C-like ("C"), by default "F"

    Returns
    -------
    np.ndarray
        Cell definitions containing the list of node IDs for each cell.
    """
    # sort out empty dimensions
    c_dim = [d - 1 for d in dims if d > 1]
    c_cnt = int(np.prod(c_dim))
    mesh_dim = len(c_dim)
    c_rng = np.arange(c_cnt, dtype=int)
    if mesh_dim == 0:
        # cells are vertices in 0D
        c = np.array([[0]], dtype=int)
    elif mesh_dim == 1:
        # cells are lines in 1D
        c = np.empty((c_cnt, 2), dtype=int)
        c[:, 0] = c_rng
        c[:, 1] = c[:, 0] + 1
    elif mesh_dim == 2:
        # cells are quad in 2D
        c = np.empty((c_cnt, 4), dtype=int)
        # top left corner (last node in cell definition)
        c[:, 3] = c_rng
        c[:, 3] += c_rng // c_dim[0]
        # top right corner one ID higher than left
        c[:, 2] = c[:, 3] + 1
        # lower right corner two IDs higher than top left in next row
        c[:, 1] = c[:, 3] + 2 + c_dim[0]
        # lower left corner one ID lower than right
        c[:, 0] = c[:, 1] - 1
    else:
        # cells are hex in 3D
        c = np.empty((c_cnt, 8), dtype=int)
        # ? should upper and lower layer be swapped?
        # upper layer
        c[:, 3] = c_rng
        c[:, 3] += (c_dim[0] + c_dim[1] + 1) * (c_rng // (c_dim[0] * c_dim[1]))
        c[:, 3] += (c_rng % (c_dim[0] * c_dim[1])) // c_dim[0]
        c[:, 2] = c[:, 3] + 1
        c[:, 1] = c[:, 3] + 2 + c_dim[0]
        c[:, 0] = c[:, 1] - 1
        # lower layer
        c[:, 7] = c[:, 3] + (1 + c_dim[0]) * (1 + c_dim[1])
        c[:, 6] = c[:, 7] + 1
        c[:, 5] = c[:, 7] + 2 + c_dim[0]
        c[:, 4] = c[:, 5] - 1
    if order == "C" and mesh_dim > 1:
        # inverse reorder point ids
        c = order_map(dims, of="C", to="F")[c]
        # reorder cells
        c = c[order_map(c_dim, of="F", to="C")]
    return c


def check_axes_monotonicity(axes):
    """
    Check axes to be strictly monotonic, and makes them strictly monotonic increasing.

    Parameters
    ----------
    axes : list of np.ndarray
        Axes defining the coordinates in each direction (xyz order).
        Will be modified inplace to be increasing.

    Returns
    -------
    axes_increase : list of bool
        False to indicate a bottom up axis.

    Raises
    ------
    ValueError
        In case an axis in not strictly monotonic.
    """
    axes_increase = np.empty(len(axes), dtype=bool)
    for i, ax in enumerate(axes):
        if len(ax) == 1:
            axes_increase[i] = True
            continue
        dx = ax[1:] - ax[:-1]
        if np.all(dx > 0):
            axes_increase[i] = True
        elif np.all(dx < 0):
            ax[:] = ax[::-1]
            axes_increase[i] = False
        else:
            raise ValueError(f"Grid: axes[{i}] not strictly monotonic.")
    return axes_increase


def check_axes_uniformity(axes):
    """
    Check axes to be uniform.

    Parameters
    ----------
    axes : list of np.ndarray
        Axes defining the coordinates in each direction (xyz order).

    Returns
    -------
    is_uniform : list of float
        Spacing or NaN for each axis. NaN indicates non-uniformity
    """
    return [check_uniformity(ax) for ax in axes]


def check_uniformity(values):
    """Checks for uniform spacing of values

    Parameters
    ----------
    values : np.ndarray
        Values to check.

    Returns
    -------
    is_uniform : float
        Average spacing, of NaN if not uniform.
    """
    delta = None
    for i in range(len(values) - 1):
        d = values[i + 1] - values[i]
        if delta is None:
            delta = d
        elif not isclose(delta, d):
            return nan

    return (values[-1] - values[0]) / (len(values) - 1)


def prepare_vtk_kwargs(data_location, data, cell_data, point_data, field_data):
    """
    Prepare keyword arguments for evtk routines.

    Parameters
    ----------
    data_location : Location
        Data location in the grid, by default Location.CELLS
    data : dict or None
        Data in the corresponding shape given by name
    cell_data : dict or None
        Additional cell data
    point_data : dict or None
        Additional point data
    field_data : dict or None
        Additional field data

    Returns
    -------
    dict
        Keyword arguments.
    """
    cdat = data_location == Location.CELLS
    kw = {"cellData": None, "pointData": None, "fieldData": None}
    kw["cellData" if cdat else "pointData"] = data
    if kw["cellData"]:
        kw["cellData"].update(cell_data if cell_data is not None else {})
    else:
        kw["cellData"] = cell_data
    if kw["pointData"]:
        kw["pointData"].update(point_data if point_data is not None else {})
    else:
        kw["pointData"] = point_data
    kw["fieldData"] = field_data
    return kw


def prepare_vtk_data(
    data, axes_reversed=False, axes_increase=None, flat=False, order="F"
):
    """
    Prepare data dictionary for VTK export.

    Parameters
    ----------
    data : dict or None
        Dictionary containing data arrays by name.
    axes_reversed : bool, optional
        Indicate reversed axes order for the associated data, by default False
    axes_increase : arraylike or None, optional
        False to indicate a bottom up axis (xyz order), by default None
    flat : bool, optional
        True to flatten data, by default False
    order : str, optional
        Point and cell ordering.
        Either Fortran-like ("F") or C-like ("C"), by default "F"

    Returns
    -------
    dict or None
        Prepared data.
    """
    if data is not None:
        data = dict(data)
        for name, value in data.items():
            data[name] = np.ascontiguousarray(
                _prepare(value, axes_reversed, axes_increase, flat, order)
            )
    return data


def _prepare(data, axes_reversed, axes_increase, flat, order):
    if axes_increase is not None and data.ndim != len(axes_increase):
        raise ValueError("prepare_vtk_data: data has wrong dimension.")
    if axes_increase is None:
        axes_increase = np.full(data.ndim, True, dtype=bool)
    if axes_reversed and data.ndim > 1:
        data = data.T
    for i, inc in enumerate(axes_increase):
        # only flip if not converting to unstructured
        if not (inc or flat):
            data = np.flip(data, axis=i)
    # get 3D or flat shape
    shape = -1 if flat else (data.shape + (1,) * (3 - data.ndim))
    return data.reshape(shape, order=order)


def canonical_data(data, grid, flat=False):
    """
    Make data canonical.

    Data axes will follow increasing (x, y, z) axes.

    Parameters
    ----------
    data : numpy.ndarray
        The data to be made canonical
    grid : Grid
            grid specification
    flat : bool, optional
        True to flatten data, by default False

    Returns
    -------
    numpy.ndarray
        The canonical data array.
    """
    if not isinstance(grid, Grid):
        raise ValueError("canonical_data: grid is not an instance of Grid.")
    flat = flat or not isinstance(grid, StructuredGrid)
    axes_reversed = getattr(grid, "axes_reversed", False)
    axes_increase = getattr(grid, "axes_increase", None)
    res = _prepare(data, axes_reversed, axes_increase, flat, grid.order)
    # remove appended dimensions
    return res if flat else np.squeeze(res, axis=tuple(range(grid.dim, 3)))


def flatten_cells(cells):
    """
    Flatten cells array.

    Parameters
    ----------
    cells : np.ndarray
        Cells given as 2D array containing cell defining node IDs.
        -1 will be interpreted as used entries.

    Returns
    -------
    np.ndarray
        All cell definitions concatenated.
    """
    if cells.ndim == 1:
        return cells
    # unused entries in "cells" marked with "-1"
    return np.ma.masked_values(cells, -1).compressed()


class Location(Enum):
    """Data location in the grid."""

    CELLS = 0
    POINTS = 1


class CellType(IntEnum):
    """Supported cell types."""

    # VTK and ESMF cell node order is counter clockwise
    # https://kitware.github.io/vtk-examples/site/VTKFileFormats/#legacy-file-examples
    # https://earthsystemmodeling.org/docs/release/latest/ESMF_refdoc/node5.html#const:meshelemtype

    # vertex for no-cell meshes
    VERTEX = 0
    # lines for 1D
    LINE = 1
    # 2D following ESMF
    TRI = 2
    QUAD = 3
    # 3D following ESMF
    TETRA = 4
    HEX = 5


NODE_COUNT = np.array([1, 2, 3, 4, 4, 8], dtype=int)
"""np.ndarray: Node numbers per CellType."""


CELL_DIM = np.array([0, 1, 2, 2, 3, 3], dtype=int)
"""np.ndarray: Cell dimension per CellType."""


VTK_TYPE_MAP = np.array([1, 3, 5, 9, 10, 12], dtype=int)
"""np.ndarray: Cell dimension per CellType."""


ESMF_TYPE_MAP = np.array([-1, -1, 3, 4, 10, 12], dtype=int)
"""np.ndarray: Cell dimension per CellType."""


class GridBase(ABC):
    """Abstract grid base."""

    @property
    def name(self):
        """Grid name."""
        return self.__class__.__name__

    @property
    @abstractmethod
    def dim(self):
        """int: Dimension of the grid or data."""


class Grid(GridBase):
    """Abstract grid specification."""

    @property
    @abstractmethod
    def crs(self):
        """The coordinate reference system."""

    @property
    @abstractmethod
    def point_count(self):
        """int: Number of grid points."""

    @property
    @abstractmethod
    def cell_count(self):
        """int: Number of grid cells."""

    @property
    @abstractmethod
    def points(self):
        """np.ndarray: Grid points."""

    @property
    @abstractmethod
    def cells(self):
        """np.ndarray: Cell nodes in ESMF format."""

    @property
    @abstractmethod
    def cell_types(self):
        """np.ndarray: Cell types."""

    @property
    def cell_centers(self):
        """np.ndarray: Grid cell centers."""
        return gen_node_centers(self)

    @property
    def cell_node_counts(self):
        """np.ndarray: Node count for each cell."""
        return NODE_COUNT[self.cell_types]

    @property
    def mesh_dim(self):
        """int: Maximal cell dimension."""
        return np.max(CELL_DIM[self.cell_types])

    @property
    @abstractmethod
    def data_location(self):
        """Location of the associated data (either CELLS or POINTS)."""

    @property
    def data_points(self):
        """Points of the associated data (either cell_centers or points)."""
        if self.data_location == Location.POINTS:
            return self.points
        return self.cell_centers

    @property
    @abstractmethod
    def data_shape(self):
        """tuple: Shape of the associated data."""

    @property
    def data_size(self):
        """int: Size of the associated data."""
        return np.prod(self.data_shape)

    @property
    @abstractmethod
    def order(self):
        """str: Data order (C-like or F-like to flatten data)."""

    @property
    @abstractmethod
    def axes_names(self):
        """list of str: Axes names (xyz order)."""

    @property
    def data_axes_names(self):
        """list of str: Axes names of the data."""
        return ["id"]

    def __repr__(self):
        return f"{self.__class__.__name__} ({self.dim}D) {self.data_shape}"

    def __eq__(self, other):
        if not isinstance(other, Grid):
            return False

        if isinstance(self, StructuredGrid) != isinstance(other, StructuredGrid):
            return False

        return (
            self.dim == other.dim
            and self.crs == other.crs
            and self.order == other.order
            and self.data_location == other.data_location
            and self.data_shape == other.data_shape
            and np.allclose(self.data_points, other.data_points)
        )

    def export_vtk(
        self,
        path,
        data=None,
        cell_data=None,
        point_data=None,
        field_data=None,
        mesh_type="unstructured",
    ):
        """
        Export grid and data to a VTK file.

        Parameters
        ----------
        path : pathlike
            File path. Suffix will be replaced according to mesh type (.vtu)
        data : dict or None, optional
            Data in the corresponding shape given by name, by default None
        cell_data : dict or None, optional
            Additional cell data, by default None
        point_data : dict or None, optional
            Additional point data, by default None
        field_data : dict or None, optional
            Additional field data, by default None
        mesh_type : str, optional
            Mesh type, by default "unstructured"

        Raises
        ------
        ValueError
            If mesh type is not supported.
        """
        data = prepare_vtk_data(data, flat=True)
        kw = prepare_vtk_kwargs(
            self.data_location, data, cell_data, point_data, field_data
        )
        if mesh_type == "unstructured":
            path = str(Path(path).with_suffix(""))
            # don't create increasing axes
            points = self.points
            x = np.ascontiguousarray(points[:, 0])
            y = np.ascontiguousarray(points[:, 1] if self.dim > 1 else np.zeros_like(x))
            z = np.ascontiguousarray(points[:, 2] if self.dim > 2 else np.zeros_like(x))
            con = flatten_cells(self.cells)
            off = np.cumsum(NODE_COUNT[self.cell_types])
            typ = VTK_TYPE_MAP[self.cell_types]
            unstructuredGridToVTK(path, x, y, z, con, off, typ, **kw)
        else:
            raise ValueError(f"export_vtk: unsupported mesh type '{mesh_type}'")


class StructuredGrid(Grid):
    """Abstract structured grid specification."""

    @property
    @abstractmethod
    def dims(self):
        """tuple: Axes lengths (xyz order)."""

    @property
    @abstractmethod
    def axes(self):
        """list of np.ndarray: Axes of the structured grid in standard xyz order."""

    @property
    @abstractmethod
    def axes_reversed(self):
        """bool: Indicate reversed axes order for the associated data (zyx order)."""
        # esri grids and most netcdf files are given in inverse axes order (lat, lon)

    @property
    @abstractmethod
    def axes_increase(self):
        """list of bool: False to indicate a bottom up axis (xyz order)."""
        # esri grids and some netcdf are given bottom up (northing/lat inverted)

    @property
    @abstractmethod
    def axes_attributes(self):
        """list of dict: Axes attributes following the CF convention (xyz order)."""

    @property
    @abstractmethod
    def order(self):
        """str: Point, cell and data order (C- or Fortran-like)."""
        # vtk files use Fortran-like data ordering for structured grids

    @property
    def point_count(self):
        """int: Number of grid points."""
        # allow dims entries to be 1 (flat mesh in space)
        return np.prod(self.dims)

    @property
    def cell_count(self):
        """int: Number of grid cells."""
        return np.prod(np.maximum(np.array(self.dims) - 1, 1))

    @property
    def cell_axes(self):
        """list of np.ndarray: Axes of the cell centers (xyz order)."""
        # use cell centers as stagger locations
        return [((ax[:-1] + ax[1:]) / 2) if len(ax) > 1 else ax for ax in self.axes]

    @property
    def points(self):
        """np.ndarray: Grid points in given order starting top left corner."""
        return gen_points(
            axes=self.axes,
            order=point_order(self.order, self.axes_reversed),
            axes_increase=self.axes_increase,
        )

    @property
    def cells(self):
        """np.ndarray: Cell nodes in ESMF format."""
        return gen_cells(
            dims=self.dims,
            order=point_order(self.order, self.axes_reversed),
        )

    @property
    def cell_centers(self):
        """np.ndarray: Grid cell centers in given order starting top left corner."""
        return gen_points(
            axes=self.cell_axes,
            order=point_order(self.order, self.axes_reversed),
            axes_increase=self.axes_increase,
        )

    @property
    def mesh_dim(self):
        """int: Maximal cell dimension."""
        return np.sum(np.array(self.dims) > 1)

    @property
    def cell_types(self):
        """np.ndarray: Cell types."""
        if self.mesh_dim == 0:
            return np.full(self.cell_count, CellType.VERTEX, dtype=int)
        if self.mesh_dim == 1:
            return np.full(self.cell_count, CellType.LINE, dtype=int)
        if self.mesh_dim == 2:
            return np.full(self.cell_count, CellType.QUAD, dtype=int)
        return np.full(self.cell_count, CellType.HEX, dtype=int)

    @property
    def data_axes(self):
        """list of np.ndarray: Axes as used for the data."""
        axes = self.cell_axes if self.data_location == Location.CELLS else self.axes
        return [
            (axes[i] if self.axes_increase[i] else axes[i][::-1])
            for i in (range(self.dim)[::-1] if self.axes_reversed else range(self.dim))
        ]

    @property
    def data_axes_names(self):
        """list of str: Axes names of the data."""
        return list(
            reversed(self.axes_names) if self.axes_reversed else self.axes_names
        )

    @property
    def data_shape(self):
        """tuple: Shape of the associated data."""
        dims = np.asarray(self.dims[::-1] if self.axes_reversed else self.dims)
        return tuple(
            np.maximum(dims - 1, 1) if self.data_location == Location.CELLS else dims
        )

    def __eq__(self, other):
        if not isinstance(other, Grid):
            return False

        if not isinstance(other, StructuredGrid):
            return False

        return (
            self.dim == other.dim
            and self.crs == other.crs
            and self.order == other.order
            and self.data_location == other.data_location
            and self.data_shape == other.data_shape
            and all(np.allclose(a, b) for a, b in zip(self.axes, other.axes))
        )

    def export_vtk(
        self,
        path,
        data=None,
        cell_data=None,
        point_data=None,
        field_data=None,
        mesh_type="structured",
    ):
        """
        Export grid and data to a VTK file.

        Parameters
        ----------
        path : pathlike
            File path. Suffix will be replaced according to mesh type (.vtr, .vtu)
        data : dict or None, optional
            Data in the corresponding shape given by name, by default None
        cell_data : dict or None, optional
            Additional cell data, by default None
        point_data : dict or None, optional
            Additional point data, by default None
        field_data : dict or None, optional
            Additional field data, by default None
        mesh_type : str, optional
            Mesh type ("structured"/"unstructured"), by default "structured"

        Raises
        ------
        ValueError
            If mesh type is not supported.
        """
        data = prepare_vtk_data(
            data=data,
            axes_reversed=self.axes_reversed,
            axes_increase=self.axes_increase,
            flat=mesh_type == "unstructured",
            order=point_order(self.order, self.axes_reversed),
        )
        if mesh_type not in ["structured", "rectilinear"]:
            super().export_vtk(path, data, cell_data, point_data, field_data, mesh_type)
        else:
            kw = prepare_vtk_kwargs(
                self.data_location, data, cell_data, point_data, field_data
            )
            path = str(Path(path).with_suffix(""))
            x = np.ascontiguousarray(self.axes[0])
            y = np.ascontiguousarray(self.axes[1] if self.dim > 1 else np.array([1.0]))
            z = np.ascontiguousarray(self.axes[2] if self.dim > 2 else np.array([1.0]))
            gridToVTK(path, x, y, z, **kw)
