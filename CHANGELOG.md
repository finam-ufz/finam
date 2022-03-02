# Changelog

## [unpublished]

### Added

* `IOutput` now has a property `has_target` to determine whether it is connected (!54)
* `CallbackComponent` for generic, callback-based data generation, transform or consumption (!55)
* Minimal Python version is now 3.7, to ensure consistent `dict` order (!58)

### Changed

* Vertical/Y grid indices are now flipped, to conform with (typical) NetCDF and ASCII grid format (!51)
* Most `assert`s replaced by raising errors (!52)
* `IComponent.inputs`, `IComponent.outputs`, `IComponent.status` and `ITimeComponent.time` are now properties instead of methods (!53)

### Bug fixes

* Fix check for `None` data in `Grid` constructor (!50)

## [v0.2.0]

### Changes

* Uses Python's `datetime` and `timedelta` for all time-related parameters
* Removed temporal sum integration adapter
