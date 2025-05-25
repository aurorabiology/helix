import pytest
from helixlang.interpreter import run_code, get_var, reset_context
from helixlang.runtime_objects import Protein, Cell, SimulationResult, MutationError
from helixlang.errors import RuntimeError, TypeError, UnboundVariableError

# Reset interpreter context before each test
@pytest.fixture(autouse=True)
def reset():
    reset_context()


# ---------------------
# ✅ VARIABLE & ARITHMETIC
# ---------------------

def test_variable_assignment_and_lookup():
    run_code("x = 10; y = x + 5")
    assert get_var("x") == 10
    assert get_var("y") == 15

def test_chained_operations():
    run_code("a = 2 + 3 * 4 - 1")
    assert get_var("a") == 13


# ---------------------
# ✅ CONTROL FLOW
# ---------------------

def test_if_else_execution_true_branch():
    run_code("""
    x = 5
    if x > 2:
        y = 10
    else:
        y = 20
    """)
    assert get_var("y") == 10

def test_if_else_execution_false_branch():
    run_code("""
    x = 1
    if x > 2:
        y = 10
    else:
        y = 20
    """)
    assert get_var("y") == 20

def test_for_loop_sum():
    run_code("""
    total = 0
    for i in range(1, 5):
        total = total + i
    """)
    assert get_var("total") == 10


# ---------------------
# ✅ BUILT-IN FUNCTIONS
# ---------------------

def test_simulate_builtin():
    run_code("""
    cell = Cell()
    result = simulate(cell)
    """)
    result = get_var("result")
    assert isinstance(result, SimulationResult)
    assert result.success is True

def test_mutate_builtin():
    run_code("""
    protein = Protein("MYSEQ")
    mutated = mutate(protein, position=2, to="L")
    """)
    mutated = get_var("mutated")
    assert isinstance(mutated, Protein)
    assert mutated.sequence[2] == "L"

def test_export_builtin():
    run_code("""
    protein = Protein("ACGT")
    export(protein, path="test_output.pdb", format="pdb")
    """)
    # No assertion needed unless mocking file output


# ---------------------
# ✅ SCOPING & NAMESPACES
# ---------------------

def test_variable_shadowing():
    run_code("""
    x = 10
    if True:
        x = 5
    """)
    assert get_var("x") == 5

def test_loop_variable_scope():
    run_code("""
    for i in range(3):
        temp = i
    """)
    assert get_var("temp") == 2


# ---------------------
# ✅ OBJECT RUNTIME INTEGRITY
# ---------------------

def test_protein_runtime_object():
    run_code('p = Protein("ACGT")')
    p = get_var("p")
    assert isinstance(p, Protein)
    assert p.sequence == "ACGT"

def test_cell_mutation():
    run_code("""
    cell = Cell()
    cell.mutate_gene("gene1", "TGC")
    """)
    cell = get_var("cell")
    assert isinstance(cell, Cell)
    assert cell.genes["gene1"] == "TGC"


# ---------------------
# ❌ RUNTIME ERROR HANDLING
# ---------------------

def test_unbound_variable():
    with pytest.raises(UnboundVariableError):
        run_code("x = y + 1")

def test_division_by_zero():
    with pytest.raises(RuntimeError):
        run_code("x = 10 / 0")

def test_type_error():
    with pytest.raises(TypeError):
        run_code('x = "hello" + 5')

def test_invalid_mutation_call():
    with pytest.raises(MutationError):
        run_code("""
        protein = Protein("ABC")
        mutate(protein, position=1000, to="Z")
        """)


# ---------------------
# ✅ EDGE CASES
# ---------------------

def test_empty_program():
    run_code("")

def test_comments_and_whitespace():
    run_code("""
    # Comment above
    x = 1  # Inline comment
    """)
    assert get_var("x") == 1
