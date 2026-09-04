"""
VM Test Suite - Comprehensive tests for VM execution engine

Tests cover:
- Register operations
- Instruction dispatch
- Memory operations
- Control flow
- Error handling
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orthos.vm.core import OrthosVM, VMState, Register, Instruction
from orthos.vm.loader import OrthosLoader


class TestVMInitialization:
    """Test VM initialization and setup."""

    def test_vm_creation(self):
        """Test VM can be created."""
        vm = OrthosVM()
        assert vm is not None
        assert vm.state == VMState.IDLE

    def test_vm_state_initialization(self):
        """Test VM starts in IDLE state."""
        vm = OrthosVM()
        assert vm.state == VMState.IDLE
        assert vm.pc == 0

    def test_register_count(self):
        """Test VM has 256 registers."""
        vm = OrthosVM()
        assert len(vm.registers) == 256

    def test_register_initialization(self):
        """Test all registers initialized to zero."""
        vm = OrthosVM()
        for i in range(256):
            assert vm.registers[i].value == 0
            assert vm.registers[i].type == Register.Type.EMPTY

    def test_program_counter_initialization(self):
        """Test program counter starts at zero."""
        vm = OrthosVM()
        assert vm.pc == 0

    def test_stack_initialization(self):
        """Test stack is empty initially."""
        vm = OrthosVM()
        assert len(vm.stack) == 0

    def test_memory_initialization(self):
        """Test memory is empty initially."""
        vm = OrthosVM()
        assert len(vm.memory) == 0


class TestRegisterOperations:
    """Test register operations."""

    def test_register_set_value(self):
        """Test setting register value."""
        vm = OrthosVM()
        vm.registers[0].value = 42
        assert vm.registers[0].value == 42

    def test_register_type_change(self):
        """Test changing register type."""
        vm = OrthosVM()
        vm.registers[0].type = Register.Type.INTEGER
        assert vm.registers[0].type == Register.Type.INTEGER

    def test_register_load_from_memory(self):
        """Test loading value from memory to register."""
        vm = OrthosVM()
        vm.memory.append(100)
        vm.registers[0].load_from_memory(vm, 0)
        assert vm.registers[0].value == 100

    def test_register_store_to_memory(self):
        """Test storing value from register to memory."""
        vm = OrthosVM()
        vm.registers[0].value = 200
        vm.registers[0].store_to_memory(vm, 0)
        assert vm.memory[0] == 200

    def test_register_arithmetic(self):
        """Test register arithmetic operations."""
        vm = OrthosVM()
        vm.registers[0].value = 10
        vm.registers[1].value = 5
        result = vm.registers[0].add(vm.registers[1])
        assert result.value == 15

    def test_register_comparison(self):
        """Test register comparison operations."""
        vm = OrthosVM()
        vm.registers[0].value = 10
        vm.registers[1].value = 5
        result = vm.registers[0].compare(vm.registers[1], Register.Operation.GT)
        assert result == 1  # Greater than

        vm.registers[1].value = 10
        result = vm.registers[0].compare(vm.registers[1], Register.Operation.EQ)
        assert result == 1  # Equal

        vm.registers[1].value = 15
        result = vm.registers[0].compare(vm.registers[1], Register.Operation.LT)
        assert result == 1  # Less than


class TestInstructionDispatch:
    """Test instruction dispatch and execution."""

    def test_halt_instruction(self):
        """Test HALT instruction."""
        vm = OrthosVM()
        instruction = Instruction(
            opcode=Instruction.Opcodes.HALT,
            operands=[],
            line_number=0
        )
        vm.dispatch(instruction)
        assert vm.state == VMState.HALTED

    def test_mov_instruction(self):
        """Test MOV instruction."""
        vm = OrthosVM()
        instruction = Instruction(
            opcode=Instruction.Opcodes.MOV,
            operands=[0, 1],  # dest, src
            line_number=0
        )
        vm.registers[1].value = 42
        vm.dispatch(instruction)
        assert vm.registers[0].value == 42

    def test_load_const_instruction(self):
        """Test LOAD_CONST instruction."""
        vm = OrthosVM()
        instruction = Instruction(
            opcode=Instruction.Opcodes.LOAD_CONST,
            operands=[100],  # constant value
            line_number=0
        )
        vm.dispatch(instruction)
        assert vm.registers[0].value == 100

    def test_jmp_instruction(self):
        """Test JMP instruction."""
        vm = OrthosVM()
        instruction = Instruction(
            opcode=Instruction.Opcodes.JMP,
            operands=[10],  # target address
            line_number=0
        )
        vm.dispatch(instruction)
        assert vm.pc == 10

    def test_jmp_if_zero_instruction(self):
        """Test JMP_IF_ZERO instruction."""
        vm = OrthosVM()
        instruction = Instruction(
            opcode=Instruction.Opcodes.JMP_IF_ZERO,
            operands=[0, 10],  # register, target
            line_number=0
        )
        vm.registers[0].value = 0
        vm.dispatch(instruction)
        assert vm.pc == 10

        vm.registers[0].value = 1
        vm.pc = 0
        vm.dispatch(instruction)
        assert vm.pc != 10  # Should not jump

    def test_bound_check_instruction(self):
        """Test BOUND_CHECK instruction."""
        vm = OrthosVM()
        instruction = Instruction(
            opcode=Instruction.Opcodes.BOUND_CHECK,
            operands=[0, 5, 10],  # register, min, max
            line_number=0
        )
        vm.registers[0].value = 7
        vm.dispatch(instruction)
        assert vm.registers[0].value == 7  # In bounds

        vm.registers[0].value = 15
        vm.dispatch(instruction)
        assert vm.registers[0].value == 10  # Clamped to max


class TestMemoryOperations:
    """Test memory operations."""

    def test_memory_append(self):
        """Test appending to memory."""
        vm = OrthosVM()
        vm.memory.append(100)
        assert len(vm.memory) == 1
        assert vm.memory[0] == 100

    def test_memory_read(self):
        """Test reading from memory."""
        vm = OrthosVM()
        vm.memory.append(200)
        value = vm.memory.read(0)
        assert value == 200

    def test_memory_write(self):
        """Test writing to memory."""
        vm = OrthosVM()
        vm.memory.append(0)
        vm.memory.write(0, 300)
        assert vm.memory[0] == 300

    def test_memory_bounds_check(self):
        """Test memory bounds checking."""
        vm = OrthosVM()
        vm.memory.append(100)
        with pytest.raises(IndexError):
            vm.memory.read(10)

    def test_memory_resize(self):
        """Test memory resizing."""
        vm = OrthosVM()
        vm.memory.append(100)
        vm.memory.resize(10)
        assert len(vm.memory) == 10


class TestControlFlow:
    """Test control flow operations."""

    def test_loop_execution(self):
        """Test simple loop execution."""
        vm = OrthosVM()
        
        # Simple loop: load 5, subtract 1, check if zero, repeat
        instructions = [
            Instruction(Instruction.Opcodes.LOAD_CONST, [5], 0),
            Instruction(Instruction.Opcodes.MOV, [0, 0], 1),
            Instruction(Instruction.Opcodes.LOAD_CONST, [1], 2),
            Instruction(Instruction.Opcodes.SUB, [0, 0], 3),
            Instruction(Instruction.Opcodes.JMP_IF_ZERO, [0, 4], 4),
            Instruction(Instruction.Opcodes.LOAD_CONST, [0], 5),
            Instruction(Instruction.Opcodes.JMP, [1], 6),
        ]
        
        vm.program = instructions
        vm.run()
        
        assert vm.registers[0].value == 0

    def test_branch_execution(self):
        """Test conditional branch execution."""
        vm = OrthosVM()
        
        instructions = [
            Instruction(Instruction.Opcodes.LOAD_CONST, [10], 0),
            Instruction(Instruction.Opcodes.LOAD_CONST, [5], 1),
            Instruction(Instruction.Opcodes.SUB, [0, 0], 2),
            Instruction(Instruction.Opcodes.JMP_IF_ZERO, [0, 3], 3),
            Instruction(Instruction.Opcodes.LOAD_CONST, [1], 4),
            Instruction(Instruction.Opcodes.JMP, [5], 5),
            Instruction(Instruction.Opcodes.LOAD_CONST, [0], 6),
        ]
        
        vm.program = instructions
        vm.run()
        
        assert vm.registers[0].value == 1  # Branch taken


class TestErrorHandling:
    """Test error handling in VM."""

    def test_invalid_opcode(self):
        """Test handling of invalid opcode."""
        vm = OrthosVM()
        instruction = Instruction(
            opcode=999,  # Invalid opcode
            operands=[],
            line_number=0
        )
        
        with pytest.raises(ValueError):
            vm.dispatch(instruction)

    def test_invalid_operand_count(self):
        """Test handling of invalid operand count."""
        vm = OrthosVM()
        instruction = Instruction(
            opcode=Instruction.Opcodes.MOV,
            operands=[0],  # Missing operand
            line_number=0
        )
        
        with pytest.raises(ValueError):
            vm.dispatch(instruction)

    def test_register_out_of_bounds(self):
        """Test handling of out-of-bounds register access."""
        vm = OrthosVM()
        instruction = Instruction(
            opcode=Instruction.Opcodes.LOAD_CONST,
            operands=[300],  # Invalid register
            line_number=0
        )
        
        with pytest.raises(IndexError):
            vm.dispatch(instruction)

    def test_memory_access_violation(self):
        """Test handling of memory access violations."""
        vm = OrthosVM()
        vm.memory.append(100)
        
        instruction = Instruction(
            opcode=Instruction.Opcodes.MOV,
            operands=[0, 100],  # Out of bounds
            line_number=0
        )
        
        with pytest.raises(IndexError):
            vm.dispatch(instruction)


class TestVMExecution:
    """Test complete VM execution scenarios."""

    def test_empty_program(self):
        """Test execution of empty program."""
        vm = OrthosVM()
        vm.run()
        assert vm.state == VMState.HALTED

    def test_single_instruction(self):
        """Test execution of single instruction."""
        vm = OrthosVM()
        instruction = Instruction(
            opcode=Instruction.Opcodes.LOAD_CONST,
            operands=[42],
            line_number=0
        )
        vm.program = [instruction]
        vm.run()
        assert vm.registers[0].value == 42

    def test_multiple_instructions(self):
        """Test execution of multiple instructions."""
        vm = OrthosVM()
        
        instructions = [
            Instruction(Instruction.Opcodes.LOAD_CONST, [10], 0),
            Instruction(Instruction.Opcodes.LOAD_CONST, [5], 1),
            Instruction(Instruction.Opcodes.ADD, [0, 0], 2),
            Instruction(Instruction.Opcodes.LOAD_CONST, [2], 3),
            Instruction(Instruction.Opcodes.MUL, [0, 0], 4),
        ]
        
        vm.program = instructions
        vm.run()
        
        assert vm.registers[0].value == 100  # (10 + 5) * 2

    def test_program_with_memory(self):
        """Test program using memory."""
        vm = OrthosVM()
        
        instructions = [
            Instruction(Instruction.Opcodes.LOAD_CONST, [100], 0),
            Instruction(Instruction.Opcodes.MOV, [0, 0], 1),
            Instruction(Instruction.Opcodes.LOAD_CONST, [50], 2),
            Instruction(Instruction.Opcodes.MOV, [1, 0], 3),
            Instruction(Instruction.Opcodes.LOAD_CONST, [2], 4),
            Instruction(Instruction.Opcodes.MUL, [1, 1], 5),
            Instruction(Instruction.Opcodes.MOV, [0, 1], 6),
        ]
        
        vm.program = instructions
        vm.run()
        
        assert vm.registers[0].value == 100
        assert vm.registers[1].value == 50


class TestOrthosLoader:
    """Test .oxb file loader."""

    def test_loader_creation(self):
        """Test loader can be created."""
        loader = OrthosLoader()
        assert loader is not None

    def test_load_nonexistent_file(self):
        """Test loading nonexistent file raises error."""
        loader = OrthosLoader()
        with pytest.raises(FileNotFoundError):
            loader.load("nonexistent.oxb")

    def test_load_valid_oxb_file(self, tmp_path):
        """Test loading valid .oxb file."""
        import struct
        
        # Create a minimal valid .oxb file
        filepath = tmp_path / "test.oxb"
        
        # Write header
        header = struct.pack(">IIB", 0x54505853, 1, 0)  # Magic, version, checksum
        
        # Write bytecode
        bytecode = bytes([
            Instruction.Opcodes.LOAD_CONST,  # opcode
            42,  # operand
        ])
        
        # Write CRC32
        import zlib
        data = header + bytecode
        checksum = zlib.crc32(data) & 0xFFFFFFFF
        
        with open(filepath, "wb") as f:
            f.write(data)
            f.write(struct.pack(">I", checksum))
        
        # Load file
        loader = OrthosLoader()
        program = loader.load(str(filepath))
        
        assert program is not None
        assert len(program) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
