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

from .errors import FinamStatusError
from .interfaces import (
    ComponentStatus,
    IAdapter,
    IComponent,
    IInput,
    ITimeComponent,
    Loggable,
    NoBranchAdapter,
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
            to_update.update()
            self._check_status(
                to_update, [ComponentStatus.VALIDATED, ComponentStatus.UPDATED]
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


def _check_branching(module, out):
    targets = [(out, False)]

    while len(targets) > 0:
        target, no_branch = targets.pop()
        no_branch = no_branch or isinstance(target, NoBranchAdapter)

        curr_targets = target.get_targets()

        if no_branch and len(curr_targets) > 1:
            raise ValueError(
                f"Disallowed branching of output '{out.name}' for "
                f"module {module.name} ({target.__class__.__name__})"
            )

        for target in curr_targets:
            if isinstance(target, IAdapter):
                targets.append((target, no_branch))


def _check_input_connected(module, inp):
    while isinstance(inp, IInput):
        if inp.get_source() is None:
            raise ValueError(f"Unconnected input '{inp.name}' for module {module.name}")
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


def _dead_link_error(module, chain, first_index, last_index):
    link_message = ""
    for i, item in enumerate(reversed(chain)):
        link_message += item.name
        if i < len(chain) - 1:
            link_message += (
                " >/> " if i == first_index or i + 1 == last_index else " >> "
            )

    return ValueError(
        f"Dead link detected between "
        f"{chain[0].name} and {str(module)}->{chain[-1].name}:\n"
        f"{link_message}"
    )
