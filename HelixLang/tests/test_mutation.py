import pytest
from helixlang.runtime import Protein, mutate, MutationError


# ---------------------------
# ✅ POINT MUTATION TESTS
# ---------------------------

def test_point_mutation_success():
    p = Protein(sequence="MKTAYIAKQRQISFVK")
    mutate(p, position=4, to="L")
    assert p.sequence[3] == "L"  # 0-indexed


def test_point_mutation_boundary_first():
    p = Protein(sequence="MKTAYIAKQRQISFVK")
    mutate(p, position=1, to="G")
    assert p.sequence[0] == "G"


def test_point_mutation_boundary_last():
    p = Protein(sequence="MKTAYIAKQRQISFVK")
    mutate(p, position=len(p.sequence), to="G")
    assert p.sequence[-1] == "G"


# ---------------------------
# ✅ INSERTION MUTATION TESTS
# ---------------------------

def test_insertion_mutation_middle():
    p = Protein(sequence="MKTA")
    mutate(p, position=3, insert="G")
    assert p.sequence == "MKTGA"

def test_insertion_mutation_start():
    p = Protein(sequence="MKTA")
    mutate(p, position=1, insert="L")
    assert p.sequence == "LMKTA"

def test_insertion_mutation_end():
    p = Protein(sequence="MKTA")
    mutate(p, position=5, insert="Y")
    assert p.sequence == "MKTAY"


# ---------------------------
# ✅ DELETION MUTATION TESTS
# ---------------------------

def test_deletion_mutation():
    p = Protein(sequence="MKTA")
    mutate(p, position=2, delete=True)
    assert p.sequence == "MTA"

def test_deletion_first():
    p = Protein(sequence="MKTA")
    mutate(p, position=1, delete=True)
    assert p.sequence == "KTA"

def test_deletion_last():
    p = Protein(sequence="MKTA")
    mutate(p, position=4, delete=True)
    assert p.sequence == "MKT"


# ---------------------------
# ✅ INVALID MUTATION CASES
# ---------------------------

def test_invalid_position_raises():
    p = Protein(sequence="MKTA")
    with pytest.raises(MutationError):
        mutate(p, position=0, to="L")

def test_out_of_bounds_position():
    p = Protein(sequence="MKTA")
    with pytest.raises(MutationError):
        mutate(p, position=10, to="L")

def test_invalid_amino_acid_replacement():
    p = Protein(sequence="MKTA")
    with pytest.raises(MutationError):
        mutate(p, position=2, to="Z")  # 'Z' is not valid


# ---------------------------
# ✅ CHAINED MUTATION CASES
# ---------------------------

def test_multiple_mutations_chain():
    p = Protein(sequence="MKTAYIAKQR")
    mutate(p, position=2, to="V")
    mutate(p, position=3, insert="G")
    mutate(p, position=5, delete=True)
    assert len(p.sequence) == 9
    assert p.sequence[1] == "V"
    assert p.sequence[2] == "G"


# ---------------------------
# ✅ BIOLOGICAL RULES
# ---------------------------

def test_mutation_preserves_sequence_length_point():
    p = Protein(sequence="MKTA")
    old_len = len(p.sequence)
    mutate(p, position=2, to="L")
    assert len(p.sequence) == old_len

def test_mutation_changes_sequence_content():
    p = Protein(sequence="MKTA")
    old_seq = p.sequence
    mutate(p, position=3, to="P")
    assert p.sequence != old_seq


# ---------------------------
# ✅ EDGE CASES
# ---------------------------

def test_mutation_on_empty_sequence():
    p = Protein(sequence="")
    with pytest.raises(MutationError):
        mutate(p, position=1, to="L")

def test_insertion_on_empty_sequence_start():
    p = Protein(sequence="")
    mutate(p, position=1, insert="M")
    assert p.sequence == "M"
