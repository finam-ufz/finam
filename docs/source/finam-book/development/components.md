# Writing components

This chapter provides a step-by-step guide to implement a component with time (e.g. a model) in pure Python.
For writing Python bindings for other languages, see [Python bindings](./py-bindings).

Completing the chapter will result in a simple component called `DummyModel`.
We will build up the component step by step, accompanied by some test code.
Finally, it will have two input slots and one output slot, and will calculate the sum of its inputs.

The component will have internal time stepping, like a simulation model would have.
For implementing components without internal time, see chapter [Components without time step](./special_components).

It is assumed that you have FINAM [installed](../usage/installation), as well as [`pytest`](https://docs.pytest.org/en/6.2.x/).

## Set up a Python project

Create the following project structure:

```
- dummy_model/
   +- src/
```

We call ```dummy_model``` the project directory from here on.

## Implement `TimeComponent`

The class `TimeComponent` provides an abstract implementation of the interface `ITimeComponent` to make implementation easier.
Start by extending `TimeComponent` in a class we call `DummyModel` in `src/dummy_model.py`.

```python
import finam as fm


class DummyModel(fm.TimeComponent):
    pass
```

However, we want to test our implementation while building up, so extend the file to the following content:

```python
import finam as fm
import unittest                                                      # <--


class DummyModel(fm.TimeComponent):
    pass


class TestDummy(unittest.TestCase):                                  # <--
    def test_dummy_model(self):                                      # <--
        model = DummyModel()                                         # <--
        self.assertTrue(isinstance(model, DummyModel))               # <--
```

In your project directory run the following to test it:

```shell
$ python -m pytest -s src/dummy_model.py
```

## Constructor

The component needs a constructor which calls the super class constructor.

```python
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
```

The property `status` is provided by `TimeComponent`, as are `inputs` and `outputs`, which are initialized with defaults.
We will manipulate them later.

`TimeComponent`'s `time` property must be initialized with a `datetime` object.

The constructor is also the place to define class variables required by the component.
We want our component to have a user-defined time step, so we add it here:

```python
import finam as fm
import unittest
from datetime import datetime, timedelta


class DummyModel(fm.TimeComponent):

    def __init__(self, start, step):                                 # <--
        super().__init__()
        self._step = step                                            # <--
        self.time = start


class TestDummy(unittest.TestCase):
    def test_dummy_model(self):
        model = DummyModel(start=datetime(2000, 1, 1),               # <--
                           step=timedelta(days=7))                   # <--
        self.assertEqual(model.status, fm.ComponentStatus.CREATED)
        self.assertEqual(model.time, datetime(2000, 1, 1))
        self.assertEqual(model._step, timedelta(days=7))             # <--
```

Run the test again to check everything is working.

Next, we need to implement or override some methods of `TimeComponent`

## Initialize

In `_initialize()`, we define the component's input and output slots.
It is called internally by the `initialize()` method.

(We will shorten previously completed parts and imports from now on.)

```python
import finam as fm
import unittest
from datetime import datetime, timedelta


class DummyModel(fm.TimeComponent):

    def __init__(self, start, step):
        # ...

    def _initialize(self):                                             # <--
        self.inputs.add(name="A", grid=fm.NoGrid())                    # <--
        self.inputs.add(name="B", grid=fm.NoGrid())                    # <--
        self.outputs.add(name="Sum", grid=fm.NoGrid())                 # <--

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
```

Note that inputs and outputs are added with a name and a grid (or grid specification).
They can later be accessed by the name, like `self.inputs["A"]`.

The grid specification defines what inputs expect to receive, or what outputs provide.
Here, we set it to `NoGrid()`, as we want to handle scalars only.
In most real use cases, however, `grid` will be a grid specification like rectilinear or unstructured grids.
See chapter [Data types](data_metadata) for more details.

In the last line, we call `create_connector()`, which sets up an internal helper that manages the initial exchange of data and metadata.
For details and possible arguments, see chapter [The Connect Phase &trade;](./connect_phase).

## Connect and validate

For the coupling to work, it is necessary that every component populates its outputs with initial values.
This is done in `_connect()`.

After this connection phase, models can validate their state in `_validate()`. We do nothing there.

```python
# imports...


class DummyModel(fm.TimeComponent):

    def __init__(self, step):
        # ...

    def _initialize(self):
        # ...

    def _connect(self):                                                      # <--
        self.try_connect(time=self.time, push_data={"Sum": 0})               # <--

    def _validate(self):                                                     # <--
        pass                                                                 # <--
```

In `_connect()`, we call `try_connect` with the component's time (it's starting time),
and a dictionary of data to push for each input.
For more complex use cases like pulling data, see chapter [The Connect Phase &trade;](./connect_phase).

For the tests, we need to set up a real coupling from here on, as the component's inputs require connections in this phase.

```python
class TestDummy(unittest.TestCase):
    def test_dummy_model(self):
        # our model
        model = DummyModel(start=datetime(2000, 1, 1),
                           step=timedelta(days=7))

        # a component to produce inputs, details not important
        generator = fm.modules.generators.CallbackGenerator(
            callbacks={
                "A": (lambda t: t.day, fm.Info(grid=fm.NoGrid())),
                "B": (lambda t: t.day * 2, fm.Info(grid=fm.NoGrid()))
            },
            start=datetime(2000, 1, 1),
            step=timedelta(days=7)
        )

        # a component to consume output, details not important
        consumer = fm.modules.debug.DebugConsumer(
            inputs={"Sum": fm.Info(grid=fm.NoGrid())},
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
```

Here, we set up a complete coupling using a `CallbackGenerator` as source.
A `DebugConsumer` is used as a sink to force the data flow and to allow us to inspect the result.

## Update

Method `_update()` is where the actual work happens.
It is called every time the [scheduler](../principles/coupling_scheduling) decides that the component is on turn to make an update.

In `_update`, we get the component's input data, do a "model step", increment the time, and push results to the output slot.

```python
# imports...


class DummyModel(fm.TimeComponent):

    def __init__(self, step):
        # ...

    def _initialize(self):
        # ...

    def _connect(self):
        # ...

    def _validate(self):
        # ...

    def _update(self):
        a = self.inputs["A"].pull_data(self.time)
        b = self.inputs["B"].pull_data(self.time)

        result = a + b

        # We need to unwrap the data here, as the push time will not equal the pull time.
        # This would result in conflicting timestamps in the internal checks
        result = fm.data.strip_data(result)

        self._time += self._step

        self.outputs["Sum"].push_data(result, self.time)


class TestDummy(unittest.TestCase):
    def test_dummy_model(self):
        # ...

        composition.run(t_max=datetime(2000, 12, 31))
```

The test should fail, as we still need to implement the `_finalize()` method.

## Finalize

In method `_finalize`, the component can do any cleanup required at the end of the coupled run, like closing streams or writing final output data to disk.

We do nothing special here.

```python
# imports...


class DummyModel(TimeComponent):

    def __init__(self, step):
        # ...

    def _initialize(self):
        # ...

    def _connect(self):
        # ...

    def _validate(self):
        # ...

    def _update(self):
        # ...

    def _finalize(self):
        pass
```

## Final code

Here is the final code of the completed component.

```python
import unittest
from datetime import datetime, timedelta

import finam as fm


class DummyModel(fm.TimeComponent):
    def __init__(self, start, step):  # <--
        super().__init__()
        self._step = step  # <--
        self.time = start

    def _initialize(self):  # <--
        self.inputs.add(name="A", grid=fm.NoGrid())  # <--
        self.inputs.add(name="B", grid=fm.NoGrid())  # <--
        self.outputs.add(name="Sum", grid=fm.NoGrid())  # <--

        self.create_connector()  # <--

    def _connect(self):  # <--
        self.try_connect(time=self.time, push_data={"Sum": 0})  # <--

    def _validate(self):  # <--
        pass

    def _update(self):
        a = self.inputs["A"].pull_data(self.time)
        b = self.inputs["B"].pull_data(self.time)

        result = a + b

        # We need to unwrap the data here, as the push time will not equal the pull time.
        # This would result in conflicting timestamps in the internal checks
        result = fm.data.strip_data(result)

        self._time += self._step

        self.outputs["Sum"].push_data(result, self.time)

    def _finalize(self):
        pass


class TestDummy(unittest.TestCase):
    def test_dummy_model(self):
        model = DummyModel(start=datetime(2000, 1, 1), step=timedelta(days=7))
        generator = fm.modules.generators.CallbackGenerator(
            callbacks={
                "A": (lambda t: t.day, fm.Info(grid=fm.NoGrid())),
                "B": (lambda t: t.day * 2, fm.Info(grid=fm.NoGrid())),
            },
            start=datetime(2000, 1, 1),
            step=timedelta(days=7),
        )
        consumer = fm.modules.debug.DebugConsumer(
            inputs={"Sum": fm.Info(grid=fm.NoGrid())},
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

        composition.run(t_max=datetime(2000, 12, 31))
```
