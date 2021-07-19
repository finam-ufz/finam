"""
Dummy model mimicking Formind. Uses multiple MPI processes.

To use this model component from the project's root directory, run ``export PYTHONPATH="./formind"`` before
(``set PYTHONPATH=./formind`` on Windows).
"""

import math
import numpy as np
from multiprocessing import Pipe, Process

from core import mpi
from core.sdk import ATimeComponent, Input, Output, AAdapter
from core.interfaces import ComponentStatus, IMpiComponent, NoBranchAdapter
from data import assert_type
from data.grid import Grid

TAG_DATA = 0
TAG_STOP = 1


class FormindWorker:
    def __init__(self, processes, index, total_cells, par_file):
        self.indices = calc_indices(processes, total_cells)[index]
        self.cells = [create_cell(par_file) for _ in self.indices]


def create_cell(par_file):
    parent_conn, child_conn = Pipe()
    p = Process(target=run_cell, args=(child_conn, par_file))
    p.start()

    return parent_conn


def run_cell(conn, par_file):
    from pyformind_finam import Model

    model = Model()
    model.read_par_file(par_file)
    model.start()

    conn.send(model.get_lai())

    while True:
        msg = conn.recv()

        if msg is None:
            break

        model.set_reduction_factor(msg)
        model.step()
        conn.send(model.get_lai())


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
        buffer[i] = cell.recv()


class Formind(ATimeComponent, IMpiComponent):
    def __init__(self, comm, grid_spec, par_file, step):
        super(Formind, self).__init__()
        self._comm = comm
        self._time = 0
        self._step = step

        self.par_file = par_file

        self._grid_spec = grid_spec
        self.lai = None

        self.indices = None

        self._status = ComponentStatus.CREATED

    def initialize(self):
        super().initialize()
        print("Initializing Formind main process")

        self.lai = Grid(self._grid_spec)

        self._inputs["reduction_factor"] = Input()
        self._outputs["LAI"] = Output()

        self.indices = calc_indices(
            processes=self._comm.Get_size() - 1, total_cells=len(self.lai.data)
        )

        self._status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()

        print(f"Connecting ({self._comm.Get_size() - 1}+1 processes)...")
        for rank in range(1, self._comm.Get_size()):
            r = self.indices[rank - 1]
            self._comm.Recv(self.lai.data[r.start : r.stop], source=rank, tag=TAG_DATA)

        print("   Connecting done")

        self._outputs["LAI"].push_data(self.lai, self.time())

        self._status = ComponentStatus.CONNECTED

    def validate(self):
        super().validate()

        self._status = ComponentStatus.VALIDATED

    def update(self):
        super().update()

        # Retrieve inputs
        reduction_factor = self._inputs["reduction_factor"].pull_data(self.time())

        # Check input data types
        assert_type(self, "reduction_factor", reduction_factor, [Grid])
        if self.lai.spec != reduction_factor.spec:
            raise Exception(
                f"Grid specifications not matching for reduction_factor in Formind."
            )

        print(f"Updating MPI processes (t={self._time})...")
        size = self._comm.Get_size()
        for rank in range(1, size):
            r = self.indices[rank - 1]
            data_slice = reduction_factor.data[r.start : r.stop]
            self._comm.Send(data_slice, dest=rank, tag=TAG_DATA)

        for rank in range(1, size):
            r = self.indices[rank - 1]
            data_slice = self.lai.data[r.start : r.stop]
            self._comm.Recv(data_slice, source=rank, tag=TAG_DATA)

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
            self._comm.send(True, dest=rank, tag=TAG_STOP)

        self._comm.Disconnect()
        print("   Disconnecting done")

        self._status = ComponentStatus.FINALIZED

    def run_mpi(self):
        from mpi4py import MPI

        if mpi.is_null(self._comm):
            return

        total_cells = self._grid_spec.nrows * self._grid_spec.ncols
        worker = FormindWorker(
            processes=self._comm.Get_size() - 1,
            index=self._comm.Get_rank() - 1,
            total_cells=total_cells,
            par_file=self.par_file,
        )

        data_buffer = np.empty(len(worker.cells), dtype=np.float64)
        lai_buffer = np.empty(len(worker.cells), dtype=np.float64)

        fill_lai_buffer(worker.cells, lai_buffer)
        self._comm.Send(lai_buffer, dest=0)

        while True:
            info = MPI.Status()
            self._comm.Probe(source=0, tag=MPI.ANY_TAG, status=info)

            if info.tag == TAG_STOP:
                for c in worker.cells:
                    c.send(None)
                self._comm.Disconnect()
                break
            elif info.tag != TAG_DATA:
                raise Exception(
                    f"Invalid message tag {info.tag} received in Formind worker"
                )

            self._comm.Recv(data_buffer, source=0, tag=TAG_DATA)

            for i, cell in enumerate(worker.cells):
                cell.send(data_buffer[i])

            fill_lai_buffer(worker.cells, lai_buffer)
            self._comm.Send(lai_buffer, dest=0, tag=TAG_DATA)


class SoilWaterAdapter(AAdapter, NoBranchAdapter):
    def __init__(self, pwp, fc):
        super().__init__()

        self.pwp = pwp
        self.fc = fc
        self.msw = pwp + 0.4 * (fc - pwp)

        self.factor_sum = None
        self.counter = 0

    def source_changed(self, time):
        data = self.pull_data(time)

        if self.factor_sum is None:
            if isinstance(data, Grid):
                self.factor_sum = Grid.create_like(data)
            else:
                self.factor_sum = 0.0

        f = calc_reduction_factor(data, self.pwp, self.msw)
        self.factor_sum += f
        self.counter += 1

        self.notify_targets(time)

    def get_data(self, time):
        result = self.factor_sum / self.counter

        if isinstance(self.factor_sum, Grid):
            self.factor_sum.fill(0.0)
        else:
            self.factor_sum = 0

        self.counter = 0

        return result


def calc_reduction_factor(sw, pwp, msw):
    return (np.clip(sw, pwp, msw) - pwp) / (msw - pwp)
