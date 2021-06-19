from sdk import AModelComponent, AInput
from interfaces import ComponentStatus


class CsvPrinter(AModelComponent):
    def __init__(self, step, inputs):
        super(CsvPrinter, self).__init__()
        self._time = 0
        self._step = step

        self._input_names = inputs
        self._inputs = {inp: AInput(inp) for inp in inputs}

        print(";".join(["time"] + self._input_names))

        self._status = ComponentStatus.CREATED

    def initialize(self):
        self._status = ComponentStatus.INITIALIZED

    def validate(self):
        self._status = ComponentStatus.VALIDATED

    def update(self):
        values = [self._inputs[inp].pull_data(self.time()) for inp in self._input_names]

        print(";".join(map(str, [self.time()] + values)))

        self._time += self._step

        self._status = ComponentStatus.UPDATED

    def finalize(self):
        self._status = ComponentStatus.FINALIZED

    def time(self):
        return self._time

    def status(self):
        return self._status
