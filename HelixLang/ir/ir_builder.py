# helixlang/ir/ir_builder.py

from helixlang.ir.ir_nodes import (
    IRNode,
    NodeType,
    FunctionNode,
    VariableNode,
    AssignmentNode,
    IfNode,
    WhileNode,
    CallNode,
    ReturnNode,
    ConstantNode,
    BinaryOpNode,
    UnaryOpNode,
    BlockNode,
)
from helixlang.errors import HelixSemanticError

class IRBuilder:
    """
    Converts HelixLang AST nodes into IRNode trees.
    Tracks symbol tables for scope and attaches semantic info.
    """

    def __init__(self, ast_root):
        self.ast_root = ast_root
        self.global_scope = {}
        self.scopes = [self.global_scope]  # stack of dicts for nested scopes

    def build(self) -> IRNode:
        return self._build_node(self.ast_root)

    def _current_scope(self):
        return self.scopes[-1]

    def _enter_scope(self):
        self.scopes.append({})

    def _exit_scope(self):
        self.scopes.pop()

    def _declare_symbol(self, name: str, node: IRNode):
        scope = self._current_scope()
        if name in scope:
            raise HelixSemanticError(f"Symbol '{name}' already declared in this scope")
        scope[name] = node

    def _lookup_symbol(self, name: str) -> IRNode:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise HelixSemanticError(f"Undefined symbol '{name}'")

    def _build_node(self, ast_node) -> IRNode:
        t = ast_node.type

        if t == "FunctionDef":
            return self._build_function(ast_node)

        elif t == "VarDecl":
            return self._build_vardecl(ast_node)

        elif t == "Assignment":
            return self._build_assignment(ast_node)

        elif t == "If":
            return self._build_if(ast_node)

        elif t == "While":
            return self._build_while(ast_node)

        elif t == "Return":
            return self._build_return(ast_node)

        elif t == "Call":
            return self._build_call(ast_node)

        elif t == "Constant":
            return ConstantNode(value=ast_node.value, const_type=ast_node.const_type)

        elif t == "BinaryOp":
            left = self._build_node(ast_node.left)
            right = self._build_node(ast_node.right)
            op = ast_node.operator
            return BinaryOpNode(operator=op, left=left, right=right)

        elif t == "UnaryOp":
            operand = self._build_node(ast_node.operand)
            op = ast_node.operator
            return UnaryOpNode(operator=op, operand=operand)

        elif t == "Variable":
            # Lookup variable in scope
            var_node = self._lookup_symbol(ast_node.name)
            return var_node

        elif t == "Block":
            return self._build_block(ast_node)

        else:
            raise NotImplementedError(f"Unhandled AST node type '{t}'")

    def _build_function(self, ast_node):
        # Function scope begins
        self._enter_scope()

        # Declare parameters in current scope
        params = []
        for param in ast_node.params:
            param_name = param.name
            param_type = getattr(param, "var_type", None)
            var_node = VariableNode(param_name, param_type)
            self._declare_symbol(param_name, var_node)
            params.append(param_name)

        # Build function body IR nodes
        body_ir = [self._build_node(stmt) for stmt in ast_node.body]

        # Function scope ends
        self._exit_scope()

        return FunctionNode(
            name=ast_node.name,
            params=params,
            body=body_ir,
            return_type=getattr(ast_node, "return_type", None)
        )

    def _build_vardecl(self, ast_node):
        name = ast_node.name
        var_type = getattr(ast_node, "var_type", None)

        var_node = VariableNode(name, var_type)
        # Declare in current scope, error if redeclared
        self._declare_symbol(name, var_node)
        return var_node

    def _build_assignment(self, ast_node):
        target = self._build_node(ast_node.target)
        value = self._build_node(ast_node.value)
        # Optional: Type checks could go here
        return AssignmentNode(target, value)

    def _build_if(self, ast_node):
        cond_ir = self._build_node(ast_node.condition)

        # Then block scope
        self._enter_scope()
        then_body_ir = [self._build_node(stmt) for stmt in ast_node.then_body]
        self._exit_scope()

        else_body_ir = []
        if hasattr(ast_node, "else_body") and ast_node.else_body is not None:
            self._enter_scope()
            else_body_ir = [self._build_node(stmt) for stmt in ast_node.else_body]
            self._exit_scope()

        return IfNode(cond_ir, then_body_ir, else_body_ir)

    def _build_while(self, ast_node):
        cond_ir = self._build_node(ast_node.condition)
        self._enter_scope()
        body_ir = [self._build_node(stmt) for stmt in ast_node.body]
        self._exit_scope()
        return WhileNode(cond_ir, body_ir)

    def _build_return(self, ast_node):
        if hasattr(ast_node, "value") and ast_node.value is not None:
            val_ir = self._build_node(ast_node.value)
        else:
            val_ir = None
        return ReturnNode(val_ir)

    def _build_call(self, ast_node):
        func_name = ast_node.function_name
        args_ir = [self._build_node(arg) for arg in ast_node.arguments]
        # Optional: semantic checks if function exists could go here
        return CallNode(func_name, args_ir)

    def _build_block(self, ast_node):
        self._enter_scope()
        statements_ir = [self._build_node(stmt) for stmt in ast_node.statements]
        self._exit_scope()
        return BlockNode(statements_ir)
