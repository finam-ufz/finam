# Changelog

## [unpublished]

### Changes

* Vertical/Y grid indices are now flipped, to conform with (typical) NetCDF and ASCII grid format

### Bug fixes

* Fix check for `None` data in `Grid` constructor

## [v0.2.0]

### Changes

* Uses Python's `datetime` and `timedelta` for all time-related parameters
* Removed temporal sum integration adapter
