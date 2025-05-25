# interpreter.py

from ast_nodes import *
from symbols import SymbolTable  # assumed symbol lookup helper
from types import TypeChecker     # assumed runtime type checker
from runtime import RuntimeError, ReturnException, Environment  # helpers

class Interpreter(ASTVisitor):
    def __init__(self):
        self.global_env = Environment()
        self.env = self.global_env  # Current environment/scope
        self.type_checker = TypeChecker()

    # --- Helpers for environment and scopes ---

    def push_env(self):
        self.env = Environment(parent=self.env)

    def pop_env(self):
        self.env = self.env.parent

    # --- Entry point ---

    def interpret(self, node: ASTNode):
        try:
            return node.accept(self)
        except RuntimeError as e:
            print(f"Runtime error at {e.line}:{e.column} - {e}")
            return None
        except ReturnException as ret:
            print("Unexpected return statement outside function.")
            return None

    # --- Expression Visitors ---

    def visit_literal(self, node: LiteralNode):
        return node.value

    def visit_variable(self, node: VariableNode):
        value = self.env.get(node.name)
        if value is None:
            raise RuntimeError(f"Undefined variable '{node.name}'", node.line, node.column)
        return value

    def visit_binary_op(self, node: BinaryOpNode):
        left = node.left.accept(self)
        right = node.right.accept(self)
        op = node.operator

        # Example basic ops - extend as needed
        if op == '+':
            self.type_checker.check_numeric(left, right, node)
            return left + right
        elif op == '-':
            self.type_checker.check_numeric(left, right, node)
            return left - right
        elif op == '*':
            self.type_checker.check_numeric(left, right, node)
            return left * right
        elif op == '/':
            self.type_checker.check_numeric(left, right, node)
            if right == 0:
                raise RuntimeError("Division by zero", node.line, node.column)
            return left / right
        elif op == '==':
            return left == right
        elif op == '!=':
            return left != right
        elif op == '<':
            self.type_checker.check_numeric(left, right, node)
            return left < right
        elif op == '<=':
            self.type_checker.check_numeric(left, right, node)
            return left <= right
        elif op == '>':
            self.type_checker.check_numeric(left, right, node)
            return left > right
        elif op == '>=':
            self.type_checker.check_numeric(left, right, node)
            return left >= right
        elif op == '&&':
            return bool(left) and bool(right)
        elif op == '||':
            return bool(left) or bool(right)
        else:
            raise RuntimeError(f"Unknown binary operator '{op}'", node.line, node.column)

    def visit_unary_op(self, node: UnaryOpNode):
        operand = node.operand.accept(self)
        op = node.operator

        if op == '-':
            self.type_checker.check_numeric(operand, None, node)
            return -operand
        elif op == '!':
            return not bool(operand)
        else:
            raise RuntimeError(f"Unknown unary operator '{op}'", node.line, node.column)

    def visit_call(self, node: CallNode):
        callee = node.callee.accept(self)

        if not callable(callee):
            raise RuntimeError(f"Attempted to call non-function '{callee}'", node.line, node.column)

        args = [arg.accept(self) for arg in node.arguments]
        try:
            # Assume user-defined functions are closures represented as Function objects (defined later)
            return callee.call(self, args)
        except RuntimeError as e:
            # Propagate runtime error with location info from call site
            raise RuntimeError(str(e), node.line, node.column)

    # --- Statement Visitors ---

    def visit_variable_decl(self, node: VariableDeclNode):
        value = node.initializer.accept(self) if node.initializer else None
        self.env.define(node.name, value)

    def visit_assignment(self, node: AssignmentNode):
        value = node.value.accept(self)
        if not self.env.assign(node.target.name, value):
            raise RuntimeError(f"Undefined variable '{node.target.name}'", node.line, node.column)

    def visit_block(self, node: BlockNode):
        self.push_env()
        try:
            for stmt in node.statements:
                stmt.accept(self)
        finally:
            self.pop_env()

    def visit_if(self, node: IfNode):
        cond = node.condition.accept(self)
        if cond:
            node.then_branch.accept(self)
        elif node.else_branch:
            node.else_branch.accept(self)

    def visit_while(self, node: WhileNode):
        while node.condition.accept(self):
            node.body.accept(self)

    def visit_for(self, node: ForNode):
        self.push_env()
        try:
            node.initializer.accept(self)
            while node.condition.accept(self):
                node.body.accept(self)
                node.increment.accept(self)
        finally:
            self.pop_env()

    def visit_return(self, node: ReturnNode):
        value = node.value.accept(self) if node.value else None
        raise ReturnException(value)

    def visit_function_def(self, node: FunctionDefNode):
        func = Function(node, self.env)
        self.env.define(node.name, func)

    def visit_struct_def(self, node: StructDefNode):
        # For now: store struct metadata in environment (could be expanded)
        self.env.define(node.name, node)

    def visit_import(self, node: ImportNode):
        # Stub: Could integrate module system
        print(f"Importing module {node.module_name} (not implemented)")

# --- Function object to represent user-defined functions with closures ---

class Function:
    def __init__(self, declaration: FunctionDefNode, closure: Environment):
        self.declaration = declaration
        self.closure = closure  # The environment at function declaration time (for closures)

    def call(self, interpreter: Interpreter, arguments: list):
        # Create new environment for function call, enclosing closure
        env = Environment(parent=self.closure)
        # Bind parameters
        if len(arguments) != len(self.declaration.params):
            raise RuntimeError(f"Expected {len(self.declaration.params)} arguments but got {len(arguments)}",
                               self.declaration.line, self.declaration.column)

        for name, value in zip(self.declaration.params, arguments):
            env.define(name, value)

        # Execute function body in new environment
        try:
            interpreter.push_env()
            interpreter.env = env
            self.declaration.body.accept(interpreter)
        except ReturnException as ret:
            return ret.value
        finally:
            interpreter.pop_env()

        # If no explicit return, return None
        return None


# --- runtime.py (stubs for demonstration) ---

class RuntimeError(Exception):
    def __init__(self, message, line=None, column=None):
        super().__init__(message)
        self.line = line
        self.column = column

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

class Environment:
    def __init__(self, parent=None):
        self.values = {}
        self.parent = parent

    def define(self, name, value):
        self.values[name] = value

    def assign(self, name, value):
        if name in self.values:
            self.values[name] = value
            return True
        elif self.parent:
            return self.parent.assign(name, value)
        else:
            return False

    def get(self, name):
        if name in self.values:
            return self.values[name]
        elif self.parent:
            return self.parent.get(name)
        else:
            return None


# --- types.py (stubs for demonstration) ---

class TypeChecker:
    def check_numeric(self, left, right, node):
        if not (isinstance(left, (int, float)) and (right is None or isinstance(right, (int, float)))):
            raise RuntimeError("Operands must be numeric", node.line, node.column)

