"""
Orthos Code Generator - Bytecode Emitter
========================================

Generates bytecode from AST for VM execution.
"""

import ast
import struct
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from orthos.vm.core import Instruction

logger = logging.getLogger(__name__)


@dataclass
class BytecodeInstruction:
    """Single bytecode instruction."""
    opcode: int
    operand: int = 0
    operand2: int = 0


class Bytecode(bytes):
    """Bytecode representation that behaves as bytes and iterates Instructions."""
    def __new__(cls, data: bytes, instructions: Optional[List[Any]] = None):
        obj = super().__new__(cls, data)
        obj.instructions = list(instructions or [])
        return obj

    def __iter__(self):
        return iter(self.instructions)


class OrthosCodeGenerator:
    """
    Code generator that emits bytecode from AST.
    
    Generates optimized bytecode for the Orthos VM.
    """
    
    # Opcodes
    OP_HALT = 0x00
    OP_MOV = 0x01
    OP_LOAD_CONST = 0x02
    OP_FAUL_EVAL = 0x10
    OP_MAT_EXP = 0x11
    OP_DIOPH_FLAT = 0x12
    OP_VEC_ADD = 0x15
    OP_VEC_MUL = 0x16
    OP_DEMAND_PULL = 0x20
    OP_SCOPE_FUSE = 0x21
    OP_SPAN_MAKE = 0x40
    OP_SPAN_MATERIALIZE = 0x41
    OP_BOUND_CHECK = 0x42
    OP_JMP = 0x30
    OP_JMP_IF_ZERO = 0x31
    
    def __init__(self):
        """Initialize the code generator."""
        self.instructions: List[BytecodeInstruction] = []
        self.vm_instructions: List[Instruction] = []
        self.constants: List[Any] = []
        self.label_counter: int = 0
    
    def generate(self, ast_tree: Any) -> Bytecode:
        """
        Generate bytecode from AST.
        
        Args:
            ast_tree: AST to compile
            
        Returns:
            Bytecode bytes
        """
        try:
            if hasattr(ast_tree, 'tree') and ast_tree.tree is not None:
                ast_tree = ast_tree.tree

            self.instructions = []
            self.vm_instructions = []
            self.constants = []
            self.label_counter = 0

            # Generate bytecode
            self._generate_from_ast(ast_tree)

            # Ensure there is at least a HALT instruction if empty
            if not self.instructions:
                self._emit_halt()

            # Build bytecode
            bytecode = self._build_bytecode()

            logger.info(f"Generated {len(self.instructions)} instructions")
            logger.info(f"Constants: {len(self.constants)}")

            return Bytecode(bytecode, self.vm_instructions)

        except Exception as e:
            logger.error(f"Code generation error: {e}")
            raise

    def _generate_from_ast(self, node: Any) -> None:
        """Generate bytecode from AST node."""
        if isinstance(node, ast.Module):
            for stmt in node.body:
                self._generate_from_ast(stmt)

        elif isinstance(node, ast.Assign):
            self._generate_from_ast(node.value)

        elif isinstance(node, ast.Expr):
            self._generate_from_ast(node.value)
        
        elif isinstance(node, ast.Constant):
            self._emit_load_const(node.value)
        
        elif isinstance(node, ast.Name):
            self._emit_load_name(node.id)
        
        elif isinstance(node, ast.BinOp):
            self._generate_from_ast(node.left)
            self._generate_from_ast(node.right)
            self._emit_binop(type(node.op))
        
        elif isinstance(node, ast.UnaryOp):
            self._generate_from_ast(node.operand)
            self._emit_unaryop(type(node.op))
        
        elif isinstance(node, ast.If):
            self._generate_from_ast(node.test)
            self._emit_jmp_if_zero()
            
            # Generate else body
            if node.orelse:
                self._generate_from_ast(node.orelse[0])
            
            # Generate then body
            self._generate_from_ast(node.body[0])
        
        elif isinstance(node, ast.For):
            # Loop variable
            self._emit_load_const(None)  # Placeholder
            
            # Loop body
            self._generate_from_ast(node.body[0])
            
            # Loop back
            self._emit_jmp()
            
            # Loop end
            self._emit_halt()
        
        elif isinstance(node, ast.FunctionDef):
            self._generate_function(node)
    
    def _emit_load_const(self, value: Any) -> None:
        """Emit LOAD_CONST instruction."""
        # Add constant if not already present
        const_index = None
        for i, c in enumerate(self.constants):
            if c == value:
                const_index = i
                break
        
        if const_index is None:
            self.constants.append(value)
            const_index = len(self.constants) - 1
        
        self.instructions.append(BytecodeInstruction(
            opcode=self.OP_LOAD_CONST,
            operand=const_index
        ))
        val_int = value if isinstance(value, int) else 0
        self.vm_instructions.append(Instruction(
            opcode=Instruction.Opcodes.LOAD_CONST,
            operands=[0, val_int],
            rd_or_operands=0,
            r1_or_line=val_int
        ))
    
    def _emit_load_name(self, name: str) -> None:
        """Emit LOAD_NAME instruction."""
        # For now, load as constant
        self._emit_load_const(name)
    
    def _emit_binop(self, op_type: type) -> None:
        """Emit binary operation."""
        op_map = {
            ast.Add: self.OP_MOV,  # Simplified
            ast.Sub: self.OP_MOV,
            ast.Mult: self.OP_MOV,
            ast.Div: self.OP_MOV,
            ast.Mod: self.OP_MOV,
            ast.Pow: self.OP_FAUL_EVAL,
            ast.Eq: self.OP_BOUND_CHECK,
            ast.NotEq: self.OP_BOUND_CHECK,
            ast.Lt: self.OP_BOUND_CHECK,
            ast.Gt: self.OP_BOUND_CHECK,
            ast.LtE: self.OP_BOUND_CHECK,
            ast.GtE: self.OP_BOUND_CHECK,
            ast.And: self.OP_MOV,
            ast.Or: self.OP_MOV
        }
        
        opcode = op_map.get(op_type, self.OP_MOV)
        self.instructions.append(BytecodeInstruction(opcode=opcode))
        self.vm_instructions.append(Instruction(
            opcode=Instruction.Opcodes.ADD,
            operands=[0, 1]
        ))
    
    def _emit_unaryop(self, op_type: type) -> None:
        """Emit unary operation."""
        self.instructions.append(BytecodeInstruction(opcode=self.OP_MOV))
    
    def _emit_jmp_if_zero(self) -> None:
        """Emit JMP_IF_ZERO instruction."""
        self.instructions.append(BytecodeInstruction(
            opcode=self.OP_JMP_IF_ZERO
        ))
    
    def _emit_jmp(self) -> None:
        """Emit JMP instruction."""
        self.instructions.append(BytecodeInstruction(
            opcode=self.OP_JMP
        ))
    
    def _emit_halt(self) -> None:
        """Emit HALT instruction."""
        self.instructions.append(BytecodeInstruction(
            opcode=self.OP_HALT
        ))
        self.vm_instructions.append(Instruction(
            opcode=Instruction.Opcodes.HALT,
            operands=[0]
        ))
    
    def _generate_function(self, func: ast.FunctionDef) -> None:
        """Generate bytecode for a function."""
        # Function entry
        self._emit_load_const(None)
        
        # Function body
        for stmt in func.body:
            self._generate_from_ast(stmt)
        
        # Function exit
        self._emit_halt()
    
    def _build_bytecode(self) -> bytes:
        """Build bytecode from instructions."""
        bytecode = bytearray()
        
        for instr in self.instructions:
            # Pack instruction as 4 bytes
            bytecode.extend(struct.pack('>4B', instr.opcode, instr.operand, 
                                       instr.operand2, 0))
        
        return bytes(bytecode)
    
    def get_instructions(self) -> List[BytecodeInstruction]:
        """Get generated instructions."""
        return self.instructions
    
    def get_constants(self) -> List[Any]:
        """Get constants pool."""
        return self.constants


def compile_ast(ast_tree: Any) -> bytes:
    """
    Convenience function to compile AST to bytecode.
    
    Args:
        ast_tree: AST to compile
        
    Returns:
        Bytecode bytes
    """
    generator = OrthosCodeGenerator()
    return generator.generate(ast_tree)
