"""
Driver/scheduler for executing a coupled model composition.
"""
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from .interfaces import (
    IAdapter,
    IComponent,
    IMpiComponent,
    ITimeComponent,
    NoBranchAdapter,
)


class Composition:
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
        log = logging.getLogger(name=self.logger_name)
        log.setLevel(log_level)
        # set log format
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        # setup log output
        if print_log:
            sh = logging.StreamHandler(sys.stdout)
            sh.setFormatter(formatter)
            log.addHandler(sh)
        if log_file:
            # for log_file=True use a default name
            if isinstance(log_file, bool):
                log_file = f"./FINAM_{time.strftime('%Y-%m-%d_%H-%M-%S')}.log"
            fh = logging.FileHandler(Path(log_file), mode="w")
            fh.setFormatter(formatter)
            log.addHandler(fh)
        for module in modules:
            try:
                if not isinstance(module, IComponent):
                    raise ValueError(
                        "Composition: modules need to be instances of 'IComponent'."
                    )
            except ValueError as err:
                self.logger.exception(err)
                raise

        self.modules = modules
        self.mpi_rank = mpi_rank

    def run_mpi(self):
        """Run MPI processes is not on rank 0.

        Returns
        -------
        bool
            True if on rank 0, false otherwise.
        """
        self.logger.debug("run mpi composition")
        if self.mpi_rank == 0:
            return True

        for mod in self.modules:
            if isinstance(mod, IMpiComponent):
                mod.run_mpi()

        return False

    def initialize(self):
        """Initialize all modules.

        After the call, module inputs and outputs are available for linking.
        """
        self.logger.debug("init composition")
        for mod in self.modules:
            mod._base_logger_name = self.logger_name
            mod.initialize()
            for input in mod.inputs:
                mod.inputs[input]._name = input
                mod.inputs[input]._base_logger_name = mod.logger_name
            for output in mod.outputs:
                mod.outputs[output]._name = output
                mod.outputs[output]._base_logger_name = mod.logger_name

    def run(self, t_max):
        """Run this composition using the loop-based update strategy.

        Parameters
        ----------
        t_max : datetime
            Simulation time up to which to simulate.
        """
        self.logger.debug("run composition")
        self.validate()

        try:
            if not isinstance(t_max, datetime):
                raise ValueError("t_max must be of type datetime")
        except ValueError as err:
            self.logger.exception(err)
            raise

        for mod in self.modules:
            mod.connect()

        for mod in self.modules:
            mod.validate()

        time_modules = list(
            filter(lambda m: isinstance(m, ITimeComponent), self.modules)
        )

        while True:
            to_update = min(time_modules, key=lambda m: m.time)
            to_update.update()

            any_running = False
            for mod in time_modules:
                if mod.time < t_max:
                    any_running = True
                    break

            if not any_running:
                break

        for mod in self.modules:
            mod.finalize()

    def validate(self):
        """Validates the coupling setup by checking for dangling inputs and disallowed branching connections."""
        self.logger.debug("validate composition")
        for mod in self.modules:
            for (name, inp) in mod.inputs.items():
                par_inp = inp.get_source()
                while True:
                    try:
                        if par_inp is None:
                            raise ValueError(
                                f"Unconnected input '{name}' for module {mod.name}"
                            )
                    except ValueError as err:
                        inp.logger.exception(err)
                        raise

                    if not isinstance(par_inp, IAdapter):
                        break

                    par_inp = par_inp.get_source()

            for (name, out) in mod.outputs.items():
                targets = [(out, False)]

                while len(targets) > 0:
                    target, no_branch = targets.pop()
                    no_branch = no_branch or isinstance(target, NoBranchAdapter)

                    curr_targets = target.get_targets()

                    try:
                        if no_branch and len(curr_targets) > 1:
                            raise ValueError(
                                f"Disallowed branching of output '{name}' for "
                                f"module {mod.name} ({target.__class__.__name__})"
                            )
                    except ValueError as err:
                        out.logger.exception(err)
                        raise

                    for target in curr_targets:
                        if isinstance(target, IAdapter):
                            targets.append((target, no_branch))

    @property
    def logger_name(self):
        """Logger name for the composition."""
        return self._logger_name

    @property
    def logger(self):
        """Logger for the composition."""
        return logging.getLogger(self.logger_name)
