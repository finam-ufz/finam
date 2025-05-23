# Release notes

## [v1.0.1]

### Bug fixes

* make `GridToValue` and `ValueToGrid` compatible with masked data (!291)

## [v1.0.0]

### Breaking changes

* submodule `modules` renamed to `components` for consistency (!289)
* argument `modules` renamed to `components` in `Composition` for consistency (!289)
* Components now implement `_next_time` instead of the property `next_time` for consistency (!283)
* All fields of `Composition` are now private (!273)
* `Input.source` is private, `Input.get_source()` becomes property `Input.source`, `Input.set_source` becomes a getter (!273)
* `Output.targets` is private, `Output.get_targets()` becomes property `Output.targets` (!273)
* Composition metadata was restructured to hold components and adapters in separate sub-dictionaries (!274)
* Time components implement method `_next_time` instead of property `next_time` (!283)
* `Info` now has properties for `grid`, `time` and `mask` (!286)
* all init-args of `Info` are now optional (!286)
* `Info.accepts` has changed signature: renamed `ignore_none` to `incoming_donwstream` (!286)
* `Info.accepts` now only checks: `grid`, `mask` and `units` (other meta data can differ) (!286)
* `Grid.to_/from_canonical` now allows additional dimensions (!286)
* `data_shape` now a property of `GridBase` (!286)
  * `NoGrid` can be initialized with `dim` or `data_shape` now
  * `NoGrid.data_shape` can have `-1` entries for variable size dimensions
  * if only `dim` given to `NoGrid`, all entries in `data_shape` will be `-1`

### Features

* Components and adapters automatically provide default metadata that can be extended by implementations (!274, !276)
* Grid class now have attributes providing connectivity information for the contained cells (!275)
  * `cells_connectivity`: connectivity array as used by ESMF and VTK
  * `cells_definition`: cell definition as used by PyVista and legacy VTK
  * `cells_offset`: location of the start of each cell in `cells_connectivity`
* added convenience functions and constants to `grid_tools`  (!275)
  * `get_cells_matrix`: convert `cells_connectivity` or `cells_definition` back to the default cells matrix used in the Grid class (can be used to convert VTK-grids into FINAM-grids)
  * `INV_VTK_TYPE_MAP`: inverse mapping to `VTK_TYPE_MAP` - FINAM cell type to VTK cell type
  * `VTK_CELL_DIM`: parametric dimension for each VTK cell type
* Grid class now reusable when having different data locations and better grid type casting (!278)
  * added `copy` method to grids with optional argument `deep` (`False` by default) to create a copy of a grid
  * added setter for `data_location` in order to set a new data location (e.g. after copying a grid)
  * added class attribute `valid_locations` in order to check the set data location (esri-grid only supports cells, unstructured-points only support points)
  * added missing casting methods to convert esri to uniform and uniform to rectilinear (when you want to use point data on an esri-grid, you can cast it to uniform first)
  * added `axes_attributes` also to unstructured grids
* Grid method `compatible_with` now has a `check_location` argument to optionally check data location (!280)
* added `Mask` enum with two options: (!286)
  * `Mask.FLEX` for flexible masking
  * `Mask.NONE` to explicitly use plain numpy arrays
* added `mask` attribute and init-arg to `Info` : can be a `Mask` value or a valid mask for `numpy.ma.MaskedArray` (!286)
* `data.tools.prepare` now applies masks to data if set in `Info` object (!286)
* `ARegridding` now has a `out_mask` arg (!286)
* `RegridNearest` and `RegridLinear` now support explicitly masked data (input doesn't have `Mask.FLEX`) (!286)
* adapters now have an `in_info` property (!286)

### Bug fixes

* cells for structured grids in 3D are now created correctly (no negative Volume in VTK/ESMF) (!286)
* cf_units.py was broken for pint>=0.24 (!282)

### Documentation

* Minor fixes in documentation examples and links (!272)
* Adds a book section on composition, component and adapter metadata (!274)

## [v0.5.1]

### Bug fixes

* Fix unquantified masked arrays loosing mask in `fm.data.prepare()` (#115, !270)

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


[unpublished]: https://git.ufz.de/FINAM/finam/-/compare/v1.0.1...main
[v1.0.1]: https://git.ufz.de/FINAM/finam/-/compare/v1.0.0...v1.0.1
[v1.0.0]: https://git.ufz.de/FINAM/finam/-/compare/v0.5.1...v1.0.0
[v0.5.1]: https://git.ufz.de/FINAM/finam/-/compare/v0.5.0...v0.5.1
[v0.5.0]: https://git.ufz.de/FINAM/finam/-/compare/v0.4.0...v0.5.0
[v0.4.0]: https://git.ufz.de/FINAM/finam/-/compare/v0.4.0-rc.2...v0.4.0
[v0.4.0-rc.2]: https://git.ufz.de/FINAM/finam/-/compare/v0.4.0-rc.1...v0.4.0-rc.2
[v0.4.0-rc.1]: https://git.ufz.de/FINAM/finam/-/compare/v0.3.0...v0.4.0-rc.1
[v0.3.0]: https://git.ufz.de/FINAM/finam/-/compare/v0.2.0...v0.3.0
[v0.2.0]: https://git.ufz.de/FINAM/finam/-/compare/v0.1.0...v0.2.0
[v0.1.0]: https://git.ufz.de/FINAM/finam/-/commits/v0.1.0
