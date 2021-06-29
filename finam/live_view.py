import random
import numpy as np

from adapters import time, base
from core.schedule import Composition
from modules import generators, grid_view, time_series_view
from data.grid import Grid, GridSpec

"""
Coupling flow chart:

                                    
+-----------------+                ,--<Lin>---- 1d -> +-----------------+
| Random grid 10d | (grid) -- <G2V>                   | Plot viewer 1d  |
+-----------------+       \        `--<Mean>-- 50d -> +-----------------+
                           \
                            \                 +-----------------+
                             '-- <Lin> -----> | Grid viewer 1d  |
                                              +-----------------+
"""
if __name__ == "__main__":

    def generate_grid(t):
        grid = Grid(GridSpec(50, 50))

        for i in range(len(grid.data)):
            grid.data[i] = random.uniform(0, 1) + i / float(50 * 50)

        return grid

    generator = generators.CallbackGenerator({"Grid": generate_grid}, step=10)
    viewer = grid_view.TimedGridView()
    plot = time_series_view.TimeSeriesView(
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
