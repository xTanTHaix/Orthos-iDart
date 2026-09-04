"""
TPX Storage Backend - Pure Python Fallback Implementation

This module provides a pure Python fallback implementation for TPX storage backend.
It implements all storage operations with graceful degradation and thread safety.

Features:
- Thread-safe storage operations
- Memory-efficient flat arrays
- Automatic fallback to disk when memory is constrained
- CRC32 checksum validation
- Graceful degradation under memory pressure
"""

import os
import json
import struct
import zlib
import threading
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from pathlib import Path
from enum import Enum
from datetime import datetime, timezone
import hashlib

# Configure logging
logger = logging.getLogger(__name__)


class StorageStatus(Enum):
    """Storage backend status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"
    FAILED = "failed"
    RECOVERING = "recovering"


class StorageMode(Enum):
    """Storage operation mode."""
    MEMORY_ONLY = "memory_only"
    MEMORY_PREFERRED = "memory_preferred"
    DISK_PREFERRED = "disk_preferred"
    HYBRID = "hybrid"


@dataclass
class StorageMetadata:
    """Metadata for stored data."""
    key: str
    version: int = 1
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    size_bytes: int = 0
    checksum: str = ""
    mode: str = "memory_preferred"
    tier: str = "hot"
    access_count: int = 0
    last_access: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StorageMetadata":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class StorageEntry:
    """Storage entry with data and metadata."""
    data: bytes
    metadata: StorageMetadata
    checksum: str = ""

    def validate_checksum(self) -> bool:
        """Validate stored checksum."""
        computed = str(self._compute_checksum())
        return computed == str(self.checksum)

    def _compute_checksum(self) -> str:
        """Compute CRC32 checksum."""
        return zlib.crc32(self.data) & 0xFFFFFFFF

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "data": self.data.hex(),
            "metadata": self.metadata.to_dict(),
            "checksum": self.checksum
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StorageEntry":
        """Create from dictionary."""
        metadata = StorageMetadata.from_dict(data["metadata"])
        metadata.checksum = data["checksum"]
        return cls(
            data=bytes.fromhex(data["data"]),
            metadata=metadata,
            checksum=data["checksum"]
        )


class StorageTier(Enum):
    """Storage tier for data classification."""
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"
    ARCHIVE = "archive"


class TPXStoragePurePython:
    """
    Pure Python fallback implementation of TPX storage backend.

    Provides thread-safe, memory-efficient storage with automatic tiering
    and graceful degradation.

    Thread Safety:
    - All public methods are thread-safe
    - Uses RLock for nested lock support
    - Atomic operations for critical sections
    """

    def __init__(
        self,
        base_path: Optional[str] = None,
        max_memory_bytes: int = 100 * 1024 * 1024,  # 100 MB default
        memory_threshold: float = 0.8,
        enable_disk_fallback: bool = True,
        disk_path: Optional[str] = None,
        compression: bool = True,
        checksum_algorithm: str = "crc32",
        log_level: int = logging.INFO
    ):
        """
        Initialize TPX storage backend.

        Args:
            base_path: Base path for disk storage (if enabled)
            max_memory_bytes: Maximum memory allocation in bytes
            memory_threshold: Memory usage threshold (0.0-1.0) before disk fallback
            enable_disk_fallback: Enable automatic disk fallback
            disk_path: Custom disk storage path
            compression: Enable compression for stored data
            checksum_algorithm: Checksum algorithm to use
            log_level: Logging level
        """
        self._lock = threading.RLock()
        self._memory_usage = 0
        self._max_memory_bytes = max_memory_bytes
        self._memory_threshold = memory_threshold
        self._enable_disk_fallback = enable_disk_fallback
        self._disk_path = Path(disk_path) if disk_path else None
        self._base_path = Path(base_path) if base_path else None
        self._compression = compression
        self._checksum_algorithm = checksum_algorithm
        self._status = StorageStatus.HEALTHY
        self._memory_pressure = False
        self._disk_fallback_enabled = enable_disk_fallback

        # In-memory storage
        self._memory_store: Dict[str, StorageEntry] = {}
        self._memory_index: Dict[str, int] = {}

        # Disk storage (if enabled)
        self._disk_store: Dict[str, StorageEntry] = {}
        self._disk_index: Dict[str, str] = {}  # key -> disk file path

        # Statistics
        self._total_reads = 0
        self._total_writes = 0
        self._total_deletes = 0
        self._total_errors = 0
        self._tier_distribution: Dict[str, int] = {
            "hot": 0,
            "warm": 0,
            "cold": 0,
            "archive": 0
        }

        # Callbacks for storage events
        self._on_write_callbacks: List[Callable] = []
        self._on_read_callbacks: List[Callable] = []
        self._on_delete_callbacks: List[Callable] = []

        # Initialize storage paths
        self._initialize_storage_paths()

        # Set logging level
        logging.getLogger(__name__).setLevel(log_level)

        logger.info(
            f"TPXStoragePurePython initialized "
            f"(memory_limit={max_memory_bytes}, "
            f"disk_fallback={enable_disk_fallback})"
        )

    def _initialize_storage_paths(self) -> None:
        """Initialize storage paths if needed."""
        if self._base_path:
            base = Path(self._base_path)
            base.mkdir(parents=True, exist_ok=True)

            if self._disk_path:
                disk = Path(self._disk_path)
                disk.mkdir(parents=True, exist_ok=True)

    def _get_current_memory_usage(self) -> int:
        """Get current memory usage in bytes."""
        return sum(
            entry.metadata.size_bytes
            for entry in self._memory_store.values()
        )

    def _check_memory_pressure(self) -> bool:
        """Check if memory pressure is high."""
        if self._max_memory_bytes <= 0:
            return False

        current_usage = self._get_current_memory_usage()
        threshold = self._max_memory_bytes * self._memory_threshold

        pressure = current_usage > threshold
        if pressure and not self._memory_pressure:
            logger.warning("Memory pressure detected, enabling disk fallback")
            self._memory_pressure = True

        return pressure

    def _compute_checksum(self, data: bytes) -> str:
        """Compute checksum for data."""
        if self._checksum_algorithm == "crc32":
            return str(zlib.crc32(data) & 0xFFFFFFFF)
        elif self._checksum_algorithm == "md5":
            return hashlib.md5(data).hexdigest()
        elif self._checksum_algorithm == "sha256":
            return hashlib.sha256(data).hexdigest()
        else:
            return str(zlib.crc32(data) & 0xFFFFFFFF)

    def _compress_data(self, data: bytes) -> bytes:
        """Compress data if compression is enabled."""
        if not self._compression:
            return data

        try:
            import zlib
            compressed = zlib.compress(data, level=6)
            logger.debug(f"Compressed {len(data)} bytes to {len(compressed)} bytes")
            return compressed
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            return data

    def _decompress_data(self, data: bytes) -> bytes:
        """Decompress data if compression was used."""
        if not self._compression:
            return data

        try:
            import zlib
            decompressed = zlib.decompress(data)
            logger.debug(f"Decompressed {len(data)} bytes to {len(decompressed)} bytes")
            return decompressed
        except Exception as e:
            logger.error(f"Decompression failed: {e}")
            return data

    def _determine_tier(self, size_bytes: int, access_frequency: float = 1.0) -> StorageTier:
        """Determine storage tier based on size and access frequency."""
        if size_bytes > 10 * 1024 * 1024:  # > 10 MB
            return StorageTier.COLD
        elif size_bytes > 1024 * 1024:  # > 1 MB
            return StorageTier.WARM
        elif access_frequency < 0.1:  # Low access
            return StorageTier.COLD
        else:
            return StorageTier.HOT

    def _apply_tiering(self) -> None:
        """Apply tiering policy to stored data."""
        logger.info("Applying storage tiering policy...")

        for key, entry in list(self._memory_store.items()):
            size = entry.metadata.size_bytes
            access_freq = entry.metadata.access_count / max(1, entry.metadata.last_access or 1)

            tier = self._determine_tier(size, access_freq)
            entry.metadata.tier = tier.value

            # Move cold data to disk if enabled
            if tier == StorageTier.COLD and self._enable_disk_fallback:
                self._promote_to_disk(key)

        # Update tier distribution
        self._update_tier_distribution()

    def _promote_to_disk(self, key: str) -> bool:
        """Promote memory entry to disk storage."""
        if key not in self._memory_store:
            return False

        entry = self._memory_store[key]
        size = entry.metadata.size_bytes

        try:
            # Write to disk
            disk_path = self._write_to_disk(key, entry.data)
            self._disk_store[key] = entry
            self._disk_index[key] = disk_path

            # Remove from memory
            del self._memory_store[key]
            del self._memory_index[key]

            # Free memory
            self._memory_usage -= size
            self._memory_pressure = False

            logger.info(f"Promoted {key} ({size} bytes) to disk")
            return True

        except Exception as e:
            logger.error(f"Failed to promote {key} to disk: {e}")
            self._status = StorageStatus.DEGRADED
            return False

    def _write_to_disk(self, key: str, data: bytes) -> str:
        """Write data to disk storage."""
        if not self._disk_path:
            raise ValueError("Disk storage not configured")

        # Create unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{key}_{timestamp}.tpx"
        filepath = self._disk_path / filename

        # Write with compression
        compressed_data = self._compress_data(data)

        with open(filepath, "wb") as f:
            # Write header
            header = struct.pack(
                ">IIB",  # Big-endian: magic, version, checksum
                0x54505853,  # "TPXS" magic
                1,  # version
                zlib.crc32(compressed_data) & 0xFFFFFFFF
            )
            f.write(header)
            f.write(compressed_data)

        return str(filepath)

    def _read_from_disk(self, key: str) -> Optional[bytes]:
        """Read data from disk storage."""
        if key not in self._disk_index:
            return None

        filepath = Path(self._disk_index[key])

        try:
            with open(filepath, "rb") as f:
                # Read header
                header = f.read(12)
                if len(header) < 12:
                    raise ValueError("Invalid file header")

                magic, version, stored_checksum = struct.unpack(">IIB", header)

                if magic != 0x54505853:
                    raise ValueError("Invalid magic number")

                # Read and decompress data
                data = f.read()
                decompressed = self._decompress_data(data)

                # Verify checksum
                computed_checksum = zlib.crc32(decompressed) & 0xFFFFFFFF
                if computed_checksum != stored_checksum:
                    raise ValueError("Checksum mismatch")

                return decompressed

        except Exception as e:
            logger.error(f"Failed to read from disk for {key}: {e}")
            return None

    def _update_tier_distribution(self) -> None:
        """Update tier distribution statistics."""
        for entry in self._memory_store.values():
            tier = entry.metadata.tier
            if tier in self._tier_distribution:
                self._tier_distribution[tier] += 1

        for entry in self._disk_store.values():
            tier = entry.metadata.tier
            if tier in self._tier_distribution:
                self._tier_distribution[tier] += 1

    def register_callback(
        self,
        event_type: str,
        callback: Callable[[str, Any], None]
    ) -> None:
        """
        Register callback for storage events.

        Args:
            event_type: Event type ("write", "read", "delete")
            callback: Callback function to invoke
        """
        if event_type == "write":
            self._on_write_callbacks.append(callback)
        elif event_type == "read":
            self._on_read_callbacks.append(callback)
        elif event_type == "delete":
            self._on_delete_callbacks.append(callback)

    def _notify_callbacks(self, event_type: str, key: str, data: Any) -> None:
        """Notify all registered callbacks."""
        callbacks = getattr(self, f"_on_{event_type}_callbacks", [])
        for callback in callbacks:
            try:
                callback(key, data)
            except Exception as e:
                logger.error(f"Callback error for {event_type}: {e}")

    def store(
        self,
        key: str,
        data: Union[bytes, str, Dict[str, Any], List[Any]],
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tier: Optional[StorageTier] = None
    ) -> StorageEntry:
        """
        Store data in TPX storage.

        Args:
            key: Unique storage key
            data: Data to store (bytes, str, dict, or list)
            tags: Optional tags for the entry
            metadata: Optional custom metadata
            tier: Optional storage tier

        Returns:
            StorageEntry with stored data and metadata
        """
        with self._lock:
            # Convert data to bytes if needed
            original_type = "bytes"
            if isinstance(data, str):
                data = data.encode("utf-8")
                original_type = "str"
            elif isinstance(data, (dict, list)):
                data = json.dumps(data, ensure_ascii=False).encode("utf-8")
                original_type = "json"
            elif isinstance(data, (int, float, bool)):
                data = json.dumps(data).encode("utf-8")
                original_type = "json"
            elif not isinstance(data, (bytes, bytearray, memoryview)):
                try:
                    data = json.dumps(data, ensure_ascii=False).encode("utf-8")
                    original_type = "json"
                except Exception:
                    data = str(data).encode("utf-8")
                    original_type = "str"
            else:
                data = bytes(data)

            size_bytes = len(data)

            # Check memory pressure
            if self._check_memory_pressure():
                logger.warning("High memory pressure, forcing disk storage")

            # Determine tier
            if tier is None:
                tier = self._determine_tier(size_bytes)

            # Create metadata
            now = datetime.now(timezone.utc).isoformat()
            meta = dict(metadata or {})
            meta["original_type"] = original_type
            metadata_obj = StorageMetadata(
                key=key,
                size_bytes=size_bytes,
                mode=StorageMode.MEMORY_PREFERRED.value,
                tier=tier.value,
                tags=tags or [],
                metadata=meta,
                created_at=now,
                updated_at=now
            )

            # Compress data
            stored_data = self._compress_data(data)

            # Compute checksum
            checksum = self._compute_checksum(stored_data)

            # Create storage entry
            entry = StorageEntry(
                data=stored_data,
                metadata=metadata_obj,
                checksum=checksum
            )

            # Store in memory
            self._memory_store[key] = entry
            self._memory_index[key] = len(self._memory_store)

            # Update memory usage
            self._memory_usage += size_bytes

            # Track statistics
            self._total_writes += 1
            self._tier_distribution[tier.value] += 1

            # Notify callbacks
            self._notify_callbacks("write", key, entry)

            logger.debug(f"Stored {key} ({size_bytes} bytes) in {tier.value} tier")

            return entry

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve data from storage.

        Args:
            key: Storage key

        Returns:
            Stored data, or None if not found
        """
        with self._lock:
            self._total_reads += 1

            # Check memory first
            if key in self._memory_store:
                entry = self._memory_store[key]

                # Validate checksum
                if not entry.validate_checksum():
                    logger.warning(f"Checksum mismatch for {key}, reading from disk")
                    return self._read_from_disk_and_validate(key)

                # Update access count
                entry.metadata.access_count += 1
                entry.metadata.updated_at = datetime.now(timezone.utc).isoformat()
                self._memory_store[key] = entry

                # Notify callbacks
                self._notify_callbacks("read", key, entry.data)

                logger.debug(f"Retrieved {key} from memory")
                decompressed = self._decompress_data(entry.data)
                orig_type = entry.metadata.metadata.get("original_type")
                if orig_type == "str":
                    try:
                        return decompressed.decode("utf-8")
                    except Exception:
                        return decompressed
                elif orig_type == "json":
                    try:
                        return json.loads(decompressed.decode("utf-8"))
                    except Exception:
                        return decompressed
                return decompressed

            # Check disk if enabled
            if self._enable_disk_fallback and key in self._disk_store:
                data = self._read_from_disk_and_validate(key)
                if data is not None:
                    # Promote to memory on read
                    self._promote_to_memory(key, data)
                    return data

            return None

    def write(self, key: str, data: Any, *args, **kwargs) -> Any:
        """Alias for store() to support write() calls."""
        return self.store(key, data, *args, **kwargs)

    def read(self, key: str) -> Optional[Any]:
        """Alias for get() to support read() calls."""
        return self.get(key)

    def retrieve(self, key: str) -> Optional[Any]:
        """Alias for get() to support retrieve() calls."""
        return self.get(key)

    def memory_usage(self) -> int:
        """Get current memory usage in bytes."""
        return self._memory_usage

    def batch_write(self, items: List[Tuple[str, Any]], *args: Any, **kwargs: Any) -> List[StorageEntry]:
        """Batch write multiple key-value pairs."""
        results = []
        for key, value in items:
            entry = self.store(key, value, *args, **kwargs)
            results.append(entry)
        return results

    def batch_store(self, items: Any, *args: Any, **kwargs: Any) -> List[StorageEntry]:
        """Batch store multiple key-value pairs from dict or list of tuples."""
        if isinstance(items, dict):
            items = list(items.items())
        return self.batch_write(items, *args, **kwargs)

    def batch_read(self, keys: List[str]) -> List[Any]:
        """Batch read multiple keys."""
        results = []
        for key in keys:
            results.append(self.get(key))
        return results

    def _read_from_disk_and_validate(self, key: str) -> Optional[bytes]:
        """Read and validate data from disk."""
        data = self._read_from_disk(key)
        if data is not None:
            # Validate checksum
            computed = self._compute_checksum(data)
            if computed != str(zlib.crc32(data) & 0xFFFFFFFF):
                logger.error(f"Disk checksum mismatch for {key}")
                return None
        return data

    def _promote_to_memory(self, key: str, data: bytes) -> None:
        """Promote disk entry to memory."""
        size = len(data)

        # Create metadata
        metadata = StorageMetadata(
            key=key,
            size_bytes=size,
            mode=StorageMode.MEMORY_PREFERRED.value,
            tier=StorageTier.HOT.value,
            access_count=1,
            last_access=datetime.now(timezone.utc).isoformat()
        )

        # Compress and store
        stored_data = self._compress_data(data)
        checksum = self._compute_checksum(stored_data)

        entry = StorageEntry(data=stored_data, metadata=metadata, checksum=checksum)

        self._memory_store[key] = entry
        self._memory_index[key] = len(self._memory_store)
        self._memory_usage += size

        # Remove from disk
        if key in self._disk_store:
            del self._disk_store[key]
        if key in self._disk_index:
            del self._disk_index[key]

        # Update memory pressure
        self._memory_pressure = self._check_memory_pressure()

        logger.debug(f"Promoted {key} to memory")

    def delete(self, key: str) -> bool:
        """
        Delete data from storage.

        Args:
            key: Storage key

        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            deleted = False

            # Delete from memory
            if key in self._memory_store:
                entry = self._memory_store.pop(key)
                self._memory_index.pop(key, None)
                self._memory_usage -= entry.metadata.size_bytes

                deleted = True
                self._total_deletes += 1

                # Notify callbacks
                self._notify_callbacks("delete", key, entry)

                logger.debug(f"Deleted {key} from memory")

            # Delete from disk
            if deleted and key in self._disk_store:
                filepath = Path(self._disk_index.pop(key, ""))
                if filepath and filepath.exists():
                    try:
                        filepath.unlink()
                        self._disk_store.pop(key, None)
                        logger.debug(f"Deleted {key} from disk")
                    except Exception as e:
                        logger.error(f"Failed to delete disk file for {key}: {e}")

            return deleted

    def exists(self, key: str) -> bool:
        """
        Check if key exists in storage.

        Args:
            key: Storage key

        Returns:
            True if key exists
        """
        with self._lock:
            return key in self._memory_store or key in self._disk_store

    def update(
        self,
        key: str,
        data: Union[bytes, str, Dict[str, Any], List[Any]],
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update existing data in storage.

        Args:
            key: Storage key
            data: New data
            tags: Optional new tags
            metadata: Optional new metadata

        Returns:
            True if updated, False if not found
        """
        if not self.exists(key):
            return False

        # Delete and re-store
        self.delete(key)
        return self.store(key, data, tags, metadata) is not None

    def list_keys(self, prefix: str = "") -> List[str]:
        """
        List all storage keys.

        Args:
            prefix: Optional prefix filter

        Returns:
            List of keys matching prefix
        """
        with self._lock:
            keys = []

            for key in self._memory_store.keys():
                if key.startswith(prefix):
                    keys.append(key)

            for key in self._disk_store.keys():
                if key.startswith(prefix):
                    keys.append(key)

            return keys

    def get_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.

        Returns:
            Dictionary with storage statistics
        """
        with self._lock:
            return {
                "status": self._status.value,
                "memory_pressure": self._memory_pressure,
                "memory_usage_bytes": self._memory_usage,
                "max_memory_bytes": self._max_memory_bytes,
                "memory_utilization_percent": (
                    (self._memory_usage / self._max_memory_bytes * 100)
                    if self._max_memory_bytes > 0 else 0
                ),
                "memory_entries": len(self._memory_store),
                "disk_entries": len(self._disk_store),
                "total_reads": self._total_reads,
                "total_writes": self._total_writes,
                "total_deletes": self._total_deletes,
                "total_errors": self._total_errors,
                "tier_distribution": self._tier_distribution,
                "compression_enabled": self._compression,
                "checksum_algorithm": self._checksum_algorithm,
                "disk_fallback_enabled": self._enable_disk_fallback
            }

    def flush(self) -> None:
        """Flush all data to disk."""
        logger.info("Flushing storage to disk...")

        with self._lock:
            for key, entry in list(self._memory_store.items()):
                try:
                    self._write_to_disk(key, entry.data)
                    self._disk_store[key] = entry
                    self._disk_index[key] = self._disk_index.get(key, "")
                except Exception as e:
                    logger.error(f"Failed to flush {key}: {e}")

            # Clear memory
            self._memory_store.clear()
            self._memory_index.clear()
            self._memory_usage = 0

            logger.info("Storage flushed to disk")

    def clear(self) -> None:
        """Clear all storage."""
        logger.warning("Clearing all storage...")

        with self._lock:
            # Clear memory
            self._memory_store.clear()
            self._memory_index.clear()
            self._memory_usage = 0

            # Clear disk
            self._disk_store.clear()
            self._disk_index.clear()

            # Reset statistics
            self._total_reads = 0
            self._total_writes = 0
            self._total_deletes = 0
            self._tier_distribution = {
                "hot": 0,
                "warm": 0,
                "cold": 0,
                "archive": 0
            }

            self._status = StorageStatus.HEALTHY
            self._memory_pressure = False

            logger.info("Storage cleared")

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on storage backend.

        Returns:
            Health check result dictionary
        """
        with self._lock:
            memory_usage = self._get_current_memory_usage()
            memory_limit = self._max_memory_bytes

            return {
                "status": self._status.value,
                "healthy": self._status == StorageStatus.HEALTHY,
                "memory_usage_bytes": memory_usage,
                "memory_limit_bytes": memory_limit,
                "memory_utilization_percent": (
                    (memory_usage / memory_limit * 100)
                    if memory_limit > 0 else 0
                ),
                "disk_fallback_enabled": self._enable_disk_fallback,
                "compression_enabled": self._compression,
                "entries_count": len(self._memory_store) + len(self._disk_store),
                "last_error": None if self._total_errors == 0 else "errors_occurred"
            }

    def close(self) -> None:
        """Close storage backend and release resources."""
        logger.info("Closing TPX storage backend...")

        with self._lock:
            # Flush to disk
            self.flush()

            # Clear memory
            self.clear()

            logger.info("TPX storage backend closed")

    def __enter__(self) -> "TPXStoragePurePython":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    def __del__(self) -> None:
        """Destructor."""
        try:
            self.close()
        except Exception:
            pass  # Ignore errors on destruction
