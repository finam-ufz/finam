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
