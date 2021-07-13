"""
Dummy model mimicking Formind. Uses multiple MPI processes.
"""

import math
import random
import numpy as np

from core import mpi
from core.sdk import ATimeComponent, Input, Output
from core.interfaces import ComponentStatus, IMpiComponent
from data import assert_type
from data.grid import Grid


class FormindCell:
    def __init__(self):
        self.lai = 1.0
        self.soil_moisture = 0.0

    def step(self):
        growth = (1.0 - math.exp(-0.1 * self.soil_moisture)) * random.uniform(0.5, 1.0)
        self.lai = (self.lai + growth) * 0.9


class FormindWorker:
    def __init__(self, processes, index, total_cells):
        self.indices = calc_indices(processes, total_cells)[index]
        self.cells = [FormindCell() for _ in self.indices]

    def step(self):
        for cell in self.cells:
            cell.step()


def calc_indices(processes, total_cells):
    indices = []

    start = 0
    for idx in range(processes):
        count = math.ceil((total_cells - idx) / processes)
        indices.append(range(start, start + count))
        start += count

    return indices


def fill_lai_buffer(cells, buffer):
    for i, cell in enumerate(cells):
        buffer[i] = cell.lai


class Formind(ATimeComponent, IMpiComponent):
    def __init__(self, comm, grid_spec, step):
        super(Formind, self).__init__()
        self._comm = comm
        self._time = 0
        self._step = step

        self._grid_spec = grid_spec
        self.lai = None
        self.lai_buffers = None

        self.indices = None

        self._status = ComponentStatus.CREATED

    def initialize(self):
        super().initialize()
        print("Initializing Formind main process")

        self.lai = Grid(self._grid_spec)

        self._inputs["soil_moisture"] = Input()
        self._outputs["LAI"] = Output()

        self.indices = calc_indices(
            processes=self._comm.Get_size() - 1, total_cells=len(self.lai.data)
        )

        self.lai_buffers = [np.empty(len(r), dtype=np.float64) for r in self.indices]

        self._status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()

        print(f"Connecting ({self._comm.Get_size() - 1}+1 processes)...")
        for rank in range(1, self._comm.Get_size()):
            r = self.indices[rank - 1]
            self._comm.Recv(self.lai.data[r.start : r.stop], source=rank)

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
        size = self._comm.Get_size()
        for rank in range(1, size):
            r = self.indices[rank - 1]
            self._comm.send(True, dest=rank)

            data_slice = soil_moisture.data[r.start : r.stop]
            self._comm.Send(data_slice, dest=rank)

        for rank in range(1, size):
            r = self.indices[rank - 1]
            data_slice = self.lai.data[r.start : r.stop]
            self._comm.Recv(data_slice, source=rank)

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
            self._comm.send(False, dest=rank)

        self._comm.Disconnect()
        print("   Disconnecting done")

        self._status = ComponentStatus.FINALIZED

    def run_mpi(self):
        if mpi.is_null(self._comm):
            return

        total_cells = self._grid_spec.nrows * self._grid_spec.ncols
        worker = FormindWorker(
            processes=self._comm.Get_size() - 1,
            index=self._comm.Get_rank() - 1,
            total_cells=total_cells,
        )

        data_buffer = np.empty(len(worker.cells), dtype=np.float64)
        lai_buffer = np.empty(len(worker.cells), dtype=np.float64)

        fill_lai_buffer(worker.cells, lai_buffer)
        self._comm.Send(lai_buffer, dest=0)

        while True:
            if not self._comm.recv(source=0):
                self._comm.Disconnect()
                break

            self._comm.Recv(data_buffer, source=0)

            for i, cell in enumerate(worker.cells):
                cell.soil_moisture = data_buffer[i]

            worker.step()

            fill_lai_buffer(worker.cells, lai_buffer)
            self._comm.Send(lai_buffer, dest=0)
