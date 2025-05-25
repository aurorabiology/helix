# helixlang/core/__init__.py

"""
Core package of HelixLang: parsing, interpreting, compiling, type checking, etc.

This module marks the core directory as a Python package and exposes
key classes and functions for easier imports.

Example usage:
    from helixlang.core import Parser, Tokenizer, Interpreter
"""

# Optionally, define the core package version here or import from version.py
try:
    from .version import __version__
except ImportError:
    __version__ = "0.1.0"  # fallback version if version.py is missing

# Import key components to expose them at the package level
from .parser import Parser
from .tokenizer import Tokenizer
from .interpreter import Interpreter
from .compiler import Compiler
from .runtime import Runtime
from .types import TypeSystem
from .symbols import SymbolTable
from .errors import (
    SyntaxError as HelixSyntaxError,
    TypeError as HelixTypeError,
    RuntimeError as HelixRuntimeError,
)
from .optimizer import Optimizer
from .validator import Validator

# Optional: initialize any package-wide state here
# (Avoid this if not strictly necessary to prevent tight coupling)

__all__ = [
    "Parser",
    "Tokenizer",
    "Interpreter",
    "Compiler",
    "Runtime",
    "TypeSystem",
    "SymbolTable",
    "HelixSyntaxError",
    "HelixTypeError",
    "HelixRuntimeError",
    "Optimizer",
    "Validator",
    "__version__",
]
