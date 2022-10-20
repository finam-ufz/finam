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
from datetime import datetime, timedelta

import numpy as np

import finam as fm


class Mhm(fm.ATimeComponent):
    def __init__(self, grid, start, step):
        super().__init__()

        if not isinstance(start, datetime):
            raise ValueError("Start must be of type datetime")
        if not isinstance(step, timedelta):
            raise ValueError("Step must be of type timedelta")

        self._time = start
        self._step = step

        self.grid = grid
        self.soil_water = None

    def _initialize(self):
        self.soil_water = fm.data.full(
            1.0, "soil_water", fm.Info(grid=self.grid), self.time
        )

        self.inputs.add(name="precipitation", grid=fm.NoGrid(), units="mm")
        self.inputs.add(name="LAI", grid=self.grid)
        self.outputs.add(name="ETP", grid=fm.NoGrid(), units="mm")
        self.outputs.add(name="GW_recharge", grid=fm.NoGrid(), units="mm")
        self.outputs.add(name="soil_water", grid=self.grid)

        self.create_connector()

    def _connect(self):
        push_data = {
            "soil_water": self.soil_water,
            "GW_recharge": 0.0,
            "ETP": 0.0,
        }
        self.try_connect(time=self.time, push_data=push_data)

    def _validate(self):
        pass

    def _update(self):
        # Retrieve inputs
        precipitation = fm.data.strip_time(
            self.inputs["precipitation"].pull_data(self.time)
        )
        lai = fm.data.strip_time(self.inputs["LAI"].pull_data(self.time))

        # Run the model step here
        base_flow = 0.0
        mm = fm.UNITS.Unit("mm")
        total_recharge = 0.0 * mm
        mean_evaporation = 0.0 * mm
        for x in range(self.soil_water.shape[1]):
            for y in range(self.soil_water.shape[2]):
                sm = self.soil_water[0, x, y]
                sm += fm.data.get_magnitude(precipitation)
                recharge = 0.1 * sm
                evaporation = 0.5 * sm * (1.0 - np.exp(-0.05 * lai[x, y]))
                sm -= recharge + evaporation
                self.soil_water[0, x, y] = sm

                total_recharge += recharge * mm
                mean_evaporation += evaporation * mm

        mean_evaporation /= float(len(self.soil_water.data))

        # Increment model time
        self._time += self._step
        # Push model state to outputs
        self.outputs["soil_water"].push_data(
            fm.data.get_data(self.soil_water), self.time
        )
        self.outputs["GW_recharge"].push_data(
            fm.data.get_data(total_recharge), self.time
        )
        self.outputs["ETP"].push_data(fm.data.get_data(mean_evaporation), self.time)

    def _finalize(self):
        pass

    @property
    def step(self):
        return self._step
