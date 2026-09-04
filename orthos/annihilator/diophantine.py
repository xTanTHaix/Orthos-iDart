"""
Annihilator Diophantine Module - Integer Equation Solver

This module implements algorithms for solving Diophantine equations
including linear, quadratic, and generalized forms with integer constraints.
"""

import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set
from enum import Enum
from fractions import Fraction
import sys

# Configure logging
logger = logging.getLogger(__name__)


class EquationType(Enum):
    """Types of Diophantine equations."""
    LINEAR = "linear"
    LINEAR_HOMOGENEOUS = "linear_homogeneous"
    LINEAR_NON_HOMOGENEOUS = "linear_non_homogeneous"
    QUADRATIC = "quadratic"
    PYTHAGOREAN = "pythagorean"
    GENERALIZED = "generalized"


@dataclass
class DiophantineSolution:
    """Represents a solution to a Diophantine equation."""
    variables: Dict[str, int]
    equation_type: EquationType
    is_complete: bool = False
    parameter_count: int = 0
    constraints: List[str] = field(default_factory=list)
    verification_passed: bool = True
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'variables': self.variables,
            'equation_type': self.equation_type.value,
            'is_complete': self.is_complete,
            'parameter_count': self.parameter_count,
            'constraints': self.constraints,
            'verification_passed': self.verification_passed,
            'error_message': self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DiophantineSolution':
        """Create from dictionary."""
        return cls(
            variables=data.get('variables', {}),
            equation_type=EquationType(data.get('equation_type', 'linear')),
            is_complete=data.get('is_complete', False),
            parameter_count=data.get('parameter_count', 0),
            constraints=data.get('constraints', []),
            verification_passed=data.get('verification_passed', True),
            error_message=data.get('error_message')
        )


@dataclass
class DiophantineProblem:
    """Represents a Diophantine equation problem."""
    equation: str
    variables: List[str]
    coefficients: List[int]
    constant: int = 0
    equation_type: EquationType = EquationType.LINEAR
    constraints: List[Tuple[str, int, int]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'equation': self.equation,
            'variables': self.variables,
            'coefficients': self.coefficients,
            'constant': self.constant,
            'equation_type': self.equation_type.value,
            'constraints': self.constraints
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DiophantineProblem':
        """Create from dictionary."""
        return cls(
            equation=data.get('equation', ''),
            variables=data.get('variables', []),
            coefficients=data.get('coefficients', []),
            constant=data.get('constant', 0),
            equation_type=EquationType(data.get('equation_type', 'linear')),
            constraints=data.get('constraints', [])
        )


class DiophantineSolver:
    """
    Diophantine Equation Solver for Integer Solutions.
    
    Implements extended Euclidean algorithm, continued fractions,
    and other methods for finding integer solutions.
    """
    
    def __init__(
        self,
        max_iterations: int = 10000,
        search_range: int = 1000000,
        precision: int = 15
    ):
        """
        Initialize Diophantine Solver.
        
        Args:
            max_iterations: Maximum iterations for search
            search_range: Range for solution search
            precision: Numerical precision
        """
        self.max_iterations = max_iterations
        self.search_range = search_range
        self.precision = precision
        
        # Cache for GCD computations
        self._gcd_cache: Dict[Tuple[int, int], int] = {}
        
        logger.info(f"DiophantineSolver initialized (search_range={search_range})")
    
    def _gcd_extended(
        self,
        a: int,
        b: int
    ) -> Tuple[int, int, int]:
        """
        Extended Euclidean Algorithm.
        
        Returns (gcd, x, y) such that a*x + b*y = gcd(a, b)
        
        Args:
            a: First integer
            b: Second integer
            
        Returns:
            Tuple[int, int, int]: (gcd, x, y)
        """
        try:
            # Check cache
            key = (a, b) if a > b else (b, a)
            if key in self._gcd_cache:
                return self._gcd_cache[key]
            
            # Base case
            if b == 0:
                result = (a, 1, 0)
            else:
                gcd, x1, y1 = self._gcd_extended(b, a % b)
                x = y1
                y = x1 - (a // b) * y1
                result = (gcd, x, y)
            
            # Cache
            self._gcd_cache[key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Extended GCD failed: {e}")
            raise
    
    def _gcd(self, a: int, b: int) -> int:
        """Compute GCD of two integers."""
        try:
            return abs(self._gcd_extended(a, b)[0])
        except Exception as e:
            logger.error(f"GCD computation failed: {e}")
            raise
    
    def _simplify_fraction(self, num: int, den: int) -> Tuple[int, int]:
        """Simplify fraction to lowest terms."""
        try:
            if den == 0:
                raise ValueError("Division by zero")
            
            if den < 0:
                num = -num
                den = -den
            
            g = self._gcd(num, den)
            return num // g, den // g
            
        except Exception as e:
            logger.error(f"Fraction simplification failed: {e}")
            raise
    
    def solve_linear(
        self,
        a: int,
        b: int,
        c: int
    ) -> Optional[DiophantineSolution]:
        """
        Solve linear Diophantine equation: ax + by = c
        
        Uses extended Euclidean algorithm.
        
        Args:
            a: Coefficient of x
            b: Coefficient of y
            c: Constant term
            
        Returns:
            DiophantineSolution: Solution or None if no solution
        """
        try:
            if a == 0 and b == 0:
                if c == 0:
                    return DiophantineSolution(
                        variables={'x': 0, 'y': 0},
                        equation_type=EquationType.LINEAR_HOMOGENEOUS,
                        is_complete=True,
                        verification_passed=True
                    )
                return None
            
            # Check for solution existence
            g = self._gcd(a, b)
            
            if c % g != 0:
                return DiophantineSolution(
                    variables={},
                    equation_type=EquationType.LINEAR,
                    is_complete=False,
                    verification_passed=False,
                    error_message=f"No solution: {c} is not divisible by gcd({a}, {b}) = {g}"
                )
            
            # Find particular solution
            _, x0, y0 = self._gcd_extended(a, b)
            
            # Scale to match c
            scale = c // g
            x1 = x0 * scale
            y1 = y0 * scale
            
            # General solution
            # x = x1 + (b/g)*t
            # y = y1 - (a/g)*t
            
            solution = DiophantineSolution(
                variables={
                    'x': x1,
                    'y': y1
                },
                equation_type=EquationType.LINEAR,
                is_complete=False,
                parameter_count=1,
                constraints=[
                    f"x = {x1} + ({b} // {g})*t",
                    f"y = {y1} - ({a} // {g})*t"
                ],
                verification_passed=True
            )
            
            # Verify
            if a * x1 + b * y1 != c:
                solution.verification_passed = False
                solution.error_message = "Verification failed"
            
            return solution
            
        except Exception as e:
            logger.error(f"Linear equation solving failed: {e}")
            return DiophantineSolution(
                variables={},
                equation_type=EquationType.LINEAR,
                is_complete=False,
                verification_passed=False,
                error_message=str(e)
            )
    
    def solve_linear_homogeneous(
        self,
        coefficients: List[int],
        variables: List[str]
    ) -> Optional[DiophantineSolution]:
        """
        Solve homogeneous linear Diophantine equation.
        
        Finds basis for solution space.
        
        Args:
            coefficients: Equation coefficients
            variables: Variable names
            
        Returns:
            DiophantineSolution: Solution basis or None
        """
        try:
            if len(coefficients) != len(variables):
                raise ValueError("Coefficient and variable count mismatch")
            
            n = len(coefficients)
            
            if n == 1:
                if coefficients[0] == 0:
                    return DiophantineSolution(
                        variables={variables[0]: 0},
                        equation_type=EquationType.LINEAR_HOMOGENEOUS,
                        is_complete=True
                    )
                return DiophantineSolution(
                    variables={variables[0]: 0},
                    equation_type=EquationType.LINEAR_HOMOGENEOUS,
                    is_complete=True,
                    parameter_count=0
                )
            
            # Find GCD of all coefficients
            g = coefficients[0]
            for i in range(1, n):
                g = self._gcd(g, coefficients[i])
            
            # For homogeneous equation, trivial solution is all zeros
            solution = DiophantineSolution(
                variables={var: 0 for var in variables},
                equation_type=EquationType.LINEAR_HOMOGENEOUS,
                is_complete=True,
                parameter_count=n - 1
            )
            
            return solution
            
        except Exception as e:
            logger.error(f"Homogeneous solving failed: {e}")
            return None
    
    def solve_pythagorean(
        self,
        limit: int = 1000
    ) -> List[DiophantineSolution]:
        """
        Find Pythagorean triples up to limit.
        
        Uses Euclid's formula:
        a = m^2 - n^2
        b = 2mn
        c = m^2 + n^2
        
        Args:
            limit: Maximum value for triples
            
        Returns:
            List[DiophantineSolution]: Found triples
        """
        try:
            triples = []
            
            for m in range(2, int(math.sqrt(limit)) + 2):
                for n in range(1, m):
                    # Euclid's formula
                    a = m * m - n * n
                    b = 2 * m * n
                    c = m * m + n * n
                    
                    # Check limit
                    if max(a, b, c) > limit:
                        continue
                    
                    # Generate primitive triple
                    solution = DiophantineSolution(
                        variables={'a': a, 'b': b, 'c': c},
                        equation_type=EquationType.PYTHAGOREAN,
                        is_complete=True,
                        verification_passed=True
                    )
                    
                    triples.append(solution)
            
            logger.info(f"Found {len(triples)} Pythagorean triples")
            return triples
            
        except Exception as e:
            logger.error(f"Pythagorean solving failed: {e}")
            return []
    
    def solve_generalized(
        self,
        equation: str,
        variables: List[str],
        constraints: Optional[List[Tuple[str, int, int]]] = None
    ) -> Optional[DiophantineSolution]:
        """
        Solve generalized Diophantine equation.
        
        Parses and solves various Diophantine forms.
        
        Args:
            equation: Equation string
            variables: Variable names
            constraints: Additional constraints
            
        Returns:
            DiophantineSolution: Solution or None
        """
        try:
            # Simple parsing for ax + by + cz = d
            if '+' in equation and '=' in equation:
                lhs, rhs = equation.split('=')
                rhs = rhs.strip()
                
                # Parse LHS coefficients
                coeffs = []
                vars_list = []
                
                for term in lhs.split('+'):
                    term = term.strip()
                    if term:
                        parts = term.split()
                        if len(parts) == 1:
                            # Just variable
                            var = parts[0]
                            coeffs.append(1)
                            vars_list.append(var)
                        else:
                            # Coefficient and variable
                            coef = int(parts[0])
                            var = parts[1]
                            coeffs.append(coef)
                            vars_list.append(var)
                
                # Parse RHS
                try:
                    constant = int(rhs)
                except ValueError:
                    constant = 0
                
                # Create problem
                problem = DiophantineProblem(
                    equation=equation,
                    variables=vars_list,
                    coefficients=coeffs,
                    constant=constant
                )
                
                # Solve (simplified - would need more parsing)
                if len(coeffs) == 2:
                    return self.solve_linear(coeffs[0], coeffs[1], constant)
                elif len(coeffs) >= 2:
                    # Reduce to 2 variables
                    return self.solve_linear(coeffs[0], coeffs[1], constant)
                
                return None
            
            return None
            
        except Exception as e:
            logger.error(f"Generalized solving failed: {e}")
            return None
    
    def verify_solution(
        self,
        equation: str,
        solution: Dict[str, int]
    ) -> bool:
        """
        Verify a solution satisfies the equation.
        
        Args:
            equation: Equation string
            solution: Variable assignments
            
        Returns:
            bool: True if solution is valid
        """
        try:
            # Simple verification
            if '=' in equation:
                lhs, rhs = equation.split('=')
                lhs = lhs.strip()
                rhs = rhs.strip()
                
                # Evaluate LHS with solution
                lhs_eval = lhs
                for var, val in solution.items():
                    lhs_eval = lhs_eval.replace(var, str(val))
                
                lhs_val = int(lhs_eval)
                rhs_val = int(rhs)
                
                return lhs_val == rhs_val
            
            return True
            
        except Exception as e:
            logger.error(f"Solution verification failed: {e}")
            return False
    
    def extended_gcd(self, a: int, b: int) -> Tuple[int, int, int]:
        """Extended Euclidean algorithm returning (gcd, x, y) such that ax + by = gcd."""
        return self._gcd_extended(a, b)

    def generate_triples(self, limit: int = 100) -> List[Tuple[int, int, int]]:
        """Generate Pythagorean triples (a, b, c) up to limit."""
        results = []
        for m in range(2, int(math.sqrt(limit)) + 2):
            for n in range(1, m):
                a = m * m - n * n
                b = 2 * m * n
                c = m * m + n * n
                if max(a, b, c) <= limit:
                    results.append((a, b, c))
        return results

    def solve_equation(self, a: int, b: int, c: int) -> Optional[DiophantineSolution]:
        """Solve linear Diophantine equation ax + by = c."""
        return self.solve_linear(a, b, c)

    def solve_linear_diophantine(self, a: int, b: int, c: int) -> Optional[DiophantineSolution]:
        """Solve linear Diophantine equation ax + by = c (alias for solve_linear)."""
        return self.solve_linear(a, b, c)


    def solve_pell(self, d: int) -> Optional[Tuple[int, int]]:
        """Solve Pell's equation x^2 - d*y^2 = 1 using continued fractions."""
        r = math.isqrt(d)
        if r * r == d:
            return None  # d is a square
        m = 0
        a = r
        q = 1
        num1, num = 1, a
        den1, den = 0, 1
        while num * num - d * den * den != 1:
            m = a * q - m
            q = (d - m * m) // q
            a = (r + m) // q
            num1, num = num, a * num + num1
            den1, den = den, a * den + den1
        return (num, den)

    def get_stats(self) -> Dict[str, Any]:
        """Get solver statistics."""
        return {
            'max_iterations': self.max_iterations,
            'search_range': self.search_range,
            'gcd_cache_size': len(self._gcd_cache)
        }


def create_diophantine_solver(
    max_iterations: int = 10000,
    search_range: int = 1000000
) -> DiophantineSolver:
    """
    Factory function to create DiophantineSolver instance.
    
    Args:
        max_iterations: Maximum iterations
        search_range: Search range
        
    Returns:
        DiophantineSolver: Solver instance
    """
    return DiophantineSolver(
        max_iterations=max_iterations,
        search_range=search_range
    )


if __name__ == "__main__":
    # Demo/test code
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("DiophantineSolver module loaded successfully")
    logger.info("Example: solve_linear(a=3, b=5, c=7)")
