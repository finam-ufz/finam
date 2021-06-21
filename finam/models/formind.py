import math

from core.sdk import AModelComponent, Input, Output
from core.interfaces import ComponentStatus


class Formind(AModelComponent):
    def __init__(self, step):
        super(Formind, self).__init__()
        self._time = 0
        self._step = step
        self.lai = 1.0
        self._status = ComponentStatus.CREATED

    def initialize(self):
        self._inputs["soil_moisture"] = Input()
        self._outputs["LAI"] = Output()
        self._status = ComponentStatus.INITIALIZED

    def validate(self):
        self._outputs["LAI"].push_data(self.lai, self.time())
        self._status = ComponentStatus.VALIDATED

    def update(self):
        soil_moisture = self._inputs["soil_moisture"].pull_data(self.time())

        # Run the model step here
        growth = 1.0 - math.exp(-0.1 * soil_moisture)
        self.lai = (self.lai + growth) * 0.6

        self._time += self._step

        self._outputs["LAI"].push_data(self.lai, self.time())

        self._status = ComponentStatus.UPDATED

    def finalize(self):
        self._status = ComponentStatus.FINALIZED

    def time(self):
        return self._time

    def status(self):
        return self._status
