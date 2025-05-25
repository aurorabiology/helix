import pytest
from helixlang.parser import parse_code
from helixlang.ast import (
    LoadProteinNode,
    AssignNode,
    IdentifierNode,
    IfNode,
    ForNode,
    MutateNode,
    SimulateNode,
    BlockNode,
    NumberNode,
    StringNode,
    ParseError,
)

# -------------------------------
# Valid Single-Line Statement Tests
# -------------------------------

def test_load_protein_stmt():
    tree = parse_code('protein A = load("P12345")')
    stmt = tree.body[0]
    assert isinstance(stmt, AssignNode)
    assert isinstance(stmt.value, LoadProteinNode)
    assert stmt.value.accession == "P12345"
    assert stmt.target.name == "A"

def test_assignment_with_math_expr():
    tree = parse_code("x = 5 + 2 * 3")
    stmt = tree.body[0]
    assert stmt.target.name == "x"
    assert stmt.value.op == "+"
    assert stmt.value.left.value == 5
    assert stmt.value.right.op == "*"

# -------------------------------
# Block and Control Structure Tests
# -------------------------------

def test_if_block_structure():
    code = """
    if x > 5:
        y = 10
    else:
        y = 20
    """
    tree = parse_code(code)
    if_node = tree.body[0]
    assert isinstance(if_node, IfNode)
    assert isinstance(if_node.condition, BinaryOpNode)
    assert isinstance(if_node.then_block, BlockNode)
    assert isinstance(if_node.else_block, BlockNode)
    assert len(if_node.then_block.body) == 1

def test_for_loop_structure():
    code = """
    for i in range(0, 10):
        simulate(cell)
    """
    tree = parse_code(code)
    for_node = tree.body[0]
    assert isinstance(for_node, ForNode)
    assert for_node.iterator.name == "i"
    assert for_node.range.start.value == 0
    assert isinstance(for_node.body, BlockNode)
    assert isinstance(for_node.body.body[0], SimulateNode)

def test_nested_blocks():
    code = """
    if x > 0:
        for i in range(5):
            mutate(protein, position=2, to="L")
    """
    tree = parse_code(code)
    if_node = tree.body[0]
    assert isinstance(if_node, IfNode)
    for_node = if_node.then_block.body[0]
    assert isinstance(for_node, ForNode)
    assert isinstance(for_node.body.body[0], MutateNode)

# -------------------------------
# AST Structural Validations
# -------------------------------

def test_ast_node_positions():
    code = 'protein A = load("P12345")'
    tree = parse_code(code)
    stmt = tree.body[0]
    assert stmt.position.line == 1
    assert stmt.position.column == 1
    assert stmt.target.position.column == 9

# -------------------------------
# Error Handling and Recovery
# -------------------------------

def test_syntax_error_detection():
    with pytest.raises(ParseError) as exc_info:
        parse_code("protein = load(")
    assert "unexpected EOF" in str(exc_info.value)

def test_invalid_mutation_syntax():
    with pytest.raises(ParseError):
        parse_code('mutate(protein, "K", 10)')  # Invalid arg order

def test_error_recovery_multiple_statements():
    code = """
    protein A = load("P12345")
    simulate(
    protein B = load("P67890")
    """
    try:
        parse_code(code)
    except ParseError as e:
        assert e.line == 3
        assert "simulate" in e.message

# -------------------------------
# Edge Case and Recovery Tests
# -------------------------------

def test_empty_input_returns_empty_ast():
    tree = parse_code("")
    assert tree.body == []

def test_whitespace_and_comments_ignored():
    code = """
    # This is a comment
    protein A = load("XYZ")
    """
    tree = parse_code(code)
    assert len(tree.body) == 1
    assert isinstance(tree.body[0], AssignNode)

# -------------------------------
# Helper Mocks (if needed)
# -------------------------------

# Optional if not already defined:
class BinaryOpNode:
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right
