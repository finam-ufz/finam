import random

from adapters import time, base
from core.schedule import Composition
from models import formind, ogs, mhm
from modules import csv_writer, generators, grid_view
from data.grid import Grid, GridSpec

"""
Coupling flow chart:

+-----------------+
| Random grid 50d |
+-----------------+
     (grid)
        |
      <Lin>
        |
        V
+-----------------+
| Live viewer 1d  |
+-----------------+
"""
if __name__ == "__main__":

    def generate_grid(t):
        grid = Grid(GridSpec(100, 100))

        for i in range(len(grid.data)):
            grid.data[i] = random.uniform(0, 1)

        return grid

    generator = generators.CallbackGenerator({"Grid": generate_grid}, step=50)
    viewer = grid_view.GridView(step=1)

    modules = [generator, viewer]

    for m in modules:
        m.initialize()

    (
        generator.outputs()["Grid"]
        >> time.LinearInterpolation()
        >> viewer.inputs()["Grid"]
    )

    composition = Composition(modules)
    composition.run(1000)
