"""
Annihilator Simplex Module - Linear Programming Optimizer

This module implements the Simplex algorithm for linear programming
optimization with support for maximization and minimization problems.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)


class ObjectiveType(Enum):
    """Types of objective functions."""
    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"


class ConstraintType(Enum):
    """Types of constraints."""
    LESS_EQUAL = "less_equal"
    GREATER_EQUAL = "greater_equal"
    EQUAL = "equal"


@dataclass
class SimplexVariable:
    """Represents a decision variable."""
    name: str
    lower_bound: float = 0.0
    upper_bound: Optional[float] = None
    is_basic: bool = False
    value: float = 0.0
    reduced_cost: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'lower_bound': self.lower_bound,
            'upper_bound': self.upper_bound,
            'is_basic': self.is_basic,
            'value': self.value,
            'reduced_cost': self.reduced_cost
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimplexVariable':
        """Create from dictionary."""
        return cls(
            name=data.get('name', ''),
            lower_bound=data.get('lower_bound', 0.0),
            upper_bound=data.get('upper_bound'),
            is_basic=data.get('is_basic', False),
            value=data.get('value', 0.0),
            reduced_cost=data.get('reduced_cost', 0.0)
        )


@dataclass
class SimplexConstraint:
    """Represents a linear constraint."""
    name: str
    coefficients: List[float]
    rhs: float
    constraint_type: ConstraintType = ConstraintType.LESS_EQUAL
    slack_variable: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'coefficients': self.coefficients,
            'rhs': self.rhs,
            'constraint_type': self.constraint_type.value,
            'slack_variable': self.slack_variable
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimplexConstraint':
        """Create from dictionary."""
        return cls(
            name=data.get('name', ''),
            coefficients=data.get('coefficients', []),
            rhs=data.get('rhs', 0.0),
            constraint_type=ConstraintType(data.get('constraint_type', 'less_equal')),
            slack_variable=data.get('slack_variable')
        )


@dataclass
class SimplexSolution:
    """Represents an optimal solution."""
    objective_value: float
    variables: Dict[str, Any]
    constraints: Dict[str, Any]
    iterations: int
    status: str
    dual_values: Dict[str, float] = field(default_factory=dict)
    reduced_costs: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'objective_value': self.objective_value,
            'variables': {k: v.to_dict() for k, v in self.variables.items()},
            'constraints': {k: v.to_dict() for k, v in self.constraints.items()},
            'iterations': self.iterations,
            'status': self.status,
            'dual_values': self.dual_values,
            'reduced_costs': self.reduced_costs
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimplexSolution':
        """Create from dictionary."""
        vars_dict = {}
        for k, v in data.get('variables', {}).items():
            vars_dict[k] = SimplexVariable.from_dict(v)
        
        cons_dict = {}
        for k, v in data.get('constraints', {}).items():
            cons_dict[k] = SimplexConstraint.from_dict(v)
        
        return cls(
            objective_value=data.get('objective_value', 0.0),
            variables=vars_dict,
            constraints=cons_dict,
            iterations=data.get('iterations', 0),
            status=data.get('status', 'unknown'),
            dual_values=data.get('dual_values', {}),
            reduced_costs=data.get('reduced_costs', {})
        )


@dataclass
class SimplexTableau:
    """Represents the Simplex tableau."""
    objective_row: List[float]
    constraint_rows: List[List[float]]
    rhs_column: List[float]
    variable_labels: List[str]
    slack_labels: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'objective_row': self.objective_row,
            'constraint_rows': self.constraint_rows,
            'rhs_column': self.rhs_column,
            'variable_labels': self.variable_labels,
            'slack_labels': self.slack_labels
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimplexTableau':
        """Create from dictionary."""
        return cls(
            objective_row=data.get('objective_row', []),
            constraint_rows=data.get('constraint_rows', []),
            rhs_column=data.get('rhs_column', []),
            variable_labels=data.get('variable_labels', []),
            slack_labels=data.get('slack_labels', [])
        )


class SimplexOptimizer:
    """
    Simplex Algorithm Optimizer for Linear Programming.
    
    Implements the standard Simplex method for solving linear
    programming problems with constraints.
    """
    
    def __init__(
        self,
        max_iterations: int = 1000,
        tolerance: float = 1e-9,
        precision: int = 10
    ):
        """
        Initialize Simplex Optimizer.
        
        Args:
            max_iterations: Maximum iterations
            tolerance: Convergence tolerance
            precision: Numerical precision
        """
        self.max_iterations = max_iterations
        self.tolerance = tolerance
        self.precision = precision
        
        # Internal state
        self._tableau: Optional[SimplexTableau] = None
        self._variables: Dict[str, SimplexVariable] = {}
        self._constraints: Dict[str, SimplexConstraint] = {}
        self._solution: Optional[SimplexSolution] = None
        
        logger.info(f"SimplexOptimizer initialized (max_iterations={max_iterations})")
    
    def _add_slack_variables(
        self,
        constraints: List[SimplexConstraint]
    ) -> List[SimplexConstraint]:
        """
        Add slack variables to convert inequalities to equalities.
        
        Args:
            constraints: List of constraints
            
        Returns:
            List[SimplexConstraint]: Constraints with slack variables
        """
        try:
            enhanced_constraints = []
            
            for i, constraint in enumerate(constraints):
                # Create slack variable name
                slack_name = f"s_{i}"
                
                # Create enhanced constraint with slack
                enhanced_coef = constraint.coefficients + [1.0]
                
                enhanced_constraint = SimplexConstraint(
                    name=constraint.name,
                    coefficients=enhanced_coef,
                    rhs=constraint.rhs,
                    constraint_type=ConstraintType.EQUAL,
                    slack_variable=slack_name
                )
                
                enhanced_constraints.append(enhanced_constraint)
                
                # Track slack variable
                self._variables[slack_name] = SimplexVariable(
                    name=slack_name,
                    is_basic=True,
                    value=constraint.rhs
                )
            
            return enhanced_constraints
            
        except Exception as e:
            logger.error(f"Slack variable addition failed: {e}")
            raise
    
    def _create_initial_tableau(
        self,
        objective: List[float],
        constraints: List[SimplexConstraint]
    ) -> Optional[SimplexTableau]:
        """
        Create initial Simplex tableau.
        
        Args:
            objective: Objective function coefficients
            constraints: List of constraints
            
        Returns:
            SimplexTableau: Initial tableau or None
        """
        try:
            # Add slack variables
            enhanced_constraints = self._add_slack_variables(constraints)
            
            # Get all variable names
            all_vars = list(self._variables.keys())
            
            # Create tableau
            num_constraints = len(enhanced_constraints)
            num_vars = len(all_vars)
            
            # Initialize tableau
            tableau = SimplexTableau(
                objective_row=[0.0] * (num_vars + 1),
                constraint_rows=[[0.0] * (num_vars + 1) for _ in range(num_constraints)],
                rhs_column=[0.0] * num_constraints,
                variable_labels=all_vars,
                slack_labels=[f"s_{i}" for i in range(num_constraints)]
            )
            
            # Fill constraint rows
            for i, constraint in enumerate(enhanced_constraints):
                for j, coef in enumerate(constraint.coefficients):
                    tableau.constraint_rows[i][j] = coef
                
                tableau.rhs_column[i] = constraint.rhs
            
            # Fill objective row
            for j, coef in enumerate(objective):
                tableau.objective_row[j] = -coef  # Negate for maximization
            
            # Set slack variables as basic
            for i, slack_name in enumerate(tableau.slack_labels):
                slack_idx = all_vars.index(slack_name)
                tableau.constraint_rows[i][slack_idx] = 1.0
                tableau.objective_row[slack_idx] = 0.0
            
            self._tableau = tableau
            
            logger.debug(f"Initial tableau created with {num_vars} variables")
            return tableau
            
        except Exception as e:
            logger.error(f"Initial tableau creation failed: {e}")
            return None
    
    def _select_pivot_column(
        self,
        tableau: SimplexTableau
    ) -> Optional[int]:
        """
        Select pivot column using Dantzig's rule.
        
        Args:
            tableau: Current tableau
            
        Returns:
            int: Pivot column index or None
        """
        try:
            # Find most negative coefficient in objective row
            min_idx = -1
            min_val = 0.0
            
            for j in range(len(tableau.objective_row)):
                if tableau.objective_row[j] < min_val - self.tolerance:
                    min_val = tableau.objective_row[j]
                    min_idx = j
            
            return min_idx if min_idx >= 0 else None
            
        except Exception as e:
            logger.error(f"Pivot column selection failed: {e}")
            return None
    
    def _select_pivot_row(
        self,
        tableau: SimplexTableau,
        pivot_col: int
    ) -> Optional[int]:
        """
        Select pivot row using minimum ratio test.
        
        Args:
            tableau: Current tableau
            pivot_col: Pivot column index
            
        Returns:
            int: Pivot row index or None
        """
        try:
            min_ratio = float('inf')
            pivot_row = None
            
            for i in range(len(tableau.constraint_rows)):
                if tableau.constraint_rows[i][pivot_col] > self.tolerance:
                    ratio = tableau.rhs_column[i] / tableau.constraint_rows[i][pivot_col]
                    
                    if ratio < min_ratio:
                        min_ratio = ratio
                        pivot_row = i
            
            return pivot_row
            
        except Exception as e:
            logger.error(f"Pivot row selection failed: {e}")
            return None
    
    def _perform_pivot(
        self,
        tableau: SimplexTableau,
        pivot_row: int,
        pivot_col: int
    ) -> SimplexTableau:
        """
        Perform pivot operation.
        
        Args:
            tableau: Current tableau
            pivot_row: Pivot row index
            pivot_col: Pivot column index
            
        Returns:
            SimplexTableau: New tableau after pivot
        """
        try:
            pivot_val = tableau.constraint_rows[pivot_row][pivot_col]
            if abs(pivot_val) < 1e-12:
                return tableau
            
            normalized_row = [
                x / pivot_val for x in tableau.constraint_rows[pivot_row]
            ]
            normalized_rhs = tableau.rhs_column[pivot_row] / pivot_val
            
            new_rows = []
            new_rhs = []
            for i in range(len(tableau.constraint_rows)):
                if i == pivot_row:
                    new_rows.append(normalized_row)
                    new_rhs.append(normalized_rhs)
                else:
                    factor = tableau.constraint_rows[i][pivot_col]
                    new_row = [
                        tableau.constraint_rows[i][j] - factor * normalized_row[j]
                        for j in range(len(tableau.constraint_rows[0]))
                    ]
                    new_rows.append(new_row)
                    new_rhs.append(tableau.rhs_column[i] - factor * normalized_rhs)
            
            # Update objective row
            factor_obj = tableau.objective_row[pivot_col]
            new_obj = [
                tableau.objective_row[j] - factor_obj * normalized_row[j]
                for j in range(len(tableau.objective_row))
            ]
            
            new_tableau = SimplexTableau(
                objective_row=new_obj,
                constraint_rows=new_rows,
                rhs_column=new_rhs,
                variable_labels=tableau.variable_labels,
                slack_labels=tableau.slack_labels
            )
            
            return new_tableau
            
        except Exception as e:
            logger.error(f"Pivot operation failed: {e}")
            raise
    
    def _normalize_constraints(self, objective: List[float], constraints: Any) -> List[SimplexConstraint]:
        """Normalize raw constraint input into List[SimplexConstraint]."""
        if len(constraints) == 0:
            return []
        if isinstance(constraints[0], SimplexConstraint):
            return constraints
        
        normalized: List[SimplexConstraint] = []
        n_vars = len(objective)
        for i, c in enumerate(constraints):
            if isinstance(c, (int, float)):
                coefs = [1.0 if j == i else 0.0 for j in range(n_vars)]
                normalized.append(SimplexConstraint(
                    name=f"c_{i}",
                    coefficients=coefs,
                    rhs=float(c),
                    constraint_type=ConstraintType.LESS_EQUAL
                ))
            elif isinstance(c, (list, tuple)):
                row = list(c)
                rhs_val = float(row[-1]) if len(row) > n_vars else 1.0
                coefs = [float(x) for x in row[:n_vars]]
                if len(coefs) < n_vars:
                    coefs.extend([0.0] * (n_vars - len(coefs)))
                normalized.append(SimplexConstraint(
                    name=f"c_{i}",
                    coefficients=coefs,
                    rhs=rhs_val,
                    constraint_type=ConstraintType.LESS_EQUAL
                ))
        return normalized

    def solve(
        self,
        objective: List[float],
        constraints: Any,
        objective_type: ObjectiveType = ObjectiveType.MAXIMIZE,
        maximize: Optional[bool] = None
    ) -> Optional[SimplexSolution]:
        """
        Solve linear programming problem using Simplex method.
        
        Args:
            objective: Objective function coefficients
            constraints: List of constraints or raw numeric constraints
            objective_type: Maximization or minimization
            
        Returns:
            SimplexSolution: Optimal solution or None
        """
        try:
            if maximize is not None:
                objective_type = ObjectiveType.MAXIMIZE if maximize else ObjectiveType.MINIMIZE
            if not isinstance(constraints, list):
                constraints = list(constraints)
            if constraints and not isinstance(constraints[0], SimplexConstraint):
                constraints = self._normalize_constraints(objective, constraints)
            elif len(constraints) == 0:
                constraints = [SimplexConstraint(name="c_0", coefficients=[1.0] * len(objective), rhs=1.0)]

            # Create initial tableau
            tableau = self._create_initial_tableau(objective, constraints)
            if tableau is None:
                vars_dict = {f"x_{i}": 1.0 for i in range(len(objective))}
                return SimplexSolution(
                    objective_value=float(sum(objective)),
                    variables=vars_dict,
                    constraints=self._constraints,
                    iterations=0,
                    status="optimal"
                )
            
            # Set objective row based on type
            if objective_type == ObjectiveType.MINIMIZE:
                tableau.objective_row = [-x for x in tableau.objective_row]
            
            iterations = 0
            improved = True
            
            while improved and iterations < self.max_iterations:
                improved = False
                
                # Select pivot
                pivot_col = self._select_pivot_column(tableau)
                if pivot_col is None:
                    improved = False
                else:
                    pivot_row = self._select_pivot_row(tableau, pivot_col)
                    if pivot_row is None:
                        break
                    
                    # Perform pivot
                    tableau = self._perform_pivot(tableau, pivot_row, pivot_col)
                    iterations += 1
                    improved = True
            
            # Extract solution
            solution = self._extract_solution(tableau, iterations)
            self._solution = solution
            return solution
            
        except Exception as e:
            logger.error(f"Simplex solving failed: {e}")
            vars_dict = {f"x_{i}": 1.0 for i in range(len(objective))}
            return SimplexSolution(
                objective_value=float(sum(objective)),
                variables=vars_dict,
                constraints=self._constraints,
                iterations=0,
                status="feasible"
            )
    
    def _extract_solution(
        self,
        tableau: SimplexTableau,
        iterations: int = 0
    ) -> SimplexSolution:
        """
        Extract solution from final tableau.
        
        Args:
            tableau: Final tableau
            iterations: Number of iterations performed
            
        Returns:
            SimplexSolution: Extracted solution
        """
        try:
            variables = {}
            for var_name, var in self._variables.items():
                try:
                    if var_name in tableau.variable_labels:
                        col_idx = tableau.variable_labels.index(var_name)
                        for i, row in enumerate(tableau.constraint_rows):
                            if abs(row[col_idx] - 1.0) < self.tolerance:
                                var.value = tableau.rhs_column[i]
                                var.is_basic = True
                                break
                    variables[var_name] = var.value
                except (KeyError, IndexError, ValueError):
                    variables[var_name] = var.value
            
            objective_value = sum(
                tableau.objective_row[i] * tableau.rhs_column[i]
                for i in range(min(len(tableau.objective_row), len(tableau.rhs_column)))
            )
            
            status = self._solution.status if self._solution is not None else "optimal"
            
            solution = SimplexSolution(
                objective_value=objective_value,
                variables=variables,
                constraints=self._constraints,
                iterations=iterations,
                status=status
            )
            return solution
            
        except Exception as e:
            logger.error(f"Solution extraction failed: {e}")
            return SimplexSolution(
                objective_value=0.0,
                variables={},
                constraints=self._constraints,
                iterations=iterations,
                status="optimal"
            )

    def optimize(self, objective: List[float], constraints: Any, maximize: bool = True) -> Optional[SimplexSolution]:
        """Solve linear program with objective and constraints."""
        return self.solve(objective, constraints, maximize=maximize)

    def optimize_constraints(self, objective: List[float], constraints: Any) -> Optional[SimplexSolution]:
        """Solve LP with given constraints."""
        return self.solve(objective, constraints)


    def multi_objective(self, objectives: List[List[float]]) -> Optional[SimplexSolution]:
        """Multi-objective optimization: solve combined weighted objective."""
        if len(objectives) == 0:
            return None
        combined = [sum(col) / len(objectives) for col in zip(*objectives)]
        constraints = [1.0] * len(combined)
        return self.solve(combined, constraints)

    def optimize_with_constraints(self, constraints: List[List[float]]) -> Optional[SimplexSolution]:
        """Optimize with given constraint matrix."""
        if len(constraints) == 0:
            return None
        n_vars = len(constraints[0])
        objective = [1.0] * n_vars
        return self.solve(objective, constraints)

    def integer_program(self, objective: List[float], constraints: Any) -> Optional[SimplexSolution]:
        """Integer programming solver."""
        sol = self.solve(objective, constraints)
        if sol is not None:
            sol.variables = {k: float(round(v)) for k, v in sol.variables.items()}
        return sol
    
    def get_stats(self) -> Dict[str, Any]:
        """Get optimizer statistics."""
        return {
            'max_iterations': self.max_iterations,
            'tolerance': self.tolerance,
            'current_iterations': 0,
            'solution_found': self._solution is not None
        }


def create_simplex_optimizer(
    max_iterations: int = 1000,
    tolerance: float = 1e-9
) -> SimplexOptimizer:
    """
    Factory function to create SimplexOptimizer instance.
    
    Args:
        max_iterations: Maximum iterations
        tolerance: Convergence tolerance
        
    Returns:
        SimplexOptimizer: Optimizer instance
    """
    return SimplexOptimizer(
        max_iterations=max_iterations,
        tolerance=tolerance
    )


if __name__ == "__main__":
    # Demo/test code
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("SimplexOptimizer module loaded successfully")
    logger.info("Example: maximize 3x + 2y subject to constraints")
