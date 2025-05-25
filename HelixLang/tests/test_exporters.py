import os
import json
import csv
import pytest
from pathlib import Path
from helixlang.export import export, ExportError
from helixlang.runtime import Protein, Genome

# ------------------------------
# ✅ PROTEIN EXPORT TESTS
# ------------------------------

def test_export_protein_as_json(tmp_path):
    protein = Protein(sequence="MKTAYIAK")
    output = tmp_path / "protein.json"
    export(protein, format="json", path=str(output))
    
    assert output.exists()
    with open(output) as f:
        data = json.load(f)
        assert "sequence" in data
        assert data["sequence"] == "MKTAYIAK"


def test_export_protein_as_gltf(tmp_path):
    protein = Protein(sequence="MKTAYIAK")
    output = tmp_path / "protein.gltf"
    export(protein, format="gltf", path=str(output))
    
    assert output.exists()
    with open(output) as f:
        content = f.read()
        assert "asset" in content or "meshes" in content  # glTF schema keys


def test_export_protein_as_pdb(tmp_path):
    protein = Protein(sequence="MKTAYIAK")
    output = tmp_path / "protein.pdb"
    export(protein, format="pdb", path=str(output))

    assert output.exists()
    with open(output) as f:
        lines = f.readlines()
        assert any(line.startswith("ATOM") for line in lines)


# ------------------------------
# ✅ GENOME EXPORT TESTS
# ------------------------------

def test_export_genome_as_csv(tmp_path):
    genome = Genome(sequence="ACGTACGT")
    output = tmp_path / "genome.csv"
    export(genome, format="csv", path=str(output))

    assert output.exists()
    with open(output) as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert any("A" in row for row in rows)


def test_export_genome_as_fasta(tmp_path):
    genome = Genome(sequence="ACGTACGT")
    output = tmp_path / "genome.fasta"
    export(genome, format="fasta", path=str(output))

    assert output.exists()
    with open(output) as f:
        contents = f.read()
        assert contents.startswith(">HelixLangGenome")
        assert "ACGTACGT" in contents


# ------------------------------
# ✅ FILE INTEGRITY CHECKS
# ------------------------------

def test_export_file_created_and_non_empty(tmp_path):
    protein = Protein(sequence="MKT")
    file_path = tmp_path / "protein.obj"
    export(protein, format="obj", path=str(file_path))

    assert file_path.exists()
    assert file_path.stat().st_size > 0


def test_export_directory_created_if_not_exists(tmp_path):
    nested_dir = tmp_path / "nested" / "exports"
    output_path = nested_dir / "protein.json"
    protein = Protein(sequence="MKT")
    
    export(protein, format="json", path=str(output_path))
    
    assert output_path.exists()
    assert output_path.parent.exists()


# ------------------------------
# ✅ API AND FORMAT SURFACE
# ------------------------------

def test_export_api_signature_json(tmp_path):
    protein = Protein(sequence="MKT")
    output = tmp_path / "p.json"
    result = export(protein, format="json", path=str(output))
    assert result is None  # Expected: no return value, just file effect


def test_export_raises_on_unsupported_format(tmp_path):
    protein = Protein(sequence="MKT")
    with pytest.raises(ExportError):
        export(protein, format="xyz", path=str(tmp_path / "bad.xyz"))


def test_export_fails_on_invalid_model(tmp_path):
    class FakeObject:
        pass
    
    fake = FakeObject()
    with pytest.raises(ExportError):
        export(fake, format="json", path=str(tmp_path / "bad.json"))


# ------------------------------
# ✅ ROUNDTRIP EXPORT/IMPORT (If Supported)
# ------------------------------

def test_export_and_readback_json_roundtrip(tmp_path):
    protein = Protein(sequence="MKTAYIAK")
    output = tmp_path / "out.json"
    export(protein, format="json", path=str(output))

    with open(output) as f:
        data = json.load(f)

    assert data["sequence"] == "MKTAYIAK"
    assert "metadata" in data or "structure" in data


# ------------------------------
# ✅ MULTIPLE EXPORTS AND OVERWRITE
# ------------------------------

def test_multiple_exports_with_overwrite(tmp_path):
    protein = Protein(sequence="MKTA")
    output = tmp_path / "prot.pdb"

    export(protein, format="pdb", path=str(output))
    original_size = output.stat().st_size

    # Export again
    export(protein, format="pdb", path=str(output))
    new_size = output.stat().st_size

    assert new_size == original_size


# ------------------------------
# ✅ EXTENSION VALIDATION (Optional)
# ------------------------------

def test_export_enforces_correct_extension(tmp_path):
    protein = Protein(sequence="MKTA")
    wrong_ext_path = tmp_path / "protein.txt"
    with pytest.raises(ExportError):
        export(protein, format="json", path=str(wrong_ext_path))
