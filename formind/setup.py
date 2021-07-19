import glob
import os
import sys
import shutil
from distutils.core import setup, Extension

from Cython.Build import cythonize

NAME = "formind"

cpp_dir = "cpp"
cpp_modules = [os.path.join(cpp_dir, "formind.cpp")]

extensions = [
    Extension(
        NAME,
        cpp_modules + [NAME + ".pyx"],
        include_dirs=[cpp_dir],
    )
]

setup(
    name=NAME,
    ext_modules=cythonize(extensions, language_level="3", annotate=True),
)

# Boilerplate to get the path of the build artifact and add it to the python path.
version = sys.version_info
version_str = f"{version.major}.{version.minor}"
platform = "win" if sys.platform == "win32" else "linux"

path = f"build/lib.{platform}-amd64-{version_str}/"
file = glob.glob(path + "formind.*")[0]
ext = "pyd" if os.name == "nt" else "so"

shutil.copyfile(file, f"formind.{ext}")
