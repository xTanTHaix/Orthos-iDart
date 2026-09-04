"""
Circuit Breaker for Orthos Safety System
Provides fail-safe mechanisms to prevent cascading failures
"""

import logging
import time
import threading
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """States of the circuit breaker"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovery possible


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5        # Number of failures before opening
    recovery_timeout: float = 30.0    # Seconds before trying again
    half_open_max_calls: int = 3      # Max calls in half-open state
    monitoring_window: float = 60.0   # Window for failure tracking


@dataclass
class CircuitBreakerEvent:
    """Event from circuit breaker"""
    event_type: str  # OPENED, CLOSED, HALF_OPENED
    timestamp: float
    state: CircuitState
    failure_count: int = 0


@dataclass
class CircuitStatus:
    """Current status of a circuit breaker"""
    state: CircuitState
    failure_count: int
    success_count: int
    last_failure_time: Optional[float]
    last_state_change: float
    total_calls: int
    failed_calls: int
    success_rate: float


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for fault tolerance.
    
    Prevents cascading failures by temporarily stopping requests
    when a service or operation is failing.
    """
    
    def __init__(self, 
                 name: str = "default",
                 config: CircuitBreakerConfig = None,
                 max_failures: Optional[int] = None):
        """
        Initialize circuit breaker.
        
        Args:
            name: Unique name for this circuit breaker
            config: Configuration options
            max_failures: Direct override for failure_threshold
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        if max_failures is not None:
            self.config.failure_threshold = max_failures
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._total_calls = 0
        self._failed_calls = 0
        self._last_failure_time: Optional[float] = None
        self._last_state_change = time.time()
        
        self._lock = threading.RLock()
        self._call_history: deque = deque(maxlen=1000)
        
        self._logger = logging.getLogger(__name__)
        self._callbacks: Dict[CircuitState, list] = {
            state: [] for state in CircuitState
        }
    
    def register_callback(self, state: CircuitState, callback: Callable) -> None:
        """
        Register callback for state changes.
        
        Args:
            state: State to monitor
            callback: Function to call when state changes
        """
        self._callbacks[state].append(callback)
        self._logger.debug(f"Registered callback for {state}")
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function through the circuit breaker.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitOpenError: If circuit is open
        """
        with self._lock:
            self._total_calls += 1
            
            if self._state == CircuitState.OPEN:
                if self._should_try_again():
                    self._transition_to(CircuitState.HALF_OPEN)
                else:
                    self._logger.error(f"Circuit {self.name} is OPEN")
                    raise CircuitOpenError(
                        f"Circuit {self.name} is open. "
                        f"Failures: {self._failure_count}, "
                        f"Timeout: {self.config.recovery_timeout}s"
                    )
        
        try:
            result = func(*args, **kwargs)
            
            with self._lock:
                self._success_count += 1
                self._failure_count = 0
                self._last_failure_time = None
                
                if self._state == CircuitState.HALF_OPEN:
                    if self._success_count >= self.config.half_open_max_calls:
                        self._transition_to(CircuitState.CLOSED)
            
            return result
            
        except Exception as e:
            with self._lock:
                self._failed_calls += 1
                self._failure_count += 1
                self._last_failure_time = time.time()
                
                if self._failure_count >= self.config.failure_threshold:
                    self._transition_to(CircuitState.OPEN)
            
            raise
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Alternative method name for execute.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
        """
        return self.execute(func, *args, **kwargs)
    
    def record_failure(self) -> None:
        """Record an operation failure and open the circuit if threshold exceeded."""
        with self._lock:
            self._failure_count += 1
            self._failed_calls += 1
            self._last_failure_time = time.time()
            if self._failure_count >= self.config.failure_threshold:
                self._state = CircuitState.OPEN
                self._last_state_change = time.time()

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed."""
        with self._lock:
            return self._state == CircuitState.CLOSED
    
    @property
    def is_open(self) -> bool:
        """Check if circuit is open."""
        with self._lock:
            return self._state == CircuitState.OPEN
    
    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open."""
        with self._lock:
            return self._state == CircuitState.HALF_OPEN
    
    def get_status(self) -> CircuitStatus:
        """Get current circuit status."""
        with self._lock:
            return CircuitStatus(
                state=self._state,
                failure_count=self._failure_count,
                success_count=self._success_count,
                last_failure_time=self._last_failure_time,
                last_state_change=self._last_state_change,
                total_calls=self._total_calls,
                failed_calls=self._failed_calls,
                success_rate=self._failed_calls / max(1, self._total_calls)
            )
    
    def reset(self) -> None:
        """Reset circuit breaker to initial state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._total_calls = 0
            self._failed_calls = 0
            self._last_failure_time = None
            self._last_state_change = time.time()
            
            self._logger.info(f"Circuit {self.name} reset")
    
    def force_open(self) -> None:
        """Force circuit to open state."""
        with self._lock:
            self._state = CircuitState.OPEN
            self._last_state_change = time.time()
            
            self._logger.warning(f"Circuit {self.name} forced open")
    
    def force_close(self) -> None:
        """Force circuit to closed state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
            self._last_state_change = time.time()
            
            self._logger.info(f"Circuit {self.name} forced closed")
    
    def _should_try_again(self) -> bool:
        """Check if we should try again after timeout."""
        if self._last_failure_time is None:
            return True
        
        elapsed = time.time() - self._last_failure_time
        return elapsed >= self.config.recovery_timeout
    
    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new state."""
        old_state = self._state
        
        if old_state != new_state:
            self._state = new_state
            self._last_state_change = time.time()
            
            # Call callbacks
            for callback in self._callbacks[new_state]:
                try:
                    callback(new_state, self)
                except Exception as e:
                    self._logger.error(f"Callback error: {e}")
            
            self._logger.info(
                f"Circuit {self.name}: {old_state.value} -> {new_state.value}"
            )
    
    def get_history(self) -> list:
        """Get call history."""
        with self._lock:
            return list(self._call_history)


class CircuitOpenError(Exception):
    """Exception raised when circuit is open."""
    pass


# Global circuit breakers registry
_circuit_breakers: Dict[str, CircuitBreaker] = {}
_lock = threading.Lock()


def get_circuit_breaker(name: str = "default") -> CircuitBreaker:
    """Get or create a circuit breaker by name."""
    global _circuit_breakers
    
    with _lock:
        if name not in _circuit_breakers:
            _circuit_breakers[name] = CircuitBreaker(name=name)
        return _circuit_breakers[name]


def create_circuit_breaker(name: str = "default",
                          config: CircuitBreakerConfig = None) -> CircuitBreaker:
    """Create a new circuit breaker."""
    return CircuitBreaker(name=name, config=config)


if __name__ == "__main__":
    # Test circuit breaker
    cb = CircuitBreaker(name="test_circuit")
    
    print("Initial state:", cb.get_status().state.value)
    
    # Register callback
    def on_state_change(state, breaker):
        print(f"State changed to: {state.value}")
    
    cb.register_callback(CircuitState.OPENED, on_state_change)
    cb.register_callback(CircuitState.CLOSED, on_state_change)
    
    # Simulate failures
    def failing_function():
        raise ValueError("Simulated failure")
    
    print("\nSimulating failures...")
    for i in range(7):
        try:
            cb.execute(failing_function)
        except Exception as e:
            print(f"  Attempt {i+1}: {type(e).__name__}: {e}")
    
    print("\nFinal state:", cb.get_status().state.value)
    
    # Reset
    cb.reset()
    print("After reset:", cb.get_status().state.value)
