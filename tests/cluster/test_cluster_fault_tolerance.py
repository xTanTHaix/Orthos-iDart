"""
Cluster Fault Tolerance Test Suite - Tests for fault tolerance and recovery

Tests cover:
- Node failure detection
- Automatic failover
- Task redistribution
- State recovery
- Graceful degradation
"""

import pytest
import time
import threading
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class NodeFailureType(Enum):
    """Types of node failures."""
    CRASH = "crash"
    NETWORK_PARTITION = "network_partition"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    MAINTENANCE = "maintenance"


@dataclass
class FailureEvent:
    """Represents a failure event."""
    node_id: str
    failure_type: NodeFailureType
    detected_at: float = field(default_factory=time.time)
    recovered_at: Optional[float] = None
    recovery_time: float = 0.0


class FailureDetector:
    """Detects node failures."""
    
    def __init__(self, heartbeat_timeout: float = 5.0):
        self.heartbeat_timeout = heartbeat_timeout
        self._last_heartbeat: Dict[str, float] = {}
        self._detected_failures: Dict[str, FailureEvent] = {}
        self._lock = threading.RLock()
    
    def record_heartbeat(self, node_id: str) -> None:
        """Record heartbeat from node."""
        with self._lock:
            self._last_heartbeat[node_id] = time.time()
    
    def detect_failure(self, node_id: str, failure_type: NodeFailureType = NodeFailureType.CRASH) -> Optional[FailureEvent]:
        """Detect failure for node."""
        with self._lock:
            if node_id not in self._last_heartbeat:
                return None
            
            last_heartbeat = self._last_heartbeat[node_id]
            if time.time() - last_heartbeat > self.heartbeat_timeout:
                failure = FailureEvent(
                    node_id=node_id,
                    failure_type=failure_type,
                    detected_at=time.time()
                )
                self._detected_failures[node_id] = failure
                return failure
            
            return None
    
    def get_failure(self, node_id: str) -> Optional[FailureEvent]:
        """Get failure event for node."""
        with self._lock:
            return self._detected_failures.get(node_id)
    
    def clear_failure(self, node_id: str) -> bool:
        """Clear failure event for node."""
        with self._lock:
            if node_id in self._detected_failures:
                failure = self._detected_failures[node_id]
                failure.recovered_at = time.time()
                failure.recovery_time = failure.recovered_at - failure.detected_at
                del self._detected_failures[node_id]
                return True
            return False
    
    def get_all_failures(self) -> List[FailureEvent]:
        """Get all detected failures."""
        with self._lock:
            return list(self._detected_failures.values())
    
    def is_node_failed(self, node_id: str) -> bool:
        """Check if node has failed."""
        with self._lock:
            return node_id in self._detected_failures


class FailoverManager:
    """Manages failover operations."""
    
    def __init__(self):
        self._active_nodes: Dict[str, bool] = {}
        self._standby_nodes: Dict[str, bool] = {}
        self._lock = threading.RLock()
    
    def register_active_node(self, node_id: str) -> None:
        """Register active node."""
        with self._lock:
            self._active_nodes[node_id] = True
    
    def register_standby_node(self, node_id: str) -> None:
        """Register standby node."""
        with self._lock:
            self._standby_nodes[node_id] = True
    
    def promote_standby(self, standby_id: str) -> Optional[str]:
        """Promote standby node to active."""
        with self._lock:
            if standby_id not in self._standby_nodes:
                return None
            
            self._active_nodes[standby_id] = True
            del self._standby_nodes[standby_id]
            
            return standby_id
    
    def demote_active(self, node_id: str) -> bool:
        """Demote active node."""
        with self._lock:
            if node_id not in self._active_nodes:
                return False
            
            self._active_nodes[node_id] = False
            return True
    
    def get_active_nodes(self) -> List[str]:
        """Get all active nodes."""
        with self._lock:
            return [
                node_id for node_id, active in self._active_nodes.items()
                if active
            ]
    
    def get_standby_nodes(self) -> List[str]:
        """Get all standby nodes."""
        with self._lock:
            return [
                node_id for node_id, standby in self._standby_nodes.items()
                if standby
            ]
    
    def get_available_standby(self) -> Optional[str]:
        """Get available standby node."""
        with self._lock:
            standby_nodes = list(self._standby_nodes.keys())
            if standby_nodes:
                return standby_nodes[0]
            return None


class TaskRedistributor:
    """Redistributes tasks when nodes fail."""
    
    def __init__(self):
        self._node_tasks: Dict[str, List[str]] = defaultdict(list)
        self._lock = threading.RLock()
    
    def assign_task_to_node(self, task_id: str, node_id: str) -> None:
        """Assign task to node."""
        with self._lock:
            self._node_tasks[node_id].append(task_id)
    
    def get_node_tasks(self, node_id: str) -> List[str]:
        """Get all tasks assigned to node."""
        with self._lock:
            return list(self._node_tasks.get(node_id, []))
    
    def redistribute_tasks(self, failed_node: str, available_nodes: List[str]) -> Dict[str, List[str]]:
        """Redistribute tasks from failed node to available nodes."""
        with self._lock:
            failed_tasks = self._node_tasks.pop(failed_node, [])
            
            if not failed_tasks or not available_nodes:
                return {}
            
            # Distribute evenly
            tasks_per_node = len(failed_tasks) // len(available_nodes)
            remaining = len(failed_tasks) % len(available_nodes)
            
            redistributed: Dict[str, List[str]] = {}
            task_index = 0
            
            for node_id in available_nodes:
                tasks = failed_tasks[task_index:task_index + tasks_per_node + (1 if task_index < remaining else 0)]
                redistributed[node_id] = tasks
                
                for task_id in tasks:
                    self._node_tasks[node_id].append(task_id)
                
                task_index += tasks_per_node + (1 if task_index < remaining else 0)
            
            return redistributed
    
    def get_total_tasks(self) -> int:
        """Get total number of tasks."""
        with self._lock:
            return sum(len(tasks) for tasks in self._node_tasks.values())


class StateRecoveryManager:
    """Manages state recovery after failures."""
    
    def __init__(self):
        self._node_states: Dict[str, Dict] = {}
        self._checkpoint_interval: float = 10.0
        self._lock = threading.RLock()
    
    def save_state(self, node_id: str, state: Dict) -> None:
        """Save node state."""
        with self._lock:
            self._node_states[node_id] = state.copy()
    
    def get_state(self, node_id: str) -> Optional[Dict]:
        """Get saved state for node."""
        with self._lock:
            return self._node_states.get(node_id).copy()
    
    def clear_state(self, node_id: str) -> bool:
        """Clear saved state for node."""
        with self._lock:
            if node_id in self._node_states:
                del self._node_states[node_id]
                return True
            return False
    
    def recover_state(self, node_id: str) -> Optional[Dict]:
        """Recover state for node."""
        with self._lock:
            if node_id in self._node_states:
                state = self._node_states[node_id].copy()
                del self._node_states[node_id]
                return state
            return None


class TestFailureDetector:
    """Test failure detection operations."""
    
    def test_heartbeat_recording(self):
        """Test heartbeat recording."""
        detector = FailureDetector(heartbeat_timeout=5.0)
        
        detector.record_heartbeat("node-1")
        
        assert "node-1" in detector._last_heartbeat
    
    def test_failure_detection(self):
        """Test failure detection after timeout."""
        detector = FailureDetector(heartbeat_timeout=0.1)  # Short timeout for test
        
        detector.record_heartbeat("node-1")
        
        # Wait for timeout
        time.sleep(0.15)
        
        failure = detector.detect_failure("node-1")
        
        assert failure is not None
        assert failure.node_id == "node-1"
        assert failure.failure_type == NodeFailureType.CRASH
    
    def test_no_failure_before_timeout(self):
        """Test no failure detected before timeout."""
        detector = FailureDetector(heartbeat_timeout=5.0)
        
        detector.record_heartbeat("node-1")
        
        failure = detector.detect_failure("node-1")
        
        assert failure is None
    
    def test_failure_clearing(self):
        """Test failure clearing."""
        detector = FailureDetector(heartbeat_timeout=0.1)
        
        detector.record_heartbeat("node-1")
        time.sleep(0.15)
        detector.detect_failure("node-1")
        
        assert detector.is_node_failed("node-1")
        
        detector.clear_failure("node-1")
        
        assert not detector.is_node_failed("node-1")
    
    def test_multiple_failures(self):
        """Test detection of multiple failures."""
        detector = FailureDetector(heartbeat_timeout=0.1)
        
        for i in range(3):
            detector.record_heartbeat(f"node-{i}")
            time.sleep(0.15)
            detector.detect_failure(f"node-{i}")
        
        failures = detector.get_all_failures()
        
        assert len(failures) == 3


class TestFailoverManager:
    """Test failover management operations."""
    
    def test_register_nodes(self):
        """Test node registration."""
        manager = FailoverManager()
        
        manager.register_active_node("node-1")
        manager.register_standby_node("node-2")
        
        assert "node-1" in manager.get_active_nodes()
        assert "node-2" in manager.get_standby_nodes()
    
    def test_promote_standby(self):
        """Test standby promotion to active."""
        manager = FailoverManager()
        
        manager.register_active_node("node-1")
        manager.register_standby_node("node-2")
        
        promoted = manager.promote_standby("node-2")
        
        assert promoted == "node-2"
        assert "node-2" in manager.get_active_nodes()
        assert "node-2" not in manager.get_standby_nodes()
    
    def test_demote_active(self):
        """Test active node demotion."""
        manager = FailoverManager()
        
        manager.register_active_node("node-1")
        
        result = manager.demote_active("node-1")
        
        assert result is True
        assert "node-1" not in manager.get_active_nodes()
    
    def test_promote_no_standby(self):
        """Test promotion with no standby returns None."""
        manager = FailoverManager()
        
        manager.register_active_node("node-1")
        
        result = manager.promote_standby("nonexistent")
        
        assert result is None
    
    def test_multiple_standby_promotion(self):
        """Test multiple standby promotions."""
        manager = FailoverManager()
        
        manager.register_active_node("node-1")
        manager.register_standby_node("node-2")
        manager.register_standby_node("node-3")
        
        promoted1 = manager.promote_standby("node-2")
        promoted2 = manager.promote_standby("node-3")
        
        assert promoted1 == "node-2"
        assert promoted2 == "node-3"
        assert len(manager.get_active_nodes()) == 3


class TestTaskRedistribution:
    """Test task redistribution operations."""
    
    def test_task_assignment(self):
        """Test task assignment to node."""
        distributor = TaskRedistributor()
        
        distributor.assign_task_to_node("task-1", "node-1")
        distributor.assign_task_to_node("task-2", "node-1")
        
        tasks = distributor.get_node_tasks("node-1")
        
        assert len(tasks) == 2
        assert "task-1" in tasks
        assert "task-2" in tasks
    
    def test_redistribution(self):
        """Test task redistribution."""
        distributor = TaskRedistributor()
        
        # Assign tasks to node that will fail
        for i in range(5):
            distributor.assign_task_to_node(f"task-{i}", "failed-node")
        
        # Redistribute to available nodes
        available = ["node-1", "node-2", "node-3"]
        redistributed = distributor.redistribute_tasks("failed-node", available)
        
        assert len(redistributed) == 3
        
        # Each node should have ~2 tasks
        for node_id, tasks in redistributed.items():
            assert len(tasks) >= 1
    
    def test_redistribution_no_available_nodes(self):
        """Test redistribution with no available nodes."""
        distributor = TaskRedistributor()
        
        distributor.assign_task_to_node("task-1", "failed-node")
        
        result = distributor.redistribute_tasks("failed-node", [])
        
        assert result == {}
    
    def test_redistribution_no_failed_tasks(self):
        """Test redistribution with no failed tasks."""
        distributor = TaskRedistributor()
        
        result = distributor.redistribute_tasks("nonexistent", ["node-1"])
        
        assert result == {}
    
    def test_total_task_count(self):
        """Test total task count tracking."""
        distributor = TaskRedistributor()
        
        for i in range(10):
            distributor.assign_task_to_node(f"task-{i}", f"node-{i % 3}")
        
        total = distributor.get_total_tasks()
        
        assert total == 10


class TestStateRecovery:
    """Test state recovery operations."""
    
    def test_state_saving(self):
        """Test state saving."""
        manager = StateRecoveryManager()
        
        state = {"key1": "value1", "key2": 42}
        manager.save_state("node-1", state)
        
        assert "node-1" in manager._node_states
    
    def test_state_retrieval(self):
        """Test state retrieval."""
        manager = StateRecoveryManager()
        
        state = {"data": "test"}
        manager.save_state("node-1", state)
        
        retrieved = manager.get_state("node-1")
        
        assert retrieved is not None
        assert retrieved["data"] == "test"
    
    def test_state_clearing(self):
        """Test state clearing."""
        manager = StateRecoveryManager()
        
        manager.save_state("node-1", {"data": "test"})
        
        result = manager.clear_state("node-1")
        
        assert result is True
        assert "node-1" not in manager._node_states
    
    def test_clear_nonexistent_state(self):
        """Test clearing nonexistent state."""
        manager = StateRecoveryManager()
        
        result = manager.clear_state("nonexistent")
        
        assert result is False
    
    def test_state_recovery(self):
        """Test state recovery."""
        manager = StateRecoveryManager()
        
        state = {"recovered": True}
        manager.save_state("node-1", state)
        
        recovered = manager.recover_state("node-1")
        
        assert recovered is not None
        assert recovered["recovered"] is True
        assert "node-1" not in manager._node_states  # State cleared after recovery
    
    def test_recovery_nonexistent_state(self):
        """Test recovery of nonexistent state."""
        manager = StateRecoveryManager()
        
        result = manager.recover_state("nonexistent")
        
        assert result is None


class TestFaultToleranceIntegration:
    """Test integration of fault tolerance components."""
    
    def test_full_failure_recovery(self):
        """Test complete failure and recovery scenario."""
        detector = FailureDetector(heartbeat_timeout=0.1)
        failover = FailoverManager()
        distributor = TaskRedistributor()
        recovery = StateRecoveryManager()
        
        # Setup: register nodes and assign tasks
        failover.register_active_node("node-1")
        failover.register_standby_node("node-2")
        
        for i in range(5):
            distributor.assign_task_to_node(f"task-{i}", "node-1")
        
        recovery.save_state("node-1", {"tasks": ["task-0", "task-1"]})
        
        # Detect failure
        detector.record_heartbeat("node-1")
        time.sleep(0.15)
        failure = detector.detect_failure("node-1")
        
        assert failure is not None
        
        # Failover
        promoted = failover.promote_standby("node-2")
        assert promoted == "node-2"
        
        # Redistribute tasks
        redistributed = distributor.redistribute_tasks("node-1", ["node-2"])
        assert len(redistributed) > 0
        
        # Recover state
        recovered_state = recovery.recover_state("node-1")
        assert recovered_state is not None
    
    def test_concurrent_failure_detection(self):
        """Test concurrent failure detection."""
        detector = FailureDetector(heartbeat_timeout=0.1)
        
        def record_heartbeat(node_id: str):
            detector.record_heartbeat(node_id)
        
        threads = []
        for i in range(5):
            t = threading.Thread(target=record_heartbeat, args=(f"node-{i}",))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # All nodes should have recent heartbeats
        for i in range(5):
            failure = detector.detect_failure(f"node-{i}")
            assert failure is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
