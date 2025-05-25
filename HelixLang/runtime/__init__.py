"""
HelixLang Runtime Package

This package contains modules for execution and memory management
during HelixLang program runtime, including environment management,
memory handling, complex data types, standard functions, mutation
mechanics, and I/O support.
"""

__version__ = "0.1.0"

# Explicitly expose runtime submodules for convenient imports
from . import runtime_env
from . import memory
from . import value_types
from . import std_functions
from . import mutation_runtime
from . import io_runtime
