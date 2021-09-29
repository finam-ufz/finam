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
            grid.data[i] = (t / 365) % 5 * 2.0 + np.random.uniform(10.0, 30.0)
        return grid

    sw_comp = generators.CallbackGenerator({"soil_water": soil_water}, step=1)

    formind_comp = formind_mpi.Formind(
        comm=communicators["formind"],
        grid_spec=GridSpec(5, 5, cell_size=1000),
        step=365,
        par_file="formind/formind_parameters/beech_forest.par",
    )

    soil_water_csv = writers.CsvWriter(
        path="soil_water.csv",
        step=1,
        inputs=["SW"],
    )

    formind_csv = writers.CsvWriter(
        path="formind.csv",
        step=365,
        inputs=["SW_in", "RW_in", "LAI"],
    )

    composition = Composition(
        [sw_comp, formind_comp, soil_water_csv, formind_csv], mpi_rank=rank
    )

    if not composition.run_mpi():
        exit(0)

    composition.initialize()

    # Model coupling

    (
        sw_comp.outputs()["soil_water"]
        >> formind_mpi.SoilWaterAdapter(pwp=20.0, fc=40.0)
        >> formind_comp.inputs()["reduction_factor"]
    )

    (
        sw_comp.outputs()["soil_water"]
        >> base.GridToValue(func=np.mean)
        >> time.LinearInterpolation()
        >> soil_water_csv.inputs()["SW"]
    )

    (
        sw_comp.outputs()["soil_water"]
        >> base.GridToValue(func=np.mean)
        >> time.LinearIntegration.mean()
        >> formind_csv.inputs()["SW_in"]
    )

    (
        sw_comp.outputs()["soil_water"]
        >> formind_mpi.SoilWaterAdapter(pwp=20.0, fc=40.0)
        >> base.GridToValue(func=np.mean)
        >> formind_csv.inputs()["RW_in"]
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
