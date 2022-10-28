# Changelog

## [unpublished]

### Data and metadata rework

* Outputs check compatibility between metadata of inputs if there is more than one target input (!104)
* Add data tools function `check_units(lhs, rhs)` to check for convertibility (!105)
* Components can exchange their starting time through the `Info` object (!111)
* `Info` now requires time in constructor (can be `None`) (!111)
* Scheduler checks for dead links that don't work in terms of push/pull combination (!112)
* `IInput`, `IOutput` and `IAdapter` have new internally used properties `needs_push` and `needs_pull` (!112)
* `to_xarray` now checks the data shape if the data is not flat (!130)

### Components

* Add `modules.WeightedSum` for aggregation of multiple inputs (!105)
* Add `modules.SimplexNoise` for generating spatio-temporal noise (!131)
* Add `modules.TimeTrigger` to forward data from pull-based to push-based components (!131)

### Other

* Remove module `core`, subpackages now under `finam` (!106)
* Rename `IOutput.source_changed()` to `source_updated` (!107)
* Rename `LogError` to `ErrorLogger` (!107)
* Rename abstract SDK classes: (!107)
  * `AAdapter` is now `Adapter`
  * `AComponent` is now `Component`
  * `ATimeComponent` is now `TimeComponent`
* Changed arguments for `create_connector()`
  * Removed `required_out_infos`
  * Renamed `required_in_data` to `pull_data`
* All error types are in module `errors` now, and re-exported at top level

## [v0.4.0-rc.2]

### Data and metadata rework

* Add conversion between CRS to regridding adapters, using `pyproj` (!95)
* Add more data tool functions: `quantify(xdata)`, `check_axes_uniformity(axes)` and `strip_data(xdata)` (!96, !100)
* In outputs, the name of the data is overwritten instead of failing the check (!98)
* Adapters can pass through data with time, even if it does not match the pull time (which is quite common) (!98)

### Interface

* Add `CallbackOutput` for implementing pull-based components (!102)
* Connect phase of scheduler can be called separately from run (!99)
* No need to set component status in constructor anymore (!100)

### Other

* Components are allowed to be in state VALIDATED at the end of a run (i.e. not updated) (!97)
* Component connector checks that inputs and outputs referenced in arguments actually exist (!101)

## [v0.4.0-rc.1]

### Data and metadata rework

* Grid specifications for structured and unstructured grids (!74):
  `RectilinearGrid`, `UniformGrid`, `EsriGrid`, `UnstructuredGrid` and `UnstructuredPoints`
* Use of `xarray.DataArray` for all exchanged data (!74)
* All exchanged data must have `pint` units (can be "dimensionless") (!74)
* Metadata about grid specification, units and other metadata is exchanged before the first data exchange (!77)
* Metadata exchange is iterative and bi-directional (!77)
  Components can depend on metadata from source or target components
* Inputs check compatibility of incoming metadata with own requirements (!77)
* Inputs and outputs check compatibility of incoming data with metadata (!77)
* Automatic conversion of array-like and scalars to `xarray.DataArray` in outputs, with metadata check (!74, !77)

### Adapters

* New adapters for linear and nearest-neighbour regridding from and to all available grid types (!77, !87)
* Removed adapter `GridCellCallback` (!79)

### Components

* Removed `GridView` component (new implementation in [finam-plot](https://git.ufz.de/FINAM/finam-plot)) (!79)

### Usability

* The finam package has a flatter module hierarchy now, so the most important classes are now exported at the top level (!92)
* Component developers do not overwrite interface methods like `update()` anymore, but internal methods like `_update()` instead (!85)

### Other

* More ergonomic input and output creation in components (!80, !82)
* Input and output mappings are immutable after initialization (!82)
* Brought up test coverage to 98% (!93)

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

## [v0.1.0]

* initial release of FINAM

[unpublished]: https://git.ufz.de/FINAM/finam/-/compare/v0.4.0-rc.2...main
[v0.4.0-rc.2]: https://git.ufz.de/FINAM/finam/-/compare/v0.4.0-rc.1...v0.4.0-rc.2
[v0.4.0-rc.1]: https://git.ufz.de/FINAM/finam/-/compare/v0.3.0...v0.4.0-rc.1
[v0.3.0]: https://git.ufz.de/FINAM/finam/-/compare/v0.2.0...v0.3.0
[v0.2.0]: https://git.ufz.de/FINAM/finam/-/compare/v0.1.0...v0.2.0
[v0.1.0]: https://git.ufz.de/FINAM/finam/-/commits/v0.1.0