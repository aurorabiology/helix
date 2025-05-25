import random
import threading
from typing import List, Optional, Dict, Any, Union

from helixlang.runtime.value_types import Genome, Protein, Cell, RuntimeTypeError

# Mutation configuration: default parameters
DEFAULT_MUTATION_RATE = 0.01  # 1% mutation chance per base
DEFAULT_MUTATION_TYPES = ["point", "insertion", "deletion"]
DEFAULT_DETERMINISTIC = False  # stochastic by default

# Thread lock for mutation safety in parallel contexts
_mutation_lock = threading.RLock()

# Mutation record structure for tracking history
class MutationRecord:
    def __init__(self, mutation_type: str, target_obj: Any, details: Dict[str, Any]):
        self.mutation_type = mutation_type  # e.g., 'point', 'insertion', 'deletion'
        self.target_obj = target_obj
        self.details = details  # e.g., position, old_value, new_value

    def __repr__(self):
        return f"MutationRecord(type={self.mutation_type}, details={self.details})"


class MutationRuntime:
    """
    Handles mutation operations on biological data types at runtime.
    Tracks mutation history and supports rollback.
    """

    def __init__(self, 
                 mutation_rate: float = DEFAULT_MUTATION_RATE, 
                 mutation_types: Optional[List[str]] = None, 
                 deterministic: bool = DEFAULT_DETERMINISTIC):
        self.mutation_rate = mutation_rate
        self.mutation_types = mutation_types if mutation_types else DEFAULT_MUTATION_TYPES
        self.deterministic = deterministic
        self.history: List[MutationRecord] = []

    def _random_choice(self, choices: List[Any]) -> Any:
        if self.deterministic:
            return choices[0]  # Always pick the first for deterministic behavior
        else:
            return random.choice(choices)

    def _should_mutate(self) -> bool:
        if self.deterministic:
            return True
        return random.random() < self.mutation_rate

    def point_mutation(self, genome: Genome, position: int, new_base: str) -> Genome:
        """
        Applies a point mutation at `position` in the genome to `new_base`.
        Records the mutation in history.
        """
        with _mutation_lock:
            if position < 0 or position >= len(genome.sequence):
                raise IndexError("Point mutation position out of range")

            old_base = genome.sequence[position]
            if old_base == new_base:
                # No mutation needed if base is the same
                return genome

            # Apply mutation using Genome's mutation method or direct mutation
            mutated_genome = genome.mutate({"position": position, "new_base": new_base})

            # Record mutation history
            record = MutationRecord(
                mutation_type="point",
                target_obj=genome,
                details={"position": position, "old_base": old_base, "new_base": new_base}
            )
            self.history.append(record)

            return mutated_genome

    def insertion_mutation(self, genome: Genome, position: int, insertion_seq: str) -> Genome:
        """
        Inserts a sequence at the specified position.
        """
        with _mutation_lock:
            if position < 0 or position > len(genome.sequence):
                raise IndexError("Insertion position out of range")

            old_seq = genome.sequence

            new_seq = old_seq[:position] + insertion_seq + old_seq[position:]
            mutated_genome = Genome(new_seq)

            record = MutationRecord(
                mutation_type="insertion",
                target_obj=genome,
                details={"position": position, "inserted_seq": insertion_seq}
            )
            self.history.append(record)

            return mutated_genome

    def deletion_mutation(self, genome: Genome, position: int, length: int = 1) -> Genome:
        """
        Deletes a subsequence of given length starting from position.
        """
        with _mutation_lock:
            if position < 0 or (position + length) > len(genome.sequence):
                raise IndexError("Deletion range out of bounds")

            old_seq = genome.sequence
            deleted_seq = old_seq[position:position + length]
            new_seq = old_seq[:position] + old_seq[position + length:]
            mutated_genome = Genome(new_seq)

            record = MutationRecord(
                mutation_type="deletion",
                target_obj=genome,
                details={"position": position, "deleted_seq": deleted_seq}
            )
            self.history.append(record)

            return mutated_genome

    def apply_stochastic_mutation(self, genome: Genome) -> Genome:
        """
        Applies mutations randomly across the genome based on mutation_rate and allowed mutation_types.
        """
        with _mutation_lock:
            seq_list = list(genome.sequence)
            length = len(seq_list)
            for pos in range(length):
                if not self._should_mutate():
                    continue

                mutation_type = self._random_choice(self.mutation_types)
                logger_msg = f"Applying {mutation_type} at position {pos} on genome."
                print(logger_msg)  # Could use logging instead

                if mutation_type == "point":
                    # Mutate base at position
                    bases = ['A', 'C', 'G', 'T']
                    current_base = seq_list[pos]
                    possible_bases = [b for b in bases if b != current_base]
                    new_base = self._random_choice(possible_bases)
                    seq_list[pos] = new_base
                    self.history.append(MutationRecord("point", genome, {"position": pos, "old_base": current_base, "new_base": new_base}))

                elif mutation_type == "insertion":
                    # Insert a random base after current position
                    bases = ['A', 'C', 'G', 'T']
                    insertion_base = self._random_choice(bases)
                    seq_list.insert(pos, insertion_base)
                    self.history.append(MutationRecord("insertion", genome, {"position": pos, "inserted_base": insertion_base}))

                elif mutation_type == "deletion":
                    # Delete base at current position if possible
                    if length > 1:
                        deleted_base = seq_list.pop(pos)
                        self.history.append(MutationRecord("deletion", genome, {"position": pos, "deleted_base": deleted_base}))
                        length -= 1

            mutated_seq = ''.join(seq_list)
            mutated_genome = Genome(mutated_seq)
            return mutated_genome

    def rollback_last_mutation(self) -> bool:
        """
        Attempts to rollback the last mutation by reversing its effect.
        Returns True if rollback succeeded, False if no history or rollback unsupported.
        """
        with _mutation_lock:
            if not self.history:
                return False

            last_mutation = self.history.pop()

            if last_mutation.mutation_type == "point":
                # Reverse point mutation
                genome = last_mutation.target_obj
                pos = last_mutation.details["position"]
                old_base = last_mutation.details["old_base"]
                # Revert mutation
                reverted_genome = genome.mutate({"position": pos, "new_base": old_base})
                return reverted_genome

            elif last_mutation.mutation_type == "insertion":
                genome = last_mutation.target_obj
                pos = last_mutation.details["position"]
                inserted_seq = last_mutation.details["inserted_seq"]
                # Remove inserted sequence
                seq = genome.sequence
                new_seq = seq[:pos] + seq[pos + len(inserted_seq):]
                reverted_genome = Genome(new_seq)
                return reverted_genome

            elif last_mutation.mutation_type == "deletion":
                genome = last_mutation.target_obj
                pos = last_mutation.details["position"]
                deleted_seq = last_mutation.details["deleted_seq"]
                # Re-insert deleted sequence
                seq = genome.sequence
                new_seq = seq[:pos] + deleted_seq + seq[pos:]
                reverted_genome = Genome(new_seq)
                return reverted_genome

            else:
                # Unsupported mutation rollback
                return False

    def mutate_protein(self, protein: Protein, mutation_func: Optional[Any] = None) -> Protein:
        """
        Apply mutations to a Protein. Mutation_func is a user-defined function accepting Protein.
        """
        with _mutation_lock:
            if mutation_func:
                mutated_protein = mutation_func(protein)
            else:
                # Default: randomly change one amino acid in structure
                structure = list(protein.structure)
                if not structure:
                    return protein
                pos = random.randint(0, len(structure) - 1)
                amino_acids = list("ACDEFGHIKLMNPQRSTVWY")  # Standard amino acids
                current_aa = structure[pos]
                possible_aas = [aa for aa in amino_acids if aa != current_aa]
                new_aa = self._random_choice(possible_aas)
                structure[pos] = new_aa
                mutated_protein = Protein(''.join(structure))

            self.history.append(MutationRecord("protein_mutation", protein, {"details": "custom mutation applied"}))
            return mutated_protein

    def mutate_cell(self, cell: Cell, protein_mutation_func: Optional[Any] = None) -> Cell:
        """
        Mutate the Cell by mutating its Genome and Proteins.
        """
        with _mutation_lock:
            # Mutate genome
            mutated_genome = self.apply_stochastic_mutation(cell.genome)

            # Mutate proteins
            mutated_proteins = []
            for prot in cell.proteins:
                mutated_proteins.append(self.mutate_protein(prot, mutation_func=protein_mutation_func))

            mutated_cell = Cell(genome=mutated_genome, proteins=mutated_proteins, behaviors=cell.behaviors)
            self.history.append(MutationRecord("cell_mutation", cell, {"details": "genome + protein mutations"}))
            return mutated_cell

