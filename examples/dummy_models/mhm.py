"""
Dummy model mimicking mHM.

From an input scalar ``precipitation`` and an input grid ``LAI``,
it calculates the output grid ``soil_water`` and output scalars ``base_flow`` and ``ETP``.

.. code-block:: text

                      +---------+
    --> precipitation |         | soil_water -->
                      |   mHM   | GW_recharge -->
              --> LAI |         | ETP -->
                      +---------+

For each grid cell, calculations in each model step are as follows:

.. math::

    sm_{temp} = soil\_moisture(t) + precipitation

    gwr = 0.1 * sm_{temp}

    etp = 0.5 * sm_{temp} * (1.0 - e^{-0.05 * LAI})

    soil\_moisture(t + \Delta t) = sm_{temp} - (gwr + etp)

Output ``ETP`` is the average of ``etp`` over all cells. ``GW_recharge`` is the sum of ``gwr`` over all cells.
"""

import math
from datetime import datetime, timedelta

from finam.core.interfaces import ComponentStatus
from finam.core.sdk import ATimeComponent, Input, Output
from finam.data import assert_type
from finam.data.grid import Grid


class Mhm(ATimeComponent):
    def __init__(self, grid_spec, start, step):
        super(Mhm, self).__init__()

        if not isinstance(start, datetime):
            raise ValueError("Start must be of type datetime")
        if not isinstance(step, timedelta):
            raise ValueError("Step must be of type timedelta")

        self._time = start
        self._step = step

        self._grid_spec = grid_spec
        self.soil_water = None

        self._status = ComponentStatus.CREATED

    def initialize(self):
        super().initialize()

        self.soil_water = Grid(self._grid_spec)

        self._inputs["precipitation"] = Input()
        self._inputs["LAI"] = Input()
        self._outputs["soil_water"] = Output()
        self._outputs["GW_recharge"] = Output()
        self._outputs["ETP"] = Output()

        self._status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()

        self._outputs["soil_water"].push_data(self.soil_water, self.time)
        self._outputs["GW_recharge"].push_data(0.0, self.time)
        self._outputs["ETP"].push_data(0.0, self.time)

        self._status = ComponentStatus.CONNECTED

    def validate(self):
        super().validate()

        self._status = ComponentStatus.VALIDATED

    def update(self):
        super().update()

        # Retrieve inputs
        precipitation = self._inputs["precipitation"].pull_data(self.time)
        lai = self._inputs["LAI"].pull_data(self.time)

        # Check input data types
        assert_type(self, "precipitation", precipitation, [int, float])
        assert_type(self, "LAI", lai, [Grid])
        if self.soil_water.spec != lai.spec:
            raise Exception(f"Grid specifications not matching for LAI in mHM.")

        # Run the model step here
        base_flow = 0.0
        total_recharge = 0.0
        mean_evaporation = 0.0
        for i in range(len(self.soil_water.data)):
            sm = self.soil_water.data[i]
            sm += precipitation
            recharge = 0.1 * sm
            evaporation = 0.5 * sm * (1.0 - math.exp(-0.05 * lai.data[i]))
            sm -= recharge + evaporation
            self.soil_water.data[i] = sm

            total_recharge += recharge
            mean_evaporation += evaporation

        mean_evaporation /= float(len(self.soil_water.data))

        # Increment model time
        self._time += self._step
        # Push model state to outputs
        self._outputs["soil_water"].push_data(self.soil_water, self.time)
        self._outputs["GW_recharge"].push_data(total_recharge, self.time)
        self._outputs["ETP"].push_data(mean_evaporation, self.time)

        # Update component status
        self._status = ComponentStatus.UPDATED

    def finalize(self):
        super().finalize()

        self._status = ComponentStatus.FINALIZED

    @property
    def step(self):
        return self._step
