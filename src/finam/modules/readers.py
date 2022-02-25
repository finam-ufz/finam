"""
Modules for reading data.
"""
# pylint: disable=E1101
from datetime import datetime

from ..core.interfaces import ComponentStatus
from ..core.sdk import ATimeComponent, Output


class CsvReader(ATimeComponent):
    """Reads CSV time series with one row per time step, and emits values based on a time column.

    .. code-block:: text

        +-----------+
        |           | [custom] -->
        | CsvReader | [custom] -->
        |           | [......] -->
        +-----------+

    Parameters
    ----------
    path : PathLike
        Path to the input file.
    time_column
        Time column selector.
    outputs : list of str
        Output names.
    date_format : optional
        Format specifier for date.
    """

    def __init__(self, path, time_column, outputs, date_format=None):
        super().__init__()
        self._path = path
        self._time = None
        self._time_column = time_column
        self._date_format = date_format
        self._data = None
        self._row_index = 0

        self._output_names = outputs
        self._outputs = {o: Output() for o in outputs}

        self._status = ComponentStatus.CREATED

    def initialize(self):
        """Initialize the component.

        After the method call, the component's inputs and outputs must be available,
        and the component should have status INITIALIZED.
        """
        super().initialize()

        import pandas

        self._data = pandas.read_csv(self._path, sep=";")

        self._status = ComponentStatus.INITIALIZED

    def connect(self):
        """Push initial values to outputs.

        After the method call, the component should have status CONNECTED.
        """
        super().connect()

        self._time = self._push_row(self._data.iloc[self._row_index])
        self._row_index += 1

        self._status = ComponentStatus.CONNECTED

    def validate(self):
        """Validate the correctness of the component's settings and coupling.

        After the method call, the component should have status VALIDATED.
        """
        super().validate()

        self._status = ComponentStatus.VALIDATED

    def update(self):
        """Update the component by one time step.
        Push new values to outputs.

        After the method call, the component should have status UPDATED or FINISHED.
        """
        super().update()

        self._time = self._push_row(self._data.iloc[self._row_index])
        self._row_index += 1

        if self._row_index >= self._data.shape[0]:
            self._status = ComponentStatus.FINISHED
        else:
            self._status = ComponentStatus.UPDATED

    def finalize(self):
        """Finalize and clean up the component.

        After the method call, the component should have status FINALIZED.
        """
        super().finalize()

        self._status = ComponentStatus.FINALIZED

    def _push_row(self, row):
        if self._date_format is None:
            time = datetime.fromisoformat(row[self._time_column])
        else:
            time = datetime.strptime(row[self._time_column], self._date_format)

        for o in self._output_names:
            self._outputs[o].push_data(row[o], time)

        return time
