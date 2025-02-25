"""Pull-based components for merging multiple inputs into a single output"""
from finam.interfaces import ComponentStatus

from ..data.tools import compatible_units, strip_time
from ..errors import FinamMetaDataError
from ..sdk import CallbackOutput, Component
from ..tools.log_helper import ErrorLogger


class WeightedSum(Component):
    """Pull-based component to merge inputs by weighted sum.

    This component does not have an own time step.
    Execution is triggered by downstream pulls.

    .. code-block:: text

                             +-------------------+
      --> [<custom1>       ] |                   |
      --> [<custom1>_weight] |                   |
      --> [<custom2>       ] | CallbackComponent | [WeightedSum] -->
      --> [<custom2>_weight] |                   |
      --> [....            ] |                   |
                             +-------------------+

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        component = fm.components.WeightedSum(inputs=["A", "B", "C"])

        # ... create and initialize composition

        # comp_1.outputs["Value"] >> component.inputs["A"]
        # comp_1.outputs["Weight"] >> component.inputs["A_weight"]
        # ...

    .. testcode:: constructor
        :hide:

        component.initialize()

    Parameters
    ----------
    inputs : list(str)
        Base input names; will create two inputs for each entry: "<name>" and "<name>_weight"
    start : :class:`datetime <datetime.datetime>`
        Starting time, for initial data exchange
    grid : GridBase or None
        Expected input grid specification; tries to obtain grid specs from inputs if set to None
    """

    def __init__(self, inputs, grid=None):
        super().__init__()
        self._input_names = inputs
        self._grid = grid
        self._units = None
        self._in_data = None
        self._out_data = None
        self._last_update = None

    def _initialize(self):
        for name in self._input_names:
            self.inputs.add(name=name, time=None, grid=self._grid, units=None)
            self.inputs.add(name=name + "_weight", time=None, grid=self._grid, units="")

        self._grid = None

        self.outputs.add(CallbackOutput(callback=self._get_data, name="WeightedSum"))
        self.create_connector(pull_data=list(self.inputs))

    def _connect(self, start_time):
        push_infos = self._check_infos()
        self.try_connect(start_time, push_infos=push_infos)

        if self.status == ComponentStatus.CONNECTED:
            # just to check for all inputs equal
            _push_infos = self._check_infos()

        if self.connector.all_data_pulled:
            self._in_data = self.connector.in_data

    def _check_infos(self):
        push_infos = {}
        for name in self._input_names:
            info = self.connector.in_infos[name]
            if info is not None:
                if not self.connector.infos_pushed["WeightedSum"]:
                    push_infos["WeightedSum"] = info.copy_with()

                self._check_grid(info)
                self._compatible_units(info)

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

    def _compatible_units(self, info):
        if self._units is None:
            self._units = info.units
        else:
            if not compatible_units(self._units, info.units):
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
                value = strip_time(self._in_data[name], self._grid)
                weight = strip_time(self._in_data[name + "_weight"], self._grid)

                if result is None:
                    result = value * weight
                else:
                    result += value * weight

            self._out_data = result
            self._last_update = time

        return self._out_data
