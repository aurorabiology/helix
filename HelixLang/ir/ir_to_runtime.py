# helixlang/ir/ir_to_runtime.py

from helixlang.ir.ir_nodes import NodeType

class IRToRuntime:
    """
    Converts HelixLang IR nodes into runtime-executable instructions.
    Uses a simple stack-based bytecode model.
    """

    def __init__(self, ir_root):
        self.ir_root = ir_root
        self.bytecode = []
        self.debug_info = []  # Optional: store source locations or annotations per instruction

    def compile(self):
        self._emit_node(self.ir_root)
        return self.bytecode

    def _emit_node(self, node):
        """
        Dispatch based on IR node type.
        Recursively emits instructions for children nodes first if needed.
        """

        # Optional debug hook: attach source location info if available
        def emit_with_debug(instr):
            self.bytecode.append(instr)
            if 'source_loc' in getattr(node, 'metadata', {}):
                self.debug_info.append((len(self.bytecode) - 1, node.metadata['source_loc']))

        if node.node_type == NodeType.FUNCTION:
            emit_with_debug(f"FUNC_START {node.name}")
            # Emit parameter handling (assuming params are variables)
            for param in node.params:
                emit_with_debug(f"PARAM {param}")
            # Emit function body
            for child in node.children:
                self._emit_node(child)
            emit_with_debug("FUNC_END")

        elif node.node_type == NodeType.ASSIGNMENT:
            # Emit value first (stack push)
            target_node, value_node = node.children
            self._emit_node(value_node)
            # Store top of stack into variable
            emit_with_debug(f"STORE {target_node.name}")

        elif node.node_type == NodeType.VARIABLE:
            # Push variable value onto stack
            emit_with_debug(f"LOAD {node.name}")

        elif node.node_type == NodeType.CONSTANT:
            # Push constant value onto stack
            value = node.metadata.get('value', None)
            emit_with_debug(f"PUSH_CONST {value}")

        elif node.node_type == NodeType.BINARY_OP:
            # Evaluate left and right operands
            self._emit_node(node.left)
            self._emit_node(node.right)
            # Emit operator instruction
            op_instr = self._map_operator_to_instr(node.operator)
            emit_with_debug(op_instr)

        elif node.node_type == NodeType.CALL:
            # Evaluate arguments in order (push on stack)
            for arg in node.arguments:
                self._emit_node(arg)
            # Emit call instruction
            emit_with_debug(f"CALL {node.function_name} {len(node.arguments)}")

        elif node.node_type == NodeType.RETURN:
            if node.children:
                self._emit_node(node.children[0])  # Return value
            else:
                emit_with_debug("PUSH_CONST None")  # Return None if no value
            emit_with_debug("RETURN")

        elif node.node_type == NodeType.IF:
            # Simple example of conditional jump with labels
            else_label = self._new_label("else")
            end_label = self._new_label("endif")

            # Emit condition
            self._emit_node(node.condition)
            emit_with_debug(f"JUMP_IF_FALSE {else_label}")

            # Emit then block
            for stmt in node.then_block:
                self._emit_node(stmt)
            emit_with_debug(f"JUMP {end_label}")

            # Else block
            emit_with_debug(f"LABEL {else_label}")
            for stmt in node.else_block:
                self._emit_node(stmt)

            emit_with_debug(f"LABEL {end_label}")

        elif node.node_type == NodeType.WHILE:
            start_label = self._new_label("while_start")
            end_label = self._new_label("while_end")

            emit_with_debug(f"LABEL {start_label}")
            self._emit_node(node.condition)
            emit_with_debug(f"JUMP_IF_FALSE {end_label}")

            for stmt in node.body:
                self._emit_node(stmt)
            emit_with_debug(f"JUMP {start_label}")
            emit_with_debug(f"LABEL {end_label}")

        elif node.node_type == NodeType.BLOCK:
            for stmt in node.children:
                self._emit_node(stmt)

        else:
            raise NotImplementedError(f"IRToRuntime: Unsupported node type {node.node_type}")

    def _map_operator_to_instr(self, operator_str):
        """
        Map IR operator strings to bytecode instructions.
        """
        op_map = {
            '+': "ADD",
            '-': "SUB",
            '*': "MUL",
            '/': "DIV",
            '%': "MOD",
            '==': "EQ",
            '!=': "NEQ",
            '<': "LT",
            '<=': "LTE",
            '>': "GT",
            '>=': "GTE",
            'and': "AND",
            'or': "OR",
            # Add more as needed
        }
        if operator_str not in op_map:
            raise ValueError(f"Unknown operator for bytecode: {operator_str}")
        return op_map[operator_str]

    _label_counter = 0

    def _new_label(self, prefix):
        """
        Generate unique labels for jumps.
        """
        self._label_counter += 1
        return f"{prefix}_{self._label_counter}"

