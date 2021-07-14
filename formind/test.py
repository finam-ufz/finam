import sys

# Boilerplate to get the path of the build artifact and add it to the python path.
version = sys.version_info
version_str = f"{version.major}.{version.minor}"
platform = "win" if sys.platform == "win32" else "linux"

path = f"build/lib.{platform}-amd64-{version_str}/"
sys.path.insert(0, path)

# Interesting code starts here

import formind

model = formind.Model()

model.initialize()

for i in range(10):
    model.update()

model.finalize()
