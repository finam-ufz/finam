"""
Adapters for statistics over grids.
"""
import numpy as np

from ..data import get_magnitude
from ..data.grid_spec import UniformGrid
from ..sdk import Adapter

__all__ = [
    "Histogram",
]


class Histogram(Adapter):
    """Calculates a histogram over grid values.

    Results are returned as a 1-D uniform grid.

    Parameters
    ----------
    lower : float
        Lower bound of the histogram.
    upper : float
        Upper bound of the histogram.
    bins : int, optional
        Number of bins. Default: 10.
    density : bool, optional
        Calculates densities instead of counts. Default: False.

    Returns
    -------

    UniformGrid
        A 1-D grid using :class:`.UniformGrid` as specification.
    """

    def __init__(self, lower, upper, bins=10, density=False):
        super().__init__()
        self.lower = lower
        self.upper = upper
        self.bins = bins
        self.density = density

        step = (upper - lower) / bins
        self.grid = UniformGrid(dims=(bins + 1,), spacing=(step,), origin=(lower,))

    def _get_data(self, time, target):
        d = get_magnitude(self.pull_data(time, target))

        values = np.histogram(
            d, bins=self.bins, range=(self.lower, self.upper), density=self.density
        )
        return values[0]

    def _get_info(self, info):
        info = info.copy_with(grid=None)
        in_info = self.exchange_info(info)
        out_info = in_info.copy_with(grid=self.grid, units="")
        return out_info
