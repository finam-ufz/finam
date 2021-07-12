"""
The mHM/OGS/Formind setup, with Formind using multiple MPI processes.
"""

import random
import argparse

from adapters import time
from core import mpi
from core.schedule import Composition
from models import formind_mpi, ogs, mhm
from modules import generators
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
    )

    composition = Composition(
        [precipitation_comp, mhm_comp, ogs_comp, formind_comp], mpi_rank=rank
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
        mhm_comp.outputs()["soil_moisture"]
        >> time.LinearIntegration.mean()
        >> formind_comp.inputs()["soil_moisture"]
    )

    (  # Formind -> mHM (LAI)
        formind_comp.outputs()["LAI"] >> time.NextValue() >> mhm_comp.inputs()["LAI"]
    )

    (  # mHM -> OGS (base_flow)
        mhm_comp.outputs()["GW_recharge"]
        >> time.LinearIntegration.sum()
        >> ogs_comp.inputs()["GW_recharge"]
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
