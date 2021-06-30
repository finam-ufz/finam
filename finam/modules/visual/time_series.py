from core.sdk import ATimeComponent, Input
from core.interfaces import ComponentStatus
from data import assert_type


class TimeSeriesView(ATimeComponent):
    """
    Live time series viewer.

    Expects all inputs to be scalar values.

    .. code-block:: text

                     +----------------+
        --> [custom] |                |
        --> [custom] | TimeSeriesView |
        --> [......] |                |
                     +----------------+
    """

    def __init__(self, inputs, intervals=None, step=1, update_interval=1):
        """
        Create a time series viewer.

        :param inputs: List of input names (plot series) that will become available for coupling
        :param intervals: List of interval values to interleave data retrieval of certain inputs.
                          Values are numbers of updates, i.e. whole-numbered factors for ``step``
        :param step: Update/request time step in model time
        :param update_interval: Redraw interval (independent of data retrieval)
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
        super().initialize()

        import matplotlib.pyplot as plt

        self._figure, self._axes = plt.subplots()
        self._figure.show()

        self._status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()

        self._status = ComponentStatus.CONNECTED

    def validate(self):
        super().validate()

        self._status = ComponentStatus.VALIDATED

    def update(self):
        super().update()

        if self._lines is None:
            self._lines = [
                self._axes.plot([], [], label=h)[0] for h in self._input_names
            ]
            self._axes.legend(loc=1)

        for i, inp in enumerate(self._input_names):
            if self._updates % self._intervals[i] == 0:
                value = self._inputs[inp].pull_data(self.time())
                assert_type(self, inp, value, [int, float])

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
        super().finalize()

        self._status = ComponentStatus.FINALIZED
