# Release notes

## [v0.5.0]

### Features

* Components and adapters can provide a dictionary of meta data (!259)
* Class `Composition` hat a property `metadata` that collects and returns the meta data from all components and adapters (!259)
* Automatic conversion between compatible grids (!255)
* Adds methods `to_canonical`, `from_canonical` and `get_transform_to` to grid classes (!255)
* Adds support for masked grids using `numpy.ma.MaskedArray` (!258, !260)
* Adds convenience functions for dealing with masked arrays in `data.tools` (!260):  
  `is_masked_array`, `has_masked_values`, `filled`, `to_compressed`, `from_compressed`, `check_data_covers_domain`

### Documentation

* Adds a book chapter on wrapping existing models for FINAM (!256)
* Adds a book section on masked data (!262)

### Bug fixes

* No more logging of expected `FinamNoDataError` in inputs during the connect phase (!257)

### Other

* FINAM is now available on Conda via conda-forge

## [v0.4.0]

### New scheduling algorithm

* FINAM uses a new scheduling algorithm that allows components to use future data instead of only past/current (!157, !159)
* New adapters to resolve circular coupling through the use of delayed data (!187)
* It is now possible to set up static couplings that run only once and have no explicit time or stepping (!166)
* FINAM can handle different starting times of components by pushing initial data twice (!206):  
  Once for the common starting time, and once for the actual component time
* Components are no longer required to push all outputs on every step (!208)

### Data and metadata rework

* Outputs check compatibility between metadata of inputs if there is more than one target input (!104)
* Add data tools function `compatible_units` to check for convertibility (!105)
* Components can exchange their starting time through the `Info` object (!111)
* Info exchange is automated by the `ConnectHelper` by specifying transfer rules at initialization (!154)
* `Info` now requires time in constructor (can be `None`) (!111)
* Scheduler checks for dead links that don't work in terms of push/pull combination (!112)
* `IInput`, `IOutput` and `IAdapter` have new internally used properties `needs_push` and `needs_pull` (!112)
* `to_xarray` now checks the data shape if the data is not flat (!130)
* Outputs can be flagged `static` for data that is only used during initialization, or that is constant (!166)
* Inputs can be flagged `static` for constant data (!171)
* Outputs accept and convert compatible units, not only exactly equal units (!215)
* Outputs check that subsequent data pushes don't share memory (!217)
* Exchanged `xarray` data has no time coordinate anymore, only a dimension without values (for performance and usability) (!223)
* Remove the `xarray` wrapping completely. Use numpy arrays in pint `Quantity` (!235)
* Outputs and adapters can have a `memory_limit` and write data to disk if the limit is exceeded (!238)

### Components

* Add `modules.WeightedSum` for aggregation of multiple inputs (!105)
* Add `modules.SimplexNoise` for generating spatio-temporal noise (!131)
* Add `modules.TimeTrigger` to forward data from pull-based to push-based components (!131)
* Add `modules.ScheduleLogger` to visualize scheduling/module updates through ASCII charts (!160)
* Add `modules.DebugPushConsumer` as a push-based variant of the debug consumer (!165)
* Add `modules.UserControl` that lets users control FINAM runs from the terminal (!184)
* `modules.DebugConsumer` and `modules.DebugPushConsumer` can use optional callbacks for better debugging (!176)
* Components can be renamed using the method `with_name()` (!243)

### Adapters

* Add `adapters.Histogram` to extract a histogram from grid values (!182)
* Add `adapters.DelayFixed`, `adapters.DelayToPull` and `adapters.DelayToPush` to resolve circular coupling through the use of delayed data (!187)
* Add `adapters.StepTime` for step-wise interpolation (!194)
* Restructuring of time integration adapters (!194)
  * `adapters.IntegrateTime` renamed to `adapters.AvgOverTime`
  * Add `adapters.SumOverTime` for sum/Area under Curve integration
* Adapters have a method `finalize()` for cleanup (!226).
* Adapters can be renamed using the method `with_name()` (!243)

### Other

* Remove module `core`, subpackages now under `finam` (!106)
* Rename `IOutput.source_changed()` to `source_updated` (!107)
* Rename `LogError` to `ErrorLogger` (!107)
* Rename abstract SDK classes: (!107)
  * `AAdapter` is now `Adapter`
  * `AComponent` is now `Component`
  * `ATimeComponent` is now `TimeComponent`
* Changed arguments for `create_connector()` (!111)
  * Removed `required_out_infos`
  * Renamed `required_in_data` to `pull_data`
  * Added arguments to specify info exchange rules
* All error types are in module `errors` now, and re-exported at top level (!116)
* Overwriting `_validate()` and `_finalize()` in components is now mandatory (!156)
* Input and output slots can be accessed from components directly, e.g. `comp["A"]` instead of `comp.inputs["A"]` (!147)
* Inputs and outputs can be marked as `static` for constant data without time information (!166, !171)
* New helper function `tools.inspect()` to inspect components, adapters and I/O slots (!197)
* Publish on PyPI, starting with the next release (!198, !200, !201)
* Added benchmarks for the most important FINAM functions
  (see the [benchmarks README](https://git.ufz.de/FINAM/finam/-/blob/main/benchmarks/README.md))
* Added profiling for full runs to the CI (!221)
* Optimization of data tool functions, with approx. 20-fold speedup of basic push+pull
  (!222, !223, !224, !228, !229, !237).
* Add two more log levels: `TRACE` (most verbose) and `PROFILE` (between `DEBUG` and `INFO`) (!240)

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

[unpublished]: https://git.ufz.de/FINAM/finam/-/compare/v0.5.0...main
[v0.5.0]: https://git.ufz.de/FINAM/finam/-/compare/v0.4.0...v0.5.0
[v0.4.0]: https://git.ufz.de/FINAM/finam/-/compare/v0.4.0-rc.2...v0.4.0
[v0.4.0-rc.2]: https://git.ufz.de/FINAM/finam/-/compare/v0.4.0-rc.1...v0.4.0-rc.2
[v0.4.0-rc.1]: https://git.ufz.de/FINAM/finam/-/compare/v0.3.0...v0.4.0-rc.1
[v0.3.0]: https://git.ufz.de/FINAM/finam/-/compare/v0.2.0...v0.3.0
[v0.2.0]: https://git.ufz.de/FINAM/finam/-/compare/v0.1.0...v0.2.0
[v0.1.0]: https://git.ufz.de/FINAM/finam/-/commits/v0.1.0
