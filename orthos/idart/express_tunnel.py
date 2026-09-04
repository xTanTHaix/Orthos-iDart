"""
IDart Express Tunnel Module - Zero-Copy Optimization Pipeline

This module implements zero-copy optimization techniques including
span-based memory access, demand-driven computation, and
direct memory mapping for high-performance data movement.
"""

import logging
import struct
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from collections import defaultdict

# Configure logging
logger = logging.getLogger(__name__)


class TunnelType(Enum):
    """Types of express tunnels."""
    MEMORY = "memory"
    STREAM = "stream"
    SHARED = "shared"
    DIRECT = "direct"


class OptimizationOp(Enum):
    """Available optimization operations."""
    ZERO_COPY = "zero_copy"
    BUFFER_REUSE = "buffer_reuse"
    STREAM_MERGE = "stream_merge"
    MEMORY_COALESCING = "memory_coalescing"
    PREDICTIVE_LOADING = "predictive_loading"
    CACHE_OPTIMIZATION = "cache_optimization"


@dataclass
class SpanDescriptor:
    """Descriptor for zero-copy memory spans."""
    src_register: int
    offset: int
    length: int
    alignment: int = 8
    is_read: bool = True
    is_write: bool = False
    access_pattern: str = "sequential"
    cache_line: int = 0
    
    def to_bytes(self) -> bytes:
        """Pack span descriptor to binary format."""
        pat = 0 if self.access_pattern == "sequential" else 1
        return struct.pack(
            '<IIIbb',
            self.src_register,
            self.offset,
            self.length,
            self.alignment,
            pat
        )
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'SpanDescriptor':
        """Unpack binary format to span descriptor."""
        register, offset, length, alignment, access_pattern = struct.unpack(
            '<IIIbb', data
        )
        return cls(
            src_register=register,
            offset=offset,
            length=length,
            alignment=alignment,
            access_pattern="sequential" if access_pattern == 0 else "random"
        )
    
    def __len__(self) -> int:
        return self.length
    
    def __hash__(self) -> int:
        return hash((self.src_register, self.offset, self.length))
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SpanDescriptor):
            return False
        return (
            self.src_register == other.src_register and
            self.offset == other.offset and
            self.length == other.length
        )


@dataclass
class TunnelConfig:
    """Configuration for express tunnel."""
    tunnel_id: int = 0
    tunnel_type: TunnelType = TunnelType.MEMORY
    max_bandwidth: int = 1000000000  # 1 GB/s default
    latency_budget: float = 0.001  # 1ms
    buffer_size: int = 65536  # 64KB
    priority: int = 0
    enabled: bool = True
    compression: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'tunnel_id': self.tunnel_id,
            'tunnel_type': self.tunnel_type.value,
            'max_bandwidth': self.max_bandwidth,
            'latency_budget': self.latency_budget,
            'buffer_size': self.buffer_size,
            'priority': self.priority,
            'enabled': self.enabled,
            'compression': self.compression
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TunnelConfig':
        """Create from dictionary."""
        return cls(
            tunnel_id=data.get('tunnel_id', 0),
            tunnel_type=TunnelType(data.get('tunnel_type', 'memory')),
            max_bandwidth=data.get('max_bandwidth', 1000000000),
            latency_budget=data.get('latency_budget', 0.001),
            buffer_size=data.get('buffer_size', 65536),
            priority=data.get('priority', 0),
            enabled=data.get('enabled', True),
            compression=data.get('compression', False)
        )


@dataclass
class TunnelStats:
    """Statistics for tunnel performance."""
    tunnel_id: int
    bytes_transferred: int = 0
    operations_count: int = 0
    avg_latency: float = 0.0
    peak_bandwidth: int = 0
    errors: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'tunnel_id': self.tunnel_id,
            'bytes_transferred': self.bytes_transferred,
            'operations_count': self.operations_count,
            'avg_latency': self.avg_latency,
            'peak_bandwidth': self.peak_bandwidth,
            'errors': self.errors,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': self.cache_hits / max(1, self.cache_hits + self.cache_misses)
        }


class ExpressTunnel:
    """
    Zero-Copy Express Tunnel for High-Performance Data Movement.
    
    Implements demand-driven, zero-copy memory access patterns
    with support for span-based operations and buffer reuse.
    """
    
    def __init__(
        self,
        tunnel_id: int = 0,
        tunnel_type: Any = TunnelType.MEMORY,
        config: Optional[TunnelConfig] = None,
        optimization_op: Optional[OptimizationOp] = None,
        **kwargs: Any
    ):
        """
        Initialize Express Tunnel.
        
        Args:
            tunnel_id: Unique tunnel identifier
            tunnel_type: Type of tunnel
            config: Optional configuration
            optimization_op: Optional initial optimization operation
        """
        if isinstance(tunnel_type, str):
            try:
                tunnel_type = TunnelType[tunnel_type.upper()]
            except KeyError:
                tunnel_type = TunnelType.MEMORY

        self.tunnel_id = tunnel_id
        self.tunnel_type = tunnel_type
        self.optimization_op = optimization_op
        self.config = config or TunnelConfig(tunnel_id=tunnel_id, tunnel_type=tunnel_type)
        
        # Internal state
        self._spans: Dict[SpanDescriptor, bytes] = {}
        self._buffers: Dict[int, bytes] = {}
        self._access_log: List[Tuple[int, int, float]] = []
        self._memory_map: Dict[int, int] = {}  # register -> address
        
        # Statistics
        self._stats = TunnelStats(tunnel_id=tunnel_id)
        
        logger.info(f"ExpressTunnel #{tunnel_id} initialized (type: {tunnel_type.value})")
    
    def set_mode(self, mode: Any) -> None:
        """Set tunnel mode/type."""
        if isinstance(mode, str):
            try:
                mode = TunnelType[mode.upper()]
            except KeyError:
                mode = TunnelType.MEMORY
        self.tunnel_type = mode
        self.config.tunnel_type = mode

    def close(self) -> None:
        """Close the tunnel."""
        self.config.enabled = False

    def create(self) -> 'ExpressTunnel':
        """Create and activate the tunnel."""
        self.config.enabled = True
        return self

    def create_stream(self, buffer_size: int = 4096) -> bytearray:
        """Create stream buffer."""
        buf = bytearray(buffer_size)
        self._buffers[len(self._buffers)] = bytes(buf)
        return buf

    def create_shared_buffer(self, size: int = 2048) -> bytearray:
        """Create shared buffer."""
        buf = bytearray(size)
        self._buffers[len(self._buffers)] = bytes(buf)
        return buf

    def create_direct_access(self, offset: int = 0, length: int = 512) -> memoryview:
        """Create direct access memoryview."""
        data = bytearray(offset + length)
        mv = memoryview(data)[offset:offset + length]
        return mv

    def enable_zero_copy(self) -> None:
        """Enable zero-copy optimization."""
        self.optimization_op = OptimizationOp.ZERO_COPY

    def enable_buffer_reuse(self) -> None:
        """Enable buffer reuse optimization."""
        self.optimization_op = OptimizationOp.BUFFER_REUSE

    def enable_stream_merge(self) -> None:
        """Enable stream merge optimization."""
        self.optimization_op = OptimizationOp.STREAM_MERGE

    def enable_memory_coalescing(self) -> None:
        """Enable memory coalescing optimization."""
        self.optimization_op = OptimizationOp.MEMORY_COALESCING

    def _validate_span(self, src_register: int, offset: int, length: int) -> bool:
        """Validate span parameters."""
        try:
            if src_register < 0 or src_register > 255:
                logger.error(f"Invalid register: {src_register}")
                return False
            
            if offset < 0:
                logger.error(f"Invalid offset: {offset}")
                return False
            
            if length <= 0:
                logger.error(f"Invalid length: {length}")
                return False
            
            # Check alignment
            if length % 8 != 0:
                logger.warning(f"Length not aligned to 8 bytes: {length}")
            
            return True
            
        except Exception as e:
            logger.error(f"Span validation failed: {e}")
            return False
    
    def create_span(
        self,
        src_register: int = 0,
        offset: int = 0,
        length: Optional[int] = None,
        alignment: int = 8,
        size: Optional[int] = None,
        **kwargs: Any
    ) -> Optional[SpanDescriptor]:
        """
        Create a zero-copy span descriptor.
        
        Args:
            src_register: Source register number (0-255)
            offset: Byte offset from register base
            length: Length in bytes
            alignment: Memory alignment requirement
            size: Alternative alias for length
            
        Returns:
            SpanDescriptor: Created span or None on failure
        """
        try:
            actual_length = size if size is not None else (length if length is not None else 1024)
            if not self._validate_span(src_register, offset, actual_length):
                return None
            
            # Calculate cache line
            cache_line = (offset + actual_length + 63) // 64
            
            span = SpanDescriptor(
                src_register=src_register,
                offset=offset,
                length=actual_length,
                alignment=alignment,
                cache_line=cache_line
            )
            
            self._spans[span] = b'\x00' * actual_length
            self._stats.operations_count += 1
            
            logger.debug(f"Created span: reg={src_register}, off={offset}, len={actual_length}")
            return span
            
        except Exception as e:
            logger.error(f"Failed to create span: {e}")
            return None
    
    def materialize_span(self, span: SpanDescriptor) -> Optional[bytes]:
        """
        Materialize span data into memory.
        
        Args:
            span: Span descriptor to materialize
            
        Returns:
            bytes: Materialized data or None on failure
        """
        try:
            if span not in self._spans:
                logger.warning(f"Span not found: {span}")
                return None
            
            # Simulate materialization (in real implementation, would access memory)
            data = self._spans[span]
            
            # Update statistics
            self._stats.bytes_transferred += len(data)
            self._stats.operations_count += 1
            
            # Log access
            self._access_log.append((
                span.src_register,
                span.offset,
                len(data)
            ))
            
            return data
            
        except Exception as e:
            logger.error(f"Materialize span failed: {e}")
            return None
    
    def pull_demand(
        self,
        src_register: int,
        offset: int,
        length: int
    ) -> Optional[SpanDescriptor]:
        """
        Pull data on-demand without explicit span creation.
        
        Args:
            src_register: Source register
            offset: Byte offset
            length: Length to pull
            
        Returns:
            SpanDescriptor: Created span for pulled data
        """
        try:
            if not self._validate_span(src_register, offset, length):
                return None
            
            span = self.create_span(src_register, offset, length)
            
            if span is None:
                return None
            
            # Pull operation (simulated)
            data = self.materialize_span(span)
            
            return span
            
        except Exception as e:
            logger.error(f"Pull demand failed: {e}")
            return None
    
    def merge_streams(
        self,
        spans: List[SpanDescriptor],
        target_register: int
    ) -> bool:
        """
        Merge multiple spans into a single stream.
        
        Args:
            spans: List of spans to merge
            target_register: Target register for merged stream
            
        Returns:
            bool: Success status
        """
        try:
            if len(spans) == 0:
                logger.warning("No spans to merge")
                return False
            
            # Validate all spans
            for span in spans:
                if span not in self._spans:
                    logger.warning(f"Span not found: {span}")
                    return False
            
            # Merge spans (simulated)
            merged_data = b''.join(self._spans[span] for span in spans)
            
            # Create merged span
            merged_span = SpanDescriptor(
                src_register=target_register,
                offset=0,
                length=len(merged_data),
                access_pattern="stream"
            )
            
            self._spans[merged_span] = merged_data
            self._stats.bytes_transferred += len(merged_data)
            self._stats.operations_count += 1
            
            logger.info(f"Merged {len(spans)} spans into target register {target_register}")
            return True
            
        except Exception as e:
            logger.error(f"Stream merge failed: {e}")
            return False
    
    def reuse_buffer(
        self,
        old_span: SpanDescriptor,
        new_span: SpanDescriptor
    ) -> bool:
        """
        Reuse buffer from old span for new span.
        
        Args:
            old_span: Source span for buffer reuse
            new_span: Target span to reuse buffer
            
        Returns:
            bool: Success status
        """
        try:
            if old_span not in self._spans:
                logger.warning(f"Old span not found: {old_span}")
                return False
            
            # Reuse buffer
            self._spans[new_span] = self._spans[old_span]
            
            # Clear old span
            del self._spans[old_span]
            
            self._stats.cache_hits += 1
            logger.debug(f"Buffer reused from {old_span} to {new_span}")
            return True
            
        except Exception as e:
            logger.error(f"Buffer reuse failed: {e}")
            return False
    
    def coalesce_memory(
        self,
        spans: List[SpanDescriptor]
    ) -> List[SpanDescriptor]:
        """
        Coalesce adjacent spans into larger contiguous blocks.
        
        Args:
            spans: List of spans to coalesce
            
        Returns:
            List[SpanDescriptor]: Coalesced spans
        """
        try:
            if len(spans) == 0:
                return []
            
            # Sort spans by offset
            sorted_spans = sorted(spans, key=lambda s: s.offset)
            
            coalesced = []
            current_span = sorted_spans[0]
            current_data = self._spans.get(current_span, b'')
            
            for span in sorted_spans[1:]:
                # Check if adjacent
                if span.offset == current_span.offset + len(current_span):
                    # Coalesce
                    current_data += self._spans.get(span, b'')
                    current_span.length = len(current_data)
                else:
                    # Save current and start new
                    coalesced.append(current_span)
                    current_span = span
                    current_data = self._spans.get(span, b'')
            
            coalesced.append(current_span)
            
            # Update internal storage
            for span in coalesced:
                self._spans[span] = self._spans.get(span, b'')
            
            self._stats.cache_hits += len(coalesced)
            logger.info(f"Coalesced {len(spans)} spans into {len(coalesced)} blocks")
            
            return coalesced
            
        except Exception as e:
            logger.error(f"Memory coalescing failed: {e}")
            return spans
    
    def get_stats(self) -> TunnelStats:
        """Get tunnel statistics."""
        return self._stats
    
    def reset_stats(self):
        """Reset tunnel statistics."""
        self._stats = TunnelStats(tunnel_id=self.tunnel_id)
        logger.info(f"Tunnel #{self.tunnel_id} stats reset")
    
    def is_enabled(self) -> bool:
        """Check if tunnel is enabled."""
        return self.config.enabled
    
    def set_enabled(self, enabled: bool):
        """Enable or disable tunnel."""
        self.config.enabled = enabled
        logger.info(f"Tunnel #{self.tunnel_id} {'enabled' if enabled else 'disabled'}")


@dataclass
class ManagerStats:
    """Statistics for express tunnel manager."""
    total_tunnels_created: int = 0
    active_tunnels: int = 0
    optimized_tunnels: int = 0

    def get_tunnel_count(self) -> int:
        return self.total_tunnels_created


class ExpressTunnelManager:
    """
    Manager for multiple express tunnels.
    
    Handles tunnel lifecycle, routing, and load balancing.
    """
    
    def __init__(self):
        """Initialize tunnel manager."""
        self._tunnels: Dict[int, ExpressTunnel] = {}
        self._next_id = 0
        self._total_created = 0
        self._optimized_tunnels: List[ExpressTunnel] = []
        self._routing_table: Dict[int, int] = {}  # register -> tunnel_id
        self._load_balancer: Dict[int, List[int]] = defaultdict(list)
        
        logger.info("ExpressTunnelManager initialized")
    
    def create_tunnel(
        self,
        tunnel_type_or_name: Any = TunnelType.MEMORY,
        config: Optional[TunnelConfig] = None,
        **kwargs: Any
    ) -> ExpressTunnel:
        """
        Create a new express tunnel.
        
        Args:
            tunnel_type_or_name: Type or name of tunnel
            config: Optional configuration
            
        Returns:
            ExpressTunnel: Created tunnel
        """
        try:
            actual_type = TunnelType.MEMORY
            tunnel_name = None
            if isinstance(tunnel_type_or_name, TunnelType):
                actual_type = tunnel_type_or_name
            elif isinstance(tunnel_type_or_name, str):
                try:
                    actual_type = TunnelType[tunnel_type_or_name.upper()]
                except KeyError:
                    tunnel_name = tunnel_type_or_name
                    actual_type = TunnelType.MEMORY
            
            tunnel = ExpressTunnel(
                tunnel_id=self._next_id,
                tunnel_type=actual_type,
                config=config,
                **kwargs
            )
            if tunnel_name:
                tunnel.name = tunnel_name
            
            self._tunnels[self._next_id] = tunnel
            self._next_id += 1
            self._total_created += 1
            
            logger.info(f"Created tunnel #{self._next_id - 1} (type: {actual_type.value})")
            return tunnel
            
        except Exception as e:
            logger.error(f"Failed to create tunnel: {e}")
            raise
    
    def add_tunnel(self, tunnel: ExpressTunnel) -> int:
        """Add an existing tunnel to manager."""
        tid = getattr(tunnel, 'tunnel_id', None)
        if tid is None:
            tid = len(self._tunnels)
        self._tunnels[tid] = tunnel
        return tid

    def get_tunnel(self, tunnel_id: int) -> Optional[ExpressTunnel]:
        """Get tunnel by ID."""
        return self._tunnels.get(tunnel_id)
    
    def get_tunnel_or_create(
        self,
        tunnel_id: int,
        tunnel_type: TunnelType = TunnelType.MEMORY
    ) -> ExpressTunnel:
        """Get existing tunnel or create new one."""
        if tunnel_id not in self._tunnels:
            return self.create_tunnel(tunnel_type_or_name=tunnel_type)
        return self._tunnels[tunnel_id]
    
    def route_register(self, register: int) -> int:
        """Route a register to appropriate tunnel."""
        if register in self._routing_table:
            return self._routing_table[register]
        
        # Find least loaded tunnel
        tunnel_id = self._find_least_loaded_tunnel()
        
        self._routing_table[register] = tunnel_id
        return tunnel_id
    
    def _find_least_loaded_tunnel(self) -> int:
        """Find tunnel with least load."""
        if not self._tunnels:
            return 0
        
        # Simple round-robin for now
        tunnel_ids = list(self._tunnels.keys())
        return tunnel_ids[0]
    
    def get_tunnels(self) -> List[ExpressTunnel]:
        """Get all tunnels."""
        return list(self._tunnels.values())

    def get_all_tunnels(self) -> List[ExpressTunnel]:
        """Get all tunnels."""
        return list(self._tunnels.values())
    
    def get_statistics(self) -> ManagerStats:
        """Get statistics for the tunnel manager."""
        active = sum(1 for t in self._tunnels.values() if t.config.enabled)
        return ManagerStats(
            total_tunnels_created=self._total_created,
            active_tunnels=active,
            optimized_tunnels=len(self._optimized_tunnels)
        )

    def enable_optimization(self) -> None:
        """Enable optimization across all managed tunnels."""
        self._optimized_tunnels = []
        for tunnel in self._tunnels.values():
            tunnel.enable_zero_copy()
            self._optimized_tunnels.append(tunnel)

    def get_optimized_tunnels(self) -> List[ExpressTunnel]:
        """Get all optimized tunnels."""
        return list(self._optimized_tunnels)

    def get_stats_summary(self) -> Dict[int, TunnelStats]:
        """Get statistics summary for all tunnels."""
        return {
            tunnel_id: tunnel.get_stats()
            for tunnel_id, tunnel in self._tunnels.items()
        }


def create_tunnel(
    tunnel_id: int = 0,
    tunnel_type: TunnelType = TunnelType.MEMORY
) -> ExpressTunnel:
    """
    Factory function to create an ExpressTunnel instance.
    
    Args:
        tunnel_id: Unique tunnel identifier
        tunnel_type: Type of tunnel
        
    Returns:
        ExpressTunnel: Created tunnel instance
    """
    return ExpressTunnel(tunnel_id=tunnel_id, tunnel_type=tunnel_type)


def create_tunnel_manager() -> ExpressTunnelManager:
    """
    Factory function to create an ExpressTunnelManager instance.
    
    Returns:
        ExpressTunnelManager: Manager instance
    """
    return ExpressTunnelManager()


if __name__ == "__main__":
    # Demo/test code
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("ExpressTunnel module loaded successfully")
    logger.info("Available tunnel types: MEMORY, STREAM, SHARED, DIRECT")
    logger.info("Available optimizations: ZERO_COPY, BUFFER_REUSE, STREAM_MERGE, MEMORY_COALESCING")
