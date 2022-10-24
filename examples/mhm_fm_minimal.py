"""
Coupling setup realizing the first LandTrans coupling step.
"""

import logging
import random
from datetime import datetime, timedelta

from dummy_models import formind, mhm

import finam as fm
from finam.adapters import regrid, time
from finam.modules import generators

if __name__ == "__main__":

    start_date = datetime(2000, 1, 1)

    def precip(t):
        tt = (t - start_date).days
        p = 0.1 * (1 + int(tt / (5 * 365)) % 2)
        return (1.0 if random.uniform(0, 1) < p else 0.0) * fm.UNITS.Unit("mm")

    precipitation = generators.CallbackGenerator(
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
    formind = formind.Formind(
        grid=fm.UniformGrid(
            (11, 7), spacing=(2000.0, 2000.0, 2000.0), data_location="POINTS"
        ),
        start=start_date,
        step=timedelta(days=365),
    )

    composition = fm.Composition([precipitation, mhm, formind], log_level=logging.DEBUG)
    composition.initialize()

    # Model coupling

    (  # RNG -> mHM (precipitation)
        precipitation.outputs["precipitation"]
        >> time.IntegrateTime()
        >> mhm.inputs["precipitation"]
    )

    (  # mHM -> Formind (soil moisture)
        mhm.outputs["soil_water"]
        >> time.IntegrateTime()
        >> regrid.RegridLinear(fill_with_nearest=True)
        >> formind.inputs["soil_water"]
    )

    (  # Formind -> mHM (LAI)
        formind.outputs["LAI"]
        >> time.NextTime()
        >> regrid.RegridLinear(fill_with_nearest=True)
        >> mhm.inputs["LAI"]
    )

    composition.run(datetime(2025, 1, 1))
