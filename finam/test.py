from adapters import NextValue, PreviousValue, LinearInterpolation, LinearIntegration
from models import formind
from modules import csv_writer, random_output


def run(mods, t_max):
    for mod in mods:
        mod.validate()

    while True:
        mods.sort(key=lambda m: m.time())
        # print(models[0].__class__.__name__, models[0].time())

        mods[0].update()

        any_running = False
        for mod in mods:
            if mod.time() < t_max:
                any_running = True
                break

        if not any_running:
            break


if __name__ == "__main__":
    rng = random_output.RandomOutput(step=5)
    formind = formind.Formind(step=25)

    rng_csv = csv_writer.CsvWriter(path="rng.csv", step=5, inputs=["soil_moisture"])
    formind_csv = csv_writer.CsvWriter(path="formind.csv", step=25, inputs=["soil_moisture", "LAI"])

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
    LinearInterpolation().link(
        formind.outputs()["LAI"], formind_csv.inputs()["LAI"]
    )

    run(modules, 1000)
