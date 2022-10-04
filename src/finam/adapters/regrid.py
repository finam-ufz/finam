"""
Basic linear and NN regridding adapter.
"""
import numpy as np
import xarray as xr
from scipy.interpolate import RegularGridInterpolator as RDI

from ..core.interfaces import FinamMetaDataError
from ..core.sdk import AAdapter
from ..tools.log_helper import LogError


class Regrid(AAdapter):
    """Regrid data between two grid specifications"""

    def __init__(self, method="linear"):
        super().__init__()
        self.method = method
        self.in_spec = None
        self.out_spec = None

    def get_data(self, time):
        in_data = self.pull_data(time)
        interp = RDI(
            points=self.in_spec.data_axes,
            values=in_data.pint.magnitude,
            method=self.method,
        )

        arr = np.reshape(
            interp(self.out_spec.data_points),
            newshape=self.out_spec.data_shape,
            order=self.in_spec.order,
        )

        out_data = xr.DataArray(arr).pint.quantify(in_data.pint.units)

        return out_data

    def get_info(self, request_params):
        self.logger.debug("get info")

        info = self.pull_info(request_params)

        if "grid_spec" not in request_params:
            with LogError(self.logger):
                raise FinamMetaDataError("Missing target grid specification")
        if "grid_spec" not in info:
            with LogError(self.logger):
                raise FinamMetaDataError("Missing source grid specification")

        if self.out_spec is not None and self.out_spec != request_params["grid_spec"]:
            with LogError(self.logger):
                raise FinamMetaDataError(
                    "Target grid specification is already set, new specs differ"
                )

        self.in_spec = info["grid_spec"]
        self.out_spec = request_params["grid_spec"]

        out_info = dict(info)
        out_info["grid_spec"] = self.out_spec

        return out_info
