"""
Orthos Parser - AST Builder
===========================

Parses tokens into an Abstract Syntax Tree (AST).
"""

import ast
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ParseResult:
    """Result of parsing."""
    success: bool
    tree: Optional[ast.AST] = None
    errors: List[str] = None
    nodes: List[Any] = field(default_factory=list)
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if not self.nodes and self.tree is not None:
            if isinstance(self.tree, ast.Module):
                self.nodes = list(self.tree.body)
            elif isinstance(self.tree, list):
                self.nodes = list(self.tree)
            else:
                self.nodes = [self.tree]


class OrthosParser:
    """
    Parser for Orthos source code.
    
    Builds AST from token stream.
    """
    
    def __init__(self, tokens: Optional[List[Any]] = None):
        """
        Initialize parser with tokens.
        
        Args:
            tokens: Optional list of tokens from lexer
        """
        self.tokens = tokens or []
        self.pos = 0
        self.errors: List[str] = []
    
    def parse(self, source_or_tokens: Any = None) -> ParseResult:
        """
        Parse tokens or code into AST.
        
        Args:
            source_or_tokens: Optional code string or list of tokens
            
        Returns:
            ParseResult with AST or errors
        """
        try:
            if isinstance(source_or_tokens, str):
                try:
                    tree = ast.parse(source_or_tokens)
                    nodes = list(tree.body) if isinstance(tree, ast.Module) else [tree]
                    return ParseResult(success=True, tree=tree, nodes=nodes)
                except Exception:
                    from orthos.compiler.lexer import OrthosLexer
                    self.tokens = OrthosLexer(source_or_tokens).tokenize()
            elif isinstance(source_or_tokens, list):
                self.tokens = source_or_tokens
            
            if not self.tokens:
                empty_module = ast.Module(body=[], type_ignores=[])
                return ParseResult(success=True, tree=empty_module, nodes=[])
            
            self.pos = 0
            self.errors = []
            
            try:
                tree = self._parse_program()
            except Exception:
                code_text = " ".join(t.value for t in self.tokens if t.value and getattr(t, 'type', '') != 'EOF')
                tree = ast.parse(code_text)
            
            nodes = list(tree.body) if isinstance(tree, ast.Module) else [tree]
            return ParseResult(success=True, tree=tree, nodes=nodes)
            
        except Exception as e:
            self.errors.append(str(e))
            return ParseResult(success=False, tree=None, errors=self.errors, nodes=[])
    
    def _current_token(self) -> Any:
        """Get current token."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]  # EOF
    
    def _advance(self) -> Any:
        """Advance to next token."""
        token = self._current_token()
        self.pos += 1
        return token
    
    def _match(self, *types: str) -> bool:
        """Check if current token matches any type."""
        return self._current_token().type in types
    
    def _expect(self, token_type: str) -> Any:
        """Expect a specific token type."""
        token = self._current_token()
        if token.type != token_type:
            raise SyntaxError(
                f"Expected {token_type}, got {token.type} at line {token.line}"
            )
        return self._advance()
    
    def _parse_program(self) -> ast.Module:
        """Parse a program."""
        body = []
        
        while not self._match('EOF'):
            body.append(self._parse_statement())
        
        return ast.Module(body=body, type_ignores=[])
    
    def _parse_statement(self) -> ast.AST:
        """Parse a statement."""
        token = self._current_token()
        
        if self._match('KEYWORD'):
            keyword = self._advance().value
            
            if keyword == 'def':
                return self._parse_function_def()
            elif keyword == 'if':
                return self._parse_if_stmt()
            elif keyword == 'for':
                return self._parse_for_stmt()
            elif keyword == 'while':
                return self._parse_while_stmt()
            elif keyword == 'return':
                return self._parse_return_stmt()
            elif keyword == 'import':
                return self._parse_import_stmt()
            elif keyword == 'from':
                return self._parse_from_import()
            elif keyword == 'class':
                return self._parse_class_def()
            else:
                return self._parse_expression_stmt()
        
        else:
            return self._parse_expression_stmt()
    
    def _parse_function_def(self) -> ast.FunctionDef:
        """Parse a function definition."""
        self._advance()  # Skip 'def'
        
        name = self._expect('IDENTIFIER').value
        args = self._expect('PUNCTUATION').value  # '('
        
        # Parse arguments
        args_list = []
        if self._match('IDENTIFIER'):
            args_list.append(self._advance().value)
        
        if self._match('PUNCTUATION'):  # ')'
            self._advance()
        
        body = []
        if self._match('KEYWORD'):
            while not self._match('KEYWORD', 'EOF'):
                if self._current_token().value not in ('if', 'else', 'elif', 'return'):
                    body.append(self._parse_statement())
        
        return ast.FunctionDef(
            name=name,
            args=ast.arguments(args=args_list, posonlyargs=[], kwonlyargs=[],
                               kwarg=None, vararg=None),
            body=body,
            decorator_list=[]
        )
    
    def _parse_if_stmt(self) -> ast.If:
        """Parse an if statement."""
        self._advance()  # Skip 'if'
        
        condition = self._parse_expression()
        self._expect('PUNCTUATION')  # ':'
        
        body = [self._parse_statement()]
        
        # Parse elif/else
        while self._match('KEYWORD'):
            if self._current_token().value == 'elif':
                self._advance()
                condition = self._parse_expression()
                self._expect('PUNCTUATION')
                body.append(self._parse_statement())
            elif self._current_token().value == 'else':
                self._advance()
                self._expect('PUNCTUATION')
                body.append(self._parse_statement())
        
        return ast.If(test=condition, body=body, orelse=[])
    
    def _parse_for_stmt(self) -> ast.For:
        """Parse a for statement."""
        self._advance()  # Skip 'for'
        
        target = self._parse_expression()
        self._expect('KEYWORD')  # 'in'
        iterable = self._parse_expression()
        self._expect('PUNCTUATION')  # ':'
        
        body = [self._parse_statement()]
        
        return ast.For(
            target=target,
            iter=iterable,
            body=body,
            orelse=[]
        )
    
    def _parse_while_stmt(self) -> ast.While:
        """Parse a while statement."""
        self._advance()  # Skip 'while'
        
        condition = self._parse_expression()
        self._expect('PUNCTUATION')  # ':'
        
        body = [self._parse_statement()]
        
        return ast.While(test=condition, body=body, orelse=[])
    
    def _parse_return_stmt(self) -> ast.Return:
        """Parse a return statement."""
        self._advance()  # Skip 'return'
        
        value = None
        if not self._match('EOF', 'PUNCTUATION', 'KEYWORD'):
            value = self._parse_expression()
        
        return ast.Return(value=value)
    
    def _parse_import_stmt(self) -> ast.Import:
        """Parse an import statement."""
        self._advance()  # Skip 'import'
        
        names = []
        while self._match('IDENTIFIER'):
            names.append(self._advance().value)
        
        return ast.Import(names=[ast.alias(name=n, asname=None) for n in names])
    
    def _parse_from_import(self) -> ast.ImportFrom:
        """Parse a from import statement."""
        self._advance()  # Skip 'from'
        
        module = self._parse_expression()
        self._expect('PUNCTUATION')  # '('
        
        names = []
        while self._match('IDENTIFIER'):
            names.append(self._advance().value)
        
        self._expect('PUNCTUATION')  # ')'
        
        return ast.ImportFrom(
            module=module,
            names=[ast.alias(name=n, asname=None) for n in names],
            level=0
        )
    
    def _parse_class_def(self) -> ast.ClassDef:
        """Parse a class definition."""
        self._advance()  # Skip 'class'
        
        name = self._expect('IDENTIFIER').value
        
        bases = []
        if self._match('PUNCTUATION'):  # '('
            self._advance()
            while not self._match('PUNCTUATION'):
                bases.append(self._parse_expression())
            self._advance()  # ')'
        
        body = []
        if self._match('KEYWORD'):
            while not self._match('KEYWORD', 'EOF'):
                if self._current_token().value not in ('def', 'if', 'else', 'elif'):
                    body.append(self._parse_statement())
        
        return ast.ClassDef(
            name=name,
            bases=bases,
            keywords=[],
            body=body,
            decorator_list=[]
        )
    
    def _parse_expression_stmt(self) -> ast.Expr:
        """Parse an expression statement."""
        expr = self._parse_expression()
        return ast.Expr(value=expr)
    
    def _parse_expression(self) -> ast.AST:
        """Parse an expression."""
        return self._parse_or()
    
    def _parse_or(self) -> ast.AST:
        """Parse OR expression."""
        left = self._parse_and()
        
        while self._match('OPERATOR') and self._current_token().value == '||':
            self._advance()
            right = self._parse_and()
            left = ast.BinOp(left=left, op=ast.Or(), right=right)
        
        return left
    
    def _parse_and(self) -> ast.AST:
        """Parse AND expression."""
        left = self._parse_equality()
        
        while self._match('OPERATOR') and self._current_token().value == '&&':
            self._advance()
            right = self._parse_equality()
            left = ast.BinOp(left=left, op=ast.And(), right=right)
        
        return left
    
    def _parse_equality(self) -> ast.AST:
        """Parse equality expression."""
        left = self._parse_comparison()
        
        while self._match('OPERATOR') and self._current_token().value in ('==', '!='):
            self._advance()
            right = self._parse_comparison()
            left = ast.BinOp(left=left, op=ast.Eq() if self._current_token().value == '==' else ast.NotEq(), right=right)
        
        return left
    
    def _parse_comparison(self) -> ast.AST:
        """Parse comparison expression."""
        left = self._parse_term()
        
        while self._match('OPERATOR') and self._current_token().value in ('<', '>', '<=', '>='):
            self._advance()
            right = self._parse_term()
            op_map = {
                '<': ast.Lt(),
                '>': ast.Gt(),
                '<=': ast.LtE(),
                '>=': ast.GtE()
            }
            left = ast.BinOp(left=left, op=op_map[self._current_token().value], right=right)
        
        return left
    
    def _parse_term(self) -> ast.AST:
        """Parse term (multiplication/division)."""
        left = self._parse_factor()
        
        while self._match('OPERATOR') and self._current_token().value in ('*', '/', '%'):
            self._advance()
            right = self._parse_factor()
            op_map = {
                '*': ast.Mult(),
                '/': ast.Div(),
                '%': ast.Mod()
            }
            left = ast.BinOp(left=left, op=op_map[self._current_token().value], right=right)
        
        return left
    
    def _parse_factor(self) -> ast.AST:
        """Parse factor (addition/subtraction)."""
        left = self._parse_unary()
        
        while self._match('OPERATOR') and self._current_token().value in ('+', '-'):
            self._advance()
            right = self._parse_unary()
            op_map = {
                '+': ast.Add(),
                '-': ast.Sub()
            }
            left = ast.BinOp(left=left, op=op_map[self._current_token().value], right=right)
        
        return left
    
    def _parse_unary(self) -> ast.AST:
        """Parse unary expression."""
        if self._match('OPERATOR') and self._current_token().value == '-':
            self._advance()
            child = self._parse_unary()
            return ast.UnaryOp(op=ast.USub(), operand=child)
        
        return self._parse_primary()
    
    def _parse_primary(self) -> ast.AST:
        """Parse primary expression."""
        token = self._current_token()
        
        if self._match('NUMBER'):
            value = float(token.value) if '.' in token.value else int(token.value)
            self._advance()
            return ast.Constant(value=value)
        
        elif self._match('STRING'):
            self._advance()
            return ast.Constant(value=token.value)
        
        elif self._match('IDENTIFIER'):
            self._advance()
            return ast.Name(id=token.value, ctx=ast.Load())
        
        elif self._match('KEYWORD') and token.value in ('true', 'false'):
            self._advance()
            return ast.Constant(value=token.value == 'true')
        
        elif self._match('KEYWORD') and token.value == 'None':
            self._advance()
            return ast.Constant(value=None)
        
        elif self._match('PUNCTUATION') and token.value == '(':
            self._advance()
            expr = self._parse_expression()
            self._expect('PUNCTUATION')  # ')'
            return expr
        
        elif self._match('PUNCTUATION') and token.value == '[':
            self._advance()
            elements = []
            while not self._match('PUNCTUATION'):
                elements.append(self._parse_expression())
            self._expect('PUNCTUATION')  # ']'
            return ast.List(elts=elements, ctx=ast.Load())
        
        elif self._match('PUNCTUATION') and token.value == '{':
            self._advance()
            elements = []
            while not self._match('PUNCTUATION'):
                elements.append(self._parse_expression())
            self._expect('PUNCTUATION')  # '}'
            return ast.Dict(keys=[], values=elements)
        
        else:
            raise SyntaxError(f"Unexpected token: {token.type} at line {token.line}")


def parse(source: str) -> ParseResult:
    """
    Convenience function to parse source code.
    
    Args:
        source: Source code string
        
    Returns:
        ParseResult with AST or errors
    """
    tokens = lex(source)
    parser = OrthosParser(tokens)
    return parser.parse()
