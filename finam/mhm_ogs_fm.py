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

import random
import numpy as np

from adapters import time, base
from core.schedule import Composition
from models import formind, ogs, mhm
from modules import csv_writer, generators
from data.grid import GridSpec


if __name__ == "__main__":

    def precip(t):
        p = 0.1 * (1 + int(t / (5 * 365)) % 2)
        return 1.0 if random.uniform(0, 1) < p else 0.0

    precipitation = generators.CallbackGenerator({"precipitation": precip}, step=1)
    mhm = mhm.Mhm(grid_spec=GridSpec(5, 5, cell_size=1000), step=7)
    ogs = ogs.Ogs(step=30)
    formind = formind.Formind(grid_spec=GridSpec(5, 5, cell_size=1000), step=365)

    mhm_csv = csv_writer.CsvWriter(
        path="mhm.csv",
        step=7,
        inputs=["precip_in", "LAI_in", "soil_moisture", "GW_recharge", "ETP"],
    )
    ogs_csv = csv_writer.CsvWriter(
        path="ogs.csv", step=30, inputs=["GW_recharge_in", "head"]
    )
    formind_csv = csv_writer.CsvWriter(
        path="formind.csv", step=365, inputs=["soil_moisture_in", "LAI"]
    )

    composition = Composition(
        [precipitation, mhm, ogs, formind, mhm_csv, ogs_csv, formind_csv]
    )
    composition.initialize()

    # Model coupling

    (  # RNG -> mHM (precipitation)
        precipitation.outputs()["precipitation"]
        >> time.LinearIntegration.sum()
        >> mhm.inputs()["precipitation"]
    )

    (  # mHM -> Formind (soil moisture)
        mhm.outputs()["soil_moisture"]
        >> time.LinearIntegration.mean()
        >> formind.inputs()["soil_moisture"]
    )

    (  # Formind -> mHM (LAI)
        formind.outputs()["LAI"] >> time.NextValue() >> mhm.inputs()["LAI"]
    )

    (  # mHM -> OGS (base_flow)
        mhm.outputs()["GW_recharge"]
        >> time.LinearIntegration.sum()
        >> ogs.inputs()["GW_recharge"]
    )

    # Observer coupling for CSV output

    (  # RNG -> CSV (precipitation)
        precipitation.outputs()["precipitation"]
        >> time.LinearIntegration.sum()
        >> mhm_csv.inputs()["precip_in"]
    )

    (  # mHM/Formind -> CSV (LAI input)
        formind.outputs()["LAI"]
        >> base.GridToValue(func=np.mean)
        >> time.NextValue()
        >> mhm_csv.inputs()["LAI_in"]
    )

    (  # mHM -> CSV (soil_moisture)
        mhm.outputs()["soil_moisture"]
        >> base.GridToValue(func=np.mean)
        >> time.LinearInterpolation()
        >> mhm_csv.inputs()["soil_moisture"]
    )

    (  # mHM -> CSV (base_flow)
        mhm.outputs()["GW_recharge"]
        >> time.LinearInterpolation()
        >> mhm_csv.inputs()["GW_recharge"]
    )

    (  # mHM -> CSV (ETP)
        mhm.outputs()["ETP"] >> time.LinearInterpolation() >> mhm_csv.inputs()["ETP"]
    )

    (  # OGS -> CSV (head)
        ogs.outputs()["head"] >> time.LinearInterpolation() >> ogs_csv.inputs()["head"]
    )

    (  # OGS -> CSV (base_flow_in)
        mhm.outputs()["GW_recharge"]
        >> time.LinearIntegration.sum()
        >> ogs_csv.inputs()["GW_recharge_in"]
    )

    (  # formind -> CSV (LAI)
        formind.outputs()["LAI"]
        >> base.GridToValue(func=np.mean)
        >> time.LinearInterpolation()
        >> formind_csv.inputs()["LAI"]
    )

    (  # formind -> CSV (soil_moisture_in)
        mhm.outputs()["soil_moisture"]
        >> base.GridToValue(func=np.mean)
        >> time.LinearIntegration.mean()
        >> formind_csv.inputs()["soil_moisture_in"]
    )

    composition.run(365 * 25)
