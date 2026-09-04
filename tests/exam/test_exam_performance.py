"""
Orthos-iDart Exam Test Suite: Performance Tests
Tests performance metrics, benchmarks, and execution speed.
"""

import sys
import os
import time
import timeit
from typing import List, Dict, Optional, Tuple, Callable
from dataclasses import dataclass, field
import statistics
import logging
import platform

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orthos.vm.core import OrthosVM
from orthos.compiler.packer import BytecodePacker, CompiledModule
from orthos.idart.cutter import IDartCutter, CutStrategy
from orthos.annihilator.cost_model import CostModel
from orthos.storage.tpx.fallback_pure_python import TPXStoragePurePython

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data."""
    name: str
    value: float
    unit: str = "ms"
    benchmark: str = ""


@dataclass
class BenchmarkResult:
    """Benchmark result."""
    name: str
    iterations: int
    min_time: float
    max_time: float
    avg_time: float
    std_dev: float
    throughput: float
    memory_usage: int


class PerformanceTestSuite:
    """Comprehensive performance test suite."""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.metrics: List[PerformanceMetric] = []
        self.passed_tests = 0
        self.failed_tests = 0
        
    def register_benchmark(self, benchmark_name: str, test_func: Callable) -> None:
        """Register a benchmark test."""
        logger.info(f"Registered benchmark: {benchmark_name}")
    
    def run_benchmark(self, benchmark_name: str, test_func: Callable, 
                     iterations: int = 10, warmup: int = 3) -> BenchmarkResult:
        """Run a single benchmark."""
        try:
            # Warmup
            logger.info(f"Warming up: {benchmark_name}...")
            for _ in range(warmup):
                test_func()
            
            # Measure
            logger.info(f"Running benchmark: {benchmark_name} ({iterations} iterations)...")
            
            times = []
            for i in range(iterations):
                start = time.perf_counter()
                test_func()
                end = time.perf_counter()
                times.append((end - start) * 1000)  # Convert to ms
            
            # Calculate statistics
            min_time = min(times)
            max_time = max(times)
            avg_time = statistics.mean(times)
            std_dev = statistics.stdev(times) if len(times) > 1 else 0.0
            
            # Get memory usage
            memory_usage = self._get_memory_usage()
            
            # Calculate throughput
            throughput = iterations / (avg_time / 1000)  # operations per second
            
            result = BenchmarkResult(
                name=benchmark_name,
                iterations=iterations,
                min_time=min_time,
                max_time=max_time,
                avg_time=avg_time,
                std_dev=std_dev,
                throughput=throughput,
                memory_usage=memory_usage
            )
            
            self.results.append(result)
            self.metrics.append(PerformanceMetric(
                name=benchmark_name,
                value=avg_time,
                unit="ms",
                benchmark=benchmark_name
            ))
            
            logger.info(f"✓ Benchmark completed: {benchmark_name}")
            logger.info(f"  Avg: {avg_time:.3f}ms, Min: {min_time:.3f}ms, Max: {max_time:.3f}ms")
            logger.info(f"  Std Dev: {std_dev:.3f}ms, Throughput: {throughput:.2f} ops/s")
            
            return result
            
        except Exception as e:
            logger.error(f"✗ Benchmark failed: {benchmark_name} - {str(e)}")
            self.failed_tests += 1
            return None
    
    def _get_memory_usage(self) -> int:
        """Get current process memory usage in bytes (cross-platform)."""
        try:
            if platform.system() == "Windows":
                import ctypes
                import ctypes.wintypes
                # Use Windows PROCESS_MEMORY_COUNTERS via GetProcessMemoryInfo
                class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                    _fields_ = [
                        ("cb", ctypes.wintypes.DWORD),
                        ("PageFaultCount", ctypes.wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t),
                        ("PeakPagefileUsage", ctypes.c_size_t),
                    ]
                pmc = PROCESS_MEMORY_COUNTERS()
                pmc.cb = ctypes.sizeof(pmc)
                psapi = ctypes.windll.psapi  # type: ignore[attr-defined]
                kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
                handle = kernel32.GetCurrentProcess()
                if psapi.GetProcessMemoryInfo(handle, ctypes.byref(pmc), pmc.cb):
                    return pmc.WorkingSetSize
                return 0
            else:
                import resource as _resource
                usage = _resource.getrusage(_resource.RUSAGE_SELF)
                # ru_maxrss is KB on Linux, bytes on macOS
                multiplier = 1024 if platform.system() == "Linux" else 1
                return usage.ru_maxrss * multiplier
        except Exception:
            return 0

    
    def test_vm_execution_speed(self) -> BenchmarkResult:
        """Test VM execution speed."""
        def test():
            vm = OrthosVM()
            # Execute a simple instruction sequence
            vm.execute_instruction('HALT')
            vm.execute_instruction('MOV', 0, 1)
            vm.execute_instruction('LOAD_CONST', 42)
        
        return self.run_benchmark("VM_Execution_Speed", test, iterations=100)
    
    def test_bytecode_packing_speed(self) -> BenchmarkResult:
        """Test bytecode packing speed."""
        def test():
            packer = BytecodePacker()
            # Pack a simple module
            module = CompiledModule(name="test", version=0x0002)
            packer.pack(module)
        
        return self.run_benchmark("Bytecode_Packing_Speed", test, iterations=50)
    
    def test_storage_operations_speed(self) -> BenchmarkResult:
        """Test storage operation speed."""
        def test():
            storage = TPXStoragePurePython()
            # Store and retrieve
            storage.store("test_key", "test_value")
            value = storage.get("test_key")
        
        return self.run_benchmark("Storage_Operation_Speed", test, iterations=100)
    
    def test_compiler_optimization_speed(self) -> BenchmarkResult:
        """Test compiler optimization speed."""
        def test():
            cutter = IDartCutter()
            # Create and cut a simple graph
            graph = {
                'nodes': list(range(5)),
                'edges': [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)],
                'adjacency': {i: [(i-1) % 5, (i+1) % 5] for i in range(5)}
            }
            cutter.cut_graph(graph, CutStrategy.BALANCED)
        
        return self.run_benchmark("Compiler_Optimization_Speed", test, iterations=20)
    
    def test_cost_analysis_speed(self) -> BenchmarkResult:
        """Test cost analysis speed."""
        def test():
            cost_model = CostModel()
            # Analyze different complexities
            for complexity in ['O(1)', 'O(n)', 'O(n^2)', 'O(n^3)']:
                cost_model.analyze(1000, complexity)
        
        return self.run_benchmark("Cost_Analysis_Speed", test, iterations=10)
    
    def test_memory_allocation_speed(self) -> BenchmarkResult:
        """Test memory allocation speed."""
        def test():
            # Allocate and deallocate memory
            data = [0] * 1000
            del data
            data = [0] * 1000
            del data
        
        return self.run_benchmark("Memory_Allocation_Speed", test, iterations=100)
    
    def test_gc_collection_speed(self) -> BenchmarkResult:
        """Test garbage collection speed."""
        def test():
            import gc
            # Create garbage
            garbage = [object() for _ in range(100)]
            # Collect
            gc.collect()
        
        return self.run_benchmark("GC_Collection_Speed", test, iterations=10)
    
    def test_concurrent_execution_speed(self) -> BenchmarkResult:
        """Test concurrent execution speed."""
        def test():
            import threading
            results = []
            
            def worker():
                for _ in range(100):
                    pass
            
            threads = [threading.Thread(target=worker) for _ in range(4)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        
        return self.run_benchmark("Concurrent_Execution_Speed", test, iterations=5)
    
    def run_all_benchmarks(self) -> Dict:
        """Run all registered benchmarks."""
        logger.info("=" * 60)
        logger.info("ORTHOS-IDART PERFORMANCE TEST SUITE")
        logger.info("=" * 60)
        
        # Register benchmarks
        self.register_benchmark("VM_Execution_Speed", self.test_vm_execution_speed)
        self.register_benchmark("Bytecode_Packing_Speed", self.test_bytecode_packing_speed)
        self.register_benchmark("Storage_Operation_Speed", self.test_storage_operations_speed)
        self.register_benchmark("Compiler_Optimization_Speed", self.test_compiler_optimization_speed)
        self.register_benchmark("Cost_Analysis_Speed", self.test_cost_analysis_speed)
        self.register_benchmark("Memory_Allocation_Speed", self.test_memory_allocation_speed)
        self.register_benchmark("GC_Collection_Speed", self.test_gc_collection_speed)
        self.register_benchmark("Concurrent_Execution_Speed", self.test_concurrent_execution_speed)
        
        # Run all benchmarks
        logger.info("\nRunning benchmarks...")
        for result in self.results:
            logger.info(f"  {result.name}: {result.avg_time:.3f}ms ± {result.std_dev:.3f}ms")
        
        logger.info(f"\nCompleted {len(self.results)} benchmarks")
        
        return {
            'total': len(self.results),
            'results': self.results,
            'metrics': self.metrics
        }
    
    def generate_report(self) -> str:
        """Generate performance report."""
        if not self.results:
            return "No benchmarks run."
        
        report = []
        report.append("=" * 60)
        report.append("ORTHOS-IDART PERFORMANCE REPORT")
        report.append("=" * 60)
        report.append("")
        report.append(f"Benchmarks Run: {len(self.results)}")
        report.append("")
        report.append("-" * 60)
        report.append(f"{'Benchmark':<40} {'Avg (ms)':<12} {'Std Dev':<12} {'Throughput':<15}")
        report.append("-" * 60)
        
        for result in self.results:
            report.append(
                f"{result.name:<40} {result.avg_time:<12.3f} {result.std_dev:<12.3f} {result.throughput:<15.2f}"
            )
        
        report.append("-" * 60)
        report.append("")
        
        # Calculate overall statistics
        all_times = [r.avg_time for r in self.results]
        report.append("Overall Statistics:")
        report.append(f"  Total Benchmarks: {len(all_times)}")
        report.append(f"  Fastest: {min(all_times):.3f}ms")
        report.append(f"  Slowest: {max(all_times):.3f}ms")
        report.append(f"  Average: {statistics.mean(all_times):.3f}ms")
        report.append(f"  Std Dev: {statistics.stdev(all_times):.3f}ms" if len(all_times) > 1 else "")
        
        return "\n".join(report)


class PerformanceRegressionTest:
    """Regression tests for performance."""
    
    def __init__(self):
        self.baseline_results = {}
        
    def set_baseline(self, benchmark_name: str, result: BenchmarkResult) -> None:
        """Set baseline for a benchmark."""
        self.baseline_results[benchmark_name] = result
        logger.info(f"Set baseline for {benchmark_name}")
    
    def check_regression(self, benchmark_name: str, result: BenchmarkResult, 
                        threshold: float = 0.2) -> bool:
        """Check for performance regression."""
        if benchmark_name not in self.baseline_results:
            logger.warning(f"No baseline for {benchmark_name}")
            return True
        
        baseline = self.baseline_results[benchmark_name]
        regression = (result.avg_time - baseline.avg_time) / baseline.avg_time
        
        if regression > threshold:
            logger.error(f"PERFORMANCE REGRESSION DETECTED in {benchmark_name}")
            logger.error(f"  Baseline: {baseline.avg_time:.3f}ms")
            logger.error(f"  Current:  {result.avg_time:.3f}ms")
            logger.error(f"  Regression: {regression*100:.1f}%")
            return False
        else:
            logger.info(f"✓ No regression in {benchmark_name}")
            return True


def run_performance_tests():
    """Main function to run all performance tests."""
    logger.info("=" * 60)
    logger.info("ORTHOS-IDART PERFORMANCE TEST SUITE")
    logger.info("=" * 60)
    
    # Create test suite
    test_suite = PerformanceTestSuite()
    
    # Run all benchmarks
    results = test_suite.run_all_benchmarks()
    
    # Generate report
    report = test_suite.generate_report()
    logger.info("\n" + report)
    
    # Check for regressions (if baselines exist)
    logger.info("\n" + "=" * 60)
    logger.info("REGRESSION CHECK")
    logger.info("=" * 60)
    
    regression_suite = PerformanceRegressionTest()
    all_passed = True
    
    for result in test_suite.results:
        if regression_suite.check_regression(result.name, result):
            test_suite.passed_tests += 1
        else:
            test_suite.failed_tests += 1
            all_passed = False
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("PERFORMANCE TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total Benchmarks: {len(test_suite.results)}")
    logger.info(f"Passed: {test_suite.passed_tests}")
    logger.info(f"Failed: {test_suite.failed_tests}")
    
    return all_passed


class TestPerformanceSuite:
    """Pytest wrapper for performance test suite."""

    def test_vm_execution_speed(self):
        suite = PerformanceTestSuite()
        res = suite.test_vm_execution_speed()
        assert res is not None

    def test_bytecode_packing_speed(self):
        suite = PerformanceTestSuite()
        res = suite.test_bytecode_packing_speed()
        assert res is not None

    def test_storage_operations_speed(self):
        suite = PerformanceTestSuite()
        res = suite.test_storage_operations_speed()
        assert res is not None

    def test_compiler_optimization_speed(self):
        suite = PerformanceTestSuite()
        res = suite.test_compiler_optimization_speed()
        assert res is not None

    def test_cost_analysis_speed(self):
        suite = PerformanceTestSuite()
        res = suite.test_cost_analysis_speed()
        assert res is not None

    def test_memory_allocation_speed(self):
        suite = PerformanceTestSuite()
        res = suite.test_memory_allocation_speed()
        assert res is not None

    def test_gc_collection_speed(self):
        suite = PerformanceTestSuite()
        res = suite.test_gc_collection_speed()
        assert res is not None

    def test_concurrent_execution_speed(self):
        suite = PerformanceTestSuite()
        res = suite.test_concurrent_execution_speed()
        assert res is not None

    def test_full_benchmark_run(self):
        res = run_performance_tests()
        assert res is True


if __name__ == "__main__":
    success = run_performance_tests()
    sys.exit(0 if success else 1)
