"""
Scope Analysis Module for Orthos Compiler
Handles variable scope detection, binding, and lifetime analysis
"""

import ast
import logging
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class ScopeType(Enum):
    """Types of scopes in the program"""
    GLOBAL = "global"
    MODULE = "module"
    FUNCTION = "function"
    CLASS = "class"
    COMPREHENSION = "comprehension"
    LAMBDA = "lambda"


@dataclass
class VariableBinding:
    """Represents a variable binding with scope information"""
    name: str
    scope_type: ScopeType
    scope_depth: int
    line_number: int
    is_global: bool = False
    is_nonlocal: bool = False
    is_local: bool = True
    assignments: List[int] = field(default_factory=list)
    references: List[int] = field(default_factory=list)
    definition_line: int = 0
    
    def is_read(self) -> bool:
        """Check if variable is read before write"""
        return len(self.references) > 0
    
    def is_written(self) -> bool:
        """Check if variable is written"""
        return len(self.assignments) > 0


@dataclass
class Scope:
    """Represents a scope with its variables"""
    scope_type: ScopeType
    depth: int
    parent: Optional['Scope'] = None
    variables: Dict[str, VariableBinding] = field(default_factory=dict)
    line_number: int = 0
    is_closure: bool = False
    captured_vars: List[str] = field(default_factory=list)
    
    def __str__(self) -> str:
        vars_str = ", ".join(self.variables.keys())
        return f"Scope({self.scope_type.value}, depth={self.depth}, vars=[{vars_str}])"
    
    def get_variable(self, name: str) -> Optional[VariableBinding]:
        """Get variable by name, searching up the scope chain"""
        if name in self.variables:
            return self.variables[name]
        
        if self.parent:
            return self.parent.get_variable(name)
        
        return None
    
    def declare(self, name: str, scope_type: ScopeType, 
                is_global: bool = False, is_nonlocal: bool = False,
                line_number: int = 0) -> VariableBinding:
        """Declare a variable in this scope"""
        binding = VariableBinding(
            name=name,
            scope_type=scope_type,
            scope_depth=self.depth,
            line_number=line_number,
            is_global=is_global,
            is_nonlocal=is_nonlocal,
            definition_line=line_number
        )
        
        self.variables[name] = binding
        return binding
    
    def assign(self, name: str, line_number: int) -> VariableBinding:
        """Assign to an existing variable, or declare if not yet declared"""
        binding = self.get_variable(name)
        if binding:
            binding.assignments.append(line_number)
            binding.is_local = (binding.scope_depth == self.depth)
            return binding
        return self.declare(name, self.scope_type, line_number=line_number)
    
    def reference(self, name: str, line_number: int) -> Optional[VariableBinding]:
        """Reference a variable"""
        binding = self.get_variable(name)
        if binding:
            binding.references.append(line_number)
            return binding
        return None
    
    def get_all_variables(self) -> Dict[str, VariableBinding]:
        """Get all variables in this scope and ancestors"""
        result = dict(self.variables)
        if self.parent:
            result.update(self.parent.get_all_variables())
        return result
    
    def get_free_variables(self) -> List[str]:
        """Get variables that are free (not bound in this scope)"""
        free = []
        for name, binding in self.variables.items():
            if not binding.is_local:
                free.append(name)
        return free


class ScopeResult(list):
    """Result of scope analysis behaving as a list of Scope objects and dict of metadata."""
    def __init__(self, scopes: List[Scope], metadata: Optional[Dict[str, Any]] = None):
        super().__init__(scopes)
        self._metadata: Dict[str, Any] = metadata or {}

    def __getitem__(self, item: Any) -> Any:
        if isinstance(item, str):
            return self._metadata.get(item)
        return super().__getitem__(item)

    def __contains__(self, item: Any) -> bool:
        if isinstance(item, str):
            return item in self._metadata
        return super().__contains__(item)

    def get(self, key: str, default: Any = None) -> Any:
        return self._metadata.get(key, default)

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata


class ScopeASTVisitor(ast.NodeVisitor):
    """AST visitor for identifying scopes and variable bindings."""

    def __init__(self, analyzer: 'ScopeAnalyzer'):
        self.analyzer = analyzer

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._handle_func(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._handle_func(node)

    def _handle_func(self, node: Any) -> None:
        lineno = getattr(node, 'lineno', 1)
        if self.analyzer._current_scope:
            binding = self.analyzer._current_scope.declare(
                node.name,
                self.analyzer._current_scope.scope_type,
                line_number=lineno
            )
            self.analyzer._all_bindings[node.name] = binding

        parent = self.analyzer._current_scope
        depth = (parent.depth + 1) if parent else 0
        func_scope = Scope(
            scope_type=ScopeType.FUNCTION,
            depth=depth,
            parent=parent,
            line_number=lineno
        )
        self.analyzer._scopes.append(func_scope)
        self.analyzer._current_scope = func_scope

        all_args = list(node.args.posonlyargs) + list(node.args.args) + list(node.args.kwonlyargs)
        for arg in all_args:
            b = func_scope.declare(arg.arg, ScopeType.FUNCTION, line_number=getattr(arg, 'lineno', lineno))
            self.analyzer._all_bindings[arg.arg] = b
        if node.args.vararg:
            b = func_scope.declare(node.args.vararg.arg, ScopeType.FUNCTION, line_number=getattr(node.args.vararg, 'lineno', lineno))
            self.analyzer._all_bindings[node.args.vararg.arg] = b
        if node.args.kwarg:
            b = func_scope.declare(node.args.kwarg.arg, ScopeType.FUNCTION, line_number=getattr(node.args.kwarg, 'lineno', lineno))
            self.analyzer._all_bindings[node.args.kwarg.arg] = b

        for stmt in node.body:
            self.visit(stmt)

        self.analyzer._current_scope = parent

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        lineno = getattr(node, 'lineno', 1)
        if self.analyzer._current_scope:
            b = self.analyzer._current_scope.declare(
                node.name,
                self.analyzer._current_scope.scope_type,
                line_number=lineno
            )
            self.analyzer._all_bindings[node.name] = b

        parent = self.analyzer._current_scope
        depth = (parent.depth + 1) if parent else 0
        class_scope = Scope(
            scope_type=ScopeType.CLASS,
            depth=depth,
            parent=parent,
            line_number=lineno
        )
        self.analyzer._scopes.append(class_scope)
        self.analyzer._current_scope = class_scope

        for stmt in node.body:
            self.visit(stmt)

        self.analyzer._current_scope = parent

    def visit_Lambda(self, node: ast.Lambda) -> None:
        lineno = getattr(node, 'lineno', 1)
        parent = self.analyzer._current_scope
        depth = (parent.depth + 1) if parent else 0
        lambda_scope = Scope(
            scope_type=ScopeType.LAMBDA,
            depth=depth,
            parent=parent,
            line_number=lineno
        )
        self.analyzer._scopes.append(lambda_scope)
        self.analyzer._current_scope = lambda_scope

        all_args = list(node.args.posonlyargs) + list(node.args.args) + list(node.args.kwonlyargs)
        for arg in all_args:
            b = lambda_scope.declare(arg.arg, ScopeType.LAMBDA, line_number=getattr(arg, 'lineno', lineno))
            self.analyzer._all_bindings[arg.arg] = b
        if node.args.vararg:
            b = lambda_scope.declare(node.args.vararg.arg, ScopeType.LAMBDA, line_number=getattr(node.args.vararg, 'lineno', lineno))
            self.analyzer._all_bindings[node.args.vararg.arg] = b
        if node.args.kwarg:
            b = lambda_scope.declare(node.args.kwarg.arg, ScopeType.LAMBDA, line_number=getattr(node.args.kwarg, 'lineno', lineno))
            self.analyzer._all_bindings[node.args.kwarg.arg] = b

        self.visit(node.body)
        self.analyzer._current_scope = parent

    def visit_ListComp(self, node: ast.ListComp) -> None:
        self._handle_comp(node)

    def visit_SetComp(self, node: ast.SetComp) -> None:
        self._handle_comp(node)

    def visit_DictComp(self, node: ast.DictComp) -> None:
        self._handle_comp(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        self._handle_comp(node)

    def _handle_comp(self, node: Any) -> None:
        lineno = getattr(node, 'lineno', 1)
        parent = self.analyzer._current_scope
        depth = (parent.depth + 1) if parent else 0
        comp_scope = Scope(
            scope_type=ScopeType.COMPREHENSION,
            depth=depth,
            parent=parent,
            line_number=lineno
        )
        self.analyzer._scopes.append(comp_scope)
        self.analyzer._current_scope = comp_scope

        for gen in node.generators:
            self.visit(gen)
        if hasattr(node, 'elt'):
            self.visit(node.elt)
        if hasattr(node, 'key'):
            self.visit(node.key)
        if hasattr(node, 'value'):
            self.visit(node.value)

        self.analyzer._current_scope = parent

    def visit_Global(self, node: ast.Global) -> None:
        lineno = getattr(node, 'lineno', 1)
        for name in node.names:
            self.analyzer._global_vars.add(name)
            if self.analyzer._current_scope:
                b = self.analyzer._current_scope.declare(
                    name, ScopeType.GLOBAL, is_global=True, line_number=lineno
                )
                self.analyzer._all_bindings[name] = b

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        lineno = getattr(node, 'lineno', 1)
        for name in node.names:
            if self.analyzer._current_scope:
                b = self.analyzer._current_scope.declare(
                    name, ScopeType.FUNCTION, is_nonlocal=True, line_number=lineno
                )
                self.analyzer._all_bindings[name] = b

    def _handle_target(self, target: Any, lineno: int) -> None:
        if isinstance(target, ast.Name):
            if self.analyzer._current_scope:
                binding = self.analyzer._current_scope.assign(target.id, lineno)
                self.analyzer._all_bindings[target.id] = binding
        elif isinstance(target, (ast.Tuple, ast.List)):
            for elt in target.elts:
                self._handle_target(elt, lineno)

    def visit_Assign(self, node: ast.Assign) -> None:
        lineno = getattr(node, 'lineno', 1)
        for target in node.targets:
            self._handle_target(target, lineno)
        self.visit(node.value)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        lineno = getattr(node, 'lineno', 1)
        self._handle_target(node.target, lineno)
        self.visit(node.value)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        lineno = getattr(node, 'lineno', 1)
        self._handle_target(node.target, lineno)
        if node.value:
            self.visit(node.value)

    def visit_For(self, node: ast.For) -> None:
        lineno = getattr(node, 'lineno', 1)
        self._handle_target(node.target, lineno)
        self.visit(node.iter)
        for stmt in node.body:
            self.visit(stmt)
        for stmt in node.orelse:
            self.visit(stmt)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        lineno = getattr(node, 'lineno', 1)
        self._handle_target(node.target, lineno)
        self.visit(node.iter)
        for stmt in node.body:
            self.visit(stmt)
        for stmt in node.orelse:
            self.visit(stmt)

    def visit_Name(self, node: ast.Name) -> None:
        lineno = getattr(node, 'lineno', 1)
        if isinstance(node.ctx, ast.Store):
            self._handle_target(node, lineno)
        elif isinstance(node.ctx, (ast.Load, ast.Del)):
            if self.analyzer._current_scope:
                b = self.analyzer._current_scope.reference(node.id, lineno)
                if b is not None:
                    self.analyzer._all_bindings[node.id] = b


class ScopeAnalyzer:
    """Analyzes Python code for scope information"""
    
    def __init__(self):
        self._scopes: List[Scope] = []
        self._current_scope: Optional[Scope] = None
        self._all_bindings: Dict[str, VariableBinding] = {}
        self._global_vars: Set[str] = set()
        self._logger = logging.getLogger(__name__)
    
    def analyze(self, code_or_ast: Any, filename: str = "<unknown>") -> ScopeResult:
        """
        Analyze code or AST for scope information
        
        Args:
            code_or_ast: Python source code string, ParseResult, or ast.AST
            filename: Source filename
            
        Returns:
            ScopeResult with scope analysis list and metadata dictionary access
        """
        try:
            self._scopes = []
            self._current_scope = None
            self._all_bindings = {}
            self._global_vars = set()
            
            # Create initial global scope
            global_scope = Scope(
                scope_type=ScopeType.GLOBAL,
                depth=0,
                line_number=1
            )
            self._scopes.append(global_scope)
            self._current_scope = global_scope
            
            # Obtain root AST node
            tree = None
            if isinstance(code_or_ast, str):
                tree = ast.parse(code_or_ast, filename=filename)
            elif hasattr(code_or_ast, "tree") and code_or_ast.tree is not None:
                tree = code_or_ast.tree
            elif isinstance(code_or_ast, ast.AST):
                tree = code_or_ast
            elif hasattr(code_or_ast, "nodes") and code_or_ast.nodes:
                tree = ast.Module(body=list(code_or_ast.nodes), type_ignores=[])
            else:
                try:
                    tree = ast.parse(str(code_or_ast))
                except Exception:
                    tree = ast.Module(body=[], type_ignores=[])
            
            # Traverse AST
            visitor = ScopeASTVisitor(self)
            if isinstance(tree, ast.Module):
                for stmt in tree.body:
                    visitor.visit(stmt)
            else:
                visitor.visit(tree)
            
            # Format results
            metadata = {
                "filename": filename,
                "total_scopes": len(self._scopes),
                "total_variables": len(self._all_bindings),
                "global_variables": list(self._global_vars),
                "scopes": self._scopes,
                "unbound_variables": [],
                "shadowed_variables": []
            }
            
            for name, binding in self._all_bindings.items():
                if not binding.references and not binding.assignments:
                    metadata["unbound_variables"].append(name)
            
            seen_depths: Dict[str, int] = {}
            for name, binding in self._all_bindings.items():
                if name in seen_depths:
                    if seen_depths[name] != binding.scope_depth:
                        metadata["shadowed_variables"].append(name)
                seen_depths[name] = binding.scope_depth
            
            self._logger.info(f"Analyzed {filename}: {len(self._scopes)} scopes, "
                              f"{len(self._all_bindings)} variables")
            
            return ScopeResult(self._scopes, metadata)
            
        except Exception as e:
            self._logger.error(f"Scope analysis error: {e}")
            raise
    
    def get_scope_chain(self) -> List[Scope]:
        """Get current scope chain"""
        return list(reversed(self._scopes))
    
    def get_all_bindings(self) -> Dict[str, VariableBinding]:
        """Get all variable bindings"""
        return self._all_bindings


# Singleton instance
_analyzer_instance: Optional[ScopeAnalyzer] = None


def get_analyzer() -> ScopeAnalyzer:
    """Get or create analyzer singleton"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = ScopeAnalyzer()
    return _analyzer_instance


if __name__ == "__main__":
    # Test scope analyzer
    code = """
x = 1
y = 2

def foo(a, b):
    global x
    nonlocal y
    c = a + b
    return c * 2

class Bar:
    def __init__(self):
        self.value = 10
    
    def method(self):
        for i in range(10):
            if i > 5:
                print(i)
    
    @staticmethod
    def static():
        return 42

result = [i * 2 for i in range(5)]
lambda_func = lambda x: x + 1
"""
    
    analyzer = ScopeAnalyzer()
    results = analyzer.analyze(code, "test.py")
    
    print(f"Total scopes: {results['total_scopes']}")
    print(f"Total variables: {results['total_variables']}")
    print(f"Global variables: {results['global_variables']}")
    print(f"Unbound variables: {results['unbound_variables']}")
    print(f"Shadowed variables: {results['shadowed_variables']}")
    
    for scope in results['scopes']:
        print(f"  Scope {scope['type']} (depth {scope['depth']}): {scope['variables']}")
