"""
helixlang.simulation
--------------------

Core simulation components of HelixLang, supporting multi-scale biological
processes such as metabolic networks, gene regulation, protein folding,
molecular dynamics, and environment modeling.

This package initializes shared configuration, random seeds, and registers
simulation submodules for extensibility. Provides centralized access to
key simulation classes and utilities.

Example usage:

    from helixlang.simulation import Scheduler, MetabolicNetwork

    scheduler = Scheduler()
    metabolism = MetabolicNetwork()

"""

import os
import sys
import importlib
import logging
import random
import yaml  # For configuration loading

# === Core simulation constants ===
SIMULATION_TIME_UNIT = 1e-3  # seconds, base time unit for scheduler ticks
MAX_STEP_SIZE = 0.01  # max timestep in seconds for numerical integrators
FLOAT_PRECISION = 1e-6  # numerical tolerance for calculations

# === Shared global state ===
GLOBAL_RANDOM_SEED = 42  # default deterministic seed
random.seed(GLOBAL_RANDOM_SEED)

# Setup logger for simulation package
logger = logging.getLogger('helixlang.simulation')
logger.setLevel(logging.INFO)  # default log level

ch = logging.StreamHandler()
formatter = logging.Formatter('[%(levelname)s] %(name)s: %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

# === Load simulation-wide configuration from YAML file ===
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.yaml')
_simulation_config = {}

try:
    with open(CONFIG_FILE, 'r') as f:
        _simulation_config = yaml.safe_load(f)
    # Apply settings from config
    if 'random_seed' in _simulation_config:
        GLOBAL_RANDOM_SEED = _simulation_config['random_seed']
        random.seed(GLOBAL_RANDOM_SEED)
    if 'logging_level' in _simulation_config:
        level_name = _simulation_config['logging_level'].upper()
        logger.setLevel(getattr(logging, level_name, logging.INFO))
    if 'max_step_size' in _simulation_config:
        global MAX_STEP_SIZE
        MAX_STEP_SIZE = float(_simulation_config['max_step_size'])
    logger.info("Simulation configuration loaded from config.yaml")
except FileNotFoundError:
    logger.warning("No simulation config file found; using default settings")

# === Dynamically import all simulation submodules ===
_package_dir = os.path.dirname(__file__)
_submodules = []

for fname in os.listdir(_package_dir):
    if fname.endswith('.py') and not fname.startswith('_') and fname != '__init__.py':
        mod_name = fname[:-3]
        try:
            imported_module = importlib.import_module(f'{__name__}.{mod_name}')
            _submodules.append(imported_module)
            logger.debug(f"Registered simulation submodule: {mod_name}")
        except Exception as e:
            logger.error(f"Failed to import submodule {mod_name}: {e}")

# === Explicit imports for core classes/functions ===
from .scheduler import Scheduler
from .metabolic_network import MetabolicNetwork
from .genetic_regulation import GeneticRegulation
from .protein_folding import ProteinFolding
from .molecular_dynamics import MolecularDynamics
from .env_model import EnvModel
from .mutation_engine import MutationEngine
from .pathway_mapper import PathwayMapper
from .visualization_engine import VisualizationEngine

__all__ = [
    "Scheduler",
    "MetabolicNetwork",
    "GeneticRegulation",
    "ProteinFolding",
    "MolecularDynamics",
    "EnvModel",
    "MutationEngine",
    "PathwayMapper",
    "VisualizationEngine",
]

# === Expose shared constants, config, and logger ===
__simulation_constants__ = {
    "SIMULATION_TIME_UNIT": SIMULATION_TIME_UNIT,
    "MAX_STEP_SIZE": MAX_STEP_SIZE,
    "FLOAT_PRECISION": FLOAT_PRECISION,
    "GLOBAL_RANDOM_SEED": GLOBAL_RANDOM_SEED,
}

__logger__ = logger
__config__ = _simulation_config
