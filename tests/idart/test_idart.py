"""
iDart Optimization Test Suite - Comprehensive tests for optimization pipeline

Tests cover:
- Demand tracer
- Graph cutter
- Express tunnel
- Optimization opportunities
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orthos.idart.demand_tracer import DemandTracer, DemandPattern, OptimizationOpportunity
from orthos.idart.cutter import IDartCutter, CutStrategy, NodeProfile, EdgeWeight
from orthos.idart.express_tunnel import ExpressTunnel, ExpressTunnelManager, TunnelType


class TestDemandTracer:
    """Test demand tracer for optimization opportunities."""

    def test_tracer_creation(self):
        """Test tracer can be created."""
        tracer = DemandTracer()
        assert tracer is not None

    def test_track_demand(self):
        """Test tracking demand patterns."""
        tracer = DemandTracer()
        tracer.track_demand("compute", 100)
        tracer.track_demand("compute", 200)
        tracer.track_demand("compute", 150)
        
        demands = tracer.get_demands()
        assert len(demands) > 0

    def test_detect_hotspots(self):
        """Test detecting hotspots."""
        tracer = DemandTracer()
        
        # Simulate hotspot
        for i in range(100):
            tracer.track_demand("hot_function", i)
        
        hotspots = tracer.detect_hotspots(threshold=50)
        assert len(hotspots) > 0

    def test_identify_patterns(self):
        """Test identifying demand patterns."""
        tracer = DemandTracer()
        
        # Create pattern
        tracer.track_demand("pattern_func", 10)
        tracer.track_demand("pattern_func", 20)
        tracer.track_demand("pattern_func", 30)
        
        patterns = tracer.identify_patterns()
        assert patterns is not None

    def test_find_optimization_opportunities(self):
        """Test finding optimization opportunities."""
        tracer = DemandTracer()
        
        # Create multiple calls
        for i in range(50):
            tracer.track_demand("optimize_me", i)
        
        opportunities = tracer.find_opportunities()
        assert opportunities is not None

    def test_tracer_with_graph(self):
        """Test tracer with dependency graph."""
        tracer = DemandTracer()
        
        # Simulate graph
        tracer.add_dependency("func_a", "func_b")
        tracer.add_dependency("func_b", "func_c")
        
        graph = tracer.get_dependency_graph()
        assert graph is not None


class TestIDartCutter:
    """Test IDart graph cutter for optimization."""

    def test_cutter_creation(self):
        """Test cutter can be created."""
        cutter = IDartCutter()
        assert cutter is not None

    def test_cut_min_cut(self):
        """Test MIN_CUT strategy."""
        cutter = IDartCutter()
        
        # Create sample graph
        nodes = [
            NodeProfile(name="root", cost=100, degree=3),
            NodeProfile(name="leaf1", cost=10, degree=1),
            NodeProfile(name="leaf2", cost=10, degree=1),
        ]
        
        edges = [
            EdgeWeight(source="root", target="leaf1", weight=50),
            EdgeWeight(source="root", target="leaf2", weight=50),
        ]
        
        result = cutter.cut(nodes, edges, strategy=CutStrategy.MIN_CUT)
        assert result is not None

    def test_cut_balanced(self):
        """Test BALANCED strategy."""
        cutter = IDartCutter()
        
        nodes = [
            NodeProfile(name="root", cost=100, degree=4),
            NodeProfile(name="node1", cost=25, degree=1),
            NodeProfile(name="node2", cost=25, degree=1),
            NodeProfile(name="node3", cost=25, degree=1),
            NodeProfile(name="node4", cost=25, degree=1),
        ]
        
        edges = [
            EdgeWeight(source="root", target="node1", weight=30),
            EdgeWeight(source="root", target="node2", weight=30),
            EdgeWeight(source="root", target="node3", weight=30),
            EdgeWeight(source="root", target="node4", weight=30),
        ]
        
        result = cutter.cut(nodes, edges, strategy=CutStrategy.BALANCED)
        assert result is not None

    def test_cut_hotspot(self):
        """Test HOTSPOT strategy."""
        cutter = IDartCutter()
        
        nodes = [
            NodeProfile(name="hotspot", cost=500, degree=5),
            NodeProfile(name="normal", cost=50, degree=1),
        ]
        
        edges = [
            EdgeWeight(source="hotspot", target="normal", weight=100),
        ]
        
        result = cutter.cut(nodes, edges, strategy=CutStrategy.HOTSPOT)
        assert result is not None

    def test_cut_depth_first(self):
        """Test DEPTH_FIRST strategy."""
        cutter = IDartCutter()
        
        nodes = [
            NodeProfile(name="root", cost=100, degree=2),
            NodeProfile(name="child1", cost=50, degree=2),
            NodeProfile(name="child2", cost=50, degree=1),
            NodeProfile(name="grandchild", cost=25, degree=1),
        ]
        
        edges = [
            EdgeWeight(source="root", target="child1", weight=40),
            EdgeWeight(source="root", target="child2", weight=40),
            EdgeWeight(source="child1", target="grandchild", weight=20),
        ]
        
        result = cutter.cut(nodes, edges, strategy=CutStrategy.DEPTH_FIRST)
        assert result is not None

    def test_isolate_hotspots(self):
        """Test hotspot isolation."""
        cutter = IDartCutter()
        
        nodes = [
            NodeProfile(name="hot1", cost=400, degree=3),
            NodeProfile(name="hot2", cost=350, degree=3),
            NodeProfile(name="cold", cost=10, degree=1),
        ]
        
        edges = [
            EdgeWeight(source="hot1", target="hot2", weight=200),
            EdgeWeight(source="hot1", target="cold", weight=50),
            EdgeWeight(source="hot2", target="cold", weight=50),
        ]
        
        result = cutter.isolate_hotspots(nodes, edges, threshold=200)
        assert result is not None

    def test_analyze_graph_complexity(self):
        """Test graph complexity analysis."""
        cutter = IDartCutter()
        
        nodes = [
            NodeProfile(name="root", cost=100, degree=4),
            NodeProfile(name="n1", cost=50, degree=2),
            NodeProfile(name="n2", cost=50, degree=2),
            NodeProfile(name="n3", cost=50, degree=2),
            NodeProfile(name="n4", cost=50, degree=2),
            NodeProfile(name="n5", cost=50, degree=2),
        ]
        
        edges = [
            EdgeWeight(source="root", target="n1", weight=30),
            EdgeWeight(source="root", target="n2", weight=30),
            EdgeWeight(source="root", target="n3", weight=30),
            EdgeWeight(source="root", target="n4", weight=30),
            EdgeWeight(source="root", target="n5", weight=30),
        ]
        
        complexity = cutter.analyze_graph_complexity(nodes, edges)
        assert complexity is not None


class TestExpressTunnel:
    """Test express tunnel for zero-copy optimization."""

    def test_tunnel_creation(self):
        """Test tunnel can be created."""
        tunnel = ExpressTunnel()
        assert tunnel is not None

    def test_tunnel_memory_mode(self):
        """Test tunnel in memory mode."""
        tunnel = ExpressTunnel()
        tunnel.set_mode(TunnelType.MEMORY)
        
        # Create span
        span = tunnel.create_span(size=1024)
        assert span is not None

    def test_tunnel_stream_mode(self):
        """Test tunnel in stream mode."""
        tunnel = ExpressTunnel()
        tunnel.set_mode(TunnelType.STREAM)
        
        # Create stream
        stream = tunnel.create_stream(buffer_size=4096)
        assert stream is not None

    def test_tunnel_shared_mode(self):
        """Test tunnel in shared mode."""
        tunnel = ExpressTunnel()
        tunnel.set_mode(TunnelType.SHARED)
        
        # Create shared buffer
        buffer = tunnel.create_shared_buffer(size=2048)
        assert buffer is not None

    def test_tunnel_direct_mode(self):
        """Test tunnel in direct mode."""
        tunnel = ExpressTunnel()
        tunnel.set_mode(TunnelType.DIRECT)
        
        # Create direct access
        access = tunnel.create_direct_access(offset=0, length=512)
        assert access is not None

    def test_tunnel_zero_copy(self):
        """Test zero-copy optimization."""
        tunnel = ExpressTunnel()
        tunnel.set_mode(TunnelType.MEMORY)
        
        # Enable zero-copy
        tunnel.enable_zero_copy()
        
        span = tunnel.create_span(size=1024)
        assert span is not None

    def test_tunnel_buffer_reuse(self):
        """Test buffer reuse optimization."""
        tunnel = ExpressTunnel()
        tunnel.set_mode(TunnelType.MEMORY)
        
        # Enable buffer reuse
        tunnel.enable_buffer_reuse()
        
        span1 = tunnel.create_span(size=512)
        span2 = tunnel.create_span(size=512)
        
        assert span1 is not None
        assert span2 is not None

    def test_tunnel_stream_merge(self):
        """Test stream merge optimization."""
        tunnel = ExpressTunnel()
        tunnel.set_mode(TunnelType.STREAM)
        
        # Enable stream merge
        tunnel.enable_stream_merge()
        
        stream1 = tunnel.create_stream(buffer_size=1024)
        stream2 = tunnel.create_stream(buffer_size=1024)
        
        assert stream1 is not None
        assert stream2 is not None

    def test_tunnel_memory_coalescing(self):
        """Test memory coalescing optimization."""
        tunnel = ExpressTunnel()
        tunnel.set_mode(TunnelType.MEMORY)
        
        # Enable memory coalescing
        tunnel.enable_memory_coalescing()
        
        spans = [
            tunnel.create_span(size=256) for _ in range(10)
        ]
        
        assert all(s is not None for s in spans)


class TestExpressTunnelManager:
    """Test express tunnel manager for multiple tunnels."""

    def test_manager_creation(self):
        """Test manager can be created."""
        manager = ExpressTunnelManager()
        assert manager is not None

    def test_create_multiple_tunnels(self):
        """Test creating multiple tunnels."""
        manager = ExpressTunnelManager()
        
        tunnels = []
        for i in range(5):
            tunnel = manager.create_tunnel(f"tunnel_{i}")
            tunnels.append(tunnel)
        
        assert len(tunnels) == 5

    def test_tunnel_lifecycle(self):
        """Test tunnel lifecycle management."""
        manager = ExpressTunnelManager()
        
        tunnel = manager.create_tunnel("test_tunnel")
        assert tunnel is not None
        
        # Use tunnel
        span = tunnel.create_span(size=1024)
        assert span is not None
        
        # Close tunnel
        tunnel.close()

    def test_manager_statistics(self):
        """Test manager statistics tracking."""
        manager = ExpressTunnelManager()
        
        # Create and use tunnels
        for i in range(10):
            tunnel = manager.create_tunnel(f"tunnel_{i}")
            tunnel.create_span(size=512)
            tunnel.close()
        
        stats = manager.get_statistics()
        assert stats is not None
        assert stats.total_tunnels_created == 10

    def test_manager_tiering(self):
        """Test automatic tiering of tunnels."""
        manager = ExpressTunnelManager()
        
        # Create tunnels with different usage patterns
        hot_tunnel = manager.create_tunnel("hot")
        hot_tunnel.create_span(size=1024)
        
        cold_tunnel = manager.create_tunnel("cold")
        cold_tunnel.create_span(size=1024)
        
        # Check tiering
        tunnels = manager.get_tunnels()
        assert len(tunnels) == 2

    def test_manager_optimization(self):
        """Test automatic optimization of tunnels."""
        manager = ExpressTunnelManager()
        
        # Create many tunnels
        for i in range(20):
            tunnel = manager.create_tunnel(f"tunnel_{i}")
            tunnel.create_span(size=256)
        
        # Enable optimization
        manager.enable_optimization()
        
        # Check optimized tunnels
        optimized = manager.get_optimized_tunnels()
        assert optimized is not None


class TestIDartIntegration:
    """Test full iDart optimization pipeline integration."""

    def test_full_pipeline(self):
        """Test full iDart optimization pipeline."""
        # Create tracer
        tracer = DemandTracer()
        
        # Simulate program execution
        for i in range(100):
            tracer.track_demand("compute", i)
            tracer.track_demand("process", i)
        
        # Find opportunities
        opportunities = tracer.find_opportunities()
        assert opportunities is not None

    def test_optimization_workflow(self):
        """Test complete optimization workflow."""
        # Trace
        tracer = DemandTracer()
        for i in range(50):
            tracer.track_demand("optimize_func", i)
        
        # Cut graph
        cutter = IDartCutter()
        nodes = [
            NodeProfile(name="optimize_func", cost=500, degree=5),
            NodeProfile(name="helper", cost=50, degree=1),
        ]
        edges = [
            EdgeWeight(source="optimize_func", target="helper", weight=100),
        ]
        
        result = cutter.cut(nodes, edges, strategy=CutStrategy.HOTSPOT)
        assert result is not None

    def test_tunnel_integration(self):
        """Test tunnel integration with optimization."""
        # Create tunnel manager
        manager = ExpressTunnelManager()
        
        # Create optimized tunnel
        tunnel = manager.create_tunnel("optimized")
        tunnel.set_mode(TunnelType.MEMORY)
        tunnel.enable_zero_copy()
        
        # Create span
        span = tunnel.create_span(size=4096)
        assert span is not None
        
        # Close
        tunnel.close()


class TestOptimizationMetrics:
    """Test optimization metrics and analysis."""

    def test_measure_optimization_impact(self):
        """Test measuring optimization impact."""
        tracer = DemandTracer()
        
        # Before optimization
        for i in range(100):
            tracer.track_demand("before_opt", i)
        
        before_count = tracer.get_demand_count("before_opt")
        assert before_count == 100

    def test_calculate_speedup(self):
        """Test calculating speedup from optimization."""
        tracer = DemandTracer()
        
        # Simulate before and after
        for i in range(1000):
            tracer.track_demand("original", i)
        
        for i in range(100):
            tracer.track_demand("optimized", i)
        
        # Calculate ratio
        original_count = tracer.get_demand_count("original")
        optimized_count = tracer.get_demand_count("optimized")
        
        ratio = original_count / optimized_count if optimized_count > 0 else 0
        assert ratio > 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
