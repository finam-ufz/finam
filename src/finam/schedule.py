"""
Driver/scheduler for executing a coupled model composition.

Composition
===========

.. autosummary::
   :toctree: generated

    :noindex: Composition
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from time import strftime

from ._version import __version__
from .errors import (
    FinamCircularCouplingError,
    FinamConnectError,
    FinamStatusError,
    FinamTimeError,
)
from .interfaces import (
    ComponentStatus,
    IAdapter,
    IComponent,
    IInput,
    IOutput,
    ITimeComponent,
    ITimeDelayAdapter,
    Loggable,
    NoBranchAdapter,
    NoDependencyAdapter,
)
from .tools.log_helper import ErrorLogger, is_loggable


class Composition(Loggable):
    """A composition of linked components.

    Manages initialization, initial connection and update schedule of components.

    See :doc:`/finam-book/usage/coupling_scripts` for usage details.

    Examples
    --------

    .. code-block:: Python

        comp_a = SomeComponent(...)
        comp_b = AnotherComponent(...)

        composition = Composition([comp_a, comp_b])

        comp_b.outputs["Out"] >> SomeAdapter() >> comp_b.inputs["In"]

        composition.run(end_time=...)

    Parameters
    ----------
    components : list of IComponent
        Components in the composition.
    logger_name : str, optional
        Name for the base logger, by default "FINAM"
    print_log : bool, optional
        Whether to print log to stdout, by default True
    log_file : str, None or bool, optional
        Whether to write a log file, by default None
    log_level : int or str, optional
        Logging level, by default logging.INFO
    slot_memory_limit : int, optional
        Memory limit per output and adapter data, in bytes.
        When the limit is exceeded, data is stored to disk under the path of ``slot_memory_location``.
        Default: no limit (``None``).
    slot_memory_location : str, optional
        Location for storing data when exceeding ``slot_memory_limit``.
        Default: "temp".
    """

    def __init__(
        self,
        components,
        logger_name="FINAM",
        print_log=True,
        log_file=None,
        log_level=logging.INFO,
        slot_memory_limit=None,
        slot_memory_location="temp",
    ):
        super().__init__()
        # setup logger
        self._logger_name = logger_name
        self.logger.setLevel(log_level)
        # set log format
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)-36s - %(name)s"
        )
        # setup log output
        if print_log:
            sh = logging.StreamHandler(sys.stdout)
            sh.setFormatter(formatter)
            self.logger.addHandler(sh)
        if log_file:
            # for log_file=True use a default name
            if isinstance(log_file, bool):
                log_file = f"./{logger_name}_{strftime('%Y-%m-%d_%H-%M-%S')}.log"
            fh = logging.FileHandler(Path(log_file), mode="w")
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)

        for comp in components:
            if not isinstance(comp, IComponent):
                with ErrorLogger(self.logger):
                    raise ValueError(
                        "Composition: components need to be instances of 'IComponent'."
                    )
        self._components = components
        self._adapters = set()
        self._dependencies = None
        self._input_owners = None
        self._output_owners = None
        self._is_connected = False

        self._time_frame = (None, None)

        self._slot_memory_limit = slot_memory_limit
        self._slot_memory_location = slot_memory_location

        # initialize
        self.logger.info("init composition")

        for comp in self._components:
            self._check_status(comp, [ComponentStatus.CREATED])

        if self._slot_memory_location is not None:
            os.makedirs(self._slot_memory_location, exist_ok=True)

        for comp in self._components:
            if is_loggable(comp) and comp.uses_base_logger_name:
                comp.base_logger_name = self.logger_name
            comp.initialize()
            # set logger
            with ErrorLogger(self.logger):
                comp.inputs.set_logger(comp)
                comp.outputs.set_logger(comp)

            for _, out in comp.outputs.items():
                if out.memory_limit is None:
                    out.memory_limit = self._slot_memory_limit
                if out.memory_location is None:
                    out.memory_location = self._slot_memory_location

            self._check_status(comp, [ComponentStatus.INITIALIZED])

    def connect(self, start_time=None):
        """Performs the connect and validate phases of the composition

        If this was not called by the user, it is called at the start of :meth:`.run`.

        Parameters
        ----------
        start_time : :class:`datetime <datetime.datetime>`, optional
            Starting time of the composition.
            If provided, it should be the starting time of the earliest component.
            If not provided, the composition tries to determine the starting time automatically.
        """
        if self._is_connected:
            raise FinamStatusError("Composition was already connected.")

        time_components = [m for m in self._components if isinstance(m, ITimeComponent)]

        with ErrorLogger(self.logger):
            if len(time_components) == 0:
                if start_time is not None:
                    raise ValueError(
                        "start must be None for a composition without time components"
                    )
            else:
                if start_time is None:
                    start_time = _get_start_time(time_components)
                if not isinstance(start_time, datetime):
                    raise ValueError(
                        "start must be of type datetime for a composition with time components"
                    )

        self._collect_adapters()
        self._validate_composition()

        for ada in self._adapters:
            if ada.memory_limit is None:
                ada.memory_limit = self._slot_memory_limit
            if ada.memory_location is None:
                ada.memory_location = self._slot_memory_location

        self._connect_components(start_time)

        self.logger.info("validate components")
        for comp in self._components:
            comp.validate()
            self._check_status(comp, [ComponentStatus.VALIDATED])

        self._output_owners = _map_outputs(self._components)
        self._input_owners = _map_inputs(self._components)

        self._is_connected = True
        self._time_frame = (start_time, None)

    def run(self, start_time=None, end_time=None):
        """Run this composition using the loop-based update strategy.

        Performs the connect phase if it ``connect()`` was not already called.

        Parameters
        ----------
        start_time : :class:`datetime <datetime.datetime>`, optional
            Starting time of the composition.
            If provided, it should be the starting time of the earliest component.
            If not provided, the composition tries to determine the starting time automatically.
            Ignored if :meth:`.connect` was already called.
        end_time : :class:`datetime <datetime.datetime>`, optional
            Simulation time up to which to simulate.
            Should be ``None`` if no components with time are present.
        """
        time_components = [m for m in self._components if isinstance(m, ITimeComponent)]

        with ErrorLogger(self.logger):
            if len(time_components) == 0:
                if end_time is not None:
                    raise ValueError(
                        "end must be None for a composition without time components"
                    )
            else:
                if not isinstance(end_time, datetime):
                    raise ValueError(
                        "end must be of type datetime for a composition with time components"
                    )

        if not self._is_connected:
            self.connect(start_time)

        self._time_frame = (self._time_frame[0], end_time)

        self.logger.info("run composition")
        while len(time_components) > 0:
            sort_components = list(time_components)
            sort_components.sort(key=lambda m: m.time)
            to_update = sort_components[0]
            updated = self._update_recursive(to_update)
            self._check_status(
                updated, [ComponentStatus.VALIDATED, ComponentStatus.UPDATED]
            )

            any_running = False
            for comp in time_components:
                if comp.status != ComponentStatus.FINISHED and comp.time < end_time:
                    any_running = True
                    break

            if not any_running:
                break

        self._finalize_components()
        self._finalize_composition()

    def _update_recursive(self, comp, chain=None, target_time=None):
        chain = chain or {}
        if comp in chain:
            with ErrorLogger(self.logger):
                joined = " >> ".join(
                    [
                        f"({'*' if delayed else ''}{t or '-'}) {c.name}"
                        for c, (t, delayed) in reversed(chain.items())
                    ]
                )
                raise FinamCircularCouplingError(
                    f"Unresolved circular coupling:\n"
                    f"{comp.name} >> "
                    f"{joined}\n"
                    f"(Deltas are time lags of upstream components, * denotes delayed links)\n"
                    f"You may need to insert a NoDependencyAdapter or ITimeDelayAdapter subclass somewhere, "
                    f"or increase the adapter's delay."
                )

        chain[comp] = None

        if isinstance(comp, ITimeComponent):
            target_time = comp.next_time

        deps = _find_dependencies(comp, self._output_owners, target_time)

        for dep, (local_time, delayed) in deps.items():
            c = self._output_owners[dep]
            if isinstance(c, ITimeComponent):
                if dep.time < local_time:
                    chain[comp] = (local_time - dep.time, delayed)
                    return self._update_recursive(c, chain)
            else:
                updated = self._update_recursive(c, chain, local_time)
                if updated is not None:
                    return updated

        if isinstance(comp, ITimeComponent):
            if comp.status != ComponentStatus.FINISHED:
                comp.update()
            else:
                raise FinamTimeError(
                    f"Can't update dependency component {comp.name}, as it is already finished."
                )
            return comp

        return None

    def _collect_adapters(self):
        for comp in self._components:
            for _, inp in comp.inputs.items():
                _collect_adapters_input(inp, self._adapters)
            for _, out in comp.outputs.items():
                _collect_adapters_output(out, self._adapters)

    def _validate_composition(self):
        """Validates the coupling setup by checking for dangling inputs and disallowed branching connections."""
        self.logger.info("validate composition")
        for comp in self._components:
            with ErrorLogger(comp.logger if is_loggable(comp) else self.logger):
                for inp in comp.inputs.values():
                    _check_input_connected(comp, inp)
                    _check_dead_links(comp, inp)

                for out in comp.outputs.values():
                    _check_branching(comp, out)

        with ErrorLogger(self.logger):
            _check_missing_components(self._components)

    def _connect_components(self, time):
        self.logger.info("connect components")
        counter = 0
        while True:
            self.logger.debug("connect iteration %d", counter)
            any_unconnected = False
            any_new_connection = False
            for comp in self._components:
                if comp.status != ComponentStatus.CONNECTED:
                    comp.connect(time)
                    self._check_status(
                        comp,
                        [
                            ComponentStatus.CONNECTING,
                            ComponentStatus.CONNECTING_IDLE,
                            ComponentStatus.CONNECTED,
                        ],
                    )
                    if comp.status == ComponentStatus.CONNECTED:
                        any_new_connection = True
                    else:
                        if comp.status == ComponentStatus.CONNECTING:
                            any_new_connection = True

                        any_unconnected = True

            if not any_unconnected:
                break
            if not any_new_connection:
                unconn = [
                    m.name
                    for m in self._components
                    if m.status != ComponentStatus.CONNECTED
                ]
                with ErrorLogger(self.logger):
                    raise FinamCircularCouplingError(
                        f"Unresolved circular coupling during initial connect. "
                        f"Unconnected components: [{', '.join(unconn)}]"
                    )

            counter += 1

    def _finalize_components(self):
        self.logger.info("finalize components")
        for comp in self._components:
            self._check_status(
                comp,
                [
                    ComponentStatus.VALIDATED,
                    ComponentStatus.UPDATED,
                    ComponentStatus.FINISHED,
                ],
            )
            if (
                isinstance(comp, ITimeComponent)
                and comp.status == ComponentStatus.VALIDATED
            ):
                self.logger.warning(
                    "Time component %s was not updated during this run", comp.name
                )
            comp.finalize()
            self._check_status(comp, [ComponentStatus.FINALIZED])

        for ada in self._adapters:
            ada.finalize()

    def _finalize_composition(self):
        self.logger.info("finalize composition")
        handlers = self.logger.handlers[:]
        for handler in handlers:
            self.logger.removeHandler(handler)
            handler.close()

    @property
    def logger_name(self):
        """Logger name for the composition."""
        return self._logger_name

    @property
    def uses_base_logger_name(self):
        """Whether this class has a ``base_logger_name`` attribute. False."""
        return False

    def _check_status(self, comp, desired_list):
        if comp.status not in desired_list:
            with ErrorLogger(comp.logger if is_loggable(comp) else self.logger):
                raise FinamStatusError(
                    f"Unexpected component state {comp.status} in {comp.name}. "
                    f"Expecting one of [{', '.join(map(str, desired_list))}]"
                )

    @property
    def metadata(self):
        """
        Meta data for all components and adapters.
        Can only be used after ``connect``.

        Returns
        -------
        dict
            A ``dict`` with the following metadata keys:
              - ``components`` - A `dict` containing metadata for all components.
                Individual entries are generated by :attr:`Component.metadata`
              - ``adapters`` - A `dict` containing metadata for all adapters.
                Individual entries are generated by :attr:`Adapter.metadata`
              - ``links`` - A list of all coupling connections
              - ``time_frame`` - A list of two items: simulation start and end time

            Component and adapter sub-dictionaries use keys like ``name@id``.

        Raises
        ------
        FinamStatusError
            Raises the error if ``connect`` was not called.
        """
        if not self._is_connected:
            with ErrorLogger(self.logger):
                raise FinamStatusError(
                    "can't get meta data for a composition before connect was called"
                )

        comps = {}
        for comp in self._components:
            key = f"{comp.name}@{id(comp)}"
            comps[key] = comp.metadata

        adas = {}
        for ada in self._adapters:
            key = f"{ada.name}@{id(ada)}"
            adas[key] = ada.metadata

        links = []

        for comp in self._components:
            for out_name, out in comp.outputs.items():
                for target in out.targets:
                    if isinstance(target, IAdapter):
                        to = {
                            "adapter": f"{target.name}@{id(target)}",
                        }
                    else:
                        owner = self._input_owners[target]
                        to = {
                            "component": f"{owner.name}@{id(owner)}",
                            "input": target.name,
                        }

                    links.append(
                        {
                            "from": {
                                "component": f"{comp.name}@{id(comp)}",
                                "output": out_name,
                            },
                            "to": to,
                        }
                    )

        for ada in self._adapters:
            for target in ada.targets:
                if isinstance(target, IAdapter):
                    to = {
                        "adapter": f"{target.name}@{id(target)}",
                    }
                else:
                    owner = self._input_owners[target]
                    to = {
                        "component": f"{owner.name}@{id(owner)}",
                        "input": target.name,
                    }

                links.append(
                    {
                        "from": {
                            "adapter": f"{ada.name}@{id(ada)}",
                        },
                        "to": to,
                    }
                )

        return {
            "version": __version__,
            "components": comps,
            "adapters": adas,
            "links": links,
            "time_frame": list(self._time_frame),
        }


def _collect_adapters_input(inp: IInput, out_adapters: set):
    src = inp.source
    if src is None:
        return

    if isinstance(src, IAdapter):
        out_adapters.add(src)
        _collect_adapters_input(src, out_adapters)


def _collect_adapters_output(out: IOutput, out_adapters: set):
    for trg in out.targets:
        if isinstance(trg, IAdapter):
            out_adapters.add(trg)
            _collect_adapters_output(trg, out_adapters)


def _get_start_time(time_components):
    t_min = None
    for comp in time_components:
        if comp.time is not None:
            if t_min is None or comp.time < t_min:
                t_min = comp.time
    if t_min is None:
        raise ValueError(
            "Unable to determine starting time of the composition."
            "Please provide a starting time in ``run()`` or ``connect()``"
        )
    return t_min


def _check_missing_components(components):
    inputs, outputs = _collect_inputs_outputs(components)

    comp_inputs = {inp for comp in components for inp in comp.inputs.values()}
    comp_outputs = {out for comp in components for out in comp.outputs.values()}

    unlinked_inputs = inputs - comp_inputs
    comp_outputs = outputs - comp_outputs

    if len(unlinked_inputs) > 0:
        raise FinamConnectError(
            f"A component was coupled, but not added to this Composition. "
            f"Affected inputs: {[inp.name for inp in unlinked_inputs]}"
        )
    if len(comp_outputs) > 0:
        raise FinamConnectError(
            f"A component was coupled, but not added to this Composition. "
            f"Affected outputs: {[out.name for out in comp_outputs]}"
        )


def _collect_inputs_outputs(components):
    all_inputs = set()
    all_outputs = set()

    for comp in components:
        for _, inp in comp.inputs.items():
            while isinstance(inp, IInput):
                inp = inp.source
            all_outputs.add(inp)

        for _, out in comp.outputs.items():
            targets = {out}
            while len(targets) > 0:
                target = targets.pop()
                curr_targets = target.targets
                for target in curr_targets:
                    if isinstance(target, IOutput):
                        targets.add(target)
                    else:
                        all_inputs.add(target)

    return all_inputs, all_outputs


def _check_branching(comp, out):
    targets = [(out, False)]

    while len(targets) > 0:
        target, no_branch = targets.pop()
        no_branch = no_branch or isinstance(target, NoBranchAdapter)

        curr_targets = target.targets

        if no_branch and len(curr_targets) > 1:
            raise FinamConnectError(
                f"Disallowed branching of output '{out.name}' for "
                f"component {comp.name} ({target.__class__.__name__})"
            )

        for target in curr_targets:
            if isinstance(target, IOutput):
                targets.append((target, no_branch))


def _check_input_connected(comp, inp):
    static = inp.is_static

    while isinstance(inp, IInput):
        if inp.source is None:
            raise FinamConnectError(
                f"Unconnected input '{inp.name}' for target component {comp.name}"
            )
        inp = inp.source

    if static and not inp.is_static:
        raise FinamConnectError("Can't connect a static input to a non-static output.")


def _check_dead_links(comp, inp):
    chain = [inp]
    while isinstance(inp, IInput):
        inp = inp.source
        chain.append(inp)

    first_index = -1
    for i, item in enumerate(reversed(chain)):
        if first_index >= 0 and item.needs_push:
            raise _dead_link_error(comp, chain, first_index, i)
        if item.needs_pull:
            first_index = i


def _map_outputs(components):
    out_map = {}
    for comp in components:
        for _, out in comp.outputs.items():
            out_map[out] = comp
    return out_map


def _map_inputs(components):
    in_map = {}
    for comp in components:
        for _, inp in comp.inputs.items():
            in_map[inp] = comp
    return in_map


def _find_dependencies(component, output_owners, target_time):
    deps = {}
    for _, inp in component.inputs.items():
        local_time = target_time
        delayed = False
        while isinstance(inp, IInput):
            inp = inp.source
            if isinstance(inp, NoDependencyAdapter):
                break
            if isinstance(inp, ITimeDelayAdapter):
                local_time = inp.with_delay(target_time)
                delayed = True

        if not isinstance(inp, NoDependencyAdapter) and not inp.is_static:
            comp = output_owners[inp]
            if not isinstance(comp, ITimeComponent) or (
                isinstance(comp, ITimeComponent) and inp.time < local_time
            ):
                if inp not in deps or local_time > deps[inp][0]:
                    deps[inp] = (local_time, delayed)

    return deps


def _dead_link_error(component, chain, first_index, last_index):
    link_message = ""
    for i, item in enumerate(reversed(chain)):
        link_message += item.name
        if i < len(chain) - 1:
            link_message += (
                " >/> " if i == first_index or i + 1 == last_index else " >> "
            )

    return FinamConnectError(
        f"Dead link detected between "
        f"{chain[0].name} and {str(component)}->{chain[-1].name}:\n"
        f"{link_message}"
    )
