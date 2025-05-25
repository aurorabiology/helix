from collections import deque

class RuntimeError(Exception):
    """Custom exception for runtime environment errors."""
    pass

class Scope:
    """
    Represents a single scope's symbol table.
    Implements dictionary-like storage for variable bindings.
    """
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent  # Link to outer scope (for nested lookup)

    def get(self, name):
        if name in self.symbols:
            return self.symbols[name]
        elif self.parent:
            return self.parent.get(name)
        else:
            raise RuntimeError(f"Variable '{name}' is not defined in the current scope chain.")

    def set(self, name, value):
        # Set variable in the current scope or recursively in outer scope if exists
        if name in self.symbols:
            self.symbols[name] = value
        elif self.parent and self.parent.has(name):
            self.parent.set(name, value)
        else:
            # New variable assignment in current scope
            self.symbols[name] = value

    def declare(self, name, value=None):
        # Declare a new variable in the current scope, error if redefined
        if name in self.symbols:
            raise RuntimeError(f"Variable '{name}' already declared in current scope.")
        self.symbols[name] = value

    def has(self, name):
        if name in self.symbols:
            return True
        elif self.parent:
            return self.parent.has(name)
        return False

class StackFrame:
    """
    Represents a function call frame.
    Contains local scope and execution context info.
    """
    def __init__(self, function_name, return_address=None, parent_scope=None):
        self.function_name = function_name
        self.local_scope = Scope(parent=parent_scope)
        self.return_address = return_address
        self.instruction_pointer = 0  # For interpreters tracking
        self.metadata = {}  # Additional info (e.g., debug info, call depth)

class RuntimeEnv:
    """
    Core runtime environment manager.
    Manages call stack, scopes, variables, and execution state.
    """

    def __init__(self):
        # Global scope lives at the bottom and never disappears
        self.global_scope = Scope()
        # Call stack of StackFrame instances
        self.call_stack = deque()
        # Start with global "frame" that acts as top-level scope context
        self.push_stack_frame(function_name="<global>", parent_scope=self.global_scope)

    def push_stack_frame(self, function_name, return_address=None, parent_scope=None):
        """
        Enter a new function scope (stack frame).
        """
        frame = StackFrame(function_name, return_address, parent_scope)
        self.call_stack.append(frame)
        return frame

    def pop_stack_frame(self):
        """
        Exit current function scope.
        """
        if len(self.call_stack) <= 1:
            # Do not pop global frame
            raise RuntimeError("Attempted to pop global frame which is not allowed.")
        return self.call_stack.pop()

    def current_frame(self):
        """
        Returns the current active StackFrame.
        """
        return self.call_stack[-1]

    def get_variable(self, name):
        """
        Lookup variable from current local scope up to global.
        """
        return self.current_frame().local_scope.get(name)

    def set_variable(self, name, value):
        """
        Set variable value, respecting nested scopes.
        If variable exists in an outer scope, update there;
        else, create in current local scope.
        """
        self.current_frame().local_scope.set(name, value)

    def declare_variable(self, name, value=None):
        """
        Declare a new variable in the current local scope.
        """
        self.current_frame().local_scope.declare(name, value)

    def variable_exists(self, name):
        """
        Check if variable exists in current or outer scopes.
        """
        return self.current_frame().local_scope.has(name)

    def call_function(self, function_name, args):
        """
        Simulate a function call: push a new frame,
        bind arguments as variables in local scope.
        """
        # For demonstration, assume we have a way to get function metadata (signature, body)
        # In real system, this would fetch from runtime function table or IR
        func_meta = self.lookup_function(function_name)
        if len(args) != len(func_meta['params']):
            raise RuntimeError(f"Function '{function_name}' expects {len(func_meta['params'])} arguments, got {len(args)}.")

        # Create new stack frame, child of global scope for now
        new_frame = self.push_stack_frame(function_name=function_name, parent_scope=self.global_scope)

        # Bind arguments
        for param_name, arg_value in zip(func_meta['params'], args):
            new_frame.local_scope.declare(param_name, arg_value)

        # Set instruction pointer or other context as needed
        new_frame.instruction_pointer = 0

        # Return new frame for further execution control
        return new_frame

    def lookup_function(self, function_name):
        """
        Placeholder for function metadata lookup.
        In full runtime, this connects to function registry or IR.
        """
        # Example stub
        example_functions = {
            "foo": {"params": ["x", "y"], "body": None},
            "bar": {"params": [], "body": None},
        }
        if function_name not in example_functions:
            raise RuntimeError(f"Function '{function_name}' is not defined.")
        return example_functions[function_name]

    def current_instruction_pointer(self):
        """
        Get current instruction pointer of top frame.
        """
        return self.current_frame().instruction_pointer

    def set_instruction_pointer(self, ip):
        """
        Set current instruction pointer of top frame.
        """
        self.current_frame().instruction_pointer = ip

    # Additional debugging and error hooks could be added here
    def debug_print_stack(self):
        print("Call Stack (most recent last):")
        for frame in self.call_stack:
            print(f" - {frame.function_name} (IP={frame.instruction_pointer})")

    def debug_print_variables(self):
        print("Variables in current frame:")
        for name, value in self.current_frame().local_scope.symbols.items():
            print(f"  {name} = {value}")

# Example usage inside a runtime system might look like:
# env = RuntimeEnv()
# env.declare_variable("a", 10)
# env.set_variable("a", 20)
# val = env.get_variable("a")  # 20
# env.call_function("foo", [1, 2])
