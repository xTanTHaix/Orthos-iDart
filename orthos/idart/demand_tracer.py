"""
Demand Tracer for iDart Optimization
Tracks demand patterns in code for optimization opportunities
"""

import logging
import ast
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class DemandPattern:
    """Represents a demand pattern in code"""
    pattern_type: str
    frequency: int
    locations: List[int] = field(default_factory=list)
    variables: List[str] = field(default_factory=list)


@dataclass
class OptimizationOpportunity:
    """Represents an optimization opportunity"""
    location: int
    pattern: str
    potential_savings: float
    recommendation: str


@dataclass
class DemandTracerResult:
    """Result of demand tracing"""
    patterns: List[DemandPattern] = field(default_factory=list)
    opportunities: List[OptimizationOpportunity] = field(default_factory=list)
    total_demand: int = 0
    hot_spots: List[int] = field(default_factory=list)


class DemandTracer:
    """
    Traces demand patterns in code for optimization.
    
    Identifies:
    - Frequently accessed variables
    - Hot loops and branches
    - Memory access patterns
    - Computation hotspots
    """
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._demands: Dict[str, List[int]] = defaultdict(list)
        self._dependencies: Dict[str, Set[str]] = defaultdict(set)

    def track_demand(self, name: str, count: int) -> None:
        """Track demand for a given operation or function."""
        self._demands[name].append(count)

    def get_demands(self) -> Dict[str, List[int]]:
        """Get tracked demands."""
        return self._demands

    def get_demand_count(self, name: str) -> int:
        """Get the total demand count for a given name."""
        return len(self._demands.get(name, []))

    def detect_hotspots(self, threshold: float = 50) -> List[str]:
        """Detect hotspots where demand exceeds threshold."""
        hotspots = []
        for name, counts in self._demands.items():
            if counts and (max(counts) >= threshold or (sum(counts) / len(counts)) >= threshold):
                hotspots.append(name)
        return hotspots

    def identify_patterns(self) -> List[Dict[str, Any]]:
        """Identify demand patterns from tracked runtime demands."""
        patterns = []
        for name, counts in self._demands.items():
            patterns.append({
                "name": name,
                "frequency": len(counts),
                "total": sum(counts),
                "avg": sum(counts) / len(counts) if counts else 0
            })
        return patterns

    def find_opportunities(self) -> List[Dict[str, Any]]:
        """Find optimization opportunities from tracked runtime demands."""
        opps = []
        for name, counts in self._demands.items():
            if len(counts) >= 10 or sum(counts) >= 50:
                opps.append({
                    "name": name,
                    "type": "HOT_PATH",
                    "savings_potential": 0.3,
                    "recommendation": f"Inline or cache {name}"
                })
        return opps

    def add_dependency(self, source: str, target: str) -> None:
        """Add a dependency relationship."""
        self._dependencies[source].add(target)

    def get_dependency_graph(self) -> Dict[str, Set[str]]:
        """Get the dependency graph."""
        return dict(self._dependencies)
    
    def detect_patterns(self, code: str) -> List[DemandPattern]:
        """
        Detect demand patterns in source code.

        Args:
            code: Python source code string

        Returns:
            List of detected DemandPattern objects
        """
        result = self.trace(code)
        return result.patterns

    def trace(self, code: str, filename: str = "<unknown>") -> DemandTracerResult:
        """
        Trace demand patterns in code.
        
        Args:
            code: Python source code
            filename: Source filename
            
        Returns:
            DemandTracerResult with patterns and opportunities
        """
        try:
            logger.info(f"Tracing demand patterns in {filename}")
            
            result = DemandTracerResult()
            
            # Parse code
            tree = ast.parse(code)
            
            # Find patterns
            patterns = self._find_patterns(tree)
            result.patterns = patterns
            
            # Find opportunities
            opportunities = self._find_opportunities(tree, patterns)
            result.opportunities = opportunities
            
            # Calculate total demand
            result.total_demand = sum(p.frequency for p in patterns)
            
            # Find hot spots
            result.hot_spots = self._find_hot_spots(tree)
            
            logger.info(f"Demand tracing complete: {len(patterns)} patterns, "
                      f"{len(opportunities)} opportunities")
            
            return result
            
        except Exception as e:
            logger.error(f"Demand tracing error: {e}")
            return DemandTracerResult(
                patterns=[],
                opportunities=[],
                total_demand=0,
                hot_spots=[]
            )
    
    def _find_patterns(self, tree: ast.AST) -> List[DemandPattern]:
        """Find demand patterns in code."""
        patterns = []
        
        # Track variable access frequency
        var_access: Dict[str, int] = defaultdict(int)
        var_locations: Dict[str, List[int]] = defaultdict(list)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                var_access[node.id] += 1
                var_locations[node.id].append(node.lineno)
            
            elif isinstance(node, ast.Attribute):
                # Track attribute access
                attr_name = node.attr
                var_access[attr_name] += 1
                var_locations[attr_name].append(node.lineno)
        
        # Create patterns for frequently accessed variables
        for var_name, freq in sorted(var_access.items(), key=lambda x: -x[1]):
            if freq >= 3:  # Threshold for "frequent"
                patterns.append(DemandPattern(
                    pattern_type="VARIABLE_ACCESS",
                    frequency=freq,
                    locations=var_locations[var_name][:10],  # Limit locations
                    variables=[var_name]
                ))
        
        # Find loop patterns
        loops = self._find_loops(tree)
        for loop in loops:
            patterns.append(DemandPattern(
                pattern_type="LOOP_ITERATION",
                frequency=loop.count,
                locations=[loop.start_line],
                variables=loop.variables
            ))
        
        return patterns
    
    def _find_loops(self, tree: ast.AST) -> List[Dict]:
        """Find loop constructs."""
        loops = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                loop_info = {
                    'start_line': node.lineno,
                    'count': 0,  # Would need runtime info
                    'variables': []
                }
                
                # Extract loop variables
                if isinstance(node, ast.For):
                    if node.target:
                        loop_info['variables'].append(ast.dump(node.target))
                
                loops.append(loop_info)
        
        return loops
    
    def _find_opportunities(self, tree: ast.AST,
                          patterns: List[DemandPattern]) -> List[OptimizationOpportunity]:
        """Find optimization opportunities based on patterns."""
        opportunities = []
        
        for pattern in patterns:
            if pattern.pattern_type == "VARIABLE_ACCESS":
                if pattern.frequency > 10:
                    opportunities.append(OptimizationOpportunity(
                        location=pattern.locations[0] if pattern.locations else 0,
                        pattern="HIGH_VARIABLE_ACCESS",
                        potential_savings=0.15,
                        recommendation=f"Consider caching {pattern.variables[0]}"
                    ))
            
            elif pattern.pattern_type == "LOOP_ITERATION":
                if pattern.frequency > 100:
                    opportunities.append(OptimizationOpportunity(
                        location=pattern.locations[0] if pattern.locations else 0,
                        pattern="HOT_LOOP",
                        potential_savings=0.25,
                        recommendation="Consider loop unrolling or vectorization"
                    ))
        
        return opportunities
    
    def _find_hot_spots(self, tree: ast.AST) -> List[int]:
        """Find hot spots in code."""
        hot_spots = []
        
        # Lines with many operations
        line_operations: Dict[int, int] = defaultdict(int)
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.BinOp, ast.UnaryOp, ast.Call, ast.If)):
                line_operations[node.lineno] += 1
        
        # Lines with high operation count
        for line, count in sorted(line_operations.items(), key=lambda x: -x[1]):
            if count >= 3:
                hot_spots.append(line)
        
        return hot_spots[:10]  # Top 10 hot spots
    
    def is_hot(self, code: str) -> bool:
        """Quick check if code has hot patterns."""
        result = self.trace(code)
        return len(result.hot_spots) > 0 or any(
            p.frequency > 50 for p in result.patterns
        )
    
    def get_summary(self, code: str) -> Dict[str, Any]:
        """Get summary of demand tracing."""
        result = self.trace(code)
        
        return {
            'total_demand': result.total_demand,
            'patterns_count': len(result.patterns),
            'opportunities_count': len(result.opportunities),
            'hot_spots_count': len(result.hot_spots),
            'patterns': [
                {
                    'type': p.pattern_type,
                    'frequency': p.frequency,
                    'variables': p.variables
                }
                for p in result.patterns[:10]
            ]
        }


# Singleton instance
_tracer_instance: Optional[DemandTracer] = None


def get_demand_tracer() -> DemandTracer:
    """Get or create demand tracer singleton."""
    global _tracer_instance
    if _tracer_instance is None:
        _tracer_instance = DemandTracer()
    return _tracer_instance


if __name__ == "__main__":
    # Test demand tracer
    tracer = get_demand_tracer()
    
    code = """
def hot_function(n):
    total = 0
    for i in range(n):
        for j in range(n):
            total += i * j
            data[i][j] = total  # Frequent access
    
    result = []
    for i in range(n):
        for j in range(n):
            result.append(data[i][j] * 2)
    
    return sum(result)

def cold_function(x):
    return x + 1
"""
    
    print("Demand tracing summary:")
    print(tracer.get_summary(code))
    
    print("\nHot spots:", tracer.get_summary(code)['hot_spots_count'])
