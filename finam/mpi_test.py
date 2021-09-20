"""
The mHM/OGS/Formind setup, with Formind using multiple MPI processes.

To run this example from the project's root directory, run ``export PYTHONPATH="./formind"`` before
(``set PYTHONPATH=./formind`` on Windows).

This example must be run using ``mpirun``:

* ``mpirun -n 4 python finam/mpi_test.py --mpi formind 3``, or
* ``mpiexec -n 4 python finam/mpi_test.py --mpi formind 3`` on Windows.
"""

import random
import argparse
import numpy as np

from adapters import base, time
from core import mpi
from core.schedule import Composition
from models import formind_mpi, ogs, mhm
from modules import generators, writers
from data.grid import GridSpec


def run():
    from mpi4py import MPI

    communicators = parse_args()

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    def precip(t):
        p = 0.1 * (1 + int(t / (5 * 365)) % 2)
        return 1.0 if random.uniform(0, 1) < p else 0.0

    precipitation_comp = generators.CallbackGenerator({"precipitation": precip}, step=1)
    mhm_comp = mhm.Mhm(grid_spec=GridSpec(5, 5, cell_size=1000), step=7)
    ogs_comp = ogs.Ogs(step=30)
    formind_comp = formind_mpi.Formind(
        comm=communicators["formind"],
        grid_spec=GridSpec(5, 5, cell_size=1000),
        step=365,
        par_file="formind/formind_parameters/beech_forest.par",
    )

    mhm_csv = writers.CsvWriter(
        path="mhm.csv",
        step=7,
        inputs=["precip_in", "LAI_in", "soil_water", "GW_recharge", "ETP"],
    )

    composition = Composition(
        [precipitation_comp, mhm_comp, ogs_comp, formind_comp, mhm_csv], mpi_rank=rank
    )

    if not composition.run_mpi():
        exit(0)

    composition.initialize()

    # Model coupling

    (  # RNG -> mHM (precipitation)
        precipitation_comp.outputs()["precipitation"]
        >> time.LinearIntegration.sum()
        >> mhm_comp.inputs()["precipitation"]
    )

    (  # mHM -> Formind (soil moisture)
        mhm_comp.outputs()["soil_water"]
        >> time.LinearIntegration.mean()
        >> formind_comp.inputs()["soil_water"]
    )

    (  # Formind -> mHM (LAI)
        formind_comp.outputs()["LAI"] >> time.NextValue() >> mhm_comp.inputs()["LAI"]
    )

    (  # mHM -> OGS (base_flow)
        mhm_comp.outputs()["GW_recharge"]
        >> time.LinearIntegration.sum()
        >> ogs_comp.inputs()["GW_recharge"]
    )

    # Observer coupling for CSV output

    (  # RNG -> CSV (precipitation)
        precipitation_comp.outputs()["precipitation"]
        >> time.LinearIntegration.sum()
        >> mhm_csv.inputs()["precip_in"]
    )

    (  # mHM/Formind -> CSV (LAI input)
        formind_comp.outputs()["LAI"]
        >> base.GridToValue(func=np.mean)
        >> time.NextValue()
        >> mhm_csv.inputs()["LAI_in"]
    )

    (  # mHM -> CSV (soil_water)
        mhm_comp.outputs()["soil_water"]
        >> base.GridToValue(func=np.mean)
        >> time.LinearInterpolation()
        >> mhm_csv.inputs()["soil_water"]
    )

    (  # mHM -> CSV (base_flow)
        mhm_comp.outputs()["GW_recharge"]
        >> time.LinearInterpolation()
        >> mhm_csv.inputs()["GW_recharge"]
    )

    (  # mHM -> CSV (ETP)
        mhm_comp.outputs()["ETP"]
        >> time.LinearInterpolation()
        >> mhm_csv.inputs()["ETP"]
    )

    composition.run(365 * 25)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mpi", nargs="+", help="key value pairs for number of MPI processes"
    )
    args = parser.parse_args()

    mpi_dict = args.mpi or []

    if len(mpi_dict) % 2 != 0:
        raise Exception("An even number of arguments is required for option '--mpi'")

    processes = {
        mpi_dict[i * 2]: int(mpi_dict[i * 2 + 1]) for i in range(len(mpi_dict) // 2)
    }

    return mpi.create_communicators(processes)


if __name__ == "__main__":
    run()