"""
Scoring Module Tests - Comprehensive tests for scoring engine

Tests cover:
- Scoring engine
- Scoring configuration
- Results report generation
- Performance metrics
"""

import pytest
import sys
import os
import json
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.scoring.scoring_engine import ScoringEngine
from tests.scoring.scoring_config import ScoringConfig
from tests.scoring.results_report import ResultsReportGenerator


class TestScoringConfig:
    """Test scoring configuration."""

    def test_config_creation(self):
        """Test config can be created."""
        config = ScoringConfig()
        assert config is not None

    def test_default_weights(self):
        """Test default scoring weights."""
        config = ScoringConfig()
        
        assert config.weights is not None
        assert "correctness" in config.weights
        assert "performance" in config.weights
        assert "complexity" in config.weights

    def test_custom_weights(self):
        """Test custom scoring weights."""
        config = ScoringConfig(
            weights={
                "correctness": 0.4,
                "performance": 0.35,
                "complexity": 0.25
            }
        )
        
        assert config.weights["correctness"] == 0.4
        assert config.weights["performance"] == 0.35
        assert config.weights["complexity"] == 0.25

    def test_thresholds(self):
        """Test scoring thresholds."""
        config = ScoringConfig()
        
        assert config.thresholds is not None
        assert "pass" in config.thresholds
        assert "warning" in config.thresholds
        assert "fail" in config.thresholds

    def test_performance_targets(self):
        """Test performance targets."""
        config = ScoringConfig()
        
        assert config.performance_targets is not None
        assert "target_time" in config.performance_targets
        assert "max_time" in config.performance_targets

    def test_complexity_limits(self):
        """Test complexity limits."""
        config = ScoringConfig()
        
        assert config.complexity_limits is not None
        assert "max_cyclomatic" in config.complexity_limits
        assert "max_lines" in config.complexity_limits

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        config_data = {
            "weights": {
                "correctness": 0.5,
                "performance": 0.3,
                "complexity": 0.2
            },
            "thresholds": {
                "pass": 0.7,
                "warning": 0.5,
                "fail": 0.3
            }
        }
        
        config = ScoringConfig.from_dict(config_data)
        assert config is not None
        assert config.weights["correctness"] == 0.5


class TestScoringEngine:
    """Test scoring engine."""

    def test_engine_creation(self):
        """Test engine can be created."""
        engine = ScoringEngine()
        assert engine is not None

    def test_score_correctness(self):
        """Test scoring correctness."""
        engine = ScoringEngine()
        
        # Perfect correctness
        score = engine.score_correctness(
            expected_output="result",
            actual_output="result"
        )
        assert score == 1.0

        # Partial correctness
        score = engine.score_correctness(
            expected_output="a, b, c",
            actual_output="a, b"
        )
        assert 0 < score < 1.0

        # Incorrect
        score = engine.score_correctness(
            expected_output="result",
            actual_output="wrong"
        )
        assert score == 0.0

    def test_score_performance(self):
        """Test scoring performance."""
        engine = ScoringEngine()
        
        # Measure execution time
        start = time.time()
        sum_val = sum(range(1000))
        elapsed = time.time() - start
        
        # Score based on time
        score = engine.score_performance(
            elapsed_time=elapsed,
            target_time=1.0,
            max_time=10.0
        )
        
        assert 0 <= score <= 1.0

    def test_score_complexity(self):
        """Test scoring complexity."""
        engine = ScoringEngine()
        
        # Simple code
        score = engine.score_complexity(
            cyclomatic=2,
            lines=10,
            max_cyclomatic=10,
            max_lines=100
        )
        assert score > 0.8

        # Complex code
        score = engine.score_complexity(
            cyclomatic=20,
            lines=500,
            max_cyclomatic=10,
            max_lines=100
        )
        assert score < 0.5

    def test_score_memory(self):
        """Test scoring memory usage."""
        engine = ScoringEngine()
        
        score = engine.score_memory(
            memory_used=1024 * 1024,  # 1 MB
            memory_limit=100 * 1024 * 1024,  # 100 MB
            target_ratio=0.1
        )
        
        assert 0 <= score <= 1.0

    def test_calculate_total_score(self):
        """Test calculating total weighted score."""
        engine = ScoringEngine()
        
        scores = {
            "correctness": 0.9,
            "performance": 0.8,
            "complexity": 0.7,
            "memory": 0.85
        }
        
        weights = {
            "correctness": 0.4,
            "performance": 0.3,
            "complexity": 0.2,
            "memory": 0.1
        }
        
        total = engine.calculate_total_score(scores, weights)
        assert 0 <= total <= 1.0

    def test_determine_grade(self):
        """Test determining grade from score."""
        engine = ScoringEngine()
        
        # Perfect score
        grade = engine.determine_grade(1.0)
        assert grade == "A"

        # Good score
        grade = engine.determine_grade(0.8)
        assert grade in ["A", "B"]

        # Average score
        grade = engine.determine_grade(0.6)
        assert grade in ["C", "D"]

        # Poor score
        grade = engine.determine_grade(0.3)
        assert grade in ["F", "Fail"]

    def test_generate_score_breakdown(self):
        """Test generating score breakdown."""
        engine = ScoringEngine()
        
        scores = {
            "correctness": 0.9,
            "performance": 0.8,
            "complexity": 0.7,
            "memory": 0.85
        }
        
        weights = {
            "correctness": 0.4,
            "performance": 0.3,
            "complexity": 0.2,
            "memory": 0.1
        }
        
        breakdown = engine.generate_score_breakdown(scores, weights)
        assert breakdown is not None
        assert "total" in breakdown
        assert "components" in breakdown

    def test_score_with_config(self):
        """Test scoring with custom configuration."""
        config = ScoringConfig(
            weights={
                "correctness": 0.5,
                "performance": 0.3,
                "complexity": 0.2
            }
        )
        
        engine = ScoringEngine(config=config)
        
        scores = {
            "correctness": 1.0,
            "performance": 0.5,
            "complexity": 0.8
        }
        
        total = engine.calculate_total_score(scores, config.weights)
        assert round(total, 2) == 0.81  # 0.5*1.0 + 0.3*0.5 + 0.2*0.8

    def test_batch_scoring(self):
        """Test batch scoring multiple items."""
        engine = ScoringEngine()
        
        results = []
        for i in range(10):
            score = engine.score_correctness(
                expected_output=f"expected_{i}",
                actual_output=f"actual_{i}"
            )
            results.append(score)
        
        assert len(results) == 10
        assert all(0 <= r <= 1.0 for r in results)

    def test_score_edge_cases(self):
        """Test scoring edge cases."""
        engine = ScoringEngine()
        
        # Empty outputs
        score = engine.score_correctness(
            expected_output="",
            actual_output=""
        )
        assert score == 1.0  # Empty matches empty

        # None values
        score = engine.score_correctness(
            expected_output=None,
            actual_output=None
        )
        assert score == 1.0

        # Very large values
        score = engine.score_performance(
            elapsed_time=0.001,
            target_time=1.0,
            max_time=10.0
        )
        assert 0 <= score <= 1.0


class TestResultsReportGenerator:
    """Test results report generation."""

    def test_report_generator_creation(self):
        """Test report generator can be created."""
        generator = ResultsReportGenerator()
        assert generator is not None

    def test_generate_text_report(self):
        """Test generating text report."""
        generator = ResultsReportGenerator()
        
        results = {
            "test_name": "test_function",
            "scores": {
                "correctness": 0.9,
                "performance": 0.8,
                "complexity": 0.7
            },
            "execution_time": 0.5,
            "memory_used": 1024
        }
        
        report = generator.generate_text_report(results)
        assert report is not None
        assert isinstance(report, str)
        assert "test_function" in report

    def test_generate_json_report(self):
        """Test generating JSON report."""
        generator = ResultsReportGenerator()
        
        results = {
            "test_name": "test_function",
            "scores": {
                "correctness": 0.9,
                "performance": 0.8,
                "complexity": 0.7
            },
            "execution_time": 0.5,
            "memory_used": 1024
        }
        
        report = generator.generate_json_report(results)
        assert report is not None
        assert isinstance(report, str)
        data = json.loads(report)
        assert "test_name" in data

    def test_generate_html_report(self):
        """Test generating HTML report."""
        generator = ResultsReportGenerator()
        
        results = {
            "test_name": "test_function",
            "scores": {
                "correctness": 0.9,
                "performance": 0.8,
                "complexity": 0.7
            },
            "execution_time": 0.5,
            "memory_used": 1024
        }
        
        report = generator.generate_html_report(results)
        assert report is not None
        assert isinstance(report, str)
        assert "<html" in report.lower() or "<!DOCTYPE" in report

    def test_generate_summary_report(self):
        """Test generating summary report."""
        generator = ResultsReportGenerator()
        
        results = {
            "test_name": "test_function",
            "scores": {
                "correctness": 0.9,
                "performance": 0.8,
                "complexity": 0.7
            },
            "execution_time": 0.5,
            "memory_used": 1024
        }
        
        summary = generator.generate_summary_report(results)
        assert summary is not None
        assert "Summary" in summary or "summary" in summary.lower()

    def test_report_with_multiple_tests(self):
        """Test report with multiple test results."""
        generator = ResultsReportGenerator()
        
        results = [
            {
                "test_name": f"test_{i}",
                "scores": {
                    "correctness": 0.9,
                    "performance": 0.8,
                    "complexity": 0.7
                },
                "execution_time": 0.5,
                "memory_used": 1024
            }
            for i in range(5)
        ]
        
        report = generator.generate_text_report(results)
        assert report is not None
        assert len(results) > 0

    def test_report_with_grades(self):
        """Test report with grades."""
        generator = ResultsReportGenerator()
        
        results = {
            "test_name": "test_function",
            "scores": {
                "correctness": 0.95,
                "performance": 0.9,
                "complexity": 0.85
            },
            "execution_time": 0.3,
            "memory_used": 512
        }
        
        report = generator.generate_text_report(results)
        assert report is not None
        # Should include grade information
        assert "grade" in report.lower() or "A" in report or "B" in report


class TestPerformanceMetrics:
    """Test performance metrics calculation."""

    def test_calculate_throughput(self):
        """Test calculating throughput."""
        engine = ScoringEngine()
        
        # Simulate multiple executions
        times = [0.1, 0.15, 0.12, 0.14, 0.13]
        total_time = sum(times)
        count = len(times)
        
        throughput = engine.calculate_throughput(times)
        expected = count / total_time
        
        assert abs(throughput - expected) < 0.01

    def test_calculate_latency(self):
        """Test calculating latency metrics."""
        engine = ScoringEngine()
        
        times = [0.1, 0.15, 0.12, 0.14, 0.13]
        
        avg_latency = engine.calculate_latency(times)
        assert avg_latency > 0

        max_latency = engine.calculate_max_latency(times)
        assert max_latency == 0.15

        min_latency = engine.calculate_min_latency(times)
        assert min_latency == 0.1

    def test_calculate_variance(self):
        """Test calculating variance."""
        engine = ScoringEngine()
        
        times = [0.1, 0.1, 0.1, 0.1, 0.1]
        variance = engine.calculate_variance(times)
        assert variance == 0.0

        times = [0.1, 0.2, 0.3, 0.4, 0.5]
        variance = engine.calculate_variance(times)
        assert variance > 0

    def test_calculate_percentiles(self):
        """Test calculating percentiles."""
        engine = ScoringEngine()
        
        times = [0.1, 0.15, 0.12, 0.14, 0.13, 0.16, 0.11, 0.17]
        times.sort()
        
        p50 = engine.calculate_percentile(times, 50)
        assert p50 == 0.13

        p90 = engine.calculate_percentile(times, 90)
        assert p90 >= 0.16


class TestScoringIntegration:
    """Test full scoring integration."""

    def test_full_scoring_workflow(self):
        """Test complete scoring workflow."""
        # Create config
        config = ScoringConfig(
            weights={
                "correctness": 0.4,
                "performance": 0.35,
                "complexity": 0.25
            }
        )
        
        # Create engine
        engine = ScoringEngine(config=config)
        
        # Score components
        correctness = engine.score_correctness(
            expected_output="result",
            actual_output="result"
        )
        
        performance = engine.score_performance(
            elapsed_time=0.5,
            target_time=1.0,
            max_time=5.0
        )
        
        complexity = engine.score_complexity(
            cyclomatic=5,
            lines=50,
            max_cyclomatic=10,
            max_lines=100
        )
        
        # Calculate total
        total = engine.calculate_total_score(
            {"correctness": correctness, "performance": performance, "complexity": complexity},
            config.weights
        )
        
        assert 0 <= total <= 1.0

    def test_batch_workflow(self):
        """Test batch scoring workflow."""
        config = ScoringConfig()
        engine = ScoringEngine(config=config)
        
        results = []
        for i in range(10):
            correctness = engine.score_correctness(
                expected_output=f"expected_{i}",
                actual_output=f"actual_{i}"
            )
            
            performance = engine.score_performance(
                elapsed_time=0.1 + i * 0.01,
                target_time=1.0,
                max_time=10.0
            )
            
            complexity = engine.score_complexity(
                cyclomatic=2 + i,
                lines=10 + i * 5,
                max_cyclomatic=10,
                max_lines=100
            )
            
            results.append({
                "test": f"test_{i}",
                "scores": {
                    "correctness": correctness,
                    "performance": performance,
                    "complexity": complexity
                }
            })
        
        assert len(results) == 10

    def test_report_generation_workflow(self):
        """Test report generation workflow."""
        config = ScoringConfig()
        engine = ScoringEngine(config=config)
        generator = ResultsReportGenerator()
        
        results = []
        for i in range(5):
            scores = {
                "correctness": 0.9,
                "performance": 0.8,
                "complexity": 0.7
            }
            
            total = engine.calculate_total_score(scores, config.weights)
            
            results.append({
                "test_name": f"test_{i}",
                "scores": scores,
                "total_score": total,
                "grade": engine.determine_grade(total),
                "execution_time": 0.5,
                "memory_used": 1024
            })
        
        # Generate reports
        text_report = generator.generate_text_report(results)
        json_report = generator.generate_json_report(results)
        
        assert text_report is not None
        assert json_report is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
