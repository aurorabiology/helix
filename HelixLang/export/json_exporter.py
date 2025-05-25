import json
from typing import Any, Dict, List, Optional, Callable, Union, Iterator

class JSONExporter:
    """
    Exports HelixLang simulation/runtime state, models, or data into JSON format.
    """

    def __init__(
        self,
        indent: int = 4,
        include_metadata: bool = True,
        include_raw_data: bool = True,
        include_derived_stats: bool = True,
        custom_filter: Optional[Callable[[str, Any], bool]] = None,
        chunk_size: int = 1000,
    ):
        """
        Parameters:
            indent: Number of spaces for pretty JSON indentation.
            include_metadata: Whether to include metadata fields.
            include_raw_data: Whether to include raw simulation/model data.
            include_derived_stats: Whether to include derived statistics.
            custom_filter: Optional callback to filter keys/values.
                Signature: (key: str, value: Any) -> bool, return True to include.
            chunk_size: Number of elements per chunk when streaming large data.
        """
        self.indent = indent
        self.include_metadata = include_metadata
        self.include_raw_data = include_raw_data
        self.include_derived_stats = include_derived_stats
        self.custom_filter = custom_filter
        self.chunk_size = chunk_size

    def export(
        self,
        obj: Any,
        to_file: Optional[str] = None,
        stream: bool = False,
    ) -> Optional[str]:
        """
        Serialize an object to JSON.

        Parameters:
            obj: The Python object representing HelixLang state/model.
            to_file: If specified, write JSON output to this file.
            stream: If True and obj is iterable, yields JSON chunks (generator).

        Returns:
            JSON string if to_file is None and stream=False,
            else None.
        """
        if stream and hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes, dict)):
            # Stream large iterable data as JSON chunks
            gen = self._stream_serialize(obj)
            if to_file:
                with open(to_file, "w") as f:
                    for chunk in gen:
                        f.write(chunk)
                return None
            else:
                # Return generator of JSON strings
                return gen

        # Otherwise, serialize all at once
        serializable_obj = self._prepare_obj(obj)
        json_str = json.dumps(serializable_obj, indent=self.indent)
        if to_file:
            with open(to_file, "w") as f:
                f.write(json_str)
            return None
        else:
            return json_str

    def _prepare_obj(self, obj: Any) -> Any:
        """
        Recursively prepare the object for JSON serialization.

        Applies filters for metadata/raw data/derived stats.
        Converts any custom HelixLang classes to dict.
        """
        if isinstance(obj, dict):
            new_dict = {}
            for k, v in obj.items():
                if not self._include_key(k):
                    continue
                new_dict[k] = self._prepare_obj(v)
            return new_dict
        elif isinstance(obj, (list, tuple, set)):
            return [self._prepare_obj(i) for i in obj]
        elif hasattr(obj, "to_dict"):
            # Support custom HelixLang objects that implement to_dict()
            return self._prepare_obj(obj.to_dict())
        elif hasattr(obj, "__dict__"):
            # Fallback for custom objects without to_dict()
            return self._prepare_obj(vars(obj))
        else:
            # Primitive types or unknown types, return as-is
            return obj

    def _include_key(self, key: str) -> bool:
        """
        Determine if a key should be included based on filters and options.
        """
        key_lower = key.lower()
        if not self.include_metadata and key_lower.startswith("meta"):
            return False
        if not self.include_raw_data and key_lower.startswith("raw"):
            return False
        if not self.include_derived_stats and ("stat" in key_lower or "derived" in key_lower):
            return False
        if self.custom_filter and not self.custom_filter(key, None):
            return False
        return True

    def _stream_serialize(self, iterable: Any) -> Iterator[str]:
        """
        Stream serialize large iterable objects in JSON array chunks.
        """
        yield "[\n"
        first_chunk = True
        chunk = []
        count = 0

        for item in iterable:
            chunk.append(self._prepare_obj(item))
            count += 1
            if count % self.chunk_size == 0:
                chunk_json = json.dumps(chunk, indent=self.indent)[1:-1]  # remove surrounding []
                if not first_chunk:
                    yield ",\n"
                yield chunk_json
                first_chunk = False
                chunk = []

        # Yield remaining items
        if chunk:
            chunk_json = json.dumps(chunk, indent=self.indent)[1:-1]
            if not first_chunk:
                yield ",\n"
            yield chunk_json

        yield "\n]\n"


# === Example HelixLang-compatible data classes ===

class ProteinFoldingState:
    def __init__(self, id: str, residues: List[Dict[str, Any]], metadata: Dict[str, Any]):
        self.id = id
        self.residues = residues
        self.metadata = metadata

    def to_dict(self):
        return {
            "id": self.id,
            "residues": self.residues,
            "metadata": self.metadata
        }

class SimulationCheckpoint:
    def __init__(self, step: int, time: float, state: Any, stats: Dict[str, float], raw_data: Any):
        self.step = step
        self.time = time
        self.state = state
        self.stats = stats
        self.raw_data = raw_data

    def to_dict(self):
        return {
            "step": self.step,
            "time": self.time,
            "state": self.state,
            "stats": self.stats,
            "raw_data": self.raw_data,
        }

# === Usage example ===

def example_usage():
    # Construct sample folding state
    folding_state = ProteinFoldingState(
        id="folding_01",
        residues=[
            {"name": "ALA", "position": 1, "coords": [1.2, 2.3, 3.4]},
            {"name": "GLY", "position": 2, "coords": [1.5, 2.1, 3.8]},
        ],
        metadata={"created_by": "HelixLang", "version": "1.0"},
    )

    # Construct checkpoint
    checkpoint = SimulationCheckpoint(
        step=100,
        time=12.5,
        state=folding_state,
        stats={"energy": -23.5, "rmsd": 1.2},
        raw_data={"temperature": 300, "pressure": 1.0},
    )

    exporter = JSONExporter(
        indent=2,
        include_metadata=True,
        include_raw_data=False,  # exclude raw data for export
        include_derived_stats=True,
    )

    json_text = exporter.export(checkpoint)
    print(json_text)


if __name__ == "__main__":
    example_usage()
