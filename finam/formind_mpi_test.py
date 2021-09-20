import argparse
import numpy as np

from adapters import base, time
from core import mpi
from core.schedule import Composition
from models import formind_mpi
from modules import generators, writers
from data.grid import Grid, GridSpec


def run():
    from mpi4py import MPI

    communicators = parse_args()

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    def soil_water(t):
        grid = Grid(GridSpec(5, 5, cell_size=1000))
        for i in range(len(grid.data)):
            grid.data[i] = 25.0 + i * 0.1
        return grid

    sw_comp = generators.CallbackGenerator({"soil_water": soil_water}, step=365)
    formind_comp = formind_mpi.Formind(
        comm=communicators["formind"],
        grid_spec=GridSpec(5, 5, cell_size=1000),
        step=365,
        par_file="formind/formind_parameters/beech_forest.par",
    )

    formind_csv = writers.CsvWriter(
        path="formind.csv",
        step=365,
        inputs=["SW_in", "LAI"],
    )

    composition = Composition([sw_comp, formind_comp, formind_csv], mpi_rank=rank)

    if not composition.run_mpi():
        exit(0)

    composition.initialize()

    # Model coupling

    (
        sw_comp.outputs()["soil_water"]
        >> time.LinearInterpolation()
        >> formind_comp.inputs()["soil_water"]
    )

    (
        sw_comp.outputs()["soil_water"]
        >> base.GridToValue(func=np.mean)
        >> time.LinearInterpolation()
        >> formind_csv.inputs()["SW_in"]
    )

    (
        formind_comp.outputs()["LAI"]
        >> base.GridToValue(func=np.mean)
        >> time.LinearInterpolation()
        >> formind_csv.inputs()["LAI"]
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
