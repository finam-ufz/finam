# Writing adapters

This chapter provides a step-by-step guide to implement adapters in pure Python.
For writing Python bindings for other languages, see [Python bindings](./py-bindings).

Completing the chapter will result in two adapters called `Scale` and `TimeInterpolation`.
We will build up the adapters step by step, accompanied by some test code.

It is assumed that you have FINAM [installed](../usage/installation), as well as [`pytest`](https://docs.pytest.org/en/6.2.x/).

## Set up a Python project

Create the following project structure:

```
- dummy_adapters/
   +- src/
```

## Simple `Scale` adapter

This is a simple, purely pull-based adapter.
When output is requested, it should simply pull from its input, transform and forward it.

We implement `Adapter` and only need to overwrite its method `get_data(self, time)`,
which is called from downstream to request data.

File `src/scale.py`:

```python
import finam as fm


class Scale(fm.Adapter):
    def __init__(self, scale):
        super().__init__()
        self.scale = scale

    def _get_data(self, time):
        d = self.pull_data(time)
        return d * self.scale
```

In `_get_data(self, time)`, we:

1. Pull the input for the requested `time`
1. Multiply the input by `scale` and return the result

## Time-dependent `TimeInterpolation` adapter

The purpose of this adapter is to do temporal interpolation between upstream time steps.
As an example, there could be a model with a weekly time step that passes data to another model with a daily time step.
Assuming continuous transitions of the modelled data, temporal interpolation between the weekly time steps is required.

```
  ^                          V
  |                        _.o----
  |                    _.-´
  |                _.-´|
  |            _.-´    |
  |      V _.-´        |
  |  ----o´            |
  +-------------------------------------> t
                       ^
```

Here, a simple pull-based mechanism is not sufficient.
The adapter needs to store each new data entry that becomes available, and calculate the interpolated data when requested.

Due to FINAM's scheduling algorithm, it is guaranteed that the time stamp of any request lies in the interval of the previous two time steps of any other component
(see [Coubling and Scheduling](../principles/coupling_scheduling) for details).
Thus, it is not required to store data for more than two time stamps.

Accordingly, this is the constructor (file `src/time_interpolation.py`):

```python
import finam as fm

class TimeInterpolation(fm.Adapter):

    def __init__(self):
        super().__init__()
        self.old_data = None
        self.new_data = None
```

The adapter needs to react to downstream requests as well as to new data available upstream.
This functionality is provided by `Adapter`'s methods `_get_data(self, time)` and `_source_updated(self, time)`, respectively.

```python
import finam as fm

class TimeInterpolation(fm.Adapter):

    def __init__(self):
        super().__init__()
        self.old_data = None
        self.new_data = None

    def _source_updated(self, time):
        pass

    def _get_data(self, time):
        pass
```

In `_source_updated(...)`, we need to store incoming data:

```python
import finam as fm

class TimeInterpolation(fm.Adapter):

    def __init__(self):
        super().__init__()
        self.old_data = None
        self.new_data = None

    def _source_updated(self, time):
        self.old_data = self.new_data
        self.new_data = (time, fm.data.strip_data(self.pull_data(time)))

    def _get_data(self, time):
        pass
```

We "move" the previous `new_data` to `old_data`, and replace `new_data` by the incoming data, as a `(time, data)` tuple.
As the output time will differ from the input time, we need to strip the time off the data by calling `strip_data(data)`.

In `_get_data(...)`, we can now do the interpolation whenever data is requested from upstream.

```python
import finam as fm

class TimeInterpolation(fm.Adapter):

    def __init__(self):
        super().__init__()
        self.old_data = None
        self.new_data = None

    def _source_updated(self, time):
        self.old_data = self.new_data
        self.new_data = (time, fm.data.strip_data(self.pull_data(time)))

    def _get_data(self, time):
        if self.old_data is None:
            return self.new_data[1]

        dt = (time - self.old_data[0]) / (self.new_data[0] - self.old_data[0])

        o = self.old_data[1]
        n = self.new_data[1]

        return o + dt * (n - o)
```

In `_get_data(...)`, the following happens:

1. If only one data entry was received so far, we can't interpolate and simply return the available data. Otherwise...
1. Calculate `dt` as the relative position of `time` in the available data interval (in range [0, 1])
1. Interpolate and return the data

Note that, although we use `datetime` when calculating `dt`, we get a scalar output.
Due to `dt` being relative, time units cancel out here.