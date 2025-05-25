"""
genetic_regulation.py

HelixLang Gene Regulatory Network (GRN) Simulation Module

Simulates gene regulatory networks using rule-based and logic-based models defined
in HelixLang’s domain-specific scripting language (DSL). Tracks gene expression levels,
transcription factor binding states, and epigenetic modifications, updating dynamically
at each simulation step with optional stochastic noise.

Integration:
- Outputs gene expression levels influencing metabolic enzyme concentrations.
- Modulates protein folding via chaperone expression.
- Affects mutation repair pathways through DNA repair gene regulation.

Example Use Case:
Model toggle switch synthetic circuits or complex gene expression programs.

Author: HelixLang Team
Date: 2025-05-24
"""

import random
import logging

logger = logging.getLogger("helixlang.simulation.genetic_regulation")

class GeneRegulationNetwork:
    """
    Represents a Gene Regulatory Network (GRN) for HelixLang simulations.

    Core Responsibilities:
    - Encode gene regulatory logic (activation, repression, feedback loops) through
      user-defined rules compatible with HelixLang DSL.
    - Track gene expression levels, transcription factor binding states, and epigenetic markers.
    - Update gene expression dynamically at each simulation tick based on current state and context.
    - Optionally simulate stochastic gene expression noise and cell-to-cell variability.
    - Provide interfaces for integration with metabolic, protein folding, and mutation engines.
    """

    def __init__(self, genes, regulatory_rules, initial_expression=None, stochastic=True):
        """
        Initialize the GRN simulation model.

        Args:
            genes (list[str]): List of gene identifiers in the network.
            regulatory_rules (dict[str, callable]): Mapping from gene to a function implementing
                the regulatory logic. Each function receives current gene expressions and
                environmental context and returns new expression level (0.0 - 1.0).
            initial_expression (dict[str, float], optional): Starting expression levels for genes.
                Defaults to 0.0 expression for all genes.
            stochastic (bool): Enable stochastic simulation of gene expression noise.
        """
        self.genes = genes
        self.regulatory_rules = regulatory_rules
        self.stochastic = stochastic

        # Initialize gene expression levels, default 0.0 (no expression)
        if initial_expression:
            self.expression = {g: initial_expression.get(g, 0.0) for g in genes}
        else:
            self.expression = {g: 0.0 for g in genes}

        # Initialize transcription factor binding states and epigenetic marks (empty by default)
        self.tf_binding_states = {g: False for g in genes}  # placeholder: True if TF bound
        self.epigenetic_modifications = {g: {} for g in genes}  # e.g., methylation levels

        logger.info(f"Initialized GRN with genes: {genes}")

    def step(self, context=None):
        """
        Advance the simulation by one scheduler tick.

        Evaluates regulatory logic for each gene, updates expression levels, and
        incorporates stochastic noise if enabled.

        Args:
            context (dict, optional): External signals, metabolite concentrations,
                or mutation states influencing regulation.

        Returns:
            dict[str, float]: Updated gene expression levels after this step.
        """
        context = context or {}
        new_expression = {}

        for gene in self.genes:
            rule_fn = self.regulatory_rules.get(gene)

            if not rule_fn:
                # No regulatory rule provided; maintain current expression
                new_expression[gene] = self.expression[gene]
                continue

            # Compute raw expression level using regulatory logic
            try:
                expr_level = rule_fn(self.expression, self.tf_binding_states, self.epigenetic_modifications, context)
            except Exception as e:
                logger.error(f"Error evaluating regulatory rule for gene '{gene}': {e}")
                expr_level = self.expression[gene]

            # Apply stochastic noise if enabled
            if self.stochastic:
                expr_level = self._apply_stochastic_noise(expr_level)

            # Clamp expression to valid range [0.0, 1.0]
            new_expression[gene] = max(0.0, min(1.0, expr_level))

        self.expression = new_expression
        logger.debug(f"Updated gene expression: {self.expression}")
        return self.expression

    def _apply_stochastic_noise(self, expr_level):
        """
        Simulate biological noise in gene expression by adding Gaussian noise.

        Args:
            expr_level (float): Raw gene expression value (0.0 to 1.0).

        Returns:
            float: Expression level with noise applied.
        """
        noise_std_dev = 0.05  # Adjustable noise intensity
        noisy_value = expr_level + random.gauss(0, noise_std_dev)
        return noisy_value

    def set_expression(self, gene, value):
        """
        Set expression level of a specific gene directly.

        Args:
            gene (str): Target gene.
            value (float): New expression level (0.0 - 1.0).
        """
        if gene not in self.genes:
            raise KeyError(f"Gene '{gene}' not found in GRN.")
        self.expression[gene] = max(0.0, min(1.0, value))
        logger.info(f"Gene '{gene}' expression set to {self.expression[gene]}")

    def get_expression(self, gene):
        """
        Get the current expression level of a specific gene.

        Args:
            gene (str): Target gene.

        Returns:
            float: Current expression level.
        """
        return self.expression.get(gene)

    def update_tf_binding(self, gene, bound):
        """
        Update transcription factor binding state for a gene.

        Args:
            gene (str): Target gene.
            bound (bool): True if TF is bound, False otherwise.
        """
        if gene not in self.genes:
            raise KeyError(f"Gene '{gene}' not found in GRN.")
        self.tf_binding_states[gene] = bound
        logger.debug(f"TF binding state for '{gene}' updated to {bound}")

    def set_epigenetic_modification(self, gene, modification, value):
        """
        Set epigenetic modification for a gene.

        Args:
            gene (str): Target gene.
            modification (str): Modification type (e.g., 'methylation').
            value (any): Modification value or state.
        """
        if gene not in self.genes:
            raise KeyError(f"Gene '{gene}' not found in GRN.")
        self.epigenetic_modifications[gene][modification] = value
        logger.debug(f"Epigenetic modification '{modification}' for '{gene}' set to {value}")


# ---------------------------
# Example toggle switch regulatory logic (for HelixLang users to define)
# ---------------------------

def toggle_switch_rule_A(expression, tf_states, epigenetics, context):
    """
    Gene A expression repressed by Gene B.

    Args:
        expression (dict): Current gene expressions.
        tf_states (dict): TF binding states.
        epigenetics (dict): Epigenetic markers.
        context (dict): External factors (ignored here).

    Returns:
        float: New expression level for Gene A.
    """
    repression_strength = 0.9
    basal_expression = 0.1
    # Simple linear repression
    return basal_expression + (1 - repression_strength * expression.get('B', 0.0))

def toggle_switch_rule_B(expression, tf_states, epigenetics, context):
    """
    Gene B expression repressed by Gene A.

    Args and returns same as above.
    """
    repression_strength = 0.9
    basal_expression = 0.1
    return basal_expression + (1 - repression_strength * expression.get('A', 0.0))


# ---------------------------
# Example usage (for testing or integration with HelixLang scheduler)
# ---------------------------
if __name__ == "__main__":
    # Setup logging for debug
    logging.basicConfig(level=logging.DEBUG)

    genes = ['A', 'B']
    rules = {
        'A': toggle_switch_rule_A,
        'B': toggle_switch_rule_B,
    }
    grn = GeneRegulationNetwork(genes, rules)

    print("Starting toggle switch simulation:")
    for step in range(20):
        expr = grn.step()
        print(f"Step {step+1}: {expr}")
