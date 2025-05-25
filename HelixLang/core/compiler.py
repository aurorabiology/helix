# compiler.py

from ast_nodes import *
import ir_nodes as ir

class Compiler(ASTVisitor):
    def __init__(self):
        self.instructions = []
        self.current_reg = 0
        self.label_count = 0
        self.function_bodies = {}  # name -> list of IR instructions
        self.current_function = None

    # Helper to generate fresh virtual registers
    def new_reg(self):
        reg = f"r{self.current_reg}"
        self.current_reg += 1
        return reg

    # Helper to generate unique labels
    def new_label(self, prefix="L"):
        label = f"{prefix}{self.label_count}"
        self.label_count += 1
        return label

    # Entry point
    def compile(self, node: ASTNode):
        self.instructions.clear()
        self.current_reg = 0
        self.label_count = 0
        self.current_function = None

        node.accept(self)

        # Optionally run optimizer here:
        # self.instructions = optimizer.optimize(self.instructions)

        return self.instructions

    # --- Expressions ---

    def visit_literal(self, node: LiteralNode):
        reg = self.new_reg()
        self.instructions.append(ir.IRLoadConst(reg, node.value))
        return reg

    def visit_variable(self, node: VariableNode):
        reg = self.new_reg()
        self.instructions.append(ir.IRLoadVar(reg, node.name))
        return reg

    def visit_binary_op(self, node: BinaryOpNode):
        left_reg = node.left.accept(self)
        right_reg = node.right.accept(self)
        dest_reg = self.new_reg()
        self.instructions.append(ir.IRBinaryOp(node.operator, dest_reg, left_reg, right_reg))
        return dest_reg

    def visit_unary_op(self, node: UnaryOpNode):
        operand_reg = node.operand.accept(self)
        dest_reg = self.new_reg()
        # For simplicity: treat unary minus as binary 0 - operand
        if node.operator == '-':
            zero_reg = self.new_reg()
            self.instructions.append(ir.IRLoadConst(zero_reg, 0))
            self.instructions.append(ir.IRBinaryOp('-', dest_reg, zero_reg, operand_reg))
        elif node.operator == '!':
            # Could define a special IRUnaryOp, but let's fake with binary '==' to 0
            zero_reg = self.new_reg()
            self.instructions.append(ir.IRLoadConst(zero_reg, 0))
            self.instructions.append(ir.IRBinaryOp('==', dest_reg, operand_reg, zero_reg))
        else:
            raise Exception(f"Unknown unary operator {node.operator}")
        return dest_reg

    def visit_call(self, node: CallNode):
        arg_regs = [arg.accept(self) for arg in node.arguments]
        dest_reg = self.new_reg()
        # Assuming function name is a VariableNode or a string
        if isinstance(node.callee, VariableNode):
            func_name = node.callee.name
        else:
            raise Exception("Complex callables not supported in this IR")
        self.instructions.append(ir.IRCall(dest_reg, func_name, arg_regs))
        return dest_reg

    # --- Statements ---

    def visit_variable_decl(self, node: VariableDeclNode):
        if node.initializer:
            value_reg = node.initializer.accept(self)
            self.instructions.append(ir.IRStoreVar(node.name, value_reg))
        else:
            # Initialize to None or 0 by default
            default_reg = self.new_reg()
            self.instructions.append(ir.IRLoadConst(default_reg, None))
            self.instructions.append(ir.IRStoreVar(node.name, default_reg))

    def visit_assignment(self, node: AssignmentNode):
        value_reg = node.value.accept(self)
        self.instructions.append(ir.IRStoreVar(node.target.name, value_reg))

    def visit_block(self, node: BlockNode):
        for stmt in node.statements:
            stmt.accept(self)

    def visit_if(self, node: IfNode):
        cond_reg = node.condition.accept(self)
        else_label = self.new_label("else")
        end_label = self.new_label("endif")

        # Jump to else if condition is false
        self.instructions.append(ir.IRJumpIfFalse(cond_reg, else_label))

        node.then_branch.accept(self)
        self.instructions.append(ir.IRJump(end_label))

        self.instructions.append(ir.IRLabel(else_label))
        if node.else_branch:
            node.else_branch.accept(self)
        self.instructions.append(ir.IRLabel(end_label))

    def visit_while(self, node: WhileNode):
        start_label = self.new_label("while_start")
        end_label = self.new_label("while_end")

        self.instructions.append(ir.IRLabel(start_label))
        cond_reg = node.condition.accept(self)
        self.instructions.append(ir.IRJumpIfFalse(cond_reg, end_label))
        node.body.accept(self)
        self.instructions.append(ir.IRJump(start_label))
        self.instructions.append(ir.IRLabel(end_label))

    def visit_for(self, node: ForNode):
        self.push_scope()  # If scope management is implemented

        node.initializer.accept(self)

        start_label = self.new_label("for_start")
        end_label = self.new_label("for_end")

        self.instructions.append(ir.IRLabel(start_label))
        cond_reg = node.condition.accept(self)
        self.instructions.append(ir.IRJumpIfFalse(cond_reg, end_label))

        node.body.accept(self)
        node.increment.accept(self)
        self.instructions.append(ir.IRJump(start_label))
        self.instructions.append(ir.IRLabel(end_label))

        self.pop_scope()

    def visit_return(self, node: ReturnNode):
        if node.value:
            ret_reg = node.value.accept(self)
        else:
            ret_reg = None
        self.instructions.append(ir.IRReturn(ret_reg))

    def visit_function_def(self, node: FunctionDefNode):
        # Compile function body into separate instruction list
        saved_instructions = self.instructions
        self.instructions = []

        self.current_function = node.name
        node.body.accept(self)
        body_instructions = self.instructions

        self.instructions = saved_instructions
        self.instructions.append(ir.IRFunctionDef(node.name, body_instructions))
        self.current_function = None

    def visit_struct_def(self, node: StructDefNode):
        # For now, just generate a no-op or metadata instruction
        self.instructions.append(ir.IRNoOp())

    def visit_import(self, node: ImportNode):
        # Imports might translate to special IR or be handled at runtime
        self.instructions.append(ir.IRNoOp())

    # Optional scope management helpers
    def push_scope(self):
        # For variable scoping in IR if needed
        pass

    def pop_scope(self):
        pass
