=================
Data and metadata
=================

This chapter explains data and metadata in FINAM.

## Data arrays

Internally, all data is passed as [`xarray.DataArray`](https://docs.xarray.dev/en/stable/generated/xarray.DataArray.html).
In addition, data is wrapped in [`pint`](https://pint.readthedocs.io) units,
and a time axis with a single entry is added.

Data can be pushed to outputs as any type that can be wrapped in `xarray.DataArray`.
This includes [`numpy`](https://numpy.org/) [`ndarray`](https://numpy.org/doc/stable/reference/generated/numpy.ndarray.html),
lists, and scalar values.
Wrapping, adding time axis and units are performed internally, based on the available metadata (see section [Metadata](metadata)).

Inputs receive data in the `xarray` form, with units and time axis.

Several tool functions are provided in `finam.data` to convert to and from `xarray`:

* `to_xarray(data, name, info, time)`
  Wraps data, adds time axis and units based on `info` (see [The `Info` object](the-info-object)).
  Performs a metadata check if `data` is already an `xarray`.
* `strip_time(xdata)`
  Squeezes away the time axis if there is a single entry only, and raises an error otherwise.
  Returns an `xarray` with units.
* `get_data(xdata)`
  Unwraps the data to a `numpy` array with units (`pint.Quantity`), and with time axis preserved.
* `strip_data(xdata)`
  Combines `strip_time(xdata)` and `get_data(xdata)`.
  Returns a `numpy` array with units, without the time axis.
* `get_magnitude(xdata)`
  Extracts data without units. Returns a `numpy` array without units, but with time axis preserved.
* `get_units(xdata)`
  Gets the `pint` units of the data
* `get_dimensionality(xdata)`
  Gets the `pint` dimensionality of the data (like length, mass, ...)
* `has_time(xdata)`
  Checks if the data has a time axis
* `get_time(xdata)`
  Gets the time axis values of the data

(metadata)=
## Metadata

In FINAM, all data is associated with metadata.

Inputs and outputs of components specify the metadata describing the data they send or receive.
Internally, this is used for consistency checks, and for automated data transformations.

FINAM metadata follows the [CF Conventions](https://cfconventions.org/).

There are two types of mandatory metadata:
* [Grid specification](grid-specification)
* [Units](units) (missing units are assumed as dimensionless)

Metadata is passed around as objects of type `Info`:

(the-info-object)=
### The `Info` object

Objects of type `Info` represent the metadata associated with an input or output.
It has the following properties:

* `grid` - for the [Grid specification](grid-specification)
* `meta` - a `dict` for all other metadata

For convenience, entries in `meta` can be used like normal member variables:

```python
info = Info(grid=NoGrid(), units="m", foo="bar")

print(info.units)
print(info.foo)
```

When creating inputs or outputs in components, the `Info` object does not need to be constructed explicitly.
In component code, these two lines are equivalent:

```python
self.inputs.add(name="A", grid=NoGrid(), units="m")
self.inputs.add(name="A", info=Info(grid=NoGrid(), units="m"))
```

#### Metadata from source or target

Any `Info` attributes initialized with `None` will be filled from the metadata on the other end of the coupling link.
E.g. if the grid specification of an input is intended to be taken from the connected output, the input can be initialized like this:

```
self.inputs.add(name="Input_A", grid=None, units="m")
```

This works in the same way for outputs to get metadata from connected inputs.

For more details on metadata exchange, see chapter [The Connect Phase &trade;](./connect_phase).

(grid-specification)=
### Grid specification

Most of the data exchanged through FINAM will be spatio-temporal be their nature.
FINAM supports different types of structured grids and unstructured grids/meshes,
as well as unstructured point data.

For data that is not on a spatial grid, a placeholder "no-grid" type is provided.

Inputs as well as outputs must specify the grid specification for the data they send and receive, respectively.
We provide regridding adapters to transform between different grids or meshes in an automated way.

Coordinate Reference Systems (CRS) conversions are also covered by the regridding adapters.

Available grid types are:

#### Non-spatial grids

```python
NoGrid(dims)
```

For data that is not on a spacial grid.
`dims` specifies the number of dimensions, like 0 for scalars, 1 for 1D arrays, etc.

#### Spatial grids

All spatial grids can have up to 3 dimensions.

```python
RectilinearGrid(axes=[axis_x, axis_y, axis_z])
```

For rectilinear grids, with uneven spacing along some axes.

```python
UniformGrid(dims=(sx, sy, sz), spacing=(dx, dy, dz), origin=(ox, oy, oz))
```

For uniform rectangular grids, with even spacing along each axis.
A sub-class of `RectilinearGrid`.

```python
EsriGrid(nrows, ncols, cellsize, xllcorner, yllcorner)
```

For square grids according the ESRI/ASCII grid standard.
A sub-class of `UniformGrid`.

```python
UnstructuredGrid(points, cells, celltypes)
```

For unstructured grids (or meshes), composed of triangles and/or quads in 2D, and tetrahedrons of hexahedrons in 3D.

```python
UnstructuredPoints(points)
```

For unstructured point-associated data that does not require cells.

#### Class diagram grids

The following figure shows a diagram of grid classes inheritance hierarchy.

<img width="400" src="../images/class-diagram-grids.svg" />

#### Common grid properties

**CRS**: All spatial grid types have a property `crs` for the Coordinate Reference Systems.
The property can take any values understood by [`pyproj4`](https://pyproj4.github.io/pyproj/stable/).
In many cases, this will just be an EPSG code, like `crs="EPSG:32632"`

**Order**: All structured grids have an `order` attribute for being in either Fortran (`"F"`) or C (`"C"`) order.

**Data location**: For all spatial grids except `UnstructuredPoints`, data can be associated to either cells or points,
given by the `data_location` attribute.

**Axis names**: Grid axes are names according to the `axes_names` attribute.

**Axis order**: Regular grids can have inverted axis order (i.e. zyx instead of xyz),
indicated by the `axes_reversed` attribute.

**Axis direction**: Axis direction can be inverted, like with descending velues for the y axis.
This is indicated by the `axes_increase` attribute, which is a tuple of boolean values.

(units)=
### Units

All data in FINAM has units of measurement.
The units can, however, be "dimensionless" for no actual units.

Unit conversions along links between components is done automatically,
based on the metadata provided by the receiving inputs.
So if an input was initialized with `units="km"`, and data is passed in meters,
the input will internally do the conversion to kilometers.

FINAM uses the [`pint`](https://pint.readthedocs.io) library for units handling,
and follows the [CF Conventions](https://cfconventions.org/).

For direct access to `pint` units, the central units registry is exposed by `finam.UNITS`.

## Metadata flow

For details on how metadata is provided, and how it is passed around during coupling,
see chapter [The Connect Phase &trade;](./connect_phase).
