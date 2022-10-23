=================
Data and metadata
=================

This chapter explains data and metadata in FINAM.

Data arrays
-----------

Internally, all data is passed as :class:`xarray.DataArray`.
In addition, data is wrapped in :mod:`pint` units,
and a time axis with a single entry is added.

Data can be pushed to outputs as any type that can be wrapped in :class:`xarray.DataArray`.
This includes :class:`numpy.ndarray`,
lists, and scalar values.
Wrapping, adding time axis and units are performed internally, based on the available metadata (see section metadata_).

Inputs receive data in the :mod:`xarray` form, with units and time axis.

Several tool functions are provided in :mod:`.data` to convert to and from :class:`xarray.DataArray`:

* :func:`to_xarray(data, name, info, time) <.data.to_xarray>`
  Wraps data, adds time axis and units based on ``info`` (see `The Info object`_).
  Performs a metadata check if ``data`` is already an :class:`xarray.DataArray`.
* :func:`strip_time(xdata) <.data.strip_time>`
  Squeezes away the time axis if there is a single entry only, and raises an error otherwise.
  Returns an :class:`xarray.DataArray` with units.
* :func:`get_data(xdata) <.data.get_data>`
  Unwraps the data to a :mod:`numpy` array with units (:class:`pint.Quantity`), and with time axis preserved.
* :func:`strip_data(xdata) <.data.strip_data>`
  Combines :func:`strip_time <.data.strip_time>` and :func:`get_data <.data.get_data>`.
  Returns a :mod:`numpy` array with units, without the time axis.
* :func:`get_magnitude(xdata) <.data.get_magnitude>`
  Extracts data without units. Returns a :mod:`numpy` array without units, but with time axis preserved.
* :func:`get_units(xdata) <.data.get_units>`
  Gets the :mod:`pint` units of the data
* :func:`get_dimensionality(xdata) <.data.get_dimensionality>`
  Gets the :mod:`pint` dimensionality of the data (like length, mass, ...)
* :func:`has_time(xdata) <.data.has_time>`
  Checks if the data has a time axis
* :func:`get_time(xdata) <.data.get_time>`
  Gets the time axis values of the data

Metadata
--------

In FINAM, all data is associated with metadata.

Inputs and outputs of components specify the metadata describing the data they send or receive.
Internally, this is used for consistency checks, and for automated data transformations.

FINAM metadata follows the `CF Conventions <https://cfconventions.org/>`_.

There are two types of mandatory metadata:

* `Grid specification`_
* `Units`_ (missing units are assumed as dimensionless)

Metadata is passed around as objects of type :class:`.Info`:

The :class:`.Info` object
^^^^^^^^^^^^^^^^^^^^^^^^^

Objects of type :class:`.Info` represent the metadata associated with an input or output.
It has the following properties:

* ``grid`` - for the [Grid specification](grid-specification)
* ``meta`` - a :class:`dict` for all other metadata

For convenience, entries in ``meta`` can be used like normal member variables:

.. code-block:: Python

    info = Info(grid=NoGrid(), units="m", foo="bar")

    print(info.units)
    print(info.foo)

When creating inputs or outputs in components, the :class:`.Info` object does not need to be constructed explicitly.
In component code, these two lines are equivalent:

.. code-block:: Python

    self.inputs.add(name="A", grid=NoGrid(), units="m")
    self.inputs.add(name="A", info=Info(grid=NoGrid(), units="m"))

Metadata from source or target
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Any `Info` attributes initialized with `None` will be filled from the metadata on the other end of the coupling link.
E.g. if the grid specification of an input is intended to be taken from the connected output, the input can be initialized like this:

.. code-block:: Python

    self.inputs.add(name="Input_A", grid=None, units="m")

This works in the same way for outputs to get metadata from connected inputs.

For more details on metadata exchange, see chapter :doc:`./connect_phase`.

Grid specification
^^^^^^^^^^^^^^^^^^

Most of the data exchanged through FINAM will be spatio-temporal be their nature.
FINAM supports different types of structured grids and unstructured grids/meshes,
as well as unstructured point data.

For data that is not on a spatial grid, a placeholder "no-grid" type is provided.

Inputs as well as outputs must specify the grid specification for the data they send and receive, respectively.
We provide regridding adapters to transform between different grids or meshes in an automated way.

Coordinate Reference Systems (CRS) conversions are also covered by the regridding adapters.

Available grid types are:

Non-spatial grids
"""""""""""""""""

:class:`NoGrid(dims) <.NoGrid>`

For data that is not on a spacial grid.
``dims`` specifies the number of dimensions, like 0 for scalars, 1 for 1D arrays, etc.

Spatial grids
"""""""""""""

All spatial grids can have up to 3 dimensions.

:class:`RectilinearGrid(axes=[axis_x, axis_y, axis_z]) <.RectilinearGrid>`

For rectilinear grids, with uneven spacing along some axes.

:class:`UniformGrid(dims=(sx, sy, sz), spacing=(dx, dy, dz), origin=(ox, oy, oz)) <.UniformGrid>`

For uniform rectangular grids, with even spacing along each axis.
A sub-class of :class:`.RectilinearGrid`.

:class:`EsriGrid(nrows, ncols, cellsize, xllcorner, yllcorner) <.EsriGrid>`

For square grids according the ESRI/ASCII grid standard.
A sub-class of :class:`.UniformGrid`.

:class:`UnstructuredGrid(points, cells, celltypes) <.UnstructuredGrid>`

For unstructured grids (or meshes), composed of triangles and/or quads in 2D, and tetrahedrons of hexahedrons in 3D.

:class:`UnstructuredPoints(points) <.UnstructuredPoints>`

For unstructured point-associated data that does not require cells.

Class diagram grids
"""""""""""""""""""

The following figure shows a diagram of grid classes inheritance hierarchy.

.. figure:: ../images/class-diagram-grids.svg
    :alt: FINAM interfaces class diagram
    :class: dark-light p-2
    :width: 400px

    Figure 1: FINAM grids class diagram

Common grid properties
""""""""""""""""""""""

**CRS**: All spatial grid types have a property ``crs`` for the Coordinate Reference Systems.
The property can take any values understood by :mod:`pyproj`.
In many cases, this will just be an EPSG code, like ``crs="EPSG:32632"``

**Order**: All structured grids have an ``order`` attribute for being in either Fortran (``"F"``) or C (``"C"``) order.

**Data location**: For all spatial grids except :class:`.UnstructuredPoints`, data can be associated to either cells or points,
given by the ``data_location`` attribute.

**Axis names**: Grid axes are names according to the ``axes_names`` attribute.

**Axis order**: Regular grids can have inverted axis order (i.e. zyx instead of xyz),
indicated by the ``axes_reversed`` attribute.

**Axis direction**: Axis direction can be inverted, like with descending values for the y axis.
This is indicated by the ``axes_increase`` attribute, which is a tuple of boolean values.

Units
^^^^^

All data in FINAM has units of measurement.
The units can, however, be "dimensionless" for no actual units.

Unit conversions along links between components is done automatically,
based on the metadata provided by the receiving inputs.
So if an input was initialized with ``units="km"``, and data is passed in meters,
the input will internally do the conversion to kilometers.

FINAM uses the :mod:`pint` library for units handling,
and follows the `CF Conventions <https://cfconventions.org/>`_.

For direct access to :mod:`pint` units, the central units registry is exposed by :data:`.UNITS`.

Metadata flow
-------------

For details on how metadata is provided, and how it is passed around during coupling,
see chapter :doc:`./connect_phase`.
