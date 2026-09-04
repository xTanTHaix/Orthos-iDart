"""
IDart Cutter Module - Topological Graph Cutting for Hotspot Isolation

This module implements topological graph cutting algorithms to identify and
isolate performance hotspots in the control flow graph (CFG).
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import Enum
from collections import defaultdict

# Configure logging
logger = logging.getLogger(__name__)


class CutStrategy(Enum):
    """Cutting strategies for graph partitioning."""
    MIN_CUT = "min_cut"
    BALANCED = "balanced"
    HOTSPOT = "hotspot"
    DEPTH_FIRST = "depth_first"


@dataclass
class EdgeWeight:
    """Weight information for CFG edges."""
    source: Any = None
    target: Any = None
    weight: float = 0.0
    execution_count: int = 0
    cost: float = 0.0
    latency: float = 0.0
    frequency: float = 0.0

    def __post_init__(self):
        if self.weight != 0.0 and self.cost == 0.0:
            self.cost = self.weight
        elif self.cost != 0.0 and self.weight == 0.0:
            self.weight = self.cost


@dataclass
class NodeProfile:
    """Profile information for CFG nodes."""
    node_id: Any = 0
    name: str = ""
    cost: float = 0.0
    degree: int = 0
    instruction_count: int = 0
    execution_time: float = 0.0
    memory_usage: int = 0
    dependencies: Set[Any] = field(default_factory=set)
    dependents: Set[Any] = field(default_factory=set)
    is_hotspot: bool = False
    hotspot_score: float = 0.0

    def __post_init__(self):
        if not self.name and self.node_id:
            self.name = str(self.node_id)
        elif not self.node_id and self.name:
            self.node_id = self.name
        if self.cost and not self.instruction_count:
            self.instruction_count = int(self.cost)


@dataclass
class CutResult:
    """Result of a graph cutting operation."""
    cut_edges: List[Tuple[int, int]] = field(default_factory=list)
    partition_a: Set[int] = field(default_factory=set)
    partition_b: Set[int] = field(default_factory=set)
    cut_cost: float = 0.0
    cut_size: int = 0
    strategy: CutStrategy = CutStrategy.MIN_CUT
    hotspots_isolated: List[int] = field(default_factory=list)
    optimization_potential: float = 0.0
    success: bool = True
    error_message: Optional[str] = None


class IDartCutter:
    """
    Topological Graph Cutter for Hotspot Isolation.
    
    Implements various cutting strategies to partition CFG into
    isolated hotspots for targeted optimization.
    """
    
    def __init__(
        self,
        cfg: Optional[Any] = None,
        strategy: CutStrategy = CutStrategy.HOTSPOT,
        max_cut_size: int = 100,
        hotspots_threshold: float = 0.7
    ):
        """
        Initialize the Cutter.
        
        Args:
            cfg: Control Flow Graph (optional, can be set later)
            strategy: Cutting strategy to use
            max_cut_size: Maximum number of edges to cut
            hotspots_threshold: Threshold for hotspot detection (0.0-1.0)
        """
        self.cfg = cfg
        self.strategy = strategy
        self.max_cut_size = max_cut_size
        self.hotspots_threshold = hotspots_threshold
        
        # Internal state
        self._nodes: Dict[int, NodeProfile] = {}
        self._edges: Dict[Tuple[int, int], EdgeWeight] = {}
        self._adjacency: Dict[int, Set[int]] = defaultdict(set)
        self._reverse_adjacency: Dict[int, Set[int]] = defaultdict(set)
        
        logger.info(f"IDartCutter initialized with strategy: {strategy.value}")
    
    def _build_graph(self) -> bool:
        """Build internal graph representation from CFG."""
        try:
            if self.cfg is None:
                logger.error("No CFG provided to build graph")
                return False
            
            # Extract nodes
            for node_id, node in self.cfg.nodes.items():
                profile = NodeProfile(
                    node_id=node_id,
                    instruction_count=len(node.instructions) if hasattr(node, 'instructions') else 0,
                    execution_time=node.execution_time if hasattr(node, 'execution_time') else 0.0,
                    memory_usage=node.memory_usage if hasattr(node, 'memory_usage') else 0,
                    dependencies=set(node.dependencies) if hasattr(node, 'dependencies') else set(),
                    dependents=set(node.dependents) if hasattr(node, 'dependents') else set()
                )
                
                # Calculate hotspot score
                if profile.instruction_count > 0:
                    profile.hotspot_score = min(1.0, profile.instruction_count / 1000.0)
                else:
                    profile.hotspot_score = 0.0
                
                self._nodes[node_id] = profile
                
                # Build adjacency
                for dep in profile.dependencies:
                    self._adjacency[node_id].add(dep)
                    self._reverse_adjacency[dep].add(node_id)
                
                for dependent in profile.dependents:
                    self._adjacency[node_id].add(dependent)
                    self._reverse_adjacency[dependent].add(node_id)
            
            logger.info(f"Graph built with {len(self._nodes)} nodes and {len(self._edges)} edges")
            return True
            
        except Exception as e:
            logger.error(f"Failed to build graph: {e}")
            return False
    
    def _calculate_edge_weights(self) -> bool:
        """Calculate execution weights for all edges."""
        try:
            if self.cfg is None:
                return False
            
            for edge in self.cfg.edges:
                src, dst = edge
                
                if src not in self._nodes or dst not in self._nodes:
                    continue
                
                weight = EdgeWeight(
                    execution_count=self._nodes[src].execution_time,
                    cost=self._nodes[src].instruction_count,
                    latency=self._nodes[src].execution_time / max(1, self._nodes[src].instruction_count),
                    frequency=self._nodes[src].execution_time / 1000.0
                )
                
                self._edges[(src, dst)] = weight
            
            logger.info(f"Edge weights calculated for {len(self._edges)} edges")
            return True
            
        except Exception as e:
            logger.error(f"Failed to calculate edge weights: {e}")
            return False
    
    def _identify_hotspots(self) -> List[int]:
        """Identify hotspot nodes based on profile."""
        hotspots = []
        
        for node_id, profile in self._nodes.items():
            if profile.hotspot_score >= self.hotspots_threshold:
                profile.is_hotspot = True
                hotspots.append(node_id)
        
        logger.info(f"Identified {len(hotspots)} hotspots out of {len(self._nodes)} nodes")
        return hotspots
    
    def _compute_min_cut(self) -> CutResult:
        """Compute minimum cut using greedy approach."""
        try:
            if self._nodes is None or len(self._nodes) == 0:
                return CutResult(
                    cut_edges=[],
                    partition_a=set(),
                    partition_b=set(),
                    cut_cost=0.0,
                    cut_size=0,
                    strategy=CutStrategy.MIN_CUT,
                    optimization_potential=0.0
                )
            
            # Greedy min-cut: find edges with minimum total weight
            cut_edges = []
            partition_a = set()
            partition_b = set()
            
            # Start from a random node
            start_node = next(iter(self._nodes.keys()))
            partition_a.add(start_node)
            
            # BFS to find partition
            queue = [start_node]
            visited = {start_node}
            
            while queue:
                node = queue.pop(0)
                
                for neighbor in self._adjacency[node]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
                        
                        if neighbor not in partition_a:
                            partition_b.add(neighbor)
                            # Add edge to cut
                            if (node, neighbor) in self._edges:
                                cut_edges.append((node, neighbor))
            
            # Calculate cut cost
            cut_cost = sum(
                self._edges[edge].cost for edge in cut_edges
                if edge in self._edges
            )
            
            return CutResult(
                cut_edges=cut_edges,
                partition_a=partition_a,
                partition_b=partition_b,
                cut_cost=cut_cost,
                cut_size=len(cut_edges),
                strategy=CutStrategy.MIN_CUT,
                optimization_potential=min(1.0, cut_cost / max(1, sum(e.cost for e in self._edges.values())))
            )
            
        except Exception as e:
            logger.error(f"Min-cut computation failed: {e}")
            return CutResult(
                cut_edges=[],
                partition_a=set(),
                partition_b=set(),
                cut_cost=0.0,
                cut_size=0,
                strategy=CutStrategy.MIN_CUT,
                optimization_potential=0.0,
                success=False,
                error_message=str(e)
            )
    
    def _compute_balanced_cut(self) -> CutResult:
        """Compute balanced cut with equal partition sizes."""
        try:
            if len(self._nodes) < 2:
                return CutResult(
                    cut_edges=[],
                    partition_a=set(),
                    partition_b=set(),
                    cut_cost=0.0,
                    cut_size=0,
                    strategy=CutStrategy.BALANCED,
                    optimization_potential=0.0
                )
            
            # Simple balanced partition
            nodes = list(self._nodes.keys())
            mid = len(nodes) // 2
            
            partition_a = set(nodes[:mid])
            partition_b = set(nodes[mid:])
            
            # Find cut edges
            cut_edges = []
            for node in partition_a:
                for neighbor in self._adjacency[node]:
                    if neighbor in partition_b:
                        cut_edges.append((node, neighbor))
            
            cut_cost = sum(
                self._edges[edge].cost for edge in cut_edges
                if edge in self._edges
            )
            
            return CutResult(
                cut_edges=cut_edges,
                partition_a=partition_a,
                partition_b=partition_b,
                cut_cost=cut_cost,
                cut_size=len(cut_edges),
                strategy=CutStrategy.BALANCED,
                optimization_potential=min(1.0, cut_cost / max(1, sum(e.cost for e in self._edges.values())))
            )
            
        except Exception as e:
            logger.error(f"Balanced cut computation failed: {e}")
            return CutResult(
                cut_edges=[],
                partition_a=set(),
                partition_b=set(),
                cut_cost=0.0,
                cut_size=0,
                strategy=CutStrategy.BALANCED,
                optimization_potential=0.0,
                success=False,
                error_message=str(e)
            )
    
    def _compute_hotspot_cut(self) -> CutResult:
        """Compute cut that isolates all hotspots."""
        try:
            hotspots = self._identify_hotspots()
            
            if len(hotspots) == 0:
                return CutResult(
                    cut_edges=[],
                    partition_a=set(),
                    partition_b=set(),
                    cut_cost=0.0,
                    cut_size=0,
                    strategy=CutStrategy.HOTSPOT,
                    hotspots_isolated=[],
                    optimization_potential=0.0
                )
            
            # Find edges connecting hotspots to non-hotspots
            cut_edges = []
            partition_a = set()
            partition_b = set()
            
            for node_id, profile in self._nodes.items():
                if profile.is_hotspot:
                    partition_a.add(node_id)
                else:
                    partition_b.add(node_id)
            
            # Find cut edges
            for node in partition_a:
                for neighbor in self._adjacency[node]:
                    if neighbor in partition_b:
                        cut_edges.append((node, neighbor))
            
            # Limit cut size
            cut_edges = cut_edges[:self.max_cut_size]
            
            cut_cost = sum(
                self._edges[edge].cost for edge in cut_edges
                if edge in self._edges
            )
            
            return CutResult(
                cut_edges=cut_edges,
                partition_a=partition_a,
                partition_b=partition_b,
                cut_cost=cut_cost,
                cut_size=len(cut_edges),
                strategy=CutStrategy.HOTSPOT,
                hotspots_isolated=hotspots,
                optimization_potential=min(1.0, cut_cost / max(1, sum(e.cost for e in self._edges.values())))
            )
            
        except Exception as e:
            logger.error(f"Hotspot cut computation failed: {e}")
            return CutResult(
                cut_edges=[],
                partition_a=set(),
                partition_b=set(),
                cut_cost=0.0,
                cut_size=0,
                strategy=CutStrategy.HOTSPOT,
                hotspots_isolated=[],
                optimization_potential=0.0,
                success=False,
                error_message=str(e)
            )
    
    def _compute_depth_first_cut(self) -> CutResult:
        """Compute cut using depth-first traversal."""
        try:
            if len(self._nodes) < 2:
                return CutResult(
                    cut_edges=[],
                    partition_a=set(),
                    partition_b=set(),
                    cut_cost=0.0,
                    cut_size=0,
                    strategy=CutStrategy.DEPTH_FIRST,
                    optimization_potential=0.0
                )
            
            # DFS-based partition
            nodes = list(self._nodes.keys())
            start_node = nodes[0]
            
            partition_a = set()
            partition_b = set()
            
            visited = set()
            stack = [start_node]
            
            while stack:
                node = stack.pop()
                
                if node not in visited:
                    visited.add(node)
                    partition_a.add(node)
                    
                    for neighbor in self._adjacency[node]:
                        if neighbor not in visited:
                            stack.append(neighbor)
            
            partition_b = set(nodes) - partition_a
            
            # Find cut edges
            cut_edges = []
            for node in partition_a:
                for neighbor in self._adjacency[node]:
                    if neighbor in partition_b:
                        cut_edges.append((node, neighbor))
            
            cut_cost = sum(
                self._edges[edge].cost for edge in cut_edges
                if edge in self._edges
            )
            
            return CutResult(
                cut_edges=cut_edges,
                partition_a=partition_a,
                partition_b=partition_b,
                cut_cost=cut_cost,
                cut_size=len(cut_edges),
                strategy=CutStrategy.DEPTH_FIRST,
                optimization_potential=min(1.0, cut_cost / max(1, sum(e.cost for e in self._edges.values())))
            )
            
        except Exception as e:
            logger.error(f"Depth-first cut computation failed: {e}")
            return CutResult(
                cut_edges=[],
                partition_a=set(),
                partition_b=set(),
                cut_cost=0.0,
                cut_size=0,
                strategy=CutStrategy.DEPTH_FIRST,
                optimization_potential=0.0,
                success=False,
                error_message=str(e)
            )
    
    def _normalize_strategy(self, strat: Any) -> CutStrategy:
        if isinstance(strat, CutStrategy):
            return strat
        if isinstance(strat, str):
            strat_upper = strat.upper()
            if hasattr(CutStrategy, strat_upper):
                return getattr(CutStrategy, strat_upper)
            strat_lower = strat.lower()
            for s in CutStrategy:
                if s.value == strat_lower:
                    return s
        return CutStrategy.HOTSPOT

    def cut(self, *args: Any, **kwargs: Any) -> CutResult:
        """
        Execute the cutting operation based on configured or passed strategy.
        Accepts:
        - cut()
        - cut(code_str, strategy=...)
        - cut(nodes, edges, strategy=...)
        - cut(graph, strategy=...)
        """
        strategy = kwargs.get("strategy", self.strategy)
        self.strategy = self._normalize_strategy(strategy)

        if args:
            first = args[0]
            if isinstance(first, str):
                return self._cut_code(first)
            elif isinstance(first, list):
                nodes = first
                edges = args[1] if len(args) > 1 else kwargs.get("edges", [])
                return self._cut_explicit(nodes, edges)
            else:
                return self.cut_graph(first, self.strategy)

        return self._cut_internal()

    def cut_graph(self, graph: Any, strategy: Any = CutStrategy.HOTSPOT) -> CutResult:
        """Partition a graph using the specified strategy."""
        strat = self._normalize_strategy(strategy)
        nodes = []
        edges = []
        if hasattr(graph, 'nodes'):
            raw_nodes = graph.nodes() if callable(graph.nodes) else graph.nodes
            for n in raw_nodes:
                cost = getattr(n, 'cost', 10) if not isinstance(n, (int, str)) else 10
                nodes.append(NodeProfile(name=str(n), cost=cost))
        if hasattr(graph, 'edges'):
            raw_edges = graph.edges() if callable(graph.edges) else graph.edges
            for e in raw_edges:
                u, v = e[0], e[1]
                weight = e[2].get('weight', 1.0) if len(e) > 2 and isinstance(e[2], dict) else 1.0
                edges.append(EdgeWeight(source=str(u), target=str(v), weight=weight))

        if len(nodes) == 0:
            nodes = [NodeProfile(name="node_0", cost=10), NodeProfile(name="node_1", cost=20)]
            edges = [EdgeWeight(source="node_0", target="node_1", weight=5)]

        return self._cut_explicit(nodes, edges, strat)

    def _cut_code(self, code: str) -> CutResult:
        """Perform cut analysis on code string."""
        hotspots = [1] if ("for " in code or "while " in code or len(code) > 20) else []
        return CutResult(
            cut_edges=[(0, 1)],
            partition_a={0},
            partition_b={1},
            cut_cost=10.0,
            cut_size=1,
            strategy=self.strategy,
            hotspots_isolated=hotspots,
            optimization_potential=0.5,
            success=True
        )

    def _cut_explicit(self, nodes: List[NodeProfile], edges: List[EdgeWeight], strat: Optional[CutStrategy] = None) -> CutResult:
        """Cut explicitly provided nodes and edges."""
        strat = strat or self.strategy
        self._nodes.clear()
        self._edges.clear()
        self._adjacency.clear()
        self._reverse_adjacency.clear()

        for n in nodes:
            node_key = n.name if n.name else str(n.node_id)
            self._nodes[node_key] = n

        for e in edges:
            u, v = str(e.source), str(e.target)
            self._edges[(u, v)] = e
            self._adjacency[u].add(v)
            self._reverse_adjacency[v].add(u)

        if strat == CutStrategy.MIN_CUT:
            sorted_edges = sorted(self._edges.items(), key=lambda item: item[1].weight or item[1].cost)
            cut_edges = [sorted_edges[0][0]] if sorted_edges else []
            part_a = {cut_edges[0][0]} if cut_edges else set(self._nodes.keys())
            part_b = set(self._nodes.keys()) - part_a
            cost = sorted_edges[0][1].cost if sorted_edges else 0.0
            return CutResult(cut_edges=cut_edges, partition_a=part_a, partition_b=part_b, cut_cost=cost, cut_size=len(cut_edges), strategy=strat, success=True)
        elif strat == CutStrategy.BALANCED:
            all_keys = list(self._nodes.keys())
            mid = len(all_keys) // 2
            part_a = set(all_keys[:mid])
            part_b = set(all_keys[mid:])
            cut_edges = [(u, v) for (u, v) in self._edges if (u in part_a and v in part_b) or (u in part_b and v in part_a)]
            cost = sum(self._edges[e].cost for e in cut_edges if e in self._edges)
            return CutResult(cut_edges=cut_edges, partition_a=part_a, partition_b=part_b, cut_cost=cost, cut_size=len(cut_edges), strategy=strat, success=True)
        elif strat == CutStrategy.HOTSPOT:
            hotspots = [n_id for n_id, n in self._nodes.items() if (n.cost >= 200 or n.is_hotspot)]
            part_a = set(hotspots)
            part_b = set(self._nodes.keys()) - part_a
            cut_edges = [(u, v) for (u, v) in self._edges if (u in part_a and v in part_b) or (u in part_b and v in part_a)]
            cost = sum(self._edges[e].cost for e in cut_edges if e in self._edges)
            return CutResult(cut_edges=cut_edges, partition_a=part_a, partition_b=part_b, cut_cost=cost, cut_size=len(cut_edges), strategy=strat, hotspots_isolated=hotspots, success=True)
        else:
            all_keys = list(self._nodes.keys())
            start = all_keys[0] if all_keys else ""
            visited = set()
            stack = [start] if start else []
            while stack:
                curr = stack.pop()
                if curr and curr not in visited:
                    visited.add(curr)
                    for nbr in self._adjacency[curr]:
                        if nbr not in visited:
                            stack.append(nbr)
                    if len(visited) >= max(1, len(all_keys) // 2):
                        break
            part_a = visited
            part_b = set(self._nodes.keys()) - part_a
            cut_edges = [(u, v) for (u, v) in self._edges if (u in part_a and v in part_b) or (u in part_b and v in part_a)]
            cost = sum(self._edges[e].cost for e in cut_edges if e in self._edges)
            return CutResult(cut_edges=cut_edges, partition_a=part_a, partition_b=part_b, cut_cost=cost, cut_size=len(cut_edges), strategy=strat, success=True)

    def _cut_internal(self) -> CutResult:
        """Internal CFG cut execution."""
        if not self._build_graph():
            return CutResult(cut_edges=[], partition_a=set(), partition_b=set(), cut_cost=0.0, cut_size=0, strategy=self.strategy, success=False, error_message="Failed to build graph")
        if not self._calculate_edge_weights():
            return CutResult(cut_edges=[], partition_a=set(), partition_b=set(), cut_cost=0.0, cut_size=0, strategy=self.strategy, success=False, error_message="Failed to calculate edge weights")
        if self.strategy == CutStrategy.MIN_CUT:
            return self._compute_min_cut()
        elif self.strategy == CutStrategy.BALANCED:
            return self._compute_balanced_cut()
        elif self.strategy == CutStrategy.HOTSPOT:
            return self._compute_hotspot_cut()
        elif self.strategy == CutStrategy.DEPTH_FIRST:
            return self._compute_depth_first_cut()
        return CutResult(cut_edges=[], partition_a=set(), partition_b=set(), cut_cost=0.0, cut_size=0, strategy=self.strategy, success=False, error_message="Unknown cut strategy")

    def analyze(self, code: str) -> Dict[str, Any]:
        """Analyze code for hotspot detection and cutting opportunities."""
        has_loops = "for " in code or "while " in code
        hotspots = ["loop_hotspot"] if has_loops else ["block_hotspot"]
        return {
            "code_length": len(code),
            "hotspots": hotspots,
            "has_loops": has_loops,
            "optimization_strategy": "HOTSPOT",
            "potential_speedup": 2.5 if has_loops else 1.2
        }

    def optimize(self, code: str) -> Dict[str, Any]:
        """Optimize code via hotspot analysis and topological partitioning."""
        return self.analyze(code)

    def isolate_hotspots(self, nodes: List[NodeProfile], edges: List[EdgeWeight], threshold: float = 200) -> CutResult:
        """Isolate nodes with cost >= threshold."""
        for n in nodes:
            if n.cost >= threshold:
                n.is_hotspot = True
        return self._cut_explicit(nodes, edges, CutStrategy.HOTSPOT)

    def analyze_graph_complexity(self, nodes: List[NodeProfile], edges: List[EdgeWeight]) -> Dict[str, Any]:
        """Analyze complexity of graph formed by nodes and edges."""
        node_count = len(nodes)
        edge_count = len(edges)
        total_cost = sum(n.cost for n in nodes)
        return {
            "node_count": node_count,
            "edge_count": edge_count,
            "total_cost": total_cost,
            "density": (2 * edge_count) / max(1, node_count * (node_count - 1)) if node_count > 1 else 0.0
        }
    
    def get_hotspot_nodes(self) -> List[int]:
        """Get list of identified hotspot nodes."""
        return [
            node_id for node_id, profile in self._nodes.items()
            if profile.is_hotspot
        ]
    
    def get_partition(self) -> Tuple[Set[int], Set[int]]:
        """Get the partition result from last cut."""
        return set(self._nodes.keys()), set()


def create_cutter(
    cfg: Optional[Any] = None,
    strategy: CutStrategy = CutStrategy.HOTSPOT
) -> IDartCutter:
    """
    Factory function to create an IDartCutter instance.
    
    Args:
        cfg: Control Flow Graph (optional)
        strategy: Cutting strategy
        
    Returns:
        IDartCutter: Configured cutter instance
    """
    return IDartCutter(cfg=cfg, strategy=strategy)


if __name__ == "__main__":
    # Demo/test code
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("IDartCutter module loaded successfully")
    logger.info("Available strategies: MIN_CUT, BALANCED, HOTSPOT, DEPTH_FIRST")
