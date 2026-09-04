"""
Verification Cache Module for Orthos Compiler
Provides caching and memoization for verification results
"""

import logging
import hashlib
import time
import threading
from typing import Dict, List, Set, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from collections import defaultdict

logger = logging.getLogger(__name__)


class VerificationStatus(Enum):
    """Status of verification results"""
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass
class VerificationKey:
    """Unique key for verification result"""
    code_hash: str
    filename: str
    version: int = 0
    
    def __hash__(self) -> int:
        return hash((self.code_hash, self.filename, self.version))
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VerificationKey):
            return False
        return (self.code_hash, self.filename, self.version) == \
               (other.code_hash, other.filename, other.version)
    
    def __str__(self) -> str:
        return f"VerificationKey({self.code_hash[:16]}...)"


@dataclass
class VerificationResult:
    """Result of a verification check"""
    key: VerificationKey
    status: VerificationStatus
    timestamp: float
    duration_ms: float
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    def is_valid(self) -> bool:
        """Check if verification passed"""
        return self.status == VerificationStatus.VERIFIED
    
    def is_invalid(self) -> bool:
        """Check if verification failed"""
        return self.status in (VerificationStatus.FAILED, 
                              VerificationStatus.TIMEOUT)


class VerificationCache:
    """Thread-safe cache for verification results"""
    
    def __init__(self, max_size: int = 10000, ttl_seconds: int = 3600):
        self._cache: Dict[VerificationKey, VerificationResult] = {}
        self._generic_store: Dict[str, Any] = {}
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._lock = threading.RLock()
        self._access_log: List[Tuple[VerificationKey, float]] = []
        self._logger = logging.getLogger(__name__)

    def store(self, key: str, value: Any) -> None:
        """Store key-value in cache"""
        with self._lock:
            self._generic_store[key] = value

    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve key-value from cache"""
        with self._lock:
            return self._generic_store.get(key)

    def hit(self, key: str) -> bool:
        """Check if key exists in cache"""
        with self._lock:
            return key in self._generic_store
    
    def get(self, code: str, filename: str = "<unknown>", 
            version: int = 0) -> Optional[VerificationResult]:
        """
        Get verification result from cache
        
        Args:
            code: Source code
            filename: Source filename
            version: Cache version
            
        Returns:
            VerificationResult or None if not found/expired
        """
        try:
            # Create key
            code_hash = hashlib.sha256(code.encode()).hexdigest()
            key = VerificationKey(
                code_hash=code_hash,
                filename=filename,
                version=version
            )
            
            with self._lock:
                # Check cache
                if key in self._cache:
                    result = self._cache[key]
                    
                    # Check TTL
                    if time.time() - result.timestamp < self._ttl:
                        # Log access
                        self._access_log.append((key, time.time()))
                        if len(self._access_log) > 10000:
                            self._access_log = self._access_log[-10000:]
                        
                        return result
                    
                    # Expired, remove from cache
                    del self._cache[key]
                
                return None
                
        except Exception as e:
            self._logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, code: str, filename: str = "<unknown>", 
            version: int = 0, result: VerificationResult = None) -> None:
        """
        Set verification result in cache
        
        Args:
            code: Source code
            filename: Source filename
            version: Cache version
            result: VerificationResult to cache
        """
        try:
            with self._lock:
                # Create key
                code_hash = hashlib.sha256(code.encode()).hexdigest()
                key = VerificationKey(
                    code_hash=code_hash,
                    filename=filename,
                    version=version
                )
                
                # Enforce max size
                if len(self._cache) >= self._max_size:
                    self._evict_oldest()
                
                # Store result
                self._cache[key] = result
                
                self._logger.debug(f"Cached verification: {key}")
                
        except Exception as e:
            self._logger.error(f"Cache set error: {e}")
            raise
    
    def invalidate(self, code: str, filename: str = "<unknown>") -> int:
        """
        Invalidate cache for specific code
        
        Args:
            code: Source code
            filename: Source filename
            
        Returns:
            Number of entries invalidated
        """
        try:
            code_hash = hashlib.sha256(code.encode()).hexdigest()
            count = 0
            
            with self._lock:
                keys_to_remove = [
                    k for k in self._cache.keys()
                    if k.code_hash == code_hash and k.filename == filename
                ]
                
                for key in keys_to_remove:
                    del self._cache[key]
                    count += 1
            
            self._logger.info(f"Invalidated {count} entries for {filename}")
            return count
            
        except Exception as e:
            self._logger.error(f"Invalidate error: {e}")
            return 0
    
    def invalidate_all(self) -> int:
        """
        Invalidate all cache entries
        
        Returns:
            Number of entries invalidated
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._logger.info(f"Cleared all {count} cache entries")
            return count
    
    def clear_expired(self) -> int:
        """
        Clear all expired entries
        
        Returns:
            Number of entries cleared
        """
        try:
            now = time.time()
            expired = []
            
            with self._lock:
                for key, result in self._cache.items():
                    if now - result.timestamp >= self._ttl:
                        expired.append(key)
                
                for key in expired:
                    del self._cache[key]
            
            self._logger.info(f"Cleared {len(expired)} expired entries")
            return len(expired)
            
        except Exception as e:
            self._logger.error(f"Clear expired error: {e}")
            return 0
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        with self._lock:
            now = time.time()
            
            # Count by status
            status_counts: Dict[VerificationStatus, int] = defaultdict(int)
            for result in self._cache.values():
                status_counts[result.status] += 1
            
            # Count expired
            expired_count = sum(
                1 for r in self._cache.values()
                if now - r.timestamp >= self._ttl
            )
            
            return {
                "total_entries": len(self._cache),
                "max_size": self._max_size,
                "utilization": len(self._cache) / self._max_size * 100,
                "status_counts": dict(status_counts),
                "expired_count": expired_count,
                "ttl_seconds": self._ttl
            }
    
    def _evict_oldest(self) -> None:
        """Evict oldest entries when cache is full"""
        if not self._cache:
            return
        
        # Find oldest entry
        oldest_key = None
        oldest_time = float('inf')
        
        for key, result in self._cache.items():
            if result.timestamp < oldest_time:
                oldest_time = result.timestamp
                oldest_key = key
        
        if oldest_key:
            del self._cache[oldest_key]
            self._logger.debug("Evicted oldest cache entry")


class VerificationMemoizer:
    """Decorator for memoizing verification functions"""
    
    def __init__(self, cache: VerificationCache = None):
        self._cache = cache or VerificationCache()
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Create cache key from arguments
            key_str = f"{func.__name__}:{args}:{kwargs}"
            code_hash = hashlib.sha256(key_str.encode()).hexdigest()
            
            # Try to get from cache
            cached = self._cache.get(
                code=code_hash,
                filename="<memoized>",
                version=0
            )
            
            if cached and cached.is_valid():
                return cached.details
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            verification_result = VerificationResult(
                key=VerificationKey(
                    code_hash=code_hash,
                    filename="<memoized>",
                    version=0
                ),
                status=VerificationStatus.VERIFIED if result else VerificationStatus.FAILED,
                timestamp=time.time(),
                duration_ms=0,
                details=result
            )
            
            self._cache.set(
                code=code_hash,
                filename="<memoized>",
                version=0,
                result=verification_result
            )
            
            return result
        
        return wrapper


class ScopeVerifier:
    """Verifies scope correctness"""
    
    def __init__(self, cache: VerificationCache = None):
        self._cache = cache or VerificationCache()
        self._logger = logging.getLogger(__name__)
    
    def verify(self, code: str, filename: str = "<unknown>") -> VerificationResult:
        """
        Verify scope correctness of code
        
        Args:
            code: Source code
            filename: Source filename
            
        Returns:
            VerificationResult
        """
        try:
            # Check cache
            cached = self._cache.get(code, filename)
            if cached:
                return cached
            
            # Perform verification
            import ast
            tree = ast.parse(code)
            
            # Check for undefined variables
            defined_vars: Set[str] = set()
            undefined_vars: List[str] = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    if isinstance(node.ctx, ast.Store):
                        defined_vars.add(node.id)
                    elif isinstance(node.ctx, ast.Load):
                        if node.id not in defined_vars:
                            undefined_vars.append(node.id)
            
            is_valid = len(undefined_vars) == 0
            
            result = VerificationResult(
                key=VerificationKey(
                    code_hash=hashlib.sha256(code.encode()).hexdigest(),
                    filename=filename,
                    version=0
                ),
                status=VerificationStatus.VERIFIED if is_valid else VerificationStatus.FAILED,
                timestamp=time.time(),
                duration_ms=0,
                details={
                    "defined_vars": len(defined_vars),
                    "undefined_vars": len(undefined_vars),
                    "undefined_list": undefined_vars[:10]  # Limit to 10
                },
                error=str(undefined_vars) if not is_valid else None
            )
            
            self._cache.set(code, filename, result)
            return result
            
        except Exception as e:
            self._logger.error(f"Scope verification error: {e}")
            return VerificationResult(
                key=VerificationKey(
                    code_hash=hashlib.sha256(code.encode()).hexdigest(),
                    filename=filename,
                    version=0
                ),
                status=VerificationStatus.FAILED,
                timestamp=time.time(),
                duration_ms=0,
                details={"error": str(e)}
            )
    
    def is_valid(self, code: str, filename: str = "<unknown>") -> bool:
        """Quick check if code is valid"""
        result = self.verify(code, filename)
        return result.is_valid()


class ComplexityVerifier:
    """Verifies complexity limits"""
    
    def __init__(self, cache: VerificationCache = None):
        self._cache = cache or VerificationCache()
        self._logger = logging.getLogger(__name__)
    
    def verify(self, code: str, filename: str = "<unknown>") -> VerificationResult:
        """
        Verify complexity limits
        
        Args:
            code: Source code
            filename: Source filename
            
        Returns:
            VerificationResult
        """
        try:
            # Check cache
            cached = self._cache.get(code, filename)
            if cached:
                return cached
            
            # Import complexity analyzer
            from orthos.compiler.analysis.complexity_gate import ComplexityAnalyzer
            
            analyzer = ComplexityAnalyzer()
            results = analyzer.analyze(code, filename)
            
            is_valid = results["within_limits"]
            
            result = VerificationResult(
                key=VerificationKey(
                    code_hash=hashlib.sha256(code.encode()).hexdigest(),
                    filename=filename,
                    version=0
                ),
                status=VerificationStatus.VERIFIED if is_valid else VerificationStatus.FAILED,
                timestamp=time.time(),
                duration_ms=0,
                details={
                    "cyclomatic": results["cyclomatic"]["value"],
                    "mccabe": results["mccabe"]["value"],
                    "violations": len(results["violations"])
                },
                error=str(results["violations"]) if not is_valid else None
            )
            
            self._cache.set(code, filename, result)
            return result
            
        except Exception as e:
            self._logger.error(f"Complexity verification error: {e}")
            return VerificationResult(
                key=VerificationKey(
                    code_hash=hashlib.sha256(code.encode()).hexdigest(),
                    filename=filename,
                    version=0
                ),
                status=VerificationStatus.FAILED,
                timestamp=time.time(),
                duration_ms=0,
                details={"error": str(e)}
            )
    
    def is_valid(self, code: str, filename: str = "<unknown>") -> bool:
        """Quick check if code is within complexity limits"""
        result = self.verify(code, filename)
        return result.is_valid()


# Singleton instances
_scope_verifier_instance: Optional[ScopeVerifier] = None
_complexity_verifier_instance: Optional[ComplexityVerifier] = None
_verification_cache_instance: Optional[VerificationCache] = None


def get_scope_verifier() -> ScopeVerifier:
    """Get or create scope verifier singleton"""
    global _scope_verifier_instance
    if _scope_verifier_instance is None:
        _scope_verifier_instance = ScopeVerifier()
    return _scope_verifier_instance


def get_complexity_verifier() -> ComplexityVerifier:
    """Get or create complexity verifier singleton"""
    global _complexity_verifier_instance
    if _complexity_verifier_instance is None:
        _complexity_verifier_instance = ComplexityVerifier()
    return _complexity_verifier_instance


def get_verification_cache() -> VerificationCache:
    """Get or create verification cache singleton"""
    global _verification_cache_instance
    if _verification_cache_instance is None:
        _verification_cache_instance = VerificationCache()
    return _verification_cache_instance


if __name__ == "__main__":
    # Test verification cache
    code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

result = factorial(10)
"""
    
    cache = VerificationCache(max_size=100, ttl_seconds=60)
    
    # Test get/set
    result = cache.get(code, "test.py")
    print(f"Initial cache lookup: {result}")
    
    # Set result
    verification_result = VerificationResult(
        key=VerificationKey(
            code_hash="abc123",
            filename="test.py",
            version=0
        ),
        status=VerificationStatus.VERIFIED,
        timestamp=time.time(),
        duration_ms=0,
        details={"valid": True}
    )
    cache.set(code, "test.py", verification_result)
    
    # Get again
    result = cache.get(code, "test.py")
    print(f"After set: {result.status if result else 'None'}")
    
    # Get stats
    stats = cache.get_stats()
    print(f"\nCache stats: {stats}")
    
    # Test scope verifier
    from orthos.compiler.analysis.verification_cache import get_scope_verifier
    
    verifier = get_scope_verifier()
    
    valid_code = """
x = 1
y = x + 1
"""
    invalid_code = """
result = undefined_variable + 1
"""
    
    print(f"\nValid code verification: {verifier.is_valid(valid_code)}")
    print(f"Invalid code verification: {verifier.is_valid(invalid_code)}")
    
    # Test complexity verifier
    from orthos.compiler.analysis.verification_cache import get_complexity_verifier
    
    complexity_verifier = get_complexity_verifier()
    
    simple_code = """
def add(a, b):
    return a + b
"""
    
    complex_code = """
def very_complex_function(a, b, c, d, e, f, g, h, i, j):
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        if f > 0:
                            if g > 0:
                                if h > 0:
                                    if i > 0:
                                        if j > 0:
                                            return a + b + c + d + e + f + g + h + i + j
                                        else:
                                            return 0
                                    else:
                                        return 0
                                else:
                                    return 0
                            else:
                                return 0
                        else:
                            return 0
                    else:
                        return 0
                else:
                    return 0
            else:
                return 0
        else:
            return 0
    else:
        return 0
"""
    
    print(f"\nSimple code complexity: {complexity_verifier.is_valid(simple_code)}")
    print(f"Complex code complexity: {complexity_verifier.is_valid(complex_code)}")
