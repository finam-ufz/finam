"""Grid tools for FINAM."""

from enum import Enum, IntEnum
from math import isclose, nan

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
        c[:, 7] = c_rng
        c[:, 7] += (c_dim[0] + c_dim[1] + 1) * (c_rng // (c_dim[0] * c_dim[1]))
        c[:, 7] += (c_rng % (c_dim[0] * c_dim[1])) // c_dim[0]
        c[:, 6] = c[:, 7] + 1
        c[:, 5] = c[:, 7] + 2 + c_dim[0]
        c[:, 4] = c[:, 5] - 1
        # lower layer
        c[:, 3] = c[:, 7] + (1 + c_dim[0]) * (1 + c_dim[1])
        c[:, 2] = c[:, 3] + 1
        c[:, 1] = c[:, 3] + 2 + c_dim[0]
        c[:, 0] = c[:, 1] - 1
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
    data = cells.ravel()
    # unused entries in "cells" marked with "-1"
    return data.compress(data != -1)


def get_cells_matrix(cell_types, cells, connectivity=False):
    """
    Create the cells matrix as used in the Grid class.

    Parameters
    ----------
    cell_types : np.ndarray
        Cell types.

    cells : np.ndarray
        Either cell definitions given as list of number of nodes with node IDs:
        ``[n0, p0_0, p0_1, ..., p0_n, n1, p1_0, p1_1, ..., p1_n, ...]``

        Or cell connectivity given as list of node IDs:
        ``[p0_0, p0_1, ..., p0_n, p1_0, p1_1, ..., p1_n, ...]``

    connectivity : bool, optional
        Indicate that cells are given by connectivity. Default: False

    Returns
    -------
    np.ndarray
        Cell nodes as 2D array.
    """
    unique_cell_types = np.unique(cell_types)
    max_nodes = np.max(NODE_COUNT[unique_cell_types])
    cells_matrix = np.full((len(cell_types), max_nodes), fill_value=-1, dtype=int)
    cell_sizes = NODE_COUNT[cell_types]

    if connectivity:
        cell_ends = np.cumsum(cell_sizes)
        cell_starts = np.concatenate(
            [np.array([0], dtype=cell_ends.dtype), cell_ends[:-1]]
        )
    else:
        # adding one to skip cell size entry in cell definitions array
        # [(n0), p0_0, p0_1, ..., p0_n, (n1), p1_0, p1_1, ..., p1_n, ...]
        cell_ends = np.cumsum(cell_sizes + 1)
        cell_starts = (
            np.concatenate([np.array([0], dtype=cell_ends.dtype), cell_ends[:-1]]) + 1
        )

    for cell_type in unique_cell_types:
        cell_size = NODE_COUNT[cell_type]
        mask = cell_types == cell_type
        current_cell_starts = cell_starts[mask]

        cells_inds = current_cell_starts[..., np.newaxis] + np.arange(cell_size)[
            np.newaxis
        ].astype(cell_starts.dtype)
        cells_matrix[:, :cell_size][mask] = cells[cells_inds]

    return cells_matrix


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


ESMF_TYPE_MAP = np.array([-1, -1, 3, 4, 10, 12], dtype=int)
"""np.ndarray: ESMF type per CellType (-1 for unsupported)."""


VTK_TYPE_MAP = np.array((vtk_t := [1, 3, 5, 9, 10, 12]), dtype=int)
"""np.ndarray: VTK type per CellType."""


INV_VTK_TYPE_MAP = np.array(
    [vtk_t.index(i) if i in vtk_t else -1 for i in range(82)],
    dtype=int,
)
"""np.ndarray: CellType per VTK type."""


# VTK v9.3
VTK_CELL_DIM = np.array(
    # Linear cells (0-16)
    [0, 0, 0, 1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3] + 4 * [-1]
    # Quadratic / Cubic, isoparametric cells (21-37)
    + [1, 2, 2, 3, 3, 3, 3, 2, 3, 2, 3, 3, 3, 2, 1, 2, 3] + 3 * [-1]
    # Special class and Polyhedron cell (41-42)
    + [1, 3] + 8 * [-1]
    # Higher order cells in parametric form (51-56)
    + [1, 2, 2, 2, 3, 3] + 3 * [-1]
    # Higher order cells (60-67)
    + [1, 2, 2, 2, 3, 3, 3, 3]
    # Arbitrary order Lagrange elements (68-74)
    + [1, 2, 2, 3, 3, 3, 3]
    # Arbitrary order Bezier elements (75-81)
    + [1, 2, 2, 3, 3, 3, 3],
    dtype=int,
)
"""np.ndarray: Cell dimension per VTK type."""
