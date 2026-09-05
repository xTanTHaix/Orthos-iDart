"""
Annihilator Faulhaber Module - Polynomial Sum Optimization Engine

This module implements Faulhaber's formula and related polynomial
optimizations for transforming O(N) summations into O(1) closed forms.
"""

import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)


class PolynomialType(Enum):
    """Types of polynomial optimizations."""
    FAULHABER = "faulhaber"
    BERNOULLI = "bernoulli"
    ZETA = "zeta"
    GENERALIZED = "generalized"


@dataclass
class Polynomial:
    """Represents a polynomial with coefficients."""
    degree: int
    coefficients: List[float] = field(default_factory=list)
    
    def __post_init__(self):
        """Ensure coefficients match degree."""
        if len(self.coefficients) != self.degree + 1:
            # Pad with zeros
            while len(self.coefficients) < self.degree + 1:
                self.coefficients.append(0.0)
            # Trim excess
            self.coefficients = self.coefficients[:self.degree + 1]
    
    def __getitem__(self, index: int) -> float:
        """Get coefficient at index."""
        return self.coefficients[index]
    
    def __call__(self, x: float) -> float:
        """Evaluate polynomial at x."""
        result = 0.0
        for i, coef in enumerate(self.coefficients):
            result += coef * (x ** i)
        return result
    
    def __add__(self, other: 'Polynomial') -> 'Polynomial':
        """Add two polynomials."""
        max_degree = max(self.degree, other.degree)
        result = Polynomial(degree=max_degree)
        
        for i in range(max_degree + 1):
            coef1 = self[i] if i <= self.degree else 0.0
            coef2 = other[i] if i <= other.degree else 0.0
            result.coefficients[i] = coef1 + coef2
        
        return result
    
    def __sub__(self, other: 'Polynomial') -> 'Polynomial':
        """Subtract two polynomials."""
        max_degree = max(self.degree, other.degree)
        result = Polynomial(degree=max_degree)
        
        for i in range(max_degree + 1):
            coef1 = self[i] if i <= self.degree else 0.0
            coef2 = other[i] if i <= other.degree else 0.0
            result.coefficients[i] = coef1 - coef2
        
        return result
    
    def __mul__(self, other: 'Polynomial') -> 'Polynomial':
        """Multiply two polynomials."""
        result_degree = self.degree + other.degree
        result = Polynomial(degree=result_degree)
        
        for i in range(self.degree + 1):
            for j in range(other.degree + 1):
                result.coefficients[i + j] += self.coefficients[i] * other.coefficients[j]
        
        return result
    
    def __repr__(self) -> str:
        """String representation."""
        terms = []
        for i, coef in enumerate(self.coefficients):
            if abs(coef) > 1e-10:
                if i == 0:
                    terms.append(f"{coef:g}")
                elif i == 1:
                    terms.append(f"{coef:g}x")
                else:
                    terms.append(f"{coef:g}x^{i}")
        
        if len(terms) == 0:
            return "0"
        return " + ".join(terms)


@dataclass
class FaulhaberResult:
    """Result of Faulhaber optimization."""
    original_sum: str
    optimized_formula: str
    polynomial: Polynomial
    bernoulli_numbers: List[float]
    degree: int
    accuracy: float
    computation_time: float
    success: bool
    error_message: Optional[str] = None


class FaulhaberEngine:
    """
    Faulhaber's Formula Engine for Polynomial Summation.
    
    Transforms summations of polynomial powers into closed-form
    expressions using Bernoulli numbers and Faulhaber's formula.
    
    Formula: Σ(i^k) for i=1 to n = (1/(k+1)) * Σ(j=0 to k) (C(k+1,j) * B_j * n^(k+1-j))
    where B_j are Bernoulli numbers.
    """
    
    # Precomputed Bernoulli numbers (first 20)
    _BERNOULLI_CACHE: Dict[int, float] = {
        0: 1.0,
        1: -0.5,
        2: 1/6,
        3: 0.0,
        4: -1/30,
        5: 0.0,
        6: 1/42,
        7: 0.0,
        8: -1/30,
        9: 0.0,
        10: 5/66,
        11: 0.0,
        12: -691/2730,
        13: 0.0,
        14: 7/6,
        15: 0.0,
        16: -3617/510,
        17: 0.0,
        18: 43867/798,
        19: 0.0,
    }
    
    def __init__(
        self,
        max_degree: int = 20,
        cache_size: int = 1000,
        precision: int = 15
    ):
        """
        Initialize Faulhaber Engine.
        
        Args:
            max_degree: Maximum polynomial degree to support
            cache_size: Size of computation cache
            precision: Decimal precision for calculations
        """
        self.max_degree = max_degree
        self.cache_size = cache_size
        self.precision = precision
        
        # Computation cache
        self._sum_cache: Dict[Tuple[int, int], Polynomial] = {}
        self._bernoulli_cache: Dict[int, float] = self._BERNOULLI_CACHE.copy()
        
        logger.info(f"FaulhaberEngine initialized (max_degree={max_degree})")
    
    def _compute_bernoulli(self, n: int) -> float:
        """
        Compute Bernoulli number B_n using recurrence.
        
        Args:
            n: Index of Bernoulli number
            
        Returns:
            Bernoulli number B_n
        """
        try:
            if n in self._bernoulli_cache:
                return self._bernoulli_cache[n]
            
            # Use recurrence relation
            # Σ(k=0 to n) C(n+1, k) * B_k = 0 for n >= 1
            
            B_n = 0.0
            for k in range(n):
                # Binomial coefficient C(n+1, k)
                binom = math.comb(n + 1, k)
                B_n += binom * self._compute_bernoulli(k)
            
            B_n = -B_n / (n + 1)
            self._bernoulli_cache[n] = B_n
            
            logger.debug(f"Computed B_{n} = {B_n}")
            return B_n
            
        except Exception as e:
            logger.error(f"Bernoulli computation failed: {e}")
            raise
    
    def _compute_binomial(self, n: int, k: int) -> int:
        """Compute binomial coefficient C(n, k)."""
        try:
            if k < 0 or k > n:
                return 0
            
            # Use multiplicative formula for efficiency
            result = 1
            for i in range(k):
                result = result * (n - i) // (i + 1)
            
            return result
            
        except Exception as e:
            logger.error(f"Binomial computation failed: {e}")
            raise
    
    def compute_sum(self, power: int, n: int) -> float:
        """
        Compute Σ(i^power) for i=1 to n in O(1) closed form using Faulhaber's formula.
        
        Args:
            power: Power exponent
            n: Upper bound of summation
            
        Returns:
            Sum of powers: 1^power + 2^power + ... + n^power
        """
        return self._compute_power_sum(n, power)

    def _compute_power_sum(self, n: int, k: int) -> float:
        """
        Compute Σ(i^p) for i=1 to n using Faulhaber's formula.
        
        Args:
            n: Upper bound of summation
            k: Power of summation
            
        Returns:
            Sum of powers: 1^k + 2^k + ... + n^k
        """
        try:
            if n < 1:
                return 0.0
            
            if k < 0:
                raise ValueError("Power must be non-negative")
            
            if k > self.max_degree:
                logger.warning(f"Power {k} exceeds max_degree {self.max_degree}")
            
            # Check cache
            cache_key = (n, k)
            if cache_key in self._sum_cache:
                result = self._sum_cache[cache_key]
                return float(result(0))  # Evaluate at 0 to get constant term
            
            # Use Faulhaber's formula
            # S_k(n) = (1/(k+1)) * Σ(j=0 to k) (C(k+1,j) * B_j * n^(k+1-j))
            
            result = 0.0
            for j in range(k + 1):
                binom = self._compute_binomial(k + 1, j)
                bernoulli = self._compute_bernoulli(j)
                power = n ** (k + 1 - j)
                
                result += binom * bernoulli * power
            
            result /= (k + 1)
            
            # Cache result
            self._sum_cache[cache_key] = Polynomial(degree=k + 1, coefficients=[result])
            
            return result
            
        except Exception as e:
            logger.error(f"Power sum computation failed: {e}")
            raise
    
    def optimize_summation(
        self,
        power: int,
        upper_bound: int
    ) -> FaulhaberResult:
        """
        Optimize a power summation to closed form.
        
        Args:
            power: Power to sum (Σ(i^power))
            upper_bound: Upper bound of summation
            
        Returns:
            FaulhaberResult: Optimization result
        """
        try:
            if power < 0:
                raise ValueError("Power must be non-negative")
            
            if power > self.max_degree:
                raise ValueError(f"Power {power} exceeds max_degree {self.max_degree}")
            
            if upper_bound < 1:
                raise ValueError("Upper bound must be >= 1")
            
            # Compute using Faulhaber's formula
            sum_value = self._compute_power_sum(upper_bound, power)
            
            # Generate polynomial coefficients
            coefficients = []
            for j in range(power + 1):
                binom = self._compute_binomial(power + 1, j)
                bernoulli = self._compute_bernoulli(j)
                coef = binom * bernoulli / (power + 1)
                coefficients.append(coef)
            
            polynomial = Polynomial(degree=power, coefficients=coefficients)
            
            # Format formula string
            formula_terms = []
            for j, coef in enumerate(coefficients):
                if abs(coef) > 1e-10:
                    if j == 0:
                        formula_terms.append(f"{coef:g}")
                    elif j == 1:
                        formula_terms.append(f"{coef:g}n")
                    else:
                        formula_terms.append(f"{coef:g}n^{j}")
            
            formula_str = " + ".join(formula_terms) if formula_terms else "0"
            
            # Compute accuracy
            # Compare with direct computation
            direct_sum = sum(i ** power for i in range(1, upper_bound + 1))
            optimized_value = polynomial(upper_bound)
            
            if direct_sum != 0:
                accuracy = 1.0 - abs(optimized_value - direct_sum) / abs(direct_sum)
            else:
                accuracy = 1.0 if abs(optimized_value) < 1e-10 else 0.0
            
            return FaulhaberResult(
                original_sum=f"Σ(i^{power}) for i=1 to {upper_bound}",
                optimized_formula=f"{formula_str}",
                polynomial=polynomial,
                bernoulli_numbers=list(self._bernoulli_cache.values()),
                degree=power,
                accuracy=accuracy,
                computation_time=0.0,  # Would measure in real implementation
                success=True
            )
            
        except Exception as e:
            logger.error(f"Summation optimization failed: {e}")
            return FaulhaberResult(
                original_sum=f"Σ(i^{power})",
                optimized_formula="",
                polynomial=Polynomial(degree=0),
                bernoulli_numbers=[],
                degree=power,
                accuracy=0.0,
                computation_time=0.0,
                success=False,
                error_message=str(e)
            )
    
    def get_polynomial(self, power: int) -> Optional[Polynomial]:
        """
        Get precomputed polynomial for a given power.
        
        Args:
            power: Power of summation
            
        Returns:
            Polynomial: Coefficients polynomial or None
        """
        try:
            if power < 0 or power > self.max_degree:
                return None
            
            # Compute polynomial
            coefficients = []
            for j in range(power + 1):
                binom = self._compute_binomial(power + 1, j)
                bernoulli = self._compute_bernoulli(j)
                coef = binom * bernoulli / (power + 1)
                coefficients.append(coef)
            
            return Polynomial(degree=power, coefficients=coefficients)
            
        except Exception as e:
            logger.error(f"Polynomial retrieval failed: {e}")
            return None
    
    def evaluate_polynomial(
        self,
        power: int,
        n: int
    ) -> float:
        """
        Evaluate optimized polynomial at n.
        
        Args:
            power: Power of summation
            n: Value to evaluate at
            
        Returns:
            float: Sum value Σ(i^power) for i=1 to n
        """
        try:
            poly = self.get_polynomial(power)
            if poly is None:
                raise ValueError(f"Invalid power: {power}")
            
            return float(poly(n))
            
        except Exception as e:
            logger.error(f"Polynomial evaluation failed: {e}")
            raise
    
    def clear_cache(self):
        """Clear computation cache."""
        self._sum_cache.clear()
        logger.info("Cache cleared")
    
    def sum_polynomial(self, n: int, k: int) -> int:
        """Compute exact sum of powers: 1^k + 2^k + ... + n^k."""
        if n <= 0:
            return 0
        if k == 0:
            return n
        if k == 1:
            return n * (n + 1) // 2
        if k == 2:
            return n * (n + 1) * (2 * n + 1) // 6
        if k == 3:
            s = n * (n + 1) // 2
            return s * s
        val = self._compute_power_sum(n, k)
        return int(round(val))

    def compute_polynomial_sum(self, n: int, k: int) -> int:
        """Alias for sum_polynomial."""
        return self.sum_polynomial(n, k)

    def sum_series(self, n: int, start_power: int, end_power: int) -> int:
        """Compute sum of polynomial series from start_power to end_power."""
        total = 0
        for p in range(start_power, end_power + 1):
            total += self.sum_polynomial(n, p)
        return total

    def compute_bernoulli(self, n: int) -> float:
        """Compute Bernoulli number B_n."""
        return self._compute_bernoulli(n)

    def generate_bernoulli_table(self, limit: int) -> List[float]:
        """Generate table of Bernoulli numbers B_0 to B_{limit-1}."""
        return [self._compute_bernoulli(i) for i in range(limit)]

    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            'max_degree': self.max_degree,
            'cache_size': len(self._sum_cache),
            'bernoulli_count': len(self._bernoulli_cache)
        }


def create_faulhaber_engine(
    max_degree: int = 20,
    cache_size: int = 1000
) -> FaulhaberEngine:
    """
    Factory function to create FaulhaberEngine instance.
    
    Args:
        max_degree: Maximum polynomial degree
        cache_size: Cache size
        
    Returns:
        FaulhaberEngine: Engine instance
    """
    return FaulhaberEngine(max_degree=max_degree, cache_size=cache_size)


if __name__ == "__main__":
    # Demo/test code
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("FaulhaberEngine module loaded successfully")
    logger.info("Example: optimize_summation(power=2, upper_bound=100)")
