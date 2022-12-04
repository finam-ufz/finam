# FINAM benchmarks

Micro-benchmarks and profiling for important FINAM runs functions.

Note that plot panels have different units!
`ms` is milliseconds (1/1,000 second), `us` is microseconds (1/1,000,000 second).

Open images in a separate browser tab for tooltips showing exact values.

## Full runs

**Profiling data** for full runs can be found in the latest [job artifacts](https://git.ufz.de/FINAM/finam/-/jobs/artifacts/main/browse/prof?job=profile).

### Simple link, 365 steps

Simple run over one year with two coupled components with daily time step.

Groups left to right:
* Using numpy arrays, no data copy, no units conversion
* Using numpy arrays, with data copy, no units conversion
* Using xarray arrays, no data copy, no units conversion
* Using xarray arrays, with data copy, no units conversion
* Using xarray arrays, no data copy, with units conversion

![tools](https://git.ufz.de/FINAM/finam/-/jobs/artifacts/main/raw/bench/bench-run-sim.svg?job=benchmark)

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
