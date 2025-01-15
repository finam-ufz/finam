import cProfile
import datetime as dt
import io
import pstats
import sys
import time

import numpy as np

import finam as fm


def run_model():
    t = time.time()

    start_time = dt.datetime(2000, 1, 1)
    end_time = dt.datetime(2002, 1, 1)

    size = (1024, 1024)

    info1 = fm.Info(time=None, grid=fm.UniformGrid(size), units="m")
    data = fm.data.prepare(fm.data.full(0.0, info1), info1)

    def gen_data(t):
        return np.copy(data)

    source = fm.components.CallbackGenerator(
        callbacks={"Out": (gen_data, info1.copy())},
        start=start_time,
        step=dt.timedelta(days=1),
    )
    sink = fm.components.DebugConsumer(
        inputs={
            "In": info1.copy(),
        },
        start=start_time,
        step=dt.timedelta(days=365),
    )

    composition = fm.Composition([source, sink], slot_memory_limit=500 * 2**20)

    source["Out"] >> sink["In"]

    composition.run(end_time=end_time)

    print("Total time:", time.time() - t)


if __name__ == "__main__":
    pr = cProfile.Profile()
    pr.enable()

    run_model()

    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats(pstats.SortKey.CUMULATIVE)
    ps.dump_stats(sys.argv[1])
