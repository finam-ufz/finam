"""Generator definitions."""

from datetime import datetime

from finam.interfaces import ComponentStatus

from ..sdk import Component, TimeComponent
from ..tools.date_helper import is_timedelta


class CallbackGenerator(TimeComponent):
    """Component to generate data in fixed time intervals from multiple callbacks.

    .. code-block:: text

        +-------------------+
        |                   | [custom] -->
        | CallbackGenerator | [custom] -->
        |                   | [......] -->
        +-------------------+

    Examples
    --------

    .. testcode:: constructor

        import datetime as dt
        import finam as fm

        generator = fm.components.CallbackGenerator(
            callbacks={
                "Out1": (lambda t: t.day, fm.Info(time=None, grid=fm.NoGrid())),
                "Out2": (lambda t: t.month, fm.Info(time=None, grid=fm.NoGrid()))
            },
            start=dt.datetime(2000, 1, 1),
            step=dt.timedelta(days=1)
        )

    .. testcode:: constructor
        :hide:

        generator.initialize()

    Parameters
    ----------
    callbacks : dict of (str, tuple(callable, Info))
        Dict of tuples (callback, info). ``callback(time) -> data`` per output name, returning the generated data.
    start : :class:`datetime <datetime.datetime>`
        Starting time.
    step : :class:`timedelta <datetime.timedelta>` or :class:`relativedelta <dateutil.relativedelta.relativedelta>`
        Time step.
    """

    def __init__(self, callbacks, start, step):
        super().__init__()

        if not isinstance(start, datetime):
            raise ValueError("Start must be of type datetime")
        if not is_timedelta(step):
            raise ValueError("Step must be of type timedelta or relativedelta")

        self._callbacks = callbacks
        self._step = step
        self._time = start
        self._initial_data = None

    def _next_time(self):
        return None

    def _initialize(self):
        """Initialize the component.

        After the method call, the component's inputs and outputs must be available,
        and the component should have status INITIALIZED.
        """
        for key, (_, info) in self._callbacks.items():
            info.time = self.time
            self.outputs.add(name=key, info=info)

        self.create_connector()

    def _connect(self, start_time):
        """Push initial values to outputs.

        After the method call, the component should have status CONNECTED.
        """
        if self._initial_data is None:
            self._initial_data = {
                key: callback(self._time)
                for key, (callback, _) in self._callbacks.items()
            }

        push_data = {}
        for name, req in self.connector.data_required.items():
            if req:
                push_data[name] = self._initial_data[name]

        self.try_connect(start_time, push_data=push_data)

        if self.status == ComponentStatus.CONNECTED:
            del self._initial_data
            del self._connector

    def _validate(self):
        """Validate the correctness of the component's settings and coupling.

        After the method call, the component should have status VALIDATED.
        """

    def _update(self):
        """Update the component by one time step.
        Push new values to outputs.

        After the method call, the component should have status UPDATED or FINISHED.
        """
        self._time += self._step

        for key, (callback, _) in self._callbacks.items():
            data = callback(self._time)
            if data is not None:
                self.outputs[key].push_data(data, self.time)

    def _finalize(self):
        """Finalize and clean up the component.

        After the method call, the component should have status FINALIZED.
        """


class StaticCallbackGenerator(Component):
    """Component to generate static data from multiple callbacks.

    .. code-block:: text

        +-------------------------+
        |                         | [custom] -->
        | StaticCallbackGenerator | [custom] -->
        |                         | [......] -->
        +-------------------------+

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        generator = fm.components.StaticCallbackGenerator(
            callbacks={
                "Out1": (lambda: 1.0, fm.Info(time=None, grid=fm.NoGrid())),
                "Out2": (lambda: 2.0, fm.Info(time=None, grid=fm.NoGrid()))
            },
        )

    .. testcode:: constructor
        :hide:

        generator.initialize()

    Parameters
    ----------
    callbacks : dict of (str, tuple(callable, Info))
        Dict of tuples (callback, info). ``callback() -> data`` per output name, returning the generated data.
    """

    def __init__(self, callbacks):
        super().__init__()
        self._callbacks = callbacks
        self._initial_data = None

    def _initialize(self):
        """Initialize the component.

        After the method call, the component's inputs and outputs must be available,
        and the component should have status INITIALIZED.
        """
        for key, (_, info) in self._callbacks.items():
            self.outputs.add(name=key, info=info, static=True)

        self.create_connector()

    def _connect(self, start_time):
        """Push initial values to outputs.

        After the method call, the component should have status CONNECTED.
        """
        if self._initial_data is None:
            self._initial_data = {
                key: callback() for key, (callback, _) in self._callbacks.items()
            }

        push_data = {}
        for name, pushed in self.connector.data_pushed.items():
            if not pushed:
                push_data[name] = self._initial_data[name]

        self.try_connect(start_time, push_data=push_data)

        if self.status == ComponentStatus.CONNECTED:
            del self._initial_data
            del self._connector

    def _validate(self):
        """Validate the correctness of the component's settings and coupling.

        After the method call, the component should have status VALIDATED.
        """

    def _update(self):
        """Update the component by one time step.
        Push new values to outputs.

        After the method call, the component should have status UPDATED or FINISHED.
        """

    def _finalize(self):
        """Finalize and clean up the component.

        After the method call, the component should have status FINALIZED.
        """
