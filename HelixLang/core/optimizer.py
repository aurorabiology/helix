# optimizer.py

from helixlang.ast_nodes import (
    ASTNode, BinaryOpNode, UnaryOpNode, LiteralNode, VariableNode, 
    IfNode, WhileNode, ForNode, BlockNode, FunctionDefNode, AssignmentNode
)

class Optimizer:
    """
    Orchestrates optimization passes on the AST.
    """

    def __init__(self, passes=None):
        # List of optimization passes to run, by default runs all
        self.passes = passes or [
            self.constant_folding,
            self.dead_code_elimination,
            # Future passes: loop_unrolling, inline_expansion, cse...
        ]

    def optimize(self, ast: ASTNode) -> ASTNode:
        """
        Run all configured optimization passes on the AST.
        """
        for opt_pass in self.passes:
            ast = opt_pass(ast)
        return ast

    def constant_folding(self, node: ASTNode) -> ASTNode:
        """
        Recursively fold constant expressions.
        e.g. Replace (2 + 3) with 5, or (true && false) with false.
        """
        if isinstance(node, BinaryOpNode):
            left = self.constant_folding(node.left)
            right = self.constant_folding(node.right)

            if isinstance(left, LiteralNode) and isinstance(right, LiteralNode):
                folded_value = self._evaluate_binary_op(node.operator, left.value, right.value)
                if folded_value is not None:
                    return LiteralNode(folded_value, node.line, node.column)

            return BinaryOpNode(node.operator, left, right, node.line, node.column)

        elif isinstance(node, UnaryOpNode):
            operand = self.constant_folding(node.operand)
            if isinstance(operand, LiteralNode):
                folded_value = self._evaluate_unary_op(node.operator, operand.value)
                if folded_value is not None:
                    return LiteralNode(folded_value, node.line, node.column)
            return UnaryOpNode(node.operator, operand, node.line, node.column)

        elif isinstance(node, IfNode):
            node.condition = self.constant_folding(node.condition)
            node.then_branch = self.constant_folding(node.then_branch)
            node.else_branch = self.constant_folding(node.else_branch) if node.else_branch else None
            return node

        elif isinstance(node, WhileNode):
            node.condition = self.constant_folding(node.condition)
            node.body = self.constant_folding(node.body)
            return node

        elif isinstance(node, ForNode):
            node.init = self.constant_folding(node.init) if node.init else None
            node.condition = self.constant_folding(node.condition) if node.condition else None
            node.increment = self.constant_folding(node.increment) if node.increment else None
            node.body = self.constant_folding(node.body)
            return node

        elif isinstance(node, BlockNode):
            node.statements = [self.constant_folding(stmt) for stmt in node.statements]
            return node

        elif isinstance(node, FunctionDefNode):
            node.body = self.constant_folding(node.body)
            return node

        elif isinstance(node, AssignmentNode):
            node.value = self.constant_folding(node.value)
            return node

        # Default: leaf nodes or unsupported nodes returned as is
        return node

    def dead_code_elimination(self, node: ASTNode) -> ASTNode:
        """
        Remove unreachable or redundant code.
        Example: code after a return statement, branches of 'if' with constant false condition.
        """
        if isinstance(node, BlockNode):
            new_statements = []
            has_returned = False
            for stmt in node.statements:
                if has_returned:
                    # Skip unreachable code after return
                    continue
                optimized_stmt = self.dead_code_elimination(stmt)
                new_statements.append(optimized_stmt)
                if isinstance(optimized_stmt, (ReturnNode,)):
                    has_returned = True
            node.statements = new_statements
            return node

        elif isinstance(node, IfNode):
            node.condition = self.dead_code_elimination(node.condition)
            node.then_branch = self.dead_code_elimination(node.then_branch)
            if node.else_branch:
                node.else_branch = self.dead_code_elimination(node.else_branch)

            # If condition is constant true or false, replace with branch only
            if isinstance(node.condition, LiteralNode):
                if node.condition.value is True:
                    return node.then_branch
                elif node.condition.value is False:
                    return node.else_branch or BlockNode([])  # Empty block if no else

            return node

        elif isinstance(node, WhileNode):
            node.condition = self.dead_code_elimination(node.condition)
            node.body = self.dead_code_elimination(node.body)

            # If condition is constant false, remove the loop entirely
            if isinstance(node.condition, LiteralNode) and node.condition.value is False:
                return BlockNode([])  # Empty block

            return node

        elif isinstance(node, ForNode):
            node.init = self.dead_code_elimination(node.init) if node.init else None
            node.condition = self.dead_code_elimination(node.condition) if node.condition else None
            node.increment = self.dead_code_elimination(node.increment) if node.increment else None
            node.body = self.dead_code_elimination(node.body)

            # If condition is constant false, remove loop
            if node.condition and isinstance(node.condition, LiteralNode) and node.condition.value is False:
                return BlockNode([])

            return node

        elif isinstance(node, FunctionDefNode):
            node.body = self.dead_code_elimination(node.body)
            return node

        elif isinstance(node, AssignmentNode):
            node.value = self.dead_code_elimination(node.value)
            return node

        elif isinstance(node, BinaryOpNode):
            node.left = self.dead_code_elimination(node.left)
            node.right = self.dead_code_elimination(node.right)
            return node

        elif isinstance(node, UnaryOpNode):
            node.operand = self.dead_code_elimination(node.operand)
            return node

        # Default fallback
        return node

    # Helper evaluation functions for constant folding

    def _evaluate_binary_op(self, operator: str, left_val, right_val):
        try:
            if operator == '+':
                return left_val + right_val
            elif operator == '-':
                return left_val - right_val
            elif operator == '*':
                return left_val * right_val
            elif operator == '/':
                # Avoid division by zero folding here - runtime error should catch it
                return left_val / right_val if right_val != 0 else None
            elif operator == '==':
                return left_val == right_val
            elif operator == '!=':
                return left_val != right_val
            elif operator == '<':
                return left_val < right_val
            elif operator == '<=':
                return left_val <= right_val
            elif operator == '>':
                return left_val > right_val
            elif operator == '>=':
                return left_val >= right_val
            elif operator == '&&':
                return left_val and right_val
            elif operator == '||':
                return left_val or right_val
            else:
                return None
        except Exception:
            return None

    def _evaluate_unary_op(self, operator: str, operand_val):
        try:
            if operator == '-':
                return -operand_val
            elif operator == '!':
                return not operand_val
            else:
                return None
        except Exception:
            return None
