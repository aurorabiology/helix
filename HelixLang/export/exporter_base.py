import os
import io
import json
import gzip
import logging
import datetime
import importlib
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Type, List, Callable

# === Configure global logger ===
logger = logging.getLogger("helixlang.exporters")
logger.setLevel(logging.DEBUG)  # Change to INFO or WARNING in production
ch = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


# === Exceptions ===

class ExporterError(Exception):
    """Base class for exporter-specific errors."""
    pass

class ValidationError(ExporterError):
    """Thrown when exported data fails format validation."""
    pass


# === Abstract Base Exporter ===

class BaseExporter(ABC):
    """
    Abstract base class for HelixLang exporter modules.
    All exporters should inherit from this and implement `export`.
    """

    # Optional format/version metadata
    format_name: str = "generic"
    format_version: Optional[str] = None

    # Exporter version info
    exporter_version: str = "1.0"

    def __init__(self, metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize exporter with optional metadata dictionary.
        Metadata may contain author info, timestamps, versioning, etc.
        """
        self.metadata = metadata or {}
        self._attach_standard_metadata()
        self._setup_logger()

    def _setup_logger(self):
        self.logger = logger

    def _attach_standard_metadata(self):
        """
        Add standard metadata if not present: timestamp, exporter version.
        """
        if "export_timestamp" not in self.metadata:
            self.metadata["export_timestamp"] = datetime.datetime.utcnow().isoformat() + "Z"
        if "exporter_version" not in self.metadata:
            self.metadata["exporter_version"] = self.exporter_version
        if "format_name" not in self.metadata:
            self.metadata["format_name"] = self.format_name
        if self.format_version and "format_version" not in self.metadata:
            self.metadata["format_version"] = self.format_version

    @abstractmethod
    def export(self, data: Any, output_path: str) -> None:
        """
        Export the given data to the specified output path.
        Must be implemented by subclasses.

        Args:
            data: Arbitrary data to export, typically HelixLang objects.
            output_path: Path to write the exported file.
        """
        raise NotImplementedError

    def validate(self, exported_content: str) -> bool:
        """
        Optional: Validate the exported content against format-specific rules or schemas.
        Override in subclasses as needed.

        Args:
            exported_content: String content to validate.

        Returns:
            True if valid, else raise ValidationError.
        """
        # By default, no validation implemented
        self.logger.debug("Validation skipped: no schema defined.")
        return True

    def _write_file_safely(self, output_path: str, content: str, compress: bool = False) -> None:
        """
        Safely write content to a file, optionally compressing with gzip.

        Args:
            output_path: Path to output file.
            content: String content to write.
            compress: If True, compress output using gzip.
        """
        try:
            dir_path = os.path.dirname(output_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path)
                self.logger.debug(f"Created directory path: {dir_path}")

            if compress:
                if not output_path.endswith(".gz"):
                    output_path += ".gz"
                with gzip.open(output_path, "wt", encoding="utf-8") as gz_file:
                    gz_file.write(content)
                self.logger.info(f"Exported compressed file: {output_path}")
            else:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.logger.info(f"Exported file: {output_path}")

        except Exception as e:
            self.logger.error(f"Failed to write file {output_path}: {e}")
            raise ExporterError(f"File write error: {e}") from e

    def _format_header(self, title: str, extra_info: Optional[Dict[str, str]] = None) -> str:
        """
        Format a standard header comment block for exported files.

        Args:
            title: Main title/header line.
            extra_info: Optional dict of key-value metadata to include.

        Returns:
            Formatted header string.
        """
        lines = [
            f"# {title}",
            f"# Exported by HelixLang Exporter v{self.exporter_version}",
            f"# Timestamp: {self.metadata.get('export_timestamp', 'unknown')}",
        ]
        if extra_info:
            for k, v in extra_info.items():
                lines.append(f"# {k}: {v}")

        header = "\n".join(lines) + "\n\n"
        self.logger.debug(f"Generated header:\n{header}")
        return header

    def _encode_special_chars(self, s: str) -> str:
        """
        Utility to encode special characters safely (e.g., XML escaping).
        Override for formats that require special encoding.

        Args:
            s: Input string.

        Returns:
            Encoded string.
        """
        # Default: minimal escaping for XML
        return (
            s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;")
             .replace("'", "&apos;")
        )



# === Plugin registration system ===

class ExporterRegistry:
    """
    Registry for HelixLang exporters.
    Allows dynamic registration and discovery.
    """
    _exporters: Dict[str, Type[BaseExporter]] = {}

    @classmethod
    def register_exporter(cls, name: str, exporter_cls: Type[BaseExporter]) -> None:
        if name in cls._exporters:
            logger.warning(f"Exporter '{name}' is already registered and will be overwritten.")
        cls._exporters[name] = exporter_cls
        logger.debug(f"Registered exporter: {name}")

    @classmethod
    def get_exporter(cls, name: str) -> Optional[Type[BaseExporter]]:
        return cls._exporters.get(name)

    @classmethod
    def list_exporters(cls) -> List[str]:
        return list(cls._exporters.keys())

    @classmethod
    def load_exporters_from_module(cls, module_name: str) -> None:
        """
        Dynamically import a module and register exporters found in it.

        Args:
            module_name: Python module name (e.g., 'helixlang.exporters.fasta_exporter')
        """
        try:
            module = importlib.import_module(module_name)
            # Expect the module to call register_exporter internally for each exporter class.
            logger.info(f"Loaded exporters from module {module_name}")
        except ImportError as e:
            logger.error(f"Failed to load module {module_name}: {e}")
            raise ExporterError(f"Failed to load exporter module: {e}") from e


# === Example usage of the base exporter ===

if __name__ == "__main__":
    # Example dummy exporter subclass to demonstrate usage
    class DummyExporter(BaseExporter):
        format_name = "dummy"
        format_version = "0.1"

        def export(self, data: Any, output_path: str) -> None:
            content = self._format_header("Dummy Export")
            content += json.dumps(data, indent=2)
            self._write_file_safely(output_path, content)

    # Register dummy exporter dynamically
    ExporterRegistry.register_exporter("dummy", DummyExporter)

    # Create exporter instance and export some data
    exporter = DummyExporter(metadata={"author": "Murari Ambati"})
    exporter.export({"gene": "ATGC", "score": 42}, "dummy_export.json")
