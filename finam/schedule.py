class Composition:
    def __init__(self, modules):
        self.modules = modules

    def run(self, t_max):
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
