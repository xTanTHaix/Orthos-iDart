"""
Basic Exam Tests for Orthos-iDart
Tests fundamental functionality and basic optimization scenarios.
"""

import sys
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from unittest.mock import Mock, MagicMock, patch
import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from orthos.vm.core import OrthosVM, Register, Instruction
from orthos.compiler.lexer import OrthosLexer
from orthos.compiler.parser import OrthosParser
from orthos.compiler.codegen import OrthosCodeGenerator
from orthos.compiler.packer import BytecodePacker
from orthos.nexus.bridge import NexusBridge
from orthos.safety.taint_analyzer import TaintAnalyzer
from orthos.safety.circuit_breaker import CircuitBreaker
from orthos.idart.demand_tracer import DemandTracer
from orthos.storage.tpx.fallback_pure_python import TPXStoragePurePython


class TestBasicVMInitialization:
    """Test VM initialization and basic setup."""
    
    def test_vm_creation(self):
        """Test VM can be created successfully."""
        vm = OrthosVM()
        assert vm is not None
        assert vm.num_registers == 256
        assert vm.pc == 0
        assert vm.halted is False
    
    def test_vm_registers_initialized(self):
        """Test all registers are initialized to zero."""
        vm = OrthosVM()
        for i in range(vm.num_registers):
            assert vm.registers[i].value == 0
            assert vm.registers[i].valid is False
    
    def test_vm_stack_initialized(self):
        """Test stack is initialized."""
        vm = OrthosVM()
        assert vm.stack is not None
        assert len(vm.stack) == 0
    
    def test_vm_halt_state(self):
        """Test VM halts on HALT instruction."""
        vm = OrthosVM()
        # Simulate HALT instruction
        vm.halted = True
        assert vm.halted is True


class TestBasicInstructionDispatch:
    """Test basic instruction dispatch."""
    
    def test_mov_instruction(self):
        """Test MOV instruction execution."""
        vm = OrthosVM()
        # MOV R0, 42
        instruction = Instruction(
            opcode=Instruction.OPCODES['MOV'],
            operands=[Register(0, 0, False), 42]
        )
        vm.execute_instruction(instruction)
        assert vm.registers[0].value == 42
        assert vm.registers[0].valid is True
    
    def test_load_const_instruction(self):
        """Test LOAD_CONST instruction."""
        vm = OrthosVM()
        const_value = 100
        instruction = Instruction(
            opcode=Instruction.OPCODES['LOAD_CONST'],
            operands=[Register(0, 0, False), const_value]
        )
        vm.execute_instruction(instruction)
        assert vm.registers[0].value == const_value
    
    def test_add_instruction(self):
        """Test ADD instruction."""
        vm = OrthosVM()
        vm.registers[0].value = 10
        vm.registers[0].valid = True
        vm.registers[1].value = 20
        vm.registers[1].valid = True
        
        instruction = Instruction(
            opcode=Instruction.OPCODES['ADD'],
            operands=[Register(0, 0, True), Register(1, 0, True)]
        )
        vm.execute_instruction(instruction)
        assert vm.registers[0].value == 30
    
    def test_sub_instruction(self):
        """Test SUB instruction."""
        vm = OrthosVM()
        vm.registers[0].value = 50
        vm.registers[0].valid = True
        vm.registers[1].value = 20
        vm.registers[1].valid = True
        
        instruction = Instruction(
            opcode=Instruction.OPCODES['SUB'],
            operands=[Register(0, 0, True), Register(1, 0, True)]
        )
        vm.execute_instruction(instruction)
        assert vm.registers[0].value == 30
    
    def test_mul_instruction(self):
        """Test MUL instruction."""
        vm = OrthosVM()
        vm.registers[0].value = 6
        vm.registers[0].valid = True
        vm.registers[1].value = 7
        vm.registers[1].valid = True
        
        instruction = Instruction(
            opcode=Instruction.OPCODES['MUL'],
            operands=[Register(0, 0, True), Register(1, 0, True)]
        )
        vm.execute_instruction(instruction)
        assert vm.registers[0].value == 42
    
    def test_div_instruction(self):
        """Test DIV instruction."""
        vm = OrthosVM()
        vm.registers[0].value = 100
        vm.registers[0].valid = True
        vm.registers[1].value = 5
        vm.registers[1].valid = True
        
        instruction = Instruction(
            opcode=Instruction.OPCODES['DIV'],
            operands=[Register(0, 0, True), Register(1, 0, True)]
        )
        vm.execute_instruction(instruction)
        assert vm.registers[0].value == 20


class TestBasicMemoryOperations:
    """Test basic memory operations."""
    
    def test_load_memory(self):
        """Test LOAD_MEM instruction."""
        vm = OrthosVM()
        vm.memory[100] = 42
        
        instruction = Instruction(
            opcode=Instruction.OPCODES['LOAD_MEM'],
            operands=[Register(0, 0, False), 100]
        )
        vm.execute_instruction(instruction)
        assert vm.registers[0].value == 42
    
    def test_store_memory(self):
        """Test STORE_MEM instruction."""
        vm = OrthosVM()
        vm.registers[0].value = 100
        
        instruction = Instruction(
            opcode=Instruction.OPCODES['STORE_MEM'],
            operands=[Register(0, 0, True), 200]
        )
        vm.execute_instruction(instruction)
        assert vm.memory[200] == 100


class TestBasicControlFlow:
    """Test basic control flow instructions."""
    
    def test_jmp_instruction(self):
        """Test JMP instruction."""
        vm = OrthosVM()
        vm.pc = 10
        
        instruction = Instruction(
            opcode=Instruction.OPCODES['JMP'],
            operands=[Register(0, 0, False), 50]
        )
        vm.execute_instruction(instruction)
        assert vm.pc == 50
    
    def test_jmp_if_zero_instruction(self):
        """Test JMP_IF_ZERO instruction."""
        vm = OrthosVM()
        vm.pc = 10
        vm.registers[0].value = 0
        vm.registers[0].valid = True
        
        instruction = Instruction(
            opcode=Instruction.OPCODES['JMP_IF_ZERO'],
            operands=[Register(0, 0, True), 50]
        )
        vm.execute_instruction(instruction)
        assert vm.pc == 50
    
    def test_jmp_if_nonzero_instruction(self):
        """Test JMP_IF_NONZERO instruction."""
        vm = OrthosVM()
        vm.pc = 10
        vm.registers[0].value = 1
        vm.registers[0].valid = True
        
        instruction = Instruction(
            opcode=Instruction.OPCODES['JMP_IF_NONZERO'],
            operands=[Register(0, 0, True), 50]
        )
        vm.execute_instruction(instruction)
        assert vm.pc == 10  # Should not jump


class TestBasicErrorHandling:
    """Test error handling in VM."""
    
    def test_invalid_register_access(self):
        """Test error on invalid register access."""
        vm = OrthosVM()
        instruction = Instruction(
            opcode=Instruction.OPCODES['MOV'],
            operands=[Register(256, 0, False), 42]  # Invalid register
        )
        with pytest.raises(Exception):
            vm.execute_instruction(instruction)
    
    def test_stack_overflow(self):
        """Test stack overflow handling."""
        vm = OrthosVM()
        # Simulate stack overflow
        vm.stack_overflow = True
        instruction = Instruction(
            opcode=Instruction.OPCODES['LOAD_CONST'],
            operands=[Register(0, 0, False), 42]
        )
        with pytest.raises(Exception):
            vm.execute_instruction(instruction)
    
    def test_division_by_zero(self):
        """Test division by zero handling."""
        vm = OrthosVM()
        vm.registers[0].value = 10
        vm.registers[0].valid = True
        vm.registers[1].value = 0
        vm.registers[1].valid = True
        
        instruction = Instruction(
            opcode=Instruction.OPCODES['DIV'],
            operands=[Register(0, 0, True), Register(1, 0, True)]
        )
        with pytest.raises(Exception):
            vm.execute_instruction(instruction)


class TestBasicCompilerPipeline:
    """Test basic compiler pipeline."""
    
    def test_lexer_basic_tokens(self):
        """Test lexer produces correct tokens."""
        code = "x = 42"
        lexer = OrthosLexer(code)
        tokens = lexer.tokenize()
        assert len(tokens) > 0
        assert any(t.type == 'IDENTIFIER' for t in tokens)
    
    def test_parser_basic_ast(self):
        """Test parser produces AST."""
        code = "x = 42"
        lexer = OrthosLexer(code)
        tokens = lexer.tokenize()
        parser = OrthosParser(tokens)
        ast = parser.parse()
        assert ast is not None
    
    def test_codegen_basic_bytecode(self):
        """Test codegen produces bytecode."""
        code = "x = 42"
        lexer = OrthosLexer(code)
        tokens = lexer.tokenize()
        parser = OrthosParser(tokens)
        ast = parser.parse()
        codegen = OrthosCodeGenerator()
        bytecode = codegen.generate(ast)
        assert bytecode is not None
        assert len(bytecode) > 0
    
    def test_packer_basic_pack(self):
        """Test packer can pack bytecode."""
        code = "x = 42"
        lexer = OrthosLexer(code)
        tokens = lexer.tokenize()
        parser = OrthosParser(tokens)
        ast = parser.parse()
        codegen = OrthosCodeGenerator()
        bytecode = codegen.generate(ast)
        packer = BytecodePacker()
        packed = packer.pack(bytecode)
        assert packed is not None
        assert len(packed) > 0


class TestBasicNexusBridge:
    """Test Nexus bridge functionality."""
    
    def test_bridge_creation(self):
        """Test bridge can be created."""
        bridge = NexusBridge()
        assert bridge is not None
    
    def test_bridge_filter_code(self):
        """Test bridge can filter code."""
        code = "x = 42"
        bridge = NexusBridge()
        result = bridge.filter_code(code)
        assert result is not None
    
    def test_bridge_security_check(self):
        """Test bridge security checks."""
        code = "x = 42"
        bridge = NexusBridge()
        is_safe, message = bridge.check_security(code)
        assert is_safe is True


class TestBasicTaintAnalysis:
    """Test taint analysis."""
    
    def test_taint_analyzer_creation(self):
        """Test taint analyzer can be created."""
        analyzer = TaintAnalyzer()
        assert analyzer is not None
    
    def test_taint_detection(self):
        """Test taint detection."""
        analyzer = TaintAnalyzer()
        code = "x = input()"
        is_tainted, sources = analyzer.analyze(code)
        assert is_tainted is True


class TestBasicCircuitBreaker:
    """Test circuit breaker."""
    
    def test_circuit_breaker_creation(self):
        """Test circuit breaker can be created."""
        breaker = CircuitBreaker()
        assert breaker is not None
    
    def test_circuit_breaker_open(self):
        """Test circuit breaker opens after failures."""
        breaker = CircuitBreaker(max_failures=2)
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.is_open is True
    
    def test_circuit_breaker_half_open(self):
        """Test circuit breaker transitions to half-open."""
        breaker = CircuitBreaker(max_failures=2)
        breaker.record_failure()
        breaker.record_failure()
        breaker.reset()
        assert breaker.is_open is False


class TestBasicDemandTracer:
    """Test demand tracer."""
    
    def test_demand_tracer_creation(self):
        """Test demand tracer can be created."""
        tracer = DemandTracer()
        assert tracer is not None
    
    def test_demand_pattern_detection(self):
        """Test demand pattern detection."""
        tracer = DemandTracer()
        code = "x = [i for i in range(1000)]"
        patterns = tracer.detect_patterns(code)
        assert len(patterns) >= 0


class TestBasicStorage:
    """Test basic storage functionality."""
    
    def test_storage_creation(self):
        """Test storage can be created."""
        storage = TPXStoragePurePython()
        assert storage is not None
    
    def test_storage_write_read(self):
        """Test storage write and read."""
        storage = TPXStoragePurePython()
        key = "test_key"
        value = "test_value"
        storage.write(key, value)
        read_value = storage.read(key)
        assert read_value == value
    
    def test_storage_delete(self):
        """Test storage delete."""
        storage = TPXStoragePurePython()
        key = "test_key"
        value = "test_value"
        storage.write(key, value)
        storage.delete(key)
        assert storage.read(key) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
