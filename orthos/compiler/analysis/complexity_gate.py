"""
Complexity Gate Module for Orthos Compiler
Analyzes code complexity and enforces complexity limits
"""

import ast
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ComplexityType(Enum):
    """Types of complexity metrics"""
    CYCLOMATIC = "cyclomatic"
    HALSTEAD = "halstead"
    MCCABE = "mccabe"
    GOUVEIA = "gouveia"
    VOGEL = "vogel"


@dataclass
class ComplexityResult:
    """Result of complexity analysis"""
    complexity_type: ComplexityType
    value: float
    max_allowed: float
    is_within_limits: bool
    breakdown: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ComplexityViolation:
    """Represents a complexity violation"""
    complexity_type: ComplexityType
    value: float
    max_allowed: float
    location: str
    line_number: int
    recommendations: List[str] = field(default_factory=list)


class CyclomaticValue(int):
    """Integer subclass supporting dict/attribute access .value, ['value'], and int comparisons."""
    @property
    def value(self) -> int:
        return int(self)

    def __getitem__(self, key: Any) -> Any:
        if key == "value":
            return int(self)
        if key == "breakdown":
            return {"base": 1, "decisions": int(self) - 1}
        raise KeyError(key)

    def get(self, key: Any, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default


@dataclass
class HalsteadMetrics:
    """Halstead complexity metrics."""
    n1: int = 1
    n2: int = 1
    N1: int = 1
    N2: int = 1
    vocabulary: int = 2
    length: int = 2
    volume: float = 2.0
    difficulty: float = 1.0
    effort: float = 2.0
    time: float = 0.1
    bugs: float = 0.001

    def __getitem__(self, key: str) -> Any:
        if key == "value":
            return self.difficulty
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    @property
    def value(self) -> float:
        return self.difficulty


class ComplexityMetrics(dict):
    """Complexity metrics container supporting attribute, dict, and numeric operations."""
    def __init__(
        self,
        cyclomatic: int = 1,
        mccabe: int = 1,
        halstead: Optional[HalsteadMetrics] = None,
        filename: str = "<unknown>",
        within_limits: bool = True,
        violations: Optional[List[Any]] = None,
        **kwargs: Any
    ):
        super().__init__(**kwargs)
        self.filename = filename
        self._cyclomatic_val = CyclomaticValue(cyclomatic)
        self._mccabe_val = CyclomaticValue(mccabe)
        self.halstead = halstead or HalsteadMetrics()
        self.within_limits = within_limits
        self.violations = violations or []
        self.operators = self.halstead.n1
        self.operands = self.halstead.n2
        
        # Populate dict keys
        self["filename"] = filename
        self["cyclomatic"] = self._cyclomatic_val
        self["mccabe"] = self._mccabe_val
        self["halstead"] = self.halstead
        self["within_limits"] = within_limits
        self["violations"] = self.violations
        self["operators"] = self.operators
        self["operands"] = self.operands

    @property
    def cyclomatic(self) -> CyclomaticValue:
        return self._cyclomatic_val

    @cyclomatic.setter
    def cyclomatic(self, val: int) -> None:
        self._cyclomatic_val = CyclomaticValue(val)
        self["cyclomatic"] = self._cyclomatic_val

    @property
    def mccabe(self) -> CyclomaticValue:
        return self._mccabe_val

    @mccabe.setter
    def mccabe(self, val: int) -> None:
        self._mccabe_val = CyclomaticValue(val)
        self["mccabe"] = self._mccabe_val

    def __gt__(self, other: Any) -> bool:
        if isinstance(other, (int, float)):
            return int(self._cyclomatic_val) > other
        return super().__gt__(other)

    def __ge__(self, other: Any) -> bool:
        if isinstance(other, (int, float)):
            return int(self._cyclomatic_val) >= other
        return super().__ge__(other)

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, (int, float)):
            return int(self._cyclomatic_val) < other
        return super().__lt__(other)

    def __le__(self, other: Any) -> bool:
        if isinstance(other, (int, float)):
            return int(self._cyclomatic_val) <= other
        return super().__le__(other)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, (int, float)):
            return int(self._cyclomatic_val) == other
        return super().__eq__(other)

    def __int__(self) -> int:
        return int(self._cyclomatic_val)

    def __float__(self) -> float:
        return float(self._cyclomatic_val)


class DecisionPointCounter(ast.NodeVisitor):
    """AST visitor to compute decision points and Halstead symbols."""
    def __init__(self):
        self.decisions = 0
        self.operators: List[str] = []
        self.operands: List[str] = []

    def visit_If(self, node: ast.If):
        self.decisions += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While):
        self.decisions += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        self.decisions += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor):
        self.decisions += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        self.decisions += 1
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp):
        self.decisions += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp):
        self.decisions += max(1, len(node.values) - 1)
        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp):
        self.operators.append(type(node.op).__name__)
        self.generic_visit(node)

    def visit_UnaryOp(self, node: ast.UnaryOp):
        self.operators.append(type(node.op).__name__)
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare):
        for op in node.ops:
            self.operators.append(type(op).__name__)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        self.operators.append("Assign")
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign):
        self.operators.append("AugAssign")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        self.operands.append(node.id)
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant):
        self.operands.append(str(node.value))
        self.generic_visit(node)


class ComplexityAnalyzer:
    """Analyzes code complexity"""
    
    def __init__(self, max_cyclomatic: int = 10, max_mccabe: int = 10):
        self._max_cyclomatic = max_cyclomatic
        self._max_mccabe = max_mccabe
        self._logger = logging.getLogger(__name__)
    
    def analyze(self, code_or_ast: Any, filename: str = "<unknown>") -> ComplexityMetrics:
        """
        Analyze code complexity
        
        Args:
            code_or_ast: Python source code or AST
            filename: Source filename
            
        Returns:
            ComplexityMetrics container
        """
        try:
            tree = None
            code_str = ""
            if isinstance(code_or_ast, str):
                code_str = code_or_ast
                try:
                    tree = ast.parse(code_or_ast)
                except Exception:
                    tree = None
            elif hasattr(code_or_ast, 'tree') and code_or_ast.tree is not None:
                tree = code_or_ast.tree
            elif isinstance(code_or_ast, ast.AST):
                tree = code_or_ast
            elif hasattr(code_or_ast, 'nodes') and code_or_ast.nodes:
                tree = ast.Module(body=list(code_or_ast.nodes), type_ignores=[])

            counter = DecisionPointCounter()
            if tree is not None:
                counter.visit(tree)
                cyclomatic_val = 1 + counter.decisions
                mccabe_val = 1 + counter.decisions
                unique_ops = set(counter.operators)
                if not unique_ops and code_str:
                    for op in ['+', '-', '*', '/', '%', '<', '>', '=', '==', '!=']:
                        if op in code_str:
                            unique_ops.add(op)
                unique_operands = set(counter.operands)
                n1 = max(1, len(unique_ops))
                n2 = max(1, len(unique_operands))
                N1 = max(n1, len(counter.operators))
                N2 = max(n2, len(counter.operands))
            else:
                decisions = 0
                for kw in ['if ', 'elif ', 'for ', 'while ', 'try:', 'except ', 'with ']:
                    decisions += code_str.count(kw)
                cyclomatic_val = 1 + decisions
                mccabe_val = 1 + decisions
                words = code_str.split()
                n1 = max(1, len([w for w in words if w in '+-*/%=<>!']))
                n2 = max(1, len([w for w in words if w not in '+-*/%=<>!']))
                N1 = n1
                N2 = n2

            V = n1 + n2
            L = N1 + N2
            difficulty = float((n1 / 2) * (N2 / (n1 + n2))) if (n1 + n2) > 0 else 1.0
            volume = float(L * (L.bit_length())) if L > 0 else 1.0
            effort = float(volume * difficulty)

            halstead = HalsteadMetrics(
                n1=n1,
                n2=n2,
                N1=N1,
                N2=N2,
                vocabulary=V,
                length=L,
                volume=volume,
                difficulty=difficulty,
                effort=effort
            )

            within_limits = (cyclomatic_val <= self._max_cyclomatic and mccabe_val <= self._max_mccabe)
            violations = []
            if cyclomatic_val > self._max_cyclomatic:
                violations.append(
                    ComplexityViolation(
                        complexity_type=ComplexityType.CYCLOMATIC,
                        value=float(cyclomatic_val),
                        max_allowed=float(self._max_cyclomatic),
                        location=filename,
                        line_number=1,
                        recommendations=self._get_recommendations(cyclomatic_val, self._max_cyclomatic)
                    )
                )
            if mccabe_val > self._max_mccabe:
                violations.append(
                    ComplexityViolation(
                        complexity_type=ComplexityType.MCCABE,
                        value=float(mccabe_val),
                        max_allowed=float(self._max_mccabe),
                        location=filename,
                        line_number=1,
                        recommendations=self._get_recommendations(mccabe_val, self._max_mccabe)
                    )
                )

            metrics = ComplexityMetrics(
                cyclomatic=cyclomatic_val,
                mccabe=mccabe_val,
                halstead=halstead,
                filename=filename,
                within_limits=within_limits,
                violations=violations
            )
            return metrics
            
        except Exception as e:
            self._logger.error(f"Complexity analysis error: {e}")
            raise
    
    def _analyze_cyclomatic(self, code: str) -> Dict:
        """Calculate cyclomatic complexity (legacy dict method)"""
        metrics = self.analyze(code)
        return {
            "value": int(metrics.cyclomatic),
            "max_allowed": self._max_cyclomatic,
            "is_within_limits": metrics.cyclomatic <= self._max_cyclomatic,
            "breakdown": {"decisions": int(metrics.cyclomatic) - 1, "base": 1}
        }

    def _analyze_mccabe(self, code: str) -> Dict:
        """Calculate McCabe complexity (legacy dict method)"""
        metrics = self.analyze(code)
        return {
            "value": int(metrics.mccabe),
            "max_allowed": self._max_mccabe,
            "is_within_limits": metrics.mccabe <= self._max_mccabe,
            "breakdown": {"base": 1, "weighted": int(metrics.mccabe) - 1}
        }

    def _analyze_halstead(self, code: str) -> Dict:
        """Calculate Halstead complexity metrics (legacy dict method)"""
        metrics = self.analyze(code)
        h = metrics.halstead
        return {
            "value": h.difficulty,
            "max_allowed": 100.0,
            "is_within_limits": h.difficulty <= 100.0,
            "breakdown": {
                "n1": h.n1,
                "n2": h.n2,
                "V": h.vocabulary,
                "L": h.length,
                "N1": h.N1,
                "N2": h.N2,
                "difficulty": h.difficulty,
                "volume": h.volume
            }
        }
    
    def _get_recommendations(self, value: float, max_allowed: float) -> List[str]:
        """Generate recommendations for reducing complexity"""
        recommendations = []
        
        if value > max_allowed * 1.5:
            recommendations.append(
                "Consider refactoring into smaller functions"
            )
            recommendations.append(
                "Extract complex logic into separate methods"
            )
        
        if value > max_allowed * 1.2:
            recommendations.append(
                "Reduce number of conditional branches"
            )
            recommendations.append(
                "Consider using early returns instead of nested conditionals"
            )
        
        if value > max_allowed:
            recommendations.append(
                "Split large functions into smaller, focused functions"
            )
            recommendations.append(
                "Use guard clauses to reduce nesting"
            )
            recommendations.append(
                "Consider using polymorphism to reduce if-else chains"
            )
        
        return recommendations
    
    def get_complexity_score(self, code: str) -> float:
        """
        Get overall complexity score (0-100)
        
        Returns:
            Complexity score where 0 is simplest, 100 is most complex
        """
        try:
            cyclomatic = self._analyze_cyclomatic(code)
            mccabe = self._analyze_mccabe(code)
            
            # Weighted average
            score = (
                cyclomatic["value"] / self._max_cyclomatic * 40 +
                mccabe["value"] / self._max_mccabe * 60
            )
            
            return min(100.0, max(0.0, score))
            
        except Exception as e:
            self._logger.error(f"Complexity score error: {e}")
            return 100.0
    
    def is_acceptable(self, code: str) -> bool:
        """Check if code is within acceptable complexity limits"""
        try:
            results = self.analyze(code)
            return results["within_limits"]
        except Exception as e:
            self._logger.error(f"Acceptability check error: {e}")
            return False


class ComplexityGate:
    """Enforces complexity limits during compilation"""
    
    def __init__(self, analyzer: ComplexityAnalyzer = None):
        self._analyzer = analyzer or ComplexityAnalyzer()
        self._logger = logging.getLogger(__name__)
    
    def check(self, code: str, filename: str = "<unknown>") -> Tuple[bool, Dict]:
        """
        Check code against complexity limits
        
        Args:
            code: Python source code
            filename: Source filename
            
        Returns:
            Tuple of (is_acceptable, analysis_results)
        """
        try:
            results = self._analyzer.analyze(code, filename)
            is_acceptable = results["within_limits"]
            
            if is_acceptable is False:
                self._logger.warning(
                    f"Complexity gate failed for {filename}: "
                    f"violations={len(results['violations'])}"
                )
            
            return is_acceptable, results
            
        except Exception as e:
            self._logger.error(f"Complexity gate check error: {e}")
            return False, {"error": str(e)}
    
    def get_score(self, code: str) -> float:
        """Get complexity score for code"""
        return self._analyzer.get_complexity_score(code)
    
    def is_within_limits(self, code: str) -> bool:
        """Quick check if code is within limits"""
        return self._analyzer.is_acceptable(code)


# Singleton instance
_gate_instance: Optional[ComplexityGate] = None


def get_complexity_gate() -> ComplexityGate:
    """Get or create complexity gate singleton"""
    global _gate_instance
    if _gate_instance is None:
        _gate_instance = ComplexityGate()
    return _gate_instance


if __name__ == "__main__":
    # Test complexity analyzer
    code = """
def complex_function(a, b, c, d, e):
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        return a + b + c + d + e
                    else:
                        return 0
                else:
                    return 0
            else:
                return 0
        else:
            return 0
    else:
        return 0

for i in range(10):
    for j in range(10):
        for k in range(10):
            if i + j + k > 15:
                print(i, j, k)
            else:
                print(i, j, k)

try:
    result = 1 / 0
except ZeroDivisionError:
    result = 0
finally:
    print("Done")

with open('file.txt') as f:
    content = f.read()

def inner(x):
    return x * 2

result = [inner(i) for i in range(10)]
"""
    
    analyzer = ComplexityAnalyzer(max_cyclomatic=10, max_mccabe=10)
    results = analyzer.analyze(code, "test.py")
    
    print(f"Filename: {results['filename']}")
    print(f"Within limits: {results['within_limits']}")
    print(f"\nCyclomatic complexity: {results['cyclomatic']['value']}")
    print(f"  Max allowed: {results['cyclomatic']['max_allowed']}")
    print(f"  Is within limits: {results['cyclomatic']['is_within_limits']}")
    
    print(f"\nMcCabe complexity: {results['mccabe']['value']}")
    print(f"  Max allowed: {results['mccabe']['max_allowed']}")
    print(f"  Is within limits: {results['mccabe']['is_within_limits']}")
    
    print(f"\nHalstead difficulty: {results['halstead']['value']}")
    print(f"  Max allowed: {results['halstead']['max_allowed']}")
    
    print(f"\nViolations: {len(results['violations'])}")
    for violation in results['violations']:
        print(f"  - {violation.complexity_type.value}: "
              f"{violation.value} > {violation.max_allowed}")
    
    print(f"\nRecommendations:")
    for v in results['violations']:
        for rec in v.recommendations:
            print(f"  - {rec}")
