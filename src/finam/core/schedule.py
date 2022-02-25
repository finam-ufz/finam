"""
Driver/scheduler for executing a coupled model composition.
"""
from datetime import datetime

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
    mpi_rank : int, default 0
        MPI rank of the composition.
    """

    def __init__(self, modules, mpi_rank=0):
        for module in modules:
            if not isinstance(module, IComponent):
                raise ValueError(
                    "Composition: modules need to be instances of 'IComponent'."
                )

        self.modules = modules
        self.mpi_rank = mpi_rank

    def run_mpi(self):
        """Run MPI processes is not on rank 0.

        Returns
        -------
        bool
            True if on rank 0, false otherwise.
        """
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
        for mod in self.modules:
            mod.initialize()

    def run(self, t_max):
        """Run this composition using the loop-based update strategy.

        Parameters
        ----------
        t_max : datetime
            Simulation time up to which to simulate.
        """
        self.validate()

        if not isinstance(t_max, datetime):
            raise ValueError("t_max must be of type datetime")

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
        for mod in self.modules:
            for (name, inp) in mod.inputs.items():
                par_inp = inp.get_source()
                while True:
                    if par_inp is None:
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
                        raise ValueError(
                            f"Disallowed branching of output '{name}' for "
                            f"module {mod.name} ({target.__class__.__name__})"
                        )

                    for target in curr_targets:
                        if isinstance(target, IAdapter):
                            targets.append((target, no_branch))
