"""Grid tools for FINAM."""
from abc import ABC, abstractmethod
from enum import Enum

import numpy as np


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


def gen_axes(dims, spacing, origin):
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

    Returns
    -------
    list of np.ndarray
        Axes of the uniform grid.
    """
    axes = []
    for i, d in enumerate(dims):
        axes.append(np.arange(d) * spacing[i] + origin[i])
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
        # TODO: should upper and lower layer be swapped?
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
    Check axes to be strictly monotonic.

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


class Location(Enum):
    """Data location in the grid."""

    CELLS = 0
    POINTS = 1


class CellType(Enum):
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


class Grid(ABC):
    """Abstract grid specification."""

    @property
    @abstractmethod
    def dim(self):
        """int: Dimension of the grid."""

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
        if self.data_location == Location.CELLS:
            return self.cell_centers
        raise ValueError(f"Grid: unknown data location: '{self.data_location}'")

    @property
    def data_shape(self):
        """tuple: Shape of the associated data."""
        return (len(self.data_points),)

    @property
    def name(self):
        """Grid name."""
        return self.__class__.__name__


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
        # should be used for xarray later on

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
            return np.full(self.cell_count, CellType.VERTEX.value)
        if self.mesh_dim == 1:
            return np.full(self.cell_count, CellType.LINE.value)
        if self.mesh_dim == 2:
            return np.full(self.cell_count, CellType.QUAD.value)
        return np.full(self.cell_count, CellType.HEX.value)

    @property
    def data_axes(self):
        """list of np.ndarray: Axes as used for the data."""
        axes = self.cell_axes if self.data_location == Location.CELLS else self.axes
        return [
            (axes[i] if self.axes_increase[i] else axes[i][::-1])
            for i in (range(self.dim)[::-1] if self.axes_reversed else range(self.dim))
        ]

    @property
    def data_shape(self):
        """tuple: Shape of the associated data."""
        dims = np.asarray(self.dims[::-1] if self.axes_reversed else self.dims)
        return tuple(
            np.maximum(dims - 1, 1) if self.data_location == Location.CELLS else dims
        )
