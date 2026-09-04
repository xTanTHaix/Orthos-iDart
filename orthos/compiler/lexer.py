"""
Orthos Lexer - Custom .orth Language Lexer
==========================================

Tokenizes source code into lexical tokens for parsing.
"""

import re
import logging
from typing import List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TokenType(str, Enum):
    """Token type enumeration for Orthos lexer tokens."""
    EOF = "EOF"
    NUMBER = "NUMBER"
    STRING = "STRING"
    IDENTIFIER = "IDENTIFIER"
    KEYWORD = "KEYWORD"
    OPERATOR = "OPERATOR"
    PUNCTUATION = "PUNCTUATION"
    COMMENT = "COMMENT"
    NEWLINE = "NEWLINE"
    INDENT = "INDENT"
    DEDENT = "DEDENT"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, TokenType):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)


@dataclass
class Token:
    """Lexical token."""
    type: Any
    value: str
    line: int
    column: int


class OrthosLexer:
    """
    Lexer for Orthos source code.
    
    Tokenizes .orth files into tokens for the parser.
    """
    
    # Token types
    TOKEN_EOF = TokenType.EOF
    TOKEN_NUMBER = TokenType.NUMBER
    TOKEN_STRING = TokenType.STRING
    TOKEN_IDENTIFIER = TokenType.IDENTIFIER
    TOKEN_KEYWORD = TokenType.KEYWORD
    TOKEN_OPERATOR = TokenType.OPERATOR
    TOKEN_PUNCTUATION = TokenType.PUNCTUATION
    TOKEN_COMMENT = TokenType.COMMENT
    
    # Keywords
    KEYWORDS = {
        'import', 'from', 'def', 'class', 'if', 'else', 'elif',
        'for', 'while', 'return', 'true', 'false', 'None',
        'let', 'var', 'const', 'match', 'case', 'when'
    }
    
    # Operators
    OPERATORS = {
        '+', '-', '*', '/', '%', '**', '=', '==', '!=', '<', '>',
        '<=', '>=', '&&', '||', '!', '&', '|', '^', '~', '<<', '>>'
    }
    
    def __init__(self, source: Optional[str] = None):
        """
        Initialize lexer with source code.
        
        Args:
            source: Source code to tokenize
        """
        self.source = source or ""
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
    
    def tokenize(self, source: Optional[str] = None) -> List[Token]:
        """
        Tokenize the source code.
        
        Returns:
            List of tokens
        """
        if source is not None:
            self.source = source
        
        self.tokens = []
        self.pos = 0
        self.line = 1
        self.column = 1
        
        if not self.source or not self.source.strip():
            return []
        
        while self.pos < len(self.source):
            self._skip_whitespace()
            
            if self.pos >= len(self.source):
                break
            
            char = self.source[self.pos]
            
            # Comment
            if char == '#':
                self._read_comment()
            
            # Number
            elif char.isdigit() or (char == '.' and self.pos + 1 < len(self.source) and self.source[self.pos + 1].isdigit()):
                self._read_number()
            
            # String
            elif char in ('"', "'"):
                self._read_string()
            
            # Identifier or keyword
            elif char.isalpha() or char == '_':
                self._read_identifier()
            
            # Operator
            elif char in self.OPERATORS:
                self._read_operator()
            
            # Punctuation
            elif char in '()[]{}.;:,':
                self._read_punctuation()
            
            # Unknown character
            else:
                self._read_unknown()
        
        self.tokens.append(Token(self.TOKEN_EOF, '', self.line, self.column))
        return self.tokens
    
    def _skip_whitespace(self) -> None:
        """Skip whitespace characters."""
        while self.pos < len(self.source) and self.source[self.pos] in ' \t\n\r':
            if self.source[self.pos] == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            self.pos += 1
    
    def _read_comment(self) -> None:
        """Read a comment line."""
        start = self.pos
        while self.pos < len(self.source) and self.source[self.pos] not in '\n\r':
            self.pos += 1
        comment_val = self.source[start:self.pos]
        self.tokens.append(Token(self.TOKEN_COMMENT, comment_val, self.line, self.column))
    
    def _read_number(self) -> None:
        """Read a number token."""
        start = self.pos
        has_dot = False
        
        while self.pos < len(self.source):
            char = self.source[self.pos]
            if char.isdigit():
                self.pos += 1
            elif char == '.' and not has_dot:
                has_dot = True
                self.pos += 1
            else:
                break
        
        value = self.source[start:self.pos]
        self.tokens.append(Token(self.TOKEN_NUMBER, value, self.line, self.column))
    
    def _read_string(self) -> None:
        """Read a string token."""
        quote = self.source[self.pos]
        self.pos += 1
        
        start = self.pos
        while self.pos < len(self.source):
            if self.source[self.pos] == '\\' and self.pos + 1 < len(self.source):
                self.pos += 2  # Skip escape sequence
            elif self.source[self.pos] == quote:
                break
            else:
                self.pos += 1
        
        value = self.source[start:self.pos]
        if self.pos < len(self.source) and self.source[self.pos] == quote:
            self.pos += 1
        self.tokens.append(Token(self.TOKEN_STRING, value, self.line, self.column))
    
    def _read_identifier(self) -> None:
        """Read an identifier or keyword token."""
        start = self.pos
        
        while self.pos < len(self.source):
            char = self.source[self.pos]
            if char.isalnum() or char == '_':
                self.pos += 1
            else:
                break
        
        value = self.source[start:self.pos]
        
        # Check if keyword
        if value in self.KEYWORDS:
            token_type = self.TOKEN_KEYWORD
        else:
            token_type = self.TOKEN_IDENTIFIER
        
        self.tokens.append(Token(token_type, value, self.line, self.column))
    
    def _read_operator(self) -> None:
        """Read an operator token."""
        start = self.pos
        
        # Multi-character operators
        if self.pos + 1 < len(self.source):
            two_char = self.source[self.pos:self.pos + 2]
            if two_char in self.OPERATORS:
                self.pos += 2
                value = two_char
            else:
                value = self.source[self.pos]
                self.pos += 1
        else:
            value = self.source[self.pos]
            self.pos += 1
        
        self.tokens.append(Token(self.TOKEN_OPERATOR, value, self.line, self.column))
    
    def _read_punctuation(self) -> None:
        """Read a punctuation token."""
        char = self.source[self.pos]
        self.pos += 1
        self.tokens.append(Token(self.TOKEN_PUNCTUATION, char, self.line, self.column))
    
    def _read_unknown(self) -> None:
        """Read an unknown character."""
        self.pos += 1
        logger.warning(f"Unknown character: {self.source[self.pos - 1]}")


def lex(source: str) -> List[Token]:
    """
    Convenience function to tokenize source code.
    
    Args:
        source: Source code string
        
    Returns:
        List of tokens
    """
    lexer = OrthosLexer(source)
    return lexer.tokenize()
