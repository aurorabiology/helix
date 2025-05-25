import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

class SettingsError(Exception):
    pass

class Settings:
    _instance = None
    _settings_file = Path.home() / ".helixlang_settings.json"
    _defaults = {
        "theme": "dark",                  # Options: "dark", "light"
        "font": {
            "family": "Courier New",
            "size": 12,
            "style": "normal"             # Options: normal, italic, bold
        },
        "directories": {
            "default_open_dir": str(Path.home()),
            "default_export_dir": str(Path.home() / "HelixExports")
        },
        "visualization": {
            "render_quality": "high",     # Options: low, medium, high
            "show_mutation_sites": True,
            "enable_shadows": True
        },
        "credentials": {
            "api_key": None               # Placeholder for user API key
        }
    }

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance._data = {}
            cls._instance.load()
        return cls._instance

    def load(self):
        """Load settings from file or set to defaults if not found/corrupt."""
        if self._settings_file.exists():
            try:
                with open(self._settings_file, 'r') as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    raise SettingsError("Settings file corrupted or invalid format.")
                self._data = self._merge_dicts(self._defaults, data)
            except (json.JSONDecodeError, SettingsError) as e:
                print(f"[Settings] Failed to load settings, using defaults: {e}")
                self._data = self._defaults.copy()
        else:
            self._data = self._defaults.copy()
            self.save()

    def save(self):
        """Save current settings to file safely."""
        try:
            with open(self._settings_file, 'w') as f:
                json.dump(self._data, f, indent=4)
        except Exception as e:
            print(f"[Settings] Failed to save settings: {e}")

    def reset_to_defaults(self):
        """Reset settings to default values."""
        self._data = self._defaults.copy()
        self.save()

    def get(self, key_path: str, default: Optional[Any] = None) -> Any:
        """Get nested setting by dot-separated key path, e.g., 'font.size'."""
        keys = key_path.split(".")
        current = self._data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    def set(self, key_path: str, value: Any) -> bool:
        """Set nested setting by dot-separated key path with validation."""
        keys = key_path.split(".")
        current = self._data

        # Navigate to last key
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
        last_key = keys[-1]

        # Validate before setting
        if not self._validate_setting(key_path, value):
            print(f"[Settings] Invalid value for setting '{key_path}': {value}")
            return False

        current[last_key] = value
        self.save()
        return True

    def _validate_setting(self, key_path: str, value: Any) -> bool:
        """Validate value depending on setting key path."""
        # Theme
        if key_path == "theme":
            return value in ["dark", "light"]
        # Font size
        if key_path == "font.size":
            return isinstance(value, int) and 6 <= value <= 72
        # Font family (basic check)
        if key_path == "font.family":
            return isinstance(value, str) and len(value) > 0
        # Font style
        if key_path == "font.style":
            return value in ["normal", "italic", "bold"]
        # Directories: ensure paths are strings and directories exist or creatable
        if key_path in ["directories.default_open_dir", "directories.default_export_dir"]:
            if not isinstance(value, str):
                return False
            # Optionally, verify path validity here (e.g., no invalid chars)
            try:
                Path(value).mkdir(parents=True, exist_ok=True)
                return True
            except Exception:
                return False
        # Render quality
        if key_path == "visualization.render_quality":
            return value in ["low", "medium", "high"]
        # Boolean flags
        if key_path in ["visualization.show_mutation_sites", "visualization.enable_shadows"]:
            return isinstance(value, bool)
        # API key (basic validation)
        if key_path == "credentials.api_key":
            # For example, API key must be a non-empty string or None
            return value is None or (isinstance(value, str) and len(value) > 0)
        return True  # Unknown keys accept any value by default

    def _merge_dicts(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge two dicts, giving precedence to override."""
        result = base.copy()
        for k, v in override.items():
            if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                result[k] = self._merge_dicts(result[k], v)
            else:
                result[k] = v
        return result

    def all_settings(self) -> Dict[str, Any]:
        """Return all current settings as dictionary."""
        return self._data.copy()

# Example usage (for CLI or testing):
if __name__ == "__main__":
    settings = Settings()

    # Get theme
    print("Current theme:", settings.get("theme"))

    # Set new font size
    if settings.set("font.size", 16):
        print("Font size updated.")
    else:
        print("Failed to update font size.")

    # Reset all settings to default
    # settings.reset_to_defaults()

    print("All settings:", json.dumps(settings.all_settings(), indent=4))
