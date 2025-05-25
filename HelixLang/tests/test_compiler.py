import pytest
from helixlang.parser import parse_code
from helixlang.compiler import compile_ast
from helixlang.ir import IRInstruction, IRBlock, IRFunction, IRModule

# ---------------------
# BASIC EXPRESSION COMPILATION
# ---------------------

def test_basic_arithmetic_expression():
    ast = parse_code("x = 1 + 2 * 3")
    ir = compile_ast(ast)
    assert isinstance(ir, IRModule)
    assert any(instr.op == "add" or instr.op == "mul" for instr in ir.flatten())

def test_string_assignment():
    ast = parse_code('msg = "hello"')
    ir = compile_ast(ast)
    assert any(instr.op == "assign" and instr.args[1] == "hello" for instr in ir.flatten())


# ---------------------
# IF/ELSE & BRANCHING
# ---------------------

def test_if_else_generates_branching():
    ast = parse_code("if x > 0: y = 1 else: y = 2")
    ir = compile_ast(ast)
    opcodes = [instr.op for instr in ir.flatten()]
    assert "branch" in opcodes
    assert "compare_gt" in opcodes
    assert "label" in opcodes

def test_nested_conditionals():
    ast = parse_code("""
    if x > 5:
        if y < 3:
            z = 1
    else:
        z = 2
    """)
    ir = compile_ast(ast)
    assert "branch" in [i.op for i in ir.flatten()]
    assert sum(1 for i in ir.flatten() if i.op == "label") >= 2


# ---------------------
# LOOPS AND FLOW
# ---------------------

def test_for_loop_generates_iteration():
    ast = parse_code("""
    total = 0
    for i in range(3):
        total = total + i
    """)
    ir = compile_ast(ast)
    ops = [instr.op for instr in ir.flatten()]
    assert "loop_init" in ops
    assert "loop_cond" in ops
    assert "loop_body" in ops
    assert "loop_end" in ops

def test_while_loop_constructs_correctly():
    ast = parse_code("""
    i = 0
    while i < 5:
        i = i + 1
    """)
    ir = compile_ast(ast)
    ops = [instr.op for instr in ir.flatten()]
    assert "compare_lt" in ops
    assert "jump" in ops


# ---------------------
# FUNCTION DEFINITIONS
# ---------------------

def test_function_compilation():
    ast = parse_code("""
    def square(n):
        return n * n
    """)
    ir = compile_ast(ast)
    functions = [block for block in ir.blocks if isinstance(block, IRFunction)]
    assert any(f.name == "square" for f in functions)

def test_function_call_and_arguments():
    ast = parse_code("""
    def f(x): return x + 1
    y = f(5)
    """)
    ir = compile_ast(ast)
    ops = [instr.op for instr in ir.flatten()]
    assert "call" in ops
    assert "function_def" in ops


# ---------------------
# SSA / SYMBOL TRACKING
# ---------------------

def test_unique_variable_versioning_ssa():
    ast = parse_code("""
    a = 1
    a = a + 1
    """)
    ir = compile_ast(ast)
    assignments = [instr for instr in ir.flatten() if instr.op == "assign"]
    vars = [instr.target for instr in assignments]
    assert len(set(vars)) == len(vars)  # All versions are unique


# ---------------------
# OPTIMIZATION PASSES
# ---------------------

def test_dead_code_elimination():
    ast = parse_code("""
    x = 1
    y = 2
    x = 3  # Dead: x overwritten before use
    print(y)
    """)
    ir = compile_ast(ast, optimize=True)
    ops = [instr.op for instr in ir.flatten()]
    assert ops.count("assign") < 3  # One assign eliminated

def test_constant_folding():
    ast = parse_code("x = 2 + 3 * 4")
    ir = compile_ast(ast, optimize=True)
    folded = any(instr.op == "assign" and instr.args[1] == 14 for instr in ir.flatten())
    assert folded


# ---------------------
# TARGET CODEGEN STUBS (for backend compilation or export)
# ---------------------

def test_codegen_to_target_representation():
    ast = parse_code("x = 10")
    ir = compile_ast(ast)
    code = ir.to_target("LLVM")  # hypothetical backend
    assert "store" in code or "mov" in code or isinstance(code, str)


# ---------------------
# ERROR CASES
# ---------------------

def test_invalid_ast_raises():
    with pytest.raises(Exception):
        compile_ast(None)

def test_unknown_construct_fails():
    ast = parse_code("unknown_construct()")
    with pytest.raises(NotImplementedError):
        compile_ast(ast)


# ---------------------
# HELPER ASSERTIONS
# ---------------------

def test_instruction_integrity():
    ast = parse_code("x = 2 + 2")
    ir = compile_ast(ast)
    for instr in ir.flatten():
        assert isinstance(instr, IRInstruction)
        assert instr.op is not None
