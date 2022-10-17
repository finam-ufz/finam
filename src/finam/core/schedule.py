"""
Driver/scheduler for executing a coupled model composition.
"""
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from ..tools.log_helper import LogError, loggable
from .interfaces import (
    ComponentStatus,
    FinamStatusError,
    IAdapter,
    IComponent,
    ITimeComponent,
    Loggable,
    NoBranchAdapter,
)


class Composition(Loggable):
    """A composition of linked components.

    Parameters
    ----------
    modules : Component
        Components in the composition.
    logger_name : str, optional
        Name for the base logger, by default "FINAM"
    print_log : bool, optional
        Whether to print log to stdout, by default True
    log_file : str, None or bool, optional
        Whether to write a log file, by default None
    log_level : int, optional
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
                with LogError(self.logger):
                    raise ValueError(
                        "Composition: modules need to be instances of 'IComponent'."
                    )
        self.modules = modules
        self.mpi_rank = mpi_rank

    def initialize(self):
        """Initialize all modules.

        After the call, module inputs and outputs are available for linking.
        """
        self.logger.debug("init composition")
        for mod in self.modules:
            self._check_status(mod, [ComponentStatus.CREATED])

        for mod in self.modules:
            if loggable(mod) and mod.uses_base_logger_name:
                mod.base_logger_name = self.logger_name
            mod.initialize()
            # set logger
            with LogError(self.logger):
                mod.inputs.set_logger(mod)
                mod.outputs.set_logger(mod)

            self._check_status(mod, [ComponentStatus.INITIALIZED])

    def run(self, t_max):
        """Run this composition using the loop-based update strategy.

        Parameters
        ----------
        t_max : datetime.datatime
            Simulation time up to which to simulate.
        """
        self._validate()

        if not isinstance(t_max, datetime):
            with LogError(self.logger):
                raise ValueError("t_max must be of type datetime")

        self._connect()

        self.logger.debug("validate components")
        for mod in self.modules:
            mod.validate()
            self._check_status(mod, [ComponentStatus.VALIDATED])

        time_modules = [m for m in self.modules if isinstance(m, ITimeComponent)]

        self.logger.debug("running composition")
        while True:
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

        for mod in self.modules:
            self._check_status(mod, [ComponentStatus.UPDATED, ComponentStatus.FINISHED])
            mod.finalize()
            self._check_status(mod, [ComponentStatus.FINALIZED])

        self._finalize()

    def _validate(self):
        """Validates the coupling setup by checking for dangling inputs and disallowed branching connections."""
        self.logger.debug("validate composition")
        for mod in self.modules:
            for (name, inp) in mod.inputs.items():
                par_inp = inp.get_source()
                while True:
                    if par_inp is None:
                        with LogError(self.logger):
                            raise ValueError(
                                f"Unconnected input '{name}' for module {mod.name}"
                            )

                    if not isinstance(par_inp, IAdapter):
                        break

                    par_inp = par_inp.get_source()

            for (name, out) in mod.outputs.items():
                targets = [(out, False)]

                while len(targets) > 0:
                    target, no_branch = targets.pop()
                    no_branch = no_branch or isinstance(target, NoBranchAdapter)

                    curr_targets = target.get_targets()

                    if no_branch and len(curr_targets) > 1:
                        with LogError(self.logger):
                            raise ValueError(
                                f"Disallowed branching of output '{name}' for "
                                f"module {mod.name} ({target.__class__.__name__})"
                            )

                    for target in curr_targets:
                        if isinstance(target, IAdapter):
                            targets.append((target, no_branch))

    def _connect(self):
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
                with LogError(self.logger):
                    raise FinamStatusError(
                        f"Circular dependency during initial connect. "
                        f"Unconnected components: [{', '.join(unconn)}]"
                    )

            counter += 1

    def _finalize(self):
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
        """Whether this class has a 'base_logger_name' attribute."""
        return False

    def _check_status(self, module, desired_list):
        if module.status not in desired_list:
            with LogError(module.logger if loggable(module) else self.logger):
                raise FinamStatusError(
                    f"Unexpected model state {module.status} in {module.name}. "
                    f"Expecting one of [{', '.join(map(str, desired_list))}]"
                )
