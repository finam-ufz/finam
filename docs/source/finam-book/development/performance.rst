======================
Optimizing performance
======================

Performance can be critical when running large numbers of simulations with FINAM.

This chapter gives advice on how to write efficient components and adapters.
Further, suggestions regarding benchmarking and profiling are given.

Benchmarking statistics for FINAM functionality can be found in the GitLab repository
under `benchmarks <https://git.ufz.de/FINAM/finam/-/tree/main/benchmarks>`_.

Optimizing performance
----------------------

This section gives advice on how to write efficient components and adapters.

.. note::
    For logging of potentially performance-critical internal calculations,
    set the logging level of a composition to ``PROFILE``.

Units
^^^^^

All data passed around has :mod:`pint` units.
This added safety may come with a performance cost.
This section gives some hints on how to handle units efficiently.

Avoid unit conversions
""""""""""""""""""""""

FINAM does automatic units conversion in :class:`.Input` objects.
This comes at the cost of computation time.
Conversion of a 1000x1000 grid requires about 1 ms, while a push and pull without a conversion requires about 0.05 ms.
For details, see the `benchmarks <https://git.ufz.de/FINAM/finam/-/tree/main/benchmarks>`_.

Where possible, use the same units in linked components.

Equivalent units have no calculation overhead (e.g. ``mm`` and ``L/m^2``).

Use ``Quantity``
""""""""""""""""

If no copy of the data is required, use `Quantity` instead of the multiplication syntax:

.. testcode:: create-units
    :hide:

    import finam

.. testcode:: create-units

    data = finam.UNITS.Quantity(1.0, "m")  # Good / fast

    data = 1.0 * finam.UNITS.Unit("m")     # Bad / slow

Cache units
"""""""""""

Constructing units again and again is costly.
If the same units are used e.g. in loops, it might be helpful to construct them in advance:

.. testcode:: cache-units
    :hide:

    import finam
    data = [1.0]

.. testcode:: cache-units

    u = finam.UNITS.Unit("m")
    for entry in data:
        data = finam.UNITS.Quantity(data, u)

Use magnitudes when possible
""""""""""""""""""""""""""""

Mathematical calculations are significantly faster when calculating with magnitudes.
See the :mod:`pint` chapter on
`Performance Optimization <https://pint.readthedocs.io/en/stable/advanced/performance.html>`_ for details.

Memory limitations
------------------

FINAM's flexible :doc:`scheduling </finam-book/principles/coupling_scheduling>` and
:doc:`/blog/posts/time-adapters` capabilities come at the cost of holding multiple data arrays in
:class:`.Output` and time-related :class:`.Adapter` objects.

Outputs collect pushed data and release only data that is associated to a time before the last pull of any connected input.

This may become a problem if large data arrays are pushed frequently, but pulled infrequently.
Similar situations can arise if a component is forced to calculate far ahead of a target component.

As an example, in a source component with a daily step, linked to a target component with an annual step,
365 data arrays would be stored in the :class:`.Output` until the next pull.

Use ``memory_limit``
^^^^^^^^^^^^^^^^^^^^

FINAM provides a mechanism to store data that would exceed a certain memory limit to files.
The memory limit applies to each individual :class:`.Output` and :class:`.Adapter`, not to the composition as a whole.

The limit and file location can be set for all slots of the composition:

.. testcode:: memory-limit
    :hide:

    import finam

.. testcode:: memory-limit

    comp_a = finam.modules.SimplexNoise()
    comp_b = finam.modules.SimplexNoise()

    comp = finam.Composition(
        modules=[comp_a, comp_b],
        slot_memory_limit=256 * 2**20, # 256MB
        slot_memory_location="temp_dir",
    ) # doctest: +ELLIPSIS

.. testoutput:: memory-limit
    :hide:

    ...

Both properties can also be set for individual :class:`.Output` and :class:`.Adapter` objects:

.. testcode:: memory-limit

    comp_a = finam.modules.SimplexNoise()
    comp_b = finam.modules.SimplexNoise()

    comp = finam.Composition([comp_a, comp_b]) # doctest: +ELLIPSIS

    comp_a.outputs["Noise"].memory_limit = 256 * 2**20 # 256MB

.. testoutput:: memory-limit
    :hide:

    ...

.. warning::
    Storing data in files comes with a considerable runtime overhead.
    For details, see the `benchmarks <https://git.ufz.de/FINAM/finam/-/tree/main/benchmarks>`_.

Reduce time step difference
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Time steps of the same order of magnitude for linked components reduces the requirement for storing large numbers of data arrays.
In many cases, this is most effective when combined with `Aggregating data in components`_.

Aggregating data in components
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Components are not required to push data after every step.
This allows for components that use a sub-step to pull data and aggregate it internally.

This is particularly useful for components with a large time step where inputs are expected
to be an aggregate of many small time steps, like the annual sum of a daily value.

Instead of (or in addition to) using a
:class:`SumOverTime <.adapters.SumOverTime>` or :class:`AvgOverTime <.adapters.AvgOverTime>` adapter,
a component can do the aggregation internally with a daily sub-step.

Benchmarking and profiling
--------------------------

This section gives advice on how to profile FINAM modules and compositions.

[TODO]
