"""Mathematical Annihilator Package"""

from orthos.annihilator.faulhaber import FaulhaberEngine
from orthos.annihilator.companion_matrix import CompanionMatrixEngine
from orthos.annihilator.dp_collapser import DPCollapser
from orthos.annihilator.diophantine import DiophantineSolver
from orthos.annihilator.simplex import SimplexOptimizer
from orthos.annihilator.cost_model import CostModel

# Backward-compatible aliases
SimplexSolver = SimplexOptimizer

__all__ = [
    'FaulhaberEngine',
    'CompanionMatrixEngine',
    'DPCollapser',
    'DiophantineSolver',
    'SimplexOptimizer',
    'SimplexSolver',
    'CostModel',
]
