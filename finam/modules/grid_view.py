from core.sdk import AModelComponent, Input
from core.interfaces import ComponentStatus
from data.grid import Grid


class GridView(AModelComponent):
    """
    Live grid viewer module.
    """

    def __init__(self, step=1):
        """
        Creates a grid viewer

        :param step: Update/request time step in model time
        """
        super(GridView, self).__init__()
        self._step = step
        self._time = 0
        self._image = None
        self._figure = None
        self._text = None
        self._status = ComponentStatus.CREATED

    def initialize(self):
        self._inputs["Grid"] = Input()

        self._status = ComponentStatus.INITIALIZED

    def validate(self):
        self._status = ComponentStatus.VALIDATED

    def update(self):
        import matplotlib.pyplot as plt

        grid = self._inputs["Grid"].pull_data(self.time())

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
            self._text = ax.text(5, 5, f"T: {self.time()}", transform=None, fontsize=14)
        else:
            self._image.set_data(img)
            self._text.set_text(f"T: {self.time()}")

        self._figure.canvas.draw()
        self._figure.canvas.flush_events()

        self._time += self._step
        self._status = ComponentStatus.UPDATED

    def finalize(self):
        self._status = ComponentStatus.FINALIZED

    def time(self):
        return self._time

    def status(self):
        return self._status
