"""Generator definitions."""

from datetime import datetime, timedelta

from finam.interfaces import ComponentStatus

from ..sdk import TimeComponent
from ..tools.log_helper import ErrorLogger


class CallbackGenerator(TimeComponent):
    """Component to generate data in fixed time intervals from multiple callbacks.

    .. code-block:: text

        +-------------------+
        |                   | [custom] -->
        | CallbackGenerator | [custom] -->
        |                   | [......] -->
        +-------------------+

    Parameters
    ----------
    callbacks : dict of callable
        Dict of tuples (callback, info). ``callback(data, time)`` per output name, returning the generated data.
    start : datetime.datatime
        Starting time.
    step : timedelta
        Time step.
    """

    def __init__(self, callbacks, start, step):
        super().__init__()
        with ErrorLogger(self.logger):
            if not isinstance(start, datetime):
                raise ValueError("Start must be of type datetime")
            if not isinstance(step, timedelta):
                raise ValueError("Step must be of type timedelta")

        self._callbacks = callbacks
        self._step = step
        self._time = start
        self._initial_data = None

    def _initialize(self):
        """Initialize the component.

        After the method call, the component's inputs and outputs must be available,
        and the component should have status INITIALIZED.
        """
        for key, (_, info) in self._callbacks.items():
            self.outputs.add(name=key, info=info)

        self.create_connector()

    def _connect(self):
        """Push initial values to outputs.

        After the method call, the component should have status CONNECTED.
        """
        if self._initial_data is None:
            self._initial_data = {
                key: callback(self._time)
                for key, (callback, _) in self._callbacks.items()
            }

        push_data = {}
        for name, pushed in self.connector.data_pushed.items():
            if not pushed:
                push_data[name] = self._initial_data[name]

        self.try_connect(self._time, push_data=push_data)

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
            self.outputs[key].push_data(callback(self._time), self.time)

    def _finalize(self):
        """Finalize and clean up the component.

        After the method call, the component should have status FINALIZED.
        """
