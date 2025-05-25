# validator.py

"""
Semantic Validator for HelixLang

Responsibilities:
- Enforce type correctness and conversions.
- Enforce mutation safety and biological-specific constraints.
- Verify control flow and unreachable code.
- Validate function declarations and calls.
- Ensure all variables are declared and initialized.
"""

from helixlang.errors import TypeError, ValidationError, MutationError
from helixlang.symbols import SymbolTable
from helixlang.types import (
    is_subtype,
    get_type,
    FunctionType,
    BoolType,
    VoidType
)
from helixlang.constants import MUTABLE_TYPES


class Validator:
    def __init__(self):
        self.symbols = SymbolTable()
        self.errors = []
        self.current_function_return_type = None

    def validate(self, node):
        method_name = f"validate_{node.type}"
        method = getattr(self, method_name, self.generic_validate)
        return method(node)

    def generic_validate(self, node):
        for child in node.children:
            self.validate(child)

    # -------------------------------------
    # Program and Block-Level Constructs
    # -------------------------------------

    def validate_program(self, node):
        self.symbols.enter_scope()
        for stmt in node.body:
            self.validate(stmt)
        self.symbols.exit_scope()

    def validate_block(self, node):
        self.symbols.enter_scope()
        for stmt in node.body:
            self.validate(stmt)
        self.symbols.exit_scope()

    # -------------------------------------
    # Variable Declarations & Assignments
    # -------------------------------------

    def validate_var_decl(self, node):
        var_name = node.name
        var_type = get_type(node.var_type)
        expr_type = self.validate(node.value)

        if not is_subtype(expr_type, var_type):
            self.error(TypeError(f"Cannot assign {expr_type} to {var_type}", node))

        self.symbols.insert(var_name, var_type, mutable=node.mutable)
        return var_type

    def validate_assignment(self, node):
        var_info = self.symbols.lookup(node.name)
        if not var_info:
            self.error(ValidationError(f"Variable '{node.name}' not declared", node))

        if not var_info.mutable:
            self.error(MutationError(f"Cannot reassign immutable variable '{node.name}'", node))

        expr_type = self.validate(node.value)
        if not is_subtype(expr_type, var_info.type):
            self.error(TypeError(f"Type mismatch in assignment: {expr_type} to {var_info.type}", node))

    # -------------------------------------
    # Function Declarations and Calls
    # -------------------------------------

    def validate_function_decl(self, node):
        func_name = node.name
        param_types = [get_type(p.var_type) for p in node.params]
        return_type = get_type(node.return_type)
        func_type = FunctionType(param_types, return_type)
        self.symbols.insert(func_name, func_type)

        self.symbols.enter_scope()
        for param, param_type in zip(node.params, param_types):
            self.symbols.insert(param.name, param_type)
        self.current_function_return_type = return_type
        self.validate(node.body)
        self.symbols.exit_scope()

    def validate_function_call(self, node):
        func_info = self.symbols.lookup(node.name)
        if not func_info:
            self.error(ValidationError(f"Function '{node.name}' not declared", node))

        if not isinstance(func_info.type, FunctionType):
            self.error(TypeError(f"'{node.name}' is not a function", node))

        expected_params = func_info.type.param_types
        actual_args = [self.validate(arg) for arg in node.args]

        if len(expected_params) != len(actual_args):
            self.error(TypeError(f"Function '{node.name}' expects {len(expected_params)} args, got {len(actual_args)}", node))

        for i, (expected, actual) in enumerate(zip(expected_params, actual_args)):
            if not is_subtype(actual, expected):
                self.error(TypeError(f"Argument {i+1} mismatch: expected {expected}, got {actual}", node))

        return func_info.type.return_type

    # -------------------------------------
    # Expressions & Conditionals
    # -------------------------------------

    def validate_if(self, node):
        cond_type = self.validate(node.condition)
        if not is_subtype(cond_type, BoolType()):
            self.error(TypeError("Condition in 'if' must be boolean", node))

        self.validate(node.then_branch)
        if node.else_branch:
            self.validate(node.else_branch)

    def validate_while(self, node):
        cond_type = self.validate(node.condition)
        if not is_subtype(cond_type, BoolType()):
            self.error(TypeError("Condition in 'while' must be boolean", node))

        self.validate(node.body)

    def validate_return(self, node):
        if not self.current_function_return_type:
            self.error(ValidationError("Return statement outside of function", node))

        if node.value:
            return_type = self.validate(node.value)
        else:
            return_type = VoidType()

        if not is_subtype(return_type, self.current_function_return_type):
            self.error(TypeError(f"Return type mismatch: expected {self.current_function_return_type}, got {return_type}", node))

    # -------------------------------------
    # Biological-Specific Semantic Checks
    # -------------------------------------

    def validate_mutation(self, node):
        target_type = self.validate(node.target)
        if target_type not in MUTABLE_TYPES:
            self.error(MutationError(f"Cannot mutate type '{target_type}'", node))

        self.validate(node.value)  # Still check validity of mutation value

    # -------------------------------------
    # Error Handling
    # -------------------------------------

    def error(self, err):
        self.errors.append(err)
        print(err)

    def has_errors(self):
        return len(self.errors) > 0
