"""
Coupling setup realizing the first LandTrans coupling step.
"""

import random
from datetime import datetime, timedelta

from dummy_models import formind, mhm

from finam.adapters import time
from finam.core.schedule import Composition
from finam.data.grid import GridSpec
from finam.modules import generators

if __name__ == "__main__":

    start_date = datetime(2000, 1, 1)

    def precip(t):
        tt = (t - start_date).days
        p = 0.1 * (1 + int(tt / (5 * 365)) % 2)
        return 1.0 if random.uniform(0, 1) < p else 0.0

    precipitation = generators.CallbackGenerator(
        {"precipitation": precip}, start=start_date, step=timedelta(days=1)
    )
    mhm = mhm.Mhm(
        grid_spec=GridSpec(5, 5, cell_size=1000),
        start=start_date,
        step=timedelta(days=7),
    )
    formind = formind.Formind(
        grid_spec=GridSpec(5, 5, cell_size=1000),
        start=start_date,
        step=timedelta(days=365),
    )

    composition = Composition([precipitation, mhm, formind])
    composition.initialize()

    # Model coupling

    (  # RNG -> mHM (precipitation)
        precipitation.outputs["precipitation"]
        >> time.LinearIntegration()
        >> mhm.inputs["precipitation"]
    )

    (  # mHM -> Formind (soil moisture)
        mhm.outputs["soil_water"]
        >> time.LinearIntegration()
        >> formind.inputs["soil_water"]
    )

    (  # Formind -> mHM (LAI)
        formind.outputs["LAI"] >> time.NextValue() >> mhm.inputs["LAI"]
    )

    composition.run(datetime(2025, 1, 1))
