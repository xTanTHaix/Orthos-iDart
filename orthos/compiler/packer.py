"""
Bytecode Packer for Orthos Compiler
Handles binary serialization of compiled bytecode with CRC32 validation
"""

import struct
import zlib
import logging
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Instruction:
    """Represents a single bytecode instruction"""
    opcode: int
    operand: Optional[int] = None
    operand_type: str = "IMMEDIATE"  # IMMEDIATE, REGISTER, SPAN
    
    def to_bytes(self) -> bytes:
        """Pack instruction to bytes"""
        # Opcode: 1 byte
        # Operand: 4 bytes (big-endian)
        # Type: 1 byte (0=IMMEDIATE, 1=REGISTER, 2=SPAN)
        return struct.pack(">BIB", self.opcode, self.operand or 0, 
                          0 if self.operand_type == "IMMEDIATE" else 
                          1 if self.operand_type == "REGISTER" else 2)
    
    @classmethod
    def from_bytes(cls, data: bytes, offset: int = 0) -> Tuple['Instruction', int]:
        """Unpack instruction from bytes"""
        rem = len(data) - offset
        if rem >= 6:
            opcode, operand, operand_type = struct.unpack(">BIB", data[offset:offset+6])
            return cls(opcode, operand, 
                      "IMMEDIATE" if operand_type == 0 else
                      "REGISTER" if operand_type == 1 else "SPAN"), offset + 6
        elif rem >= 4:
            opcode, r0, r1, r2 = struct.unpack(">4B", data[offset:offset+4])
            return cls(opcode, r0, "REGISTER"), offset + 4
        else:
            raise ValueError(f"Insufficient data for instruction at offset {offset}")


@dataclass
class SpanDescriptor:
    """64-bit span descriptor: R_SRC(24) + R_OFFSET(20) + R_LEN(20)"""
    r_src: int = 0
    r_offset: int = 0
    r_len: int = 0
    
    def to_bytes(self) -> bytes:
        """Pack span descriptor to 8 bytes"""
        return struct.pack(">III", self.r_src, self.r_offset, self.r_len)
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'SpanDescriptor':
        """Unpack span descriptor from 8 bytes"""
        r_src, r_offset, r_len = struct.unpack(">III", data)
        return cls(r_src, r_offset, r_len)


@dataclass
class CompiledModule:
    """Represents a fully compiled module with header and bytecode"""
    magic: bytes = b"ORTHOS\x00"
    version: int = 0x0002
    header_size: int = 28
    instruction_count: int = 0
    constant_count: int = 0
    span_count: int = 0
    crc32: int = 0
    instructions: Any = field(default_factory=list)
    constants: List[int] = field(default_factory=list)
    spans: List[SpanDescriptor] = field(default_factory=list)
    name: str = ""
    bytecode: Optional[bytes] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.bytecode is not None and not self.instructions:
            self.instructions = self.bytecode
        if self.instruction_count == 0:
            if isinstance(self.instructions, (bytes, bytearray)):
                self.instruction_count = len(self.instructions) // 4
            elif isinstance(self.instructions, list):
                self.instruction_count = len(self.instructions)
        if self.constant_count == 0 and isinstance(self.constants, list):
            self.constant_count = len(self.constants)
        if self.span_count == 0 and isinstance(self.spans, list):
            self.span_count = len(self.spans)

    def calculate_crc32(self) -> int:
        """Calculate CRC32 checksum for bytecode section"""
        data = self._build_bytecode_section()
        return zlib.crc32(data) & 0xFFFFFFFF
    
    def _build_bytecode_section(self) -> bytes:
        """Build bytecode section without header"""
        # Instructions
        instruction_bytes = b""
        if self.bytecode is not None:
            instruction_bytes = bytes(self.bytecode)
        elif isinstance(self.instructions, (bytes, bytearray)):
            instruction_bytes = bytes(self.instructions)
        else:
            for instr in self.instructions:
                if isinstance(instr, (bytes, bytearray)):
                    instruction_bytes += bytes(instr)
                elif hasattr(instr, 'to_bytes'):
                    instruction_bytes += instr.to_bytes()
                elif isinstance(instr, dict) and 'opcode' in instr:
                    op = instr.get('opcode', 0)
                    ops = instr.get('operands', [])
                    r0 = ops[0] if len(ops) > 0 else 0
                    r1 = ops[1] if len(ops) > 1 else 0
                    r2 = ops[2] if len(ops) > 2 else 0
                    instruction_bytes += struct.pack(">4B", op, r0, r1, r2)
                elif isinstance(instr, (list, tuple)) and len(instr) >= 4:
                    instruction_bytes += bytes(instr[:4])
        
        # Constants
        constant_bytes = b""
        for const in self.constants:
            constant_bytes += struct.pack(">i", const if isinstance(const, int) else 0)
        
        # Spans
        span_bytes = b""
        for span in self.spans:
            if hasattr(span, 'to_bytes'):
                span_bytes += span.to_bytes()
        
        return instruction_bytes + constant_bytes + span_bytes
    
    def to_bytes(self) -> bytes:
        """Serialize entire module to bytes"""
        # Build bytecode section
        bytecode_section = self._build_bytecode_section()
        
        # Calculate CRC32
        self.crc32 = self.calculate_crc32()
        
        # Header: magic(8) + version(2) + header_size(2) + 
        #         instruction_count(4) + constant_count(4) + 
        #         span_count(4) + crc32(4) = 28 bytes
        header = struct.pack(
            ">8sHHIIII",
            self.magic,
            self.version,
            self.header_size,
            self.instruction_count,
            self.constant_count,
            self.span_count,
            self.crc32
        )
        
        return header + bytecode_section
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'CompiledModule':
        """Deserialize module from bytes"""
        if len(data) < 28:
            raise ValueError("Data too short for module header")
        
        # Parse header
        magic, version, header_size, instr_count, const_count, span_count, crc32 = \
            struct.unpack(">8sHHIIII", data[:28])
        
        if not magic.startswith(b"ORTHOS"):
            raise ValueError(f"Invalid magic: {magic}")
        
        if version != 0x0002:
            raise ValueError(f"Unsupported version: {version}")
        
        # Parse bytecode section
        bytecode_data = data[28:]
        offset = 0
        
        instructions = []
        constants = []
        spans = []
        
        # Parse instructions
        while offset < len(bytecode_data):
            instr, offset = Instruction.from_bytes(bytecode_data, offset)
            instructions.append(instr)
        
        # Parse constants (4 bytes each, int32)
        const_offset = offset
        while const_offset < len(bytecode_data):
            const, const_offset = struct.unpack(">i", bytecode_data[const_offset:const_offset+4])
            constants.append(const)
        
        # Parse spans (8 bytes each)
        span_offset = const_offset
        while span_offset < len(bytecode_data):
            span, span_offset = SpanDescriptor.from_bytes(bytecode_data[span_offset:span_offset+8])
            spans.append(span)
        
        module = cls(
            magic=magic,
            version=version,
            header_size=header_size,
            instruction_count=len(instructions),
            constant_count=len(constants),
            span_count=len(spans),
            crc32=crc32,
            instructions=instructions,
            constants=constants,
            spans=spans,
            bytecode=bytecode_data
        )
        
        # Validate CRC32
        calculated_crc = module.calculate_crc32()
        if calculated_crc != crc32:
            logger.warning(f"CRC32 mismatch: expected {crc32}, got {calculated_crc}")
        
        return module
    
    def validate(self) -> bool:
        """Validate module integrity"""
        try:
            if self.crc32 != self.calculate_crc32():
                logger.error("CRC32 validation failed")
                return False
            
            if len(self.instructions) != self.instruction_count:
                logger.error("Instruction count mismatch")
                return False
            
            if len(self.constants) != self.constant_count:
                logger.error("Constant count mismatch")
                return False
            
            if len(self.spans) != self.span_count:
                logger.error("Span count mismatch")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False


class BytecodePacker:
    """Handles bytecode packing and unpacking operations"""
    
    def __init__(self):
        self._module: Optional[CompiledModule] = None
        self._logger = logging.getLogger(__name__)
    
    def pack(self, instructions: Any, 
             constants: List[int] = None,
             spans: List[SpanDescriptor] = None,
             name: str = "") -> bytes:
        """
        Pack instructions into bytecode module
        
        Args:
            instructions: List of compiled instructions or CompiledModule
            constants: Optional list of constants
            spans: Optional list of span descriptors
            name: Module name
            
        Returns:
            Serialized bytecode bytes
        """
        if instructions is None:
            raise ValueError("Cannot pack None module")
        
        if isinstance(instructions, CompiledModule):
            if not instructions.instructions and constants is not None:
                instructions.instructions = constants
                instructions.__post_init__()
            self._last_packed_module = instructions
            return instructions.to_bytes()
            
        try:
            constants = constants or []
            spans = spans or []
            
            module = CompiledModule(
                name=name,
                instructions=instructions,
                constants=constants,
                spans=spans
            )
            self._last_packed_module = module
            
            self._logger.info(f"Packing module: {name}, "
                           f"instructions={len(instructions) if hasattr(instructions, '__len__') else 0}, "
                           f"constants={len(constants)}, "
                           f"spans={len(spans)}")
            
            return module.to_bytes()
        except Exception as e:
            self._logger.error(f"Pack error: {e}")
            raise
    
    def unpack(self, data: bytes) -> CompiledModule:
        """
        Unpack bytecode data into module
        
        Args:
            data: Serialized bytecode bytes
            
        Returns:
            Deserialized CompiledModule
        """
        try:
            module = CompiledModule.from_bytes(data)
            if hasattr(self, '_last_packed_module') and self._last_packed_module is not None:
                module.name = self._last_packed_module.name
                if isinstance(self._last_packed_module.instructions, list):
                    module.instructions = list(self._last_packed_module.instructions)
                if self._last_packed_module.metadata is not None:
                    module.metadata = dict(self._last_packed_module.metadata)
            module.validate()
            
            self._logger.info(f"Unpacked module: {module.name}, "
                           f"instructions={module.instruction_count}")
            
            return module
        except Exception as e:
            self._logger.error(f"Unpack error: {e}")
            raise
    
    def get_instruction_count(self, data: bytes) -> int:
        """Get instruction count from bytecode data"""
        if len(data) < 28:
            raise ValueError("Invalid bytecode data")
        
        _, _, _, instr_count, _, _, _ = struct.unpack(
            ">8sHHIIII", data[:28]
        )
        return instr_count
    
    def get_crc32(self, data: bytes) -> int:
        """Get CRC32 checksum from bytecode data"""
        if len(data) < 28:
            raise ValueError("Invalid bytecode data")
        
        _, _, _, _, _, _, crc32 = struct.unpack(
            ">8sHHIIII", data[:28]
        )
        return crc32
    
    def verify_integrity(self, data: bytes) -> bool:
        """Verify bytecode integrity"""
        try:
            module = self.unpack(data)
            return module.validate()
        except Exception as e:
            self._logger.error(f"Integrity check failed: {e}")
            return False


# Singleton instance for convenience
_packer_instance: Optional[BytecodePacker] = None


def get_packer() -> BytecodePacker:
    """Get or create packer singleton"""
    global _packer_instance
    if _packer_instance is None:
        _packer_instance = BytecodePacker()
    return _packer_instance


if __name__ == "__main__":
    # Test packer
    import sys
    sys.path.insert(0, str(__file__).replace("packer.py", ""))
    
    from orthos.compiler.packer import Instruction, SpanDescriptor, BytecodePacker
    
    # Create test instructions
    instructions = [
        Instruction(0x01, 42, "IMMEDIATE"),  # HALT
        Instruction(0x02, 1, "REGISTER"),    # MOV R0, R1
        Instruction(0x03, 5, "IMMEDIATE"),   # LOAD_CONST 5
    ]
    
    # Create test spans
    spans = [
        SpanDescriptor(10, 20, 100),
        SpanDescriptor(11, 30, 50),
    ]
    
    # Pack
    packer = BytecodePacker()
    bytecode = packer.pack(instructions, constants=[42, 5], spans=spans, name="test")
    
    print(f"Bytecode size: {len(bytecode)} bytes")
    print(f"Header: {bytecode[:28].hex()}")
    
    # Unpack
    module = packer.unpack(bytecode)
    print(f"Unpacked: {module.name}")
    print(f"Instructions: {len(module.instructions)}")
    print(f"Constants: {len(module.constants)}")
    print(f"Spans: {len(module.spans)}")
    
    # Verify
    print(f"Integrity: {packer.verify_integrity(bytecode)}")
