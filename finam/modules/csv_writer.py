from core.sdk import AModelComponent, Input
from core.interfaces import ComponentStatus


class CsvWriter(AModelComponent):
    """
    Writes CSV time series with one row per time step, from multiple inputs.
    """

    def __init__(self, path, step, inputs):
        """
        Create a new CsvWriter.

        :param path: Output path
        :param step: Step duration
        :param inputs: List of input names that will become available for coupling
        """
        super(CsvWriter, self).__init__()
        self._path = path
        self._time = 0
        self._step = step

        self._input_names = inputs
        self._inputs = {inp: Input() for inp in inputs}

        with open(self._path, "w") as out:
            out.write(";".join(["time"] + self._input_names) + "\n")

        self._status = ComponentStatus.CREATED

    def initialize(self):
        self._status = ComponentStatus.INITIALIZED

    def validate(self):
        self._status = ComponentStatus.VALIDATED

    def update(self):
        values = [self._inputs[inp].pull_data(self.time()) for inp in self._input_names]

        for value in values:
            if not (isinstance(value, int) or isinstance(value, float)):
                raise Exception(
                    f"Unsupported data type in CsvWriter: {value.__class__.__name__}"
                )

        with open(self._path, "a") as out:
            out.write(";".join(map(str, [self.time()] + values)) + "\n")

        self._time += self._step

        self._status = ComponentStatus.UPDATED

    def finalize(self):
        self._status = ComponentStatus.FINALIZED

    def time(self):
        return self._time

    def status(self):
        return self._status
