# utils.py

"""
HelixLang Utility Functions

General-purpose helpers shared across multiple modules:
- String utilities for common operations.
- Error formatting with source location context.
- Tree traversal helpers for AST nodes.
- Data structure utilities like deep copy, flatten.
- File reading with encoding and error handling.

Designed to improve code reuse and clarity across HelixLang codebase.
"""

import copy
import os
import sys
import json
from collections import deque
from typing import Any, Callable, Dict, List, Optional, Union

# -----------------------------------------------------
# STRING UTILITIES
# -----------------------------------------------------

def indent(text: str, level: int = 1, indent_str: str = "    ") -> str:
    """
    Indent each line of `text` by `level` indentation levels.
    Useful for formatting generated code or pretty-printing.
    """
    prefix = indent_str * level
    return "\n".join(prefix + line if line.strip() != "" else line for line in text.splitlines())


def camel_to_snake(name: str) -> str:
    """
    Convert CamelCase string to snake_case.
    Example: 'MyFunctionName' -> 'my_function_name'
    """
    import re
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def snake_to_camel(name: str) -> str:
    """
    Convert snake_case string to CamelCase.
    Example: 'my_function_name' -> 'MyFunctionName'
    """
    return "".join(word.capitalize() for word in name.split("_"))


def safe_str(obj: Any) -> str:
    """
    Convert any object to string safely, catching exceptions.
    """
    try:
        return str(obj)
    except Exception:
        return "<unprintable>"


# -----------------------------------------------------
# ERROR FORMATTING
# -----------------------------------------------------

def format_error_message(
    message: str,
    filename: Optional[str] = None,
    line: Optional[int] = None,
    column: Optional[int] = None,
    context_line: Optional[str] = None,
) -> str:
    """
    Format error message with optional source location and context.
    Example:
      filename:line:column: message
      context_line
          ^
    """
    location = ""
    if filename:
        location += f"{filename}"
        if line is not None:
            location += f":{line}"
            if column is not None:
                location += f":{column}"
        location += ": "

    error_str = f"{location}{message}"

    if context_line and column is not None and column > 0:
        pointer_line = " " * (column - 1) + "^"
        error_str += f"\n{context_line}\n{pointer_line}"

    return error_str


# -----------------------------------------------------
# AST / TREE TRAVERSAL HELPERS
# -----------------------------------------------------

def traverse_ast(node: Any, visit_fn: Callable[[Any], None]) -> None:
    """
    Recursively traverse AST nodes in preorder.
    Applies visit_fn(node) to each node.

    Assumes each node has 'children' attribute or property that returns iterable of child nodes.
    """
    if node is None:
        return
    visit_fn(node)
    children = getattr(node, "children", None)
    if children:
        for child in children:
            traverse_ast(child, visit_fn)


def find_in_ast(node: Any, predicate: Callable[[Any], bool]) -> Optional[Any]:
    """
    Recursively search AST for a node satisfying predicate.
    Returns the first matching node or None if not found.
    """
    if predicate(node):
        return node
    children = getattr(node, "children", None)
    if children:
        for child in children:
            found = find_in_ast(child, predicate)
            if found is not None:
                return found
    return None


# -----------------------------------------------------
# DATA STRUCTURE UTILITIES
# -----------------------------------------------------

def deep_copy(obj: Any) -> Any:
    """
    Return a deep copy of a complex data structure.
    Wraps Python's built-in deepcopy with error handling.
    """
    try:
        return copy.deepcopy(obj)
    except Exception as e:
        raise RuntimeError(f"Deep copy failed: {e}") from e


def flatten(nested_list: Union[List[Any], Any]) -> List[Any]:
    """
    Flatten a nested list of arbitrary depth into a single list of atomic elements.
    Example: [1, [2, [3, 4], 5], 6] -> [1, 2, 3, 4, 5, 6]
    """
    flat_list = []

    def _flatten(element):
        if isinstance(element, list):
            for item in element:
                _flatten(item)
        else:
            flat_list.append(element)

    _flatten(nested_list)
    return flat_list


def merge_dicts(*dicts: Dict[Any, Any]) -> Dict[Any, Any]:
    """
    Merge multiple dictionaries into one.
    Later dictionaries override keys of earlier ones.
    """
    merged = {}
    for d in dicts:
        merged.update(d)
    return merged


# -----------------------------------------------------
# FILE I/O HELPERS
# -----------------------------------------------------

def read_file_utf8(filename: str) -> str:
    """
    Read the entire contents of a UTF-8 encoded text file.
    Raises FileNotFoundError or UnicodeDecodeError on error.
    """
    with open(filename, "r", encoding="utf-8") as f:
        return f.read()


def write_file_utf8(filename: str, content: str) -> None:
    """
    Write string content to a file with UTF-8 encoding.
    """
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)


def ensure_dir_exists(dir_path: str) -> None:
    """
    Create directory and all intermediate directories if they do not exist.
    """
    os.makedirs(dir_path, exist_ok=True)


def file_exists(filepath: str) -> bool:
    """
    Check if a file exists at the given path.
    """
    return os.path.isfile(filepath)


# -----------------------------------------------------
# JSON UTILITIES (for config or AST export)
# -----------------------------------------------------

def json_dumps_pretty(data: Any) -> str:
    """
    Serialize Python object to a pretty-printed JSON string.
    """
    return json.dumps(data, indent=4, sort_keys=True)


def json_loads_safe(json_str: str) -> Any:
    """
    Parse JSON string safely, raising descriptive errors on failure.
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e.msg} at line {e.lineno} column {e.colno}")


# -----------------------------------------------------
# SYSTEM / ENVIRONMENT UTILITIES
# -----------------------------------------------------

def get_platform() -> str:
    """
    Return the current operating system platform (e.g., 'windows', 'linux', 'darwin').
    """
    return sys.platform


def exit_with_message(message: str, code: int = 1) -> None:
    """
    Print a message to stderr and exit with the given code.
    """
    print(message, file=sys.stderr)
    sys.exit(code)


# -----------------------------------------------------
# END OF utils.py
# -----------------------------------------------------
