"""Generator definitions."""

from datetime import datetime, timedelta

from ..core.interfaces import ComponentStatus
from ..core.sdk import ATimeComponent, Output


class CallbackGenerator(ATimeComponent):
    """Module to generate data in fixed time intervals from multiple callbacks.

    .. code-block:: text

        +-------------------+
        |                   | [custom] -->
        | CallbackGenerator | [custom] -->
        |                   | [......] -->
        +-------------------+

    Parameters
    ----------
    callbacks : list of callable
        List of callbacks ``callback(data, time)``, returning the transformed data.
    start : datetime
        Starting time.
    step : timedelta
        Time step.
    """

    def __init__(self, callbacks, start, step):
        super(CallbackGenerator, self).__init__()

        if not isinstance(start, datetime):
            raise ValueError("Start must be of type datetime")
        if not isinstance(step, timedelta):
            raise ValueError("Step must be of type timedelta")

        self._callbacks = callbacks
        self._step = step
        self._time = start
        self._status = ComponentStatus.CREATED

    def initialize(self):
        """Initialize the component.

        After the method call, the component's inputs and outputs must be available,
        and the component should have status INITIALIZED.
        """
        super().initialize()

        for key, _ in self._callbacks.items():
            self._outputs[key] = Output()

        self._status = ComponentStatus.INITIALIZED

    def connect(self):
        """Push initial values to outputs.

        After the method call, the component should have status CONNECTED.
        """
        super().connect()

        for key, callback in self._callbacks.items():
            self._outputs[key].push_data(callback(self._time), self.time)

        self._status = ComponentStatus.CONNECTED

    def validate(self):
        """Validate the correctness of the component's settings and coupling.

        After the method call, the component should have status VALIDATED.
        """
        super().validate()

        self._status = ComponentStatus.VALIDATED

    def update(self):
        """Update the component by one time step.
        Push new values to outputs.

        After the method call, the component should have status UPDATED or FINISHED.
        """
        super().update()

        self._time += self._step

        for key, callback in self._callbacks.items():
            self._outputs[key].push_data(callback(self._time), self.time)

        self._status = ComponentStatus.UPDATED

    def finalize(self):
        """Finalize and clean up the component.

        After the method call, the component should have status FINALIZED.
        """
        super().finalize()

        self._status = ComponentStatus.FINALIZED
