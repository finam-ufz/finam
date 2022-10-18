"""
Dummy model mimicking Formind.

From an input grid ``soil_water``, it calculates the output grid ``LAI``.

.. code-block:: text

                   +---------+
    --> soil_water | Formind | LAI -->
                   +---------+

For each grid cell, calculations in each model step are as follows:

.. math::

    growth = (1.0 - e^{-0.1 * soil\_moisture}) * U(0.5..1.0)

    LAI(t + \Delta t) = 0.9 * (LAI(t) + growth)
"""
import random
from datetime import datetime, timedelta

import numpy as np

from finam import ATimeComponent, ComponentStatus, Info
from finam import data as tools


class Formind(ATimeComponent):
    def __init__(self, grid, start, step):
        super().__init__()

        if not isinstance(start, datetime):
            raise ValueError("Start must be of type datetime")
        if not isinstance(step, timedelta):
            raise ValueError("Step must be of type timedelta")

        self._time = start
        self._step = step

        self.info = Info(grid)
        self.lai = None

    def _initialize(self):
        self.lai = tools.full(1.0, "LAI", self.info, self.time)

        self.inputs.add(name="soil_water", info=self.info)
        self.outputs.add(name="LAI", info=self.info)

        self.create_connector()

    def _connect(self):
        self.try_connect(time=self.time, push_data={"LAI": self.lai})

    def _validate(self):
        pass

    def _update(self):
        # Retrieve inputs
        soil_water = self.inputs["soil_water"].pull_data(self.time)

        # Run the model step here
        for i in range(len(self.lai.data)):
            growth = (1.0 - np.exp(-0.1 * soil_water.data[i])) * random.uniform(
                0.5, 1.0
            )
            self.lai.data[i] = (self.lai.data[i] + growth) * 0.9

        # Increment model time
        self._time += self._step

        # Push model state to outputs
        self.outputs["LAI"].push_data(self.lai.data, self.time)

    def _finalize(self):
        pass
