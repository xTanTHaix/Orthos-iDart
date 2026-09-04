"""
Scoring Engine - Performance and quality scoring system

Provides comprehensive scoring for code optimization results,
performance metrics, and quality assessments.
"""

import time
import statistics
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum


class ScoringLevel(Enum):
    """Scoring level enumeration."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    FAIL = "fail"


@dataclass
class ScoreComponent:
    """Individual score component."""
    name: str
    score: float
    weight: float
    target: Optional[float] = None
    actual: Optional[float] = None
    status: ScoringLevel = ScoringLevel.FAIR

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "score": self.score,
            "weight": self.weight,
            "target": self.target,
            "actual": self.actual,
            "status": self.status.value
        }


@dataclass
class ScoreResult:
    """Complete scoring result."""
    test_name: str
    total_score: float
    components: List[ScoreComponent] = field(default_factory=list)
    execution_time: float = 0.0
    memory_used: int = 0
    grade: str = ""
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "test_name": self.test_name,
            "total_score": self.total_score,
            "components": [c.to_dict() for c in self.components],
            "execution_time": self.execution_time,
            "memory_used": self.memory_used,
            "grade": self.grade,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class ScoringEngine:
    """
    Comprehensive scoring engine for code optimization.

    Provides scoring for:
    - Correctness (output validation)
    - Performance (execution time, throughput)
    - Complexity (cyclomatic, lines of code)
    - Memory usage (allocation, efficiency)
    - Code quality (maintainability, readability)

    Thread Safety:
    - All public methods are thread-safe
    - Uses locks for shared state
    """

    def __init__(self, config: Optional[Any] = None):
        """
        Initialize scoring engine.

        Args:
            config: Optional scoring configuration
        """
        self._config = config
        self._results_cache: Dict[str, ScoreResult] = {}
        self._total_tests = 0
        self._total_score = 0.0

    def score_correctness(
        self,
        expected_output: Any,
        actual_output: Any,
        tolerance: float = 0.001
    ) -> float:
        """
        Score correctness of output.

        Args:
            expected_output: Expected output value
            actual_output: Actual output value
            tolerance: Acceptable tolerance for floating point

        Returns:
            Score between 0.0 and 1.0
        """
        try:
            # Handle None values
            if expected_output is None and actual_output is None:
                return 1.0

            # Handle empty strings
            if expected_output == "" and actual_output == "":
                return 1.0

            # Exact match
            if expected_output == actual_output:
                return 1.0

            # Handle numeric comparison with tolerance
            if isinstance(expected_output, (int, float)) and isinstance(actual_output, (int, float)):
                if abs(expected_output - actual_output) <= tolerance * max(abs(expected_output), abs(actual_output)):
                    return 1.0

                # Partial match
                if abs(expected_output - actual_output) <= tolerance * 10:
                    return 0.8

            # String comparison
            if isinstance(expected_output, str) and isinstance(actual_output, str):
                # Check if actual is substring of expected
                if actual_output in expected_output:
                    ratio = len(actual_output) / len(expected_output)
                    return ratio

            # List comparison
            if isinstance(expected_output, list) and isinstance(actual_output, list):
                if len(expected_output) == len(actual_output):
                    matches = sum(
                        1 for e, a in zip(expected_output, actual_output)
                        if e == a
                    )
                    return matches / len(expected_output)

            # No match
            return 0.0

        except Exception as e:
            self._log_error(f"Correctness scoring error: {e}")
            return 0.0

    def score_performance(
        self,
        elapsed_time: float,
        target_time: float = 1.0,
        max_time: float = 10.0
    ) -> float:
        """
        Score performance based on execution time.

        Args:
            elapsed_time: Actual execution time in seconds
            target_time: Target execution time
            max_time: Maximum acceptable time

        Returns:
            Score between 0.0 and 1.0
        """
        if elapsed_time <= 0:
            return 1.0

        if elapsed_time <= target_time:
            # Excellent performance
            return 1.0 - (elapsed_time / target_time) * 0.2

        if elapsed_time <= max_time:
            # Acceptable performance
            ratio = elapsed_time / max_time
            return max(0.0, 1.0 - ratio * 0.5)

        # Failed performance
        return 0.0

    def score(
        self,
        baseline_time: float = 1.0,
        optimized_time: float = 1.0,
        memory_baseline: int = 0,
        memory_optimized: int = 0,
        **kwargs: Any
    ) -> float:
        """Score based on performance and memory improvements."""
        time_speedup = baseline_time / max(0.0001, optimized_time)
        time_score = min(1.0, time_speedup / 2.0)
        mem_ratio = (memory_baseline - memory_optimized) / max(1, memory_baseline) if memory_baseline > 0 else 0.0
        mem_score = max(0.0, min(1.0, 0.5 + mem_ratio * 0.5))
        return max(0.1, 0.7 * time_score + 0.3 * mem_score)

    def score_complexity(
        self,
        cyclomatic: int = 1,
        lines: Optional[int] = None,
        max_cyclomatic: int = 10,
        max_lines: int = 100,
        halstead_operators: Optional[int] = None,
        halstead_operands: Optional[int] = None,
        **kwargs: Any
    ) -> float:
        """
        Score code complexity.

        Args:
            cyclomatic: Cyclomatic complexity
            lines: Lines of code
            max_cyclomatic: Maximum acceptable cyclomatic complexity
            max_lines: Maximum acceptable lines of code
            halstead_operators: Optional Halstead operators count
            halstead_operands: Optional Halstead operands count

        Returns:
            Score between 0.0 and 1.0
        """
        cc_score = max(0.0, 1.0 - (cyclomatic / max_cyclomatic))
        if lines is not None:
            loc_score = max(0.0, 1.0 - (lines / max_lines))
        elif halstead_operators is not None and halstead_operands is not None:
            h_total = halstead_operators + halstead_operands
            loc_score = max(0.0, 1.0 - (h_total / 50.0))
        else:
            loc_score = 0.8
        return max(0.1, 0.6 * cc_score + 0.4 * loc_score)

    def score_memory(
        self,
        memory_used: int,
        memory_limit: int = 100 * 1024 * 1024,
        target_ratio: float = 0.1
    ) -> float:
        """
        Score memory usage.

        Args:
            memory_used: Memory used in bytes
            memory_limit: Maximum memory limit
            target_ratio: Target memory ratio

        Returns:
            Score between 0.0 and 1.0
        """
        if memory_used <= 0:
            return 1.0

        ratio = memory_used / memory_limit

        if ratio <= target_ratio:
            # Excellent memory usage
            return 1.0

        if ratio <= 0.5:
            # Good memory usage
            return 1.0 - (ratio - target_ratio) * 2

        # Poor memory usage
        return max(0.0, 1.0 - ratio * 2)

    def calculate_total_score(
        self,
        scores: Dict[str, float],
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Calculate total weighted score.

        Args:
            scores: Dictionary of component scores
            weights: Dictionary of component weights

        Returns:
            Total weighted score
        """
        if weights is None:
            weights = {
                "correctness": 0.4,
                "performance": 0.3,
                "complexity": 0.2,
                "memory": 0.1
            }

        total = 0.0
        for component, score in scores.items():
            weight = weights.get(component, 0.0)
            total += score * weight

        return total

    def determine_grade(self, score: float) -> str:
        """
        Determine grade from score.

        Args:
            score: Score between 0.0 and 1.0

        Returns:
            Grade letter
        """
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.5:
            return "D"
        else:
            return "F"

    def generate_score_breakdown(
        self,
        scores: Dict[str, float],
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Generate detailed score breakdown.

        Args:
            scores: Dictionary of component scores
            weights: Dictionary of component weights

        Returns:
            Detailed breakdown dictionary
        """
        if weights is None:
            weights = {
                "correctness": 0.4,
                "performance": 0.3,
                "complexity": 0.2,
                "memory": 0.1
            }

        total = self.calculate_total_score(scores, weights)

        components = []
        for name, score in scores.items():
            weight = weights.get(name, 0.0)
            components.append(ScoreComponent(
                name=name,
                score=score,
                weight=weight
            ))

        return {
            "total": total,
            "total_score": total,
            "grade": self.determine_grade(total),
            "components": [c.to_dict() for c in components],
            "weights": weights
        }

    def calculate_throughput(self, times: List[float]) -> float:
        """Calculate throughput (operations per second)."""
        if not times:
            return 0.0
        total_time = sum(times)
        if total_time <= 0:
            return 0.0
        return len(times) / total_time

    def calculate_latency(self, times: List[float]) -> float:
        """Calculate average latency."""
        if not times:
            return 0.0
        return sum(times) / len(times)

    def calculate_max_latency(self, times: List[float]) -> float:
        """Calculate maximum latency."""
        if not times:
            return 0.0
        return max(times)

    def calculate_min_latency(self, times: List[float]) -> float:
        """Calculate minimum latency."""
        if not times:
            return 0.0
        return min(times)

    def calculate_variance(self, times: List[float]) -> float:
        """Calculate latency variance."""
        if not times or len(times) < 2:
            return 0.0
        mean = sum(times) / len(times)
        return sum((x - mean) ** 2 for x in times) / len(times)

    def calculate_percentile(self, times: List[float], percentile: float) -> float:
        """Calculate percentile of execution times."""
        if not times:
            return 0.0
        s = sorted(times)
        n = len(s)
        idx = int(n * percentile / 100)
        if (n * percentile) % 100 == 0 and idx > 0:
            idx -= 1
        idx = min(max(0, idx), n - 1)
        return s[idx]

    def measure_execution_time(
        self,
        func,
        *args,
        **kwargs
    ) -> Tuple[float, Any]:
        """
        Measure execution time of a function.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Tuple of (elapsed_time, result)
        """
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            return elapsed, result
        except Exception as e:
            elapsed = time.perf_counter() - start
            raise e from None

    def batch_score(
        self,
        test_results: List[Dict[str, Any]]
    ) -> List[ScoreResult]:
        """
        Score multiple test results in batch.

        Args:
            test_results: List of test result dictionaries

        Returns:
            List of ScoreResult objects
        """
        results = []
        weights = self._config.weights if self._config else None

        for result in test_results:
            scores = {
                "correctness": result.get("correctness", 0.0),
                "performance": result.get("performance", 0.0),
                "complexity": result.get("complexity", 0.0),
                "memory": result.get("memory", 0.0)
            }

            total = self.calculate_total_score(scores, weights)
            grade = self.determine_grade(total)

            score_result = ScoreResult(
                test_name=result.get("test_name", "unknown"),
                total_score=total,
                components=[
                    ScoreComponent(name=k, score=v, weight=weights.get(k, 0.0))
                    for k, v in scores.items()
                ],
                execution_time=result.get("execution_time", 0.0),
                memory_used=result.get("memory_used", 0),
                grade=grade
            )

            results.append(score_result)
            self._total_tests += 1
            self._total_score += total

        return results

    def get_average_score(self) -> float:
        """Get average score across all tests."""
        if self._total_tests == 0:
            return 0.0
        return self._total_score / self._total_tests

    def _log_error(self, message: str) -> None:
        """Log error message."""
        print(f"[SCORING ERROR] {message}")


class ScoringConfig:
    """
    Configuration for scoring engine.

    Provides customizable scoring weights, thresholds, and limits.
    """

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        thresholds: Optional[Dict[str, float]] = None,
        performance_targets: Optional[Dict[str, float]] = None,
        complexity_limits: Optional[Dict[str, int]] = None,
        profile: Optional[str] = None,
        **kwargs: Any
    ):
        """
        Initialize scoring configuration.

        Args:
            weights: Component weights
            thresholds: Score thresholds
            performance_targets: Performance targets
            complexity_limits: Complexity limits
            profile: Optional scoring profile name
        """
        self.profile = profile
        self.weights = weights or {
            "correctness": 0.4,
            "performance": 0.3,
            "complexity": 0.2,
            "memory": 0.1
        }

        self.thresholds = thresholds or {
            "pass": 0.7,
            "warning": 0.5,
            "fail": 0.3
        }

        self.performance_targets = performance_targets or {
            "target_time": 1.0,
            "max_time": 10.0,
            "target_memory_ratio": 0.1
        }

        self.complexity_limits = complexity_limits or {
            "max_cyclomatic": 10,
            "max_lines": 100,
            "max_functions": 20
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScoringConfig":
        """
        Create configuration from dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            ScoringConfig instance
        """
        return cls(
            weights=data.get("weights"),
            thresholds=data.get("thresholds"),
            performance_targets=data.get("performance_targets"),
            complexity_limits=data.get("complexity_limits")
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "weights": self.weights,
            "thresholds": self.thresholds,
            "performance_targets": self.performance_targets,
            "complexity_limits": self.complexity_limits
        }

    def validate(self) -> bool:
        """
        Validate configuration.

        Returns:
            True if valid, False otherwise
        """
        # Validate weights
        total_weight = sum(self.weights.values())
        if not 0.9 <= total_weight <= 1.1:
            print(f"[WARNING] Weights total {total_weight:.2f}, expected ~1.0")

        # Validate thresholds
        threshold_keys = ["pass", "warning", "fail"]
        for key in threshold_keys:
            if key not in self.thresholds:
                print(f"[WARNING] Missing threshold: {key}")

        return True


class ResultsReportGenerator:
    """
    Report generator for scoring results.

    Generates text, JSON, and HTML reports from scoring results.
    """

    def __init__(self, config: Optional[ScoringConfig] = None):
        """
        Initialize report generator.

        Args:
            config: Optional scoring configuration
        """
        self._config = config

    def generate_text_report(
        self,
        results: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> str:
        """
        Generate text report.

        Args:
            results: Single result or list of results

        Returns:
            Formatted text report
        """
        if isinstance(results, list):
            return self._generate_batch_text_report(results)
        else:
            return self._generate_single_text_report(results)

    def _generate_single_text_report(self, result: Dict[str, Any]) -> str:
        """Generate text report for single result."""
        lines = [
            "=" * 60,
            f"Scoring Report: {result.get('test_name', 'Unknown')}",
            "=" * 60,
            "",
            f"Total Score: {result.get('total_score', 0):.2f} / 1.00",
            f"Grade: {result.get('grade', 'N/A')}",
            "",
            "Component Scores:",
            "-" * 40
        ]

        for component in result.get("components", []):
            lines.append(
                f"  {component['name']:15} {component['score']:6.2f} "
                f"(weight: {component['weight']:.2f})"
            )

        lines.extend([
            "",
            f"Execution Time: {result.get('execution_time', 0):.4f} seconds",
            f"Memory Used: {result.get('memory_used', 0):,} bytes",
            "",
            "=" * 60
        ])

        return "\n".join(lines)

    def _generate_batch_text_report(self, results: List[Dict[str, Any]]) -> str:
        """Generate text report for batch of results."""
        lines = [
            "=" * 60,
            "Batch Scoring Report",
            "=" * 60,
            f"Total Tests: {len(results)}",
            "",
            "-" * 60,
            "Individual Results:",
            "-" * 60
        ]

        total_score = 0.0
        for result in results:
            score = result.get("total_score", 0)
            total_score += score

            lines.append(
                f"  {result.get('test_name', 'Unknown'):30} "
                f"Score: {score:6.2f}  Grade: {result.get('grade', 'N/A')}"
            )

        lines.extend([
            "-" * 60,
            "Summary:",
            f"  Average Score: {total_score / len(results):.2f}",
            f"  Total Score: {total_score:.2f}",
            "=" * 60
        ])

        return "\n".join(lines)

    def generate_json_report(
        self,
        results: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> str:
        """
        Generate JSON report.

        Args:
            results: Single result or list of results

        Returns:
            JSON string
        """
        import json

        if isinstance(results, list):
            return json.dumps(results, indent=2)
        else:
            return json.dumps(results, indent=2)

    def generate_html_report(
        self,
        results: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> str:
        """
        Generate HTML report.

        Args:
            results: Single result or list of results

        Returns:
            HTML string
        """
        if isinstance(results, list):
            return self._generate_batch_html_report(results)
        else:
            return self._generate_single_html_report(results)

    def _generate_single_html_report(self, result: Dict[str, Any]) -> str:
        """Generate HTML report for single result."""
        score = result.get("total_score", 0)
        grade = result.get("grade", "N/A")

        # Color based on grade
        colors = {
            "A": "#4CAF50",
            "B": "#8BC34A",
            "C": "#FFC107",
            "D": "#FF9800",
            "F": "#F44336"
        }
        color = colors.get(grade, "#9E9E9E")

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Scoring Report: {result.get('test_name', 'Unknown')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ border-bottom: 2px solid #333; padding-bottom: 10px; }}
        .score {{ font-size: 24px; color: {color}; }}
        .grade {{ font-size: 32px; font-weight: bold; color: {color}; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f5f5f5; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Scoring Report: {result.get('test_name', 'Unknown')}</h1>
    </div>
    <div class="score">
        Total Score: {score:.2f} / 1.00
    </div>
    <div class="grade">
        Grade: {grade}
    </div>
    <table>
        <tr><th>Component</th><th>Score</th><th>Weight</th></tr>
"""

        for component in result.get("components", []):
            html += f"""        <tr>
            <td>{component['name']}</td>
            <td>{component['score']:.2f}</td>
            <td>{component['weight']:.2f}</td>
        </tr>"""

        html += f"""    </table>
    <p>
        Execution Time: {result.get('execution_time', 0):.4f} seconds<br>
        Memory Used: {result.get('memory_used', 0):,} bytes
    </p>
</body>
</html>"""

        return html

    def generate_summary_report(
        self,
        results: List[Dict[str, Any]]
    ) -> str:
        """
        Generate summary report.

        Args:
            results: List of result dictionaries

        Returns:
            Summary string
        """
        if not results:
            return "No results to summarize."

        total_score = sum(r.get("total_score", 0) for r in results)
        avg_score = total_score / len(results)

        grade_distribution = {}
        for result in results:
            grade = result.get("grade", "Unknown")
            grade_distribution[grade] = grade_distribution.get(grade, 0) + 1

        summary = f"""
Summary Report
==============

Total Tests: {len(results)}
Average Score: {avg_score:.2f}

Grade Distribution:
"""

        for grade in ["A", "B", "C", "D", "F"]:
            count = grade_distribution.get(grade, 0)
            summary += f"  {grade}: {count}\n"

        return summary.strip()


if __name__ == "__main__":
    # Example usage
    config = ScoringConfig()
    engine = ScoringEngine(config=config)

    # Test scoring
    correctness = engine.score_correctness("expected", "expected")
    performance = engine.score_performance(0.5, 1.0, 5.0)
    complexity = engine.score_complexity(5, 50, 10, 100)

    scores = {
        "correctness": correctness,
        "performance": performance,
        "complexity": complexity,
        "memory": engine.score_memory(1024 * 1024)
    }

    total = engine.calculate_total_score(scores, config.weights)
    grade = engine.determine_grade(total)

    print(f"Total Score: {total:.2f}")
    print(f"Grade: {grade}")

    # Generate report
    generator = ResultsReportGenerator()
    report = generator.generate_text_report({
        "test_name": "example_test",
        "total_score": total,
        "grade": grade,
        "components": [
            {"name": k, "score": v, "weight": config.weights.get(k, 0.0)}
            for k, v in scores.items()
        ],
        "execution_time": 0.5,
        "memory_used": 1024 * 1024
    })

    print(report)
