# Changelog

## [unpublished]

### Data and metadata rework

* Add conversion between CRS to regridding adapters, using `pyproj`

## [v0.4.0-rc.1]

### Data and metadata rework

* Grid specifications for structured and unstructured grids:  
  `RectilinearGrid`, `UniformGrid`, `EsriGrid`, `UnstructuredGrid` and `UnstructuredPoints`
* Use of `xarray.DataArray` for all exchanged data
* All exchanged data must have `pint` units (can be "dimensionless")
* Metadata about grid specification, units and other metadata is exchanged before the first data exchange
* Metadata exchange is iterative and bi-directional  
  Components can depend on metadata from source or target components
* Inputs check compatibility of incoming metadata with own requirements
* Inputs and outputs check compatibility of incoming data with metadata
* Automatic conversion of array-like and scalars to `xarray.DataArray` in outputs, with metadata check

### Adapters

* New adapters for linear and nearest-neighbour regridding from and to all available grid types
* Removed adapter `GridCellCallback`

### Components

* Removed `GridView` component (new implementation in [finam-plot](https://git.ufz.de/FINAM/finam-plot))

### Usability

* The finam package has a flatter module hierarchy now, so the most important classes are now exported at the top level
* Component developers do not overwrite interface methods like `update()` anymore, but internal methods like `_update()` instead

### Other

* More ergonomic input and output creation in components
* Input and output mappings are immutable after initialization
* Brought up test coverage to 98%

## [v0.3.0]

### Interface

* `IOutput` now has a property `has_target` to determine whether it is connected (!54)
* `IInput` now has a property `has_source` to determine whether it is connected (!63)
* `CallbackComponent` for generic, callback-based data generation, transform or consumption (!55)
* `IComponent.inputs`, `IComponent.outputs`, `IComponent.status` and `ITimeComponent.time` are now properties instead of methods (!53)
* Support for initialization from inputs / iterative connect (!69)
  * Changed logic and `ComponentStatus` to be set in component method `connect()`

### Other

* Logging capability, incl. C-level output capturing (!64, !70, !71)
* `Grid` now uses `MaskedArray`, to improve handling of missing data
* Vertical/Y grid indices are now flipped, to conform with (typical) NetCDF and ASCII grid format (!51)
* Minimal Python version is now 3.7, to ensure consistent `dict` order (!58)
* Most `assert`s replaced by raising errors (!52)
* Grid visualization supports color scale limits (!61)
* Context manager and helper function to execute code in a certain working directory (!62)
* Status checks moved from component methods to composition/scheduler (!65)
* Adapters check that requested time it in the range of available data (!66)

### Bug fixes

* Fix check for `None` data in `Grid` constructor (!50)

## [v0.2.0]

### Changes

* Uses Python's `datetime` and `timedelta` for all time-related parameters
* Removed temporal sum integration adapter
