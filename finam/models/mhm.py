"""
Dummy model mimicking mHM.

From an input scalar ``precipitation`` and an input grid ``LAI``,
it calculates the output grid ``soil_moisture`` and output scalars ``base_flow`` and ``ETP``.

.. code-block:: text

                      +---------+
    --> precipitation |         | soil_moisture -->
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

from core.sdk import ATimeComponent, Input, Output
from core.interfaces import ComponentStatus
from data import assert_type
from data.grid import Grid


class Mhm(ATimeComponent):
    def __init__(self, grid_spec, step):
        super(Mhm, self).__init__()
        self._time = 0
        self._step = step

        self._grid_spec = grid_spec
        self.soil_moisture = None

        self._status = ComponentStatus.CREATED

    def initialize(self):
        super().initialize()

        self.soil_moisture = Grid(self._grid_spec)

        self._inputs["precipitation"] = Input()
        self._inputs["LAI"] = Input()
        self._outputs["soil_moisture"] = Output()
        self._outputs["GW_recharge"] = Output()
        self._outputs["ETP"] = Output()

        self._status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()

        self._outputs["soil_moisture"].push_data(self.soil_moisture, self.time())
        self._outputs["GW_recharge"].push_data(0.0, self.time())
        self._outputs["ETP"].push_data(0.0, self.time())

        self._status = ComponentStatus.CONNECTED

    def validate(self):
        super().validate()

        self._status = ComponentStatus.VALIDATED

    def update(self):
        super().update()

        # Retrieve inputs
        precipitation = self._inputs["precipitation"].pull_data(self.time())
        lai = self._inputs["LAI"].pull_data(self.time())

        # Check input data types
        assert_type(self, "precipitation", precipitation, [int, float])
        assert_type(self, "LAI", lai, [Grid])
        if self.soil_moisture.spec != lai.spec:
            raise Exception(f"Grid specifications not matching for LAI in mHM.")

        # Run the model step here
        base_flow = 0.0
        total_recharge = 0.0
        mean_evaporation = 0.0
        for i in range(len(self.soil_moisture.data)):
            sm = self.soil_moisture.data[i]
            sm += precipitation
            recharge = 0.1 * sm
            evaporation = 0.5 * sm * (1.0 - math.exp(-0.05 * lai.data[i]))
            sm -= recharge + evaporation
            self.soil_moisture.data[i] = sm

            total_recharge += recharge
            mean_evaporation += evaporation

        mean_evaporation /= float(len(self.soil_moisture.data))

        # Increment model time
        self._time += self._step

        # Push model state to outputs
        self._outputs["soil_moisture"].push_data(self.soil_moisture, self.time())
        self._outputs["GW_recharge"].push_data(total_recharge, self.time())
        self._outputs["ETP"].push_data(mean_evaporation, self.time())

        # Update component status
        self._status = ComponentStatus.UPDATED

    def finalize(self):
        super().finalize()

        self._status = ComponentStatus.FINALIZED
