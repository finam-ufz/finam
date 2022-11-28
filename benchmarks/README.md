# FINAM benchmarks

Micro-benchmarks for important FINAM functions and functionality.

Note that plot panels have different units!
`ms` is milliseconds (1/1,000 second), `us` is microseconds (1/1,000,000 second).

## SDK

### Push & pull

Push & pull using numpy arrays (`np`) and xarray arrays (`xr`).  
(xarray benchmarks include a call to `fm.tools.assign_time`)

![tools](https://git.ufz.de/FINAM/finam/-/jobs/artifacts/main/raw/bench/bench-sdk-io.svg?job=benchmark)

## Data

### Tools

Functions in `data/tools`

![tools](https://git.ufz.de/FINAM/finam/-/jobs/artifacts/main/raw/bench/bench-data-tools.svg?job=benchmark)

Functions in `data/tools` with longer run time

![tools-slow](https://git.ufz.de/FINAM/finam/-/jobs/artifacts/main/raw/bench/bench-data-tools-slow.svg?job=benchmark)

### Grids

Grid creation

![create-grids](https://git.ufz.de/FINAM/finam/-/jobs/artifacts/main/raw/bench/bench-data-create-grids.svg?job=benchmark)

Grid functions

![grid-functions](https://git.ufz.de/FINAM/finam/-/jobs/artifacts/main/raw/bench/bench-data-grid-functions.svg?job=benchmark)

Grid functions with longer run time

![grid-functions-slow](https://git.ufz.de/FINAM/finam/-/jobs/artifacts/main/raw/bench/bench-data-grid-functions-slow.svg?job=benchmark)

## Adapters

### Regridding

Regridding adapters, dependent on grid size.

Regridding from a uniform grid to another uniform grid of the same size, with slightly offset origin.

For more performant regridding, see the
[ESMPy](https://earthsystemmodeling.org/esmpy/)-based regridding adapter in
[`finam-regrid`](https://git.ufz.de/FINAM/finam-regrid/)
([benchmarks](https://git.ufz.de/FINAM/finam-regrid/-/tree/main/benchmarks))

![adapters-regrid](https://git.ufz.de/FINAM/finam/-/jobs/artifacts/main/raw/bench/bench-adapters-regrid.svg?job=benchmark)
