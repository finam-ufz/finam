"""Pull-based for merging multiple inputs into a single output"""
from ..core.interfaces import ComponentStatus
from ..core.sdk import AComponent, CallbackOutput
from ..data.tools import Info, strip_data


class WeightedSum(AComponent):
    """Merges inputs by weighted sum"""

    def __init__(self, inputs, start, grid=None):
        super().__init__()
        self._input_names = inputs
        self._start = start
        self._grid = grid
        self._info = None
        self._in_data = None
        self._out_data = None
        self._last_update = None

    def _initialize(self):
        value_info = None if self._grid is None else Info(grid=self._grid, units=None)
        weight_info = None if self._grid is None else Info(grid=self._grid, units="")
        for name in self._input_names:
            self.inputs.add(name=name, info=value_info)
            self.inputs.add(name=name + "_weight", info=weight_info)

        self.outputs.add(
            CallbackOutput(
                callback=self._get_data, name="WeightedSum", grid=self._grid, units=None
            )
        )
        self.create_connector(
            required_in_data=list(self.inputs),
            required_out_infos=["WeightedSum"],
        )

    def _connect(self):
        in_infos = {}
        if self._grid is None:
            info = self.connector.out_infos["WeightedSum"]
            if info is not None:
                for name in self._input_names:
                    in_infos[name] = info
                    in_infos[name + "_weight"] = Info(grid=info.grid, units="")

        self.try_connect(time=self._start, exchange_infos=in_infos)

        if all((data is not None for _name, data in self.connector.in_data.items())):
            self._in_data = self.connector.in_data

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
