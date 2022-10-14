"""
Modules for reading data.
"""
# pylint: disable=E1101
from datetime import datetime

from ..core.interfaces import ComponentStatus
from ..core.sdk import ATimeComponent
from ..data import Info, NoGrid


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

        self.status = ComponentStatus.CREATED

    def _initialize(self):
        """Initialize the component.

        After the method call, the component's inputs and outputs must be available,
        and the component should have status INITIALIZED.
        """
        import pandas
        self._data = pandas.read_csv(self._path, sep=";")
        for name in self._output_names:
            self.outputs.add(name=name, info=Info(grid=NoGrid()))

        self.create_connector()

    def _connect(self):
        """Push initial values to outputs.

        After the method call, the component should have status CONNECTED.
        """
        row = self._data.iloc[self._row_index]
        if self.status == ComponentStatus.INITIALIZED:
            self._time = self._push_row(row, False)
            self._row_index += 1

        if self._date_format is None:
            time = datetime.fromisoformat(row[self._time_column])
        else:
            time = datetime.strptime(row[self._time_column], self._date_format)

        self.try_connect(time=time, push_data={name: row[name] for name in self.outputs})

    def _validate(self):
        """Validate the correctness of the component's settings and coupling.

        After the method call, the component should have status VALIDATED.
        """

    def _update(self):
        """Update the component by one time step.
        Push new values to outputs.

        After the method call, the component should have status UPDATED or FINISHED.
        """
        self._time = self._push_row(self._data.iloc[self._row_index], True)
        self._row_index += 1

        if self._row_index >= self._data.shape[0]:
            self.status = ComponentStatus.FINISHED

    def _finalize(self):
        """Finalize and clean up the component.

        After the method call, the component should have status FINALIZED.
        """

    def _push_row(self, row, push):
        if self._date_format is None:
            time = datetime.fromisoformat(row[self._time_column])
        else:
            time = datetime.strptime(row[self._time_column], self._date_format)

        if push:
            for o in self._output_names:
                self.outputs[o].push_data(row[o], time)

        return time
