======================
Model coupling scripts
======================

Coupling setups are created and executed using Python scripts.

Simple example
--------------

Here is a simple example coupling two components:

.. testcode:: simple-example

    # simple-coupling.py
    import random
    from datetime import datetime, timedelta

    import finam as fm

    # Instantiate components, e.g. models

    # Here, we use simplex noise to get a value smoothly varying over time
    generator = fm.modules.SimplexNoise(
        time_frequency=0.000001,
        info=fm.Info(time=None, grid=fm.NoGrid()),
    )

    # A debug printing component
    consumer = fm.modules.DebugConsumer(
        inputs={"Value": fm.Info(time=None, grid=fm.NoGrid())},
        start=datetime(2000, 1, 1),
        step=timedelta(days=1),
        log_data="INFO",
    )

    # Create a `Composition` containing all components
    composition = fm.Composition([generator, consumer])

    # Initialize the `Composition`
    composition.initialize()

    # Couple inputs to outputs
    generator.outputs["Noise"] >> consumer.inputs["Value"]

    # Run the composition until June 2000
    composition.run(t_max=datetime(2000, 6, 30))    # doctest: +ELLIPSIS

.. testoutput:: simple-example
    :hide:

    ...

In the above example, we couple a simplex noise generator component (:class:`.modules.SimplexNoise`)
with a consumer component for debug printing (:class:`.modules.DebugConsumer`).

Note:
    with package :mod:`finam` installed, simply run the above scripts with:

    .. code-block:: bash

        $ python simple-coupling.py

The typical steps in a script are:

#. Instantiate components and adapters (see next example)
#. Create a :class:`.Composition` and initialize it
#. Connect outputs to inputs using the overloaded ``>>`` operator (:meth:`.IOutput.__rshift__`)
#. Run the :class:`.Composition`

Inputs and outputs
------------------

Inputs and outputs of a component can be retrieved via :attr:`.IComponent.inputs` and :attr:`.IComponent.outputs` properties.
Both methods return a Python ``dict-like``, with strings as keys and input or output objects as values, respectively.

An input can be connected to an output using either ``>>`` (as in the examples), or the output's method :meth:`.IOutput.chain`. Both lines here are equivalent:

.. code-block:: Python

    generator.outputs["Value"] >> plot.inputs["Value"]
    generator.outputs["Value"].chain(consumer.inputs["Value"])

As a shortcut, slots can be accessed by the component's ``[]`` operator directly (see :meth:`.Component.__getitem__`):

.. code-block:: Python

    generator["Value"] >> plot["Value"]

Adapters
--------

In the above example, both coupled components match in terms of the exchanged data (numeric value)
as well as their time step (1 day).

This is not necessarily the case for all coupling setups.
To mediate between components, FINAM uses adapters.
Those can be used to transform data (regridding, geographic projections, ...)
or for temporal interpolation or aggregation.

The following examples uses a similar setup like the previous one, but with differing
time steps and an adapter:

.. testcode:: adapter-example

    # adapter-coupling.py
    import random
    from datetime import datetime, timedelta

    import finam as fm

    # Instantiate components, e.g. models

    # Here, we use simplex noise to get a value smoothly varying over time
    generator = fm.modules.SimplexNoise(
        time_frequency=0.000001,
        info=fm.Info(time=None, grid=fm.NoGrid()),
    )
    # A debug printing component
    consumer_1 = fm.modules.DebugConsumer(
        inputs={"Value": fm.Info(time=None, grid=fm.NoGrid())},
        start=datetime(2000, 1, 1),
        step=timedelta(days=1),
        log_data="INFO",
    )
    # A second debug printing component with a different time step
    consumer_2 = fm.modules.DebugConsumer(
        inputs={"Value": fm.Info(time=None, grid=fm.NoGrid())},
        start=datetime(2000, 1, 1),
        step=timedelta(days=2.324732),
        log_data="INFO",
    )

    # Create a `Composition` containing all components
    composition = fm.Composition([generator, consumer_1, consumer_2])

    # Initialize the `Composition`
    composition.initialize()

    # Couple inputs to outputs, without an adapter
    (
        generator.outputs["Noise"]
        >> consumer_1.inputs["Value"]
    )
    # Couple inputs to outputs, with an adapters
    (
        generator.outputs["Noise"]
        >> fm.adapters.Scale(scale=10.0)
        >> consumer_2.inputs["Value"]
    )

    # Run the composition until June 2000
    composition.run(t_max=datetime(2000, 6, 30))    # doctest: +ELLIPSIS

.. testoutput:: adapter-example
    :hide:

    ...

Adapter chaining
----------------

As can be seen from the example, components and adapters can be chained using the ``>>`` operator (or the :meth:`.IOutput.chain` method).

This is achieved by:

#. An adapter is an input, and at the same time an output
#. The chained input is returned by `>>` and :meth:`.IOutput.chain`. In case the chained input is an adapter (and thus also an output), it can be immediately reused in a further chaining operation

The syntax looks like this:

.. code-block:: Python

    (
        generator.outputs["Noise"]
        >> AdapterA()
        >> AdapterB()
        >> consumer.inputs["Value"]
    )

Or, in the short slot syntax:

.. code-block:: Python

    (
        generator["Noise"]
        >> AdapterA()
        >> AdapterB()
        >> consumer["Value"]
    )


Circular and bi-directional coupling
------------------------------------

FINAM allows for bi-directional and circular coupling.

For acyclic coupling, the FINAM scheduler updates upstream components first
to allow downstream components to pull data for the end of their next time step.
With circular dependencies, this would result in an infinite loop.
The scheduler detects these cases and exits with a respective message.

To resolve circular dependencies, one of the models in the cycle must use data from the past (i.e. delayed).
FINAM provides several adapters for this purpose:

* :class:`.adapters.DelayFixed`
* :class:`.adapters.DelayToPull`
* :class:`.adapters.DelayToPush`

The adapters are used on the inputs of the component that is intended to work with delayed data.

For all except :class:`.adapters.DelayToPush`, the adapters must be parametrized with a sensible delay.
Some rules of thumb for choosing the delay:

* For components where one time step is an integral multiple of other one,
  a delay equal to the larger step should be sufficient.
* For components with no such time step ratio,
  the sum of the (two largest) time steps should be sufficient.

Logging
-------

FINAM provides a comprehensive logging framework built on Pythons standard :mod:`logging` package.

You can configure the base logger when creating the :class:`.Composition` as shown above:

.. testcode:: composition

    import finam as fm
    import logging

    comp = fm.Composition(
        [],
        logger_name="FINAM",
        print_log=True,
        log_file=True,
        log_level=logging.INFO,
    )

There you have several options:

- ``logger_name``: (str) Base name of the logger in the output (``"FINAM"`` by default)
- ``print_log``: (bool) Whether logging should be shown in the terminal output
- ``log_file``: (None, bool, pathlike) Whether a log-file should be created
  - ``None`` or ``False``: no log file will be written
  - ``True``: a log file with the name ``{logger_name}_{time.strftime('%Y-%m-%d_%H-%M-%S')}.log`` will be created in the current working directory (e.g. ``FINAM_2022-09-26_12-58-15.log``)
  - ``<pathlike>``: log file will be created under the given path
- ``log_level``: (int) this will control the level of logging (:data:`logging.INFO` by default)
  - only log messages with a level equal or higher than the given logging level will be shown
  - options are (from most to least verbose): :data:`logging.DEBUG`, :data:`logging.INFO`, :data:`logging.WARNING`, :data:`logging.ERROR`, :data:`logging.CRITICAL` or any positive integer number

A log file could look like this, when setting the logging level to :data:`logging.INFO`:


.. code-block::

    2022-08-26 11:31:28,283 - FINAM - INFO - doing fine
    2022-08-26 11:31:28,284 - FINAM - WARNING - Boo

or like this, when setting logging level to :data:`logging.DEBUG`:

.. code-block::

    2022-08-26 11:31:28,283 - FINAM - INFO - doing fine
    2022-08-26 11:31:28,284 - FINAM - WARNING - Boo
    2022-08-26 11:31:28,285 - FINAM - DEBUG - Some debugging message
