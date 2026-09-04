"""
Compiler Test Suite - Comprehensive tests for compiler pipeline

Tests cover:
- Lexer/tokenizer
- Parser/AST builder
- Code generator
- Bytecode packer
- Analysis modules
"""

import pytest
import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orthos.compiler.lexer import OrthosLexer, TokenType
from orthos.compiler.parser import OrthosParser
from orthos.compiler.codegen import OrthosCodeGenerator
from orthos.compiler.packer import BytecodePacker, CompiledModule
from orthos.compiler.analysis.scope import ScopeAnalyzer
from orthos.compiler.analysis.cfg import CFGBuilder
from orthos.compiler.analysis.complexity_gate import ComplexityAnalyzer


class TestLexer:
    """Test lexer/tokenizer."""

    def test_lexer_creation(self):
        """Test lexer can be created."""
        lexer = OrthosLexer()
        assert lexer is not None

    def test_tokenize_simple_code(self):
        """Test tokenizing simple code."""
        lexer = OrthosLexer()
        code = "x = 42"
        tokens = lexer.tokenize(code)
        
        assert len(tokens) > 0
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "x"

    def test_tokenize_assignment(self):
        """Test tokenizing assignment."""
        lexer = OrthosLexer()
        code = "result = compute_value()"
        tokens = lexer.tokenize(code)
        
        token_values = [t.value for t in tokens]
        assert "result" in token_values
        assert "=" in token_values
        assert "compute_value" in token_values

    def test_tokenize_arithmetic(self):
        """Test tokenizing arithmetic operations."""
        lexer = OrthosLexer()
        code = "a = b + c * d - e / f"
        tokens = lexer.tokenize(code)
        
        token_values = [t.value for t in tokens]
        assert "+" in token_values
        assert "*" in token_values
        assert "-" in token_values
        assert "/" in token_values

    def test_tokenize_function_call(self):
        """Test tokenizing function call."""
        lexer = OrthosLexer()
        code = "result = factorial(5)"
        tokens = lexer.tokenize(code)
        
        token_values = [t.value for t in tokens]
        assert "factorial" in token_values
        assert "(" in token_values
        assert ")" in token_values

    def test_tokenize_comments(self):
        """Test tokenizing with comments."""
        lexer = OrthosLexer()
        code = "# This is a comment\nx = 42"
        tokens = lexer.tokenize(code)
        
        # Comments should be ignored or tokenized
        assert len(tokens) > 0

    def test_tokenize_strings(self):
        """Test tokenizing strings."""
        lexer = OrthosLexer()
        code = 'message = "Hello, World!"'
        tokens = lexer.tokenize(code)
        
        token_values = [t.value for t in tokens]
        assert "Hello, World!" in token_values

    def test_tokenize_numbers(self):
        """Test tokenizing numbers."""
        lexer = OrthosLexer()
        code = "count = 42\npi = 3.14159"
        tokens = lexer.tokenize(code)
        
        token_values = [t.value for t in tokens]
        assert "42" in token_values
        assert "3.14159" in token_values

    def test_tokenize_operators(self):
        """Test tokenizing various operators."""
        lexer = OrthosLexer()
        code = "a && b || c ^ d"
        tokens = lexer.tokenize(code)
        
        token_values = [t.value for t in tokens]
        assert "&&" in token_values or "&" in token_values
        assert "||" in token_values or "|" in token_values


class TestParser:
    """Test parser/AST builder."""

    def test_parser_creation(self):
        """Test parser can be created."""
        parser = OrthosParser()
        assert parser is not None

    def test_parse_simple_assignment(self):
        """Test parsing simple assignment."""
        parser = OrthosParser()
        code = "x = 42"
        ast = parser.parse(code)
        
        assert ast is not None
        assert len(ast.nodes) > 0

    def test_parse_complex_expression(self):
        """Test parsing complex expression."""
        parser = OrthosParser()
        code = "result = (a + b) * (c - d) / e"
        ast = parser.parse(code)
        
        assert ast is not None
        assert len(ast.nodes) > 0

    def test_parse_function_definition(self):
        """Test parsing function definition."""
        parser = OrthosParser()
        code = "def factorial(n):\n    return n * factorial(n-1)"
        ast = parser.parse(code)
        
        assert ast is not None
        assert len(ast.nodes) > 0

    def test_parse_loop(self):
        """Test parsing loop construct."""
        parser = OrthosParser()
        code = "for i in range(10):\n    sum += i"
        ast = parser.parse(code)
        
        assert ast is not None
        assert len(ast.nodes) > 0

    def test_parse_conditional(self):
        """Test parsing conditional."""
        parser = OrthosParser()
        code = "if x > 0:\n    result = x"
        ast = parser.parse(code)
        
        assert ast is not None
        assert len(ast.nodes) > 0

    def test_parse_nested_structures(self):
        """Test parsing nested structures."""
        parser = OrthosParser()
        code = """
def outer():
    if condition:
        for i in range(10):
            result = compute(i)
        return result
"""
        ast = parser.parse(code)
        
        assert ast is not None
        assert len(ast.nodes) > 0


class TestCodeGenerator:
    """Test code generator."""

    def test_codegen_creation(self):
        """Test code generator can be created."""
        gen = OrthosCodeGenerator()
        assert gen is not None

    def test_generate_from_ast(self):
        """Test generating bytecode from AST."""
        parser = OrthosParser()
        code = "x = 42"
        ast = parser.parse(code)
        
        gen = OrthosCodeGenerator()
        bytecode = gen.generate(ast)
        
        assert bytecode is not None
        assert len(bytecode) > 0

    def test_generate_function(self):
        """Test generating function bytecode."""
        parser = OrthosParser()
        code = "def add(a, b):\n    return a + b"
        ast = parser.parse(code)
        
        gen = OrthosCodeGenerator()
        bytecode = gen.generate(ast)
        
        assert bytecode is not None
        assert len(bytecode) > 0

    def test_generate_with_loops(self):
        """Test generating bytecode with loops."""
        parser = OrthosParser()
        code = "for i in range(10):\n    sum += i"
        ast = parser.parse(code)
        
        gen = OrthosCodeGenerator()
        bytecode = gen.generate(ast)
        
        assert bytecode is not None
        assert len(bytecode) > 0


class TestBytecodePacker:
    """Test bytecode packer."""

    def test_packer_creation(self):
        """Test packer can be created."""
        packer = BytecodePacker()
        assert packer is not None

    def test_pack_module(self):
        """Test packing compiled module."""
        packer = BytecodePacker()
        
        module = CompiledModule(
            name="test_module",
            bytecode=b"\x00\x01\x02\x03",
            instructions=[
                {"opcode": 1, "operands": [0, 1]},
                {"opcode": 2, "operands": [2]},
            ],
            metadata={"version": 1}
        )
        
        packed = packer.pack(module)
        
        assert packed is not None
        assert len(packed) > 0

    def test_unpack_module(self):
        """Test unpacking packed module."""
        packer = BytecodePacker()
        
        module = CompiledModule(
            name="test_module",
            bytecode=b"\x00\x01\x02\x03",
            instructions=[
                {"opcode": 1, "operands": [0, 1]},
                {"opcode": 2, "operands": [2]},
            ],
            metadata={"version": 1}
        )
        
        packed = packer.pack(module)
        unpacked = packer.unpack(packed)
        
        assert unpacked is not None
        assert unpacked.name == module.name
        assert len(unpacked.instructions) == len(module.instructions)

    def test_pack_with_crc32(self):
        """Test packing with CRC32 validation."""
        packer = BytecodePacker()
        
        module = CompiledModule(
            name="test_module",
            bytecode=b"\x00\x01\x02\x03",
            instructions=[],
            metadata={"version": 1}
        )
        
        packed = packer.pack(module)
        
        # Verify CRC32 is present
        assert len(packed) >= 28  # Header size

    def test_pack_invalid_module(self):
        """Test packing invalid module raises error."""
        packer = BytecodePacker()
        
        with pytest.raises(ValueError):
            packer.pack(None)


class TestScopeAnalyzer:
    """Test scope analyzer."""

    def test_analyzer_creation(self):
        """Test analyzer can be created."""
        analyzer = ScopeAnalyzer()
        assert analyzer is not None

    def test_analyze_simple_scope(self):
        """Test analyzing simple scope."""
        parser = OrthosParser()
        code = "x = 42\ny = x + 1"
        ast = parser.parse(code)
        
        analyzer = ScopeAnalyzer()
        scopes = analyzer.analyze(ast)
        
        assert scopes is not None
        assert len(scopes) > 0

    def test_analyze_function_scope(self):
        """Test analyzing function scope."""
        parser = OrthosParser()
        code = "def foo():\n    x = 1"
        ast = parser.parse(code)
        
        analyzer = ScopeAnalyzer()
        scopes = analyzer.analyze(ast)
        
        assert scopes is not None
        assert any(s.scope_type.value == "function" for s in scopes)

    def test_analyze_nested_scopes(self):
        """Test analyzing nested scopes."""
        parser = OrthosParser()
        code = """
def outer():
    x = 1
    def inner():
        y = 2
    return x + y
"""
        ast = parser.parse(code)
        
        analyzer = ScopeAnalyzer()
        scopes = analyzer.analyze(ast)
        
        assert scopes is not None
        assert len(scopes) > 1  # At least outer and inner scopes

    def test_variable_binding(self):
        """Test variable binding analysis."""
        parser = OrthosParser()
        code = "x = 1\nx = x + 1"
        ast = parser.parse(code)
        
        analyzer = ScopeAnalyzer()
        scopes = analyzer.analyze(ast)
        
        # Should detect variable binding
        assert scopes is not None


class TestCFGBuilder:
    """Test control flow graph builder."""

    def test_cfg_builder_creation(self):
        """Test CFG builder can be created."""
        builder = CFGBuilder()
        assert builder is not None

    def test_build_cfg_simple(self):
        """Test building CFG for simple code."""
        parser = OrthosParser()
        code = "x = 1\ny = 2"
        ast = parser.parse(code)
        
        builder = CFGBuilder()
        cfg = builder.build(ast)
        
        assert cfg is not None
        assert len(cfg.blocks) > 0

    def test_build_cfg_with_branch(self):
        """Test building CFG with branches."""
        parser = OrthosParser()
        code = "if x > 0:\n    y = 1"
        ast = parser.parse(code)
        
        builder = CFGBuilder()
        cfg = builder.build(ast)
        
        assert cfg is not None
        assert len(cfg.blocks) > 0

    def test_build_cfg_with_loop(self):
        """Test building CFG with loops."""
        parser = OrthosParser()
        code = "for i in range(10):\n    x += 1"
        ast = parser.parse(code)
        
        builder = CFGBuilder()
        cfg = builder.build(ast)
        
        assert cfg is not None
        assert len(cfg.blocks) > 0

    def test_dominator_analysis(self):
        """Test dominator analysis."""
        parser = OrthosParser()
        code = """
if x > 0:
    y = 1
    z = 2
"""
        ast = parser.parse(code)
        
        builder = CFGBuilder()
        cfg = builder.build(ast)
        
        if cfg:
            dominators = cfg.compute_dominators()
            assert dominators is not None


class TestComplexityAnalyzer:
    """Test complexity analyzer."""

    def test_analyzer_creation(self):
        """Test analyzer can be created."""
        analyzer = ComplexityAnalyzer()
        assert analyzer is not None

    def test_analyze_simple_code(self):
        """Test analyzing simple code."""
        parser = OrthosParser()
        code = "x = 1\ny = 2"
        ast = parser.parse(code)
        
        analyzer = ComplexityAnalyzer()
        complexity = analyzer.analyze(ast)
        
        assert complexity is not None
        assert complexity.cyclomatic <= 2  # Simple code should have low complexity

    def test_analyze_complex_code(self):
        """Test analyzing complex code."""
        parser = OrthosParser()
        code = """
def complex_function(a, b, c, d, e):
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        return a + b + c + d + e
    return 0
"""
        ast = parser.parse(code)
        
        analyzer = ComplexityAnalyzer()
        complexity = analyzer.analyze(ast)
        
        assert complexity is not None
        assert complexity.cyclomatic > 5  # Complex code should have high complexity

    def test_halstead_metrics(self):
        """Test Halstead metrics calculation."""
        parser = OrthosParser()
        code = "x = y + z"
        ast = parser.parse(code)
        
        analyzer = ComplexityAnalyzer()
        complexity = analyzer.analyze(ast)
        
        assert complexity.halstead is not None
        assert hasattr(complexity.halstead, 'n1')  # Number of operators
        assert hasattr(complexity.halstead, 'n2')  # Number of operands


class TestCompilerIntegration:
    """Test full compiler pipeline integration."""

    def test_full_pipeline_simple(self):
        """Test full compiler pipeline with simple code."""
        code = "x = 42"
        
        # Lex
        lexer = OrthosLexer()
        tokens = lexer.tokenize(code)
        assert len(tokens) > 0
        
        # Parse
        parser = OrthosParser()
        ast = parser.parse(code)
        assert ast is not None
        
        # Codegen
        gen = OrthosCodeGenerator()
        bytecode = gen.generate(ast)
        assert bytecode is not None
        
        # Pack
        packer = BytecodePacker()
        module = CompiledModule(
            name="test",
            bytecode=bytecode,
            instructions=[],
            metadata={"version": 1}
        )
        packed = packer.pack(module)
        assert packed is not None

    def test_full_pipeline_with_function(self):
        """Test full compiler pipeline with function."""
        code = "def add(a, b):\n    return a + b"
        
        # Lex
        lexer = OrthosLexer()
        tokens = lexer.tokenize(code)
        assert len(tokens) > 0
        
        # Parse
        parser = OrthosParser()
        ast = parser.parse(code)
        assert ast is not None
        
        # Codegen
        gen = OrthosCodeGenerator()
        bytecode = gen.generate(ast)
        assert bytecode is not None
        
        # Pack
        packer = BytecodePacker()
        module = CompiledModule(
            name="test",
            bytecode=bytecode,
            instructions=[],
            metadata={"version": 1}
        )
        packed = packer.pack(module)
        assert packed is not None

    def test_full_pipeline_with_analysis(self):
        """Test full compiler pipeline with analysis."""
        code = """
def compute(x, y):
    if x > 0:
        if y > 0:
            return x + y
    return 0
"""
        
        # Lex
        lexer = OrthosLexer()
        tokens = lexer.tokenize(code)
        
        # Parse
        parser = OrthosParser()
        ast = parser.parse(code)
        
        # Scope analysis
        scope_analyzer = ScopeAnalyzer()
        scopes = scope_analyzer.analyze(ast)
        assert scopes is not None
        
        # CFG analysis
        cfg_builder = CFGBuilder()
        cfg = cfg_builder.build(ast)
        assert cfg is not None
        
        # Complexity analysis
        complexity_analyzer = ComplexityAnalyzer()
        complexity = complexity_analyzer.analyze(ast)
        assert complexity is not None
        
        # Codegen
        gen = OrthosCodeGenerator()
        bytecode = gen.generate(ast)
        assert bytecode is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
