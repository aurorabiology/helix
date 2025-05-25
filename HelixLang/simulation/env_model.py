"""
env_model.py

HelixLang Environmental Model Module

Simulates chemical and spatial environments for cellular or molecular simulations.
Supports multi-dimensional spatial grids, chemical gradients with diffusion and decay,
spatial constraints including obstacles, and dynamic environment updates.

Use Cases:
- Tumor microenvironment modeling
- Biofilm growth simulation
- Organoid development studies

Author: HelixLang Team
Date: 2025-05-24
"""

import numpy as np
import logging

logger = logging.getLogger("helixlang.environment.env_model")


class EnvironmentModel:
    """
    Models chemical/spatial environment with diffusion, decay, and obstacles.
    """

    def __init__(self, dimensions=(50, 50, 50), space_dim=3, chemicals=None, diffusion_coeff=0.1,
                 decay_rate=0.01, obstacles=None, dt=0.01):
        """
        Initialize the environment model.

        Args:
            dimensions (tuple): Grid size in each spatial dimension.
            space_dim (int): Spatial dimension (2 or 3).
            chemicals (list[str]): Names of chemicals modeled.
            diffusion_coeff (float): Diffusion coefficient (assumed same for all chemicals).
            decay_rate (float): Chemical decay rate per timestep.
            obstacles (np.ndarray): Boolean grid marking obstacles (True = blocked).
            dt (float): Time step size.
        """
        assert space_dim in (2, 3), "space_dim must be 2 or 3"
        self.space_dim = space_dim
        self.dimensions = dimensions if len(dimensions) == space_dim else (dimensions * space_dim,)
        self.dt = dt

        self.chemicals = chemicals or ["nutrient"]
        self.num_chemicals = len(self.chemicals)

        # Initialize chemical concentration grids: shape = (num_chemicals, *dimensions)
        self.concentrations = np.zeros((self.num_chemicals, *self.dimensions), dtype=np.float32)

        self.diffusion_coeff = diffusion_coeff
        self.decay_rate = decay_rate

        # Obstacles mask: same spatial dimensions, True indicates blocked
        if obstacles is None:
            self.obstacles = np.zeros(self.dimensions, dtype=bool)
        else:
            assert obstacles.shape == self.dimensions
            self.obstacles = obstacles

        logger.info(f"EnvironmentModel initialized: space_dim={space_dim}, chemicals={self.chemicals}, grid_shape={self.dimensions}")

    def _laplacian(self, grid):
        """
        Compute discrete Laplacian of a grid using finite differences.

        Args:
            grid (np.ndarray): Concentration grid for one chemical.

        Returns:
            np.ndarray: Laplacian of grid.
        """
        if self.space_dim == 2:
            lap = (
                -4 * grid
                + np.roll(grid, 1, axis=0)
                + np.roll(grid, -1, axis=0)
                + np.roll(grid, 1, axis=1)
                + np.roll(grid, -1, axis=1)
            )
        else:  # 3D
            lap = (
                -6 * grid
                + np.roll(grid, 1, axis=0)
                + np.roll(grid, -1, axis=0)
                + np.roll(grid, 1, axis=1)
                + np.roll(grid, -1, axis=1)
                + np.roll(grid, 1, axis=2)
                + np.roll(grid, -1, axis=2)
            )
        # Zero Laplacian at obstacles: no diffusion inside obstacles
        lap[self.obstacles] = 0
        return lap

    def step_diffusion_decay(self):
        """
        Advance chemical concentrations by one timestep using diffusion + decay PDE.
        """
        for i in range(self.num_chemicals):
            conc = self.concentrations[i]

            lap = self._laplacian(conc)
            diffusion_term = self.diffusion_coeff * lap
            decay_term = -self.decay_rate * conc

            update = diffusion_term + decay_term
            update[self.obstacles] = 0  # no update inside obstacles

            self.concentrations[i] += update * self.dt

            # Clamp concentrations to non-negative
            np.clip(self.concentrations[i], 0, None, out=self.concentrations[i])

    def add_chemical_source(self, chem_name, location, amount):
        """
        Add a chemical source at a specific location.

        Args:
            chem_name (str): Chemical to add.
            location (tuple): Coordinates (int indices) in grid.
            amount (float): Amount of chemical to add.
        """
        try:
            idx = self.chemicals.index(chem_name)
        except ValueError:
            logger.warning(f"Chemical {chem_name} not found in environment")
            return

        # Add amount if location inside grid and not an obstacle
        if all(0 <= loc < dim for loc, dim in zip(location, self.dimensions)):
            if not self.obstacles[location]:
                self.concentrations[idx][location] += amount
                logger.debug(f"Added {amount} of {chem_name} at {location}")

    def set_obstacle(self, location, state=True):
        """
        Set or clear obstacle at a grid location.

        Args:
            location (tuple): Coordinates in grid.
            state (bool): True to set obstacle, False to clear.
        """
        if all(0 <= loc < dim for loc, dim in zip(location, self.dimensions)):
            self.obstacles[location] = state
            logger.info(f"Set obstacle at {location} to {state}")

    def query_local_environment(self, location, radius=1):
        """
        Query local environment state around a location.

        Args:
            location (tuple): Coordinates in grid.
            radius (int): Neighborhood radius to sample.

        Returns:
            dict: chemical concentrations averaged in neighborhood, obstacle presence.
        """
        slices = tuple(slice(max(0, loc - radius), min(dim, loc + radius + 1))
                       for loc, dim in zip(location, self.dimensions))

        neighborhood = {chem: self.concentrations[i][slices] for i, chem in enumerate(self.chemicals)}
        obstacle_neighborhood = self.obstacles[slices]

        averages = {chem: np.mean(neigh) for chem, neigh in neighborhood.items()}
        obstacle_present = np.any(obstacle_neighborhood)

        return {
            "chemical_averages": averages,
            "obstacle_present": obstacle_present
        }

    def update_dynamic_environment(self, updates):
        """
        Apply dynamic environment changes (e.g., moving obstacles, changing chemical sources).

        Args:
            updates (list[dict]): Each dict with keys:
                - 'type': 'obstacle' or 'chemical_source'
                - 'location': coordinate tuple
                - 'state' or 'amount': depending on type
                - 'chemical': required if type is 'chemical_source'
        """
        for update in updates:
            if update['type'] == 'obstacle':
                self.set_obstacle(update['location'], update.get('state', True))
            elif update['type'] == 'chemical_source':
                chem = update.get('chemical')
                amount = update.get('amount', 0)
                self.add_chemical_source(chem, update['location'], amount)

    def export_state(self):
        """
        Export current state for visualization or downstream use.

        Returns:
            dict: Contains chemical concentrations and obstacle grid.
        """
        return {
            "concentrations": self.concentrations.copy(),
            "obstacles": self.obstacles.copy()
        }


# -----------------------
# Example usage
# -----------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Initialize a 3D environment with one chemical nutrient
    env = EnvironmentModel(dimensions=(30, 30, 30), space_dim=3, chemicals=["nutrient"])

    # Add obstacle cube in center
    for x in range(12, 18):
        for y in range(12, 18):
            for z in range(12, 18):
                env.set_obstacle((x, y, z), True)

    # Add nutrient source at one corner
    env.add_chemical_source("nutrient", (0, 0, 0), 100)

    # Run diffusion-decay for 100 steps
    for _ in range(100):
        env.step_diffusion_decay()

    # Query environment near obstacle
    state = env.query_local_environment((15, 15, 15), radius=2)
    print(f"Local chemical averages near obstacle: {state['chemical_averages']}")
    print(f"Obstacle present? {state['obstacle_present']}")
