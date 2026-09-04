"""
Scoring Configuration Module

Provides configuration classes and utilities for the scoring engine.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class ScoringConfig:
    """
    Configuration for scoring engine.

    Provides customizable scoring weights, thresholds, and limits.
    """

    # Weights for each scoring component
    weights: Dict[str, float] = field(
        default_factory=lambda: {
            "correctness": 0.4,
            "performance": 0.3,
            "complexity": 0.2,
            "memory": 0.1
        }
    )

    # Score thresholds
    thresholds: Dict[str, float] = field(
        default_factory=lambda: {
            "pass": 0.7,
            "warning": 0.5,
            "fail": 0.3
        }
    )

    # Performance targets
    performance_targets: Dict[str, float] = field(
        default_factory=lambda: {
            "target_time": 1.0,
            "max_time": 10.0,
            "target_memory_ratio": 0.1
        }
    )

    # Complexity limits
    complexity_limits: Dict[str, int] = field(
        default_factory=lambda: {
            "max_cyclomatic": 10,
            "max_lines": 100,
            "max_functions": 20
        }
    )

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
            weights=data.get("weights", {}),
            thresholds=data.get("thresholds", {}),
            performance_targets=data.get("performance_targets", {}),
            complexity_limits=data.get("complexity_limits", {})
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Configuration dictionary
        """
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

    def get_weight(self, component: str, default: float = 0.0) -> float:
        """
        Get weight for a component.

        Args:
            component: Component name
            default: Default weight if not found

        Returns:
            Weight value
        """
        return self.weights.get(component, default)

    def get_threshold(self, level: str, default: float = 0.0) -> float:
        """
        Get threshold for a level.

        Args:
            level: Threshold level
            default: Default threshold if not found

        Returns:
            Threshold value
        """
        return self.thresholds.get(level, default)

    def get_performance_target(self, target: str, default: float = 1.0) -> float:
        """
        Get performance target.

        Args:
            target: Target name
            default: Default target if not found

        Returns:
            Target value
        """
        return self.performance_targets.get(target, default)

    def get_complexity_limit(self, limit: str, default: int = 10) -> int:
        """
        Get complexity limit.

        Args:
            limit: Limit name
            default: Default limit if not found

        Returns:
            Limit value
        """
        return self.complexity_limits.get(limit, default)


@dataclass
class ScoringProfile:
    """
    Scoring profile for different contexts.

    Profiles can be used to apply different scoring criteria
    based on the testing context.
    """

    name: str
    config: ScoringConfig
    description: str = ""
    active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "active": self.active,
            "config": self.config.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScoringProfile":
        """Create profile from dictionary."""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            active=data.get("active", True),
            config=ScoringConfig.from_dict(data["config"])
        )


class ScoringRegistry:
    """
    Registry for scoring profiles.

    Manages multiple scoring profiles and allows switching
    between them based on context.
    """

    def __init__(self):
        """Initialize registry."""
        self._profiles: Dict[str, ScoringProfile] = {}
        self._default_profile: Optional[ScoringProfile] = None

    def register(self, profile: ScoringProfile) -> None:
        """
        Register a scoring profile.

        Args:
            profile: Profile to register
        """
        self._profiles[profile.name] = profile

    def unregister(self, name: str) -> bool:
        """
        Unregister a scoring profile.

        Args:
            name: Profile name

        Returns:
            True if removed, False if not found
        """
        if name in self._profiles:
            del self._profiles[name]
            return True
        return False

    def get(self, name: str) -> Optional[ScoringProfile]:
        """
        Get a scoring profile by name.

        Args:
            name: Profile name

        Returns:
            Profile or None if not found
        """
        return self._profiles.get(name)

    def get_active(self) -> Optional[ScoringProfile]:
        """
        Get active scoring profile.

        Returns:
            Active profile or None
        """
        for profile in self._profiles.values():
            if profile.active:
                return profile
        return self._default_profile

    def set_default(self, name: str) -> bool:
        """
        Set default profile.

        Args:
            name: Profile name

        Returns:
            True if set, False if not found
        """
        if name in self._profiles:
            self._default_profile = self._profiles[name]
            return True
        return False

    def list_profiles(self) -> List[Dict[str, Any]]:
        """
        List all profiles.

        Returns:
            List of profile dictionaries
        """
        return [p.to_dict() for p in self._profiles.values()]


class ScoringValidator:
    """
    Validator for scoring results.

    Validates scoring results against configured thresholds
    and limits.
    """

    def __init__(self, config: Optional[ScoringConfig] = None):
        """
        Initialize validator.

        Args:
            config: Scoring configuration
        """
        self._config = config or ScoringConfig()

    def validate_score(self, score: float) -> bool:
        """
        Validate score is within acceptable range.

        Args:
            score: Score to validate

        Returns:
            True if valid
        """
        return 0.0 <= score <= 1.0

    def validate_threshold(self, score: float) -> str:
        """
        Determine threshold level for score.

        Args:
            score: Score to evaluate

        Returns:
            Threshold level string
        """
        thresholds = self._config.thresholds

        if score >= thresholds.get("pass", 0.7):
            return "pass"
        elif score >= thresholds.get("warning", 0.5):
            return "warning"
        else:
            return "fail"

    def validate_complexity(
        self,
        cyclomatic: int,
        lines: int
    ) -> Dict[str, Any]:
        """
        Validate complexity metrics.

        Args:
            cyclomatic: Cyclomatic complexity
            lines: Lines of code

        Returns:
            Validation result
        """
        limits = self._config.complexity_limits

        result = {
            "valid": True,
            "issues": []
        }

        if cyclomatic > limits.get("max_cyclomatic", 10):
            result["valid"] = False
            result["issues"].append(
                f"Cyclomatic complexity {cyclomatic} exceeds limit {limits['max_cyclomatic']}"
            )

        if lines > limits.get("max_lines", 100):
            result["valid"] = False
            result["issues"].append(
                f"Lines of code {lines} exceeds limit {limits['max_lines']}"
            )

        return result

    def validate_performance(
        self,
        elapsed_time: float,
        memory_used: int
    ) -> Dict[str, Any]:
        """
        Validate performance metrics.

        Args:
            elapsed_time: Execution time in seconds
            memory_used: Memory used in bytes

        Returns:
            Validation result
        """
        targets = self._config.performance_targets

        result = {
            "valid": True,
            "issues": []
        }

        if elapsed_time > targets.get("max_time", 10.0):
            result["valid"] = False
            result["issues"].append(
                f"Execution time {elapsed_time:.2f}s exceeds max {targets['max_time']}s"
            )

        memory_limit = targets.get("max_time", 10.0) * 1024 * 1024  # Rough estimate
        if memory_used > memory_limit:
            result["valid"] = False
            result["issues"].append(
                f"Memory usage {memory_used} bytes exceeds limit"
            )

        return result

    def validate_result(
        self,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate complete scoring result.

        Args:
            result: Scoring result dictionary

        Returns:
            Validation result
        """
        validation = {
            "valid": True,
            "issues": []
        }

        # Validate score
        score = result.get("total_score", 0)
        if not self.validate_score(score):
            validation["valid"] = False
            validation["issues"].append("Invalid score value")

        # Validate threshold
        threshold = self.validate_threshold(score)
        result["threshold"] = threshold

        # Validate complexity if present
        if "complexity" in result:
            complexity = result["complexity"]
            complexity_validation = self.validate_complexity(
                complexity.get("cyclomatic", 0),
                complexity.get("lines", 0)
            )
            if not complexity_validation["valid"]:
                validation["valid"] = False
                validation["issues"].extend(
                    complexity_validation["issues"]
                )

        # Validate performance if present
        if "execution_time" in result:
            performance_validation = self.validate_performance(
                result["execution_time"],
                result.get("memory_used", 0)
            )
            if not performance_validation["valid"]:
                validation["valid"] = False
                validation["issues"].extend(
                    performance_validation["issues"]
                )

        return validation


def create_default_config() -> ScoringConfig:
    """
    Create default scoring configuration.

    Returns:
        Default ScoringConfig instance
    """
    return ScoringConfig()


def create_strict_config() -> ScoringConfig:
    """
    Create strict scoring configuration.

    Returns:
        Strict ScoringConfig instance
    """
    return ScoringConfig(
        weights={
            "correctness": 0.5,
            "performance": 0.3,
            "complexity": 0.15,
            "memory": 0.05
        },
        thresholds={
            "pass": 0.85,
            "warning": 0.7,
            "fail": 0.5
        },
        performance_targets={
            "target_time": 0.5,
            "max_time": 5.0,
            "target_memory_ratio": 0.05
        },
        complexity_limits={
            "max_cyclomatic": 5,
            "max_lines": 50,
            "max_functions": 10
        }
    )


def create_relaxed_config() -> ScoringConfig:
    """
    Create relaxed scoring configuration.

    Returns:
        Relaxed ScoringConfig instance
    """
    return ScoringConfig(
        weights={
            "correctness": 0.3,
            "performance": 0.2,
            "complexity": 0.3,
            "memory": 0.2
        },
        thresholds={
            "pass": 0.6,
            "warning": 0.4,
            "fail": 0.2
        },
        performance_targets={
            "target_time": 2.0,
            "max_time": 20.0,
            "target_memory_ratio": 0.2
        },
        complexity_limits={
            "max_cyclomatic": 20,
            "max_lines": 200,
            "max_functions": 50
        }
    )


if __name__ == "__main__":
    # Example usage
    config = create_default_config()
    print("Default Config:")
    print(config.to_dict())
    print()

    # Create validator
    validator = ScoringValidator(config)

    # Test validation
    result = {
        "total_score": 0.85,
        "complexity": {
            "cyclomatic": 5,
            "lines": 50
        },
        "execution_time": 0.5,
        "memory_used": 1024 * 1024
    }

    validation = validator.validate_result(result)
    print("Validation Result:")
    print(f"  Valid: {validation['valid']}")
    print(f"  Issues: {validation['issues']}")
    if "threshold" in result:
        print(f"  Threshold: {result['threshold']}")
