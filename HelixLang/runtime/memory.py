from collections import defaultdict
from helixlang.runtime.value_types import RuntimeValue

class MemoryError(Exception):
    """Custom exception for memory-related errors."""
    pass

class MemoryObject:
    """
    Represents an allocated object in memory.
    Holds the data, type info, and reference count.
    """
    def __init__(self, value: RuntimeValue):
        self.value = value
        self.ref_count = 1  # Reference counting for automatic deallocation

    def inc_ref(self):
        self.ref_count += 1

    def dec_ref(self):
        self.ref_count -= 1
        if self.ref_count < 0:
            raise MemoryError("Reference count dropped below zero")

    def is_unreferenced(self):
        return self.ref_count == 0

class MemoryManager:
    """
    MemoryManager controls allocation, deallocation,
    and access of runtime objects in memory.
    Implements a basic heap model with reference counting.
    Also manages stack frames for local variables.
    """

    def __init__(self, heap_size=1024 * 1024):
        # Heap simulated as dict: address -> MemoryObject
        self.heap = {}
        self.next_addr = 1  # Simulated memory address counter

        # Stack: list of dicts representing stack frames local memory
        self.stack_frames = []

        # Mapping from variable name to address for current frame (for quick access)
        self.current_frame_vars = {}

        # Max heap size for simulation (can implement real alloc limits)
        self.heap_size = heap_size
        self.used_heap_size = 0

    ### Heap management methods ###

    def allocate(self, value: RuntimeValue) -> int:
        """
        Allocate a new object on the heap.
        Returns a unique address handle.
        """
        size = value.size_in_bytes()
        if self.used_heap_size + size > self.heap_size:
            raise MemoryError("Out of heap memory")

        addr = self.next_addr
        self.next_addr += 1

        self.heap[addr] = MemoryObject(value)
        self.used_heap_size += size

        return addr

    def deallocate(self, addr: int):
        """
        Deallocate the object at given address if unreferenced.
        """
        if addr not in self.heap:
            raise MemoryError(f"Invalid free at address {addr}")

        obj = self.heap[addr]

        if not obj.is_unreferenced():
            raise MemoryError(f"Attempt to free still-referenced object at {addr}")

        self.used_heap_size -= obj.value.size_in_bytes()
        del self.heap[addr]

    def inc_ref(self, addr: int):
        """
        Increase reference count of the object at address.
        """
        if addr not in self.heap:
            raise MemoryError(f"Invalid inc_ref on address {addr}")
        self.heap[addr].inc_ref()

    def dec_ref(self, addr: int):
        """
        Decrease reference count and deallocate if zero.
        """
        if addr not in self.heap:
            raise MemoryError(f"Invalid dec_ref on address {addr}")

        obj = self.heap[addr]
        obj.dec_ref()

        if obj.is_unreferenced():
            self.deallocate(addr)

    def read(self, addr: int) -> RuntimeValue:
        """
        Read the object value at a given address.
        """
        if addr not in self.heap:
            raise MemoryError(f"Invalid memory read at address {addr}")
        return self.heap[addr].value

    def write(self, addr: int, value: RuntimeValue):
        """
        Write a new value to the object at the given address.
        """
        if addr not in self.heap:
            raise MemoryError(f"Invalid memory write at address {addr}")

        old_obj = self.heap[addr]
        old_size = old_obj.value.size_in_bytes()
        new_size = value.size_in_bytes()

        # Update heap size usage
        self.used_heap_size += (new_size - old_size)

        old_obj.value = value

    ### Stack frame management ###

    def push_stack_frame(self):
        """
        Push a new stack frame for local variables.
        """
        self.stack_frames.append({})
        self.current_frame_vars = self.stack_frames[-1]

    def pop_stack_frame(self):
        """
        Pop the current stack frame and release variables.
        """
        if not self.stack_frames:
            raise MemoryError("Pop stack frame called on empty stack")

        frame = self.stack_frames.pop()
        # Decrement references for all addresses in the frame
        for var, addr in frame.items():
            self.dec_ref(addr)

        # Update current frame pointer
        self.current_frame_vars = self.stack_frames[-1] if self.stack_frames else {}

    def declare_local_variable(self, name: str, value: RuntimeValue):
        """
        Allocate memory for a local variable and bind it.
        """
        addr = self.allocate(value)
        self.current_frame_vars[name] = addr

    def get_local_variable(self, name: str) -> RuntimeValue:
        """
        Retrieve the value of a local variable.
        """
        if name not in self.current_frame_vars:
            raise MemoryError(f"Local variable '{name}' not found in current frame")
        addr = self.current_frame_vars[name]
        return self.read(addr)

    def set_local_variable(self, name: str, value: RuntimeValue):
        """
        Update an existing local variable's value.
        """
        if name not in self.current_frame_vars:
            raise MemoryError(f"Local variable '{name}' not found in current frame")
        addr = self.current_frame_vars[name]
        self.write(addr, value)

    ### Safety checks and utilities ###

    def check_address_valid(self, addr: int) -> bool:
        """
        Check if an address is valid (allocated in heap).
        """
        return addr in self.heap

    def debug_print_heap(self):
        print(f"Heap Usage: {self.used_heap_size} / {self.heap_size} bytes")
        for addr, obj in self.heap.items():
            print(f"Addr {addr}: Value={obj.value} RefCount={obj.ref_count}")

    def debug_print_stack(self):
        print("Stack Frames:")
        for idx, frame in enumerate(self.stack_frames):
            print(f"Frame {idx}:")
            for var, addr in frame.items():
                val = self.read(addr)
                print(f"  {var} -> Addr {addr} = {val}")

