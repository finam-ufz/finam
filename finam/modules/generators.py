from core.sdk import ATimeComponent, Output
from core.interfaces import ComponentStatus


class CallbackGenerator(ATimeComponent):
    """
    Module to generate data in fixed time intervals from a callback.
    """

    def __init__(self, callbacks, step):
        """
        Create a new CallbackGenerator.

        :param callbacks: A dictionary of callback.
                          Keys are output name string, values are callbacks ``callback(time)``.
                          E.g. ``callbacks={"Time": lambda t: t}``.
        :param step: Step size for data generation.
        """
        super(CallbackGenerator, self).__init__()
        self._callbacks = callbacks
        self._step = step
        self._time = 0
        self._status = ComponentStatus.CREATED

    def initialize(self):
        super().initialize()

        for key, _ in self._callbacks.items():
            self._outputs[key] = Output()

        self._status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()

        for key, callback in self._callbacks.items():
            self._outputs[key].push_data(callback(self._time), self.time())

        self._status = ComponentStatus.CONNECTED

    def validate(self):
        super().validate()

        self._status = ComponentStatus.VALIDATED

    def update(self):
        super().update()

        self._time += self._step

        for key, callback in self._callbacks.items():
            self._outputs[key].push_data(callback(self._time), self.time())

        self._status = ComponentStatus.UPDATED

    def finalize(self):
        super().finalize()

        self._status = ComponentStatus.FINALIZED
