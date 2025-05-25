# helixlang/ir/ir_optimizer.py

from helixlang.ir.ir_nodes import (
    IRNode,
    NodeType,
    ConstantNode,
    AssignmentNode,
    BinaryOpNode,
    BlockNode,
    FunctionNode,
    ReturnNode,
)
import operator

class IROptimizer:
    """
    Manages and applies optimization passes to the IR tree.
    """

    def __init__(self, ir_root: IRNode):
        self.ir_root = ir_root
        # Define pass sequence here, easily extendable
        self.passes = [
            self.constant_folding_pass,
            self.dead_code_elimination_pass,
            # Add more passes here...
        ]

    def optimize(self):
        """
        Apply all optimization passes sequentially.
        """
        for optimization_pass in self.passes:
            self.ir_root = optimization_pass(self.ir_root)
        return self.ir_root

    #########################
    # Pass 1: Constant Folding
    #########################
    def constant_folding_pass(self, node: IRNode) -> IRNode:
        """
        Recursively fold constant expressions into constants.
        """

        # Post-order traversal: optimize children first
        new_children = []
        for child in getattr(node, 'children', []):
            optimized_child = self.constant_folding_pass(child)
            new_children.append(optimized_child)

        # Replace children with optimized ones
        if hasattr(node, 'children'):
            node.children = new_children

        # Handle specific node types
        if node.node_type == NodeType.BINARY_OP or node.node_type == NodeType.EXPRESSION:
            return self._fold_binary_op(node)

        elif node.node_type == NodeType.ASSIGNMENT:
            # Assignment target typically variable node, value can be folded
            target, value = node.children
            folded_value = self.constant_folding_pass(value)
            node.children[1] = folded_value
            return node

        elif node.node_type == NodeType.FUNCTION:
            # Fold inside function body
            folded_body = []
            for child in node.children:
                folded_body.append(self.constant_folding_pass(child))
            node.children = folded_body
            return node

        elif node.node_type == NodeType.BLOCK:
            # Fold inside blocks
            folded_stmts = []
            for stmt in node.children:
                folded_stmts.append(self.constant_folding_pass(stmt))
            node.children = folded_stmts
            return node

        # Base case: return node unchanged
        return node

    def _fold_binary_op(self, node: IRNode) -> IRNode:
        """
        If both operands are constants, evaluate and return a ConstantNode.
        """

        if not hasattr(node, 'left') or not hasattr(node, 'right') or not hasattr(node, 'operator'):
            # Defensive: if node does not match expected BinaryOp shape, skip folding
            return node

        left = node.left
        right = node.right
        op = node.operator

        if self._is_constant_node(left) and self._is_constant_node(right):
            try:
                # Evaluate based on operator
                value = self._evaluate_binary_op(op, left.value, right.value)
                # Return new constant node
                return ConstantNode(value=value, const_type=type(value).__name__)
            except Exception:
                # If evaluation fails, skip folding
                return node
        return node

    def _is_constant_node(self, node: IRNode) -> bool:
        return node.node_type == NodeType.CONSTANT

    def _evaluate_binary_op(self, operator_str: str, left_val, right_val):
        """
        Map operator string to actual Python operation and execute.
        """
        ops = {
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': operator.truediv,
            '%': operator.mod,
            '==': operator.eq,
            '!=': operator.ne,
            '<': operator.lt,
            '<=': operator.le,
            '>': operator.gt,
            '>=': operator.ge,
            'and': operator.and_,
            'or': operator.or_,
            # Add more operators as needed
        }
        if operator_str not in ops:
            raise ValueError(f"Unsupported operator for folding: {operator_str}")
        return ops[operator_str](left_val, right_val)

    ##############################
    # Pass 2: Dead Code Elimination
    ##############################
    def dead_code_elimination_pass(self, node: IRNode) -> IRNode:
        """
        Recursively remove IR nodes that have no effect, such as:
        - Unreachable code after return
        - Variables assigned but never used (basic)
        """

        # Handle different node types
        if node.node_type == NodeType.FUNCTION:
            # Dead code elimination inside function body
            node.children = self._eliminate_dead_code_block(node.children)
            return node

        elif node.node_type == NodeType.BLOCK:
            # Dead code elimination inside block
            node.children = self._eliminate_dead_code_block(node.children)
            return node

        # Other nodes are returned unchanged
        return node

    def _eliminate_dead_code_block(self, statements):
        """
        Remove statements that come after an unconditional return.
        Basic dead code elimination.
        """
        new_statements = []
        has_returned = False

        for stmt in statements:
            if has_returned:
                # Statement unreachable - drop it
                continue

            optimized_stmt = self.dead_code_elimination_pass(stmt)
            new_statements.append(optimized_stmt)

            if stmt.node_type == NodeType.RETURN:
                has_returned = True

        return new_statements

    # Additional utility passes (e.g., loop unrolling, inline expansion) can be added similarly.

