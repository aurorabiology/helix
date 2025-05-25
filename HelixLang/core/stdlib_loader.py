# stdlib_loader.py

import os
from typing import List, Dict, Optional
from helixlang import parser, compiler, symbols, errors

class StdLibLoader:
    """
    Loads and integrates HelixLang standard library source files.

    Responsibilities:
    - Locate stdlib source files in `stdlib/` directory.
    - Parse source files into ASTs using parser.
    - Compile ASTs into IR using compiler.
    - Inject stdlib symbols into global environment.
    """

    def __init__(self, stdlib_path: Optional[str] = None):
        """
        Initialize the loader.

        Args:
            stdlib_path: Optional custom path to the stdlib directory.
                         Defaults to 'stdlib' relative to current working directory.
        """
        self.stdlib_path = stdlib_path or os.path.join(os.getcwd(), "stdlib")
        self.files_to_load: List[str] = []
        self.loaded_modules: Dict[str, Dict] = {}
        # keys: module name, values: dict with 'ast', 'ir', 'symbols'

    def discover_files(self) -> None:
        """
        Discover all HelixLang stdlib source files (.hl) in the stdlib directory.
        Populates self.files_to_load with absolute file paths.
        """
        if not os.path.isdir(self.stdlib_path):
            raise errors.RuntimeError(f"Stdlib directory not found at {self.stdlib_path}")

        files = []
        for filename in os.listdir(self.stdlib_path):
            if filename.endswith(".hl"):
                full_path = os.path.join(self.stdlib_path, filename)
                files.append(full_path)
        if not files:
            raise errors.RuntimeError(f"No stdlib source files (.hl) found in {self.stdlib_path}")

        self.files_to_load = sorted(files)  # deterministic order

    def load_all(self, global_symbol_table: symbols.SymbolTable) -> None:
        """
        Load, parse, compile, and integrate all stdlib files into the global symbol table.

        Args:
            global_symbol_table: The global symbol table/environment to inject stdlib symbols into.
        """
        self.discover_files()

        for filepath in self.files_to_load:
            module_name = self._extract_module_name(filepath)
            try:
                source_code = self._read_source(filepath)
                ast_root = self._parse_source(source_code, filepath)
                ir = self._compile_ast(ast_root)
                module_symbols = self._extract_symbols(ast_root, global_symbol_table)

                # Inject symbols into the global symbol table
                self._inject_symbols(global_symbol_table, module_symbols)

                # Cache loaded module info
                self.loaded_modules[module_name] = {
                    'ast': ast_root,
                    'ir': ir,
                    'symbols': module_symbols,
                    'filepath': filepath,
                }

                print(f"[StdLibLoader] Loaded stdlib module '{module_name}' from '{filepath}'")

            except (errors.SyntaxError, errors.RuntimeError, errors.TypeError) as e:
                raise errors.RuntimeError(f"Failed to load stdlib module '{module_name}': {e}")

    def _extract_module_name(self, filepath: str) -> str:
        """
        Derive module name from filename (e.g. base.hl -> base).
        """
        filename = os.path.basename(filepath)
        module_name, _ = os.path.splitext(filename)
        return module_name

    def _read_source(self, filepath: str) -> str:
        """
        Read source code from a stdlib file.
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except IOError as e:
            raise errors.RuntimeError(f"Unable to read stdlib file '{filepath}': {e}")

    def _parse_source(self, source_code: str, filepath: str):
        """
        Parse source code into AST using helixlang.parser.

        Args:
            source_code: The raw source code string.
            filepath: For error reporting.

        Returns:
            AST root node.
        """
        try:
            return parser.parse(source_code, source_name=filepath)
        except errors.SyntaxError as e:
            raise errors.SyntaxError(f"Syntax error in stdlib file '{filepath}': {e}")

    def _compile_ast(self, ast_root):
        """
        Compile AST to IR using helixlang.compiler.

        Args:
            ast_root: The AST root node.

        Returns:
            IR nodes or IR module representation.
        """
        try:
            return compiler.compile(ast_root)
        except errors.RuntimeError as e:
            raise errors.RuntimeError(f"Compilation error in stdlib: {e}")

    def _extract_symbols(self, ast_root, global_symbol_table: symbols.SymbolTable):
        """
        Extract symbols (functions, types, constants) from the AST of stdlib.

        For simplicity, assume AST nodes have a method or attribute
        to enumerate declared symbols.

        Args:
            ast_root: The AST root node.
            global_symbol_table: Used to check for conflicts.

        Returns:
            Dict[str, symbols.SymbolInfo] mapping symbol names to info.
        """
        # This is a placeholder. Real implementation depends on AST structure.
        declared_symbols = {}

        # Example traversal:
        for decl in ast_root.get_declarations():
            name = decl.name
            typ = decl.type_info
            # Additional metadata: mutability, visibility, etc.
            symbol_info = symbols.SymbolInfo(name=name, type=typ, scope_level=0, mutable=False, visible=True)

            if global_symbol_table.lookup(name):
                raise errors.RuntimeError(f"Stdlib symbol '{name}' conflicts with existing symbol")

            declared_symbols[name] = symbol_info

        return declared_symbols

    def _inject_symbols(self, global_symbol_table: symbols.SymbolTable, symbols_dict: Dict[str, symbols.SymbolInfo]):
        """
        Inject stdlib symbols into the global symbol table.

        Args:
            global_symbol_table: The global symbol table.
            symbols_dict: Dict of symbol names to SymbolInfo.
        """
        for name, symbol_info in symbols_dict.items():
            global_symbol_table.insert(symbol_info)

    def get_loaded_modules(self) -> List[str]:
        """
        Returns a list of loaded stdlib module names.
        """
        return list(self.loaded_modules.keys())

    def get_module_info(self, module_name: str) -> Optional[Dict]:
        """
        Get detailed info about a loaded stdlib module.

        Returns:
            Dict containing 'ast', 'ir', 'symbols', 'filepath' or None if not found.
        """
        return self.loaded_modules.get(module_name)


# Singleton-like instance to be used throughout HelixLang runtime
stdlib_loader = StdLibLoader()
