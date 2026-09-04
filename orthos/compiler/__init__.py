"""Orthos Compiler Package"""

from orthos.compiler.lexer import OrthosLexer
from orthos.compiler.parser import OrthosParser
from orthos.compiler.codegen import OrthosCodeGenerator
from orthos.compiler.packer import BytecodePacker, CompiledModule, Instruction, SpanDescriptor
from orthos.compiler.analysis.scope import ScopeAnalyzer, Scope, VariableBinding, ScopeType
from orthos.compiler.analysis.cfg import CFG, CFGBuilder, BasicBlock, NodeType
from orthos.compiler.analysis.complexity_gate import (
    ComplexityAnalyzer, ComplexityGate, ComplexityType, ComplexityResult, ComplexityViolation
)
from orthos.compiler.analysis.verification_cache import (
    VerificationCache, VerificationResult, VerificationStatus, VerificationKey,
    ScopeVerifier, ComplexityVerifier
)

__all__ = [
    # Core compiler
    'OrthosLexer', 'OrthosParser', 'OrthosCodeGenerator', 'BytecodePacker',
    'CompiledModule', 'Instruction', 'SpanDescriptor',
    
    # Analysis modules
    'ScopeAnalyzer', 'Scope', 'VariableBinding', 'ScopeType',
    'CFG', 'CFGBuilder', 'BasicBlock', 'NodeType',
    'ComplexityAnalyzer', 'ComplexityGate', 'ComplexityType',
    'ComplexityResult', 'ComplexityViolation',
    'VerificationCache', 'VerificationResult', 'VerificationStatus', 'VerificationKey',
    'ScopeVerifier', 'ComplexityVerifier'
]
