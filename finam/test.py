from adapters import NextValue, PreviousValue, LinearInterpolation, LinearIntegration
from models import formind
from modules import csv_printer, random_output


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
    random_time_series = random_output.RandomOutput(step=5)
    formind = formind.Formind(step=25)
    csv = csv_printer.CsvPrinter(step=5, inputs=["soil_moisture", "LAI", "soil_moisture_int", "LAI_int"])

    modules = [random_time_series, formind, csv]

    for m in modules:
        m.initialize()

    LinearInterpolation().link(
        random_time_series.outputs()["Random"], formind.inputs()["soil_moisture"]
    )

    LinearInterpolation().link(
        random_time_series.outputs()["Random"], csv.inputs()["soil_moisture"]
    )
    LinearInterpolation().link(formind.outputs()["LAI"], csv.inputs()["LAI"])

    LinearIntegration.mean().link(formind.outputs()["LAI"], csv.inputs()["LAI_int"])
    LinearIntegration.mean().link(
        random_time_series.outputs()["Random"], csv.inputs()["soil_moisture_int"]
    )

    run(modules, 1000)
