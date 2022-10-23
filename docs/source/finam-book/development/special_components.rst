============================
Components without time step
============================

So far, we mainly dealt with components that have an internal time step.
In some cases, however, components without an internal time step can be useful.
Instead of being updated by the scheduler, they can react to push or pull events from other, linked components.

An example for a push-based component is a file writer that writes data for a time step when it receives some new input.
Another example is a map visualization that updates when revieving new data.

An example for a pull-based component could be a generator, or a statistical model, that needs to do calculations only when pulled.

Components without a time step must implement `IComponent`.
Developers can derive from the abstract implementation `Component`.
(In contrast to `ITimeComponent`/`TimeComponent`)

Components without a time step usually use `CallbackInput` or `CallbackOutput`
for push-based and pull-based, respectively.

**Before starting this chapter**, it is highly recommended to complete chapter [Writing components](./components) first.

## Push-based components

Push-based components can use `CallbackInput` to get informed about incoming data.

```python
import finam as fm

class PushComponent(fm.Component):
    def __init__(self):
        super().__init__()
        self.data = []

    def _initialize(self):
        self.inputs.add(
            fm.CallbackInput(
                callback=self._data_changed, name="In", grid=fm.NoGrid()
            )
        )
        self.create_connector()

    def _data_changed(self, caller, time):
        data = caller.pull_data(time)
        self.data.append((time, data))

    def _connect(self):
        self.try_connect()

    def _validate(self):
        pass

    def _update(self):
        pass

    def _finalize(self):
        write_to_file(self.data)
```

In `_initialize()`, a `CallbackInput` is added that calls `_data_changed()` when notified about new data.

In `_data_changed()`, the data from the calling input is pulled, and stored for later writing to file.
In `_finalize()`, the collected data is written to a file.

Be aware that the callback is already called once during [The Connect Phase &trade;](./connect_phase).

With multiple inputs, it may be necessary to check that notifications for all of them are synchronized in time,
depending on the particular purpose of the component.
This might e.g. be the case when inputs are columns in an output table, with a complete row per time step.

## Pull-based components

Push-based components can use `CallbackOutput` to intercept data pulls.

```python
import finam as fm

class PullComponent(fm.Component):
    def __init__(self):
        super().__init__()

    def _initialize(self):
        self.outputs.add(
            fm.CallbackOutput(
                callback=self._get_data, name="Out", grid=fm.NoGrid()
            )
        )
        self.create_connector()

    def _get_data(self, _caller, time):
        return time.day

    def _connect(self):
        self.try_connect()

    def _validate(self):
        pass

    def _update(self):
        pass

    def _finalize(self):
        pass
```

In `_initialize()`, a `CallbackOutput` is added that calls `_get_data()` when pulled.
`_get_data()` must return the data that would normally be pushed to the output.

Here, simply the day of month of the request data is returned.

Be aware that the callback is already called once during [The Connect Phase &trade;](./connect_phase).
This can happen multiple times if it returned `None` to indicate that no data is available yet.

Also note that the outputs of pull-based components can't be connected to time-interpolating adapters,
as they rely on being notified by push events.
