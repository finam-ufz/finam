import math

from sdk import AModelComponent, Input, Output
from interfaces import ComponentStatus


class Mhm(AModelComponent):
    def __init__(self, step):
        super(Mhm, self).__init__()
        self._time = 0
        self._step = step
        self.soil_moisture = 1.0
        self._status = ComponentStatus.CREATED

    def initialize(self):
        self._inputs["precipitation"] = Input()
        self._inputs["LAI"] = Input()
        self._outputs["soil_moisture"] = Output()
        self._outputs["base_flow"] = Output()
        self._status = ComponentStatus.INITIALIZED

    def validate(self):
        self._outputs["soil_moisture"].push_data(self.soil_moisture, self.time())
        self._outputs["base_flow"].push_data(0.0, self.time())
        self._status = ComponentStatus.VALIDATED

    def update(self):
        precipitation = self._inputs["precipitation"].pull_data(self.time())
        lai = self._inputs["LAI"].pull_data(self.time())

        # Run the model step here
        self.soil_moisture += precipitation
        base_flow = 0.1 * self.soil_moisture
        evaporation = 0.5 * (1.0 - math.exp(-0.2 * self.soil_moisture))
        self.soil_moisture -= base_flow + evaporation

        self._time += self._step

        self._outputs["soil_moisture"].push_data(self.soil_moisture, self.time())
        self._outputs["base_flow"].push_data(base_flow, self.time())

        self._status = ComponentStatus.UPDATED

    def finalize(self):
        self._status = ComponentStatus.FINALIZED

    def time(self):
        return self._time

    def status(self):
        return self._status
