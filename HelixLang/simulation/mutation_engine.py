"""
mutation_engine.py

HelixLang Mutation Engine Module

Simulates probabilistic mutations during biological simulations.
Handles point mutations, insertions/deletions, chromosomal rearrangements,
influenced by environment and internal cellular states.

Integrates with gene regulatory and metabolic modules by modifying parameters/states.
Supports logging and checkpointing for reproducibility.

Author: HelixLang Team
Date: 2025-05-24
"""

import random
import logging

logger = logging.getLogger("helixlang.mutation_engine")


class MutationEngine:
    """
    Mutation engine managing probabilistic mutations on genetic elements.
    """

    def __init__(self, env_model, grn_model, metabolic_model, base_mutation_rate=1e-6):
        """
        Initialize mutation engine.

        Args:
            env_model (EnvironmentModel): Reference to environment to get stress info.
            grn_model (object): Reference to gene regulatory network module to apply mutations.
            metabolic_model (object): Reference to metabolic pathways model to apply mutations.
            base_mutation_rate (float): Baseline mutation probability per gene/unit time.
        """
        self.env_model = env_model
        self.grn_model = grn_model
        self.metabolic_model = metabolic_model
        self.base_mutation_rate = base_mutation_rate

        # User-definable mutation spectra (probabilities for mutation types)
        self.mutation_spectra = {
            "point": 0.8,
            "insertion": 0.1,
            "deletion": 0.1,
            "rearrangement": 0.01
        }

        self.mutation_log = []

    def _calculate_mutation_rate(self, cell_state):
        """
        Calculate effective mutation rate influenced by environment and cell state.

        Args:
            cell_state (dict): Includes DNA repair efficiency, etc.

        Returns:
            float: Effective mutation probability.
        """
        # Example: increase mutation under environmental stress
        stress_factor = self._get_environmental_stress()
        repair_efficiency = cell_state.get("dna_repair_efficiency", 1.0)

        rate = self.base_mutation_rate * stress_factor * (1.0 / repair_efficiency)
        logger.debug(f"Calculated mutation rate: {rate} (stress_factor={stress_factor}, repair_efficiency={repair_efficiency})")
        return rate

    def _get_environmental_stress(self):
        """
        Get a scalar representing environmental stress from env_model.

        Returns:
            float: Stress factor >= 1.0 (1 means baseline).
        """
        # Simplified: Higher concentration of toxins or chemicals raises stress
        stress_chemicals = ["toxin", "radiation"]

        stress_factor = 1.0
        for chem in stress_chemicals:
            if chem in self.env_model.chemicals:
                idx = self.env_model.chemicals.index(chem)
                avg_conc = self.env_model.concentrations[idx].mean()
                stress_factor += avg_conc * 0.1  # tunable factor

        logger.debug(f"Environmental stress factor: {stress_factor}")
        return max(1.0, stress_factor)

    def _choose_mutation_type(self):
        """
        Randomly choose a mutation type based on mutation spectra.

        Returns:
            str: Mutation type.
        """
        types = list(self.mutation_spectra.keys())
        probs = list(self.mutation_spectra.values())
        total = sum(probs)
        norm_probs = [p / total for p in probs]
        chosen = random.choices(types, norm_probs)[0]
        logger.debug(f"Chosen mutation type: {chosen}")
        return chosen

    def _apply_mutation(self, mutation_type, target_gene):
        """
        Apply the mutation of given type to the target gene or pathway.

        Args:
            mutation_type (str): One of ['point', 'insertion', 'deletion', 'rearrangement'].
            target_gene (str): Identifier for gene or pathway affected.
        """
        logger.info(f"Applying {mutation_type} mutation to gene {target_gene}")

        if mutation_type == "point":
            # Simulate point mutation: alter gene parameters in grn_model
            self.grn_model.mutate_point(target_gene)
        elif mutation_type == "insertion":
            # Insert sequence - change gene length or regulatory region
            self.grn_model.mutate_insertion(target_gene)
        elif mutation_type == "deletion":
            # Delete part of gene or regulatory element
            self.grn_model.mutate_deletion(target_gene)
        elif mutation_type == "rearrangement":
            # Large-scale rearrangement - could affect multiple genes or pathways
            self.grn_model.mutate_rearrangement(target_gene)
            self.metabolic_model.adjust_pathways(target_gene)

        # Log mutation event
        mutation_record = {
            "gene": target_gene,
            "type": mutation_type,
            "timestamp": self._current_sim_time()
        }
        self.mutation_log.append(mutation_record)

    def _current_sim_time(self):
        """
        Placeholder for current simulation time retrieval.

        Returns:
            float: Current simulation time.
        """
        # In real HelixLang integration, retrieve from global simulation scheduler
        import time
        return time.time()

    def simulate_mutations(self, cell_population_states):
        """
        Simulate mutations over a cell population.

        Args:
            cell_population_states (list[dict]): List of cell states, each with info including
                'gene_list' (list of genes), 'dna_repair_efficiency', etc.

        Returns:
            list: Updated cell population states with mutations applied.
        """
        updated_states = []
        for cell_state in cell_population_states:
            mutation_rate = self._calculate_mutation_rate(cell_state)
            mutated_genes = []

            for gene in cell_state.get("gene_list", []):
                if random.random() < mutation_rate:
                    mut_type = self._choose_mutation_type()
                    self._apply_mutation(mut_type, gene)
                    mutated_genes.append((gene, mut_type))

            cell_state["mutated_genes"] = mutated_genes
            updated_states.append(cell_state)

        return updated_states

    def export_mutation_log(self):
        """
        Export logged mutations for checkpointing or debugging.

        Returns:
            list[dict]: Mutation event records.
        """
        return self.mutation_log.copy()


# -----------------------
# Example usage
# -----------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Dummy stubs for GRN and Metabolic modules
    class DummyGRN:
        def mutate_point(self, gene): print(f"Point mutation on {gene}")
        def mutate_insertion(self, gene): print(f"Insertion mutation on {gene}")
        def mutate_deletion(self, gene): print(f"Deletion mutation on {gene}")
        def mutate_rearrangement(self, gene): print(f"Rearrangement mutation on {gene}")

    class DummyMetabolic:
        def adjust_pathways(self, gene): print(f"Adjust metabolic pathways for {gene}")

    # Create environment with 'toxin' chemical to increase stress
    from env_model import EnvironmentModel
    env = EnvironmentModel(chemicals=["nutrient", "toxin"])
    env.add_chemical_source("toxin", (0, 0, 0), 50)  # high toxin concentration

    # Initialize mutation engine
    mutation_engine = MutationEngine(env_model=env,
                                     grn_model=DummyGRN(),
                                     metabolic_model=DummyMetabolic(),
                                     base_mutation_rate=1e-5)

    # Example cell population states
    cells = [
        {"gene_list": ["geneA", "geneB", "geneC"], "dna_repair_efficiency": 0.5},
        {"gene_list": ["geneX", "geneY"], "dna_repair_efficiency": 1.0}
    ]

    updated_cells = mutation_engine.simulate_mutations(cells)
    print("Mutation log:", mutation_engine.export_mutation_log())
