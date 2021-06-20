from adapters import NextValue, PreviousValue, LinearInterpolation, LinearIntegration
from schedule import Composition
from models import formind
from modules import csv_writer, random_output


if __name__ == "__main__":
    rng = random_output.RandomOutput(step=5)
    formind = formind.Formind(step=25)

    rng_csv = csv_writer.CsvWriter(path="rng.csv", step=5, inputs=["soil_moisture"])
    formind_csv = csv_writer.CsvWriter(
        path="formind.csv", step=25, inputs=["soil_moisture", "LAI"]
    )

    modules = [rng, formind, rng_csv, formind_csv]

    for m in modules:
        m.initialize()

    LinearIntegration.mean().link(
        rng.outputs()["Random"], formind.inputs()["soil_moisture"]
    )

    LinearInterpolation().link(
        rng.outputs()["Random"], rng_csv.inputs()["soil_moisture"]
    )

    LinearIntegration.mean().link(
        rng.outputs()["Random"], formind_csv.inputs()["soil_moisture"]
    )
    LinearInterpolation().link(formind.outputs()["LAI"], formind_csv.inputs()["LAI"])

    composition = Composition(modules)
    composition.run(1000)
