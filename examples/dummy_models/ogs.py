"""
Dummy model mimicking OGS.

From an input scalar ``base_flow``, it calculates the output scalar ``head``.

.. code-block:: text

                    +---------+
    --> GW_recharge |   OGS   | head -->
                    +---------+

Calculations in each model step are as follows:

.. math::

    head(t + \Delta t) = (head(t) + GW\_recharge) * 0.9
"""
from datetime import datetime, timedelta

import finam as fm


class Ogs(fm.TimeComponent):
    def __init__(self, start, step):
        super().__init__()

        if not isinstance(start, datetime):
            raise ValueError("Start must be of type datetime")
        if not isinstance(step, timedelta):
            raise ValueError("Step must be of type timedelta")

        self._time = start
        self._step = step
        self.head = 0 * fm.UNITS.Unit("mm")

    def _initialize(self):

        self.inputs.add(
            name="GW_recharge", time=self.time, grid=fm.NoGrid(), units="mm"
        )
        self.outputs.add(name="head", time=self.time, grid=fm.NoGrid(), units="mm")

        self.create_connector()

    def _connect(self):
        self.try_connect(time=self.time, push_data={"head": 0})

    def _validate(self):
        pass

    def _update(self):
        # Retrieve inputs
        recharge = fm.data.strip_time(self.inputs["GW_recharge"].pull_data(self.time))

        # Run the model step here
        self.head = (self.head + fm.data.get_data(recharge)) * 0.9

        # Increment model time
        self._time += self.step

        # Push model state to outputs
        self.outputs["head"].push_data(self.head, self.time)

    def _finalize(self):
        pass

    @property
    def step(self):
        return self._step
