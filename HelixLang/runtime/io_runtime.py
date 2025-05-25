import os
import io
import json
import threading
from typing import Optional, Union, Any, Callable
from pathlib import Path

from helixlang.runtime.value_types import Genome, Cell, Protein

# Thread lock for safe concurrent I/O
_io_lock = threading.RLock()

# Allowed base directory for sandboxed file access (can be configured)
_SANDBOX_BASE_PATH = Path("/sandbox/helixlang_io")

# Ensure sandbox directory exists
_SANDBOX_BASE_PATH.mkdir(parents=True, exist_ok=True)

# Buffer size for streaming reads/writes
_DEFAULT_BUFFER_SIZE = 4096

# Exception for unsafe file access attempts
class UnsafeAccessError(PermissionError):
    pass

def _is_safe_path(base_dir: Path, target_path: Path) -> bool:
    """
    Ensure that the target_path is within the base_dir sandbox.
    Prevents directory traversal attacks.
    """
    try:
        base_dir = base_dir.resolve()
        target_path = target_path.resolve()
        return str(target_path).startswith(str(base_dir))
    except Exception:
        return False

def _serialize_data(obj: Any) -> str:
    """
    Serialize complex HelixLang domain objects to JSON string.
    Supports Genome, Cell, Protein types.
    """
    if isinstance(obj, Genome):
        return json.dumps({"type": "Genome", "sequence": obj.sequence})
    elif isinstance(obj, Protein):
        return json.dumps({"type": "Protein", "structure": obj.structure})
    elif isinstance(obj, Cell):
        # Recursively serialize genome and proteins
        return json.dumps({
            "type": "Cell",
            "genome": {"sequence": obj.genome.sequence},
            "proteins": [{"structure": p.structure} for p in obj.proteins],
            "behaviors": obj.behaviors
        })
    else:
        raise TypeError(f"Unsupported serialization type: {type(obj)}")

def _deserialize_data(data: str) -> Any:
    """
    Deserialize JSON string to HelixLang domain objects.
    """
    obj = json.loads(data)
    obj_type = obj.get("type")
    if obj_type == "Genome":
        return Genome(obj["sequence"])
    elif obj_type == "Protein":
        return Protein(obj["structure"])
    elif obj_type == "Cell":
        genome = Genome(obj["genome"]["sequence"])
        proteins = [Protein(p["structure"]) for p in obj["proteins"]]
        behaviors = obj.get("behaviors", [])
        return Cell(genome=genome, proteins=proteins, behaviors=behaviors)
    else:
        raise TypeError(f"Unsupported deserialization type: {obj_type}")


class IORuntime:
    """
    Runtime system for handling all I/O operations in HelixLang.
    Supports file, console, and future network I/O with sandboxing and serialization.
    """

    def __init__(self, sandbox_path: Optional[Union[str, Path]] = None):
        if sandbox_path is not None:
            self.sandbox_base = Path(sandbox_path).resolve()
        else:
            self.sandbox_base = _SANDBOX_BASE_PATH

        # Create sandbox directory if missing
        self.sandbox_base.mkdir(parents=True, exist_ok=True)

    def _check_path_safe(self, file_path: Union[str, Path]) -> Path:
        """
        Validate that file_path is inside the sandbox.
        Raise UnsafeAccessError if not safe.
        """
        path = Path(file_path).resolve()
        if not _is_safe_path(self.sandbox_base, path):
            raise UnsafeAccessError(f"Access to path {path} is denied (outside sandbox).")
        return path

    def read_file(self, file_path: Union[str, Path], buffer_size: int = _DEFAULT_BUFFER_SIZE) -> str:
        """
        Read the content of a file safely and return as string.
        Buffered reading for performance.
        """
        with _io_lock:
            path = self._check_path_safe(file_path)
            if not path.is_file():
                raise FileNotFoundError(f"File not found: {path}")

            with open(path, "r", encoding="utf-8") as f:
                buffer = []
                while True:
                    chunk = f.read(buffer_size)
                    if not chunk:
                        break
                    buffer.append(chunk)
                return ''.join(buffer)

    def write_file(self, file_path: Union[str, Path], data: Union[str, Genome, Cell, Protein], buffer_size: int = _DEFAULT_BUFFER_SIZE):
        """
        Write data to file, supporting serialization of complex objects.
        Uses buffered writing.
        """
        with _io_lock:
            path = self._check_path_safe(file_path)

            # Serialize if domain type
            if isinstance(data, (Genome, Cell, Protein)):
                serialized = _serialize_data(data)
            elif isinstance(data, str):
                serialized = data
            else:
                raise TypeError(f"Unsupported data type for writing: {type(data)}")

            with open(path, "w", encoding="utf-8") as f:
                # Write in chunks if large
                for i in range(0, len(serialized), buffer_size):
                    f.write(serialized[i:i+buffer_size])

    def read_stdin(self, prompt: Optional[str] = None) -> str:
        """
        Read from standard input.
        """
        with _io_lock:
            if prompt:
                print(prompt, end='', flush=True)
            return input()

    def write_stdout(self, data: Union[str, Genome, Cell, Protein]):
        """
        Write to standard output. Serialize domain types as strings.
        """
        with _io_lock:
            if isinstance(data, (Genome, Cell, Protein)):
                print(_serialize_data(data))
            else:
                print(str(data))

    def write_stderr(self, data: Union[str, Exception]):
        """
        Write error messages to standard error.
        """
        with _io_lock:
            import sys
            if isinstance(data, Exception):
                print(f"Error: {repr(data)}", file=sys.stderr)
            else:
                print(str(data), file=sys.stderr)

    def log_debug(self, message: str):
        """
        Runtime debug logging (could be extended to log files).
        """
        with _io_lock:
            print(f"[DEBUG] {message}")

    # Placeholder for future asynchronous or network I/O support
    def async_read_file(self, *args, **kwargs):
        raise NotImplementedError("Async I/O not yet implemented.")

    def async_write_file(self, *args, **kwargs):
        raise NotImplementedError("Async I/O not yet implemented.")

    def network_send(self, *args, **kwargs):
        raise NotImplementedError("Network I/O not yet implemented.")

    def network_receive(self, *args, **kwargs):
        raise NotImplementedError("Network I/O not yet implemented.")
