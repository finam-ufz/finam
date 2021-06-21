import random

from core.sdk import AModelComponent, Output
from core.interfaces import ComponentStatus


class CallbackGenerator(AModelComponent):
    def __init__(self, callbacks, step):
        super(CallbackGenerator, self).__init__()
        self._callbacks = callbacks
        self._step = step
        self._time = 0
        self._status = ComponentStatus.CREATED

    def initialize(self):
        for key, _ in self._callbacks.items():
            self._outputs[key] = Output()
        self._status = ComponentStatus.INITIALIZED

    def validate(self):
        for key, callback in self._callbacks.items():
            self._outputs[key].push_data(callback(self._time), self.time())

        self._status = ComponentStatus.VALIDATED

    def update(self):
        self._time += self._step

        for key, callback in self._callbacks.items():
            self._outputs[key].push_data(callback(self._time), self.time())

        self._status = ComponentStatus.UPDATED

    def finalize(self):
        self._status = ComponentStatus.FINALIZED

    def time(self):
        return self._time

    def status(self):
        return self._status
