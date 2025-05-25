# config.py
import os
import json
import argparse
from enum import Enum, auto
from typing import Any, Dict, Optional


class RuntimeMode(Enum):
    INTERPRETED = 'interpreted'
    COMPILED = 'compiled'
    JIT = 'jit'  # future mode


class LanguageDialect(Enum):
    V1 = '1.0'
    V2 = '2.0'
    EXPERIMENTAL = 'experimental'


class ConfigError(Exception):
    pass


class Config:
    """
    Global configuration manager for HelixLang.
    Implements singleton pattern by storing a class-level instance.

    Supports loading config from:
    - Environment variables
    - JSON config files
    - Command-line arguments

    Provides type-safe access with validation.
    """

    _instance = None

    # Default configuration values
    _defaults = {
        'debug_mode': False,
        'optimization_level': 2,  # 0 (none) to 3 (max)
        'runtime_mode': RuntimeMode.INTERPRETED,
        'language_dialect': LanguageDialect.V1,
        'max_stack_depth': 1024,
        'enable_gc': True,
        'log_level': 'INFO',  # DEBUG, INFO, WARN, ERROR
        'config_file_path': None,
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._config = cls._defaults.copy()
            cls._instance._load_sources()
        return cls._instance

    def _load_sources(self):
        """
        Load configuration in order:
        1. From config file (if specified)
        2. From environment variables
        3. From command line arguments
        """
        self._load_from_env()
        self._load_from_file()
        self._load_from_cli()

    def _load_from_env(self):
        # Prefix for environment variables
        prefix = "HELIX_"

        # Map env vars to config keys
        env_map = {
            'DEBUG_MODE': 'debug_mode',
            'OPT_LEVEL': 'optimization_level',
            'RUNTIME_MODE': 'runtime_mode',
            'LANGUAGE_DIALECT': 'language_dialect',
            'MAX_STACK_DEPTH': 'max_stack_depth',
            'ENABLE_GC': 'enable_gc',
            'LOG_LEVEL': 'log_level',
            'CONFIG_FILE_PATH': 'config_file_path',
        }

        for env_key, config_key in env_map.items():
            val = os.getenv(prefix + env_key)
            if val is not None:
                self._set_config_value(config_key, val, source="env")

    def _load_from_file(self):
        path = self._config.get('config_file_path')
        if path:
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                for key, val in data.items():
                    self._set_config_value(key, val, source=f"file:{path}")
            except FileNotFoundError:
                # Config file missing is not fatal, just ignore
                pass
            except json.JSONDecodeError as e:
                raise ConfigError(f"Invalid JSON in config file {path}: {e}")

    def _load_from_cli(self):
        parser = argparse.ArgumentParser(description="HelixLang Configuration")

        parser.add_argument('--debug', action='store_true', help="Enable debug mode")
        parser.add_argument('--opt-level', type=int, choices=range(0,4), help="Optimization level (0-3)")
        parser.add_argument('--runtime', choices=[m.value for m in RuntimeMode], help="Runtime mode")
        parser.add_argument('--dialect', choices=[d.value for d in LanguageDialect], help="Language dialect/version")
        parser.add_argument('--max-stack-depth', type=int, help="Maximum stack depth")
        parser.add_argument('--enable-gc', type=bool, help="Enable garbage collection")
        parser.add_argument('--log-level', choices=['DEBUG','INFO','WARN','ERROR'], help="Logging level")
        parser.add_argument('--config-file', type=str, help="Path to config JSON file")

        args, unknown = parser.parse_known_args()

        # Override only if specified
        if args.debug:
            self._config['debug_mode'] = True
        if args.opt_level is not None:
            self._config['optimization_level'] = args.opt_level
        if args.runtime:
            self._config['runtime_mode'] = RuntimeMode(args.runtime)
        if args.dialect:
            self._config['language_dialect'] = LanguageDialect(args.dialect)
        if args.max_stack_depth is not None:
            self._config['max_stack_depth'] = args.max_stack_depth
        if args.enable_gc is not None:
            self._config['enable_gc'] = args.enable_gc
        if args.log_level:
            self._config['log_level'] = args.log_level
        if args.config_file:
            self._config['config_file_path'] = args.config_file

    def _set_config_value(self, key: str, value: Any, source: Optional[str] = None):
        """
        Set config value with validation and casting.
        """
        try:
            if key == 'debug_mode':
                self._config[key] = self._cast_bool(value)
            elif key == 'optimization_level':
                self._config[key] = self._cast_int(value, 0, 3)
            elif key == 'runtime_mode':
                self._config[key] = RuntimeMode(value) if isinstance(value, str) else value
            elif key == 'language_dialect':
                self._config[key] = LanguageDialect(value) if isinstance(value, str) else value
            elif key == 'max_stack_depth':
                self._config[key] = self._cast_int(value, 1, 100000)
            elif key == 'enable_gc':
                self._config[key] = self._cast_bool(value)
            elif key == 'log_level':
                allowed = ['DEBUG', 'INFO', 'WARN', 'ERROR']
                if value not in allowed:
                    raise ConfigError(f"Invalid log_level '{value}'")
                self._config[key] = value
            elif key == 'config_file_path':
                self._config[key] = str(value)
            else:
                # Unknown keys just store raw
                self._config[key] = value
        except Exception as e:
            raise ConfigError(f"Invalid config value for {key} from {source or 'unknown source'}: {e}")

    def get(self, key: str) -> Any:
        """
        Get the value of a config key.
        """
        if key not in self._config:
            raise ConfigError(f"Config key '{key}' not found.")
        return self._config[key]

    def set(self, key: str, value: Any):
        """
        Dynamically set a config key at runtime.
        """
        self._set_config_value(key, value)

    def all(self) -> Dict[str, Any]:
        """
        Return all config values as a dictionary.
        """
        return self._config.copy()

    def reload(self):
        """
        Reload config from all sources.
        """
        self._config = self._defaults.copy()
        self._load_sources()

    # ====== Helpers ======

    def _cast_bool(self, val):
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            val_lower = val.lower()
            if val_lower in ('true', '1', 'yes', 'on'):
                return True
            elif val_lower in ('false', '0', 'no', 'off'):
                return False
        raise ValueError(f"Cannot cast '{val}' to bool")

    def _cast_int(self, val, min_val=None, max_val=None):
        iv = int(val)
        if min_val is not None and iv < min_val:
            raise ValueError(f"Value {iv} less than min allowed {min_val}")
        if max_val is not None and iv > max_val:
            raise ValueError(f"Value {iv} greater than max allowed {max_val}")
        return iv


# Singleton instance accessible via this:
config = Config()


# Usage example:
# from config import config
# debug = config.get('debug_mode')
# config.set('optimization_level', 3)
