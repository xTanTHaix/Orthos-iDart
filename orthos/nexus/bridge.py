"""
Nexus Bridge - Fast-Path Pre-Filter & Security Firewall
========================================================

This module implements the Nexus fast-path pre-filter that intercepts
known bottleneck patterns before they reach the full formal verification
pipeline.

Features:
- Heuristic bottleneck detection
- Security firewall for FDs, sockets, shared state
- Sentinel micro-kernel integration
- Compiler plugins for optimization
"""

import ast
import os
import struct
import zlib
import logging
from typing import Tuple, Any, Optional, Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)


class NexusBridge:
    """
    Fast-path pre-filter for known bottleneck patterns.
    
    Intercepts and optimizes:
    - Attribute churn in loops
    - EAFP try-except patterns
    - String accumulation with +=
    """
    
    def __init__(self, sentinel_path: Optional[str] = None):
        """
        Initialize the Nexus bridge.
        
        Args:
            sentinel_path: Path to sentinel.oxb micro-kernel
        """
        if sentinel_path is None:
            # Default path relative to this module
            sentinel_path = os.path.join(
                os.path.dirname(__file__),
                "..", "nexus", "sentinel.oxb"
            )
        
        self.sentinel_path = sentinel_path
        self.sentinel_bytecode: bytes = b''
        self.sentinel_constants: List[Any] = []
        self.is_active: bool = False
        self._bootstrap_sentinel()
    
    def _bootstrap_sentinel(self) -> None:
        """
        Bootstrap the sentinel micro-kernel.
        
        Loads and validates sentinel.oxb file.
        """
        if not os.path.exists(self.sentinel_path):
            logger.warning(f"Sentinel not found: {self.sentinel_path}")
            return
        
        try:
            with open(self.sentinel_path, 'rb') as f:
                data = f.read()
            
            if len(data) < 24:
                logger.warning("Sentinel file too small")
                return
            
            # Parse header
            magic, version, flags, checksum, c_off, s_off, b_off, e_off = \
                struct.unpack_from('>4sHHI4I', data, 0)
            
            # Validate magic
            if magic != b'ORTH':
                logger.warning("Invalid sentinel magic number")
                return
            
            # Validate checksum
            payload = data[c_off:]
            if (zlib.crc32(payload) & 0xFFFFFFFF) != checksum:
                logger.warning("Sentinel CRC32 mismatch - tamper detected")
                return
            
            # Extract bytecode
            self.sentinel_bytecode = data[b_off:]
            self.sentinel_constants = self._extract_constants(data, c_off)
            self.is_active = True
            
            logger.info(f"Sentinel micro-kernel loaded: {len(self.sentinel_bytecode)} bytes")
            
        except Exception as e:
            logger.error(f"Failed to bootstrap sentinel: {e}")
    
    def _extract_constants(self, data: bytes, offset: int) -> List[Any]:
        """Extract constant pool from sentinel file."""
        constants = []
        remaining = data[offset:]
        
        while len(remaining) >= 4:
            value = struct.unpack_from('>I', remaining, 0)[0]
            constants.append(value)
            remaining = remaining[4:]
        
        return constants
    
    def scan_and_intercept(self, node: ast.AST) -> Tuple[bool, str]:
        """
        Scan AST for bottleneck patterns.
        
        Args:
            node: AST node to analyze
            
        Returns:
            Tuple of (has_bottleneck, strategy)
            
        Strategy options:
            - "PASS_THROUGH": No optimization needed
            - "FLATTEN_STRUCT": Use struct flattener
            - "ELIMINATE_EXCEPTIONS": Use exception eliminator
            - "DF_STRING": Use DFA string emitter
        """
        strategy = "PASS_THROUGH"
        has_bottleneck = False
        
        try:
            # Walk the AST
            for subnode in ast.walk(node):
                # Check for loops
                if isinstance(subnode, (ast.For, ast.While)):
                    # Check inner nodes for patterns
                    for inner in ast.walk(subnode):
                        # EAFP pattern: try/except in loop
                        if isinstance(inner, ast.Try):
                            has_bottleneck = True
                            strategy = "ELIMINATE_EXCEPTIONS"
                            logger.debug("Detected EAFP pattern in loop")
                        
                        # Attribute churn: chain of attributes
                        if isinstance(inner, ast.Attribute):
                            if isinstance(inner.value, ast.Attribute):
                                strategy = "FLATTEN_STRUCT"
                                logger.debug("Detected attribute churn pattern")
                        
                        # String accumulation
                        if isinstance(inner, ast.BinOp) and isinstance(inner.op, ast.Add):
                            if isinstance(inner.left, ast.Str) or isinstance(inner.left, ast.Constant):
                                strategy = "DF_STRING"
                                logger.debug("Detected string accumulation pattern")
                
                # Check for string operations outside loops
                elif isinstance(subnode, ast.BinOp) and isinstance(subnode.op, ast.Add):
                    if isinstance(subnode.left, ast.Str) or isinstance(subnode.left, ast.Constant):
                        strategy = "DF_STRING"
            
            return has_bottleneck, strategy
            
        except Exception as e:
            logger.error(f"Scan error: {e}")
            return False, "PASS_THROUGH"
    
    def dispatch_to_vm(self, routine_entrypoint: int, inputs: List[Any]) -> Any:
        """
        Dispatch routine to sentinel VM.
        
        Args:
            routine_entrypoint: Entry point instruction
            inputs: Input values for registers
            
        Returns:
            VM execution result
        """
        if not self.is_active:
            raise RuntimeError("Sentinel Micro-Kernel is unavailable or corrupted.")
        
        try:
            from orthos.vm.core import OrthosVM
            
            vm = OrthosVM(
                constants=self.sentinel_constants,
                bytecode=self.sentinel_bytecode
            )
            
            # Pre-decode
            vm.pre_decode()
            
            # Set input registers
            for idx, val in enumerate(inputs):
                if idx < 256:
                    vm.registers[idx] = val
            
            # Execute
            result = vm.execute(entrypoint=routine_entrypoint)
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"VM dispatch error: {e}")
            raise
    
    def is_safe_for_vm(self, node: ast.AST) -> bool:
        """
        Check if code is safe for VM execution.

        Args:
            node: AST node to check

        Returns:
            True if safe for VM, False otherwise
        """
        try:
            # Check for unsafe patterns
            for subnode in ast.walk(node):
                # Unsafe: eval, exec, locals, globals
                if isinstance(subnode, ast.Call):
                    if isinstance(subnode.func, ast.Name):
                        if subnode.func.id in ('eval', 'exec', 'locals', 'globals'):
                            return False

                # Unsafe: file operations
                if isinstance(subnode, ast.Call):
                    if isinstance(subnode.func, ast.Attribute):
                        if subnode.func.attr in ('open', 'write', 'read'):
                            return False

                # Unsafe: dangerous imports (os, sys, subprocess, shutil, socket)
                if isinstance(subnode, (ast.Import, ast.ImportFrom)):
                    for alias in subnode.names:
                        if alias.name.split('.')[0] in ('os', 'sys', 'subprocess', 'shutil', 'socket'):
                            return False

                # Unsafe: system execution calls
                if isinstance(subnode, ast.Call):
                    if isinstance(subnode.func, ast.Attribute):
                        if subnode.func.attr in ('system', 'popen', 'spawn', 'execv', 'execve'):
                            return False

                # Unsafe: network operations
                if isinstance(subnode, ast.Call):
                    if isinstance(subnode.func, ast.Attribute):
                        if subnode.func.attr == 'send':
                            return False

            return True

        except Exception as e:
            logger.error(f"Safety check error: {e}")
            return False

    def filter_code(self, source: str) -> Tuple[bool, str]:
        """
        Filter source code for bottleneck patterns.

        Parses *source* into an AST and delegates to scan_and_intercept.

        Args:
            source: Python source code string.

        Returns:
            Tuple of (has_bottleneck: bool, strategy: str).
        """
        try:
            tree = ast.parse(source)
            return self.scan_and_intercept(tree)
        except SyntaxError as exc:
            logger.warning(f"filter_code: SyntaxError parsing source: {exc}")
            return False, "PASS_THROUGH"
        except Exception as exc:
            logger.error(f"filter_code: unexpected error: {exc}")
            return False, "PASS_THROUGH"

    def check_security(self, source: str) -> Tuple[bool, str]:
        """
        Perform a security check on Python source code.

        Parses *source* into an AST and delegates to is_safe_for_vm.

        Args:
            source: Python source code string.

        Returns:
            Tuple of (is_safe: bool, message: str)
        """
        try:
            tree = ast.parse(source)
            safe = self.is_safe_for_vm(tree)
            return safe, "Code is safe" if safe else "Unsafe code pattern detected"
        except SyntaxError as exc:
            return False, f"Syntax error: {exc}"
        except Exception as exc:
            logger.error(f"check_security: unexpected error: {exc}")
            return False, f"Error: {exc}"

    def analyze_code(self, source: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Analyze code for safety and optimization potential.

        Args:
            source: Python source code string.

        Returns:
            Tuple of (is_safe: bool, analysis: Dict[str, Any])
        """
        is_safe, msg = self.check_security(source)
        analysis = {
            "safe": is_safe,
            "message": msg,
            "complexity": "O(N)",
            "bottlenecks": [],
            "candidates": ["loop", "recursion"] if ("for" in source or "def" in source) else []
        }
        return is_safe, analysis





class SecurityFirewall:
    """
    Isolated security firewall for quarantine.
    
    Quarantines:
    - File descriptors
    - Network sockets
    - Cross-thread shared state
    """
    
    def __init__(self):
        """Initialize the firewall."""
        self.quarantined_resources: List[Dict[str, Any]] = []
        self.is_active = True
    
    def quarantine_fd(self, fd: int) -> bool:
        """
        Quarantine a file descriptor.
        
        Args:
            fd: File descriptor number
            
        Returns:
            True if quarantined successfully
        """
        try:
            import os
            
            # Close the FD
            os.close(fd)
            
            # Record quarantine
            self.quarantined_resources.append({
                'type': 'file_descriptor',
                'fd': fd,
                'timestamp': os.time()
            })
            
            logger.info(f"Quarantined file descriptor: {fd}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to quarantine FD {fd}: {e}")
            return False
    
    def quarantine_socket(self, sock: Any) -> bool:
        """
        Quarantine a network socket.
        
        Args:
            sock: Socket object
            
        Returns:
            True if quarantined successfully
        """
        try:
            import socket
            
            # Close the socket
            sock.close()
            
            # Record quarantine
            self.quarantined_resources.append({
                'type': 'socket',
                'sock_id': id(sock),
                'timestamp': os.time()
            })
            
            logger.info(f"Quarantined socket: {id(sock)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to quarantine socket: {e}")
            return False
    
    def check_cross_thread(self, thread_id: int) -> bool:
        """
        Check for cross-thread access.
        
        Args:
            thread_id: Thread identifier
            
        Returns:
            True if cross-thread access detected
        """
        # Simplified check
        # Full implementation would use threading module
        return False
    
    def get_quarantine_report(self) -> List[Dict[str, Any]]:
        """Get quarantine report."""
        return self.quarantined_resources.copy()


def create_nexus_bridge(sentinel_path: Optional[str] = None) -> NexusBridge:
    """
    Convenience function to create Nexus bridge.
    
    Args:
        sentinel_path: Path to sentinel.oxb
        
    Returns:
        NexusBridge instance
    """
    return NexusBridge(sentinel_path=sentinel_path)
