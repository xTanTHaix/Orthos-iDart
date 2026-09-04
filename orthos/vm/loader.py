"""
Orthos VM Loader - .oxb File Format Handler
===========================================

This module handles loading and validation of .oxb bytecode files.

Features:
- CRC32 checksum verification
- Version gate checking
- Wire format parsing
- Safe fallback on validation failure
"""

import os
import struct
import zlib
import logging
from typing import Tuple, Optional, List, Any
from orthos.vm.core import Instruction

logger = logging.getLogger(__name__)


class OXBValidationError(Exception):
    """Exception raised for .oxb file validation errors."""
    pass


class OrthosLoader:
    """
    Loader for .oxb bytecode files.
    
    Validates and loads .oxb files with:
    - Magic number verification
    - CRC32 checksum validation
    - Version compatibility checking
    - Wire format parsing
    """
    
    # Magic number for .oxb files
    MAGIC = b'ORTH'
    
    # Wire format version
    VERSION = 0x0002
    
    # Header structure (Big-Endian)
    # Offset 0: Magic (4 bytes)
    # Offset 4: Version (2 bytes)
    # Offset 6: Flags (2 bytes)
    # Offset 8: CRC32 checksum (4 bytes)
    # Offset 12: Constant offset (4 bytes)
    # Offset 16: Span source offset (4 bytes)
    # Offset 20: Bytecode offset (4 bytes)
    # Offset 24: End offset (4 bytes)
    HEADER_SIZE = 28
    
    def __init__(self):
        """Initialize the loader."""
        self.file_path: Optional[str] = None
        self.file_data: Optional[bytes] = None
        self.constants: List[Any] = []
        self.span_sources: List[bytes] = []
        self.bytecode: bytes = b''
        self.is_valid: bool = False
    
    def load(self, file_path: str) -> Any:
        """
        Load and validate a .oxb file.
        
        Args:
            file_path: Path to the .oxb file
            
        Returns:
            Instructions list or True if loaded successfully, False otherwise
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            self.file_path = file_path
            self.file_data = None
            
            # Read file
            with open(file_path, 'rb') as f:
                self.file_data = f.read()
            
            # Check for TPXS minimal format
            if len(self.file_data) >= 9 and self.file_data[:4] == b"TPXS":
                payload = self.file_data[9:-4]
                self.bytecode = payload
                self.is_valid = True
                instructions = []
                idx = 0
                while idx < len(payload):
                    op = payload[idx]
                    next_pos = idx + 1
                    operand = payload[next_pos] if next_pos < len(payload) else 0
                    instructions.append(Instruction(op, [operand], 0))
                    idx += 2
                self.instructions = instructions
                return instructions

            if len(self.file_data) < self.HEADER_SIZE:
                logger.error(f"File too small: {file_path}")
                return False
            
            # Parse header
            header = self._parse_header()
            
            # Validate magic number
            if not self._validate_magic(header):
                logger.error(f"Invalid magic number in {file_path}")
                return False
            
            # Validate version
            if not self._validate_version(header):
                logger.error(f"Unsupported version in {file_path}")
                return False
            
            # Validate CRC32
            if not self._validate_checksum(header):
                logger.error(f"CRC32 mismatch in {file_path}")
                return False
            
            # Extract sections
            self.constants = self._extract_constants(header)
            self.span_sources = self._extract_span_sources(header)
            self.bytecode = self._extract_bytecode(header)
            
            self.is_valid = True
            logger.info(f"Loaded .oxb file: {file_path}")
            logger.info(f"  Version: {header['version']}")
            logger.info(f"  Constants: {len(self.constants)}")
            logger.info(f"  Span sources: {len(self.span_sources)}")
            logger.info(f"  Bytecode: {len(self.bytecode)} bytes")
            
            instructions = []
            if self.bytecode:
                for i in range(0, len(self.bytecode), 4):
                    chunk = self.bytecode[i:i+4]
                    if len(chunk) == 4:
                        op, rd, r1, r2 = chunk
                        instructions.append(Instruction(op, rd, r1, r2))
            self.instructions = instructions
            return instructions if instructions else True
            
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to load .oxb file {file_path}: {e}")
            return False
    
    def _parse_header(self) -> dict:
        """Parse the .oxb file header."""
        header = {
            'magic': None,
            'version': None,
            'flags': None,
            'checksum': None,
            'const_offset': None,
            'span_offset': None,
            'bytecode_offset': None,
            'end_offset': None
        }
        
        # Unpack header (Big-Endian)
        magic, version, flags, checksum, c_off, s_off, b_off, e_off = \
            struct.unpack_from('>4sHHI4I', self.file_data, 0)
        
        header['magic'] = magic
        header['version'] = version
        header['flags'] = flags
        header['checksum'] = checksum
        header['const_offset'] = c_off
        header['span_offset'] = s_off
        header['bytecode_offset'] = b_off
        header['end_offset'] = e_off
        
        return header
    
    def _validate_magic(self, header: dict) -> bool:
        """Validate magic number."""
        return header['magic'] == self.MAGIC
    
    def _validate_version(self, header: dict) -> bool:
        """Validate file version."""
        # Accept current version and older versions for backward compatibility
        return header['version'] <= self.VERSION
    
    def _validate_checksum(self, header: dict) -> bool:
        """Validate CRC32 checksum."""
        # Extract payload (everything after header)
        payload = self.file_data[self.HEADER_SIZE:]
        
        # Calculate CRC32
        calculated_crc = zlib.crc32(payload) & 0xFFFFFFFF
        
        # Compare with stored checksum
        return calculated_crc == header['checksum']
    
    def _extract_constants(self, header: dict) -> List[Any]:
        """Extract constant pool from file."""
        try:
            const_offset = header['const_offset']
            const_end = header['end_offset']
            
            if const_offset >= const_end:
                return []
            
            # Constants are stored as 4-byte integers
            constants = []
            data = self.file_data[const_offset:const_end]
            
            while len(data) >= 4:
                value = struct.unpack_from('>I', data, 0)[0]
                constants.append(value)
                data = data[4:]
            
            return constants
            
        except Exception as e:
            logger.error(f"Failed to extract constants: {e}")
            return []
    
    def _extract_span_sources(self, header: dict) -> List[bytes]:
        """Extract span source buffers from file."""
        try:
            span_offset = header['span_offset']
            bytecode_offset = header['bytecode_offset']
            
            if span_offset >= bytecode_offset:
                return []
            
            # Span sources are between span_offset and bytecode_offset
            sources_data = self.file_data[span_offset:bytecode_offset]
            
            # For now, return empty list
            # Full implementation would parse span source headers
            return []
            
        except Exception as e:
            logger.error(f"Failed to extract span sources: {e}")
            return []
    
    def _extract_bytecode(self, header: dict) -> bytes:
        """Extract bytecode from file."""
        try:
            bytecode_offset = header['bytecode_offset']
            end_offset = header['end_offset']
            
            if bytecode_offset >= end_offset:
                return b''
            
            return self.file_data[bytecode_offset:end_offset]
            
        except Exception as e:
            logger.error(f"Failed to extract bytecode: {e}")
            return b''
    
    def get_bytecode(self) -> bytes:
        """Get loaded bytecode."""
        return self.bytecode
    
    def get_constants(self) -> List[Any]:
        """Get loaded constants."""
        return self.constants
    
    def get_span_sources(self) -> List[bytes]:
        """Get loaded span sources."""
        return self.span_sources
    
    def get_info(self) -> dict:
        """Get loader information."""
        return {
            'file_path': self.file_path,
            'is_valid': self.is_valid,
            'version': self.VERSION,
            'constants_count': len(self.constants),
            'span_sources_count': len(self.span_sources),
            'bytecode_size': len(self.bytecode)
        }
    
    def validate_only(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate a .oxb file without loading.
        
        Args:
            file_path: Path to the .oxb file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            if len(data) < self.HEADER_SIZE:
                return False, "File too small"
            
            # Parse header
            magic, version, flags, checksum, _, _, _, _ = \
                struct.unpack_from('>4sHHI4I', data, 0)
            
            # Validate
            if magic != self.MAGIC:
                return False, "Invalid magic number"
            
            if version > self.VERSION:
                return False, f"Unsupported version: {version}"
            
            # Validate checksum
            payload = data[self.HEADER_SIZE:]
            calculated_crc = zlib.crc32(payload) & 0xFFFFFFFF
            
            if calculated_crc != checksum:
                return False, "CRC32 mismatch"
            
            return True, "Valid"
            
        except Exception as e:
            return False, str(e)


def load_oxb_file(file_path: str) -> Tuple[bool, OrthosLoader]:
    """
    Convenience function to load a .oxb file.
    
    Args:
        file_path: Path to the .oxb file
        
    Returns:
        Tuple of (success, loader_instance)
    """
    loader = OrthosLoader()
    success = loader.load(file_path)
    return success, loader
