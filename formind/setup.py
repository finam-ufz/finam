import os
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
