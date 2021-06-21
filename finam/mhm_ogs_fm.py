import random

from adapters import time, base
from core.schedule import Composition
from models import formind, ogs, mhm
from modules import csv_writer, generators

"""
Coupling flow chart, without connections to CSV output:

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
+-----------+ <------------ <Next> -- (LAI) +--------------+
 (base flow)
      |
    <Sum>
      |
      V
+-----------+
| OGS 30d   |
+-----------+
"""

if __name__ == "__main__":
    rng = generators.CallbackGenerator(
        {"precipitation": lambda t: 1.0 if random.uniform(0, 1) < 0.2 else 0.0}, step=1
    )
    mhm = mhm.Mhm(step=7)
    ogs = ogs.Ogs(step=30)
    formind = formind.Formind(step=365)

    precip_csv = csv_writer.CsvWriter(
        path="precip.csv", step=7, inputs=["precipitation"]
    )
    mhm_csv = csv_writer.CsvWriter(
        path="mhm.csv", step=7, inputs=["soil_moisture", "base_flow"]
    )
    ogs_csv = csv_writer.CsvWriter(path="ogs.csv", step=30, inputs=["head"])
    formind_csv = csv_writer.CsvWriter(path="formind.csv", step=365, inputs=["LAI"])

    modules = [rng, mhm, ogs, formind, precip_csv, mhm_csv, ogs_csv, formind_csv]

    for m in modules:
        m.initialize()

    # Model coupling

    (  # RNG -> mHM (precipitation)
        rng.outputs()["precipitation"]
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
        mhm.outputs()["base_flow"]
        >> time.LinearIntegration.sum()
        >> ogs.inputs()["base_flow"]
    )

    # Observer coupling for CSV output

    (  # RNG -> CSV (precipitation)
        rng.outputs()["precipitation"]
        >> time.LinearIntegration.sum()
        >> precip_csv.inputs()["precipitation"]
    )

    (  # mHM -> CSV (soil_moisture)
        mhm.outputs()["soil_moisture"]
        >> time.LinearInterpolation()
        >> mhm_csv.inputs()["soil_moisture"]
    )

    (  # mHM -> CSV (base_flow)
        mhm.outputs()["base_flow"]
        >> time.LinearInterpolation()
        >> mhm_csv.inputs()["base_flow"]
    )

    (  # OGS -> CSV (head)
        ogs.outputs()["head"] >> time.LinearInterpolation() >> ogs_csv.inputs()["head"]
    )

    (  # formind -> CSV (LAI)
        formind.outputs()["LAI"]
        >> time.LinearInterpolation()
        >> formind_csv.inputs()["LAI"]
    )

    composition = Composition(modules)
    composition.run(365 * 25)
