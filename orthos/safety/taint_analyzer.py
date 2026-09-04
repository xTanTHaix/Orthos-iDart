"""
Taint Analyzer for Orthos Safety System
Analyzes code for potential security vulnerabilities and taint patterns
"""

import logging
import ast
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class TaintSource:
    """Represents a source of tainted data"""
    node_type: str
    line_number: int
    column: int
    value: Optional[str] = None
    description: str = ""


@dataclass
class TaintSink:
    """Represents a sink that could be exploited"""
    node_type: str
    line_number: int
    column: int
    function_name: Optional[str] = None
    description: str = ""


@dataclass
class TaintFlow:
    """Represents a flow from source to sink"""
    source: TaintSource
    sink: TaintSink
    path: List[str] = field(default_factory=list)
    is_safe: bool = False


@dataclass
class TaintAnalysisResult:
    """Result of taint analysis"""
    sources: List[TaintSource] = field(default_factory=list)
    sinks: List[TaintSink] = field(default_factory=list)
    flows: List[TaintFlow] = field(default_factory=list)
    is_safe: bool = True
    issues: List[str] = field(default_factory=list)
    severity: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL

    def __iter__(self):
        """Allow unpacking as (is_tainted, sources) = result."""
        yield (len(self.sources) > 0 or not self.is_safe)
        yield self.sources

    def __getitem__(self, key: str) -> Any:
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default



class TaintAnalyzer:
    """
    Analyzes Python code for taint vulnerabilities.
    
    Detects:
    - Untrusted input sources (files, network, environment)
    - Dangerous sinks (eval, exec, shell commands)
    - Potential injection vulnerabilities
    - Improper input validation
    """
    
    # Known dangerous sinks
    DANGEROUS_SINKS = {
        'eval', 'exec', 'compile',
        'os.system', 'os.popen', 'os.spawn',
        'subprocess.call', 'subprocess.run', 'subprocess.Popen',
        'shell', 'input',
        'open', 'read', 'write',
        'urllib.request.urlopen', 'requests.get', 'requests.post',
        'httpx.get', 'httpx.post',
        'socket.send', 'socket.recv',
        'ast.literal_eval',
    }
    
    # Known safe sources (whitelist)
    SAFE_SOURCES = {
        'int', 'float', 'str', 'list', 'dict', 'set',
        'len', 'sum', 'min', 'max',
        'range', 'enumerate',
    }
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
    
    def analyze(self, code: str, filename: str = "<unknown>") -> TaintAnalysisResult:
        """
        Analyze code for taint vulnerabilities.
        
        Args:
            code: Python source code
            filename: Source filename
            
        Returns:
            TaintAnalysisResult with findings
        """
        try:
            logger.info(f"Analyzing {filename} for taint vulnerabilities")
            
            result = TaintAnalysisResult()
            
            # Parse code
            tree = ast.parse(code)
            
            # Find sources
            sources = self._find_sources(tree)
            result.sources = sources
            
            # Find sinks
            sinks = self._find_sinks(tree)
            result.sinks = sinks
            
            # Find flows
            flows = self._find_flows(tree, sources, sinks)
            result.flows = flows
            
            # Determine safety
            result.is_safe = len(flows) == 0
            result.severity = self._determine_severity(result)
            
            # Generate issues
            result.issues = self._generate_issues(result)
            
            logger.info(f"Taint analysis complete: {len(sources)} sources, "
                      f"{len(sinks)} sinks, {len(flows)} flows")
            
            return result
            
        except Exception as e:
            logger.error(f"Taint analysis error: {e}")
            return TaintAnalysisResult(
                is_safe=False,
                issues=[f"Analysis error: {str(e)}"]
            )
    
    def _find_sources(self, tree: ast.AST) -> List[TaintSource]:
        """Find potential taint sources in code."""
        sources = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ('open', 'read', 'write'):
                        sources.append(TaintSource(
                            node_type="FILE_OPERATION",
                            line_number=node.lineno,
                            column=node.col_offset,
                            description=f"File operation: {node.func.id}"
                        ))
                    elif node.func.id == 'input':
                        sources.append(TaintSource(
                            node_type="USER_INPUT",
                            line_number=node.lineno,
                            column=node.col_offset,
                            description="User input via input()"
                        ))
                
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr in ('urlopen', 'get', 'post'):
                        sources.append(TaintSource(
                            node_type="NETWORK_OPERATION",
                            line_number=node.lineno,
                            column=node.col_offset,
                            description=f"Network operation: {node.func.attr}"
                        ))
                    elif node.func.attr == 'getenv':
                        sources.append(TaintSource(
                            node_type="ENVIRONMENT_VARIABLE",
                            line_number=node.lineno,
                            column=node.col_offset,
                            description="Environment variable access"
                        ))
            elif isinstance(node, ast.FunctionDef):
                for arg in node.args.args:
                    arg_name = arg.arg.lower()
                    if 'input' in arg_name or 'user' in arg_name or 'taint' in arg_name:
                        sources.append(TaintSource(
                            node_type="USER_INPUT",
                            line_number=node.lineno,
                            column=node.col_offset,
                            description=f"Untrusted parameter: {arg.arg}"
                        ))
        
        return sources
    
    def _find_sinks(self, tree: ast.AST) -> List[TaintSink]:
        """Find potential taint sinks in code."""
        sinks = []
        
        for node in ast.walk(tree):
            # Direct dangerous function calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.DANGEROUS_SINKS:
                        sinks.append(TaintSink(
                            node_type="DANGEROUS_FUNCTION",
                            line_number=node.lineno,
                            column=node.col_offset,
                            function_name=node.func.id,
                            description=f"Dangerous function: {node.func.id}"
                        ))
                
                # Attribute access to dangerous methods
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr in ('system', 'popen', 'call', 'run', 'send'):
                        sinks.append(TaintSink(
                            node_type="DANGEROUS_METHOD",
                            line_number=node.lineno,
                            column=node.col_offset,
                            function_name=f"{node.func.value.id}.{node.func.attr}" if isinstance(node.func.value, ast.Name) else None,
                            description=f"Dangerous method: {node.func.attr}"
                        ))
            
            # ast module usage
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name):
                        if node.func.value.id == 'ast' and node.func.attr == 'literal_eval':
                            sinks.append(TaintSink(
                                node_type="AST_EVAL",
                                line_number=node.lineno,
                                column=node.col_offset,
                                function_name="ast.literal_eval",
                                description="AST literal evaluation"
                            ))
        
        return sinks
    
    def _find_flows(self, tree: ast.AST, 
                   sources: List[TaintSource],
                   sinks: List[TaintSink]) -> List[TaintFlow]:
        """Find flows from sources to sinks."""
        flows = []
        
        # Simplified flow analysis
        # In a real implementation, this would build a data flow graph
        for source in sources:
            for sink in sinks:
                # Check if sink is in same function as source
                source_func = self._get_function_from_node(tree, source.line_number)
                sink_func = self._get_function_from_node(tree, sink.line_number)
                
                if source_func and sink_func and source_func == sink_func:
                    flow = TaintFlow(
                        source=source,
                        sink=sink,
                        path=[f"{source_func}:{source.line_number} -> {sink_func}:{sink.line_number}"],
                        is_safe=False
                    )
                    flows.append(flow)
        
        return flows
    
    def _get_function_from_node(self, tree: ast.AST, line_number: int) -> Optional[str]:
        """Get function name from a line number."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.lineno <= line_number < node.end_lineno:
                    return node.name
        return None
    
    def _determine_severity(self, result: TaintAnalysisResult) -> str:
        """Determine overall severity."""
        if not result.is_safe:
            # Check for critical sinks
            critical_sinks = {'eval', 'exec', 'os.system', 'subprocess'}
            
            for sink in result.sinks:
                if sink.function_name in critical_sinks:
                    return "CRITICAL"
            
            # Check for high-risk patterns
            if any(source.node_type == "USER_INPUT" for source in result.sources):
                if any(sink.function_name in ('eval', 'exec') for sink in result.sinks):
                    return "HIGH"
            
            if len(result.flows) > 5:
                return "HIGH"
            
            return "MEDIUM"
        
        return "LOW"
    
    def _generate_issues(self, result: TaintAnalysisResult) -> List[str]:
        """Generate human-readable issues."""
        issues = []
        
        if not result.is_safe:
            for source in result.sources:
                issues.append(f"Potential source at line {source.line_number}: {source.description}")
            
            for sink in result.sinks:
                issues.append(f"Potential sink at line {sink.line_number}: {sink.description}")
            
            for flow in result.flows:
                issues.append(f"Flow detected: {flow.path}")
        
        return issues
    
    def is_safe(self, code: str) -> bool:
        """Quick check if code is safe."""
        result = self.analyze(code)
        return result.is_safe
    
    def get_summary(self, code: str) -> Dict[str, Any]:
        """Get summary of taint analysis."""
        result = self.analyze(code)
        
        return {
            'is_safe': result.is_safe,
            'severity': result.severity,
            'sources_count': len(result.sources),
            'sinks_count': len(result.sinks),
            'flows_count': len(result.flows),
            'issues': result.issues
        }


# Singleton instance
_analyzer_instance: Optional[TaintAnalyzer] = None


def get_taint_analyzer() -> TaintAnalyzer:
    """Get or create taint analyzer singleton."""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = TaintAnalyzer()
    return _analyzer_instance


if __name__ == "__main__":
    # Test taint analyzer
    analyzer = get_taint_analyzer()
    
    # Safe code
    safe_code = """
def safe_function(x):
    return x + 1

result = safe_function(5)
"""
    
    # Unsafe code
    unsafe_code = """
def unsafe_function(user_input):
    eval(user_input)
    os.system(user_input)
    
    with open(user_input) as f:
        content = f.read()
"""
    
    print("Safe code analysis:")
    print(analyzer.get_summary(safe_code))
    
    print("\nUnsafe code analysis:")
    print(analyzer.get_summary(unsafe_code))
