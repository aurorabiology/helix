from typing import Optional, Dict, List, Union, Any


class Symbol:
    """
    Represents a symbol entry in the symbol table.
    Contains metadata about the symbol: name, type, scope level, mutability, visibility, etc.
    """

    def __init__(
        self,
        name: str,
        typ: Any,  # 'Type' from types.py, or 'FunctionType', or similar
        scope_level: int,
        is_mutable: bool = False,
        is_global: bool = False,
        is_function: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.type = typ
        self.scope_level = scope_level
        self.is_mutable = is_mutable
        self.is_global = is_global
        self.is_function = is_function
        self.metadata = metadata or {}

    def __repr__(self):
        return (f"Symbol(name={self.name}, type={self.type}, scope={self.scope_level}, "
                f"mutable={self.is_mutable}, global={self.is_global}, function={self.is_function})")


class Scope:
    """
    Represents a single scope frame, mapping symbol names to Symbol objects.
    """

    def __init__(self, level: int):
        self.level = level
        self.symbols: Dict[str, Symbol] = {}

    def insert(self, symbol: Symbol) -> None:
        """
        Insert a symbol into this scope.
        Raises an error if the symbol already exists in this scope.
        """
        if symbol.name in self.symbols:
            raise KeyError(f"Symbol '{symbol.name}' already declared in current scope (level {self.level}).")
        self.symbols[symbol.name] = symbol

    def lookup(self, name: str) -> Optional[Symbol]:
        """
        Lookup a symbol by name in this scope only.
        """
        return self.symbols.get(name)

    def __repr__(self):
        return f"Scope(level={self.level}, symbols={list(self.symbols.keys())})"


class SymbolTable:
    """
    Manages a stack of scopes to support nested scoping rules.
    Provides insertion and lookup operations with shadowing.
    """

    def __init__(self):
        self.scopes: List[Scope] = []
        self.current_level: int = -1
        self.enter_scope()  # initialize global scope

    def enter_scope(self) -> None:
        """
        Push a new scope onto the stack.
        """
        self.current_level += 1
        scope = Scope(self.current_level)
        self.scopes.append(scope)
        print(f"Entered new scope level {self.current_level}")

    def exit_scope(self) -> None:
        """
        Pop the current scope off the stack.
        """
        if self.current_level < 0:
            raise RuntimeError("No scope to exit.")
        popped = self.scopes.pop()
        print(f"Exited scope level {popped.level} with symbols: {list(popped.symbols.keys())}")
        self.current_level -= 1

    def insert(
        self,
        name: str,
        typ: Any,
        is_mutable: bool = False,
        is_global: bool = False,
        is_function: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Symbol:
        """
        Insert a new symbol into the current scope.
        Raises if duplicate in current scope.
        """
        symbol = Symbol(name, typ, self.current_level, is_mutable, is_global, is_function, metadata)
        self.scopes[self.current_level].insert(symbol)
        print(f"Inserted symbol '{name}' at scope level {self.current_level}")
        return symbol

    def lookup(self, name: str) -> Optional[Symbol]:
        """
        Lookup a symbol by name, starting from innermost scope to outermost.
        Returns the closest shadowed symbol or None if not found.
        """
        for scope in reversed(self.scopes):
            symbol = scope.lookup(name)
            if symbol:
                print(f"Found symbol '{name}' at scope level {scope.level}")
                return symbol
        print(f"Symbol '{name}' not found in any scope.")
        return None

    def current_scope(self) -> Scope:
        """
        Returns the current innermost scope object.
        """
        return self.scopes[self.current_level]

    def __repr__(self):
        return f"SymbolTable(scopes={self.scopes})"


# --- Example usage and test ---

if __name__ == "__main__":
    from types import IntType, FloatType, FunctionType

    symtab = SymbolTable()

    # Insert global variable
    symtab.insert("x", IntType(), is_mutable=True, is_global=True)
    # Insert global function
    symtab.insert("foo", FunctionType([IntType()], FloatType()), is_function=True)

    symtab.enter_scope()  # enter function/local scope

    # Insert local variable shadows global
    symtab.insert("x", FloatType(), is_mutable=False)

    # Lookup 'x' finds the innermost one (float)
    x_symbol = symtab.lookup("x")
    print(x_symbol)

    # Lookup 'foo' finds global function
    foo_symbol = symtab.lookup("foo")
    print(foo_symbol)

    # Exit local scope
    symtab.exit_scope()

    # Lookup 'x' after exiting returns global int type
    x_symbol = symtab.lookup("x")
    print(x_symbol)
