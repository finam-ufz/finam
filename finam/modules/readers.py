"""
Modules for reading data.
"""
import pandas
from core.interfaces import ComponentStatus
from core.sdk import ATimeComponent, Output


class CsvReader(ATimeComponent):
    """
    Reads CSV time series with one row per time step, and emits values based on a time column.

    .. code-block:: text

        +-----------+
        |           | [custom] -->
        | CsvReader | [custom] -->
        |           | [......] -->
        +-----------+

    :param path: CSV file path
    :param time_column: Time column name
    :param outputs: Column names that will become available as outputs for coupling
    """

    def __init__(self, path, time_column, outputs):
        """
        Create a new CsvReader.
        """
        super(CsvReader, self).__init__()
        self._path = path
        self._time = 0
        self._time_column = time_column
        self._data = None
        self._row_index = 0

        self._output_names = outputs
        self._outputs = {o: Output() for o in outputs}

        self._status = ComponentStatus.CREATED

    def initialize(self):
        super().initialize()

        import pandas

        self._data = pandas.read_csv(self._path, sep=";")

        self._status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()

        self._push_row(self._data.iloc[self._row_index])
        self._row_index += 1

        self._status = ComponentStatus.CONNECTED

    def validate(self):
        super().validate()

        self._status = ComponentStatus.VALIDATED

    def update(self):
        super().update()

        self._time = self._push_row(self._data.iloc[self._row_index])
        self._row_index += 1

        if self._row_index >= self._data.shape[0]:
            self._status = ComponentStatus.FINISHED
        else:
            self._status = ComponentStatus.UPDATED

    def finalize(self):
        super().finalize()

        self._status = ComponentStatus.FINALIZED

    def _push_row(self, row):
        time = row[self._time_column]
        for o in self._output_names:
            self._outputs[o].push_data(row[o], time)
        return time
