from sdk import AModelComponent, Input, Output
from interfaces import ComponentStatus


class Formind(AModelComponent):
    def __init__(self, step):
        super(Formind, self).__init__()
        self._time = 0
        self._step = step
        self.lai = 0
        self._status = ComponentStatus.CREATED

    def initialize(self):
        self._inputs["soil_moisture"] = Input()
        self._outputs["LAI"] = Output()
        self._status = ComponentStatus.INITIALIZED

    def validate(self):
        self._outputs["LAI"].push_data(0, self.time())
        self._status = ComponentStatus.VALIDATED

    def update(self):
        soil_moisture = self._inputs["soil_moisture"].pull_data(self.time())

        # Run the model step here
        self.lai = (self.lai + soil_moisture) * 0.9

        self._time += self._step

        self._outputs["LAI"].push_data(self.lai, self.time())

        self._status = ComponentStatus.UPDATED

    def finalize(self):
        self._status = ComponentStatus.FINALIZED

    def time(self):
        return self._time

    def status(self):
        return self._status
