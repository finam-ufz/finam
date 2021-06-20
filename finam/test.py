import random

from adapters import time, base
from schedule import Composition
from models import formind
from modules import csv_writer, generators


if __name__ == "__main__":
    rng = generators.CallbackGenerator(
        {"soil_moisture": lambda t: random.uniform(0, 1)}, step=5
    )
    formind = formind.Formind(step=25)

    rng_csv = csv_writer.CsvWriter(path="rng.csv", step=5, inputs=["soil_moisture"])
    formind_csv = csv_writer.CsvWriter(
        path="formind.csv", step=25, inputs=["soil_moisture", "LAI"]
    )

    modules = [rng, formind, rng_csv, formind_csv]

    for m in modules:
        m.initialize()

    time.LinearIntegration.mean().link(
        rng.outputs()["soil_moisture"], formind.inputs()["soil_moisture"]
    )

    rng.outputs()["soil_moisture"].chain(time.LinearInterpolation()).chain(
        base.Callback(lambda v, t: v * 10.0)
    ).chain(rng_csv.inputs()["soil_moisture"])

    time.LinearIntegration.mean().link(
        rng.outputs()["soil_moisture"], formind_csv.inputs()["soil_moisture"]
    )
    time.LinearInterpolation().link(
        formind.outputs()["LAI"], formind_csv.inputs()["LAI"]
    )

    composition = Composition(modules)
    composition.run(1000)
