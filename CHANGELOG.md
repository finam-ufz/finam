# Changelog

## [unpublished]

None

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
