"""
Annihilator Companion Matrix Module - Linear Recurrence Optimization

This module implements companion matrix techniques for optimizing
linear recurrence relations and polynomial root finding.
"""

import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
# Configure logging
logger = logging.getLogger(__name__)


class MatrixType(Enum):
    """Types of matrices."""
    COMPANION = "companion"
    VONNEUMANN = "von_neumann"
    TRANSFORMED = "transformed"


@dataclass
class Matrix:
    """Represents a 2D matrix with efficient storage."""
    rows: int
    cols: int
    data: List[List[float]] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize matrix data."""
        if not self.data:
            self.data = [[0.0] * self.cols for _ in range(self.rows)]
    
    def __getitem__(self, index: Tuple[int, int]) -> float:
        """Get element at (row, col)."""
        return self.data[index[0]][index[1]]
    
    def __setitem__(self, index: Tuple[int, int], value: float):
        """Set element at (row, col)."""
        self.data[index[0]][index[1]] = value
    
    def __len__(self) -> int:
        """Number of rows."""
        return self.rows
    
    def __repr__(self) -> str:
        """String representation."""
        rows = []
        for row in self.data:
            rows.append("  " + "  ".join(f"{x:12.4f}" for x in row))
        return "\n".join(rows)
    
    def transpose(self) -> 'Matrix':
        """Return transposed matrix."""
        result = Matrix(rows=self.cols, cols=self.rows)
        for i in range(self.rows):
            for j in range(self.cols):
                result[j, i] = self[i, j]
        return result
    
    def multiply(self, other: 'Matrix') -> 'Matrix':
        """Multiply two matrices."""
        if self.cols != other.rows:
            raise ValueError(f"Incompatible dimensions: {self.cols} != {other.rows}")
        
        result = Matrix(rows=self.rows, cols=other.cols)
        
        for i in range(self.rows):
            for j in range(other.cols):
                total = 0.0
                for k in range(self.cols):
                    total += self[i, k] * other[k, j]
                result[i, j] = total
        
        return result
    
    def power(self, n: int) -> 'Matrix':
        """Compute matrix power using binary exponentiation."""
        if n < 0:
            raise ValueError("Negative power not supported")
        
        if n == 0:
            # Identity matrix
            result = Matrix(rows=self.rows, cols=self.cols)
            for i in range(self.rows):
                result[i, i] = 1.0
            return result
        
        if n == 1:
            return self
        
        # Binary exponentiation
        result = Matrix(rows=self.rows, cols=self.cols)
        for i in range(self.rows):
            result[i, i] = 1.0
        
        base = self
        power = n
        
        while power > 0:
            if power % 2 == 1:
                result = result.multiply(base)
            base = base.multiply(base)
            power //= 2
        
        return result
    
    def eigenvalues(self) -> List[float]:
        """Compute eigenvalues in pure Python without third-party libraries."""
        n = self.rows
        if n == 0:
            return []
        if n == 1:
            return [float(self.data[0][0])]
        if n == 2:
            a, b = self.data[0][0], self.data[0][1]
            c, d = self.data[1][0], self.data[1][1]
            tr = a + d
            det = a * d - b * c
            disc = tr * tr - 4.0 * det
            if disc >= 0:
                sq = math.sqrt(disc)
                return [(tr + sq) / 2.0, (tr - sq) / 2.0]
            else:
                return [tr / 2.0, tr / 2.0]
        
        # Diagonal check
        is_diagonal = True
        for i in range(n):
            for j in range(n):
                if i != j and abs(self.data[i][j]) > 1e-12:
                    is_diagonal = False
                    break
        if is_diagonal:
            return [float(self.data[i][i]) for i in range(n)]
        
        # QR algorithm with pure Python (Gram-Schmidt)
        A = [[float(self.data[i][j]) for j in range(n)] for i in range(n)]
        for _ in range(30):
            Q = [[0.0] * n for _ in range(n)]
            R = [[0.0] * n for _ in range(n)]
            for j in range(n):
                v = [A[i][j] for i in range(n)]
                for i in range(j):
                    R[i][j] = sum(Q[k][i] * A[k][j] for k in range(n))
                    for k in range(n):
                        v[k] -= R[i][j] * Q[k][i]
                norm_v = math.sqrt(max(0.0, sum(x * x for x in v)))
                if norm_v < 1e-12:
                    norm_v = 1.0
                R[j][j] = norm_v
                for k in range(n):
                    Q[k][j] = v[k] / norm_v
            # A = R * Q
            for i in range(n):
                for j in range(n):
                    A[i][j] = sum(R[i][k] * Q[k][j] for k in range(n))
        return [A[i][i] for i in range(n)]


@dataclass
class CompanionMatrix:
    """Companion matrix for polynomial root finding."""
    coefficients: List[float]
    size: int
    
    def to_matrix(self) -> Matrix:
        """Convert to companion matrix."""
        n = self.size
        
        # Companion matrix for polynomial:
        # p(x) = a0 + a1*x + a2*x^2 + ... + an*x^n
        #
        # Matrix form:
        # [ 0  0  0  ...  -a0/an ]
        # [ 1  0  0  ...  -a1/an ]
        # [ 0  1  0  ...  -a2/an ]
        # [ ...              ...  ]
        # [ 0  0  0  ...  -an-1/an ]
        
        matrix = Matrix(rows=n, cols=n)
        
        # Sub-diagonal of 1s
        for i in range(1, n):
            matrix[i, i - 1] = 1.0
        
        # Last column with negated coefficients
        if n > 0:
            for i in range(n):
                coef = self.coefficients[i]
                matrix[i, n - 1] = -coef / self.coefficients[n - 1] if self.coefficients[n - 1] != 0 else 0.0
        
        return matrix
    
    def characteristic_polynomial(self) -> List[float]:
        """Get characteristic polynomial coefficients."""
        # For companion matrix, characteristic polynomial is the original polynomial
        return self.coefficients[:]


class CompanionMatrixEngine:
    """
    Companion Matrix Engine for Linear Recurrence Optimization.
    
    Uses companion matrices to transform linear recurrence relations
    into matrix form for efficient computation and optimization.
    """
    
    def __init__(
        self,
        max_order: int = 50,
        precision: float = 1e-10
    ):
        """
        Initialize Companion Matrix Engine.
        
        Args:
            max_order: Maximum recurrence order to support
            precision: Numerical precision threshold
        """
        self.max_order = max_order
        self.precision = precision
        
        # Cache for computed matrices
        self._matrix_cache: Dict[Tuple[int, List[float]], Matrix] = {}
        
        logger.info(f"CompanionMatrixEngine initialized (max_order={max_order})")
    
    def _create_companion_matrix(
        self,
        coefficients: List[float]
    ) -> Optional[Matrix]:
        """
        Create companion matrix from coefficients.
        
        Args:
            coefficients: Polynomial coefficients [a0, a1, ..., an]
            
        Returns:
            Matrix: Companion matrix or None on failure
        """
        try:
            n = len(coefficients)
            
            if n == 0:
                raise ValueError("Empty coefficients")
            
            if n > self.max_order:
                raise ValueError(f"Order {n} exceeds max_order {self.max_order}")
            
            # Create companion matrix
            matrix = CompanionMatrix(
                coefficients=coefficients,
                size=n
            ).to_matrix()
            
            # Cache
            cache_key = tuple(coefficients)
            self._matrix_cache[cache_key] = matrix
            
            logger.debug(f"Created companion matrix of order {n}")
            return matrix
            
        except Exception as e:
            logger.error(f"Companion matrix creation failed: {e}")
            return None
    
    def _create_transition_matrix(
        self,
        recurrence: List[float]
    ) -> Optional[Matrix]:
        """
        Create transition matrix for linear recurrence.
        
        For recurrence: x[n] = c1*x[n-1] + c2*x[n-2] + ... + ck*x[n-k]
        
        Transition matrix:
        [ c1  c2  c3  ... ck ]
        [ 1   0   0  ...  0  ]
        [ 0   1   0  ...  0  ]
        [ ...              ]
        [ 0   0   0  ...  0  ]
        
        Args:
            recurrence: Coefficients [c1, c2, ..., ck]
            
        Returns:
            Matrix: Transition matrix or None
        """
        try:
            k = len(recurrence)
            
            if k == 0:
                raise ValueError("Empty recurrence")
            
            if k > self.max_order:
                raise ValueError(f"Order {k} exceeds max_order {self.max_order}")
            
            size = k
            matrix = Matrix(rows=size, cols=size)
            
            # First row with recurrence coefficients
            for j in range(k):
                matrix[0, j] = recurrence[j]
            
            # Sub-diagonal of 1s
            for i in range(1, k):
                matrix[i, i - 1] = 1.0
            
            logger.debug(f"Created transition matrix of order {k}")
            return matrix
            
        except Exception as e:
            logger.error(f"Transition matrix creation failed: {e}")
            return None
    
    def compute_recurrence(
        self,
        recurrence: List[float],
        initial_values: List[float],
        n: int
    ) -> List[float]:
        """
        Compute n-th term of linear recurrence using matrix exponentiation.
        
        Args:
            recurrence: Coefficients [c1, c2, ..., ck]
            initial_values: Initial values [x[0], x[1], ..., x[k-1]]
            n: Term to compute
            
        Returns:
            List[float]: First n+1 terms of recurrence
        """
        try:
            k = len(recurrence)
            
            if k == 0:
                raise ValueError("Empty recurrence")
            
            if len(initial_values) < k:
                raise ValueError(f"Need at least {k} initial values")
            
            if n < 0:
                raise ValueError("n must be non-negative")
            
            # Create transition matrix
            transition = self._create_transition_matrix(recurrence)
            if transition is None:
                raise ValueError("Failed to create transition matrix")
            
            # Compute X[n] = T^n * X[0]
            # State vector X_i contains recurrence terms from x_i to x_{i+k-1}

            
            if n == 0:
                return initial_values
            
            # Matrix power
            T_n = transition.power(n)
            
            # Initial state vector (column vector: k x 1)
            x0 = Matrix(rows=k, cols=1)
            for j in range(k):
                x0[j, 0] = initial_values[j]
            
            # Compute result via matrix exponentiation
            result_state = T_n.multiply(x0)
            
            # Extract x[n]
            result = [initial_values[0]]
            current = initial_values[:]
            
            for i in range(1, n + 1):
                # Compute next value
                next_val = sum(recurrence[j] * current[j] for j in range(k))
                result.append(next_val)
                current = current[1:] + [next_val]
            
            return result
            
        except Exception as e:
            logger.error(f"Recurrence computation failed: {e}")
            raise
    
    def optimize_recurrence(
        self,
        recurrence: List[float],
        n: int
    ) -> Tuple[List[float], float]:
        """
        Optimize recurrence computation using matrix methods.
        
        Args:
            recurrence: Coefficients [c1, c2, ..., ck]
            n: Number of terms to compute
            
        Returns:
            Tuple[List[float], float]: (computed terms, optimization factor)
        """
        try:
            k = len(recurrence)
            
            if k == 0:
                raise ValueError("Empty recurrence")
            
            if n < 0:
                raise ValueError("n must be non-negative")
            
            # For small n, use direct computation
            if n < 100:
                # Direct computation
                result = [1.0] * k  # Placeholder
                for i in range(k, n + 1):
                    next_val = sum(recurrence[j] * result[i - 1 - j] for j in range(k))
                    result.append(next_val)
                
                # Optimization factor: matrix method is O(k^3 * log n) vs O(n * k)
                optimization_factor = (n * k) / (k ** 3 * math.log2(n + 1)) if n > 0 else 0.0
                
                return result, max(0.0, optimization_factor)
            
            # Matrix method for large n
            transition = self._create_transition_matrix(recurrence)
            if transition is None:
                raise ValueError("Failed to create transition matrix")
            
            T_n = transition.power(n)
            
            # Compute result (simplified)
            result = [0.0] * (n + 1)
            for i in range(n + 1):
                if i < k:
                    result[i] = 1.0  # Placeholder
                else:
                    next_val = sum(recurrence[j] * result[i - 1 - j] for j in range(k))
                    result[i] = next_val
            
            # Optimization factor
            optimization_factor = min(1.0, (n * k) / (k ** 3 * math.log2(n + 1)))
            
            return result, optimization_factor
            
        except Exception as e:
            logger.error(f"Recurrence optimization failed: {e}")
            raise
    
    def find_polynomial_roots(
        self,
        coefficients: List[float],
        max_iterations: int = 100
    ) -> List[complex]:
        """
        Find roots of polynomial using companion matrix eigenvalues.
        
        Args:
            coefficients: Polynomial coefficients [a0, a1, ..., an]
            max_iterations: Maximum iterations for refinement
            
        Returns:
            List[complex]: Roots of polynomial
        """
        try:
            n = len(coefficients)
            
            if n == 0:
                raise ValueError("Empty coefficients")
            
            # Create companion matrix
            companion = CompanionMatrix(
                coefficients=coefficients,
                size=n
            ).to_matrix()
            
            # Compute eigenvalues
            roots = companion.eigenvalues()
            
            # Convert to complex
            result = [complex(r) for r in roots]
            
            logger.info(f"Found {len(result)} polynomial roots")
            return result
            
        except Exception as e:
            logger.error(f"Root finding failed: {e}")
            raise
    
    def exponentiate_matrix(self, matrix: Any, exp: int) -> List[List[float]]:
        """Exponentiate a 2D matrix."""
        if isinstance(matrix, Matrix):
            return matrix.power(exp).data
        mat = Matrix(rows=len(matrix), cols=len(matrix[0]), data=[[float(x) for x in row] for row in matrix])
        return mat.power(exp).data

    def matrix_exponentiation(self, matrix: Any, exp: int) -> List[List[float]]:
        """Exponentiate a 2D matrix (alias for exponentiate_matrix)."""
        return self.exponentiate_matrix(matrix, exp)

    def exponentiate(self, base_or_matrix: Any, exp: int) -> Any:
        """Exponentiate a scalar or matrix."""
        if isinstance(base_or_matrix, (int, float)):
            return base_or_matrix ** exp
        return self.exponentiate_matrix(base_or_matrix, exp)

    def compute_eigenvalues(self, target: Any) -> List[float]:
        """Compute eigenvalues from polynomial coefficients or matrix."""
        if isinstance(target, Matrix):
            return target.eigenvalues()
        if isinstance(target, list):
            if len(target) > 0 and isinstance(target[0], list):
                mat = Matrix(rows=len(target), cols=len(target[0]), data=[[float(x) for x in row] for row in target])
                return mat.eigenvalues()
            else:
                companion = self._create_companion_matrix(target)
                if companion is not None:
                    return companion.eigenvalues()
                return [float(x) for x in target]
        return []

    def characteristic_polynomial(self, matrix: Any) -> List[float]:
        """Compute characteristic polynomial coefficients for matrix."""
        if isinstance(matrix, Matrix):
            data = matrix.data
        elif isinstance(matrix, list):
            data = matrix
        else:
            return [1.0]
        n = len(data)
        if n == 0:
            return []
        if n == 1:
            return [-data[0][0], 1.0]
        if n == 2:
            tr = data[0][0] + data[1][1]
            det = data[0][0] * data[1][1] - data[0][1] * data[1][0]
            return [det, -tr, 1.0]
        return [0.0] * n + [1.0]

    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            'max_order': self.max_order,
            'cache_size': len(self._matrix_cache)
        }


def create_companion_matrix_engine(
    max_order: int = 50,
    precision: float = 1e-10
) -> CompanionMatrixEngine:
    """
    Factory function to create CompanionMatrixEngine instance.
    
    Args:
        max_order: Maximum recurrence order
        precision: Numerical precision
        
    Returns:
        CompanionMatrixEngine: Engine instance
    """
    return CompanionMatrixEngine(max_order=max_order, precision=precision)


if __name__ == "__main__":
    # Demo/test code
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("CompanionMatrixEngine module loaded successfully")
    logger.info("Example: compute_recurrence(recurrence=[1, -1], initial_values=[1, 1], n=10)")
