from datetime import datetime, timedelta

from ..core.interfaces import ComponentStatus
from ..core.sdk import ATimeComponent, Output


class CallbackGenerator(ATimeComponent):
    """
    Module to generate data in fixed time intervals from multiple callbacks.

    .. code-block:: text

        +-------------------+
        |                   | [custom] -->
        | CallbackGenerator | [custom] -->
        |                   | [......] -->
        +-------------------+

    :param callbacks: A dictionary of callbacks.
                      Keys are output name strings, values are callbacks ``callback(time)``.
                      E.g. ``callbacks={"Time": lambda t: t}``.
    :param step: Step size for data generation.
    """

    def __init__(self, callbacks, start, step):
        """
        Create a new CallbackGenerator.
        """
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
        super().initialize()

        for key, _ in self._callbacks.items():
            self._outputs[key] = Output()

        self._status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()

        for key, callback in self._callbacks.items():
            self._outputs[key].push_data(callback(self._time), self.time)

        self._status = ComponentStatus.CONNECTED

    def validate(self):
        super().validate()

        self._status = ComponentStatus.VALIDATED

    def update(self):
        super().update()

        self._time += self._step

        for key, callback in self._callbacks.items():
            self._outputs[key].push_data(callback(self._time), self.time)

        self._status = ComponentStatus.UPDATED

    def finalize(self):
        super().finalize()

        self._status = ComponentStatus.FINALIZED
