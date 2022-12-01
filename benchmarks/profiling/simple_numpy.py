"""Simple coupling setup for profiling, using numpy arrays.

Two components, coupled via a single link.

Simulation runs for 1 year with a daily step in both components.
Components exchange a 128x64 uniform grid.
"""
import datetime as dt

import finam as fm


def run_model():
    start_time = dt.datetime(2000, 1, 1)
    end_time = dt.datetime(2000, 12, 31)

    counter = 0

    size = (128, 64)

    info1 = fm.Info(time=None, grid=fm.UniformGrid(size), units="m")
    info2 = fm.Info(time=None, grid=fm.UniformGrid(size), units="m")
    data = [
        fm.data.strip_data(fm.data.full(0.0, "input", info1, start_time)),
        fm.data.strip_data(fm.data.full(0.0, "input", info1, start_time)),
    ]

    def gen_data(t):
        nonlocal counter
        d = data[counter % 2]
        counter += 1
        return d

    source = fm.modules.CallbackGenerator(
        callbacks={"Out": (gen_data, info1.copy())},
        start=start_time,
        step=dt.timedelta(days=1),
    )
    sink = fm.modules.DebugConsumer(
        inputs={
            "In": info2.copy(),
        },
        start=start_time,
        step=dt.timedelta(days=1),
    )

    composition = fm.Composition([source, sink])
    composition.initialize()

    source["Out"] >> sink["In"]

    composition.run(end_time=end_time)


if __name__ == "__main__":
    for i in range(10):
        run_model()
