"""
Driver/scheduler for executing a coupled model composition.
"""
from datetime import datetime

from .interfaces import (
    IComponent,
    ITimeComponent,
    IMpiComponent,
    IAdapter,
    NoBranchAdapter,
)


class Composition:
    """
    A composition of linked components.
    """

    def __init__(self, modules, mpi_rank=0):
        """
        Create a new coupling composition.

        :param modules: modules in the composition
        """
        for module in modules:
            assert isinstance(module, IComponent)

        self.modules = modules
        self.mpi_rank = mpi_rank

    def run_mpi(self):
        """
        Run MPI processes is not on rank 0.

        :return: true if on rank 0, false otherwise
        """
        if self.mpi_rank == 0:
            return True

        for mod in self.modules:
            if isinstance(mod, IMpiComponent):
                mod.run_mpi()

        return False

    def initialize(self):
        """
        Initialize all modules.

        After the call, module inputs and outputs are available for linking.
        """
        for mod in self.modules:
            mod.initialize()

    def run(self, t_max):
        """
        Run this composition using the loop-based update strategy.

        :param t_max: simulation time up to which to simulate
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
            to_update = min(time_modules, key=lambda m: m.time())
            to_update.update()

            any_running = False
            for mod in time_modules:
                if mod.time() < t_max:
                    any_running = True
                    break

            if not any_running:
                break

        for mod in self.modules:
            mod.finalize()

    def validate(self):
        """
        Validates the coupling setup by checking for dangling inputs and disallowed branching connections.
        """
        for mod in self.modules:
            for (name, inp) in mod.inputs().items():
                par_inp = inp.get_source()
                while True:
                    assert (
                        par_inp is not None
                    ), f"Unconnected input '{name}' for module {mod.__class__.__name__}"

                    if not isinstance(par_inp, IAdapter):
                        break

                    par_inp = par_inp.get_source()

            for (name, out) in mod.outputs().items():
                targets = [(out, False)]

                while len(targets) > 0:
                    target, no_branch = targets.pop()
                    no_branch = no_branch or isinstance(target, NoBranchAdapter)

                    curr_targets = target.get_targets()

                    assert (not no_branch) or len(
                        curr_targets
                    ) <= 1, f"Disallowed branching of output '{name}' for module {mod.__class__.__name__} ({target.__class__.__name__})"

                    for target in curr_targets:
                        if isinstance(target, IAdapter):
                            targets.append((target, no_branch))
