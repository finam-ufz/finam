from core.sdk import AComponent, ATimeComponent, Input, CallbackInput
from core.interfaces import ComponentStatus
from data import assert_type
from data.grid import Grid


class GridView(AComponent):
    """
    Live grid viewer module, updating on pushed input changes.

    .. code-block:: text

                 +----------+
        --> Grid | GridView |
                 +----------+
    """

    def __init__(self):
        """
        Creates a grid viewer
        """
        super(GridView, self).__init__()
        self._time = 0
        self._image = None
        self._figure = None
        self._text = None
        self._status = ComponentStatus.CREATED

    def initialize(self):
        super().initialize()

        self._inputs["Grid"] = CallbackInput(self.data_changed)

        self._status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()

        self._status = ComponentStatus.CONNECTED

    def validate(self):
        super().validate()

        self.update_plot()

        self._status = ComponentStatus.VALIDATED

    def data_changed(self, caller, time):
        self._time = time
        if (
            self._status == ComponentStatus.VALIDATED
            or self._status == ComponentStatus.UPDATED
        ):
            self.update()

    def update(self):
        super().update()

        self.update_plot()

        self._status = ComponentStatus.UPDATED

    def update_plot(self):
        import matplotlib.pyplot as plt

        grid = self._inputs["Grid"].pull_data(self._time)
        assert_type(self, "Grid", grid, [Grid])

        img = grid.reshape(grid.spec.nrows, grid.spec.ncols)

        if self._image is None:
            self._figure, ax = plt.subplots()
            ax.axis("off")
            self._figure.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.06)
            self._figure.show()

            self._image = ax.imshow(img)
            self._text = ax.text(5, 5, f"T: {self._time}", transform=None, fontsize=14)
        else:
            self._image.set_data(img)
            self._text.set_text(f"T: {self._time}")

        self._figure.canvas.draw()
        self._figure.canvas.flush_events()

    def finalize(self):
        super().finalize()

        self._status = ComponentStatus.FINALIZED


class TimedGridView(ATimeComponent, GridView):
    """
    Live grid viewer module, updating in regular intervals.

    .. code-block:: text

                 +---------------+
        --> Grid | TimedGridView |
                 +---------------+
    """

    def __init__(self, step=1):
        """
        Creates a grid viewer

        :param step: Update/request time step in model time
        """
        super(TimedGridView, self).__init__()
        self._step = step

    def initialize(self):
        super().initialize()

        self._inputs["Grid"] = Input()

    def update(self):
        super().update()

        self._time += self._step
