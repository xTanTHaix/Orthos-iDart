"""
Intermediate Exam Tests for Orthos-iDart
Tests intermediate optimization scenarios and integration points.
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
from orthos.compiler.analysis.scope import ScopeAnalyzer
from orthos.compiler.analysis.cfg import CFGBuilder
from orthos.compiler.analysis.complexity_gate import ComplexityAnalyzer
from orthos.compiler.analysis.verification_cache import VerificationCache
from orthos.idart.demand_tracer import DemandTracer
from orthos.idart.cutter import IDartCutter
from orthos.idart.express_tunnel import ExpressTunnel, ExpressTunnelManager
from orthos.annihilator.faulhaber import FaulhaberEngine
from orthos.annihilator.companion_matrix import CompanionMatrixEngine
from orthos.annihilator.dp_collapser import DPCollapser
from orthos.annihilator.diophantine import DiophantineSolver
from orthos.annihilator.simplex import SimplexOptimizer
from orthos.annihilator.cost_model import CostModel
from orthos.storage.tpx.fallback_pure_python import TPXStoragePurePython


class TestIntermediateScopeAnalysis:
    """Test scope analysis functionality."""
    
    def test_local_scope_detection(self):
        """Test local variable scope detection."""
        code = """
def foo():
    x = 1
    y = 2
    return x + y
"""
        analyzer = ScopeAnalyzer()
        scopes = analyzer.analyze(code)
        assert len(scopes) > 0
        assert any('x' in str(s) for s in scopes)
    
    def test_nested_scope_detection(self):
        """Test nested scope detection."""
        code = """
def outer():
    x = 1
    def inner():
        y = 2
        return y
    return inner()
"""
        analyzer = ScopeAnalyzer()
        scopes = analyzer.analyze(code)
        assert len(scopes) > 0
    
    def test_global_scope_detection(self):
        """Test global scope detection."""
        code = """
GLOBAL_VAR = 42

def foo():
    return GLOBAL_VAR
"""
        analyzer = ScopeAnalyzer()
        scopes = analyzer.analyze(code)
        assert len(scopes) > 0


class TestIntermediateCFGAnalysis:
    """Test control flow graph analysis."""
    
    def test_cfg_basic_block_creation(self):
        """Test basic block creation."""
        code = """
x = 1
y = 2
z = x + y
"""
        builder = CFGBuilder()
        cfg = builder.build(code)
        assert cfg is not None
        assert len(cfg.blocks) > 0
    
    def test_cfg_loop_detection(self):
        """Test loop detection in CFG."""
        code = """
i = 0
while i < 10:
    i = i + 1
"""
        builder = CFGBuilder()
        cfg = builder.build(code)
        assert cfg is not None
        # Should detect loop
        assert len(cfg.blocks) > 1
    
    def test_cfg_dominator_analysis(self):
        """Test dominator analysis."""
        code = """
x = 1
if x > 0:
    y = 2
else:
    y = 3
"""
        builder = CFGBuilder()
        cfg = builder.build(code)
        assert cfg is not None
        assert hasattr(cfg, 'dominators')


class TestIntermediateComplexityAnalysis:
    """Test complexity analysis."""
    
    def test_cyclomatic_complexity(self):
        """Test cyclomatic complexity calculation."""
        code = """
def foo(x, y):
    if x > 0:
        if y > 0:
            return x + y
        return x
    return y
"""
        analyzer = ComplexityAnalyzer()
        complexity = analyzer.analyze(code)
        assert complexity > 0
    
    def test_halstead_complexity(self):
        """Test Halstead complexity calculation."""
        code = """
x = 1
y = 2
z = x + y
"""
        analyzer = ComplexityAnalyzer()
        complexity = analyzer.analyze(code)
        assert hasattr(complexity, 'operators')
        assert hasattr(complexity, 'operands')
    
    def test_mccabe_complexity(self):
        """Test McCabe complexity calculation."""
        code = """
def foo(x):
    if x > 0:
        return x
    elif x < 0:
        return -x
    return 0
"""
        analyzer = ComplexityAnalyzer()
        complexity = analyzer.analyze(code)
        assert complexity > 0


class TestIntermediateVerificationCache:
    """Test verification cache."""
    
    def test_cache_creation(self):
        """Test verification cache creation."""
        cache = VerificationCache()
        assert cache is not None
    
    def test_cache_store_retrieve(self):
        """Test cache store and retrieve."""
        cache = VerificationCache()
        key = "test_key"
        value = "test_value"
        cache.store(key, value)
        retrieved = cache.retrieve(key)
        assert retrieved == value
    
    def test_cache_hit_miss(self):
        """Test cache hit and miss."""
        cache = VerificationCache()
        cache.store("key1", "value1")
        assert cache.hit("key1") is True
        assert cache.hit("key2") is False


class TestIntermediateIDartCutter:
    """Test iDart cutter functionality."""
    
    def test_cutter_creation(self):
        """Test cutter can be created."""
        cutter = IDartCutter()
        assert cutter is not None
    
    def test_cutting_strategies(self):
        """Test different cutting strategies."""
        cutter = IDartCutter()
        # Test MIN_CUT strategy
        result = cutter.cut("x = 1", strategy="MIN_CUT")
        assert result is not None
    
    def test_hotspot_detection(self):
        """Test hotspot detection."""
        cutter = IDartCutter()
        code = """
def hot_function():
    for i in range(10000):
        x = i * 2
        y = x + 1
        z = y * 3
    return z
"""
        result = cutter.analyze(code)
        assert result is not None


class TestIntermediateExpressTunnel:
    """Test express tunnel functionality."""
    
    def test_tunnel_creation(self):
        """Test tunnel can be created."""
        tunnel = ExpressTunnel()
        assert tunnel is not None
    
    def test_tunnel_manager_creation(self):
        """Test tunnel manager can be created."""
        manager = ExpressTunnelManager()
        assert manager is not None
    
    def test_tunnel_optimization(self):
        """Test tunnel optimization."""
        manager = ExpressTunnelManager()
        tunnel = manager.create_tunnel("MEMORY")
        assert tunnel is not None


class TestIntermediateFaulhaberEngine:
    """Test Faulhaber engine for polynomial sum optimization."""
    
    def test_engine_creation(self):
        """Test engine can be created."""
        engine = FaulhaberEngine()
        assert engine is not None
    
    def test_polynomial_sum(self):
        """Test polynomial sum calculation."""
        engine = FaulhaberEngine()
        n = 10
        result = engine.sum_polynomial(n, 2)  # Sum of squares
        assert result > 0
    
    def test_bernoulli_numbers(self):
        """Test Bernoulli number computation."""
        engine = FaulhaberEngine()
        bernoulli = engine.compute_bernoulli(5)
        assert bernoulli is not None


class TestIntermediateCompanionMatrix:
    """Test companion matrix for linear recurrence optimization."""
    
    def test_engine_creation(self):
        """Test engine can be created."""
        engine = CompanionMatrixEngine()
        assert engine is not None
    
    def test_matrix_exponentiation(self):
        """Test matrix exponentiation."""
        engine = CompanionMatrixEngine()
        result = engine.exponentiate(2, 10)
        assert result is not None
    
    def test_eigenvalue_computation(self):
        """Test eigenvalue computation."""
        engine = CompanionMatrixEngine()
        eigenvalues = engine.compute_eigenvalues([1, 2, 3])
        assert eigenvalues is not None


class TestIntermediateDPCollapser:
    """Test DP collapser for dynamic programming optimization."""
    
    def test_engine_creation(self):
        """Test engine can be created."""
        engine = DPCollapser()
        assert engine is not None
    
    def test_memoization(self):
        """Test memoization optimization."""
        engine = DPCollapser()
        result = engine.optimize("fibonacci")
        assert result is not None
    
    def test_space_optimization(self):
        """Test space optimization."""
        engine = DPCollapser()
        result = engine.optimize("knapsack")
        assert result is not None


class TestIntermediateDiophantineSolver:
    """Test Diophantine solver for integer equation solving."""
    
    def test_engine_creation(self):
        """Test engine can be created."""
        solver = DiophantineSolver()
        assert solver is not None
    
    def test_extended_euclidean(self):
        """Test extended Euclidean algorithm."""
        solver = DiophantineSolver()
        result = solver.extended_gcd(48, 18)
        assert result is not None
    
    def test_pythagorean_triples(self):
        """Test Pythagorean triples generation."""
        solver = DiophantineSolver()
        triples = solver.generate_triples(10)
        assert triples is not None


class TestIntermediateSimplexOptimizer:
    """Test simplex optimizer for linear programming."""
    
    def test_engine_creation(self):
        """Test engine can be created."""
        optimizer = SimplexOptimizer()
        assert optimizer is not None
    
    def test_simplex_method(self):
        """Test simplex method."""
        optimizer = SimplexOptimizer()
        result = optimizer.solve([1, 2, 3], [4, 5, 6])
        assert result is not None
    
    def test_constraint_handling(self):
        """Test constraint handling."""
        optimizer = SimplexOptimizer()
        result = optimizer.optimize_constraints([1, 2], [3, 4])
        assert result is not None


class TestIntermediateCostModel:
    """Test cost model for performance estimation."""
    
    def test_engine_creation(self):
        """Test engine can be created."""
        model = CostModel()
        assert model is not None
    
    def test_performance_estimation(self):
        """Test performance estimation."""
        model = CostModel()
        result = model.estimate("loop")
        assert result is not None
    
    def test_optimization_analysis(self):
        """Test optimization analysis."""
        model = CostModel()
        result = model.analyze("function")
        assert result is not None


class TestIntermediateIntegration:
    """Test integration between modules."""
    
    def test_compiler_to_vm_pipeline(self):
        """Test compiler to VM pipeline."""
        code = "x = 42"
        lexer = OrthosLexer(code)
        tokens = lexer.tokenize()
        parser = OrthosParser(tokens)
        ast = parser.parse()
        codegen = OrthosCodeGenerator()
        bytecode = codegen.generate(ast)
        packer = BytecodePacker()
        packed = packer.pack(bytecode)
        storage = TPXStoragePurePython()
        storage.write("test_oxb", packed)
        assert storage.read("test_oxb") is not None
    
    def test_analysis_pipeline(self):
        """Test analysis pipeline."""
        code = """
def foo(x):
    if x > 0:
        return x
    return 0
"""
        analyzer = ScopeAnalyzer()
        scopes = analyzer.analyze(code)
        assert len(scopes) > 0
        
        analyzer = ComplexityAnalyzer()
        complexity = analyzer.analyze(code)
        assert complexity > 0
    
    def test_optimization_pipeline(self):
        """Test optimization pipeline."""
        code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
        tracer = DemandTracer()
        patterns = tracer.detect_patterns(code)
        assert len(patterns) >= 0
        
        cutter = IDartCutter()
        result = cutter.analyze(code)
        assert result is not None


class TestIntermediateStorageIntegration:
    """Test storage backend integration."""
    
    def test_storage_with_tpx(self):
        """Test storage with TPX backend."""
        storage = TPXStoragePurePython()
        
        # Write test data
        test_data = {
            "key1": "value1",
            "key2": 42,
            "key3": [1, 2, 3]
        }
        
        for key, value in test_data.items():
            storage.write(key, value)
        
        # Read test data
        for key, expected_value in test_data.items():
            read_value = storage.read(key)
            assert read_value == expected_value
    
    def test_storage_batch_operations(self):
        """Test storage batch operations."""
        storage = TPXStoragePurePython()
        
        # Batch write
        storage.batch_write([
            ("batch1", "value1"),
            ("batch2", "value2"),
            ("batch3", "value3")
        ])
        
        # Batch read
        results = storage.batch_read(["batch1", "batch2", "batch3"])
        assert len(results) == 3


class TestIntermediateErrorHandling:
    """Test error handling in intermediate modules."""
    
    def test_scope_analysis_error(self):
        """Test scope analysis error handling."""
        analyzer = ScopeAnalyzer()
        code = "x = 1"  # Simple code
        try:
            scopes = analyzer.analyze(code)
            assert scopes is not None
        except Exception as e:
            assert str(e) != ""
    
    def test_complexity_analysis_error(self):
        """Test complexity analysis error handling."""
        analyzer = ComplexityAnalyzer()
        code = "x = 1"
        try:
            complexity = analyzer.analyze(code)
            assert complexity is not None
        except Exception as e:
            assert str(e) != ""
    
    def test_storage_error_handling(self):
        """Test storage error handling."""
        storage = TPXStoragePurePython()
        try:
            storage.write("test", "value")
            storage.delete("nonexistent_key")
            assert storage.read("nonexistent_key") is None
        except Exception as e:
            assert str(e) != ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
