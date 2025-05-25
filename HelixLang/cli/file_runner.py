# helixlang/cli/file_runner.py

import os
import sys
import traceback
from helixlang.parser import parse_source_code
from helixlang.ir import load_ir, compile_ast_to_ir
from helixlang.runtime import execute_ir, execute_source
from helixlang.io import read_file, write_file
from helixlang.utils import colorize

COLOR_ERROR = "\033[91m"
COLOR_RESET = "\033[0m"

def run_file(filepath: str, *, debug=False):
    """
    Entry point to load, compile (if needed), and execute a HelixLang file.
    Supports `.hlx` (source) and `.hxir` (intermediate representation).
    """

    if not os.path.isfile(filepath):
        print(colorize(f"File not found: {filepath}", COLOR_ERROR))
        sys.exit(1)

    _, ext = os.path.splitext(filepath)
    ext = ext.lower()

    try:
        if ext == ".hlx":
            # Read source code
            source = read_file(filepath)

            if debug:
                print(f"Parsing source from {filepath}...")

            # Parse AST
            ast = parse_source_code(source)

            if debug:
                print("Compiling AST to IR...")

            # Compile AST to IR
            ir = compile_ast_to_ir(ast)

            if debug:
                print(f"Executing IR for {filepath}...")

            # Execute IR
            result = execute_ir(ir)

            return result

        elif ext == ".hxir":
            # Load IR directly from file
            if debug:
                print(f"Loading IR from {filepath}...")

            ir = load_ir(filepath)

            if debug:
                print("Executing loaded IR...")

            result = execute_ir(ir)

            return result

        else:
            print(colorize(f"Unsupported file type: {ext}", COLOR_ERROR))
            sys.exit(1)

    except Exception as e:
        tb = traceback.format_exc()
        print(colorize(f"Error running file {filepath}:\n{tb}", COLOR_ERROR))
        sys.exit(1)

# Optional: Watcher to auto-reload on changes (for development)
def watch_and_run(filepath: str, debug=False):
    """
    Watches file for changes, auto recompiles and reruns.
    Requires watchdog or similar file watching package.
    """
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        print("Watch mode requires watchdog package. Install via pip.")
        return

    class ReloadHandler(FileSystemEventHandler):
        def on_modified(self, event):
            if event.src_path == os.path.abspath(filepath):
                print(f"Detected changes in {filepath}, re-running...")
                run_file(filepath, debug=debug)

    observer = Observer()
    event_handler = ReloadHandler()
    observer.schedule(event_handler, path=os.path.dirname(filepath) or ".", recursive=False)
    observer.start()

    try:
        print(f"Watching {filepath} for changes. Press Ctrl+C to stop.")
        run_file(filepath, debug=debug)  # Run first time

        while True:
            pass  # Keep running

    except KeyboardInterrupt:
        print("Stopping watch mode...")
        observer.stop()
    observer.join()


# CLI entry for direct run usage:
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run HelixLang .hlx or .hxir files")
    parser.add_argument("file", help="Path to HelixLang source (.hlx) or IR (.hxir) file")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--watch", action="store_true", help="Watch file and reload on changes")

    args = parser.parse_args()

    if args.watch:
        watch_and_run(args.file, debug=args.debug)
    else:
        run_file(args.file, debug=args.debug)
