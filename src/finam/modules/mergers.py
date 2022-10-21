"""Pull-based for merging multiple inputs into a single output"""
from finam.interfaces import ComponentStatus, FinamMetaDataError

from ..data.tools import check_units, strip_data
from ..sdk import CallbackOutput, Component
from ..tools.log_helper import ErrorLogger


class WeightedSum(Component):
    """Merges inputs by weighted sum

    Parameters
    ----------
    inputs : list(str)
        Base input names; will create two inputs for each entry: "<name>" and "<name>_weight"
    start : datetime.datetime
        Starting time, for initial data exchange
    grid : GridBase or None
        Expected input grid specification; tries to obtain grid specs from inputs if set to None
    """

    def __init__(self, inputs, start, grid=None):
        super().__init__()
        self._input_names = inputs
        self._start = start
        self._grid = grid
        self._units = None
        self._in_data = None
        self._out_data = None
        self._last_update = None

    def _initialize(self):
        for name in self._input_names:
            self.inputs.add(name=name, grid=self._grid, units=None)
            self.inputs.add(name=name + "_weight", grid=self._grid, units="")

        self._grid = None

        self.outputs.add(CallbackOutput(callback=self._get_data, name="WeightedSum"))
        self.create_connector(required_in_data=list(self.inputs))

    def _connect(self):
        push_infos = self._check_infos()
        self.try_connect(time=self._start, push_infos=push_infos)

        if self.status == ComponentStatus.CONNECTED:
            # just to check for all inputs equal
            _push_infos = self._check_infos()

        if all((data is not None for _name, data in self.connector.in_data.items())):
            self._in_data = self.connector.in_data

    def _check_infos(self):
        push_infos = {}
        for name in self._input_names:
            info = self.connector.in_infos[name]
            if info is not None:
                if not self.connector.infos_pushed["WeightedSum"]:
                    push_infos["WeightedSum"] = info.copy_with()

                self._check_grid(info)
                self._check_units(info)

            weight_info = self.connector.in_infos[name + "_weight"]
            if weight_info is not None:
                self._check_grid(weight_info)

        return push_infos

    def _check_grid(self, info):
        if self._grid is None:
            self._grid = info.grid
        else:
            if self._grid != info.grid:
                with ErrorLogger(self.logger):
                    raise FinamMetaDataError("All inputs must have the same grid.")

    def _check_units(self, info):
        if "units" in info.meta:
            if self._units is None:
                self._units = info.units
            else:
                if not check_units(self._units, info.units):
                    with ErrorLogger(self.logger):
                        raise FinamMetaDataError(
                            "All value inputs must have the same dimensions."
                        )

    def _validate(self):
        pass

    def _update(self):
        pass

    def _finalize(self):
        pass

    def _get_data(self, _caller, time):
        if self._in_data is None:
            return None

        if time != self._last_update:
            if self.status == ComponentStatus.VALIDATED:
                self._in_data = {
                    name: inp.pull_data(time) for name, inp in self.inputs.items()
                }

            result = None

            for name in self._input_names:
                value = strip_data(self._in_data[name])
                weight = strip_data(self._in_data[name + "_weight"])

                if result is None:
                    result = value * weight
                else:
                    result += value * weight

            self._out_data = result
            self._last_update = time

        return self._out_data
