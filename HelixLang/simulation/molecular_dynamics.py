"""
molecular_dynamics.py

HelixLang Molecular Dynamics (MD) Simulation Module

Simulates physical motion, collisions, and interactions of molecules using classical mechanics
and potential energy models. Supports integration with protein folding and metabolic modules.

Features:
- Models intermolecular forces via Lennard-Jones potentials and Brownian motion.
- Implements numerical integration via Velocity-Verlet scheme.
- Supports configurable boundary conditions: periodic or reflective.
- Provides interfaces for coupling with other HelixLang modules (protein folding, metabolic network).
- Supports multi-threading or GPU acceleration hooks for scalability.
- Outputs time-series of molecule positions, velocities, and energies.

Author: HelixLang Team
Date: 2025-05-24
"""

import numpy as np
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger("helixlang.simulation.molecular_dynamics")

class MolecularDynamicsSimulator:
    """
    Core molecular dynamics simulator.
    """

    def __init__(self, molecules, box_size, time_step=1e-3, temperature=300.0,
                 boundary_condition='periodic', use_gpu=False, max_threads=4):
        """
        Initialize MD simulation.

        Args:
            molecules (list[dict]): List of molecules, each with keys:
                - 'position': np.ndarray(3,)
                - 'velocity': np.ndarray(3,)
                - 'mass': float
                - 'radius': float (for collision)
                - 'id': unique identifier
            box_size (float or np.ndarray): Size of cubic simulation box.
            time_step (float): Time step for integration (ps or arbitrary units).
            temperature (float): Temperature in Kelvin for Brownian motion.
            boundary_condition (str): 'periodic' or 'reflective'.
            use_gpu (bool): Flag to enable GPU acceleration (placeholder).
            max_threads (int): Maximum threads for parallel force computation.
        """
        self.molecules = molecules
        self.N = len(molecules)
        self.box_size = np.array([box_size]*3) if isinstance(box_size, (int, float)) else np.array(box_size)
        self.dt = time_step
        self.temperature = temperature
        self.boundary_condition = boundary_condition.lower()
        self.use_gpu = use_gpu
        self.max_threads = max_threads

        # Precompute constants for Brownian motion (simplified)
        self.kb = 1.380649e-23  # Boltzmann constant in J/K
        self.brownian_scale = np.sqrt(2 * self.kb * self.temperature * self.dt)

        # Initialize forces array (3D vector per molecule)
        self.forces = np.zeros((self.N, 3))

        logger.info(f"Initialized MD with {self.N} molecules, box size {self.box_size}, dt={self.dt}")

    def _apply_boundary_conditions(self, positions, velocities):
        """
        Apply configured boundary conditions to positions and velocities.

        Args:
            positions (np.ndarray): Nx3 array of molecule positions.
            velocities (np.ndarray): Nx3 array of molecule velocities.

        Returns:
            tuple: corrected positions and velocities.
        """
        if self.boundary_condition == 'periodic':
            # Wrap positions within box
            positions = np.mod(positions, self.box_size)
        elif self.boundary_condition == 'reflective':
            for i in range(3):
                mask_low = positions[:, i] < 0
                mask_high = positions[:, i] > self.box_size[i]
                # Reflect positions
                positions[mask_low, i] = -positions[mask_low, i]
                positions[mask_high, i] = 2*self.box_size[i] - positions[mask_high, i]
                # Reverse velocities upon reflection
                velocities[mask_low | mask_high, i] *= -1
        else:
            raise ValueError(f"Unsupported boundary condition: {self.boundary_condition}")

        return positions, velocities

    def _compute_forces_lj(self, positions):
        """
        Compute Lennard-Jones forces between molecules.

        Args:
            positions (np.ndarray): Nx3 array of positions.

        Returns:
            np.ndarray: Nx3 array of forces.
        """
        forces = np.zeros_like(positions)
        epsilon = 1.0  # Depth of potential well (arbitrary units)
        sigma = 1.0    # Finite distance at which potential is zero

        def lj_force(r_vec):
            r = np.linalg.norm(r_vec)
            if r == 0:
                return np.zeros(3)
            # Lennard-Jones force magnitude
            f_mag = 24 * epsilon * (2 * (sigma/r)**12 - (sigma/r)**6) / r**2
            return f_mag * r_vec

        # Use simple O(N^2) loop for pairwise forces (can optimize with spatial partitioning)
        for i in range(self.N):
            for j in range(i + 1, self.N):
                r_vec = positions[j] - positions[i]
                # Apply minimum image convention for periodic BCs
                if self.boundary_condition == 'periodic':
                    for k in range(3):
                        if r_vec[k] > 0.5 * self.box_size[k]:
                            r_vec[k] -= self.box_size[k]
                        elif r_vec[k] < -0.5 * self.box_size[k]:
                            r_vec[k] += self.box_size[k]
                f = lj_force(r_vec)
                forces[i] += f
                forces[j] -= f

        return forces

    def _integrate_velocity_verlet(self, positions, velocities, forces, masses):
        """
        Integrate one time step using Velocity-Verlet algorithm.

        Args:
            positions (np.ndarray): Nx3 array of positions.
            velocities (np.ndarray): Nx3 array of velocities.
            forces (np.ndarray): Nx3 array of forces.
            masses (np.ndarray): N-array of masses.

        Returns:
            tuple: new positions, velocities, forces.
        """
        dt = self.dt
        new_positions = positions + velocities * dt + 0.5 * (forces / masses[:, None]) * dt**2

        # Compute forces at new positions
        new_forces = self._compute_forces_lj(new_positions)

        new_velocities = velocities + 0.5 * (forces + new_forces) / masses[:, None] * dt

        return new_positions, new_velocities, new_forces

    def _apply_brownian_motion(self, velocities, masses):
        """
        Add Brownian motion perturbation to velocities.

        Args:
            velocities (np.ndarray): Nx3 array.
            masses (np.ndarray): N-array of masses.

        Returns:
            np.ndarray: Updated velocities.
        """
        noise = np.random.normal(0, self.brownian_scale, size=velocities.shape)
        noise /= np.sqrt(masses)[:, None]  # Scale noise inversely by sqrt(mass)
        return velocities + noise

    def step(self):
        """
        Perform a single simulation time step.

        Updates positions, velocities, and forces.
        """
        positions = np.array([mol['position'] for mol in self.molecules])
        velocities = np.array([mol['velocity'] for mol in self.molecules])
        masses = np.array([mol['mass'] for mol in self.molecules])

        # Integrate positions and velocities
        positions, velocities, forces = self._integrate_velocity_verlet(positions, velocities, self.forces, masses)

        # Apply boundary conditions
        positions, velocities = self._apply_boundary_conditions(positions, velocities)

        # Add Brownian motion noise to velocities
        velocities = self._apply_brownian_motion(velocities, masses)

        # Update molecule states
        for i, mol in enumerate(self.molecules):
            mol['position'] = positions[i]
            mol['velocity'] = velocities[i]

        self.forces = forces

    def run(self, steps=1000, output_interval=100):
        """
        Run the MD simulation for a number of steps.

        Args:
            steps (int): Number of integration steps.
            output_interval (int): Interval for logging/output.

        Returns:
            list: Time-series trajectory of molecule positions (list of np.ndarray).
        """
        trajectory = []
        logger.info(f"Starting MD run for {steps} steps")

        for step in range(steps):
            self.step()
            if step % output_interval == 0 or step == steps - 1:
                positions = np.array([mol['position'] for mol in self.molecules])
                trajectory.append(positions.copy())
                logger.info(f"Step {step}: Recorded positions")

        return trajectory

    # Placeholder for GPU acceleration
    def enable_gpu_acceleration(self):
        """
        Placeholder to enable GPU acceleration for force computation and integration.
        """
        if not self.use_gpu:
            logger.warning("GPU acceleration requested but not enabled in constructor")
            return
        logger.info("GPU acceleration enabled (placeholder)")

    # Integration hooks for coupling
    def couple_with_protein_folding(self, folding_module):
        """
        Example coupling method to interact with protein folding module.

        Args:
            folding_module (object): Instance of ProteinFoldingSimulator or similar.
        """
        logger.info("Coupling molecular dynamics with protein folding module")
        # Implement interaction logic here, e.g., update forces based on folding states

    def couple_with_metabolic_network(self, metabolic_module):
        """
        Example coupling method to interact with metabolic network module.

        Args:
            metabolic_module (object): Metabolic network simulator instance.
        """
        logger.info("Coupling molecular dynamics with metabolic network module")
        # Implement interaction logic here

# -----------------------
# Example usage
# -----------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Create simple molecules (e.g., 5 particles)
    molecules = []
    for i in range(5):
        molecules.append({
            'position': np.random.rand(3) * 10,
            'velocity': np.zeros(3),
            'mass': 1.0,
            'radius': 0.5,
            'id': i
        })

    md_sim = MolecularDynamicsSimulator(molecules, box_size=10.0, time_step=0.01)
    traj = md_sim.run(steps=500, output_interval=50)
