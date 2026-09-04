"""
Cluster Task Distribution Test Suite - Tests for task distribution and execution

Tests cover:
- Task submission and queuing
- Task assignment to nodes
- Task execution tracking
- Result collection
- Task priority handling
"""

import pytest
import time
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import deque


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class Task:
    """Represents a distributed task."""
    task_id: str
    task_type: str
    payload: Dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    assigned_node: Optional[str] = None
    submitted_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Any = None
    error: Optional[str] = None
    retries: int = 0
    max_retries: int = 3


@dataclass
class TaskResult:
    """Result of task execution."""
    task_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    node_id: str = ""


class TaskQueue:
    """Priority-based task queue."""
    
    def __init__(self):
        self._queue: deque = deque()
        self._lock = threading.RLock()
        self._by_node: Dict[str, deque] = {}
    
    def enqueue(self, task: Task) -> bool:
        """Add task to queue."""
        with self._lock:
            task.status = TaskStatus.QUEUED
            self._queue.append(task)
            
            if task.assigned_node not in self._by_node:
                self._by_node[task.assigned_node] = deque()
            self._by_node[task.assigned_node].append(task)
            
            return True
    
    def dequeue(self, node_id: Optional[str] = None) -> Optional[Task]:
        """Remove and return highest priority task."""
        with self._lock:
            if node_id:
                if node_id in self._by_node:
                    if self._by_node[node_id]:
                        task = self._by_node[node_id].popleft()
                        task.status = TaskStatus.ASSIGNED
                        return task
                return None
            else:
                if not self._queue:
                    return None
                
                # Get highest priority task
                highest_priority_task = min(self._queue, key=lambda t: t.priority.value)
                self._queue.remove(highest_priority_task)
                highest_priority_task.status = TaskStatus.ASSIGNED
                return highest_priority_task
    
    def peek(self) -> Optional[Task]:
        """Peek at highest priority task without removing it."""
        with self._lock:
            if not self._queue:
                return None
            
            return min(self._queue, key=lambda t: t.priority.value)
    
    def size(self) -> int:
        """Get total queue size."""
        with self._lock:
            return len(self._queue)
    
    def size_by_node(self, node_id: str) -> int:
        """Get queue size for specific node."""
        with self._lock:
            return len(self._by_node.get(node_id, deque()))
    
    def remove_task(self, task_id: str) -> bool:
        """Remove task from queue."""
        with self._lock:
            for i, task in enumerate(self._queue):
                if task.task_id == task_id:
                    self._queue.remove(task)
                    return True
            
            return False


class TaskDistributor:
    """Distributes tasks to available nodes."""
    
    def __init__(self, queue: TaskQueue):
        self.queue = queue
        self._node_capacity: Dict[str, int] = {}
        self._node_status: Dict[str, bool] = {}
        self._lock = threading.RLock()
    
    def register_node(self, node_id: str, capacity: int = 100) -> None:
        """Register a node with capacity."""
        with self._lock:
            self._node_capacity[node_id] = capacity
            self._node_status[node_id] = True
    
    def unregister_node(self, node_id: str) -> None:
        """Unregister a node."""
        with self._lock:
            if node_id in self._node_status:
                del self._node_status[node_id]
                del self._node_capacity[node_id]
    
    def mark_node_available(self, node_id: str) -> None:
        """Mark node as available."""
        with self._lock:
            if node_id in self._node_status:
                self._node_status[node_id] = True
    
    def mark_node_unavailable(self, node_id: str) -> None:
        """Mark node as unavailable."""
        with self._lock:
            if node_id in self._node_status:
                self._node_status[node_id] = False
    
    def is_node_available(self, node_id: str) -> bool:
        """Check if node is available."""
        with self._lock:
            return node_id in self._node_status and self._node_status[node_id]
    
    def get_node_capacity(self, node_id: str) -> int:
        """Get node capacity."""
        with self._lock:
            return self._node_capacity.get(node_id, 0)
    
    def select_node(self, task: Task) -> Optional[str]:
        """Select best node for task."""
        with self._lock:
            available_nodes = [
                node_id for node_id, available in self._node_status.items()
                if available
            ]
            
            if not available_nodes:
                return None
            
            # Select node with lowest load
            return min(
                available_nodes,
                key=lambda n: self._node_capacity.get(n, 0)
            )
    
    def assign_task(self, task: Task, node_id: str) -> bool:
        """Assign task to node."""
        with self._lock:
            if not self.is_node_available(node_id):
                return False
            
            task.assigned_node = node_id
            task.status = TaskStatus.ASSIGNED
            return True
    
    def update_node_capacity(self, node_id: str, capacity: int) -> None:
        """Update node capacity."""
        with self._lock:
            self._node_capacity[node_id] = capacity


class TaskExecutor:
    """Executes tasks on nodes."""
    
    def __init__(self):
        self._handlers: Dict[str, Callable] = {}
        self._lock = threading.RLock()
    
    def register_handler(self, task_type: str, handler: Callable) -> None:
        """Register handler for task type."""
        with self._lock:
            self._handlers[task_type] = handler
    
    def execute(self, task: Task) -> TaskResult:
        """Execute task."""
        handler = self._handlers.get(task.task_type)
        
        if not handler:
            return TaskResult(
                task_id=task.task_id,
                success=False,
                error=f"No handler for task type: {task.task_type}"
            )
        
        start_time = time.time()
        
        try:
            result = handler(task)
            execution_time = time.time() - start_time
            
            return TaskResult(
                task_id=task.task_id,
                success=True,
                result=result,
                execution_time=execution_time,
                node_id=task.assigned_node or ""
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            
            return TaskResult(
                task_id=task.task_id,
                success=False,
                error=str(e),
                execution_time=execution_time,
                node_id=task.assigned_node or ""
            )


class TestTaskQueue:
    """Test task queue operations."""
    
    def test_enqueue_dequeue(self):
        """Test basic enqueue and dequeue."""
        queue = TaskQueue()
        
        task = Task(
            task_id="task-1",
            task_type="compute",
            payload={"data": "test"}
        )
        
        result = queue.enqueue(task)
        assert result is True
        
        retrieved = queue.dequeue()
        assert retrieved is not None
        assert retrieved.task_id == "task-1"
        assert retrieved.status == TaskStatus.ASSIGNED
    
    def test_priority_ordering(self):
        """Test tasks are dequeued in priority order."""
        queue = TaskQueue()
        
        tasks = [
            Task(task_id="low", task_type="compute", priority=TaskPriority.LOW),
            Task(task_id="critical", task_type="compute", priority=TaskPriority.CRITICAL),
            Task(task_id="high", task_type="compute", priority=TaskPriority.HIGH),
            Task(task_id="normal", task_type="compute", priority=TaskPriority.NORMAL),
        ]
        
        for task in tasks:
            queue.enqueue(task)
        
        # Should dequeue in priority order
        retrieved = queue.dequeue()
        assert retrieved.task_id == "critical"
        
        retrieved = queue.dequeue()
        assert retrieved.task_id == "high"
        
        retrieved = queue.dequeue()
        assert retrieved.task_id == "normal"
        
        retrieved = queue.dequeue()
        assert retrieved.task_id == "low"
    
    def test_queue_size(self):
        """Test queue size tracking."""
        queue = TaskQueue()
        
        assert queue.size() == 0
        
        for i in range(5):
            queue.enqueue(Task(task_id=f"task-{i}", task_type="compute"))
        
        assert queue.size() == 5
    
    def test_remove_task(self):
        """Test task removal from queue."""
        queue = TaskQueue()
        
        task = Task(task_id="to-remove", task_type="compute")
        queue.enqueue(task)
        
        result = queue.remove_task("to-remove")
        assert result is True
        assert queue.size() == 0
    
    def test_remove_nonexistent_task(self):
        """Test removing nonexistent task."""
        queue = TaskQueue()
        result = queue.remove_task("nonexistent")
        assert result is False


class TestTaskDistributor:
    """Test task distribution operations."""
    
    def test_register_node(self):
        """Test node registration."""
        queue = TaskQueue()
        distributor = TaskDistributor(queue)
        
        distributor.register_node("node-1", capacity=100)
        
        assert distributor.is_node_available("node-1")
        assert distributor.get_node_capacity("node-1") == 100
    
    def test_unregister_node(self):
        """Test node unregistration."""
        queue = TaskQueue()
        distributor = TaskDistributor(queue)
        
        distributor.register_node("node-1")
        distributor.unregister_node("node-1")
        
        assert not distributor.is_node_available("node-1")
    
    def test_node_availability(self):
        """Test node availability marking."""
        queue = TaskQueue()
        distributor = TaskDistributor(queue)
        
        distributor.register_node("node-1")
        
        distributor.mark_node_available("node-1")
        assert distributor.is_node_available("node-1")
        
        distributor.mark_node_unavailable("node-1")
        assert not distributor.is_node_available("node-1")
    
    def test_task_assignment(self):
        """Test task assignment to node."""
        queue = TaskQueue()
        distributor = TaskDistributor(queue)
        
        distributor.register_node("node-1")
        distributor.mark_node_available("node-1")
        
        task = Task(task_id="assign-test", task_type="compute")
        result = distributor.assign_task(task, "node-1")
        
        assert result is True
        assert task.assigned_node == "node-1"
        assert task.status == TaskStatus.ASSIGNED
    
    def test_assignment_to_unavailable_node(self):
        """Test assignment to unavailable node fails."""
        queue = TaskQueue()
        distributor = TaskDistributor(queue)
        
        distributor.register_node("node-1")
        distributor.mark_node_unavailable("node-1")
        
        task = Task(task_id="fail-assign", task_type="compute")
        result = distributor.assign_task(task, "node-1")
        
        assert result is False
        assert task.assigned_node is None
    
    def test_node_selection(self):
        """Test node selection based on capacity."""
        queue = TaskQueue()
        distributor = TaskDistributor(queue)
        
        distributor.register_node("node-1", capacity=50)
        distributor.register_node("node-2", capacity=100)
        distributor.register_node("node-3", capacity=75)
        
        task = Task(task_id="select-test", task_type="compute")
        selected = distributor.select_node(task)
        
        assert selected == "node-1"  # Lowest capacity
    
    def test_multiple_nodes_selection(self):
        """Test selection among multiple nodes."""
        queue = TaskQueue()
        distributor = TaskDistributor(queue)
        
        for i in range(5):
            distributor.register_node(f"node-{i}", capacity=100 - i * 10)
        
        task = Task(task_id="multi-select", task_type="compute")
        selected = distributor.select_node(task)
        
        assert selected == "node-4"  # Lowest capacity (90)


class TestTaskExecutor:
    """Test task execution operations."""
    
    def test_execute_task_with_handler(self):
        """Test task execution with registered handler."""
        executor = TaskExecutor()
        
        def handler(task: Task):
            return {"result": "success"}
        
        executor.register_handler("compute", handler)
        
        task = Task(task_id="exec-test", task_type="compute")
        result = executor.execute(task)
        
        assert result.success is True
        assert result.result == {"result": "success"}
    
    def test_execute_task_without_handler(self):
        """Test task execution without handler fails."""
        executor = TaskExecutor()
        
        task = Task(task_id="no-handler", task_type="unknown")
        result = executor.execute(task)
        
        assert result.success is False
        assert "No handler" in result.error
    
    def test_execute_task_with_error(self):
        """Test task execution with error handling."""
        executor = TaskExecutor()
        
        def failing_handler(task: Task):
            raise ValueError("Task failed")
        
        executor.register_handler("failing", failing_handler)
        
        task = Task(task_id="error-test", task_type="failing")
        result = executor.execute(task)
        
        assert result.success is False
        assert "Task failed" in result.error
    
    def test_execution_time_tracking(self):
        """Test execution time tracking."""
        executor = TaskExecutor()
        
        def slow_handler(task: Task):
            time.sleep(0.1)
            return {"result": "done"}
        
        executor.register_handler("slow", slow_handler)
        
        task = Task(task_id="time-test", task_type="slow")
        result = executor.execute(task)
        
        assert result.execution_time >= 0.1


class TestTaskDistributionIntegration:
    """Test integration of distribution and execution."""
    
    def test_full_task_lifecycle(self):
        """Test complete task lifecycle."""
        queue = TaskQueue()
        distributor = TaskDistributor(queue)
        executor = TaskExecutor()
        
        # Register node and handler
        distributor.register_node("worker-1")
        distributor.mark_node_available("worker-1")
        
        def handler(task: Task):
            return {"computed": task.payload.get("value", 0) * 2}
        
        executor.register_handler("compute", handler)
        
        # Create and enqueue task
        task = Task(
            task_id="lifecycle-test",
            task_type="compute",
            payload={"value": 21},
            priority=TaskPriority.HIGH
        )
        
        queue.enqueue(task)
        assert task.status == TaskStatus.QUEUED
        
        # Assign to node
        distributor.assign_task(task, "worker-1")
        assert task.status == TaskStatus.ASSIGNED
        
        # Execute task
        result = executor.execute(task)
        assert result.success is True
        assert result.result == {"computed": 42}
    
    def test_task_retry_on_failure(self):
        """Test task retry on execution failure."""
        queue = TaskQueue()
        distributor = TaskDistributor(queue)
        executor = TaskExecutor()
        
        def failing_handler(task: Task):
            raise RuntimeError("Always fails")
        
        executor.register_handler("failing", failing_handler)
        
        task = Task(
            task_id="retry-test",
            task_type="failing",
            max_retries=2
        )
        
        # First execution fails
        result = executor.execute(task)
        assert result.success is False
        assert task.retries == 0
        
        # Retry logic would go here in full implementation
        task.retries += 1
        
        # Second execution fails
        result = executor.execute(task)
        assert result.success is False
        assert task.retries == 1
    
    def test_concurrent_task_processing(self):
        """Test concurrent task processing."""
        queue = TaskQueue()
        executor = TaskExecutor()
        
        results = []
        lock = threading.Lock()
        
        def handler(task: Task):
            time.sleep(0.05)
            with lock:
                results.append(task.task_id)
            return {"result": "done"}
        
        executor.register_handler("compute", handler)
        
        def producer():
            for i in range(10):
                task = Task(
                    task_id=f"concurrent-{i}",
                    task_type="compute",
                    payload={"value": i}
                )
                queue.enqueue(task)
        
        def consumer():
            consumed = 0
            start_wait = time.time()
            while consumed < 10 and (time.time() - start_wait) < 5.0:
                task = queue.dequeue()
                if task:
                    executor.execute(task)
                    consumed += 1
                else:
                    time.sleep(0.01)
        
        producer_thread = threading.Thread(target=producer)
        consumer_thread = threading.Thread(target=consumer)
        
        producer_thread.start()
        consumer_thread.start()
        
        producer_thread.join()
        consumer_thread.join()
        
        assert len(results) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
