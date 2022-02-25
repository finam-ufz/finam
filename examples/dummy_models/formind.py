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

import math
import random
from datetime import datetime, timedelta

from finam.core.interfaces import ComponentStatus
from finam.core.sdk import ATimeComponent, Input, Output
from finam.data import assert_type
from finam.data.grid import Grid


class Formind(ATimeComponent):
    def __init__(self, grid_spec, start, step):
        super(Formind, self).__init__()

        if not isinstance(start, datetime):
            raise ValueError("Start must be of type datetime")
        if not isinstance(step, timedelta):
            raise ValueError("Step must be of type timedelta")

        self._time = start
        self._step = step

        self._grid_spec = grid_spec
        self.lai = None

        self._status = ComponentStatus.CREATED

    def initialize(self):
        super().initialize()

        self.lai = Grid(self._grid_spec)
        self.lai.fill(1.0)

        self._inputs["soil_water"] = Input()
        self._outputs["LAI"] = Output()

        self._status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()

        self._outputs["LAI"].push_data(self.lai, self.time)

        self._status = ComponentStatus.CONNECTED

    def validate(self):
        super().validate()

        self._status = ComponentStatus.VALIDATED

    def update(self):
        super().update()

        # Retrieve inputs
        soil_water = self._inputs["soil_water"].pull_data(self.time)

        # Check input data types
        assert_type(self, "soil_water", soil_water, [Grid])
        if self.lai.spec != soil_water.spec:
            raise Exception(
                f"Grid specifications not matching for soil_water in Formind."
            )

        # Run the model step here
        for i in range(len(self.lai.data)):
            growth = (1.0 - math.exp(-0.1 * soil_water.data[i])) * random.uniform(
                0.5, 1.0
            )
            self.lai.data[i] = (self.lai.data[i] + growth) * 0.9

        # Increment model time
        self._time += self._step

        # Push model state to outputs
        self._outputs["LAI"].push_data(self.lai, self.time)

        # Update component status
        self._status = ComponentStatus.UPDATED

    def finalize(self):
        super().finalize()

        self._status = ComponentStatus.FINALIZED
