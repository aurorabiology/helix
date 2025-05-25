import os
import pathlib

# Versioning for stdlib
STD_LIB_VERSION = (1, 0, 0)
STD_LIB_VERSION_STR = "1.0.0"

# Root directory of the stdlib package
STDLIB_DIR = pathlib.Path(__file__).parent.resolve()

# List of standard modules (no file extensions)
__all__ = [
    "base",
    "genetics",
    "protein",
    "simulation",
    "environment",
    "mutation",
    "visualization",
    "export",
    "wetlab",
]

# Files to preload by default into REPL or compiled programs
PRELOAD_MODULES = [
    "base",
    "genetics",
]

def get_stdlib_path(module_name: str) -> str:
    """
    Returns the absolute path to a stdlib `.hl` file.
    """
    if module_name not in __all__:
        raise ValueError(f"Standard library module '{module_name}' not found.")
    return str(STDLIB_DIR / f"{module_name}.hl")

def list_available_modules() -> list:
    """
    Dynamically detects all valid HelixLang modules in the stdlib folder.
    """
    return [
        p.stem
        for p in STDLIB_DIR.glob("*.hl")
        if p.is_file() and not p.name.startswith("_")
    ]

def print_stdlib_metadata():
    print(f"[HelixLang Stdlib] Version: {STD_LIB_VERSION_STR}")
    print(f"Available Modules: {', '.join(list_available_modules())}")
    print(f"Preload Defaults: {', '.join(PRELOAD_MODULES)}")
