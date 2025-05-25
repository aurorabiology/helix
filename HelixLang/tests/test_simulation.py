import pytest
from helixlang.simulation import simulate, SimulationError
from helixlang.runtime import load_protein, mutate, Protein
from helixlang.export import export_trajectory

# ------------------------------
# ✅ BASIC SIMULATION TESTS
# ------------------------------

def test_simple_dynamics_run():
    p = load_protein("P12345")
    result = simulate(p, duration=100)
    assert result.total_energy < 1000
    assert result.duration == 100
    assert len(result.frames) > 1


def test_simulation_with_custom_resolution():
    p = load_protein("P12345")
    result = simulate(p, duration=50, timestep=0.5)
    assert result.num_steps == 100  # 50 / 0.5
    assert isinstance(result.frames[0].position, list)


# ------------------------------
# ✅ STRUCTURE DYNAMICS TESTS
# ------------------------------

def test_structure_changes_over_time():
    p = load_protein("P12345")
    result = simulate(p, duration=200)
    first_pos = result.frames[0].position
    last_pos = result.frames[-1].position
    assert first_pos != last_pos


def test_conformational_change():
    p = load_protein("P12345")
    result = simulate(p, duration=100)
    assert result.frames[0].structure != result.frames[-1].structure


# ------------------------------
# ✅ MUTATION EFFECTS TESTS
# ------------------------------

def test_mutation_alters_simulation_outcome():
    original = load_protein("P12345")
    mutated = load_protein("P12345")
    mutate(mutated, position=10, to="G")

    result_orig = simulate(original, duration=100)
    result_mut = simulate(mutated, duration=100)

    assert result_orig.total_energy != result_mut.total_energy
    assert result_orig.frames[-1].structure != result_mut.frames[-1].structure


# ------------------------------
# ✅ BIOLOGICAL EDGE CASES
# ------------------------------

def test_collision_handling():
    p = load_protein("P12345")
    result = simulate(p, duration=100, enable_collision_detection=True)
    assert result.collision_events >= 0


def test_simulation_failure_due_to_invalid_structure():
    broken_protein = Protein(sequence="INVALIDSEQ")
    with pytest.raises(SimulationError):
        simulate(broken_protein, duration=100)


def test_simulation_zero_duration():
    p = load_protein("P12345")
    result = simulate(p, duration=0)
    assert result.num_steps == 0
    assert result.total_energy == 0


# ------------------------------
# ✅ EXPORT TRAJECTORY
# ------------------------------

def test_export_trajectory_to_file(tmp_path):
    p = load_protein("P12345")
    result = simulate(p, duration=50)
    file_path = tmp_path / "traj.json"
    export_trajectory(result, file_path=str(file_path))
    with open(file_path) as f:
        data = f.read()
    assert "frames" in data
    assert "energy" in data


# ------------------------------
# ✅ LONG SIMULATION STABILITY
# ------------------------------

def test_long_simulation_stability():
    p = load_protein("P12345")
    result = simulate(p, duration=1000, timestep=1)
    assert result.num_steps == 1000
    assert all(isinstance(frame.energy, (int, float)) for frame in result.frames)


# ------------------------------
# ✅ PERFORMANCE BOUNDS
# ------------------------------

def test_simulation_energy_stays_bounded():
    p = load_protein("P12345")
    result = simulate(p, duration=200)
    for frame in result.frames:
        assert frame.energy < 5000  # Arbitrary physical upper bound


# ------------------------------
# ✅ SIMULATION PARITY
# ------------------------------

def test_simulation_repeatability_with_seed():
    p1 = load_protein("P12345")
    p2 = load_protein("P12345")
    r1 = simulate(p1, duration=100, seed=42)
    r2 = simulate(p2, duration=100, seed=42)
    assert r1.frames == r2.frames


def test_simulation_variability_without_seed():
    p1 = load_protein("P12345")
    p2 = load_protein("P12345")
    r1 = simulate(p1, duration=100)
    r2 = simulate(p2, duration=100)
    assert r1.frames != r2.frames
