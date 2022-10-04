"""
Unit conversion adapter.
"""
from ..core.interfaces import FinamMetaDataError
from ..core.sdk import AAdapter
from ..tools.log_helper import LogError


class ConvertUnits(AAdapter):
    """Transforms physical units"""

    def __init__(self):
        super().__init__()
        self.out_units = None

    def get_data(self, time):
        in_data = self.pull_data(time)
        return in_data.pint.to(self.out_units)

    def get_info(self, request_params):
        self.logger.debug("get info")

        info = self.pull_info(request_params)

        if "units" not in request_params:
            with LogError(self.logger):
                raise FinamMetaDataError("Missing target units")

        if self.out_units is not None and self.out_units != request_params["units"]:
            with LogError(self.logger):
                raise FinamMetaDataError(
                    "Target units is already set, new units differ"
                )

        self.out_units = request_params["units"]

        out_info = dict(info)
        out_info["units"] = self.out_units

        return out_info
