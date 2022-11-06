"""
Driver/scheduler for executing a coupled model composition.

Composition
===========

.. autosummary::
   :toctree: generated

    :noindex: Composition
"""
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from .errors import FinamConnectError, FinamStatusError
from .interfaces import (
    ComponentStatus,
    IComponent,
    IInput,
    IOutput,
    ITimeComponent,
    Loggable,
    NoBranchAdapter,
)
from .adapters.time import ExtrapolateTime
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
        composition.initialize()

        comp_b >> SomeAdapter() >> comp_b

        composition.run(t_max=...)

    Parameters
    ----------
    modules : list of IComponent
        Components in the composition.
    logger_name : str, optional
        Name for the base logger, by default "FINAM"
    print_log : bool, optional
        Whether to print log to stdout, by default True
    log_file : str, None or bool, optional
        Whether to write a log file, by default None
    log_level : int or str, optional
        Logging level, by default logging.INFO
    mpi_rank : int, default 0
        MPI rank of the composition.
    """

    def __init__(
        self,
        modules,
        logger_name="FINAM",
        print_log=True,
        log_file=None,
        log_level=logging.INFO,
        mpi_rank=0,
    ):
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
                log_file = f"./{logger_name}_{time.strftime('%Y-%m-%d_%H-%M-%S')}.log"
            fh = logging.FileHandler(Path(log_file), mode="w")
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)

        for module in modules:
            if not isinstance(module, IComponent):
                with ErrorLogger(self.logger):
                    raise ValueError(
                        "Composition: modules need to be instances of 'IComponent'."
                    )
        self.modules = modules
        self.dependencies = None
        self.is_initialized = False
        self.is_connected = False
        self.mpi_rank = mpi_rank

    def initialize(self):
        """Initialize all modules.

        After the call, module inputs and outputs are available for linking.
        """
        self.logger.debug("init composition")
        if self.is_initialized:
            raise FinamStatusError("Composition was already initialized.")

        for mod in self.modules:
            self._check_status(mod, [ComponentStatus.CREATED])

        for mod in self.modules:
            if is_loggable(mod) and mod.uses_base_logger_name:
                mod.base_logger_name = self.logger_name
            mod.initialize()
            # set logger
            with ErrorLogger(self.logger):
                mod.inputs.set_logger(mod)
                mod.outputs.set_logger(mod)

            self._check_status(mod, [ComponentStatus.INITIALIZED])

        self.is_initialized = True

    def connect(self):
        """Performs the connect and validate phases of the composition

        If this was not called by the user, it is called at the start of :meth:`.run`.
        """
        if self.is_connected:
            raise FinamStatusError("Composition was already connected.")

        self._validate_composition()

        self._connect_components()

        self.logger.debug("validate components")
        for mod in self.modules:
            mod.validate()
            self._check_status(mod, [ComponentStatus.VALIDATED])

        self.dependencies = _find_dependencies(self.modules)

        self.is_connected = True

    def run(self, t_max):
        """Run this composition using the loop-based update strategy.

        Performs the connect phase if it ``connect()`` was not already called.

        Parameters
        ----------
        t_max : datetime.datatime
            Simulation time up to which to simulate.
        """
        if not isinstance(t_max, datetime):
            with ErrorLogger(self.logger):
                raise ValueError("t_max must be of type datetime")

        if not self.is_connected:
            self.connect()

        time_modules = [m for m in self.modules if isinstance(m, ITimeComponent)]

        self.logger.debug("running composition")
        while True:
            if len(time_modules) == 0:
                self.logger.warning(
                    "No ITimeComponent in composition. Nothing to update."
                )
                break

            to_update = min(time_modules, key=lambda m: m.time)
            updated = self._update_recursive(to_update)
            self._check_status(
                updated, [ComponentStatus.VALIDATED, ComponentStatus.UPDATED]
            )

            any_running = False
            for mod in time_modules:
                if mod.time < t_max:
                    any_running = True
                    break

            if not any_running:
                break

        self._finalize_components()
        self._finalize_composition()

    def _update_recursive(self, module, chain=None, target_time=None):
        chain = chain or []
        if module in chain:
            chain.append(module)
            with ErrorLogger(self.logger):
                raise ValueError(
                    f"Circular dependency: {' >> '.join([c.name for c in reversed(chain)])}. "
                    f"You may need to insert an ExtrapolateTime adapter somewhere."
                )

        chain.append(module)

        if isinstance(module, ITimeComponent):
            target_time = module.next_time

        for dep in self.dependencies[module]:
            if isinstance(dep, ITimeComponent):
                if dep.time < target_time:
                    return self._update_recursive(dep, chain)
            else:
                updated = self._update_recursive(dep, chain, target_time)
                if updated is not None:
                    return updated

        if isinstance(module, ITimeComponent):
            module.update()
            return module

        return None

    def _validate_composition(self):
        """Validates the coupling setup by checking for dangling inputs and disallowed branching connections."""
        self.logger.debug("validate composition")
        for mod in self.modules:
            with ErrorLogger(mod.logger if is_loggable(mod) else self.logger):
                for inp in mod.inputs.values():
                    _check_input_connected(mod, inp)
                    _check_dead_links(mod, inp)

                for out in mod.outputs.values():
                    _check_branching(mod, out)

        with ErrorLogger(self.logger):
            _check_missing_modules(self.modules)

    def _connect_components(self):
        self.logger.debug("connect components")
        counter = 0
        while True:
            self.logger.debug("connect iteration %d", counter)
            any_unconnected = False
            any_new_connection = False
            for mod in self.modules:
                if mod.status != ComponentStatus.CONNECTED:
                    mod.connect()
                    self._check_status(
                        mod,
                        [
                            ComponentStatus.CONNECTING,
                            ComponentStatus.CONNECTING_IDLE,
                            ComponentStatus.CONNECTED,
                        ],
                    )
                    if mod.status == ComponentStatus.CONNECTED:
                        any_new_connection = True
                    else:
                        if mod.status == ComponentStatus.CONNECTING:
                            any_new_connection = True

                        any_unconnected = True

            if not any_unconnected:
                break
            if not any_new_connection:
                unconn = [
                    m.name
                    for m in self.modules
                    if m.status != ComponentStatus.CONNECTED
                ]
                with ErrorLogger(self.logger):
                    raise FinamStatusError(
                        f"Circular dependency during initial connect. "
                        f"Unconnected components: [{', '.join(unconn)}]"
                    )

            counter += 1

    def _finalize_components(self):
        self.logger.debug("finalize components")
        for mod in self.modules:
            self._check_status(
                mod,
                [
                    ComponentStatus.VALIDATED,
                    ComponentStatus.UPDATED,
                    ComponentStatus.FINISHED,
                ],
            )
            if (
                isinstance(mod, ITimeComponent)
                and mod.status == ComponentStatus.VALIDATED
            ):
                self.logger.warning(
                    "Time component %s was not updated during this run", mod.name
                )
            mod.finalize()
            self._check_status(mod, [ComponentStatus.FINALIZED])

    def _finalize_composition(self):
        self.logger.debug("finalize composition")
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

    def _check_status(self, module, desired_list):
        if module.status not in desired_list:
            with ErrorLogger(module.logger if is_loggable(module) else self.logger):
                raise FinamStatusError(
                    f"Unexpected model state {module.status} in {module.name}. "
                    f"Expecting one of [{', '.join(map(str, desired_list))}]"
                )


def _check_missing_modules(modules):
    inputs, outputs = _collect_inputs_outputs(modules)

    mod_inputs = {inp for mod in modules for inp in mod.inputs.values()}
    mod_outputs = {out for mod in modules for out in mod.outputs.values()}

    unlinked_inputs = inputs - mod_inputs
    mod_outputs = outputs - mod_outputs

    if len(unlinked_inputs) > 0:
        raise FinamConnectError(
            f"A component was coupled, but not added to this Composition. "
            f"Affected inputs: {[inp.name for inp in unlinked_inputs]}"
        )
    if len(mod_outputs) > 0:
        raise FinamConnectError(
            f"A component was coupled, but not added to this Composition. "
            f"Affected outputs: {[out.name for out in mod_outputs]}"
        )


def _collect_inputs_outputs(modules):
    all_inputs = set()
    all_outputs = set()

    for mod in modules:
        for _, inp in mod.inputs.items():
            while isinstance(inp, IInput):
                inp = inp.get_source()
            all_outputs.add(inp)

        for _, out in mod.outputs.items():
            targets = {out}
            while len(targets) > 0:
                target = targets.pop()
                curr_targets = target.get_targets()
                for target in curr_targets:
                    if isinstance(target, IOutput):
                        targets.add(target)
                    else:
                        all_inputs.add(target)

    return all_inputs, all_outputs


def _check_branching(module, out):
    targets = [(out, False)]

    while len(targets) > 0:
        target, no_branch = targets.pop()
        no_branch = no_branch or isinstance(target, NoBranchAdapter)

        curr_targets = target.get_targets()

        if no_branch and len(curr_targets) > 1:
            raise FinamConnectError(
                f"Disallowed branching of output '{out.name}' for "
                f"module {module.name} ({target.__class__.__name__})"
            )

        for target in curr_targets:
            if isinstance(target, IOutput):
                targets.append((target, no_branch))


def _check_input_connected(module, inp):
    while isinstance(inp, IInput):
        if inp.get_source() is None:
            raise FinamConnectError(
                f"Unconnected input '{inp.name}' for target module {module.name}"
            )
        inp = inp.get_source()


def _check_dead_links(module, inp):
    chain = [inp]
    while isinstance(inp, IInput):
        inp = inp.get_source()
        chain.append(inp)

    first_index = -1
    for i, item in enumerate(reversed(chain)):
        if first_index >= 0 and item.needs_push:
            raise _dead_link_error(module, chain, first_index, i)
        if item.needs_pull:
            first_index = i


def _find_dependencies(modules):
    out_map = {}
    for mod in modules:
        for _, out in mod.outputs.items():
            out_map[out] = mod

    dependencies = {}

    for mod in modules:
        deps = set()
        for _, inp in mod.inputs.items():
            while isinstance(inp, IInput):
                inp = inp.get_source()
                if isinstance(inp, ExtrapolateTime):
                    break
            if not isinstance(inp, ExtrapolateTime):
                comp = out_map[inp]
                deps.add(comp)

        dependencies[mod] = deps

    return dependencies


def _dead_link_error(module, chain, first_index, last_index):
    link_message = ""
    for i, item in enumerate(reversed(chain)):
        link_message += item.name
        if i < len(chain) - 1:
            link_message += (
                " >/> " if i == first_index or i + 1 == last_index else " >> "
            )

    return FinamConnectError(
        f"Dead link detected between "
        f"{chain[0].name} and {str(module)}->{chain[-1].name}:\n"
        f"{link_message}"
    )
