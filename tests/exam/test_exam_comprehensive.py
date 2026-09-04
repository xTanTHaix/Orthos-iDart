"""
Orthos-iDart Exam Test Suite: Comprehensive Tests
Tests comprehensive integration across all modules and components.
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
import time
import logging
import threading
import queue

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orthos.vm.core import OrthosVM, Register, Instruction
from orthos.compiler.lexer import OrthosLexer
from orthos.compiler.parser import OrthosParser
from orthos.compiler.codegen import OrthosCodeGenerator
from orthos.compiler.packer import BytecodePacker, CompiledModule
from orthos.nexus.bridge import NexusBridge
from orthos.compiler.analysis.scope import ScopeAnalyzer
from orthos.compiler.analysis.cfg import CFGBuilder
from orthos.compiler.analysis.complexity_gate import ComplexityAnalyzer
from orthos.compiler.analysis.verification_cache import VerificationCache
from orthos.idart.demand_tracer import DemandTracer
from orthos.idart.cutter import IDartCutter, CutStrategy
from orthos.idart.express_tunnel import ExpressTunnel, ExpressTunnelManager, TunnelType, OptimizationOp
from orthos.annihilator.faulhaber import FaulhaberEngine
from orthos.annihilator.companion_matrix import CompanionMatrixEngine
from orthos.annihilator.dp_collapser import DPCollapser
from orthos.annihilator.diophantine import DiophantineSolver
from orthos.annihilator.simplex import SimplexOptimizer
from orthos.annihilator.cost_model import CostModel
from orthos.storage.tpx.fallback_pure_python import TPXStoragePurePython
from orthos.safety.taint_analyzer import TaintAnalyzer
from orthos.safety.circuit_breaker import CircuitBreaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test dataclass for comprehensive test results
@dataclass
class ComprehensiveTestResult:
    """Result of a comprehensive test."""
    name: str
    passed: bool
    error_message: str = ""
    execution_time_ms: float = 0.0
    details: Dict = field(default_factory=dict)

class ComprehensiveTestSuite:
    """Comprehensive test suite for Orthos-iDart."""
    
    def __init__(self):
        self.results: List[ComprehensiveTestResult] = []
        self.passed_tests = 0
        self.failed_tests = 0
        self.modules_initialized = False
        self.storage = None
        self.vm = None
        self.lexer = None
        self.parser = None
        self.codegen = None
        self.packer = None
        self.nexus = None
        self.idart_cutter = None
        self.express_tunnel = None
        self.tunnel_manager = None
        self.faulhaber = None
        self.matrix_engine = None
        self.dp_collapser = None
        self.diophantine_solver = None
        self.simplex_optimizer = None
        self.cost_model = None
        self.taint_analyzer = None
        self.circuit_breaker = None
    
    def initialize_modules(self) -> bool:
        """Initialize all required modules."""
        try:
            logger.info("Initializing modules...")
            
            # Initialize VM
            self.vm = OrthosVM()
            logger.info("  ✓ VM initialized")
            
            # Initialize compiler components
            self.lexer = OrthosLexer()
            self.parser = OrthosParser()
            self.codegen = OrthosCodeGenerator()
            logger.info("  ✓ Compiler components initialized")
            
            # Initialize bytecode packer
            self.packer = BytecodePacker()
            logger.info("  ✓ Bytecode packer initialized")
            
            # Initialize Nexus bridge
            self.nexus = NexusBridge()
            logger.info("  ✓ Nexus bridge initialized")
            
            # Initialize analysis components
            scope_analyzer = ScopeAnalyzer()
            cfg_builder = CFGBuilder()
            complexity_analyzer = ComplexityAnalyzer()
            verification_cache = VerificationCache()
            logger.info("  ✓ Analysis components initialized")
            
            # Initialize iDart components
            self.idart_cutter = IDartCutter()
            self.express_tunnel = ExpressTunnel(
                tunnel_type=TunnelType.MEMORY,
                optimization_op=OptimizationOp.ZERO_COPY
            )
            self.tunnel_manager = ExpressTunnelManager()
            logger.info("  ✓ iDart components initialized")
            
            # Initialize annihilator components
            self.faulhaber = FaulhaberEngine()
            self.matrix_engine = CompanionMatrixEngine()
            self.dp_collapser = DPCollapser()
            self.diophantine_solver = DiophantineSolver()
            self.simplex_optimizer = SimplexOptimizer()
            self.cost_model = CostModel()
            logger.info("  ✓ Annihilator components initialized")
            
            # Initialize safety components
            self.taint_analyzer = TaintAnalyzer()
            self.circuit_breaker = CircuitBreaker()
            logger.info("  ✓ Safety components initialized")
            
            # Initialize storage
            self.storage = TPXStoragePurePython()
            logger.info("  ✓ Storage initialized")
            
            self.modules_initialized = True
            logger.info("✓ All modules initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"✗ Module initialization failed: {str(e)}")
            self.failed_tests += 1
            return False
    
    def run_comprehensive_test(self, test_name: str, test_func) -> ComprehensiveTestResult:
        """Run a single comprehensive test."""
        try:
            start_time = time.perf_counter()
            result = test_func()
            execution_time = (time.perf_counter() - start_time) * 1000
            
            test_result = ComprehensiveTestResult(
                name=test_name,
                passed=result is not None,
                execution_time_ms=execution_time
            )
            
            if test_result.passed:
                logger.info(f"✓ PASSED: {test_name} ({execution_time:.2f}ms)")
                self.passed_tests += 1
            else:
                logger.error(f"✗ FAILED: {test_name}")
                self.failed_tests += 1
            
            self.results.append(test_result)
            return test_result
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            test_result = ComprehensiveTestResult(
                name=test_name,
                passed=False,
                error_message=str(e),
                execution_time_ms=execution_time
            )
            
            logger.error(f"✗ ERROR: {test_name} - {str(e)}")
            self.failed_tests += 1
            self.results.append(test_result)
            return test_result
    
    def test_full_compiler_pipeline(self) -> bool:
        """Test full compiler pipeline."""
        logger.info("Testing full compiler pipeline...")
        
        # Compile simple code
        code = """
x = 10
y = 20
result = x + y
"""
        
        # Lex and parse
        tokens = self.lexer.tokenize(code)
        ast = self.parser.parse(tokens)
        
        # Generate bytecode
        bytecode = self.codegen.generate(ast)
        
        # Pack bytecode
        module = CompiledModule(name="test", version=0x0002)
        packed = self.packer.pack(module, bytecode)
        
        # Execute in VM
        self.vm.execute(packed)
        
        return True
    
    def test_full_optimization_pipeline(self) -> bool:
        """Test full optimization pipeline."""
        logger.info("Testing full optimization pipeline...")
        
        # Step 1: Lex and parse
        code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = fibonacci(10)
"""
        
        tokens = self.lexer.tokenize(code)
        ast = self.parser.parse(tokens)
        
        # Step 2: Generate bytecode
        bytecode = self.codegen.generate(ast)
        
        # Step 3: Pack bytecode
        module = CompiledModule(name="fibonacci", version=0x0002)
        packed = self.packer.pack(module, bytecode)
        
        # Step 4: Analyze with Nexus
        is_safe, analysis = self.nexus.analyze_code(code)
        
        # Step 5: Optimize with iDart
        graph = self._create_optimization_graph()
        cut_result = self.idart_cutter.cut_graph(graph, CutStrategy.HOTSPOT)
        
        # Step 6: Execute in VM
        self.vm.execute(packed)
        
        return True
    
    def _create_optimization_graph(self) -> Dict:
        """Create optimization graph."""
        return {
            'nodes': list(range(20)),
            'edges': [(i, i+1) for i in range(19)] + [(0, 19)],
            'adjacency': {i: [(i-1) % 20, (i+1) % 20] for i in range(20)}
        }
    
    def test_analysis_integration(self) -> bool:
        """Test analysis integration."""
        logger.info("Testing analysis integration...")
        
        code = """
def compute_sum(n):
    total = 0
    for i in range(n):
        total += i
    return total
"""
        
        # Analysis
        scope_analyzer = ScopeAnalyzer()
        scopes = scope_analyzer.analyze(code)
        
        complexity_analyzer = ComplexityAnalyzer()
        complexity = complexity_analyzer.analyze(code)
        
        # Optimization
        tracer = DemandTracer()
        patterns = tracer.detect_patterns(code)
        
        cutter = IDartCutter()
        optimization = cutter.analyze(code)
        
        assert scopes is not None, "Scope analysis should succeed"
        assert complexity is not None, "Complexity analysis should succeed"
        assert patterns is not None, "Pattern detection should succeed"
        assert optimization is not None, "Optimization analysis should succeed"
        
        return True
    
    def test_annihilator_integration(self) -> bool:
        """Test annihilator integration."""
        logger.info("Testing annihilator integration...")
        
        # Test Faulhaber
        result1 = self.faulhaber.compute_polynomial_sum(10, 2)
        
        # Test Matrix exponentiation
        matrix = [[1, 1], [1, 0]]
        result2 = self.matrix_engine.matrix_exponentiation(matrix, 10)
        
        # Test DP collapser
        sequence = [1, 2, 3, 4, 5]
        result3 = self.dp_collapser.optimize_sequence(sequence, 'sum')
        
        # Test Diophantine solver
        result4 = self.diophantine_solver.solve_linear_diophantine(3, 5, 7)
        
        # Test Simplex optimizer
        objective = [3, 2]
        constraints = [[1, 1, 4], [2, 1, 8], [1, 0, 3]]
        result5 = self.simplex_optimizer.optimize(objective, constraints)
        
        # Test Cost model
        result6 = self.cost_model.analyze(1000, 'O(n^2)')
        
        return True
    
    def test_storage_comprehensive(self) -> bool:
        """Test comprehensive storage functionality."""
        logger.info("Testing comprehensive storage...")
        
        # Store various data types
        self.storage.store("string_key", "string_value")
        self.storage.store("int_key", 42)
        self.storage.store("list_key", [1, 2, 3])
        self.storage.store("dict_key", {"a": 1, "b": 2})
        
        # Retrieve data
        value1 = self.storage.get("string_key")
        value2 = self.storage.get("int_key")
        value3 = self.storage.get("list_key")
        value4 = self.storage.get("dict_key")
        
        assert value1 == "string_value", "String storage failed"
        assert value2 == 42, "Integer storage failed"
        assert value3 == [1, 2, 3], "List storage failed"
        assert value4 == {"a": 1, "b": 2}, "Dict storage failed"
        
        # Test batch operations
        self.storage.batch_store({
            "batch_key1": "value1",
            "batch_key2": "value2",
            "batch_key3": "value3"
        })
        
        return True
    
    def test_security_integration(self) -> bool:
        """Test security integration."""
        logger.info("Testing security integration...")
        
        # Test taint analysis
        taint_code = """
def process_input(user_input):
    result = user_input * 2
    return result
"""
        is_tainted, sources = self.taint_analyzer.analyze(taint_code)
        assert is_tainted is True, "Taint analysis should detect tainted code"
        
        # Test circuit breaker
        breaker = CircuitBreaker(max_failures=2)
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.is_open is True, "Circuit breaker should open after failures"
        
        # Test circuit breaker recovery
        breaker.reset()
        assert breaker.is_open is False, "Circuit breaker should close after reset"
        
        return True
    
    def test_concurrent_execution(self) -> bool:
        """Test concurrent execution."""
        logger.info("Testing concurrent execution...")
        
        results = []
        errors = []
        
        def worker(thread_id):
            try:
                # Each worker does different operations
                vm = OrthosVM()
                vm.execute_instruction('HALT')
                
                storage = TPXStoragePurePython()
                storage.store(f"thread_{thread_id}", f"value_{thread_id}")
                
                cost_model = CostModel()
                cost_model.analyze(100, 'O(n)')
                
                results.append(f"thread_{thread_id}_success")
            except Exception as e:
                errors.append(f"thread_{thread_id}: {str(e)}")
        
        # Create and start threads
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join()
        
        # Check results
        if len(errors) > 0:
            logger.error(f"Concurrent execution errors: {errors}")
            return False
        
        return True
    
    def test_performance_benchmark(self) -> bool:
        """Test performance benchmark."""
        logger.info("Testing performance benchmark...")
        
        # Test large-scale computation
        engine = FaulhaberEngine()
        n = 10000
        start_time = time.time()
        result = engine.sum_polynomial(n, 2)
        elapsed = time.time() - start_time
        assert result > 0, "Should compute polynomial sum"
        assert elapsed < 1.0, "Should complete in under 1 second"
        
        return True
    
    def test_memory_efficiency(self) -> bool:
        """Test memory efficiency."""
        logger.info("Testing memory efficiency...")
        
        storage = TPXStoragePurePython()
        
        # Write large dataset
        for i in range(10000):
            storage.write(f"key_{i}", f"value_{i}")
        
        # Check memory usage
        memory_usage = storage.memory_usage()
        assert memory_usage < 100 * 1024 * 1024, "Memory usage should be reasonable"
        
        return True
    
    def test_vm_execution_integration(self) -> bool:
        """Test VM execution integration."""
        logger.info("Testing VM execution integration...")
        
        code = "x = 42"
        
        # Compile
        tokens = self.lexer.tokenize(code)
        ast = self.parser.parse(tokens)
        codegen = OrthosCodeGenerator()
        bytecode = codegen.generate(ast)
        packer = BytecodePacker()
        packed = packer.pack(bytecode)
        
        # Execute
        vm = OrthosVM()
        for instruction in bytecode:
            vm.execute_instruction(instruction)
        
        assert vm.registers[0].value == 42, "VM execution should work"
        
        return True
    
    def test_comprehensive_integration(self) -> bool:
        """Test comprehensive integration across all modules."""
        logger.info("Testing comprehensive integration...")
        
        # Full pipeline test
        code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)

result = factorial(10)
"""
        
        # Lex and parse
        tokens = self.lexer.tokenize(code)
        ast = self.parser.parse(tokens)
        
        # Code generation
        bytecode = self.codegen.generate(ast)
        
        # Packing
        module = CompiledModule(name="factorial", version=0x0002)
        packed = self.packer.pack(module, bytecode)
        
        # Storage
        self.storage.store("factorial.oxb", packed)
        
        # Analysis
        scope_analyzer = ScopeAnalyzer()
        scopes = scope_analyzer.analyze(code)
        
        complexity_analyzer = ComplexityAnalyzer()
        complexity = complexity_analyzer.analyze(code)
        
        # Optimization
        tracer = DemandTracer()
        patterns = tracer.detect_patterns(code)
        
        cutter = IDartCutter()
        optimization = cutter.analyze(code)
        
        # Execution
        vm = OrthosVM()
        vm.execute(packed)
        
        return True
    
    def run_all_comprehensive_tests(self) -> Dict:
        """Run all comprehensive tests."""
        logger.info("=" * 60)
        logger.info("ORTHOS-IDART COMPREHENSIVE TEST SUITE")
        logger.info("=" * 60)
        
        # Initialize modules
        if not self.initialize_modules():
            return {'total': 0, 'passed': 0, 'failed': 0, 'results': []}
        
        # Register tests
        tests = [
            ("Full Compiler Pipeline", self.test_full_compiler_pipeline),
            ("Full Optimization Pipeline", self.test_full_optimization_pipeline),
            ("Analysis Integration", self.test_analysis_integration),
            ("Annihilator Integration", self.test_annihilator_integration),
            ("Storage Comprehensive", self.test_storage_comprehensive),
            ("Security Integration", self.test_security_integration),
            ("Concurrent Execution", self.test_concurrent_execution),
            ("Performance Benchmark", self.test_performance_benchmark),
            ("Memory Efficiency", self.test_memory_efficiency),
            ("VM Execution Integration", self.test_vm_execution_integration),
            ("Comprehensive Integration", self.test_comprehensive_integration),
        ]
        
        # Run tests
        for test_name, test_func in tests:
            self.run_comprehensive_test(test_name, test_func)
        
        # Generate summary
        summary = {
            'total': len(self.results),
            'passed': self.passed_tests,
            'failed': self.failed_tests,
            'results': self.results
        }
        
        logger.info("\n" + "=" * 60)
        logger.info("COMPREHENSIVE TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {summary['total']}")
        logger.info(f"Passed: {summary['passed']}")
        logger.info(f"Failed: {summary['failed']}")
        
        return summary
    
    def print_results(self):
        """Print detailed results."""
        logger.info("\n" + "=" * 60)
        logger.info("DETAILED RESULTS")
        logger.info("=" * 60)
        
        for result in self.results:
            status = "✓ PASSED" if result.passed else "✗ FAILED"
            logger.info(f"{status}: {result.name}")
            if result.error_message:
                logger.info(f"  Error: {result.error_message}")
            logger.info(f"  Time: {result.execution_time_ms:.2f}ms")
        
        # Final verdict
        logger.info("\n" + "=" * 60)
        logger.info("FINAL VERDICT")
        logger.info("=" * 60)
        
        if self.failed_tests == 0:
            logger.info("✓ ALL COMPREHENSIVE TESTS PASSED")
        else:
            logger.info(f"✗ {self.failed_tests} COMPREHENSIVE TEST(S) FAILED")


def run_comprehensive_tests():
    """Main function to run all comprehensive tests."""
    logger.info("=" * 60)
    logger.info("ORTHOS-IDART COMPREHENSIVE TEST SUITE")
    logger.info("=" * 60)
    
    # Create test suite
    test_suite = ComprehensiveTestSuite()
    
    # Run all comprehensive tests
    results = test_suite.run_all_comprehensive_tests()
    
    # Print detailed results
    test_suite.print_results()
    
    # Final verdict
    if results['failed'] == 0:
        logger.info("✓ ALL COMPREHENSIVE TESTS PASSED")
        return True
    else:
        logger.info(f"✗ {results['failed']} COMPREHENSIVE TEST(S) FAILED")
        return False


class TestComprehensiveSuite:
    """Pytest wrapper for comprehensive test suite."""

    def setup_method(self):
        self.suite = ComprehensiveTestSuite()
        self.suite.initialize_modules()

    def test_full_compiler_pipeline(self):
        assert self.suite.test_full_compiler_pipeline() is True

    def test_full_optimization_pipeline(self):
        assert self.suite.test_full_optimization_pipeline() is True

    def test_analysis_integration(self):
        assert self.suite.test_analysis_integration() is True

    def test_annihilator_integration(self):
        assert self.suite.test_annihilator_integration() is True

    def test_storage_comprehensive(self):
        assert self.suite.test_storage_comprehensive() is True

    def test_security_integration(self):
        assert self.suite.test_security_integration() is True

    def test_concurrent_execution(self):
        assert self.suite.test_concurrent_execution() is True

    def test_performance_benchmark(self):
        assert self.suite.test_performance_benchmark() is True

    def test_memory_efficiency(self):
        assert self.suite.test_memory_efficiency() is True

    def test_vm_execution_integration(self):
        assert self.suite.test_vm_execution_integration() is True

    def test_comprehensive_integration(self):
        assert self.suite.test_comprehensive_integration() is True


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)

