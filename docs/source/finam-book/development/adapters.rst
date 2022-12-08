================
Writing adapters
================

This chapter provides a step-by-step guide to implement adapters in pure Python.
For writing Python bindings for other languages, see :doc:`./py-bindings`.

Completing the chapter will result in two adapters called ``Scale`` and ``TimeInterpolation``.
We will build up the adapters step by step, accompanied by some test code.

It is assumed that you have FINAM :doc:`installed <../usage/installation>`, as well as :mod:`pytest`.

For adapter implementation examples, browse the source code of the included adapters in module :mod:`.adapters`.
The source code of each API entry is linked in it's upper right corner under ``[source]``.

Set up a Python project
-----------------------

Create the following project structure:

.. code-block::

    - dummy_adapters/
       +- src/

Simple ``Scale`` adapter
------------------------

This is a simple, purely pull-based adapter.
When output is requested, it should simply pull from its input, transform and forward it.

We implement :class:`.IAdapter` by extending :class:`.Adapter`. We only need to overwrite its method :meth:`.Adapter._get_data`,
which is called from downstream to request data.

File ``src/scale.py``:

.. testcode:: scale-adapter

    import finam as fm


    class Scale(fm.Adapter):
        def __init__(self, scale):
            super().__init__()
            self.scale = scale

        def _get_data(self, time, target):
            d = self.pull_data(time, target)
            return d * self.scale

.. testcode:: scale-adapter
    :hide:

    from datetime import datetime, timedelta

    generator = fm.modules.CallbackGenerator(
        {"Value": (lambda _t: 1.0, fm.Info(time=None, grid=fm.NoGrid()))},
        start=datetime(2000, 1, 1),
        step=timedelta(days=1),
    )
    consumer = fm.modules.DebugConsumer(
        {"Input": fm.Info(None, grid=fm.NoGrid())},
        start=datetime(2000, 1, 1),
        step=timedelta(days=1),
    )
    adapter = Scale(0.5)

    comp = fm.Composition([generator, consumer])
    comp.initialize()

    generator.outputs["Value"] >> adapter >> consumer.inputs["Input"]

    comp.run(end_time=datetime(2000, 1, 2))    # doctest: +ELLIPSIS

    print(consumer.data["Input"][0, ...])

.. testoutput:: scale-adapter
    :hide:

    ...
    0.5 dimensionless

In :meth:`.Adapter._get_data`, we:

#. Pull the input for the requested ``time``
#. Multiply the input by ``scale`` and return the result

Time-dependent ``TimeInterpolation`` adapter
--------------------------------------------

The purpose of this adapter is to do temporal interpolation between upstream time steps.
As an example, there could be a model with a weekly time step that passes data to another model with a daily time step.
Assuming continuous transitions of the modelled data, temporal interpolation between the weekly time steps is required.

.. code-block::

      ^                          V
      |                        _.o----
      |                    _.-´
      |                _.-´|
      |            _.-´    |
      |      V _.-´        |
      |  ----o´            |
      +-------------------------------------> t
                           ^

Here, a simple pull-based mechanism is not sufficient.
The adapter needs to store each new data entry that becomes available, and calculate the interpolated data when requested.

Due to FINAM's scheduling algorithm, it is guaranteed that the time stamp of any request lies in the interval of the previous two time steps of any other component
(see :doc:`../principles/coupling_scheduling` for details).
Thus, it is not required to store data for more than two time stamps.

Accordingly, this is the constructor (file ``src/time_interpolation.py``):

.. code-block:: Python

    import finam as fm

    class TimeInterpolation(fm.Adapter):

        def __init__(self):
            super().__init__()
            self.old_data = None
            self.new_data = None

The adapter needs to react to downstream requests as well as to new data available upstream.
This functionality is provided by :class:`.Adapter`'s methods :meth:`.Adapter._get_data` and :meth:`.Adapter._source_updated`, respectively.

.. code-block:: Python

    import finam as fm

    class TimeInterpolation(fm.Adapter):

        def __init__(self):
            super().__init__()
            self.old_data = None
            self.new_data = None

        @property
        def needs_push(self):
            return True

        def _source_updated(self, time):
            pass

        def _get_data(self, time, target):
            pass

Note
  We need to overwrite :attr:`.Adapter.needs_push` here, as the scheduler needs to know that the adapter won't work in a purely pull-based setup.

In :meth:`.Adapter._source_updated`, we need to store incoming data:

.. code-block:: Python

    import finam as fm

    class TimeInterpolation(fm.Adapter):

        def __init__(self):
            super().__init__()
            self.old_data = None
            self.new_data = None

        @property
        def needs_push(self):
            return True

        def _source_updated(self, time):
            data = self.pull_data(time, self)

            self.old_data = self.new_data
            self.new_data = (time, data)

        def _get_data(self, time, target):
            pass

We "move" the previous ``new_data`` to ``old_data``, and replace ``new_data`` by the incoming data, as a ``(time, data)`` tuple.
As the output time will differ from the input time, we need to strip the time off the data by calling :func:`.data.strip_data`.

In :meth:`.Adapter._get_data`, we can now do the interpolation whenever data is requested from upstream.

.. testcode:: time-adapter

    import finam as fm

    class TimeInterpolation(fm.Adapter):

        def __init__(self):
            super().__init__()
            self.old_data = None
            self.new_data = None

        @property
        def needs_push(self):
            return True

        def _source_updated(self, time):
            data = self.pull_data(time, self)

            self.old_data = self.new_data
            self.new_data = (time, data)

        def _get_data(self, time, _target):
            if self.old_data is None:
                if self.new_data is None:
                    raise fm.FinamNoDataError("No data available.")
                else:
                    return self.new_data[1]

            dt = (time - self.old_data[0]) / (self.new_data[0] - self.old_data[0])

            o = self.old_data[1]
            n = self.new_data[1]

            return o + dt * (n - o)

.. testcode:: time-adapter
    :hide:

    from datetime import datetime, timedelta

    generator = fm.modules.CallbackGenerator(
        {"Value": (lambda t: t.day, fm.Info(time=None, grid=fm.NoGrid()))},
        start=datetime(2000, 1, 1),
        step=timedelta(days=30),
    )
    consumer = fm.modules.DebugConsumer(
        {"Input": fm.Info(None, grid=fm.NoGrid())},
        start=datetime(2000, 1, 1),
        step=timedelta(days=1),
    )
    adapter = TimeInterpolation()

    comp = fm.Composition([generator, consumer])
    comp.initialize()

    generator.outputs["Value"] >> adapter >> consumer.inputs["Input"]

    comp.run(end_time=datetime(2000, 1, 15))    # doctest: +ELLIPSIS

    print(consumer.data["Input"][0, ...])

.. testoutput:: time-adapter
    :hide:

    ...
    15.0 dimensionless

In :meth:`.Adapter._get_data`, the following happens:

#. If only one data entry was received so far, we can't interpolate and simply return the available data. Otherwise...
#. Calculate ``dt`` as the relative position of ``time`` in the available data interval (in range [0, 1])
#. Interpolate and return the data

Note that, although we use :class:`datetime <datetime.datetime>` when calculating ``dt``, we get a scalar output.
Due to ``dt`` being relative, time units cancel out here.
