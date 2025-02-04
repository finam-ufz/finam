"""Grid abstract base classes for FINAM."""

import copy as cp
from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np
from pyevtk.hl import gridToVTK, unstructuredGridToVTK

from .grid_tools import (
    CELL_DIM,
    NODE_COUNT,
    VTK_TYPE_MAP,
    CellType,
    Location,
    flatten_cells,
    gen_cells,
    gen_node_centers,
    gen_points,
    point_order,
    prepare_vtk_data,
    prepare_vtk_kwargs,
)


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

    @property
    @abstractmethod
    def data_shape(self):
        """tuple: Shape of the associated data."""

    def copy(self, deep=False):
        """
        Copy of this grid.

        Parameters
        ----------
        deep : bool, optional
            If false, only a shallow copy is returned to save memory, by default False

        Returns
        -------
        Grid
            The grid copy.
        """
        return cp.deepcopy(self) if deep else cp.copy(self)

    def to_canonical(self, data):
        """Convert grid specific data to canonical form."""
        return data

    def from_canonical(self, data):
        """Convert canonical data to grid specific form."""
        return data

    # pylint: disable-next=unused-argument
    def get_transform_to(self, other):
        """Transformation between compatible grids."""
        return None

    def __repr__(self):
        return f"{self.name} ({self.dim}D) {self.data_shape}"


class Grid(GridBase):
    """Abstract grid specification."""

    valid_locations = (Location.CELLS, Location.POINTS)
    """tuple: Valid locations for the grid."""

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
        """np.ndarray: Cell nodes as 2D array."""

    @property
    @abstractmethod
    def cell_types(self):
        """np.ndarray: Cell types."""

    @property
    def cells_connectivity(self):
        """np.ndarray: Cells connectivity in ESMF format (list of node IDs)."""
        return flatten_cells(self.cells)

    @property
    def cells_definition(self):
        """np.ndarray: Cell definition in VTK format (list of number of nodes with node IDs)."""
        return flatten_cells(
            np.squeeze(
                np.hstack(
                    (np.atleast_2d(self.cell_node_counts).T, np.atleast_2d(self.cells))
                )
            )
        )

    @property
    def cells_offset(self):
        """np.ndarray: The location of the start of each cell in cells_connectivity."""
        return np.concatenate(
            (np.array([0], dtype=int), np.cumsum(self.cell_node_counts))
        )

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

    @data_location.setter
    @abstractmethod
    def data_location(self, data_location):
        """Set location of the associated data (either CELLS or POINTS)."""

    @property
    def data_points(self):
        """Points of the associated data (either cell_centers or points)."""
        if self.data_location == Location.POINTS:
            return self.points
        return self.cell_centers

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
    @abstractmethod
    def axes_attributes(self):
        """list of dict: Axes attributes following the CF convention (xyz order)."""

    @property
    def data_axes_names(self):
        """list of str: Axes names of the data."""
        return ["id"]

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
        if not isinstance(other, Grid):
            return False

        if isinstance(self, StructuredGrid) != isinstance(other, StructuredGrid):
            return False

        if not (
            self.dim == other.dim
            and self.crs == other.crs
            and self.order == other.order
            and (not check_location or self.data_location == other.data_location)
        ):
            return False

        if check_location and self.data_shape != other.data_shape:
            return False

        return (
            np.allclose(self.points, other.points)
            and np.all(self.cells == other.cells)
            and np.all(self.cell_types == other.cell_types)
        )

    def __eq__(self, other):
        return self.compatible_with(other)

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
            con = self.cells_connectivity
            # pyevtk only needs the ends of the cell definition
            off = self.cells_offset[1:]
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
        """list of np.ndarray: Axes of the structured grid (xyz order, all increase)."""

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
        """list of np.ndarray: Axes of the cell centers (xyz order, all increase)."""
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
        """list of np.ndarray: Axes as used for the data matrix."""
        axes = self.cell_axes if self.data_location == Location.CELLS else self.axes
        # reverse axes if needed
        return [
            (axes[i] if self.axes_increase[i] else axes[i][::-1])
            for i in (range(self.dim)[::-1] if self.axes_reversed else range(self.dim))
        ]

    @property
    def data_axes_names(self):
        """list of str: Axes names of the data matrix."""
        return list(
            reversed(self.axes_names) if self.axes_reversed else self.axes_names
        )

    @property
    def data_shape(self):
        """tuple: Shape of the associated data matrix."""
        dims = np.asarray(self.dims[::-1] if self.axes_reversed else self.dims)
        return tuple(
            np.maximum(dims - 1, 1) if self.data_location == Location.CELLS else dims
        )

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
        if not isinstance(other, Grid):
            return False

        if not isinstance(other, StructuredGrid):
            return False

        if not (
            self.dim == other.dim
            and self.crs == other.crs
            and (not check_location or self.data_location == other.data_location)
        ):
            return False

        if check_location and self.data_shape != (
            other.data_shape[::-1]
            if self.axes_reversed != other.axes_reversed
            else other.data_shape
        ):
            return False

        return all(np.allclose(a, b) for a, b in zip(self.axes, other.axes))

    def __eq__(self, other):
        if not self.compatible_with(other):
            return False

        return (
            all(a == b for a, b in zip(self.axes_increase, other.axes_increase))
            and self.axes_reversed == other.axes_reversed
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
            y = np.ascontiguousarray(self.axes[1] if self.dim > 1 else np.array([0.0]))
            z = np.ascontiguousarray(self.axes[2] if self.dim > 2 else np.array([0.0]))
            gridToVTK(path, x, y, z, **kw)

    def to_canonical(self, data):
        """
        Convert grid specific data to canonical form.

        Canonical means, that data axis are in xyz order and
        following increasing axis values.

        Parameters
        ----------
        data : arraylike
            Data to convert.

        Returns
        -------
        arraylike
            Canonical Data.

        Raises
        ------
        ValueError
            When data has wrong shape.
        """
        rev = -1 if self.axes_reversed else 1
        d_shp, in_shp, shp_len = self.data_shape, np.shape(data), len(self.data_shape)
        if not np.array_equal(d_shp[::rev], in_shp[::rev][:shp_len]):
            msg = "to_canonical: data has wrong shape."
            raise ValueError(msg)
        if self.axes_reversed and np.ndim(data) > 1:
            data = np.transpose(data)
        for i, inc in enumerate(self.axes_increase):
            if not inc:
                data = np.flip(data, axis=i)
        return data

    def from_canonical(self, data):
        """
        Convert canonical data to grid specific form.

        Canonical means, that data axis are in xyz order and
        following increasing axis values.

        Parameters
        ----------
        data : arraylike
            Data to convert.

        Returns
        -------
        arraylike
            Grid specific Data.

        Raises
        ------
        ValueError
            When data has wrong shape.
        """
        rev = -1 if self.axes_reversed else 1
        d_shp, in_shp, shp_len = self.data_shape, np.shape(data), len(self.data_shape)
        if not np.array_equal(d_shp[::rev], in_shp[:shp_len]):
            msg = "from_canonical: data has wrong shape."
            raise ValueError(msg)
        for i, inc in enumerate(self.axes_increase):
            if not inc:
                data = np.flip(data, axis=i)
        if self.axes_reversed and np.ndim(data) > 1:
            data = np.transpose(data)
        return data

    def get_transform_to(self, other):
        """
        Get transformation for compatible grids.

        Parameters
        ----------
        other : instance of Grid
            Other grid to compatibility with.

        Returns
        -------
        callable
            data transformation
        """
        if not self.compatible_with(other):
            raise ValueError("get_transform_to: grids are not compatible.")

        def trans(data):
            """Transformation."""
            # could be optimized
            return other.from_canonical(self.to_canonical(data))

        # only use trans if grids are compatible but NOT equal
        return None if self == other else trans
