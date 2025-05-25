# helixlang/cli/repl.py

import sys
import traceback
import code
import readline
from helixlang.runtime import eval_helix_code
from helixlang.runtime.context import get_global_context
from helixlang.utils import colorize

# ANSI color codes for terminal output
COLOR_ERROR = "\033[91m"    # Red
COLOR_WARN = "\033[93m"     # Yellow
COLOR_RESET = "\033[0m"     # Reset to default

WELCOME_MSG = """
Welcome to HelixLang REPL
Type 'help' for assistance, 'exit' or 'quit' to leave.
"""

PROMPT = "helix> "
CONT_PROMPT = "...> "

# Initialize REPL global state/context
global_context = get_global_context()

def repl_loop():
    print(WELCOME_MSG)
    buffer = []

    while True:
        try:
            if buffer:
                line = input(CONT_PROMPT)
            else:
                line = input(PROMPT)
        except EOFError:
            print("\nExiting HelixLang REPL.")
            break
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt - Use 'exit' or 'quit' to leave.")
            buffer.clear()
            continue

        # Allow exit commands
        if line.strip() in {"exit", "quit"}:
            print("Bye!")
            break

        # Support multiline input until block is complete
        buffer.append(line)
        source = "\n".join(buffer)

        try:
            # Attempt to parse/compile code to check if complete
            # Using dummy function to check completeness - implement in HelixLang runtime
            if not eval_helix_code.is_complete(source):
                continue  # Input incomplete, prompt for more
        except Exception:
            # If parser error unrelated to incompleteness, show error
            print(colorize("Syntax Error:\n" + traceback.format_exc(), COLOR_ERROR))
            buffer.clear()
            continue

        # Execute the complete source
        try:
            result = eval_helix_code(source, context=global_context)
            if result is not None:
                print(colorize(repr(result), COLOR_WARN))  # Output in yellow as a highlight
        except Exception as e:
            # Print colored traceback
            tb = traceback.format_exc()
            print(colorize(f"Error:\n{tb}", COLOR_ERROR))
        finally:
            buffer.clear()

def start_shell():
    # Optional: setup readline for history, tab completion
    try:
        import rlcompleter
        readline.parse_and_bind("tab: complete")
    except ImportError:
        pass

    # Load history file if desired, e.g., ~/.helixlang_history
    try:
        readline.read_history_file(".helixlang_history")
    except FileNotFoundError:
        pass

    try:
        repl_loop()
    finally:
        # Save history on exit
        try:
            readline.write_history_file(".helixlang_history")
        except Exception:
            pass


if __name__ == "__main__":
    start_shell()
