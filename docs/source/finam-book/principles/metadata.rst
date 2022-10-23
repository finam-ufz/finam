# Metadata and time

In FINAM, data has certain information associated.
This is necessary to ensure valid coupling and is one of the foundations for the ease of use of FINAM.

This chapter gives a brief overview of the most important aspects in this regard.
For more details and usage by developers, see chapter [Data and metadata](../development/data_metadata).

## Time

In FINAM, each data exchange is associated with time information.

All times are represented by [`datetime`](https://docs.python.org/3/library/datetime.html) objects,
namely `datetime` for time points and `timedelta` for time spans.

## Metadata

In FINAM, all data is associated with metadata.

Inputs and outputs of components specify the metadata describing the data they send or receive.
Internally, this is used for consistency checks, and for automated data transformations.

FINAM metadata follows the [CF Conventions](https://cfconventions.org/).

There are two types of mandatory metadata:

### Grid specification

Most of the data exchanged through FINAM will be spatio-temporal be their nature.
FINAM supports different types of structured grids and unstructured grids/meshes,
as well as unstructured point data.

For data that is not on a spatial grid, a placeholder "no-grid" type is provided.

Inputs as well as outputs must specify the grid specification for the data they send and receive, respectively.
We provide regridding adapters to transform between different grids or meshes in an automated way.

Coordinate Reference Systems (CRS) conversions are also covered by the regridding adapters.

### Units of measurement

All data in FINAM has units of measurement.
The units can, however, be "dimensionless" for no actual units.

Unit conversions along links between components is done automatically,
based on the metadata provided by the receiving inputs.

FINAM uses the [`pint`](https://pint.readthedocs.io) library for units handling,
and follows the [CF Conventions](https://cfconventions.org/).

### More metadata

More than the above metadata items can be present on FINAM data.
For more details and usage by developers, see chapter [Data and metadata](../development/data_metadata).

Metadata is passed between components during the initialization,
which allows for initializing components from external metadata.
For details, see chapter [The Connect Phase &trade;](../development/connect_phase).
