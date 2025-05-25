# helixlang/ir/__init__.py

"""
HelixLang Intermediate Representation (IR) abstraction layer.

This module exposes the core IR builder, IR node definitions,
optimization passes, and runtime conversion utilities.

Usage example:
    from helixlang.ir import ir_builder, ir_nodes, ir_optimizer, ir_to_runtime

    # Build IR from AST
    builder = ir_builder.IRBuilder(ast_root)
    ir_root = builder.build()

    # Optimize IR
    optimizer = ir_optimizer.IROptimizer(ir_root)
    optimizer.optimize()

    # Convert IR to runtime format
    compiler = ir_to_runtime.IRToRuntime(ir_root)
    bytecode = compiler.compile()
"""

__version__ = "0.1.0"

# Expose main submodules
from . import ir_builder
from . import ir_nodes
from . import ir_optimizer
from . import ir_to_runtime

# Optional convenience shortcuts
from .ir_nodes import IRNode, NodeType, FunctionNode, VariableNode
from .ir_builder import IRBuilder
from .ir_optimizer import IROptimizer
from .ir_to_runtime import IRToRuntime

# Utility function example for debugging IR trees
def print_ir(node, indent=0):
    """ Recursively prints the IR tree for visualization and debugging. """
    prefix = "  " * indent
    print(f"{prefix}{repr(node)}")
    for child in getattr(node, 'children', []):
        print_ir(child, indent + 1)
