from typing import Optional


class HelixLangError(Exception):
    """
    Base class for all HelixLang errors.
    Contains message, optional source location (line, column), error code, and category.
    """

    def __init__(
        self,
        message: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
        error_code: Optional[str] = None,
        category: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column
        self.error_code = error_code
        self.category = category
        self.recovery_hint = recovery_hint

    def __str__(self):
        loc_info = f"Line {self.line}, Column {self.column}" if self.line is not None and self.column is not None else "Unknown location"
        code_info = f"[{self.error_code}]" if self.error_code else ""
        cat_info = f"({self.category})" if self.category else ""
        base = f"{loc_info} {code_info} {cat_info}: {self.message}"
        if self.recovery_hint:
            base += f"\nHint: {self.recovery_hint}"
        return base


class HelixSyntaxError(HelixLangError):
    """
    Error raised for syntax/parsing issues.
    """
    def __init__(
        self,
        message: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
        error_code: Optional[str] = "HLX_SYNTAX_ERR",
        recovery_hint: Optional[str] = "Check syntax near the indicated location.",
    ):
        super().__init__(message, line, column, error_code, "Syntax Error", recovery_hint)


class HelixTypeError(HelixLangError):
    """
    Error raised for type checking failures.
    """
    def __init__(
        self,
        message: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
        error_code: Optional[str] = "HLX_TYPE_ERR",
        recovery_hint: Optional[str] = "Ensure type compatibility and correctness.",
    ):
        super().__init__(message, line, column, error_code, "Type Error", recovery_hint)


class HelixRuntimeError(HelixLangError):
    """
    Error raised during runtime execution.
    """
    def __init__(
        self,
        message: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
        error_code: Optional[str] = "HLX_RUNTIME_ERR",
        recovery_hint: Optional[str] = None,
    ):
        super().__init__(message, line, column, error_code, "Runtime Error", recovery_hint)


class HelixMutationError(HelixLangError):
    """
    Error for illegal mutation attempts, e.g., changing immutable variables.
    """
    def __init__(
        self,
        message: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
        error_code: Optional[str] = "HLX_MUTATION_ERR",
        recovery_hint: Optional[str] = "Verify that you are not modifying immutable values.",
    ):
        super().__init__(message, line, column, error_code, "Mutation Error", recovery_hint)


# Additional errors can be defined similarly:
# e.g. HelixImportError, HelixNameError, HelixValueError, HelixAssertionError


# Optional helper functions to raise errors with consistent formatting:

def raise_syntax_error(message: str, line: int = None, column: int = None):
    raise HelixSyntaxError(message, line, column)

def raise_type_error(message: str, line: int = None, column: int = None):
    raise HelixTypeError(message, line, column)

def raise_runtime_error(message: str, line: int = None, column: int = None):
    raise HelixRuntimeError(message, line, column)

def raise_mutation_error(message: str, line: int = None, column: int = None):
    raise HelixMutationError(message, line, column)
