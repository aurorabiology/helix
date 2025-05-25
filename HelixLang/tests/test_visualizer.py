import pytest
from unittest.mock import patch, MagicMock
from helixlang.runtime import Protein
from helixlang.visualize import (
    generate_chimerax_commands,
    export_gltf_for_blender,
    visualize_in_blender,
    generate_annotation_script,
    visualize_with_custom_engine,
    VisualizationError
)
import os

# ------------------------------
# ✅ CHIMERAX COMMAND GENERATION
# ------------------------------

def test_chimerax_command_generation_basic():
    p = Protein(sequence="MKTAYIAK")
    cmds = generate_chimerax_commands(p)
    
    assert isinstance(cmds, list)
    assert any("color" in cmd for cmd in cmds)
    assert any("open" in cmd for cmd in cmds)
    assert any("preset" in cmd for cmd in cmds)


def test_chimerax_command_contains_annotations():
    p = Protein(sequence="MKTAYIAK")
    cmds = generate_chimerax_commands(p, annotations=True)
    
    assert any("label" in cmd for cmd in cmds)
    assert any("select" in cmd for cmd in cmds)


# ------------------------------
# ✅ BLENDER / GLTF VISUALIZATION
# ------------------------------

def test_export_gltf_for_blender_creates_valid_structure(tmp_path):
    p = Protein(sequence="MKTAYIAK")
    output_file = tmp_path / "scene.gltf"
    
    export_gltf_for_blender(p, path=str(output_file))
    
    assert output_file.exists()
    assert output_file.read_text().startswith("{")  # JSON-like glTF


@patch("helixlang.visualize.subprocess.run")
def test_visualize_in_blender_calls_subprocess(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    p = Protein(sequence="MKTAYIAK")

    visualize_in_blender(p, mode="static", mock=True)
    
    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert "blender" in call_args[0] or "blender.exe" in call_args[0]
    assert "--background" in call_args


# ------------------------------
# ✅ CUSTOM ENGINE TEST
# ------------------------------

def test_custom_engine_visualization_success(tmp_path):
    p = Protein(sequence="MKTAYIAK")
    result = visualize_with_custom_engine(p, mode="headless", output_path=str(tmp_path))
    
    assert result.success
    assert "rendered_file" in result.metadata


def test_custom_engine_visualization_failure_handling():
    p = Protein(sequence="INVALID")

    with pytest.raises(VisualizationError):
        visualize_with_custom_engine(p, mode="invalid-mode")


# ------------------------------
# ✅ ANNOTATION & COLOR SCRIPTS
# ------------------------------

def test_generate_annotation_script_formatting():
    p = Protein(sequence="MKTAYIAK")
    script = generate_annotation_script(p, highlights={2: "red", 5: "blue"})
    
    assert "color" in script
    assert "2" in script
    assert "red" in script


def test_annotation_script_supports_labels():
    p = Protein(sequence="MKTAYIAK")
    script = generate_annotation_script(p, label_positions=[1, 3, 7])
    
    for i in [1, 3, 7]:
        assert f"label {i}" in script


# ------------------------------
# ✅ HEADLESS MOCKING & ERROR HANDLING
# ------------------------------

@patch("helixlang.visualize.subprocess.run")
def test_headless_mode_with_mock_blender(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    p = Protein(sequence="MKTAYIAK")

    visualize_in_blender(p, mode="animated", mock=True)
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert "--background" in args
    assert ".blend" in " ".join(args) or ".py" in " ".join(args)


@patch("helixlang.visualize.subprocess.run", side_effect=OSError("Blender not found"))
def test_blender_not_installed_handling(mock_run):
    p = Protein(sequence="MKTAYIAK")
    
    with pytest.raises(VisualizationError):
        visualize_in_blender(p, mode="static")


# ------------------------------
# ✅ EXPORT VISUAL FILE CHECK
# ------------------------------

def test_blender_export_writes_file(tmp_path):
    p = Protein(sequence="MKTAYIAK")
    export_path = tmp_path / "model.gltf"

    export_gltf_for_blender(p, path=str(export_path))
    
    assert export_path.exists()
    assert export_path.stat().st_size > 10


# ------------------------------
# ✅ CROSS-BACKEND CONSISTENCY
# ------------------------------

def test_consistent_color_logic_across_backends():
    p = Protein(sequence="MKTAYIAK")
    chimerax_cmds = generate_chimerax_commands(p, annotations=True)
    annotation_script = generate_annotation_script(p, highlights={2: "red"})
    
    chimerax_color = [cmd for cmd in chimerax_cmds if "color" in cmd]
    assert any("red" in c for c in chimerax_color)
    assert "red" in annotation_script


# ------------------------------
# ✅ UNSUPPORTED STRUCTURE EDGE CASE
# ------------------------------

def test_visualize_with_empty_protein_should_fail():
    empty_protein = Protein(sequence="")

    with pytest.raises(VisualizationError):
        generate_chimerax_commands(empty_protein)
