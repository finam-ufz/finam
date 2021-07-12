"""
Dummy model mimicking Formind. Uses multiple MPI processes.
"""

import math
import random

from core import mpi
from core.sdk import ATimeComponent, Input, Output
from core.interfaces import ComponentStatus, IMpiComponent
from data import assert_type
from data.grid import Grid


class FormindWorker:
    def __init__(self):
        self.lai = 1.0
        self.soil_moisture = 0.0

    def step(self):
        growth = (1.0 - math.exp(-0.1 * self.soil_moisture)) * random.uniform(0.5, 1.0)
        self.lai = (self.lai + growth) * 0.9


class Formind(ATimeComponent, IMpiComponent):
    def __init__(self, comm, grid_spec, step):
        super(Formind, self).__init__()
        self._comm = comm
        self._time = 0
        self._step = step

        self._grid_spec = grid_spec
        self.lai = None

        self._status = ComponentStatus.CREATED

    def initialize(self):
        super().initialize()
        print("Initializing Formind main process")

        self.lai = Grid(self._grid_spec)
        self.lai.fill(1.0)

        self._inputs["soil_moisture"] = Input()
        self._outputs["LAI"] = Output()

        self._status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()

        print(f"Connecting ({self._comm.Get_size()-1}+1 processes)...")
        for rank in range(1, self._comm.Get_size()):
            lai = self._comm.recv(source=rank)
            # set lai grid values
        print("   Connecting done")

        self._outputs["LAI"].push_data(self.lai, self.time())

        self._status = ComponentStatus.CONNECTED

    def validate(self):
        super().validate()

        self._status = ComponentStatus.VALIDATED

    def update(self):
        super().update()

        # Retrieve inputs
        soil_moisture = self._inputs["soil_moisture"].pull_data(self.time())

        # Check input data types
        assert_type(self, "soil_moisture", soil_moisture, [Grid])
        if self.lai.spec != soil_moisture.spec:
            raise Exception(
                f"Grid specifications not matching for soil_moisture in Formind."
            )

        print(f"Updating MPI processes (t={self._time})...")
        for rank in range(1, self._comm.Get_size()):
            self._comm.send(soil_moisture.data[rank], dest=rank)
            lai = self._comm.recv(source=rank)
            # set lai grid values

        # Run the model step here
        for i in range(len(self.lai.data)):
            growth = (1.0 - math.exp(-0.1 * soil_moisture.data[i])) * random.uniform(
                0.5, 1.0
            )
            self.lai.data[i] = (self.lai.data[i] + growth) * 0.9

        # Increment model time
        self._time += self._step

        # Push model state to outputs
        self._outputs["LAI"].push_data(self.lai, self.time())

        # Update component status
        self._status = ComponentStatus.UPDATED

    def finalize(self):
        super().finalize()

        print("Disconnecting...")
        for rank in range(1, self._comm.Get_size()):
            self._comm.send(None, dest=rank)

        self._comm.Disconnect()
        print("   Disconnecting done")

        self._status = ComponentStatus.FINALIZED

    def run_mpi(self):
        if mpi.is_null(self._comm):
            return

        worker = FormindWorker()

        self._comm.send(worker.lai, dest=0)

        while True:
            inbox = self._comm.recv(source=0)
            if inbox is None:
                self._comm.Disconnect()
                break

            worker.soil_moisture = inbox

            worker.step()

            self._comm.send(worker.lai, dest=0)
