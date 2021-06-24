"""
Dummy model mimicking Formind.

From an input grid ``soil_moisture``, it calculates the output grid ``LAI``.

For each grid cell, calculations in each model step are as follows:

.. math::

    growth = (1.0 - e^{-0.1 * soil\_moisture}) * U(0.5..1.0)

    LAI(t + \Delta t) = 0.9 * (LAI(t) + growth)
"""

import math
import random

from core.sdk import ATimeComponent, Input, Output
from core.interfaces import ComponentStatus
from data.grid import Grid


class Formind(ATimeComponent):
    def __init__(self, grid_spec, step):
        super(Formind, self).__init__()
        self._time = 0
        self._step = step

        self.lai = Grid(grid_spec)
        self.lai.fill(1.0)

        self._status = ComponentStatus.CREATED

    def initialize(self):
        super().initialize()

        self._inputs["soil_moisture"] = Input()
        self._outputs["LAI"] = Output()

        self._status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()

        self._outputs["LAI"].push_data(self.lai, self.time())

        self._status = ComponentStatus.CONNECTED

    def validate(self):
        super().validate()

        self._status = ComponentStatus.VALIDATED

    def update(self):
        super().update()

        soil_moisture = self._inputs["soil_moisture"].pull_data(self.time())

        if not isinstance(soil_moisture, Grid):
            raise Exception(
                f"Unsupported data type for soil_moisture in Formind: {soil_moisture.__class__.__name__}"
            )

        if self.lai.spec != soil_moisture.spec:
            raise Exception(
                f"Grid specifications not matching for soil_moisture in Formind."
            )

        # Run the model step here
        for i in range(len(self.lai.data)):
            growth = (1.0 - math.exp(-0.1 * soil_moisture.data[i])) * random.uniform(
                0.5, 1.0
            )
            self.lai.data[i] = (self.lai.data[i] + growth) * 0.9

        self._time += self._step

        self._outputs["LAI"].push_data(self.lai, self.time())

        self._status = ComponentStatus.UPDATED

    def finalize(self):
        super().finalize()

        self._status = ComponentStatus.FINALIZED
