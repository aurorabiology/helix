from typing import List, Dict, Any, Optional, Union
import json
import copy

class RuntimeTypeError(Exception):
    """Exception for runtime type violations."""
    pass

class RuntimeValue:
    """
    Base class for all runtime values in HelixLang.
    Provides interface for:
    - Size calculation (for memory)
    - Serialization and deserialization
    - Equality and comparison
    - Mutation support hooks
    """

    def size_in_bytes(self) -> int:
        raise NotImplementedError("Must implement size_in_bytes")

    def serialize(self) -> str:
        """
        Serialize the object to a JSON-compatible string.
        Used for checkpointing or debugging.
        """
        raise NotImplementedError("Must implement serialize")

    @classmethod
    def deserialize(cls, data: str) -> 'RuntimeValue':
        """
        Deserialize from string to instance.
        """
        raise NotImplementedError("Must implement deserialize")

    def mutate(self, mutation_info: Dict[str, Any]) -> 'RuntimeValue':
        """
        Apply a mutation to the object.
        mutation_info is domain-specific.
        Returns a mutated copy or modifies in place.
        """
        raise NotImplementedError("Must implement mutate")

    def __eq__(self, other: object) -> bool:
        """
        Equality comparison.
        """
        if not isinstance(other, RuntimeValue):
            return False
        return self.serialize() == other.serialize()

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.serialize()}>"

### Basic Types with extension hooks ###

class IntValue(RuntimeValue):
    def __init__(self, value: int):
        self.value = value

    def size_in_bytes(self) -> int:
        return 4  # assuming 32-bit int

    def serialize(self) -> str:
        return json.dumps({"type": "IntValue", "value": self.value})

    @classmethod
    def deserialize(cls, data: str) -> 'IntValue':
        obj = json.loads(data)
        if obj["type"] != "IntValue":
            raise RuntimeTypeError("Type mismatch during deserialization")
        return cls(obj["value"])

    def mutate(self, mutation_info: Dict[str, Any]) -> 'IntValue':
        # Example mutation: add a delta
        delta = mutation_info.get("delta", 0)
        return IntValue(self.value + delta)

class FloatValue(RuntimeValue):
    def __init__(self, value: float):
        self.value = value

    def size_in_bytes(self) -> int:
        return 8  # 64-bit float

    def serialize(self) -> str:
        return json.dumps({"type": "FloatValue", "value": self.value})

    @classmethod
    def deserialize(cls, data: str) -> 'FloatValue':
        obj = json.loads(data)
        if obj["type"] != "FloatValue":
            raise RuntimeTypeError("Type mismatch during deserialization")
        return cls(obj["value"])

    def mutate(self, mutation_info: Dict[str, Any]) -> 'FloatValue':
        delta = mutation_info.get("delta", 0.0)
        return FloatValue(self.value + delta)

class StringValue(RuntimeValue):
    def __init__(self, value: str):
        self.value = value

    def size_in_bytes(self) -> int:
        return len(self.value.encode('utf-8'))

    def serialize(self) -> str:
        return json.dumps({"type": "StringValue", "value": self.value})

    @classmethod
    def deserialize(cls, data: str) -> 'StringValue':
        obj = json.loads(data)
        if obj["type"] != "StringValue":
            raise RuntimeTypeError("Type mismatch during deserialization")
        return cls(obj["value"])

    def mutate(self, mutation_info: Dict[str, Any]) -> 'StringValue':
        # Example mutation: append string
        append_str = mutation_info.get("append", "")
        return StringValue(self.value + append_str)

### Biological Domain-Specific Types ###

class Genome(RuntimeValue):
    """
    Genome represents a sequence of genes.
    Stores gene sequence as a string (e.g., 'ATCGGTA...')
    """

    def __init__(self, sequence: str):
        self.sequence = sequence.upper()  # Normalize to uppercase

    def size_in_bytes(self) -> int:
        # 1 byte per nucleotide for simplicity
        return len(self.sequence)

    def serialize(self) -> str:
        return json.dumps({"type": "Genome", "sequence": self.sequence})

    @classmethod
    def deserialize(cls, data: str) -> 'Genome':
        obj = json.loads(data)
        if obj["type"] != "Genome":
            raise RuntimeTypeError("Type mismatch during deserialization")
        return cls(obj["sequence"])

    def mutate(self, mutation_info: Dict[str, Any]) -> 'Genome':
        """
        Apply mutation to the genome sequence.
        mutation_info example: {"position": int, "new_base": str}
        """
        pos = mutation_info.get("position")
        new_base = mutation_info.get("new_base", "").upper()
        if pos is None or pos < 0 or pos >= len(self.sequence):
            raise RuntimeTypeError("Invalid mutation position")

        if new_base not in {'A', 'T', 'C', 'G'}:
            raise RuntimeTypeError("Invalid base for mutation")

        # Create mutated sequence
        mutated_seq = self.sequence[:pos] + new_base + self.sequence[pos + 1:]
        return Genome(mutated_seq)

    def __repr__(self):
        return f"<Genome seq='{self.sequence[:10]}...' length={len(self.sequence)}>"

class Protein(RuntimeValue):
    """
    Protein with structure and function attributes.
    """
    def __init__(self, structure: str, function: Optional[str] = None):
        # Structure could be a string representing amino acid sequence
        self.structure = structure.upper()
        self.function = function or "Unknown"

    def size_in_bytes(self) -> int:
        return len(self.structure) + len(self.function.encode('utf-8'))

    def serialize(self) -> str:
        return json.dumps({
            "type": "Protein",
            "structure": self.structure,
            "function": self.function
        })

    @classmethod
    def deserialize(cls, data: str) -> 'Protein':
        obj = json.loads(data)
        if obj["type"] != "Protein":
            raise RuntimeTypeError("Type mismatch during deserialization")
        return cls(obj["structure"], obj.get("function"))

    def mutate(self, mutation_info: Dict[str, Any]) -> 'Protein':
        # Mutation example: change amino acid at position
        pos = mutation_info.get("position")
        new_aa = mutation_info.get("new_aa", "").upper()
        if pos is None or pos < 0 or pos >= len(self.structure):
            raise RuntimeTypeError("Invalid mutation position")
        if len(new_aa) != 1 or not new_aa.isalpha():
            raise RuntimeTypeError("Invalid amino acid")

        mutated_structure = self.structure[:pos] + new_aa + self.structure[pos + 1:]
        # Optionally update function as well
        new_function = mutation_info.get("function", self.function)
        return Protein(mutated_structure, new_function)

    def __repr__(self):
        return f"<Protein structure='{self.structure[:10]}...' function='{self.function}'>"

class Cell(RuntimeValue):
    """
    Cell containing genome and proteins.
    """
    def __init__(self, genome: Genome, proteins: Optional[List[Protein]] = None):
        self.genome = genome
        self.proteins = proteins or []

    def size_in_bytes(self) -> int:
        size = self.genome.size_in_bytes()
        size += sum(p.size_in_bytes() for p in self.proteins)
        return size

    def serialize(self) -> str:
        return json.dumps({
            "type": "Cell",
            "genome": json.loads(self.genome.serialize()),
            "proteins": [json.loads(p.serialize()) for p in self.proteins]
        })

    @classmethod
    def deserialize(cls, data: str) -> 'Cell':
        obj = json.loads(data)
        if obj["type"] != "Cell":
            raise RuntimeTypeError("Type mismatch during deserialization")
        genome = Genome.deserialize(json.dumps(obj["genome"]))
        proteins = [Protein.deserialize(json.dumps(p)) for p in obj.get("proteins", [])]
        return cls(genome, proteins)

    def mutate(self, mutation_info: Dict[str, Any]) -> 'Cell':
        """
        Mutation could target genome or proteins.
        mutation_info example:
          {"target": "genome", "mutation": {...}} or
          {"target": "protein", "index": int, "mutation": {...}}
        """
        target = mutation_info.get("target")
        if target == "genome":
            mutated_genome = self.genome.mutate(mutation_info.get("mutation", {}))
            return Cell(mutated_genome, self.proteins)
        elif target == "protein":
            index = mutation_info.get("index")
            if index is None or index < 0 or index >= len(self.proteins):
                raise RuntimeTypeError("Invalid protein index")
            mutated_protein = self.proteins[index].mutate(mutation_info.get("mutation", {}))
            new_proteins = self.proteins[:]
            new_proteins[index] = mutated_protein
            return Cell(self.genome, new_proteins)
        else:
            raise RuntimeTypeError("Mutation target must be 'genome' or 'protein'")

    def __repr__(self):
        return f"<Cell genome={repr(self.genome)} proteins_count={len(self.proteins)}>"

### Optional: Memory Manager Interface ###

class MemoryManager:
    """
    Dummy memory manager interface for demonstration.
    Real implementation integrates with HelixLang runtime memory manager.
    """

    @staticmethod
    def allocate(runtime_value: RuntimeValue) -> int:
        """
        Allocates memory for runtime_value, returns pointer or id.
        """
        # Placeholder implementation
        print(f"[MemoryManager] Allocating {runtime_value.size_in_bytes()} bytes")
        return id(runtime_value)

    @staticmethod
    def deallocate(pointer: int) -> None:
        print(f"[MemoryManager] Deallocating memory at {pointer}")

    @staticmethod
    def update(pointer: int, new_value: RuntimeValue) -> None:
        print(f"[MemoryManager] Updating memory at {pointer} with {new_value}")

### Runtime Type Checking Utility ###

def check_type(obj: RuntimeValue, expected_type: type) -> None:
    if not isinstance(obj, expected_type):
        raise RuntimeTypeError(f"Expected {expected_type.__name__}, got {obj.__class__.__name__}")

