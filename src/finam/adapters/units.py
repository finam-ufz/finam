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

    def get_info(self, info):
        self.logger.debug("get info")

        in_info = self.exchange_info(info)

        if "units" not in info:
            with LogError(self.logger):
                raise FinamMetaDataError("Missing target units")

        if self.out_units is not None and self.out_units != info["units"]:
            with LogError(self.logger):
                raise FinamMetaDataError(
                    "Target units is already set, new units differ"
                )

        self.out_units = info["units"]

        out_info = dict(in_info)
        out_info["units"] = self.out_units

        return out_info
