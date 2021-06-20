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

    (  # RNG -> Formind
        rng.outputs()["soil_moisture"]
        >> time.LinearIntegration.mean()
        >> formind.inputs()["soil_moisture"]
    )

    (  # RNG -> CSV
        rng.outputs()["soil_moisture"]
        >> time.LinearInterpolation()
        >> base.Callback(lambda v, t: v * 10.0)
        >> rng_csv.inputs()["soil_moisture"]
    )

    (  # Formind input (RNG) -> CSV
        rng.outputs()["soil_moisture"]
        >> time.LinearIntegration.mean()
        >> formind_csv.inputs()["soil_moisture"]
    )

    (  # Formind output (LAI) -> CSV
        formind.outputs()["LAI"]
        >> time.LinearInterpolation()
        >> formind_csv.inputs()["LAI"]
    )

    composition = Composition(modules)
    composition.run(1000)
