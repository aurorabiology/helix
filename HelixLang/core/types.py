from typing import List, Dict, Optional, Union, Any


# --- Base Type Class ---

class Type:
    """
    Base class for all HelixLang types.
    """

    def is_subtype_of(self, other: 'Type') -> bool:
        """
        Check if self is a subtype of other.
        Default: strict equality.
        Override in subclasses.
        """
        return self == other

    def unify(self, other: 'Type') -> Optional['Type']:
        """
        Attempts to unify two types.
        Returns the unified type if compatible, else None.
        """
        if self == other:
            return self
        return None

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return str(self)


# --- Primitive Types ---

class IntType(Type):
    def __eq__(self, other):
        return isinstance(other, IntType)


class FloatType(Type):
    def __eq__(self, other):
        return isinstance(other, FloatType) or isinstance(other, IntType)  # Int <: Float

    def is_subtype_of(self, other: 'Type') -> bool:
        # FloatType is subtype of itself only
        return isinstance(other, FloatType)

    def unify(self, other: 'Type') -> Optional['Type']:
        if isinstance(other, IntType) or isinstance(other, FloatType):
            return FloatType()
        return None


class BoolType(Type):
    def __eq__(self, other):
        return isinstance(other, BoolType)


class StringType(Type):
    def __eq__(self, other):
        return isinstance(other, StringType)


# --- Domain-Specific Types ---

class GenomeType(Type):
    """
    Represents genome sequences in HelixLang.
    """
    def __eq__(self, other):
        return isinstance(other, GenomeType)


class ProteinType(Type):
    """
    Represents protein sequences or structures.
    """
    def __eq__(self, other):
        return isinstance(other, ProteinType)


class CellType(Type):
    """
    Represents biological cells.
    """
    def __eq__(self, other):
        return isinstance(other, CellType)


# --- Composite / Constructed Types ---

class ArrayType(Type):
    """
    Array of elements of some base type.
    """
    def __init__(self, element_type: Type):
        self.element_type = element_type

    def __eq__(self, other):
        return isinstance(other, ArrayType) and self.element_type == other.element_type

    def is_subtype_of(self, other: 'Type') -> bool:
        if not isinstance(other, ArrayType):
            return False
        return self.element_type.is_subtype_of(other.element_type)

    def unify(self, other: 'Type') -> Optional['Type']:
        if not isinstance(other, ArrayType):
            return None
        elem_type = self.element_type.unify(other.element_type)
        if elem_type is None:
            return None
        return ArrayType(elem_type)

    def __str__(self):
        return f"Array[{self.element_type}]"


class TupleType(Type):
    """
    Tuple of fixed length and types.
    """
    def __init__(self, element_types: List[Type]):
        self.element_types = element_types

    def __eq__(self, other):
        if not isinstance(other, TupleType):
            return False
        return all(
            a == b for a, b in zip(self.element_types, other.element_types)
        ) and len(self.element_types) == len(other.element_types)

    def is_subtype_of(self, other: 'Type') -> bool:
        if not isinstance(other, TupleType):
            return False
        if len(self.element_types) != len(other.element_types):
            return False
        return all(
            a.is_subtype_of(b) for a, b in zip(self.element_types, other.element_types)
        )

    def unify(self, other: 'Type') -> Optional['Type']:
        if not isinstance(other, TupleType):
            return None
        if len(self.element_types) != len(other.element_types):
            return None
        unified_elements = []
        for a, b in zip(self.element_types, other.element_types):
            unified = a.unify(b)
            if unified is None:
                return None
            unified_elements.append(unified)
        return TupleType(unified_elements)

    def __str__(self):
        elems = ", ".join(str(t) for t in self.element_types)
        return f"Tuple[{elems}]"


class StructType(Type):
    """
    Named fields with associated types.
    """
    def __init__(self, name: str, fields: Dict[str, Type]):
        self.name = name
        self.fields = fields

    def __eq__(self, other):
        if not isinstance(other, StructType):
            return False
        if self.name != other.name:
            return False
        # Exact field match (order doesn't matter)
        return self.fields == other.fields

    def is_subtype_of(self, other: 'Type') -> bool:
        if not isinstance(other, StructType):
            return False
        if self.name != other.name:
            return False
        # Struct subtyping could allow extra fields in self (width subtyping)
        for key, typ in other.fields.items():
            if key not in self.fields or not self.fields[key].is_subtype_of(typ):
                return False
        return True

    def unify(self, other: 'Type') -> Optional['Type']:
        if not isinstance(other, StructType) or self.name != other.name:
            return None
        unified_fields = {}
        for key in self.fields.keys() | other.fields.keys():
            t1 = self.fields.get(key)
            t2 = other.fields.get(key)
            if t1 and t2:
                unified = t1.unify(t2)
                if unified is None:
                    return None
                unified_fields[key] = unified
            else:
                # One struct is missing the field -> no unification
                return None
        return StructType(self.name, unified_fields)

    def __str__(self):
        fields_str = ", ".join(f"{k}: {v}" for k, v in self.fields.items())
        return f"Struct {self.name} {{ {fields_str} }}"


class FunctionType(Type):
    """
    Function signature: parameters and return type.
    """
    def __init__(self, param_types: List[Type], return_type: Type):
        self.param_types = param_types
        self.return_type = return_type

    def __eq__(self, other):
        if not isinstance(other, FunctionType):
            return False
        return (len(self.param_types) == len(other.param_types) and
                all(a == b for a, b in zip(self.param_types, other.param_types)) and
                self.return_type == other.return_type)

    def is_subtype_of(self, other: 'Type') -> bool:
        """
        Function subtyping:
        Contravariant in parameter types,
        Covariant in return type.
        """
        if not isinstance(other, FunctionType):
            return False
        if len(self.param_types) != len(other.param_types):
            return False
        # Check contravariance for parameters
        for a, b in zip(other.param_types, self.param_types):
            if not a.is_subtype_of(b):
                return False
        # Covariance for return type
        return self.return_type.is_subtype_of(other.return_type)

    def unify(self, other: 'Type') -> Optional['Type']:
        if not isinstance(other, FunctionType):
            return None
        if len(self.param_types) != len(other.param_types):
            return None
        unified_params = []
        for a, b in zip(self.param_types, other.param_types):
            unified = a.unify(b)
            if unified is None:
                return None
            unified_params.append(unified)
        unified_return = self.return_type.unify(other.return_type)
        if unified_return is None:
            return None
        return FunctionType(unified_params, unified_return)

    def __str__(self):
        params_str = ", ".join(str(p) for p in self.param_types)
        return f"({params_str}) -> {self.return_type}"


# --- Type Utilities and Inference Helpers ---

def least_upper_bound(t1: Type, t2: Type) -> Optional[Type]:
    """
    Compute the least upper bound (common supertype) of two types,
    if it exists.
    """
    if t1.is_subtype_of(t2):
        return t2
    if t2.is_subtype_of(t1):
        return t1
    # No direct subtype relation - for primitives we can promote int->float, etc.
    # Extend this logic based on domain needs.
    # Example: int and float -> float
    if (isinstance(t1, IntType) and isinstance(t2, FloatType)) or \
       (isinstance(t2, IntType) and isinstance(t1, FloatType)):
        return FloatType()
    return None

def are_compatible(t1: Type, t2: Type) -> bool:
    """
    Check if two types are compatible for assignments, function calls, etc.
    """
    return t1.is_subtype_of(t2) or t2.is_subtype_of(t1)


# --- Type Registry (Optional for quick lookup) ---

PRIMITIVE_TYPES = {
    "int": IntType(),
    "float": FloatType(),
    "bool": BoolType(),
    "string": StringType(),
    "genome": GenomeType(),
    "protein": ProteinType(),
    "cell": CellType()
}


# --- Example usage for type checking ---

if __name__ == "__main__":
    int_t = IntType()
    float_t = FloatType()
    bool_t = BoolType()
    string_t = StringType()

    print("Is int subtype of float?", int_t.is_subtype_of(float_t))  # True
    print("Unify int and float:", int_t.unify(float_t))              # FloatType
    print("Unify bool and int:", bool_t.unify(int_t))                # None

    arr_of_int = ArrayType(int_t)
    arr_of_float = ArrayType(float_t)
    print("Array[int] subtype of Array[float]?", arr_of_int.is_subtype_of(arr_of_float))  # True

    # Function type example
    f1 = FunctionType([int_t, float_t], bool_t)
    f2 = FunctionType([int_t, float_t], bool_t)
    print("Function types equal?", f1 == f2)  # True

    # Struct example
    struct1 = StructType("Gene", {"sequence": GenomeType(), "length": IntType()})
    struct2 = StructType("Gene", {"sequence": GenomeType(), "length": IntType()})
    print("Structs equal?", struct1 == struct2)  # True
