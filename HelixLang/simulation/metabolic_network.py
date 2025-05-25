import numpy as np
from scipy.integrate import solve_ivp
import json
import logging

logger = logging.getLogger("helixlang.simulation.metabolic_network")

class MetabolicNetwork:
    """
    HelixLang Metabolic Network Simulator

    Models metabolic pathways as directed graphs.
    Uses ODE solvers for continuous dynamics.
    Integrates HelixLang DSL for kinetic rate laws.
    """

    def __init__(self, metabolites=None, reactions=None):
        """
        Args:
            metabolites (list): List of metabolite names.
            reactions (list): List of reaction dicts with keys:
                - substrates: list of substrate metabolite names
                - products: list of product metabolite names
                - kinetics: DSL string or callable describing rate law
                - parameters: dict of kinetic parameters (Km, Vmax, etc.)
        """
        self.metabolites = metabolites or []
        self.met_index = {m: i for i, m in enumerate(self.metabolites)}

        self.reactions = reactions or []

        # Current metabolite concentrations (mM or appropriate unit)
        self.concentrations = np.zeros(len(self.metabolites))

        # Parsed kinetic functions for reactions
        self._rate_functions = []

        # Load reactions
        self._compile_kinetics()

    def _compile_kinetics(self):
        """
        Compile kinetic rate laws from DSL strings or callables to Python functions.

        For HelixLang: This can interface with HelixLang's DSL parser/compiler.
        Here we simulate with Python lambdas for example.
        """
        self._rate_functions.clear()
        for reaction in self.reactions:
            kinetics = reaction.get('kinetics')
            params = reaction.get('parameters', {})

            if callable(kinetics):
                # Already a Python callable
                rate_fn = kinetics
            elif isinstance(kinetics, str):
                # Simple DSL parsing placeholder (replace with real HelixLang DSL compiler)
                rate_fn = self._parse_helixlang_kinetics(kinetics, params)
            else:
                raise ValueError("Kinetics must be a callable or DSL string")

            self._rate_functions.append(rate_fn)

    def _parse_helixlang_kinetics(self, dsl_str, params):
        """
        Placeholder for HelixLang DSL kinetic parser.
        Converts DSL string to a Python function: rate(conc, params) -> float

        For now, support only Michaelis-Menten kinetics as example.

        Example DSL: "Vmax * S / (Km + S)"
        """
        Vmax = params.get('Vmax', 1.0)
        Km = params.get('Km', 0.5)

        def rate(conc, met_index=self.met_index):
            # Assume substrate is first substrate
            S_name = self.reactions[0]['substrates'][0]
            S_conc = conc[met_index[S_name]]
            return Vmax * S_conc / (Km + S_conc + 1e-8)  # Add epsilon for numerical stability

        return rate

    def set_concentration(self, metabolite, value):
        idx = self.met_index.get(metabolite)
        if idx is None:
            raise KeyError(f"Metabolite '{metabolite}' not found.")
        self.concentrations[idx] = value
        logger.debug(f"Set {metabolite} concentration to {value}")

    def get_concentration(self, metabolite):
        idx = self.met_index.get(metabolite)
        if idx is None:
            raise KeyError(f"Metabolite '{metabolite}' not found.")
        return self.concentrations[idx]

    def _ode_system(self, t, y):
        """
        Defines the ODE system describing metabolite concentration dynamics.

        Args:
            t (float): Current time (not used in rate laws here, but could be)
            y (np.array): Metabolite concentrations vector

        Returns:
            dydt (np.array): Time derivatives of concentrations
        """
        dydt = np.zeros_like(y)

        for reaction, rate_fn in zip(self.reactions, self._rate_functions):
            rate = rate_fn(y)
            # Subtract substrates
            for s in reaction['substrates']:
                dydt[self.met_index[s]] -= rate
            # Add products
            for p in reaction['products']:
                dydt[self.met_index[p]] += rate

        return dydt

    def simulate(self, t_span, t_eval=None, method='RK45'):
        """
        Run simulation over time span.

        Args:
            t_span (tuple): (start_time, end_time) in seconds
            t_eval (list or np.array): Time points at which to store the solution
            method (str): ODE solver method

        Returns:
            dict: Simulation results with time points and metabolite concentration arrays
        """
        logger.info(f"Starting metabolic simulation from t={t_span[0]} to {t_span[1]}")

        sol = solve_ivp(self._ode_system, t_span, self.concentrations, t_eval=t_eval, method=method)

        if not sol.success:
            logger.error(f"ODE solver failed: {sol.message}")

        results = {
            "time": sol.t.tolist(),
            "concentrations": {m: sol.y[i].tolist() for i, m in enumerate(self.metabolites)}
        }

        return results

    def export_json(self, filepath):
        """
        Export current metabolite concentrations and reaction info as JSON.

        Args:
            filepath (str): File path to save JSON.
        """
        data = {
            "metabolites": self.metabolites,
            "concentrations": self.concentrations.tolist(),
            "reactions": self.reactions
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Exported metabolic network state to {filepath}")

