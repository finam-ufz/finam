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

.. autosummary::

    RegridNearest
    RegridLinear

Time adapters
"""""""""""""

.. autosummary::

    ExtrapolateTime
    IntegrateTime
    LinearTime
    NextTime
    PreviousTime
    TimeCachingAdapter

Provided by FINAM developers
----------------------------

Components
^^^^^^^^^^
* `finam-plot <https://finam.pages.ufz.de/finam-plot/>`_
    Provides FINAM components for live plotting using :mod:`matplotlib`.
* `finam-netcdf <https://git.ufz.de/FINAM/finam-netcdf>`_
    Provides FINAM components for `NetCDF <https://www.unidata.ucar.edu/software/netcdf/>`_ file reading and writing.

Tools
^^^^^

* `finam-graph <https://git.ufz.de/FINAM/finam-graph>`_
    A tool for visualizing FINAM coupling setups.

Known 3rd party
---------------

None
