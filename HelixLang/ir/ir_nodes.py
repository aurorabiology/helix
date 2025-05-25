# helixlang/ir/ir_nodes.py

"""
Defines IR node types and structures for HelixLang.

Each node represents a language construct in the IR tree.
Supports metadata for source location, typing, and annotations.
Designed for easy traversal, transformation, and safe optimizations.
"""

from enum import Enum, auto
from typing import List, Optional, Any, Dict, Union

class NodeType(Enum):
    FUNCTION = auto()
    VARIABLE = auto()
    ASSIGNMENT = auto()
    IF = auto()
    WHILE = auto()
    EXPRESSION = auto()
    CALL = auto()
    RETURN = auto()
    CONSTANT = auto()
    BINARY_OP = auto()
    UNARY_OP = auto()
    BLOCK = auto()
    # Extend as HelixLang evolves


class IRNode:
    """
    Base class for all IR nodes.
    
    Attributes:
        node_type: NodeType enum indicating the kind of node.
        children: List of child IRNode instances (for traversal).
        metadata: Dict for storing source info, typing, annotations.
    """
    __slots__ = ('node_type', 'children', 'metadata')

    def __init__(
        self, 
        node_type: NodeType, 
        children: Optional[List['IRNode']] = None, 
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.node_type = node_type
        self.children = children if children is not None else []
        self.metadata = metadata if metadata is not None else {}

    def __repr__(self):
        return f"<IRNode {self.node_type.name} children={len(self.children)}>"

    def traverse(self):
        """Generator for traversing the IR tree depth-first."""
        yield self
        for child in self.children:
            yield from child.traverse()

    def copy_with_new_children(self, new_children: List['IRNode']) -> 'IRNode':
        """
        Returns a copy of the node with new children.
        Useful for transformations that replace subtrees.
        """
        raise NotImplementedError("Subclasses must implement copy_with_new_children.")


class FunctionNode(IRNode):
    def __init__(
        self, 
        name: str, 
        params: List[str], 
        body: List[IRNode], 
        return_type: Optional[str], 
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(NodeType.FUNCTION, children=body, metadata=metadata)
        self.name = name
        self.params = params
        self.return_type = return_type

    def __repr__(self):
        params_str = ', '.join(self.params)
        return f"<FunctionNode {self.name}({params_str}) -> {self.return_type}>"

    def copy_with_new_children(self, new_children: List[IRNode]) -> 'FunctionNode':
        return FunctionNode(
            name=self.name,
            params=self.params,
            body=new_children,
            return_type=self.return_type,
            metadata=self.metadata.copy()
        )


class VariableNode(IRNode):
    def __init__(
        self, 
        name: str, 
        var_type: Optional[str], 
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(NodeType.VARIABLE, metadata=metadata)
        self.name = name
        self.var_type = var_type

    def __repr__(self):
        return f"<VariableNode {self.name}: {self.var_type}>"

    def copy_with_new_children(self, new_children: List[IRNode]) -> 'VariableNode':
        # Variable nodes generally don't have children, so ignore new_children
        return VariableNode(
            name=self.name,
            var_type=self.var_type,
            metadata=self.metadata.copy()
        )


class AssignmentNode(IRNode):
    def __init__(
        self, 
        target: VariableNode, 
        value: IRNode, 
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(NodeType.ASSIGNMENT, children=[target, value], metadata=metadata)
        self.target = target
        self.value = value

    def __repr__(self):
        return f"<AssignmentNode {self.target.name} = ...>"

    def copy_with_new_children(self, new_children: List[IRNode]) -> 'AssignmentNode':
        return AssignmentNode(
            target=new_children[0],
            value=new_children[1],
            metadata=self.metadata.copy()
        )


class IfNode(IRNode):
    def __init__(
        self, 
        condition: IRNode, 
        then_body: List[IRNode], 
        else_body: Optional[List[IRNode]] = None, 
        metadata: Optional[Dict[str, Any]] = None
    ):
        children = [condition] + then_body
        if else_body:
            children += else_body
        super().__init__(NodeType.IF, children=children, metadata=metadata)
        self.condition = condition
        self.then_body = then_body
        self.else_body = else_body or []

    def __repr__(self):
        return f"<IfNode condition={repr(self.condition)}>"

    def copy_with_new_children(self, new_children: List[IRNode]) -> 'IfNode':
        cond = new_children[0]
        then_len = len(self.then_body)
        then_body = new_children[1:1+then_len]
        else_body = new_children[1+then_len:] if len(new_children) > 1+then_len else []
        return IfNode(
            condition=cond,
            then_body=then_body,
            else_body=else_body,
            metadata=self.metadata.copy()
        )


class WhileNode(IRNode):
    def __init__(
        self, 
        condition: IRNode, 
        body: List[IRNode], 
        metadata: Optional[Dict[str, Any]] = None
    ):
        children = [condition] + body
        super().__init__(NodeType.WHILE, children=children, metadata=metadata)
        self.condition = condition
        self.body = body

    def __repr__(self):
        return f"<WhileNode condition={repr(self.condition)}>"

    def copy_with_new_children(self, new_children: List[IRNode]) -> 'WhileNode':
        cond = new_children[0]
        body = new_children[1:]
        return WhileNode(
            condition=cond,
            body=body,
            metadata=self.metadata.copy()
        )


class ExpressionNode(IRNode):
    def __init__(
        self, 
        expression_type: str, 
        value: Any = None, 
        children: Optional[List[IRNode]] = None, 
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(NodeType.EXPRESSION, children=children, metadata=metadata)
        self.expression_type = expression_type  # e.g., 'binary_op', 'literal', 'variable_ref'
        self.value = value

    def __repr__(self):
        return f"<ExpressionNode type={self.expression_type} value={self.value}>"

    def copy_with_new_children(self, new_children: List[IRNode]) -> 'ExpressionNode':
        return ExpressionNode(
            expression_type=self.expression_type,
            value=self.value,
            children=new_children,
            metadata=self.metadata.copy()
        )


class CallNode(IRNode):
    def __init__(
        self, 
        function_name: str, 
        arguments: List[IRNode], 
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(NodeType.CALL, children=arguments, metadata=metadata)
        self.function_name = function_name
        self.arguments = arguments

    def __repr__(self):
        args_repr = ", ".join(repr(arg) for arg in self.arguments)
        return f"<CallNode {self.function_name}({args_repr})>"

    def copy_with_new_children(self, new_children: List[IRNode]) -> 'CallNode':
        return CallNode(
            function_name=self.function_name,
            arguments=new_children,
            metadata=self.metadata.copy()
        )


class ReturnNode(IRNode):
    def __init__(
        self, 
        value: Optional[IRNode] = None, 
        metadata: Optional[Dict[str, Any]] = None
    ):
        children = [value] if value else []
        super().__init__(NodeType.RETURN, children=children, metadata=metadata)
        self.value = value

    def __repr__(self):
        return f"<ReturnNode value={repr(self.value)}>"

    def copy_with_new_children(self, new_children: List[IRNode]) -> 'ReturnNode':
        value = new_children[0] if new_children else None
        return ReturnNode(
            value=value,
            metadata=self.metadata.copy()
        )


class ConstantNode(IRNode):
    def __init__(
        self, 
        value: Any, 
        const_type: Optional[str] = None, 
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(NodeType.CONSTANT, metadata=metadata)
        self.value = value
        self.const_type = const_type

    def __repr__(self):
        return f"<ConstantNode {self.value} : {self.const_type}>"

    def copy_with_new_children(self, new_children: List[IRNode]) -> 'ConstantNode':
        # Constants have no children, ignore new_children
        return ConstantNode(
            value=self.value,
            const_type=self.const_type,
            metadata=self.metadata.copy()
        )


# Additional node types like BinaryOpNode, UnaryOpNode, BlockNode, etc. can be added below.

class BinaryOpNode(ExpressionNode):
    def __init__(
        self,
        operator: str,
        left: IRNode,
        right: IRNode,
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            expression_type="binary_op",
            children=[left, right],
            metadata=metadata
        )
        self.operator = operator
        self.left = left
        self.right = right

    def __repr__(self):
        return f"<BinaryOpNode {repr(self.left)} {self.operator} {repr(self.right)}>"

    def copy_with_new_children(self, new_children: List[IRNode]) -> 'BinaryOpNode':
        return BinaryOpNode(
            operator=self.operator,
            left=new_children[0],
            right=new_children[1],
            metadata=self.metadata.copy()
        )


class UnaryOpNode(ExpressionNode):
    def __init__(
        self,
        operator: str,
        operand: IRNode,
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            expression_type="unary_op",
            children=[operand],
            metadata=metadata
        )
        self.operator = operator
        self.operand = operand

    def __repr__(self):
        return f"<UnaryOpNode {self.operator}{repr(self.operand)}>"

    def copy_with_new_children(self, new_children: List[IRNode]) -> 'UnaryOpNode':
        return UnaryOpNode(
            operator=self.operator,
            operand=new_children[0],
            metadata=self.metadata.copy()
        )


class BlockNode(IRNode):
    def __init__(
        self,
        statements: List[IRNode],
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(NodeType.BLOCK, children=statements, metadata=metadata)
        self.statements = statements

    def __repr__(self):
        return f"<BlockNode statements={len(self.statements)}>"

    def copy_with_new_children(self, new_children: List[IRNode]) -> 'BlockNode':
        return BlockNode(
            statements=new_children,
            metadata=self.metadata.copy()
        )
