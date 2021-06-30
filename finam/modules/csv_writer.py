import numpy as np

from core.sdk import ATimeComponent, Input
from core.interfaces import ComponentStatus
from data import assert_type


class CsvWriter(ATimeComponent):
    """
    Writes CSV time series with one row per time step, from multiple inputs.

    .. code-block:: text

                     +-----------+
        --> [custom] |           |
        --> [custom] | CsvWriter |
        --> [......] |           |
                     +-----------+
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

        self._rows = []

        self._status = ComponentStatus.CREATED

    def initialize(self):
        super().initialize()

        self._status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()

        self._status = ComponentStatus.CONNECTED

    def validate(self):
        super().validate()

        self._status = ComponentStatus.VALIDATED

    def update(self):
        super().update()

        values = [self._inputs[inp].pull_data(self.time()) for inp in self._input_names]

        for (value, name) in zip(values, self._input_names):
            assert_type(self, name, value, [int, float])

        self._rows.append([self.time()] + values)

        self._time += self._step

        self._status = ComponentStatus.UPDATED

    def finalize(self):
        super().finalize()

        np.savetxt(
            self._path,
            self._rows,
            fmt="%s",
            delimiter=";",
            header=";".join(["time"] + self._input_names),
            comments="",
        )

        self._status = ComponentStatus.FINALIZED
