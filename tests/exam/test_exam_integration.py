"""
Orthos-iDart Exam Test Suite: Integration Tests
Tests integration between different modules and components.
"""

import sys
import os
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
import time
import logging
import threading
import queue

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orthos.vm.core import OrthosVM
from orthos.compiler.lexer import OrthosLexer
from orthos.compiler.parser import OrthosParser
from orthos.compiler.codegen import OrthosCodeGenerator
from orthos.compiler.packer import BytecodePacker, CompiledModule
from orthos.nexus.bridge import NexusBridge
from orthos.idart.cutter import IDartCutter, CutStrategy
from orthos.idart.express_tunnel import ExpressTunnel, ExpressTunnelManager, TunnelType, OptimizationOp
from orthos.annihilator.faulhaber import FaulhaberEngine
from orthos.annihilator.companion_matrix import CompanionMatrixEngine
from orthos.annihilator.dp_collapser import DPCollapser
from orthos.annihilator.diophantine import DiophantineSolver
from orthos.annihilator.simplex import SimplexOptimizer
from orthos.annihilator.cost_model import CostModel
from orthos.storage.tpx.fallback_pure_python import TPXStoragePurePython

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class IntegrationTestResult:
    """Result of an integration test."""
    name: str
    passed: bool
    error_message: str = ""
    execution_time_ms: float = 0.0


class IntegrationTestSuite:
    """Integration test suite for Orthos-iDart."""
    
    def __init__(self):
        self.results: List[IntegrationTestResult] = []
        self.passed_tests = 0
        self.failed_tests = 0
        self.modules_initialized = False
        
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
    
    def run_integration_test(self, test_name: str, test_func) -> IntegrationTestResult:
        """Run a single integration test."""
        try:
            start_time = time.perf_counter()
            result = test_func()
            execution_time = (time.perf_counter() - start_time) * 1000
            
            test_result = IntegrationTestResult(
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
            test_result = IntegrationTestResult(
                name=test_name,
                passed=False,
                error_message=str(e),
                execution_time_ms=execution_time
            )
            
            logger.error(f"✗ ERROR: {test_name} - {str(e)}")
            self.failed_tests += 1
            self.results.append(test_result)
            return test_result
    
    def test_vm_compiler_integration(self) -> bool:
        """Test VM and compiler integration."""
        logger.info("Testing VM-Compiler integration...")
        
        # Create VM
        vm = OrthosVM()
        
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
        vm.execute(packed)
        
        return True
    
    def test_nexus_bridge_integration(self) -> bool:
        """Test Nexus bridge integration."""
        logger.info("Testing Nexus bridge integration...")
        
        # Initialize bridge
        bridge = NexusBridge()
        
        # Test fast-path filtering
        test_code = "x = 1 + 2"
        is_safe, analysis = bridge.analyze_code(test_code)
        assert is_safe is True
        
        # Test security firewall
        unsafe_code = "import os; os.system('rm -rf /')"
        is_safe_bad, analysis = bridge.analyze_code(unsafe_code)
        assert is_safe_bad is False
        
        return True
    
    def test_idart_pipeline_integration(self) -> bool:
        """Test iDart optimization pipeline integration."""
        logger.info("Testing iDart pipeline integration...")
        
        # Create test graph
        graph = {
            'nodes': list(range(10)),
            'edges': [(i, i+1) for i in range(9)] + [(0, 9)],
            'adjacency': {i: [(i-1) % 10, (i+1) % 10] for i in range(10)}
        }
        
        # Cut graph
        cut_result = self.idart_cutter.cut_graph(graph, CutStrategy.BALANCED)
        
        # Create tunnel
        tunnel = ExpressTunnel(
            tunnel_type=TunnelType.MEMORY,
            optimization_op=OptimizationOp.ZERO_COPY
        )
        tunnel.create()
        
        # Manage tunnels
        self.tunnel_manager.add_tunnel(tunnel)
        
        return True
    
    def test_annihilator_pipeline_integration(self) -> bool:
        """Test annihilator pipeline integration."""
        logger.info("Testing annihilator pipeline integration...")
        
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
    
    def test_storage_integration(self) -> bool:
        """Test storage integration."""
        logger.info("Testing storage integration...")
        
        # Store data
        self.storage.store("test_key", "test_value")
        self.storage.store("number_key", 42)
        self.storage.store("list_key", [1, 2, 3])
        
        # Retrieve data
        value1 = self.storage.get("test_key")
        value2 = self.storage.get("number_key")
        value3 = self.storage.get("list_key")
        
        # Verify data
        assert value1 == "test_value", "String storage failed"
        assert value2 == 42, "Number storage failed"
        assert value3 == [1, 2, 3], "List storage failed"
        
        # Test batch operations
        self.storage.batch_store({
            "batch_key1": "value1",
            "batch_key2": "value2",
            "batch_key3": "value3"
        })
        
        return True
    
    def test_full_pipeline_integration(self) -> bool:
        """Test full optimization pipeline integration."""
        logger.info("Testing full pipeline integration...")
        
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
    
    def test_concurrent_execution(self) -> bool:
        """Test concurrent module execution."""
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
    
    def run_all_integration_tests(self) -> Dict:
        """Run all integration tests."""
        logger.info("=" * 60)
        logger.info("ORTHOS-IDART INTEGRATION TEST SUITE")
        logger.info("=" * 60)
        
        # Initialize modules
        if not self.initialize_modules():
            return {'total': 0, 'passed': 0, 'failed': 0, 'results': []}
        
        # Register tests
        tests = [
            ("VM-Compiler Integration", self.test_vm_compiler_integration),
            ("Nexus Bridge Integration", self.test_nexus_bridge_integration),
            ("iDart Pipeline Integration", self.test_idart_pipeline_integration),
            ("Annihilator Pipeline Integration", self.test_annihilator_pipeline_integration),
            ("Storage Integration", self.test_storage_integration),
            ("Full Pipeline Integration", self.test_full_pipeline_integration),
            ("Concurrent Execution", self.test_concurrent_execution),
        ]
        
        # Run tests
        for test_name, test_func in tests:
            self.run_integration_test(test_name, test_func)
        
        # Generate summary
        summary = {
            'total': len(self.results),
            'passed': self.passed_tests,
            'failed': self.failed_tests,
            'results': self.results
        }
        
        logger.info("\n" + "=" * 60)
        logger.info("INTEGRATION TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {summary['total']}")
        logger.info(f"Passed: {summary['passed']}")
        logger.info(f"Failed: {summary['failed']}")
        
        return summary


def run_integration_tests():
    """Main function to run all integration tests."""
    logger.info("=" * 60)
    logger.info("ORTHOS-IDART INTEGRATION TEST SUITE")
    logger.info("=" * 60)
    
    # Create test suite
    test_suite = IntegrationTestSuite()
    
    # Run all integration tests
    results = test_suite.run_all_integration_tests()
    
    # Print detailed results
    logger.info("\n" + "=" * 60)
    logger.info("DETAILED RESULTS")
    logger.info("=" * 60)
    
    for result in test_suite.results:
        status = "✓ PASSED" if result.passed else "✗ FAILED"
        logger.info(f"{status}: {result.name}")
        if result.error_message:
            logger.info(f"  Error: {result.error_message}")
        logger.info(f"  Time: {result.execution_time_ms:.2f}ms")
    
    # Final verdict
    logger.info("\n" + "=" * 60)
    logger.info("FINAL VERDICT")
    logger.info("=" * 60)
    
    if results['failed'] == 0:
        logger.info("✓ ALL INTEGRATION TESTS PASSED")
        return True
    else:
        logger.info(f"✗ {results['failed']} INTEGRATION TEST(S) FAILED")
        return False


class TestIntegrationSuite:
    """Pytest wrapper for integration test suite."""

    def setup_method(self):
        self.suite = IntegrationTestSuite()
        self.suite.initialize_modules()

    def test_vm_compiler_integration(self):
        assert self.suite.test_vm_compiler_integration() is True

    def test_nexus_bridge_integration(self):
        assert self.suite.test_nexus_bridge_integration() is True

    def test_idart_pipeline_integration(self):
        assert self.suite.test_idart_pipeline_integration() is True

    def test_annihilator_pipeline_integration(self):
        assert self.suite.test_annihilator_pipeline_integration() is True

    def test_storage_integration(self):
        assert self.suite.test_storage_integration() is True

    def test_full_pipeline_integration(self):
        assert self.suite.test_full_pipeline_integration() is True

    def test_concurrent_execution(self):
        assert self.suite.test_concurrent_execution() is True


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)

