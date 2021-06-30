"""
Dummy model mimicking OGS.

From an input scalar ``base_flow``, it calculates the output scalar ``head``.

.. code-block:: text

                  +---------+
    --> base_flow |   OGS   | head -->
                  +---------+

Calculations in each model step are as follows:

.. math::

    head(t + \Delta t) = (head(t) + base\_flow) * 0.9
"""

from core.sdk import ATimeComponent, Input, Output
from core.interfaces import ComponentStatus
from data import assert_type


class Ogs(ATimeComponent):
    def __init__(self, step):
        super(Ogs, self).__init__()
        self._time = 0
        self._step = step
        self.head = 0
        self._status = ComponentStatus.CREATED

    def initialize(self):
        super().initialize()

        self._inputs["base_flow"] = Input()
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
        base_flow = self._inputs["base_flow"].pull_data(self.time())

        # Check input data types
        assert_type(self, "base_flow", base_flow, [int, float])

        # Run the model step here
        self.head = (self.head + base_flow) * 0.9

        # Increment model time
        self._time += self._step

        # Push model state to outputs
        self._outputs["head"].push_data(self.head, self.time())

        # Update component status
        self._status = ComponentStatus.UPDATED

    def finalize(self):
        super().finalize()

        self._status = ComponentStatus.FINALIZED
