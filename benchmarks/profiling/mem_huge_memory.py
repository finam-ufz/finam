import datetime as dt

import numpy as np

import finam as fm

if __name__ == "__main__":
    start_time = dt.datetime(2000, 1, 1)
    end_time = dt.datetime(2002, 1, 1)

    size = (1024, 1024)

    info1 = fm.Info(time=None, grid=fm.UniformGrid(size), units="m")
    data = fm.data.to_xarray(fm.data.full(0.0, info1), info1)

    def gen_data(t):
        return np.copy(data)

    source = fm.modules.CallbackGenerator(
        callbacks={"Out": (gen_data, info1.copy())},
        start=start_time,
        step=dt.timedelta(days=1),
    )
    sink = fm.modules.DebugConsumer(
        inputs={
            "In": info1.copy(),
        },
        start=start_time,
        step=dt.timedelta(days=365),
    )

    composition = fm.Composition([source, sink])
    composition.initialize()

    source["Out"] >> sink["In"]

    composition.run(end_time=end_time)
