from core.sdk import AComponent, CallbackInput
from core.interfaces import ComponentStatus
from data.grid import Grid


class GridView(AComponent):
    """
    Live grid viewer module.
    """

    def __init__(self):
        """
        Creates a grid viewer

        :param step: Update/request time step in model time
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

        self._status = ComponentStatus.VALIDATED

    def data_changed(self, time):
        self._time = time
        if (
            self._status == ComponentStatus.VALIDATED
            or self._status == ComponentStatus.UPDATED
        ):
            self.update()

    def update(self):
        super().update()

        import matplotlib.pyplot as plt

        grid = self._inputs["Grid"].pull_data(self._time)

        if not isinstance(grid, Grid):
            raise Exception(
                f"Unsupported data type in GridView: {grid.__class__.__name__}"
            )

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

        self._status = ComponentStatus.UPDATED

    def finalize(self):
        super().finalize()

        self._status = ComponentStatus.FINALIZED
