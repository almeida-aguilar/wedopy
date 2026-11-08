"""Build script: compiles the private Cython core ``wedopy_core._wedopy``."""
from setuptools import Extension, setup
from Cython.Build import cythonize

extensions = [
    Extension("wedopy_core._wedopy", ["wedopy_core/_wedopy.pyx"]),
]

setup(
    ext_modules=cythonize(
        extensions,
        language_level=3,
        compiler_directives={"binding": True},
    ),
)
