import random

from sdk import AModelComponent, Output
from interfaces import ComponentStatus


class RandomOutput(AModelComponent):
    def __init__(self, step):
        super(RandomOutput, self).__init__()
        self._time = 0
        self._step = step
        self._status = ComponentStatus.CREATED

    def initialize(self):
        self._outputs["Random"] = Output("Random")
        self._status = ComponentStatus.INITIALIZED

    def validate(self):
        self._outputs["Random"].push_data(random.uniform(0, 1), self.time())
        self._status = ComponentStatus.VALIDATED

    def update(self):
        self._time += self._step

        value = random.uniform(0, 1)
        self._outputs["Random"].push_data(value, self.time())

        self._status = ComponentStatus.UPDATED

    def finalize(self):
        self._status = ComponentStatus.FINALIZED

    def time(self):
        return self._time

    def status(self):
        return self._status
