from core.sdk import AModelComponent, Input
from core.interfaces import ComponentStatus


class TimeSeriesView(AModelComponent):
    """
    Live time series viewer.
    """

    def __init__(self, inputs, intervals=None, step=1, update_interval=1):
        """
        Create a time series viewer.

        :param inputs: List of input names that will become available for coupling
        :param intervals: List of interval values to interleave data retrieval of certain inputs.
                          Values are numbers of updates, i.e. a whole-numbered factor for ``step``
        :param step: Update/request time step in model time
        :param update_interval: Redraw interval (independent of data recording)
        """
        super(TimeSeriesView, self).__init__()
        self._step = step
        self._update_interval = update_interval
        self._intervals = intervals if intervals else [1 for _ in inputs]
        self._time = 0
        self._updates = 0
        self._figure = None
        self._axes = None
        self._data = [[] for _ in inputs]
        self._x = [[] for _ in inputs]
        self._lines = None

        self._input_names = inputs
        self._inputs = {inp: Input() for inp in inputs}

        self._status = ComponentStatus.CREATED

    def initialize(self):
        import matplotlib.pyplot as plt

        self._figure, self._axes = plt.subplots()
        self._figure.show()

        self._status = ComponentStatus.INITIALIZED

    def validate(self):
        self._status = ComponentStatus.VALIDATED

    def update(self):
        if self._lines is None:
            self._lines = [
                self._axes.plot([], [], label=h)[0] for h in self._input_names
            ]
            self._axes.legend(loc=1)

        for i, inp in enumerate(self._input_names):
            if self._updates % self._intervals[i] == 0:
                value = self._inputs[inp].pull_data(self.time())
                if not (isinstance(value, int) or isinstance(value, float)):
                    raise Exception(
                        f"Unsupported data type in TimeSeriesView: {value.__class__.__name__}"
                    )
                self._x[i].append(self.time())
                self._data[i].append(value)

        if self._updates % self._update_interval == 0:
            for i, line in enumerate(self._lines):
                line.set_xdata(self._x[i])
                line.set_ydata(self._data[i])

            self._axes.relim()
            self._axes.autoscale_view(True, True, True)

            self._figure.canvas.draw()
            self._figure.canvas.flush_events()

        self._time += self._step
        self._updates += 1

        self._status = ComponentStatus.UPDATED

    def finalize(self):
        self._status = ComponentStatus.FINALIZED

    def time(self):
        return self._time

    def status(self):
        return self._status
