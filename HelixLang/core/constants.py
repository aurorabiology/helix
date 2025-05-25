# constants.py

"""
HelixLang Language Constants

This module centralizes all constants used throughout the HelixLang compiler
and runtime. It includes keywords, operators, built-in function names, literals,
and other fixed language constructs.

These constants are heavily referenced by tokenizer.py, parser.py, interpreter.py,
stdlib_loader.py, and other core modules.
"""

# ---------------------------
# Keywords
# ---------------------------
# Reserved words in HelixLang that have special syntactic or semantic meaning.
KEYWORDS = [
    # Control flow
    "if", "else", "elif", "while", "for", "break", "continue", "return",

    # Function and variable declaration
    "def", "let", "var", "const",

    # Boolean literals
    "true", "false",

    # Null / None / Empty value
    "null", "none",

    # Module and import
    "import", "from", "as", "module",

    # Data structure and types
    "struct", "enum", "type", "class",

    # Exception handling
    "try", "catch", "finally", "throw", "raise",

    # Misc
    "yield", "async", "await",
    "match",  # pattern matching (future feature)

    # HelixLang-specific domain keywords (genetics etc.)
    "genome", "protein", "cell",

    # Debug and runtime
    "debug", "assert",
]

# Fast lookup for keywords (used by tokenizer)
KEYWORDS_SET = set(KEYWORDS)

# ---------------------------
# Operators
# ---------------------------
# All operator symbols supported by HelixLang
OPERATORS = {
    # Arithmetic
    "PLUS": "+",
    "MINUS": "-",
    "MULTIPLY": "*",
    "DIVIDE": "/",
    "MODULO": "%",

    # Assignment and compound assignment
    "ASSIGN": "=",
    "PLUS_ASSIGN": "+=",
    "MINUS_ASSIGN": "-=",
    "MULTIPLY_ASSIGN": "*=",
    "DIVIDE_ASSIGN": "/=",

    # Comparison
    "EQUAL": "==",
    "NOT_EQUAL": "!=",
    "LESS": "<",
    "LESS_EQUAL": "<=",
    "GREATER": ">",
    "GREATER_EQUAL": ">=",

    # Logical
    "AND": "&&",
    "OR": "||",
    "NOT": "!",

    # Bitwise
    "BIT_AND": "&",
    "BIT_OR": "|",
    "BIT_XOR": "^",
    "BIT_NOT": "~",
    "SHIFT_LEFT": "<<",
    "SHIFT_RIGHT": ">>",

    # Other
    "DOT": ".",
    "COMMA": ",",
    "COLON": ":",
    "SEMICOLON": ";",
    "ARROW": "->",

    # Parentheses and brackets
    "LPAREN": "(",
    "RPAREN": ")",
    "LBRACE": "{",
    "RBRACE": "}",
    "LBRACKET": "[",
    "RBRACKET": "]",
}

# Reverse mapping for quick token recognition (symbol -> token name)
OPERATORS_REVERSE = {v: k for k, v in OPERATORS.items()}

# ---------------------------
# Built-in Functions
# ---------------------------
# Names of built-in functions that are always available in the standard environment
BUILTIN_FUNCTIONS = [
    "print",        # Output to console
    "println",      # Output with newline
    "len",          # Length of string, array, etc.
    "range",        # Generate numeric sequences
    "input",        # Read user input
    "type",         # Return type of value
    "assert",       # Runtime assertion
    "int",          # Cast/convert to int
    "float",        # Cast/convert to float
    "str",          # Cast/convert to string
    "bool",         # Cast/convert to bool
    "abs",          # Absolute value
    "sqrt",         # Square root
    "sin", "cos", "tan",  # Trigonometric
    "random",       # Random number generation
    "exit",         # Exit program
]

BUILTIN_FUNCTIONS_SET = set(BUILTIN_FUNCTIONS)

# ---------------------------
# Literals
# ---------------------------
# Special predefined literal values in HelixLang
LITERALS = {
    "NULL": "null",
    "TRUE": "true",
    "FALSE": "false",
    "NONE": "none",  # synonym for null or empty
}

# ---------------------------
# Miscellaneous
# ---------------------------

# Comment prefixes
COMMENT_SINGLE_LINE = "//"
COMMENT_MULTI_START = "/*"
COMMENT_MULTI_END = "*/"

# Whitespace characters for tokenizer
WHITESPACE_CHARS = {" ", "\t", "\n", "\r"}

# Numeric literal prefixes (for bases)
NUMERIC_PREFIXES = {
    "BINARY": "0b",
    "OCTAL": "0o",
    "HEX": "0x",
}

# Escape sequences supported in string literals
ESCAPE_SEQUENCES = {
    "\\n": "\n",
    "\\t": "\t",
    "\\r": "\r",
    "\\\"": "\"",
    "\\'": "'",
    "\\\\": "\\",
}

# File extensions for HelixLang source files
FILE_EXTENSION = ".hl"

# ---------------------------
# Version and Dialect Flags
# ---------------------------

# Language version tags
LANGUAGE_VERSIONS = {
    "1.0": "HelixLang v1.0 stable",
    "1.1": "HelixLang v1.1 experimental features",
    "2.0": "HelixLang future major release",
}

# Default version used if none specified
DEFAULT_LANGUAGE_VERSION = "1.0"

# ---------------------------
# Error codes (optional)
# ---------------------------
ERROR_CODES = {
    "E_SYNTAX": 1001,
    "E_TYPE": 1002,
    "E_RUNTIME": 1003,
    "E_UNDEFINED_SYMBOL": 1004,
    "E_MUTATION": 1005,
    "E_DIVIDE_BY_ZERO": 1006,
}

# ---------------------------
# Usage Examples (for reference)
# ---------------------------
#
# if token.text in KEYWORDS_SET:
#     # handle keyword token
#
# if token.text in OPERATORS_REVERSE:
#     # handle operator token
#
# if function_name in BUILTIN_FUNCTIONS_SET:
#     # handle built-in function call
#

