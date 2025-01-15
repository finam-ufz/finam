"""Components for controlling data flow"""
import datetime as dt

from ..data.grid_spec import NoGrid
from ..errors import FinamMetaDataError
from ..sdk import TimeComponent
from ..tools.connect_helper import FromInput, FromOutput
from ..tools.log_helper import ErrorLogger


class TimeTrigger(TimeComponent):
    """Component to forward data in regular time intervals.

    Can be used to enable coupling of pull-based source and push-based target components,
    that would not work due to the dead link otherwise.

    .. code-block:: text

                 +-------------+
                 |             |
        --> [In] | TimeTrigger | [Out] -->
                 |             |
                 +-------------+

    The typical usage is shown in the example below.
    Here, the component will retrieve metadata from it's input,
    for all metadata fields that are ```None``.
    Because ``out_info`` is ``None``, the received metadata is then forwarded to the output.

    The same mechanism can be used in the other direction, by specifying ``out_info``
    but not ``in_info`` in the method call.

    Examples
    --------

    .. testcode:: constructor

        import datetime as dt
        import finam as fm

        component = fm.components.TimeTrigger(
            in_info=fm.Info(time=None, grid=None, units=None),
            start=dt.datetime(2000, 1, 1),
            step=dt.timedelta(days=1),
        )

    .. testcode:: constructor
        :hide:

        component.initialize()

    Parameters
    ----------
    start : :class:`datetime <datetime.datetime>`
        Starting time. Can be ``None`` to retrieve it from linked components.
        See parameter ``start_from_input`` for details.
    step : :class:`timedelta <datetime.timedelta>` or :class:`relativedelta <dateutil.relativedelta.relativedelta>`
        The component's time step
    in_info : :class:`.Info`, optional
        Input info, optional. However, one of ``in_info`` or ``out_info`` must be given.
        ``time`` is ignored and can be set to ``None``.
    out_info : :class:`.Info`, optional
        Output info, optional. However, one of ``in_info`` or ``out_info`` must be given.
        ``time`` is ignored and can be set to ``None``.
    start_from_input : bool, optional
        Whether to get the starting time from the input, instead of the output. Default ``True``.

        If ``start`` is ``None``, the component can try to retrieve the starting time either
        from the input or from the output.
        The respective linked component should have an internal time step.
        If both linked components have no time step, ``start`` must be given.
    """

    def __init__(self, start, step, in_info=None, out_info=None, start_from_input=True):
        super().__init__()

        self._ini_in_info = in_info
        self._ini_out_info = out_info

        self._start = start
        if self._start is not None:
            self.time = self._start

        self._step = step
        self._start_from_input = start_from_input

    def _next_time(self):
        return self.time + self._step

    def _initialize(self):
        with ErrorLogger(self.logger):
            if self._ini_in_info is None and self._ini_out_info is None:
                raise FinamMetaDataError(
                    "At least one of input or output info must be given."
                )
            if self._start is None:
                if self._start_from_input and self._ini_in_info is None:
                    raise FinamMetaDataError(
                        "Can't get starting time from the input without an input info."
                    )
                if not self._start_from_input and self._ini_out_info is None:
                    raise FinamMetaDataError(
                        "Can't get starting time from the output without an output info."
                    )

        if self._ini_in_info is not None:
            self._ini_in_info.time = self._start
        if self._ini_out_info is not None:
            self._ini_out_info.time = self._start

        in_info_rules = {}
        out_info_rules = {}

        if self._start is None:
            if self._start_from_input:
                self.inputs.add(name="In", info=self._ini_in_info)
                self.outputs.add(name="Out")
                out_info_rules["Out"] = [FromInput("In")]
            else:
                self.inputs.add(name="In")
                self.outputs.add(name="Out", info=self._ini_out_info)
                in_info_rules["In"] = [FromOutput("Out")]
        else:
            self.inputs.add(name="In", info=self._ini_in_info)
            self.outputs.add(name="Out", info=self._ini_out_info)
            if self._ini_out_info is None:
                out_info_rules["Out"] = [FromInput("In")]
            if self._ini_in_info is None:
                in_info_rules["In"] = [FromOutput("Out")]

        self.create_connector(
            pull_data=["In"],
            in_info_rules=in_info_rules,
            out_info_rules=out_info_rules,
        )

    def _connect(self, start_time):
        out_data = {}
        if (
            not self.connector.data_pushed["Out"]
            and self.connector.in_data["In"] is not None
        ):
            out_data["Out"] = self.connector.in_data["In"]

        self.try_connect(start_time, push_data=out_data)

        in_info = self.connector.in_infos["In"]
        if in_info is not None:
            self.time = in_info.time

    def _validate(self):
        pass

    def _update(self):
        self.time += self._step

        data = self.inputs["In"].pull_data(self.time)
        self.outputs["Out"].push_data(data, self.time)

    def _finalize(self):
        pass


class UserControl(TimeComponent):

    """Component to allow users to step a simulation.

    Prompts for input on the console.

    Users can just press ENTER to proceed by one step, or enter a target time in ISO format.

    .. code-block:: text

                 +-------------+
                 |             |
                 | UserControl | [Counter] -->
                 |             |
                 +-------------+

    Examples
    --------

    .. testcode:: constructor

        import datetime as dt
        import finam as fm

        component = fm.components.UserControl(
            start=dt.datetime(2000, 1, 1),
            step=dt.timedelta(days=1),
        )

    .. testcode:: constructor
        :hide:

        component.initialize()

    .. |relativedelta| replace:: :class:`relativedelta <dateutil.relativedelta.relativedelta>`

    Parameters
    ----------
    start : :class:`datetime <datetime.datetime>`
        Starting time. Can be ``None`` to retrieve it from linked components.
    step : :class:`timedelta <datetime.timedelta>` or |relativedelta|, optional
        The component's time step. Default 1 day.
    """

    def __init__(self, start, step=dt.timedelta(days=1)):
        super().__init__()

        self.time = start
        self.step = step
        self._counter = 0

    def _next_time(self):
        return None

    def _initialize(self):
        self.outputs.add(name="Counter", time=self.time, grid=NoGrid())

        self.create_connector()

    def _connect(self, start_time):
        push_data = {}
        if self.connector.data_required["Counter"]:
            push_data["Counter"] = self._counter

        self.try_connect(start_time, push_data=push_data)

    def _validate(self):
        pass

    def _update(self):
        self._counter += 1
        self._prompt()

    def _prompt(self):
        run_until = None

        inp = input(f"Time: {self.time} - Run until (ENTER to step): ")
        if inp == "":
            run_until = self.time + self.step
        else:
            try:
                run_until = dt.datetime.fromisoformat(inp)
            except ValueError:
                print(f"Not a time: '{inp}'.")

        if run_until is not None:
            self.time = run_until
            self.outputs["Counter"].push_data(self._counter, self.time)

    def _finalize(self):
        pass
