from adapters import NextValue, PreviousValue, LinearInterpolation
from models import formind, random_output


if __name__ == "__main__":
    random_time_series = random_output.RandomOutput(365)
    formind = formind.Formind(30)

    models = [random_time_series, formind]

    for m in models:
        m.initialize()

    adapter = LinearInterpolation()
    adapter.link(
        random_time_series.outputs()["Random"], formind.inputs()["soil_moisture"]
    )

    for m in models:
        m.validate()

    for _ in range(250):
        models.sort(key=lambda m: m.time())
        print(models[0].__class__.__name__, models[0].time())
        models[0].update()

    adapter = LinearInterpolation()
