"""
Coupling setup realizing the first LandTrans coupling step.

Coupling flow chart, without connections to CSV output:

.. code-block:: text

    +-----------+
    | Precip 1d |
    +-----------+
      (precip)
          |
        <Sum>
          |
          V
    +-----------+ (soil moisture) -- <Mean> --> +--------------+
    | mHM 7d    |                               | Formind 365d |
    +-----------+ <-- <Next> ------------ (LAI) +--------------+
     (base flow)
          |
        <Sum>
          |
          V
    +-----------+
    | OGS 30d   |
    +-----------+
"""
import logging
import random
from datetime import datetime, timedelta

import numpy as np
from dummy_models import formind, mhm, ogs

import finam as fm

if __name__ == "__main__":

    start_date = datetime(2000, 1, 1)
    day = timedelta(days=1)

    write_files = True
    sleep_seconds = 0.0001

    def precip(t):
        tt = (t - start_date).days
        p = 0.1 * (1 + int(tt / (5 * 365)) % 2)
        return (1.0 if random.uniform(0, 1) < p else 0.0) * fm.UNITS.Unit("mm")

    precipitation = fm.modules.CallbackGenerator(
        {"precipitation": (precip, fm.Info(time=None, grid=fm.NoGrid(), units="mm"))},
        start=start_date,
        step=timedelta(days=1),
    )
    mhm = mhm.Mhm(
        grid=fm.UniformGrid(
            (21, 11), spacing=(1000.0, 1000.0, 1000.0), data_location="POINTS"
        ),
        start=start_date,
        step=timedelta(days=7),
    )
    ogs = ogs.Ogs(start=start_date, step=timedelta(days=30))
    formind = formind.Formind(
        grid=fm.UniformGrid(
            (11, 7), spacing=(2000.0, 2000.0, 2000.0), data_location="POINTS"
        ),
        start=start_date,
        step=timedelta(days=365),
    )

    mhm_csv = fm.modules.CsvWriter(
        path="mhm.csv",
        start=start_date,
        step=timedelta(days=7),
        inputs=["precip_in", "ETP", "GW_recharge", "soil_water", "LAI_in"],
    )
    ogs_csv = fm.modules.CsvWriter(
        path="ogs.csv",
        start=start_date,
        step=timedelta(days=30),
        inputs=["GW_recharge_in", "head"],
    )
    formind_csv = fm.modules.CsvWriter(
        path="formind.csv",
        start=start_date,
        step=timedelta(days=365),
        inputs=["soil_water_in", "LAI"],
    )

    composition = fm.Composition(
        [precipitation, mhm, ogs, formind]
        + ([mhm_csv, ogs_csv, formind_csv] if write_files else []),
        log_level=logging.DEBUG,
    )
    composition.initialize()

    # Model coupling

    (  # RNG -> mHM (precipitation)
        precipitation.outputs["precipitation"]
        >> fm.adapters.IntegrateTime()
        >> mhm.inputs["precipitation"]
    )

    (  # mHM -> Formind (soil moisture)
        mhm.outputs["soil_water"]
        >> fm.adapters.IntegrateTime()
        >> fm.adapters.RegridLinear(fill_with_nearest=True)
        >> fm.adapters.DelayToPush()
        >> formind.inputs["soil_water"]
    )

    (  # Formind -> mHM (LAI)
        formind.outputs["LAI"]
        >> fm.adapters.NextTime()
        >> fm.adapters.RegridLinear(fill_with_nearest=True)
        >> mhm.inputs["LAI"]
    )

    (  # mHM -> OGS (base_flow)
        mhm.outputs["GW_recharge"]
        >> fm.adapters.GridToValue(func=np.sum)
        >> fm.adapters.IntegrateTime()
        >> fm.adapters.Scale(ogs.step.days)
        >> ogs.inputs["GW_recharge"]
    )

    # Observer coupling for CSV output
    if write_files:

        (  # RNG -> CSV (precipitation)
            precipitation.outputs["precipitation"]
            >> fm.adapters.IntegrateTime()
            >> fm.adapters.Scale(mhm_csv._step.days)
            >> mhm_csv.inputs["precip_in"]
        )

        (  # mHM/Formind -> CSV (LAI input)
            formind.outputs["LAI"]
            >> fm.adapters.GridToValue(func=np.mean)
            >> fm.adapters.NextTime()
            >> mhm_csv.inputs["LAI_in"]
        )

        (  # mHM -> CSV (soil_water)
            mhm.outputs["soil_water"]
            >> fm.adapters.GridToValue(func=np.mean)
            >> fm.adapters.LinearTime()
            >> mhm_csv.inputs["soil_water"]
        )

        (  # mHM -> CSV (base_flow)
            mhm.outputs["GW_recharge"]
            >> fm.adapters.GridToValue(func=np.mean)
            >> fm.adapters.LinearTime()
            >> mhm_csv.inputs["GW_recharge"]
        )

        (  # mHM -> CSV (ETP)
            mhm.outputs["ETP"]
            >> fm.adapters.GridToValue(func=np.mean)
            >> fm.adapters.LinearTime()
            >> mhm_csv.inputs["ETP"]
        )

        (  # OGS -> CSV (head)
            ogs.outputs["head"] >> fm.adapters.LinearTime() >> ogs_csv.inputs["head"]
        )

        (  # OGS -> CSV (base_flow_in)
            mhm.outputs["GW_recharge"]
            >> fm.adapters.IntegrateTime()
            >> fm.adapters.GridToValue(func=np.mean)
            >> fm.adapters.Scale(ogs_csv._step.days)
            >> ogs_csv.inputs["GW_recharge_in"]
        )

        (  # formind -> CSV (LAI)
            formind.outputs["LAI"]
            >> fm.adapters.GridToValue(func=np.mean)
            >> fm.adapters.LinearTime()
            >> formind_csv.inputs["LAI"]
        )

        (  # formind -> CSV (soil_water_in)
            mhm.outputs["soil_water"]
            >> fm.adapters.GridToValue(func=np.mean)
            >> fm.adapters.IntegrateTime()
            >> formind_csv.inputs["soil_water_in"]
        )

    composition.run(datetime(2001, 1, 1))
