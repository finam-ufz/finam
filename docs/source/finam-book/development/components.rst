==================
Writing components
==================

This chapter provides a step-by-step guide to implement a component with time (e.g. a model) in pure Python.
For writing Python bindings for other languages, see :doc:`py-bindings`.

Completing the chapter will result in a simple component called ``DummyModel``.
We will build up the component step by step, accompanied by some test code.
Finally, it will have two input slots and one output slot, and will calculate the sum of its inputs.

The component will have internal time stepping, like a simulation model would have.
For implementing components without internal time, see chapter :doc:`./special_components`.

It is assumed that you have FINAM :doc:`installed <../usage/installation>`, as well as :mod:`pytest`.

For component implementation examples, see the `FINAM Examples repository <https://git.ufz.de/FINAM/finam-examples>`_,
or browse the source code of the included components in module :mod:`.modules`.
The source code of each API entry is linked in it's upper right corner under ``[source]``.

Set up a Python project
-----------------------

Create the following project structure:

.. code-block::

    - dummy_model/
       +- src/

We call ``dummy_model`` the project directory from here on.

Implement :class:`.TimeComponent`
---------------------------------

The class :class:`.TimeComponent` provides an abstract implementation of the interface :class:`.ITimeComponent` to make implementation easier.
Start by extending :class:`.TimeComponent` in a class we call ``DummyModel`` in ``src/dummy_model.py``.

.. code-block:: Python

    import finam as fm


    class DummyModel(fm.TimeComponent):
        pass

However, we want to test our implementation while building up, so extend the file to the following content:

.. code-block:: Python

    import finam as fm
    import unittest                                                      # <--


    class DummyModel(fm.TimeComponent):
        pass


    class TestDummy(unittest.TestCase):                                  # <--
        def test_dummy_model(self):                                      # <--
            model = DummyModel()                                         # <--
            self.assertTrue(isinstance(model, DummyModel))               # <--

In your project directory run the following to test it:

.. code-block:: bash

    $ python -m pytest -s src/dummy_model.py

Constructor
-----------

The component needs a constructor which calls the super class constructor.

.. code-block:: Python

    import finam as fm
    import unittest
    from datetime import datetime                                        # <--


    class DummyModel(fm.TimeComponent):

        def __init__(self, start):                                       # <--
            super().__init__()                                           # <--
            self.time = start


    class TestDummy(unittest.TestCase):
        def test_dummy_model(self):
            model = DummyModel(start=datetime(2000, 1, 1))
            self.assertEqual(model.status, fm.ComponentStatus.CREATED)   # <--
            self.assertEqual(model.time, datetime(2000, 1, 1))           # <--


The property :attr:`.TimeComponent.status` is provided by :class:`.Component`, as are :attr:`.TimeComponent.inputs` and :attr:`.TimeComponent.outputs`, which are initialized with defaults.
We will manipulate them later.

The :attr:`.TimeComponent.time` property must be initialized with a :class:`datetime <datetime.datetime>` object.

The constructor is also the place to define class variables required by the component.
We want our component to have a user-defined time step, so we add it here:

.. code-block:: Python

    import finam as fm
    import unittest
    from datetime import datetime, timedelta


    class DummyModel(fm.TimeComponent):

        def __init__(self, start, step):                                 # <--
            super().__init__()
            self._step = step                                            # <--
            self.time = start

        @property                                                        # <--
        def next_time(self):                                             # <--
            return self.time + self._step                                # <--


    class TestDummy(unittest.TestCase):
        def test_dummy_model(self):
            model = DummyModel(start=datetime(2000, 1, 1),               # <--
                               step=timedelta(days=7))                   # <--
            self.assertEqual(model.status, fm.ComponentStatus.CREATED)
            self.assertEqual(model.time, datetime(2000, 1, 1))
            self.assertEqual(model._step, timedelta(days=7))             # <--


Run the test again to check everything is working.

Next, we need to implement or override some methods of :class:`.TimeComponent`

Initialize
----------

In :meth:`.TimeComponent._initialize`, we define the component's input and output slots.
It is called internally by the :meth:`.TimeComponent.initialize` method.

(We will shorten previously completed parts and imports from now on.)

.. code-block:: Python

    import finam as fm
    import unittest
    from datetime import datetime, timedelta


    class DummyModel(fm.TimeComponent):

        def __init__(self, start, step):
            # ...

        @property
        def next_time(self):
            # ...

        def _initialize(self):                                             # <--
            self.inputs.add(name="A", time=self.time, grid=fm.NoGrid())    # <--
            self.inputs.add(name="B", time=self.time, grid=fm.NoGrid())    # <--
            self.outputs.add(name="Sum", time=self.time, grid=fm.NoGrid()) # <--

            self.create_connector()                                        # <--


    class TestDummy(unittest.TestCase):
        def test_dummy_model(self):
            model = DummyModel(start=datetime(2000, 1, 1),
                               step=timedelta(days=7))
            # ...

            model.initialize()
            self.assertEqual(model.status, fm.ComponentStatus.INITIALIZED)  # <--
            self.assertEqual(len(model.inputs), 2)                          # <--
            self.assertEqual(len(model.outputs), 1)                         # <--

Note that inputs and outputs are added with a name and a grid (or grid specification).
They can later be accessed by the name, like ``self.inputs["A"]`` and ``self.outputs["Sum"]``.
Or, even shorter, by ``self["A"]`` and ``self["Sum"]``.
The same syntax is used for coupling, see chapter :doc:`../usage/coupling_scripts`.

.. note::

    Don't give inputs and outputs the same name, as this will prevent the use of the simplified slot access syntax.

The grid specification defines what inputs expect to receive, or what outputs provide.
Here, we set it to a :class:`NoGrid` instance, as we want to handle scalars only.
In most real use cases, however, ``grid`` will be a grid specification like rectilinear or unstructured grids.
See chapter :doc:`./data_metadata` for more details.

In the last line, we call :meth:`.TimeComponent.create_connector`, which sets up an internal helper that manages the initial exchange of data and metadata.
For details and possible arguments, see chapter :doc:`./connect_phase`.

Connect and validate
--------------------

For the coupling to work, it is necessary that every component populates its outputs with initial values.
This is done in :meth:`.TimeComponent._connect`.

After this connection phase, models can validate their state in :meth:`.TimeComponent._validate`. We do nothing there.

.. note::

    It is not strictly required to implement `_validate` but it is highly encouraged to do so.

.. code-block:: Python

    # imports...


    class DummyModel(fm.TimeComponent):

        def __init__(self, step):
            # ...

        def _initialize(self):
            # ...

        def _connect(self, start_time):                                                      # <--
            self.try_connect(start_time, push_data={"Sum": 0})                               # <--

        def _validate(self):                                                     # <--
            pass                                                                 # <--

In :meth:`.TimeComponent._connect()`, we call :meth:`.TimeComponent.try_connect` with the component's time (it's starting time),
and a dictionary of data to push for each input.
For more complex use cases like pulling data, see chapter :doc:`./connect_phase`.

For the tests, we need to set up a real coupling from here on, as the component's inputs require connections in this phase.

.. code-block:: Python

    class TestDummy(unittest.TestCase):
        def test_dummy_model(self):
            # our model
            model = DummyModel(start=datetime(2000, 1, 1),
                               step=timedelta(days=7))

            # a component to produce inputs, details not important
            generator = fm.modules.generators.CallbackGenerator(
                callbacks={
                    "A": (lambda t: t.day, fm.Info(time=None, grid=fm.NoGrid())),
                    "B": (lambda t: t.day * 2, fm.Info(time=None, grid=fm.NoGrid()))
                },
                start=datetime(2000, 1, 1),
                step=timedelta(days=7)
            )

            # a component to consume output, details not important
            consumer = fm.modules.debug.DebugConsumer(
                inputs={"Sum": fm.Info(time=None, grid=fm.NoGrid())},
                start=datetime(2000, 1, 1),
                step=timedelta(days=7)
            )

            # set up a composition
            composition = fm.Composition([model, generator, consumer],
                                         log_level="DEBUG")
            composition.initialize()

            # connect components
            generator.outputs["A"] >> model.inputs["A"]
            generator.outputs["B"] >> model.inputs["B"]

            model.outputs["Sum"] >> consumer.inputs["Sum"]

            # run the connection/exchange phase
            composition.connect()

            self.assertEqual(consumer.data, {"Sum": 0})

Here, we set up a complete coupling using a :class:`.modules.CallbackGenerator` as source.
A :class:`.modules.DebugConsumer` is used as a sink to force the data flow and to allow us to inspect the result.

Update
-------

Method :meth:`.TimeComponent._update()` is where the actual work happens.
It is called every time the :doc:`../principles/coupling_scheduling` decides that the component is on turn to make an update.

In :meth:`.TimeComponent._update`, we get the component's input data, do a "model step", increment the time, and push results to the output slot.

.. code-block:: Python

    # imports...


    class DummyModel(fm.TimeComponent):

        def __init__(self, step):
            # ...

        def _initialize(self):
            # ...

        def _connect(self, start_time):
            # ...

        def _validate(self):
            # ...

        def _update(self):
            self._time += self._step

            a = self.inputs["A"].pull_data(self.time)
            b = self.inputs["B"].pull_data(self.time)

            result = a + b

            self.outputs["Sum"].push_data(result, self.time)


    class TestDummy(unittest.TestCase):
        def test_dummy_model(self):
            # ...

            composition.run(end_time=datetime(2000, 12, 31))

The test should fail, as we still need to implement the :meth:`.TimeComponent._finalize()` method.

Finalize
--------

In method :meth:`.TimeComponent._finalize`, the component can do any cleanup required at the end of the coupled run, like closing streams or writing final output data to disk.

We do nothing special here.

.. note::

    It is not strictly required to implement `_finalize` but it is highly encouraged to do so.

.. code-block:: Python

    # imports...


    class DummyModel(TimeComponent):

        def __init__(self, step):
            # ...

        def _initialize(self):
            # ...

        def _connect(self, start_time):
            # ...

        def _validate(self):
            # ...

        def _update(self):
            # ...

        def _finalize(self):
            pass

Final code
----------

Here is the final code of the completed component.

.. testcode::

    import unittest
    from datetime import datetime, timedelta

    import finam as fm


    class DummyModel(fm.TimeComponent):
        def __init__(self, start, step):
            super().__init__()
            self._step = step
            self.time = start

        @property
        def next_time(self):
            return self.time + self._step

        def _initialize(self):
            self.inputs.add(name="A", time=self.time, grid=fm.NoGrid())
            self.inputs.add(name="B", time=self.time, grid=fm.NoGrid())
            self.outputs.add(name="Sum", time=self.time, grid=fm.NoGrid())

            self.create_connector()

        def _connect(self, start_time):
            self.try_connect(start_time, push_data={"Sum": 0})

        def _validate(self):
            pass

        def _update(self):
            self._time += self._step

            a = self.inputs["A"].pull_data(self.time)
            b = self.inputs["B"].pull_data(self.time)

            result = a + b

            self.outputs["Sum"].push_data(result, self.time)

        def _finalize(self):
            pass


    class TestDummy(unittest.TestCase):
        def test_dummy_model(self):
            model = DummyModel(start=datetime(2000, 1, 1), step=timedelta(days=7))
            generator = fm.modules.generators.CallbackGenerator(
                callbacks={
                    "A": (lambda t: t.day, fm.Info(time=None, grid=fm.NoGrid())),
                    "B": (lambda t: t.day * 2, fm.Info(time=None, grid=fm.NoGrid())),
                },
                start=datetime(2000, 1, 1),
                step=timedelta(days=7),
            )
            consumer = fm.modules.debug.DebugConsumer(
                inputs={"Sum": fm.Info(time=None, grid=fm.NoGrid())},
                start=datetime(2000, 1, 1),
                step=timedelta(days=7),
            )
            composition = fm.Composition([model, generator, consumer], log_level="DEBUG")
            composition.initialize()

            generator.outputs["A"] >> model.inputs["A"]
            generator.outputs["B"] >> model.inputs["B"]

            model.outputs["Sum"] >> consumer.inputs["Sum"]

            composition.connect()

            self.assertEqual(consumer.data, {"Sum": 0})

            composition.run(end_time=datetime(2000, 12, 31))

    if __name__ == "__main__":
        unittest.main()

.. testcode::
    :hide:

    TestDummy().test_dummy_model() #doctest: +ELLIPSIS

.. testoutput::
    :hide:

    ...
