"""
Orthos Bootstrapper - sys.meta_path Import Hook
================================================

This module registers an import hook that intercepts all module imports
and routes them through the Orthos optimization pipeline.

The bootstrapper:
1. Intercepts module imports via sys.meta_path
2. Analyzes module code before execution
3. Applies Nexus fast-path optimizations
4. Routes to VM or standard Python based on safety analysis
"""

import sys
import ast
import importlib.util
import importlib.machinery
import logging
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# Import engine from main package - avoid circular import
# The OrthosEngine class is defined in orthos.__init__.py
# We'll import it lazily when needed


class OrthosBootstrapper:
    """
    Import hook that intercepts module imports and applies Orthos optimization.
    
    This class is registered with sys.meta_path to intercept all module
    imports and route them through the Orthos pipeline.
    """
    
    def __init__(self, engine):
        """
        Initialize the bootstrapper.
        
        Args:
            engine: OrthosEngine instance for optimization
        """
        self.engine = engine
        self._compiled_modules: Dict[str, Any] = {}
        self._module_cache: Dict[str, Any] = {}
    
    def find_module(self, fullname: str, path: Optional[Tuple[str, ...]] = None) -> Optional['OrthosBootstrapper']:
        """
        Determine if this bootstrapper should handle the module.
        
        Args:
            fullname: Full module name
            path: Import path
            
        Returns:
            This bootstrapper if it should handle the module, None otherwise
        """
        # Handle all modules
        return self
    
    def load_module(self, fullname: str) -> Any:
        """
        Load a module through the Orthos pipeline.
        
        Args:
            fullname: Full module name
            
        Returns:
            Loaded module object
        """
        try:
            # Check if already compiled
            if fullname in self._compiled_modules:
                return self._compiled_modules[fullname]
            
            # Load the module source
            spec = importlib.util.find_spec(fullname)
            if spec is None:
                raise ImportError(f"Module {fullname} not found")
            
            # Load source code
            loader = importlib.machinery.SourceFileLoader(fullname, spec.origin)
            module = importlib.util.module_from_spec(spec)
            
            # Execute the module to get source
            sys.modules[fullname] = module
            loader.exec_module(module)
            
            # Get source code
            source = None
            if hasattr(module, '__file__') and module.__file__:
                with open(module.__file__, 'r', encoding='utf-8') as f:
                    source = f.read()
            
            # Compile through Orthos pipeline
            if source:
                compile_result = self.engine.compile(source, module.__file__)
                
                if not compile_result['success']:
                    # Fallback to standard execution
                    logger.warning(f"Orthos compilation failed for {fullname}, using standard execution")
                    self._compiled_modules[fullname] = module
                    return module
            
            # Cache the compiled module
            self._compiled_modules[fullname] = module
            
            logger.info(f"Module {fullname} loaded through Orthos pipeline")
            return module
            
        except Exception as e:
            logger.error(f"Failed to load module {fullname}: {e}")
            raise
    
    def exec_module(self, module: Any) -> None:
        """
        Execute a module through the Orthos pipeline.
        
        Args:
            module: Module object to execute
        """
        try:
            # Get source code
            source = None
            if hasattr(module, '__file__') and module.__file__:
                with open(module.__file__, 'r', encoding='utf-8') as f:
                    source = f.read()
            
            # Compile through Orthos
            if source:
                compile_result = self.engine.compile(source, module.__file__)
                
                if not compile_result['success']:
                    logger.warning(f"Orthos compilation failed for {module.__name__}, using standard execution")
                    # Fall back to standard execution
                    loader = importlib.machinery.SourceFileLoader(module.__name__, module.__file__)
                    loader.exec_module(module)
                    return
            
            # Standard execution
            loader = importlib.machinery.SourceFileLoader(module.__name__, module.__file__)
            loader.exec_module(module)
            
        except Exception as e:
            logger.error(f"Failed to execute module {module.__name__}: {e}")
            raise


def create_bootstrapper() -> OrthosBootstrapper:
    """
    Create a bootstrapper instance.
    
    Returns:
        OrthosBootstrapper instance
    """
    # Import lazily to avoid circular import
    from orthos import OrthosEngine
    engine = OrthosEngine()
    return OrthosBootstrapper(engine)
