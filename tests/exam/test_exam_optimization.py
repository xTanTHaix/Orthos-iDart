"""
Orthos-iDart Exam Test Suite: Optimization Tests
Tests the optimization pipeline including iDart, annihilator, and cost model modules.
"""

import sys
import os
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
import time
import math
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orthos.idart.cutter import IDartCutter, CutStrategy, NodeProfile, EdgeWeight, CutResult
from orthos.idart.express_tunnel import ExpressTunnel, ExpressTunnelManager, TunnelType, OptimizationOp
from orthos.annihilator.cost_model import CostModel, OptimizationAnalysis
from orthos.annihilator.faulhaber import FaulhaberEngine
from orthos.annihilator.companion_matrix import CompanionMatrixEngine
from orthos.annihilator.dp_collapser import DPCollapser
from orthos.annihilator.diophantine import DiophantineSolver
from orthos.annihilator.simplex import SimplexOptimizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class OptimizationTestCase:
    """Test case for optimization pipeline."""
    name: str
    input_data: any
    expected_result: any
    expected_time_ms: float
    optimization_opportunity: str = ""


class OptimizationPipelineTestSuite:
    """Test suite for optimization pipeline components."""
    __test__ = False
    
    def __init__(self):
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_cases: List[OptimizationTestCase] = []
        
    def register_test_case(self, test_case: OptimizationTestCase):
        """Register a test case."""
        self.test_cases.append(test_case)
        logger.info(f"Registered test case: {test_case.name}")
    
    def run_test(self, test_case: OptimizationTestCase) -> bool:
        """Run a single test case."""
        try:
            start_time = time.perf_counter()
            result = self._execute_optimization(test_case)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            
            # Check result
            if self._validate_result(result, test_case):
                logger.info(f"✓ PASSED: {test_case.name} ({elapsed_ms:.2f}ms)")
                self.passed_tests += 1
                return True
            else:
                logger.error(f"✗ FAILED: {test_case.name} - Result mismatch")
                self.failed_tests += 1
                return False
                
        except Exception as e:
            logger.error(f"✗ ERROR: {test_case.name} - {str(e)}")
            self.failed_tests += 1
            return False
    
    def _execute_optimization(self, test_case: OptimizationTestCase) -> any:
        """Execute optimization based on test case type."""
        if "faulhaber" in test_case.name.lower():
            return self._test_faulhaber(test_case)
        elif "matrix" in test_case.name.lower():
            return self._test_matrix_exponentiation(test_case)
        elif "dp" in test_case.name.lower():
            return self._test_dp_collapser(test_case)
        elif "diophantine" in test_case.name.lower():
            return self._test_diophantine(test_case)
        elif "simplex" in test_case.name.lower():
            return self._test_simplex(test_case)
        elif "cutter" in test_case.name.lower():
            return self._test_idart_cutter(test_case)
        elif "tunnel" in test_case.name.lower():
            return self._test_express_tunnel(test_case)
        elif "cost_model" in test_case.name.lower():
            return self._test_cost_model(test_case)
        else:
            return self._test_general_optimization(test_case)
    
    def _validate_result(self, result: any, test_case: OptimizationTestCase) -> bool:
        """Validate test result against expected."""
        if test_case.expected_result is None:
            return result is not None
        
        try:
            if isinstance(test_case.expected_result, (int, float)):
                return abs(result - test_case.expected_result) < test_case.expected_time_ms
            elif isinstance(test_case.expected_result, str):
                return result == test_case.expected_result
            elif isinstance(test_case.expected_result, (list, tuple)):
                return result == test_case.expected_result
            else:
                return result == test_case.expected_result
        except Exception:
            return False
    
    def _test_faulhaber(self, test_case: OptimizationTestCase) -> any:
        """Test Faulhaber polynomial sum optimization."""
        engine = FaulhaberEngine()
        
        if isinstance(test_case.input_data, dict):
            n = test_case.input_data.get('n', 10)
            power = test_case.input_data.get('power', 2)
        else:
            n = int(test_case.input_data)
            power = 2
        
        # Test polynomial sum
        result = engine.compute_polynomial_sum(n, power)
        return result
    
    def _test_matrix_exponentiation(self, test_case: OptimizationTestCase) -> any:
        """Test matrix exponentiation optimization."""
        engine = CompanionMatrixEngine()
        
        if isinstance(test_case.input_data, dict):
            matrix = test_case.input_data.get('matrix', [[1, 1], [1, 0]])
            power = test_case.input_data.get('power', 10)
        else:
            matrix = [[1, 1], [1, 0]]
            power = int(test_case.input_data)
        
        # Test matrix exponentiation
        result = engine.matrix_exponentiation(matrix, power)
        return result
    
    def _test_dp_collapser(self, test_case: OptimizationTestCase) -> any:
        """Test dynamic programming optimization."""
        collapser = DPCollapser()
        
        if isinstance(test_case.input_data, dict):
            sequence = test_case.input_data.get('sequence', [1, 2, 3, 4, 5])
            operation = test_case.input_data.get('operation', 'sum')
        else:
            sequence = [1, 2, 3, 4, 5]
            operation = 'sum'
        
        # Test DP optimization
        result = collapser.optimize_sequence(sequence, operation)
        return result
    
    def _test_diophantine(self, test_case: OptimizationTestCase) -> any:
        """Test Diophantine equation solver."""
        solver = DiophantineSolver()
        
        if isinstance(test_case.input_data, dict):
            a = test_case.input_data.get('a', 3)
            b = test_case.input_data.get('b', 5)
            c = test_case.input_data.get('c', 7)
        else:
            a, b, c = 3, 5, 7
        
        # Test Diophantine equation
        result = solver.solve_linear_diophantine(a, b, c)
        return result
    
    def _test_simplex(self, test_case: OptimizationTestCase) -> any:
        """Test linear programming optimization."""
        optimizer = SimplexOptimizer()
        
        if isinstance(test_case.input_data, dict):
            objective = test_case.input_data.get('objective', [3, 2])
            constraints = test_case.input_data.get('constraints', [
                [1, 1, 4],
                [2, 1, 8],
                [1, 0, 3]
            ])
        else:
            objective = [3, 2]
            constraints = [
                [1, 1, 4],
                [2, 1, 8],
                [1, 0, 3]
            ]
        
        # Test Simplex optimization
        result = optimizer.optimize(objective, constraints)
        return result
    
    def _test_idart_cutter(self, test_case: OptimizationTestCase) -> any:
        """Test iDart graph cutting."""
        cutter = IDartCutter()
        
        if isinstance(test_case.input_data, dict):
            nodes = test_case.input_data.get('nodes', 10)
            edges = test_case.input_data.get('edges', 15)
            strategy = test_case.input_data.get('strategy', CutStrategy.BALANCED)
        else:
            nodes = 10
            edges = 15
            strategy = CutStrategy.BALANCED
        
        # Create mock graph
        graph = self._create_mock_graph(nodes, edges)
        
        # Test graph cutting
        result = cutter.cut_graph(graph, strategy)
        return result
    
    def _test_express_tunnel(self, test_case: OptimizationTestCase) -> any:
        """Test express tunnel optimization."""
        manager = ExpressTunnelManager()
        
        if isinstance(test_case.input_data, dict):
            tunnel_type = test_case.input_data.get('tunnel_type', TunnelType.MEMORY)
            optimization_op = test_case.input_data.get('optimization_op', OptimizationOp.ZERO_COPY)
        else:
            tunnel_type = TunnelType.MEMORY
            optimization_op = OptimizationOp.ZERO_COPY
        
        # Test tunnel creation
        tunnel = ExpressTunnel(tunnel_type=tunnel_type, optimization_op=optimization_op)
        result = tunnel.create()
        return result
    
    def _test_cost_model(self, test_case: OptimizationTestCase) -> any:
        """Test cost model analysis."""
        cost_model = CostModel()
        
        if isinstance(test_case.input_data, dict):
            operations = test_case.input_data.get('operations', 100)
            complexity = test_case.input_data.get('complexity', 'O(n)')
        else:
            operations = 100
            complexity = 'O(n)'
        
        # Test cost analysis
        result = cost_model.analyze(operations, complexity)
        return result
    
    def _test_general_optimization(self, test_case: OptimizationTestCase) -> any:
        """Test general optimization."""
        # Generic optimization test
        result = "Optimization completed"
        return result
    
    def _create_mock_graph(self, nodes: int, edges: int) -> Dict:
        """Create a mock graph for cutting tests."""
        graph = {
            'nodes': list(range(nodes)),
            'edges': [],
            'adjacency': {}
        }
        
        for i in range(nodes):
            graph['adjacency'][i] = []
        
        for _ in range(edges):
            from_node = int(math.floor(nodes * 0.3)) + int(math.floor(edges * 0.1))
            to_node = int(math.floor(nodes * 0.6)) + int(math.floor(edges * 0.2))
            graph['edges'].append((from_node, to_node))
            graph['adjacency'][from_node].append(to_node)
            graph['adjacency'][to_node].append(from_node)
        
        return graph
    
    def run_all_tests(self) -> Dict:
        """Run all registered test cases."""
        logger.info(f"Starting optimization tests: {len(self.test_cases)} cases")
        
        results = {
            'total': len(self.test_cases),
            'passed': 0,
            'failed': 0,
            'test_results': []
        }
        
        for test_case in self.test_cases:
            success = self.run_test(test_case)
            if success:
                results['passed'] += 1
            else:
                results['failed'] += 1
            results['test_results'].append({
                'name': test_case.name,
                'passed': success,
                'time_ms': None  # Will be filled in
            })
        
        logger.info(f"Optimization tests completed: {results['passed']}/{results['total']} passed")
        return results


TestOptimizationPipeline = OptimizationPipelineTestSuite


class OptimizationIntegrationTestSuite:
    """Integration tests for optimization pipeline."""
    __test__ = False
    
    def __init__(self):
        self.results = []
        
    def test_full_optimization_pipeline(self) -> bool:
        """Test complete optimization pipeline from input to result."""
        try:
            logger.info("Testing full optimization pipeline...")
            
            # Step 1: Create cost model
            cost_model = CostModel()
            cost_analysis = cost_model.analyze(1000, 'O(n^2)')
            
            # Step 2: Create iDart cutter
            cutter = IDartCutter()
            graph = self._create_test_graph()
            cut_result = cutter.cut_graph(graph, CutStrategy.HOTSPOT)
            
            # Step 3: Create express tunnel
            tunnel = ExpressTunnel(
                tunnel_type=TunnelType.MEMORY,
                optimization_op=OptimizationOp.ZERO_COPY
            )
            tunnel.create()
            
            # Step 4: Run annihilator
            faulhaber = FaulhaberEngine()
            result = faulhaber.compute_polynomial_sum(100, 3)
            
            logger.info("✓ Full optimization pipeline test passed")
            return True
            
        except Exception as e:
            logger.error(f"✗ Full optimization pipeline test failed: {str(e)}")
            return False
    
    def _create_test_graph(self) -> Dict:
        """Create test graph for cutting."""
        return {
            'nodes': list(range(20)),
            'edges': [(i, i+1) for i in range(19)] + [(0, 19)],
            'adjacency': {i: [(i-1) % 20, (i+1) % 20] for i in range(20)}
        }


def run_optimization_tests():
    """Main function to run all optimization tests."""
    logger.info("=" * 60)
    logger.info("ORTHOS-IDART OPTIMIZATION TEST SUITE")
    logger.info("=" * 60)
    
    # Create test suite
    test_suite = TestOptimizationPipeline()
    
    # Register test cases
    test_cases = [
        OptimizationTestCase(
            name="Faulhaber_Sum_Power2",
            input_data={'n': 10, 'power': 2},
            expected_result=385,
            expected_time_ms=10.0,
            optimization_opportunity="Polynomial sum optimization"
        ),
        OptimizationTestCase(
            name="Faulhaber_Sum_Power3",
            input_data={'n': 10, 'power': 3},
            expected_result=3025,
            expected_time_ms=10.0,
            optimization_opportunity="Polynomial sum optimization"
        ),
        OptimizationTestCase(
            name="Matrix_Exponentiation_10",
            input_data={'matrix': [[1, 1], [1, 0]], 'power': 10},
            expected_result=None,
            expected_time_ms=50.0,
            optimization_opportunity="Matrix exponentiation"
        ),
        OptimizationTestCase(
            name="DP_Collapser_Sum",
            input_data={'sequence': [1, 2, 3, 4, 5], 'operation': 'sum'},
            expected_result=15,
            expected_time_ms=5.0,
            optimization_opportunity="Dynamic programming"
        ),
        OptimizationTestCase(
            name="Diophantine_Equation",
            input_data={'a': 3, 'b': 5, 'c': 7},
            expected_result=None,
            expected_time_ms=10.0,
            optimization_opportunity="Diophantine solving"
        ),
        OptimizationTestCase(
            name="Simplex_Optimization",
            input_data={'objective': [3, 2], 'constraints': [[1, 1, 4], [2, 1, 8], [1, 0, 3]]},
            expected_result=None,
            expected_time_ms=100.0,
            optimization_opportunity="Linear programming"
        ),
        OptimizationTestCase(
            name="IDart_Cutter_Balanced",
            input_data={'nodes': 10, 'edges': 15, 'strategy': CutStrategy.BALANCED},
            expected_result=None,
            expected_time_ms=50.0,
            optimization_opportunity="Graph cutting"
        ),
        OptimizationTestCase(
            name="Express_Tunnel_Memory",
            input_data={'tunnel_type': TunnelType.MEMORY, 'optimization_op': OptimizationOp.ZERO_COPY},
            expected_result=None,
            expected_time_ms=5.0,
            optimization_opportunity="Zero-copy optimization"
        ),
        OptimizationTestCase(
            name="Cost_Model_Analysis",
            input_data={'operations': 1000, 'complexity': 'O(n^2)'},
            expected_result=None,
            expected_time_ms=5.0,
            optimization_opportunity="Cost analysis"
        ),
    ]
    
    for test_case in test_cases:
        test_suite.register_test_case(test_case)
    
    # Run all tests
    results = test_suite.run_all_tests()
    
    # Run integration tests
    logger.info("\n" + "=" * 60)
    logger.info("OPTIMIZATION INTEGRATION TESTS")
    logger.info("=" * 60)
    
    integration_suite = TestOptimizationIntegration()
    integration_passed = integration_suite.test_full_optimization_pipeline()
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total Test Cases: {results['total']}")
    logger.info(f"Passed: {results['passed']}")
    logger.info(f"Failed: {results['failed']}")
    logger.info(f"Integration Test: {'PASSED' if integration_passed else 'FAILED'}")
    
    if results['failed'] == 0 and integration_passed:
        logger.info("\n✓ ALL OPTIMIZATION TESTS PASSED")
        return True
    else:
        logger.info("\n✗ SOME OPTIMIZATION TESTS FAILED")
        return False


TestOptimizationIntegration = OptimizationIntegrationTestSuite


class TestOptimizationSuite:
    """Pytest suite for optimization components."""

    def test_faulhaber_sum(self):
        pipe = OptimizationPipelineTestSuite()
        tc = OptimizationTestCase(
            name="Faulhaber_Sum_Squares",
            input_data={'n': 100, 'power': 2},
            expected_result=338350,
            expected_time_ms=10.0,
            optimization_opportunity="Faulhaber formula"
        )
        assert pipe.run_test(tc) is True

    def test_matrix_exponentiation(self):
        pipe = OptimizationPipelineTestSuite()
        tc = OptimizationTestCase(
            name="Matrix_Exponentiation_Fibonacci",
            input_data={'matrix': [[1, 1], [1, 0]], 'exp': 10},
            expected_result=[[89, 55], [55, 34]],
            expected_time_ms=50.0,
            optimization_opportunity="Matrix exponentiation"
        )
        assert pipe.run_test(tc) is True

    def test_dp_collapser(self):
        pipe = OptimizationPipelineTestSuite()
        tc = OptimizationTestCase(
            name="DP_Collapser_Sum",
            input_data={'sequence': [1, 2, 3, 4, 5], 'operation': 'sum'},
            expected_result=15,
            expected_time_ms=5.0,
            optimization_opportunity="Dynamic programming"
        )
        assert pipe.run_test(tc) is True

    def test_diophantine(self):
        pipe = OptimizationPipelineTestSuite()
        tc = OptimizationTestCase(
            name="Diophantine_Equation",
            input_data={'a': 3, 'b': 5, 'c': 7},
            expected_result=None,
            expected_time_ms=10.0,
            optimization_opportunity="Diophantine solving"
        )
        assert pipe.run_test(tc) is True

    def test_simplex(self):
        pipe = OptimizationPipelineTestSuite()
        tc = OptimizationTestCase(
            name="Simplex_Optimization",
            input_data={'objective': [3, 2], 'constraints': [[1, 1, 4], [2, 1, 8], [1, 0, 3]]},
            expected_result=None,
            expected_time_ms=100.0,
            optimization_opportunity="Linear programming"
        )
        assert pipe.run_test(tc) is True

    def test_cutter(self):
        pipe = OptimizationPipelineTestSuite()
        tc = OptimizationTestCase(
            name="IDart_Cutter_Balanced",
            input_data={'nodes': 10, 'edges': 15, 'strategy': CutStrategy.BALANCED},
            expected_result=None,
            expected_time_ms=50.0,
            optimization_opportunity="Graph cutting"
        )
        assert pipe.run_test(tc) is True

    def test_tunnel(self):
        pipe = OptimizationPipelineTestSuite()
        tc = OptimizationTestCase(
            name="Express_Tunnel_Memory",
            input_data={'tunnel_type': TunnelType.MEMORY, 'optimization_op': OptimizationOp.ZERO_COPY},
            expected_result=None,
            expected_time_ms=5.0,
            optimization_opportunity="Zero-copy optimization"
        )
        assert pipe.run_test(tc) is True

    def test_cost_model(self):
        pipe = OptimizationPipelineTestSuite()
        tc = OptimizationTestCase(
            name="Cost_Model_Analysis",
            input_data={'operations': 1000, 'complexity': 'O(n^2)'},
            expected_result=None,
            expected_time_ms=5.0,
            optimization_opportunity="Cost analysis"
        )
        assert pipe.run_test(tc) is True

    def test_full_pipeline(self):
        suite = OptimizationIntegrationTestSuite()
        assert suite.test_full_optimization_pipeline() is True


if __name__ == "__main__":
    success = run_optimization_tests()
    sys.exit(0 if success else 1)

