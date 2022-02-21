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

from finam.core.sdk import ATimeComponent, Input, Output
from finam.core.interfaces import ComponentStatus
from finam.data import assert_type


class Ogs(ATimeComponent):
    def __init__(self, start, step):
        super(Ogs, self).__init__()

        if not isinstance(start, datetime):
            raise ValueError("Start must be of type datetime")
        if not isinstance(step, timedelta):
            raise ValueError("Step must be of type timedelta")

        self._time = start
        self._step = step
        self.head = 0
        self._status = ComponentStatus.CREATED

    def initialize(self):
        super().initialize()

        self._inputs["GW_recharge"] = Input()
        self._outputs["head"] = Output()

        self._status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()
        self._outputs["head"].push_data(0, self.time())

        self._status = ComponentStatus.CONNECTED

    def validate(self):
        super().validate()

        self._status = ComponentStatus.VALIDATED

    def update(self):
        super().update()

        # Retrieve inputs
        recharge = self._inputs["GW_recharge"].pull_data(self.time())

        # Check input data types
        assert_type(self, "GW_recharge", recharge, [int, float])

        # Run the model step here
        self.head = (self.head + recharge) * 0.9

        # Increment model time
        self._time += self._step

        # Push model state to outputs
        self._outputs["head"].push_data(self.head, self.time())

        # Update component status
        self._status = ComponentStatus.UPDATED

    def finalize(self):
        super().finalize()

        self._status = ComponentStatus.FINALIZED

    @property
    def step(self):
        return self._step
