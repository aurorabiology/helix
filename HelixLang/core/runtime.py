# runtime.py

from collections import deque

class RuntimeError(Exception):
    """Runtime errors during execution of HelixLang code."""
    def __init__(self, message, node=None):
        super().__init__(message)
        self.node = node

class Function:
    """Represents a user-defined function in HelixLang."""
    def __init__(self, name, params, body, closure_env):
        self.name = name
        self.params = params  # list of parameter names
        self.body = body      # AST or IR representing function body
        self.closure_env = closure_env  # Environment where function was defined

    def __repr__(self):
        return f"<Function {self.name}({', '.join(self.params)})>"

class Environment:
    """Represents a variable scope."""
    def __init__(self, parent=None):
        self.values = {}
        self.parent = parent

    def get(self, name):
        if name in self.values:
            return self.values[name]
        elif self.parent:
            return self.parent.get(name)
        else:
            raise RuntimeError(f"Undefined variable '{name}'")

    def set(self, name, value):
        if name in self.values:
            self.values[name] = value
        elif self.parent:
            self.parent.set(name, value)
        else:
            # If variable not found in any parent, define it in current
            self.values[name] = value

    def define(self, name, value):
        self.values[name] = value

class Frame:
    """Represents a single call frame."""
    def __init__(self, func, env):
        self.func = func        # Function object
        self.env = env          # Environment for local variables
        self.return_value = None
        self.is_returning = False

class Runtime:
    def __init__(self):
        self.global_env = Environment()
        self.call_stack = deque()
        self.native_functions = {}

        # Initialize with built-in/native functions
        self.register_native_function("print", self._native_print)
        self.register_native_function("input", self._native_input)

    def push_frame(self, func, args):
        """Create a new call frame for a function call."""
        # New env chains to closure environment to support closures
        env = Environment(parent=func.closure_env)
        # Bind parameters
        if len(args) != len(func.params):
            raise RuntimeError(f"Expected {len(func.params)} arguments but got {len(args)}.")
        for name, val in zip(func.params, args):
            env.define(name, val)
        frame = Frame(func, env)
        self.call_stack.append(frame)
        return frame

    def pop_frame(self):
        """Remove the top call frame."""
        return self.call_stack.pop()

    def current_frame(self):
        if not self.call_stack:
            return None
        return self.call_stack[-1]

    def define_global(self, name, value):
        self.global_env.define(name, value)

    def get_variable(self, name):
        # Check current frame env first, then globals
        frame = self.current_frame()
        if frame:
            try:
                return frame.env.get(name)
            except RuntimeError:
                pass
        return self.global_env.get(name)

    def set_variable(self, name, value):
        frame = self.current_frame()
        if frame:
            try:
                frame.env.set(name, value)
                return
            except RuntimeError:
                pass
        self.global_env.set(name, value)

    def call_function(self, func, args):
        """Invoke a function, user-defined or native."""
        if isinstance(func, Function):
            frame = self.push_frame(func, args)
            try:
                # Assuming function body is AST and we have interpreter to run it:
                # from interpreter import Interpreter
                # interpreter = Interpreter(self)
                # interpreter.execute(func.body)
                # For simplicity, function body execution is deferred or replaced
                raise NotImplementedError("Function execution not implemented yet")
            finally:
                self.pop_frame()
            return frame.return_value
        elif callable(func):
            # Native function
            return func(*args)
        else:
            raise RuntimeError(f"Attempt to call non-function '{func}'")

    # Native functions registration
    def register_native_function(self, name, func):
        self.global_env.define(name, func)
        self.native_functions[name] = func

    # Example native implementations
    def _native_print(self, *args):
        print(*args)

    def _native_input(self, prompt=""):
        return input(prompt)

    # Exception handling helpers
    def runtime_error(self, message, node=None):
        raise RuntimeError(message, node)

    # Environment helpers (if runtime_env.py is used)
    # def load_environment(self):
    #     pass
    # def save_environment(self):
    #     pass
