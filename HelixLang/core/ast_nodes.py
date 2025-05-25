from abc import ABC, abstractmethod


class ASTNode(ABC):
    """
    Base class for all AST nodes.
    Stores source position info (line, column) for error reporting/debugging.
    """

    def __init__(self, line: int, column: int):
        self.line = line
        self.column = column

    @abstractmethod
    def accept(self, visitor):
        """
        Visitor pattern accept method.
        Each node type will call the appropriate visitor method.
        """
        pass

    @abstractmethod
    def __str__(self):
        """
        Human-readable representation for debugging.
        """
        pass


# === Expression Nodes ===

class ExprNode(ASTNode):
    """Base class for all expressions."""
    pass


class BinaryOpNode(ExprNode):
    def __init__(self, left: ExprNode, operator: str, right: ExprNode, line: int, column: int):
        super().__init__(line, column)
        self.left = left
        self.operator = operator  # e.g., '+', '-', '*', '/'
        self.right = right

    def accept(self, visitor):
        return visitor.visit_binary_op(self)

    def __str__(self):
        return f"({self.left} {self.operator} {self.right})"


class UnaryOpNode(ExprNode):
    def __init__(self, operator: str, operand: ExprNode, line: int, column: int):
        super().__init__(line, column)
        self.operator = operator  # e.g., '-', '!'
        self.operand = operand

    def accept(self, visitor):
        return visitor.visit_unary_op(self)

    def __str__(self):
        return f"({self.operator}{self.operand})"


class LiteralNode(ExprNode):
    def __init__(self, value, line: int, column: int):
        super().__init__(line, column)
        self.value = value  # Can be int, float, str, bool, etc.

    def accept(self, visitor):
        return visitor.visit_literal(self)

    def __str__(self):
        return repr(self.value)


class VariableNode(ExprNode):
    def __init__(self, name: str, line: int, column: int):
        super().__init__(line, column)
        self.name = name

    def accept(self, visitor):
        return visitor.visit_variable(self)

    def __str__(self):
        return self.name


class CallNode(ExprNode):
    def __init__(self, callee: ExprNode, arguments: list, line: int, column: int):
        super().__init__(line, column)
        self.callee = callee         # Expression identifying the function
        self.arguments = arguments   # List of ExprNode

    def accept(self, visitor):
        return visitor.visit_call(self)

    def __str__(self):
        args_str = ', '.join(str(arg) for arg in self.arguments)
        return f"{self.callee}({args_str})"


# === Statement Nodes ===

class StmtNode(ASTNode):
    """Base class for all statements."""
    pass


class IfNode(StmtNode):
    def __init__(self, condition: ExprNode, then_branch: StmtNode, else_branch: StmtNode = None, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch  # Optional

    def accept(self, visitor):
        return visitor.visit_if(self)

    def __str__(self):
        s = f"if ({self.condition}) {self.then_branch}"
        if self.else_branch:
            s += f" else {self.else_branch}"
        return s


class WhileNode(StmtNode):
    def __init__(self, condition: ExprNode, body: StmtNode, line: int, column: int):
        super().__init__(line, column)
        self.condition = condition
        self.body = body

    def accept(self, visitor):
        return visitor.visit_while(self)

    def __str__(self):
        return f"while ({self.condition}) {self.body}"


class ForNode(StmtNode):
    def __init__(self, initializer: StmtNode, condition: ExprNode, increment: StmtNode, body: StmtNode, line: int, column: int):
        super().__init__(line, column)
        self.initializer = initializer
        self.condition = condition
        self.increment = increment
        self.body = body

    def accept(self, visitor):
        return visitor.visit_for(self)

    def __str__(self):
        return f"for ({self.initializer}; {self.condition}; {self.increment}) {self.body}"


class ReturnNode(StmtNode):
    def __init__(self, value: ExprNode, line: int, column: int):
        super().__init__(line, column)
        self.value = value  # Can be None for void return

    def accept(self, visitor):
        return visitor.visit_return(self)

    def __str__(self):
        return f"return {self.value}" if self.value else "return"


class BlockNode(StmtNode):
    def __init__(self, statements: list, line: int, column: int):
        super().__init__(line, column)
        self.statements = statements  # List of StmtNode

    def accept(self, visitor):
        return visitor.visit_block(self)

    def __str__(self):
        stmts_str = '\n'.join(str(stmt) for stmt in self.statements)
        return f"{{\n{stmts_str}\n}}"


class FunctionDefNode(StmtNode):
    def __init__(self, name: str, params: list, body: BlockNode, line: int, column: int):
        super().__init__(line, column)
        self.name = name
        self.params = params        # List of parameter names (strings)
        self.body = body

    def accept(self, visitor):
        return visitor.visit_function_def(self)

    def __str__(self):
        params_str = ', '.join(self.params)
        return f"fn {self.name}({params_str}) {self.body}"


class VariableDeclNode(StmtNode):
    def __init__(self, name: str, initializer: ExprNode, line: int, column: int):
        super().__init__(line, column)
        self.name = name
        self.initializer = initializer

    def accept(self, visitor):
        return visitor.visit_variable_decl(self)

    def __str__(self):
        return f"let {self.name} = {self.initializer};"


class AssignmentNode(StmtNode):
    def __init__(self, target: VariableNode, value: ExprNode, line: int, column: int):
        super().__init__(line, column)
        self.target = target
        self.value = value

    def accept(self, visitor):
        return visitor.visit_assignment(self)

    def __str__(self):
        return f"{self.target} = {self.value};"


# === Specialized Nodes ===

class StructDefNode(StmtNode):
    def __init__(self, name: str, fields: list, line: int, column: int):
        """
        fields: list of tuples (field_name: str, field_type: str or None)
        """
        super().__init__(line, column)
        self.name = name
        self.fields = fields

    def accept(self, visitor):
        return visitor.visit_struct_def(self)

    def __str__(self):
        fields_str = ', '.join(f"{name}: {typ}" if typ else name for name, typ in self.fields)
        return f"struct {self.name} {{ {fields_str} }}"


class ImportNode(StmtNode):
    def __init__(self, module_name: str, line: int, column: int):
        super().__init__(line, column)
        self.module_name = module_name

    def accept(self, visitor):
        return visitor.visit_import(self)

    def __str__(self):
        return f"import {self.module_name};"


# === Example Visitor Interface ===

class ASTVisitor(ABC):
    """
    Example visitor interface to be implemented by interpreter/compiler/transformers.
    """

    @abstractmethod
    def visit_binary_op(self, node: BinaryOpNode):
        pass

    @abstractmethod
    def visit_unary_op(self, node: UnaryOpNode):
        pass

    @abstractmethod
    def visit_literal(self, node: LiteralNode):
        pass

    @abstractmethod
    def visit_variable(self, node: VariableNode):
        pass

    @abstractmethod
    def visit_call(self, node: CallNode):
        pass

    @abstractmethod
    def visit_if(self, node: IfNode):
        pass

    @abstractmethod
    def visit_while(self, node: WhileNode):
        pass

    @abstractmethod
    def visit_for(self, node: ForNode):
        pass

    @abstractmethod
    def visit_return(self, node: ReturnNode):
        pass

    @abstractmethod
    def visit_block(self, node: BlockNode):
        pass

    @abstractmethod
    def visit_function_def(self, node: FunctionDefNode):
        pass

    @abstractmethod
    def visit_variable_decl(self, node: VariableDeclNode):
        pass

    @abstractmethod
    def visit_assignment(self, node: AssignmentNode):
        pass

    @abstractmethod
    def visit_struct_def(self, node: StructDefNode):
        pass

    @abstractmethod
    def visit_import(self, node: ImportNode):
        pass
