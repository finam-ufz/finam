===================
Known FINAM modules
===================

This chapter lists known components and adapters for use in FINAM compositions.

Included in FINAM core package
------------------------------

Components
^^^^^^^^^^

Several components, primarily for testing and debugging, are provided in module :mod:`finam.modules`.

.. currentmodule:: finam.modules

.. autosummary::
    CallbackComponent
    CallbackGenerator
    CsvReader
    CsvWriter
    DebugConsumer
    DebugPushConsumer
    ScheduleLogger
    SimplexNoise
    StaticSimplexNoise
    TimeTrigger
    UserControl
    WeightedSum

Adapters
^^^^^^^^

Different general-purpose adapters are provided in module :mod:`finam.adapters`.

.. currentmodule:: finam.adapters


Base adapters
"""""""""""""

.. autosummary::

    Callback
    Scale
    ValueToGrid
    GridToValue

Probe adapters
""""""""""""""

.. autosummary::

    CallbackProbe

Regridding adapters
"""""""""""""""""""

See also package `finam-regrid <https://finam.pages.ufz.de/finam-regrid/>`_ for more advanced regridding.

.. autosummary::

    RegridNearest
    RegridLinear

Statistics adapters
"""""""""""""""""""

.. autosummary::

    Histogram

Time adapters
"""""""""""""

.. autosummary::

    IntegrateTime
    LinearTime
    NextTime
    PreviousTime
    StackTime
    OffsetFixed
    OffsetToPush
    OffsetToPull

Provided by FINAM developers
----------------------------

Components
^^^^^^^^^^

* `finam-plot <https://finam.pages.ufz.de/finam-plot/>`_
    FINAM components for live plotting using :mod:`matplotlib`.
* `finam-netcdf <https://finam.pages.ufz.de/finam-netcdf/>`_
    FINAM components for `NetCDF <https://www.unidata.ucar.edu/software/netcdf/>`_ file reading and writing.

Adapters
^^^^^^^^

* `finam-regrid <https://finam.pages.ufz.de/finam-regrid/>`_
    FINAM adapter for advances regridding using `ESMPy <https://earthsystemmodeling.org/esmpy/>`_.

Tools
^^^^^

* `finam-graph <https://finam.pages.ufz.de/finam-graph/>`_
    A tool for visualizing FINAM coupling setups.

Known 3rd party
---------------

None
