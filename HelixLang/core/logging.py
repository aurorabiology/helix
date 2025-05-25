# logging.py

"""
HelixLang Logging System

Provides unified logging infrastructure for all components:
parser, compiler, runtime, plugins, etc.

Features:
- Multiple log levels: DEBUG, INFO, WARNING, ERROR
- Console logging with timestamps and module context
- Optional file logging
- Optional JSON structured logs
- Color-coded output for terminal
"""

import os
import sys
import json
import time
import threading
from enum import IntEnum
from typing import Optional, Any


# -----------------------------
# Log Levels
# -----------------------------

class LogLevel(IntEnum):
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40


# -----------------------------
# Color Codes for CLI
# -----------------------------

COLOR_MAP = {
    LogLevel.DEBUG: "\033[90m",   # Grey
    LogLevel.INFO:  "\033[94m",   # Blue
    LogLevel.WARN:  "\033[93m",   # Yellow
    LogLevel.ERROR: "\033[91m",   # Red
    "RESET": "\033[0m"
}


# -----------------------------
# Logger Class
# -----------------------------

class Logger:
    def __init__(
        self,
        name: str,
        level: LogLevel = LogLevel.INFO,
        log_to_file: Optional[str] = None,
        use_json: bool = False,
        enable_colors: bool = True,
    ):
        self.name = name
        self.level = level
        self.log_file_path = log_to_file
        self.use_json = use_json
        self.enable_colors = enable_colors
        self._lock = threading.Lock()

        if self.log_file_path:
            try:
                self.log_file = open(self.log_file_path, "a")
            except Exception as e:
                print(f"Failed to open log file {self.log_file_path}: {e}")
                self.log_file = None
        else:
            self.log_file = None

    def _format_message(self, level: LogLevel, msg: str) -> str:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        return f"{timestamp} [{self.name}] {level.name}: {msg}"

    def _format_json(self, level: LogLevel, msg: str) -> str:
        log_obj = {
            "timestamp": time.time(),
            "datetime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "module": self.name,
            "level": level.name,
            "message": msg
        }
        return json.dumps(log_obj)

    def _write(self, message: str, level: LogLevel):
        with self._lock:
            if self.enable_colors and not self.use_json:
                color = COLOR_MAP.get(level, "")
                reset = COLOR_MAP["RESET"]
                print(f"{color}{message}{reset}", file=sys.stderr if level >= LogLevel.ERROR else sys.stdout)
            else:
                print(message, file=sys.stderr if level >= LogLevel.ERROR else sys.stdout)

            if self.log_file:
                try:
                    self.log_file.write(message + "\n")
                    self.log_file.flush()
                except Exception as e:
                    print(f"Error writing to log file: {e}")

    def log(self, level: LogLevel, msg: str, *args: Any):
        if level < self.level:
            return
        formatted_msg = msg.format(*args)
        output = self._format_json(level, formatted_msg) if self.use_json else self._format_message(level, formatted_msg)
        self._write(output, level)

    # Convenience methods
    def debug(self, msg: str, *args: Any):
        self.log(LogLevel.DEBUG, msg, *args)

    def info(self, msg: str, *args: Any):
        self.log(LogLevel.INFO, msg, *args)

    def warn(self, msg: str, *args: Any):
        self.log(LogLevel.WARN, msg, *args)

    def error(self, msg: str, *args: Any):
        self.log(LogLevel.ERROR, msg, *args)

    def set_level(self, level: LogLevel):
        self.level = level

    def close(self):
        if self.log_file:
            try:
                self.log_file.close()
            except Exception:
                pass


# -----------------------------
# Global Logger Registry
# -----------------------------

_loggers = {}

def get_logger(name: str = "HelixLang") -> Logger:
    """
    Retrieve a logger instance by name.
    Creates a new one if not present.
    """
    if name not in _loggers:
        _loggers[name] = Logger(name=name)
    return _loggers[name]


def configure_global_logger(
    level: LogLevel = LogLevel.INFO,
    log_to_file: Optional[str] = None,
    use_json: bool = False,
    enable_colors: bool = True,
):
    """
    Configure the root HelixLang logger.
    """
    logger = get_logger("HelixLang")
    logger.set_level(level)
    logger.log_file_path = log_to_file
    logger.use_json = use_json
    logger.enable_colors = enable_colors


# -----------------------------
# Example Usage
# -----------------------------

if __name__ == "__main__":
    logger = get_logger("helix.compiler")
    logger.set_level(LogLevel.DEBUG)

    logger.debug("Starting compiler phase: {}", "type-checking")
    logger.info("Compilation successful: {} modules compiled.", 3)
    logger.warn("Unstable optimization for block {}", "GeneAlign")
    logger.error("Compiler crash: {}", "InvalidSyntaxException")

    # JSON logging demo
    json_logger = Logger("helix.runtime", level=LogLevel.DEBUG, use_json=True)
    json_logger.info("Runtime executed with exit code {}", 0)
