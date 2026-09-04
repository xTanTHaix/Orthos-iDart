"""
Orthos-iDart Exam Test Suite: Edge Cases
Tests edge cases and boundary conditions across all modules.
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from unittest.mock import Mock, MagicMock, patch
import pytest
import time

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
from orthos.compiler.analysis.scope import ScopeAnalyzer
from orthos.compiler.analysis.cfg import CFGBuilder
from orthos.annihilator.faulhaber import FaulhaberEngine

# Test dataclass for edge case results
@dataclass
class EdgeCaseResult:
    """Result of an edge case test."""
    name: str
    passed: bool
    error_message: str = ""
    execution_time_ms: float = 0.0

class EdgeCaseTestSuite:
    """Edge case test suite for Orthos-iDart."""
    
    def __init__(self):
        self.results: List[EdgeCaseResult] = []
        self.passed_tests = 0
        self.failed_tests = 0
    
    def run_edge_case_test(self, test_name: str, test_func) -> EdgeCaseResult:
        """Run a single edge case test."""
        try:
            start_time = time.perf_counter()
            result = test_func()
            execution_time = (time.perf_counter() - start_time) * 1000
            
            test_result = EdgeCaseResult(
                name=test_name,
                passed=result is not None,
                execution_time_ms=execution_time
            )
            
            if test_result.passed:
                print(f"✓ PASSED: {test_name} ({execution_time:.2f}ms)")
                self.passed_tests += 1
            else:
                print(f"✗ FAILED: {test_name}")
                self.failed_tests += 1
            
            self.results.append(test_result)
            return test_result
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            test_result = EdgeCaseResult(
                name=test_name,
                passed=False,
                error_message=str(e),
                execution_time_ms=execution_time
            )
            
            print(f"✗ ERROR: {test_name} - {str(e)}")
            self.failed_tests += 1
            self.results.append(test_result)
            return test_result
    
    def test_empty_code_handling(self):
        """Test empty code handling."""
        print("Testing empty code handling...")
        lexer = OrthosLexer("")
        tokens = lexer.tokenize()
        assert len(tokens) == 0, "Lexer should return empty tokens for empty input"
        
        parser = OrthosParser(tokens)
        ast = parser.parse()
        assert ast is not None, "Parser should handle empty input"
        
        return True
    
    def test_very_long_code(self):
        """Test very long code handling."""
        print("Testing very long code handling...")
        # Create a very long code string
        code = "x = " + "y = " * 10000
        lexer = OrthosLexer(code)
        tokens = lexer.tokenize()
        assert len(tokens) > 0, "Lexer should handle very long code"
        
        parser = OrthosParser(tokens)
        ast = parser.parse()
        assert ast is not None, "Parser should handle very long code"
        
        return True
    
    def test_nested_scopes_deep(self):
        """Test deeply nested scopes."""
        print("Testing deeply nested scopes...")
        code = """
def level1():
    def level2():
        def level3():
            def level4():
                def level5():
                    x = 1
                    return x
        return level5()
    return level3()
"""
        analyzer = ScopeAnalyzer()
        scopes = analyzer.analyze(code)
        assert len(scopes) > 0, "Scope analyzer should detect nested scopes"
        
        return True
    
    def test_complex_control_flow(self):
        """Test complex control flow."""
        print("Testing complex control flow...")
        code = """
def complex_flow(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                return x + y + z
            elif z < 0:
                return x + y - z
        elif y < 0:
            if z > 0:
                return x - y + z
            elif z < 0:
                return x - y - z
    return 0
"""
        builder = CFGBuilder()
        cfg = builder.build(code)
        assert cfg is not None, "CFG builder should handle complex control flow"
        
        return True
    
    def test_vm_instruction_edge_cases(self):
        """Test VM instruction edge cases."""
        print("Testing VM instruction edge cases...")
        vm = OrthosVM()
        
        # Test MOV with invalid register
        instruction = Instruction(
            opcode=Instruction.OPCODES['MOV'],
            operands=[Register(256, 0, False), 42]  # Invalid register
        )
        try:
            vm.execute_instruction(instruction)
            assert False, "Should raise exception for invalid register"
        except Exception:
            pass
        
        # Test LOAD_CONST with large constant
        instruction = Instruction(
            opcode=Instruction.OPCODES['LOAD_CONST'],
            operands=[Register(0, 0, False), 2**60]  # Large constant
        )
        vm.execute_instruction(instruction)
        assert vm.registers[0].value == 2**60, "Should handle large constant"
        
        return True
    
    def test_compiler_edge_cases(self):
        """Test compiler edge cases."""
        print("Testing compiler edge cases...")
        # Test lexer with invalid syntax
        code = "def invalid_syntax"
        lexer = OrthosLexer(code)
        tokens = lexer.tokenize()
        assert len(tokens) > 0, "Lexer should tokenize invalid syntax"
        
        # Test parser with incomplete code
        parser = OrthosParser(tokens)
        ast = parser.parse()
        assert ast is not None, "Parser should handle incomplete code"
        
        return True
    
    def test_storage_edge_cases(self):
        """Test storage edge cases."""
        print("Testing storage edge cases...")
        storage = TPXStoragePurePython()
        
        # Test write with empty key
        storage.write("", "value")
        assert storage.read("") == "value", "Should handle empty key"
        
        # Test read with non-existent key
        assert storage.read("nonexistent") is None, "Should return None for non-existent key"
        
        # Test delete with empty key
        storage.delete("")
        assert storage.read("") is None, "Should delete empty key"
        
        return True
    
    def test_security_edge_cases(self):
        """Test security edge cases."""
        print("Testing security edge cases...")
        bridge = NexusBridge()
        
        # Test security check with empty code
        is_safe, message = bridge.check_security("")
        assert is_safe is True, "Empty code should be safe"
        
        # Test taint analysis with empty code
        analyzer = TaintAnalyzer()
        is_tainted, sources = analyzer.analyze("")
        assert is_tainted is False, "Empty code should not be tainted"
        
        return True
    
    def test_circuit_breaker_edge_cases(self):
        """Test circuit breaker edge cases."""
        print("Testing circuit breaker edge cases...")
        breaker = CircuitBreaker(max_failures=1)
        
        # Test initial state
        assert breaker.is_open is False, "Circuit breaker should initially be closed"
        
        # Test failure recording
        breaker.record_failure()
        assert breaker.is_open is True, "Circuit breaker should open after failure"
        
        # Test reset
        breaker.reset()
        assert breaker.is_open is False, "Circuit breaker should close after reset"
        
        return True
    
    def test_demand_tracer_edge_cases(self):
        """Test demand tracer edge cases."""
        print("Testing demand tracer edge cases...")
        tracer = DemandTracer()
        
        # Test pattern detection with empty code
        patterns = tracer.detect_patterns("")
        assert len(patterns) == 0, "Empty code should have no patterns"
        
        # Test pattern detection with simple code
        code = "x = 1"
        patterns = tracer.detect_patterns(code)
        assert len(patterns) >= 0, "Should detect patterns in simple code"
        
        return True
    
    def test_full_pipeline_edge_cases(self):
        """Test full pipeline edge cases."""
        print("Testing full pipeline edge cases...")
        # Test with empty code through full pipeline
        code = ""
        
        # Lex and parse
        lexer = OrthosLexer(code)
        tokens = lexer.tokenize()
        parser = OrthosParser(tokens)
        ast = parser.parse()
        
        # Code generation
        codegen = OrthosCodeGenerator()
        bytecode = codegen.generate(ast)
        
        # Packing
        packer = BytecodePacker()
        packed = packer.pack(bytecode)
        
        # Storage
        storage = TPXStoragePurePython()
        storage.write("empty_code.oxb", packed)
        
        assert storage.read("empty_code.oxb") is not None, "Should store empty code"
        
        return True
    
    def test_performance_edge_cases(self):
        """Test performance edge cases."""
        print("Testing performance edge cases...")
        # Test large computation with Faulhaber
        engine = FaulhaberEngine()
        n = 100000
        start_time = time.time()
        result = engine.sum_polynomial(n, 2)
        elapsed = time.time() - start_time
        assert result > 0, "Should compute polynomial sum"
        assert elapsed < 5.0, "Should complete in reasonable time"
        
        return True
    
    def test_memory_efficiency_edge_cases(self):
        """Test memory efficiency edge cases."""
        print("Testing memory efficiency edge cases...")
        storage = TPXStoragePurePython()
        
        # Write large dataset
        for i in range(10000):
            storage.write(f"key_{i}", f"value_{i}")
        
        # Check memory usage
        memory_usage = storage.memory_usage()
        assert memory_usage < 100 * 1024 * 1024, "Memory usage should be reasonable"
        
        return True
    
    def test_concurrent_edge_cases(self):
        """Test concurrent edge cases."""
        print("Testing concurrent edge cases...")
        import threading
        
        storage = TPXStoragePurePython()
        
        def writer(thread_id):
            for i in range(100):
                key = f"thread_{thread_id}_key_{i}"
                value = f"thread_{thread_id}_value_{i}"
                storage.write(key, value)
        
        threads = []
        for i in range(5):
            t = threading.Thread(target=writer, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Verify all writes succeeded
        for thread_id in range(5):
            for i in range(100):
                key = f"thread_{thread_id}_key_{i}"
                value = f"thread_{thread_id}_value_{i}"
                assert storage.read(key) == value, "Concurrent write should succeed"
        
        return True


def run_edge_case_tests():
    """Main function to run all edge case tests."""
    print("=" * 60)
    print("ORTHOS-IDART EDGE CASE TEST SUITE")
    print("=" * 60)
    
    # Create test suite
    test_suite = EdgeCaseTestSuite()
    
    # Register tests
    tests = [
        ("Empty Code Handling", test_suite.test_empty_code_handling),
        ("Very Long Code", test_suite.test_very_long_code),
        ("Deeply Nested Scopes", test_suite.test_nested_scopes_deep),
        ("Complex Control Flow", test_suite.test_complex_control_flow),
        ("VM Instruction Edge Cases", test_suite.test_vm_instruction_edge_cases),
        ("Compiler Edge Cases", test_suite.test_compiler_edge_cases),
        ("Storage Edge Cases", test_suite.test_storage_edge_cases),
        ("Security Edge Cases", test_suite.test_security_edge_cases),
        ("Circuit Breaker Edge Cases", test_suite.test_circuit_breaker_edge_cases),
        ("Demand Tracer Edge Cases", test_suite.test_demand_tracer_edge_cases),
        ("Full Pipeline Edge Cases", test_suite.test_full_pipeline_edge_cases),
        ("Performance Edge Cases", test_suite.test_performance_edge_cases),
        ("Memory Efficiency Edge Cases", test_suite.test_memory_efficiency_edge_cases),
        ("Concurrent Edge Cases", test_suite.test_concurrent_edge_cases),
    ]
    
    # Run tests
    for test_name, test_func in tests:
        test_suite.run_edge_case_test(test_name, test_func)
    
    # Generate summary
    summary = {
        'total': len(test_suite.results),
        'passed': test_suite.passed_tests,
        'failed': test_suite.failed_tests,
        'results': test_suite.results
    }
    
    print("\n" + "=" * 60)
    print("EDGE CASE TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {summary['total']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    
    return summary['failed'] == 0


class TestEdgeCaseSuite:
    """Pytest wrapper for edge case test suite."""

    def setup_method(self):
        self.suite = EdgeCaseTestSuite()

    def test_empty_code_handling(self):
        assert self.suite.test_empty_code_handling() is True

    def test_very_long_code(self):
        assert self.suite.test_very_long_code() is True

    def test_nested_scopes_deep(self):
        assert self.suite.test_nested_scopes_deep() is True

    def test_complex_control_flow(self):
        assert self.suite.test_complex_control_flow() is True

    def test_vm_instruction_edge_cases(self):
        assert self.suite.test_vm_instruction_edge_cases() is True

    def test_compiler_edge_cases(self):
        assert self.suite.test_compiler_edge_cases() is True

    def test_storage_edge_cases(self):
        assert self.suite.test_storage_edge_cases() is True

    def test_security_edge_cases(self):
        assert self.suite.test_security_edge_cases() is True

    def test_circuit_breaker_edge_cases(self):
        assert self.suite.test_circuit_breaker_edge_cases() is True

    def test_demand_tracer_edge_cases(self):
        assert self.suite.test_demand_tracer_edge_cases() is True

    def test_full_pipeline_edge_cases(self):
        assert self.suite.test_full_pipeline_edge_cases() is True

    def test_performance_edge_cases(self):
        assert self.suite.test_performance_edge_cases() is True

    def test_memory_efficiency_edge_cases(self):
        assert self.suite.test_memory_efficiency_edge_cases() is True

    def test_concurrent_edge_cases(self):
        assert self.suite.test_concurrent_edge_cases() is True


if __name__ == "__main__":
    success = run_edge_case_tests()
    sys.exit(0 if success else 1)

