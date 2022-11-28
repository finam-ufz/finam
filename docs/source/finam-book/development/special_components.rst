============================
Components without time step
============================

So far, we mainly dealt with components that have an internal time step.
In some cases, however, components without an internal time step can be useful.
Instead of being updated by the scheduler, they can react to push or pull events from other, linked components.

An example for a push-based component is a file writer that writes data for a time step when it receives some new input.
Another example is a map visualization that updates when revieving new data.

An example for a pull-based component could be a generator, or a statistical model, that needs to do calculations only when pulled.

Components without a time step must implement :class:`.IComponent`.
Developers can derive from the abstract implementation :class:`.Component`.
(In contrast to :class:`.ITimeComponent`/:class:`.TimeComponent`)

Components without a time step usually use :class:`.CallbackInput` or :class:`.CallbackOutput`
for push-based and pull-based, respectively.

**Before starting this chapter**, it is highly recommended to complete chapter :doc:`./components` first.

Push-based components
---------------------

Push-based components can use :class:`.CallbackInput` to get informed about incoming data.

.. testcode:: push-component

    import finam as fm

    class PushComponent(fm.Component):
        def __init__(self):
            super().__init__()
            self.data = []

        def _initialize(self):
            self.inputs.add(
                fm.CallbackInput(
                    callback=self._data_changed,
                    name="Input",
                    time=None,
                    grid=fm.NoGrid(),
                    unit=None,
                )
            )
            self.create_connector()

        def _data_changed(self, caller, time):
            data = caller.pull_data(time)
            self.data.append((time, data))

        def _connect(self, start_time):
            self.try_connect(start_time)

        def _validate(self):
            pass

        def _update(self):
            pass

        def _finalize(self):
            write_to_file(self.data)

.. testcode:: push-component
    :hide:

    from datetime import datetime, timedelta

    def write_to_file(data):
        pass

    generator = fm.modules.CallbackGenerator(
        {"Value": (lambda t: t.day, fm.Info(time=None, grid=fm.NoGrid()))},
        start=datetime(2000, 1, 1),
        step=timedelta(days=30),
    )
    push_comp = PushComponent()

    comp = fm.Composition([generator, push_comp])
    comp.initialize()

    generator.outputs["Value"] >> push_comp.inputs["Input"]

    comp.run(end_time=datetime(2000, 1, 15))


In ``_initialize()``, a :class:`.CallbackInput` is added that calls ``_data_changed()`` when notified about new data.

In ``_data_changed()``, the data from the calling input is pulled, and stored for later writing to file.
In ``_finalize()``, the collected data is written to a file.

Be aware that the callback is already called once during :doc:`./connect_phase`.

With multiple inputs, it may be necessary to check that notifications for all of them are synchronized in time,
depending on the particular purpose of the component.
This might e.g. be the case when inputs are columns in an output table, with a complete row per time step.

Pull-based components
---------------------

Push-based components can use :class:`.CallbackOutput` to intercept data pulls.

.. testcode:: pull-component

    import finam as fm

    class PullComponent(fm.Component):
        def __init__(self):
            super().__init__()

        def _initialize(self):
            self.outputs.add(
                fm.CallbackOutput(
                    callback=self._get_data,
                    time=None,
                    name="Output",
                    grid=fm.NoGrid(),
                )
            )
            self.create_connector()

        def _get_data(self, _caller, time):
            return time.day

        def _connect(self, start_time):
            self.try_connect(start_time)

        def _validate(self):
            pass

        def _update(self):
            pass

        def _finalize(self):
            pass

.. testcode:: pull-component
    :hide:

    from datetime import datetime, timedelta

    pull_comp = PullComponent()

    consumer = fm.modules.DebugConsumer(
        {"Input": fm.Info(time=None, grid=fm.NoGrid())},
        start=datetime(2000, 1, 1),
        step=timedelta(days=1),
    )

    comp = fm.Composition([pull_comp, consumer])
    comp.initialize()

    pull_comp.outputs["Output"] >> consumer.inputs["Input"]

    comp.run(end_time=datetime(2000, 1, 15))

In ``_initialize()``, a :class:`.CallbackOutput` is added that calls ``_get_data()`` when pulled.
``_get_data()`` must return the data that would normally be pushed to the output.

Here, simply the day of month of the request data is returned.

Be aware that the callback is already called once during :doc:`./connect_phase`.
This can happen multiple times if it returned ``None`` to indicate that no data is available yet.

Also note that the outputs of pull-based components can't be connected to time-interpolating adapters,
as they rely on being notified by push events.
