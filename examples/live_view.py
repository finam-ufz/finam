"""
Simple coupling setup demonstrating temporal integration using live view modules.

Coupling flow chart:

.. code-block:: text

    +-----------------+                ,--<Lin>---- 1d -> +-----------------+
    | Random grid 10d | (grid) -- <G2V>                   | Plot viewer 1d  |
    +-----------------+       \        `--<Mean>-- 50d -> +-----------------+
                               \ 
                                \                 +-----------------+
                                 '-- <Lin> -----> | Grid viewer 1d  |
                                                  +-----------------+
"""

import random
import numpy as np

from finam.adapters import time, base
from finam.core.schedule import Composition
from finam.modules import generators
from finam.modules.visual import grid, time_series
from finam.data.grid import Grid, GridSpec

if __name__ == "__main__":

    def generate_grid(t):
        grid = Grid(GridSpec(50, 50))

        for i in range(len(grid.data)):
            grid.data[i] = random.uniform(0, 1) + i / float(50 * 50)

        return grid

    generator = generators.CallbackGenerator({"Grid": generate_grid}, step=10)
    viewer = grid.TimedGridView()
    plot = time_series.TimeSeriesView(
        inputs=["Linear (1)", "Mean (50)"], intervals=[1, 50]
    )

    composition = Composition([generator, viewer, plot])
    composition.initialize()

    (
        generator.outputs()["Grid"]
        >> time.LinearInterpolation()
        >> viewer.inputs()["Grid"]
    )

    grid_mean = generator.outputs()["Grid"] >> base.GridToValue(func=np.mean)

    grid_mean >> time.LinearInterpolation() >> plot.inputs()["Linear (1)"]
    grid_mean >> time.LinearIntegration.mean() >> plot.inputs()["Mean (50)"]

    composition.run(1000)