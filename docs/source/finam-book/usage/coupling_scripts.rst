======================
Model coupling scripts
======================

Coupling setups are created and executed using Python scripts.

Simple example
--------------

Here is a simple example coupling two components:

.. code-block:: Python

    # simple-coupling.py

    import random
    from datetime import datetime, timedelta

    import finam as fm

    if __name__ == "__main__":
      # Instantiate components, e.g. models

      # Here, we use a simple component that outputs a random number each step
      generator = fm.modules.CallbackGenerator(
        {"Value": (lambda _t: random.uniform(0, 1), fm.Info(time=None, grid=fm.NoGrid()))},
        start=datetime(2000, 1, 1),
        step=timedelta(days=1),
      )

      # A live plotting component
      plot = fm.modules.TimeSeriesView(
        inputs=["Value"],
        start=datetime(2000, 1, 1),
        step=timedelta(days=1),
        intervals=[1],
      )

      # Create a `Composition` containing all components
      composition = fm.Composition([generator, plot])

      # Initialize the `Composition`
      composition.initialize()

      # Couple inputs to outputs
      generator.outputs["Value"] >> plot.inputs["Value"]

      # Run the composition until January 2001
      composition.run(datetime(2001, 1, 1))

In the above example, we couple a simple generator component (:class:`.modules.CallbackGenerator`)
with a live plotting component (:class:`.modules.TimeSeriesView`).

    Note: with package :mod:`finam` installed, simply run the above scripts with:

    .. code-block:: bash

        $ python simple-coupling.py

The typical steps in a script are:

1. Instantiate components and adapters (see next example)
2. Create a :class:`.Composition` and initialize it
3. Connect outputs to inputs using the overloaded ``>>`` operator (:meth:`.IOutput.__rshift__`)
4. Run the :class:`.Composition`

Inputs and outputs
------------------

Inputs and outputs of a component can be retrieved via :attr:`.IComponent.inputs` and :attr:`.IComponent.outputs` properties.
Both methods return a Python ``dict-like``, with strings as keys and input or output objects as values, respectively.

An input can be connected to an output using either ``>>`` (as in the examples), or the output's method :meth:`.IOutput.chain`. Both lines here are equivalent:

.. code-block:: Python

    generator.outputs["Value"] >> plot.inputs["Value"]
    generator.outputs["Value"].chain(plot.inputs["Value"])


Adapters
--------

In the above example, both coupled components match in terms of the exchanged data (numeric value) as well as their time step (1).

This is not necessarily the case for all coupling setups.
To mediate between components, FINAM uses adapters.
Those can be used to transform data (regridding, geographic projections, ...)
or for temporal interpolation or aggregation.

The following examples uses a similar setup like the previous one, but with differing
time steps and two chained adapters:

.. code-block:: Python

    # adapter-coupling.py

    import random
    from datetime import datetime, timedelta

    import finam as fm

    if __name__ == "__main__":
      # Instantiate components, e.g. models

      # Here, we use a simple component that outputs a random number each step
      generator = fm.modules.CallbackGenerator(
        {"Value": (lambda _t: random.uniform(0, 1), fm.Info(time=None, grid=fm.NoGrid()))},
        start=datetime(2000, 1, 1),
        step=timedelta(days=10),
      )

      # A live plotting component
      plot = fm.modules.TimeSeriesView(
        inputs=["Value"],
        start=datetime(2000, 1, 1),
        step=timedelta(days=1),
        intervals=[1],
      )

      # Create two adapters for...
      # temporal interpolation
      time_interpolation_adapter = fm.adapters.LinearTime()
      # data transformation
      square_adapter = fm.adapters.Callback(lambda x, _time: x * x)

      # Create a `Composition` containing all components
      composition = fm.Composition([generator, plot])

      # Initialize the `Composition`
      composition.initialize()

      # Couple inputs to outputs, via multiple adapters
      (
              generator.outputs["Value"]
              >> time_interpolation_adapter
              >> square_adapter
              >> plot.inputs["Value"]
      )

      # Run the composition until January 2000
      composition.run(datetime(2001, 1, 1))

### Adapter chaining

As can be seen from the example, components and adapters can be chained using the ``>>`` operator (or the :meth:`.IOutput.chain` method).

This is achieved by:

1. An adapter is an input, and at the same time an output
2. The chained input is returned by `>>` and :meth:`.IOutput.chain`. In case the chained input is an adapter (and thus also an output), it can be immediately reused in a further chaining operation

Logging
-------

FINAM provides a comprehensive logging framework built on Pythons standard :mod:`logging` package.

You can configure the base logger when creating the :class:`.Composition` as shown above:

.. code-block:: Python

    import logging

    comp = Composition(
        modules,
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
