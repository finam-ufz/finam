.. post:: 27 Oct, 2022
    :tags: announcement
    :category: Release
    :author: Martin Lange
    :excerpt: 2

==================
FINAM 0.4 released
==================

After two months of hard work since the last release, FINAM 0.4 comes with a full load of new features
and usability improvements. This version is a real breakthrough in the development of FINAM!

Highlights are a new scheduling algorithm, grid data types, automatic metadata and units handling,
more flexible exchange during initialization, and a completely reworked documentation.

What's new?
-----------

FINAM 0.4 comes with several new major features around data and metadata handling.

Scheduling algorithm
^^^^^^^^^^^^^^^^^^^^

The old scheduling algorithm simply selected the component most back in time.
It had the flaw that the data received by a component was usually associated to time passed,
rather than to the time span of the next step to perform.

The new algorithm recursively analyzes dependencies and updates upstream components before advancing downstream components.
This way, components can rely on data that is not outdated.

For circular couplings, we provide a new adapter that extrapolates in time, so the dependency cycle can be interrupted.

For more details on the new algorithm, see the book chapter :doc:`/finam-book/principles/coupling_scheduling`.

Metadata for all coupling slots
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

All component inputs and outputs have metadata now.
Mandatory metadata are `Grid specifications`_ and units, but more is possible.

FINAM automatically checks data vs. metadata to detect inconsistencies or malicious coupling setups.

All data is :mod:`xarray` with :mod:`pint` units
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add data is now passed as :class:`xarray.DataArray`, with :mod:`pint` units attached.
This allows for comprehensive checks against metadata to ensure correct grid layout, units, etc.

Users can still handle data as :mod:`numpy` :class:`ndarray <numpy.ndarray>`
and leave the conversion to FINAM.
Attached units work with :mod:`numpy` as well as :mod:`xarray` data,
so all calculations can and should be done with units for safety.
Units are checked by inputs, and converted automatically if they are compatible.
So there are no adapters required for unit conversion.

Grid specifications
^^^^^^^^^^^^^^^^^^^

One particularly important piece of metadata are grid specifications.

FINAM comes with specifications for structured grids like :class:`.UniformGrid` and :class:`.RectilinearGrid`.
For unstructured grids, :class:`.UnstructuredGrid` (i.e. meshes) and :class:`.UnstructuredPoints` are provided.

Data that is not on a grid or mesh is also supported through :class:`.NoGrid`.

For an important aspect of using grid specifications, see section `Regridding and CRS handling`_.

Bi-directional metadata exchange
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Data exchange during initialisation of a :class:`.Composition` was already possible in version 0.3,
allowing to set up components based on external data.

We bring this to a new level by exchanging the metadata of component coupling slots in both directions.
This happens in an iterative way, which allows components to use external metadata to set up their own slots.
A component can now get metadata from a source component, and use it to initialize its outputs.
It is even possible to get the metadata from targets, and use it to initialize its inputs.

Connect phase usability
^^^^^^^^^^^^^^^^^^^^^^^

The vast possibilities offered by `Bi-directional metadata exchange`_ come with some increased complexity during the :doc:`/finam-book/development/connect_phase`.

To relieve users from this burden, we provide convenience methods in :class:`.Component` to help with the process.
The methods :meth:`.Component.create_connector` and :meth:`.Component.try_connect`
make the connection phase a no-brainer for most use cases.
Of course, :class:`.TimeComponent` can also make use of them.

Enhanced components without time
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

With this release, we add full functionality to components that have no internal time step (class :class:`.Component`).
In addition to push-based components that react to newly available data,
pull-based components are now possible. This allows for components that react on pull events to their inputs.
This feature is particularly useful for analytical or statistical models that have no internal state.

An example for the use of this new feature is the :class:`SimplexNoise <.modules.SimplexNoise>` generator.
It generates time-dependent OpenSimplex noise in 1D to 3D, and does not require internal time stepping.

New components and adapters
^^^^^^^^^^^^^^^^^^^^^^^^^^^

This release also comes with new components and adapters.
Further, some components were moved to separate packages.

Regridding and CRS handling
"""""""""""""""""""""""""""

With :class:`RegridLinear <.adapters.RegridLinear>` and :class:`RegridNearest <.adapters.RegridNearest>`,
FINAM now comes with two first basic adapters for regridding between different `Grid specifications`_.
In addition to handling different grid layouts, both adapters can als perform CRS conversions.

Due to the new `Bi-directional metadata exchange`_, the input and output `Grid specifications`_ do not need to be given by the user.
Rather, the adapter automatically determines them from the connected components.

OpenSimplex noise generator
"""""""""""""""""""""""""""

For debugging and demonstration purposes, FINAM now comes with a pull-based :class:`SimplexNoise <.modules.SimplexNoise>` generator.
It generates time-dependent OpenSimplex noise on demand, in 0D to 3D, for any given grid specification.

Grid specification and units can even be determined from connected target components for particular ease of use.

Live plotting components
""""""""""""""""""""""""

The new package `finam-plot <https://finam.pages.ufz.de/finam-plot/>`_ provides a collection of visualization components for plotting grids and time series.

The old visualization components were removed from the core package.

NetCDF file I/O components
""""""""""""""""""""""""""

package `finam-netcdf <https://git.ufz.de/FINAM/finam-netcdf>`_ provides several components for reading and writing NetCDF files.

Next steps and future direction
-------------------------------

Most important in the near future, FINAM needs testing in production, as well as user feedback.

FINAM's functionality is well-tested for all use cases we have in mind, with 99% test coverage!
But still, we are working with dummy components for testing. Also, all developers working on wrappers for existing models are highly involved in the process of FINAM development.
Thus, they are probably biased and over-informed.

To make progress with FINAM, we would love to get feedback from new users that approach FINAM from an unbiased perspective.
Most of the future progress and direction will depend in this feedback.
