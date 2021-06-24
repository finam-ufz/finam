from .interfaces import IAdapter, NoBranchAdapter


class Composition:
    """
    Composition of linked components.
    """

    def __init__(self, modules):
        """
        Create a new coupling composition.

        :param modules: modules in the composition
        """
        self.modules = modules

    def run(self, t_max):
        """
        Run this composition using the loop-based update strategy.

        :param t_max: simulation to to simulate to
        """
        self.validate()

        for mod in self.modules:
            mod.connect()

        for mod in self.modules:
            mod.validate()

        while True:
            self.modules.sort(key=lambda m: m.time())

            self.modules[0].update()

            any_running = False
            for mod in self.modules:
                if mod.time() < t_max:
                    any_running = True
                    break

            if not any_running:
                break

        for mod in self.modules:
            mod.finalize()

    def validate(self):
        for mod in self.modules:
            # Check for unconnected inputs
            for (name, inp) in mod.inputs().items():
                par_inp = inp.get_source()
                while True:
                    assert (
                        par_inp is not None
                    ), f"Unconnected input '{name}' for module {mod.__class__.__name__}"

                    if not isinstance(par_inp, IAdapter):
                        break

                    par_inp = par_inp.get_source()

            # Check non-branching adapters
            for (name, out) in mod.outputs().items():
                targets = [(out, False)]

                while len(targets) > 0:
                    o, no_branch = targets.pop()
                    no_branch = no_branch or isinstance(o, NoBranchAdapter)

                    curr_targets = o.get_targets()

                    assert (not no_branch) or len(
                        curr_targets
                    ) <= 1, f"Disallowed branching of output '{name}' for module {mod.__class__.__name__} ({o.__class__.__name__})"

                    for target in curr_targets:
                        if isinstance(target, IAdapter):
                            targets.append((target, no_branch))
