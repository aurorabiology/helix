import math
import logging
from typing import List, Any, Dict, Union, Optional

# Import HelixLang runtime types for domain-specific functions
from helixlang.runtime.value_types import Genome, Protein, Cell, RuntimeValue, RuntimeTypeError

# Configure logging for runtime debug output
logger = logging.getLogger("helixlang.runtime.std_functions")
logger.setLevel(logging.DEBUG)  # Set level to DEBUG for detailed logs

# Console handler for immediate output
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
logger.addHandler(console_handler)

### Basic Math Functions ###

def std_add(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    logger.debug(f"std_add called with a={a}, b={b}")
    return a + b

def std_subtract(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    logger.debug(f"std_subtract called with a={a}, b={b}")
    return a - b

def std_multiply(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    logger.debug(f"std_multiply called with a={a}, b={b}")
    return a * b

def std_divide(a: Union[int, float], b: Union[int, float]) -> Union[float, None]:
    logger.debug(f"std_divide called with a={a}, b={b}")
    if b == 0:
        logger.error("Division by zero")
        raise ZeroDivisionError("Division by zero in std_divide")
    return a / b

def std_sqrt(x: float) -> float:
    logger.debug(f"std_sqrt called with x={x}")
    if x < 0:
        logger.error("sqrt of negative number")
        raise ValueError("Cannot compute square root of negative number")
    return math.sqrt(x)

def std_pow(base: float, exponent: float) -> float:
    logger.debug(f"std_pow called with base={base}, exponent={exponent}")
    return math.pow(base, exponent)


### String Utilities ###

def std_str_concat(a: str, b: str) -> str:
    logger.debug(f"std_str_concat called with a='{a}', b='{b}'")
    return a + b

def std_str_length(s: str) -> int:
    logger.debug(f"std_str_length called with s='{s}'")
    return len(s)

def std_str_substring(s: str, start: int, length: Optional[int] = None) -> str:
    logger.debug(f"std_str_substring called with s='{s}', start={start}, length={length}")
    if start < 0 or start >= len(s):
        logger.error("start index out of range")
        raise IndexError("Start index out of range")
    if length is None:
        return s[start:]
    if length < 0:
        logger.error("length cannot be negative")
        raise ValueError("Length cannot be negative")
    return s[start:start + length]

def std_str_upper(s: str) -> str:
    logger.debug(f"std_str_upper called with s='{s}'")
    return s.upper()

def std_str_lower(s: str) -> str:
    logger.debug(f"std_str_lower called with s='{s}'")
    return s.lower()

### Collection Utilities ###

def std_list_length(lst: List[Any]) -> int:
    logger.debug(f"std_list_length called with list of length {len(lst)}")
    return len(lst)

def std_list_append(lst: List[Any], item: Any) -> List[Any]:
    logger.debug(f"std_list_append called with item={item}")
    lst.append(item)
    return lst

def std_list_pop(lst: List[Any]) -> Any:
    if not lst:
        logger.error("pop from empty list")
        raise IndexError("pop from empty list")
    item = lst.pop()
    logger.debug(f"std_list_pop popped item={item}")
    return item

def std_list_get(lst: List[Any], index: int) -> Any:
    logger.debug(f"std_list_get called with index={index}")
    if index < 0 or index >= len(lst):
        logger.error("index out of range")
        raise IndexError("index out of range")
    return lst[index]

### Biological Domain-Specific Functions ###

def std_genome_length(genome: Genome) -> int:
    logger.debug(f"std_genome_length called with genome length {len(genome.sequence)}")
    return len(genome.sequence)

def std_genome_mutate(genome: Genome, position: int, new_base: str) -> Genome:
    logger.debug(f"std_genome_mutate called with position={position}, new_base={new_base}")
    mutation_info = {"position": position, "new_base": new_base}
    try:
        mutated_genome = genome.mutate(mutation_info)
    except RuntimeTypeError as e:
        logger.error(f"Genome mutation error: {e}")
        raise
    return mutated_genome

def std_protein_fold(protein: Protein) -> str:
    """
    Placeholder for protein folding simulation.
    Returns a string representing predicted fold (mock).
    """
    logger.debug(f"std_protein_fold called on protein with structure length {len(protein.structure)}")
    # Simulate folding logic (placeholder)
    fold_prediction = f"FoldedStructure_{protein.structure[:5]}..._{len(protein.structure)}aa"
    logger.debug(f"Fold prediction: {fold_prediction}")
    return fold_prediction

def std_cell_protein_count(cell: Cell) -> int:
    logger.debug(f"std_cell_protein_count called with {len(cell.proteins)} proteins")
    return len(cell.proteins)

def std_cell_add_protein(cell: Cell, protein: Protein) -> Cell:
    logger.debug(f"std_cell_add_protein called, adding protein with structure length {len(protein.structure)}")
    new_proteins = cell.proteins + [protein]
    return Cell(cell.genome, new_proteins)

### Runtime Environment Interface (Stub) ###

_runtime_environment: Dict[str, Any] = {}

def std_env_get_var(name: str) -> Any:
    logger.debug(f"std_env_get_var called with name='{name}'")
    if name not in _runtime_environment:
        logger.error(f"Environment variable '{name}' not found")
        raise KeyError(f"Environment variable '{name}' not found")
    return _runtime_environment[name]

def std_env_set_var(name: str, value: Any) -> None:
    logger.debug(f"std_env_set_var called with name='{name}', value={value}")
    _runtime_environment[name] = value

### Logging and Debugging Utilities ###

def std_log_info(message: str) -> None:
    logger.info(message)

def std_log_warn(message: str) -> None:
    logger.warning(message)

def std_log_error(message: str) -> None:
    logger.error(message)

def std_debug_dump(obj: Any) -> None:
    """
    Dump object representation to log for debugging.
    """
    logger.debug(f"Debug Dump: {repr(obj)}")

### Error Handling Helpers ###

def std_raise_runtime_error(message: str) -> None:
    logger.error(f"Runtime Error: {message}")
    raise RuntimeError(message)

### Extensibility ###

class StdLib:
    """
    Registry for standard functions, allowing easy addition.
    """
    _functions: Dict[str, Any] = {}

    @classmethod
    def register(cls, name: str, func: Any) -> None:
        logger.debug(f"Registering stdlib function '{name}'")
        cls._functions[name] = func

    @classmethod
    def call(cls, name: str, *args, **kwargs) -> Any:
        if name not in cls._functions:
            logger.error(f"Stdlib function '{name}' not found")
            raise RuntimeError(f"Stdlib function '{name}' not found")
        logger.debug(f"Calling stdlib function '{name}' with args={args}, kwargs={kwargs}")
        return cls._functions[name](*args, **kwargs)

# Register all functions
StdLib.register("add", std_add)
StdLib.register("subtract", std_subtract)
StdLib.register("multiply", std_multiply)
StdLib.register("divide", std_divide)
StdLib.register("sqrt", std_sqrt)
StdLib.register("pow", std_pow)

StdLib.register("str_concat", std_str_concat)
StdLib.register("str_length", std_str_length)
StdLib.register("str_substring", std_str_substring)
StdLib.register("str_upper", std_str_upper)
StdLib.register("str_lower", std_str_lower)

StdLib.register("list_length", std_list_length)
StdLib.register("list_append", std_list_append)
StdLib.register("list_pop", std_list_pop)
StdLib.register("list_get", std_list_get)

StdLib.register("genome_length", std_genome_length)
StdLib.register("genome_mutate", std_genome_mutate)
StdLib.register("protein_fold", std_protein_fold)
StdLib.register("cell_protein_count", std_cell_protein_count)
StdLib.register("cell_add_protein", std_cell_add_protein)

StdLib.register("env_get_var", std_env_get_var)
StdLib.register("env_set_var", std_env_set_var)

StdLib.register("log_info", std_log_info)
StdLib.register("log_warn", std_log_warn)
StdLib.register("log_error", std_log_error)
StdLib.register("debug_dump", std_debug_dump)

StdLib.register("raise_runtime_error", std_raise_runtime_error)
