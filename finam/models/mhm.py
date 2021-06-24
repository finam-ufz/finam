"""
Dummy model mimicking mHM.

From an input scalar ``precipitation`` and an input grid ``LAI``,
it calculates the output grid ``soil_moisture`` and output scalars ``base_flow`` and ``ETP``.

For each grid cell, calculations in each model step are as follows:

.. math::

    sm_{temp} = soil\_moisture(t) + precipitation

    bf = 0.1 * sm_{temp}

    etp = 0.5 * sm_{temp} * (1.0 - e^{-0.05 * LAI})

    soil\_moisture(t + \Delta t) = sm_{temp} - (bf + etp)

Output ``ETP`` is the average of ``etp`` over all cells. ``base_flow`` is the sum of ``bf`` over all cells.
"""

import math

from core.sdk import ATimeComponent, Input, Output
from core.interfaces import ComponentStatus
from data.grid import Grid


class Mhm(ATimeComponent):
    def __init__(self, grid_spec, step):
        super(Mhm, self).__init__()
        self._time = 0
        self._step = step
        self.soil_moisture = Grid(grid_spec)
        self._status = ComponentStatus.CREATED

    def initialize(self):
        super().initialize()

        self._inputs["precipitation"] = Input()
        self._inputs["LAI"] = Input()
        self._outputs["soil_moisture"] = Output()
        self._outputs["base_flow"] = Output()
        self._outputs["ETP"] = Output()

        self._status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()

        self._outputs["soil_moisture"].push_data(self.soil_moisture, self.time())
        self._outputs["base_flow"].push_data(0.0, self.time())
        self._outputs["ETP"].push_data(0.0, self.time())

        self._status = ComponentStatus.CONNECTED

    def validate(self):
        super().validate()

        self._status = ComponentStatus.VALIDATED

    def update(self):
        super().update()

        precipitation = self._inputs["precipitation"].pull_data(self.time())

        if not (isinstance(precipitation, int) or isinstance(precipitation, float)):
            raise Exception(
                f"Unsupported data type for precipitation in Mhm: {precipitation.__class__.__name__}"
            )

        lai = self._inputs["LAI"].pull_data(self.time())

        if not isinstance(lai, Grid):
            raise Exception(
                f"Unsupported data type for LAI in Mhm: {lai.__class__.__name__}"
            )

        if self.soil_moisture.spec != lai.spec:
            raise Exception(f"Grid specifications not matching for LAI in Mhm.")

        # Run the model step here
        base_flow = 0.0
        total_base_flow = 0.0
        mean_evaporation = 0.0
        for i in range(len(self.soil_moisture.data)):
            sm = self.soil_moisture.data[i]
            sm += precipitation
            base_flow = 0.1 * sm
            evaporation = 0.5 * sm * (1.0 - math.exp(-0.05 * lai.data[i]))
            sm -= base_flow + evaporation
            self.soil_moisture.data[i] = sm

            total_base_flow += base_flow
            mean_evaporation += evaporation

        mean_evaporation /= float(len(self.soil_moisture.data))

        self._time += self._step

        self._outputs["soil_moisture"].push_data(self.soil_moisture, self.time())
        self._outputs["base_flow"].push_data(base_flow, self.time())
        self._outputs["ETP"].push_data(mean_evaporation, self.time())

        self._status = ComponentStatus.UPDATED

    def finalize(self):
        super().finalize()

        self._status = ComponentStatus.FINALIZED
