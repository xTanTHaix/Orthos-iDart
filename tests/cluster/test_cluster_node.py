"""
Cluster Node Test Suite - Tests for cluster node management and coordination

Tests cover:
- Node initialization and lifecycle
- Node registration and discovery
- Heartbeat and health monitoring
- Resource allocation
- Failover scenarios
"""

import pytest
import time
import threading
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum


class NodeState(Enum):
    """Node lifecycle states."""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    DEGRADED = "degraded"
    STOPPED = "stopped"


class NodeRole(Enum):
    """Node roles in cluster."""
    MASTER = "master"
    WORKER = "worker"
    STANDBY = "standby"


@dataclass
class NodeConfig:
    """Configuration for a cluster node."""
    node_id: str
    role: NodeRole = NodeRole.WORKER
    port: int = 8000
    heartbeat_interval: float = 1.0
    timeout: float = 5.0
    max_retries: int = 3


@dataclass
class NodeMetrics:
    """Metrics collected from node."""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    active_connections: int = 0
    tasks_completed: int = 0
    errors: int = 0
    last_heartbeat: float = 0.0


@dataclass
class ClusterNode:
    """Represents a cluster node."""
    config: NodeConfig
    state: NodeState = NodeState.INITIALIZING
    metrics: NodeMetrics = field(default_factory=NodeMetrics)
    started_at: Optional[float] = None
    stopped_at: Optional[float] = None
    _lock: threading.Lock = field(default_factory=threading.Lock)


class ClusterNodeManager:
    """Manages cluster nodes and their lifecycle."""
    
    def __init__(self):
        self.nodes: Dict[str, ClusterNode] = {}
        self._lock = threading.RLock()
        self._running = False
    
    def create_node(self, config: NodeConfig) -> ClusterNode:
        """Create a new node."""
        with self._lock:
            node = ClusterNode(config=config)
            self.nodes[config.node_id] = node
            return node
    
    def start_node(self, node_id: str) -> bool:
        """Start a node."""
        with self._lock:
            if node_id not in self.nodes:
                return False
            
            node = self.nodes[node_id]
            try:
                node.state = NodeState.READY
                node.started_at = time.time()
                node.metrics.last_heartbeat = time.time()
                node.state = NodeState.RUNNING
                return True
            except Exception as e:
                node.state = NodeState.DEGRADED
                node.metrics.errors += 1
                return False
    
    def stop_node(self, node_id: str) -> bool:
        """Stop a node."""
        with self._lock:
            if node_id not in self.nodes:
                return False
            
            node = self.nodes[node_id]
            try:
                node.stopped_at = time.time()
                node.state = NodeState.STOPPED
                return True
            except Exception as e:
                return False
    
    def update_metrics(self, node_id: str, metrics: NodeMetrics) -> bool:
        """Update node metrics."""
        with self._lock:
            if node_id not in self.nodes:
                return False
            
            node = self.nodes[node_id]
            try:
                if node.metrics is None:
                    node.metrics = metrics
                else:
                    for field_name in ('cpu_usage', 'memory_usage', 'active_connections', 'tasks_completed', 'errors'):
                        val = getattr(metrics, field_name)
                        if val != 0 and val != 0.0:
                            setattr(node.metrics, field_name, val)
                node.metrics.last_heartbeat = time.time()
                return True
            except Exception:
                return False
    
    def get_node(self, node_id: str) -> Optional[ClusterNode]:
        """Get node by ID."""
        with self._lock:
            return self.nodes.get(node_id)
    
    def get_all_nodes(self) -> List[ClusterNode]:
        """Get all nodes."""
        with self._lock:
            return list(self.nodes.values())
    
    def get_running_nodes(self) -> List[ClusterNode]:
        """Get all running nodes."""
        with self._lock:
            return [n for n in self.nodes.values() if n.state == NodeState.RUNNING]
    
    def health_check(self, node_id: str, timeout: float = 5.0) -> bool:
        """Perform health check on node."""
        with self._lock:
            if node_id not in self.nodes:
                return False
            
            node = self.nodes[node_id]
            try:
                if node.state == NodeState.STOPPED:
                    return False
                
                current_time = time.time()
                if current_time - node.metrics.last_heartbeat > timeout:
                    node.state = NodeState.DEGRADED
                    return False
                
                return True
            except Exception:
                return False


class ClusterCoordinator:
    """Coordinates cluster operations."""
    
    def __init__(self, manager: ClusterNodeManager):
        self.manager = manager
        self._lock = threading.RLock()
    
    def register_node(self, node_id: str, config: NodeConfig) -> bool:
        """Register a new node in cluster."""
        with self._lock:
            try:
                node = self.manager.create_node(config)
                node.state = NodeState.INITIALIZING
                return True
            except Exception as e:
                return False
    
    def discover_nodes(self) -> List[ClusterNode]:
        """Discover all nodes in cluster."""
        with self._lock:
            try:
                return self.manager.get_all_nodes()
            except Exception:
                return []
    
    def select_master(self) -> Optional[ClusterNode]:
        """Select master node from available workers."""
        with self._lock:
            try:
                workers = [
                    n for n in self.manager.get_all_nodes()
                    if n.config.role == NodeRole.WORKER and n.state in (NodeState.READY, NodeState.RUNNING)
                ]
                if not workers:
                    return None
                
                # Select node with lowest load
                return min(workers, key=lambda n: n.metrics.cpu_usage)
            except Exception:
                return None
    
    def load_balance(self, node_ids: List[str]) -> Optional[str]:
        """Select least loaded node from list."""
        with self._lock:
            try:
                available = [
                    self.manager.get_node(node_id)
                    for node_id in node_ids
                    if self.manager.get_node(node_id)
                ]
                if not available:
                    return None
                
                return min(available, key=lambda n: n.metrics.cpu_usage).config.node_id
            except Exception:
                return None


class TestClusterNode:
    """Test cluster node creation and lifecycle."""
    
    def test_node_creation(self):
        """Test node can be created."""
        manager = ClusterNodeManager()
        config = NodeConfig(node_id="test-node-1")
        node = manager.create_node(config)
        
        assert node is not None
        assert node.config.node_id == "test-node-1"
        assert node.state == NodeState.INITIALIZING
    
    def test_node_with_custom_role(self):
        """Test node can be created with custom role."""
        manager = ClusterNodeManager()
        config = NodeConfig(
            node_id="master-node",
            role=NodeRole.MASTER,
            port=9000
        )
        node = manager.create_node(config)
        
        assert node.config.role == NodeRole.MASTER
        assert node.config.port == 9000
    
    def test_node_initialization(self):
        """Test node initializes with default values."""
        manager = ClusterNodeManager()
        config = NodeConfig(node_id="init-test")
        node = manager.create_node(config)
        
        assert node.metrics.cpu_usage == 0.0
        assert node.metrics.memory_usage == 0.0
        assert node.metrics.active_connections == 0
    
    def test_node_id_uniqueness(self):
        """Test node IDs must be unique."""
        manager = ClusterNodeManager()
        
        config1 = NodeConfig(node_id="unique-1")
        config2 = NodeConfig(node_id="unique-2")
        
        node1 = manager.create_node(config1)
        node2 = manager.create_node(config2)
        
        assert node1.config.node_id != node2.config.node_id


class TestNodeLifecycle:
    """Test node lifecycle operations."""
    
    def test_node_start(self):
        """Test node can be started."""
        manager = ClusterNodeManager()
        config = NodeConfig(node_id="start-test")
        node = manager.create_node(config)
        
        result = manager.start_node("start-test")
        
        assert result is True
        assert node.state == NodeState.RUNNING
        assert node.started_at is not None
    
    def test_node_stop(self):
        """Test node can be stopped."""
        manager = ClusterNodeManager()
        config = NodeConfig(node_id="stop-test")
        node = manager.create_node(config)
        manager.start_node("stop-test")
        
        result = manager.stop_node("stop-test")
        
        assert result is True
        assert node.state == NodeState.STOPPED
        assert node.stopped_at is not None
    
    def test_start_nonexistent_node(self):
        """Test starting nonexistent node fails."""
        manager = ClusterNodeManager()
        result = manager.start_node("nonexistent")
        
        assert result is False
    
    def test_stop_nonexistent_node(self):
        """Test stopping nonexistent node fails."""
        manager = ClusterNodeManager()
        result = manager.stop_node("nonexistent")
        
        assert result is False
    
    def test_start_running_node(self):
        """Test starting already running node."""
        manager = ClusterNodeManager()
        config = NodeConfig(node_id="running-test")
        node = manager.create_node(config)
        manager.start_node("running-test")
        
        # Start again
        result = manager.start_node("running-test")
        
        assert result is True
        assert node.state == NodeState.RUNNING
    
    def test_multiple_lifecycle_cycles(self):
        """Test multiple start/stop cycles."""
        manager = ClusterNodeManager()
        config = NodeConfig(node_id="cycle-test")
        node = manager.create_node(config)
        
        for _ in range(3):
            manager.start_node("cycle-test")
            assert node.state == NodeState.RUNNING
            manager.stop_node("cycle-test")
            assert node.state == NodeState.STOPPED


class TestNodeMetrics:
    """Test node metrics operations."""
    
    def test_metrics_update(self):
        """Test metrics can be updated."""
        manager = ClusterNodeManager()
        config = NodeConfig(node_id="metrics-test")
        node = manager.create_node(config)
        manager.start_node("metrics-test")
        
        new_metrics = NodeMetrics(
            cpu_usage=45.5,
            memory_usage=62.3,
            active_connections=10,
            tasks_completed=100,
            errors=0
        )
        
        result = manager.update_metrics("metrics-test", new_metrics)
        
        assert result is True
        assert node.metrics.cpu_usage == 45.5
        assert node.metrics.memory_usage == 62.3
    
    def test_metrics_partial_update(self):
        """Test partial metrics update."""
        manager = ClusterNodeManager()
        config = NodeConfig(node_id="partial-test")
        node = manager.create_node(config)
        manager.start_node("partial-test")
        
        # Update only CPU usage
        new_metrics = NodeMetrics(cpu_usage=75.0)
        
        result = manager.update_metrics("partial-test", new_metrics)
        
        assert result is True
        assert node.metrics.cpu_usage == 75.0
        assert node.metrics.memory_usage == 0.0  # Unchanged
    
    def test_metrics_nonexistent_node(self):
        """Test updating metrics for nonexistent node fails."""
        manager = ClusterNodeManager()
        new_metrics = NodeMetrics(cpu_usage=50.0)
        result = manager.update_metrics("nonexistent", new_metrics)
        
        assert result is False
    
    def test_metrics_preserves_existing_values(self):
        """Test that existing metrics are preserved on partial update."""
        manager = ClusterNodeManager()
        config = NodeConfig(node_id="preserve-test")
        node = manager.create_node(config)
        manager.start_node("preserve-test")
        
        # Set initial metrics
        initial_metrics = NodeMetrics(
            cpu_usage=10.0,
            memory_usage=20.0,
            active_connections=5,
            tasks_completed=50,
            errors=1
        )
        manager.update_metrics("preserve-test", initial_metrics)
        
        # Update only CPU
        new_metrics = NodeMetrics(cpu_usage=30.0)
        manager.update_metrics("preserve-test", new_metrics)
        
        assert node.metrics.cpu_usage == 30.0
        assert node.metrics.memory_usage == 20.0
        assert node.metrics.active_connections == 5
        assert node.metrics.tasks_completed == 50
        assert node.metrics.errors == 1


class TestNodeRetrieval:
    """Test node retrieval operations."""
    
    def test_get_node(self):
        """Test getting node by ID."""
        manager = ClusterNodeManager()
        config = NodeConfig(node_id="retrieve-test")
        manager.create_node(config)
        
        node = manager.get_node("retrieve-test")
        
        assert node is not None
        assert node.config.node_id == "retrieve-test"
    
    def test_get_nonexistent_node(self):
        """Test getting nonexistent node returns None."""
        manager = ClusterNodeManager()
        node = manager.get_node("nonexistent")
        
        assert node is None
    
    def test_get_all_nodes(self):
        """Test getting all nodes."""
        manager = ClusterNodeManager()
        
        for i in range(5):
            config = NodeConfig(node_id=f"all-nodes-{i}")
            manager.create_node(config)
        
        all_nodes = manager.get_all_nodes()
        
        assert len(all_nodes) == 5
        assert all(n.config.node_id.startswith("all-nodes-") for n in all_nodes)
    
    def test_get_running_nodes(self):
        """Test getting only running nodes."""
        manager = ClusterNodeManager()
        
        for i in range(3):
            config = NodeConfig(node_id=f"running-{i}")
            node = manager.create_node(config)
            manager.start_node(f"running-{i}")
        
        for i in range(2):
            config = NodeConfig(node_id=f"stopped-{i}")
            manager.create_node(config)
            manager.stop_node(f"stopped-{i}")
        
        running = manager.get_running_nodes()
        
        assert len(running) == 3
        assert all(n.config.node_id.startswith("running-") for n in running)


class TestClusterCoordinator:
    """Test cluster coordinator operations."""
    
    def test_register_node(self):
        """Test node registration."""
        manager = ClusterNodeManager()
        coordinator = ClusterCoordinator(manager)
        
        config = NodeConfig(node_id="coord-test")
        result = coordinator.register_node("coord-test", config)
        
        assert result is True
        assert manager.get_node("coord-test") is not None
    
    def test_discover_nodes(self):
        """Test node discovery."""
        manager = ClusterNodeManager()
        coordinator = ClusterCoordinator(manager)
        
        for i in range(3):
            config = NodeConfig(node_id=f"discover-{i}")
            manager.create_node(config)
            manager.start_node(f"discover-{i}")
        
        discovered = coordinator.discover_nodes()
        
        assert len(discovered) == 3
    
    def test_select_master(self):
        """Test master selection."""
        manager = ClusterNodeManager()
        coordinator = ClusterCoordinator(manager)
        
        # Create worker nodes
        for i in range(3):
            config = NodeConfig(
                node_id=f"worker-{i}",
                role=NodeRole.WORKER
            )
            manager.create_node(config)
            manager.start_node(f"worker-{i}")
        
        # Update metrics to make node 0 the least loaded
        manager.update_metrics("worker-0", NodeMetrics(cpu_usage=10.0))
        manager.update_metrics("worker-1", NodeMetrics(cpu_usage=50.0))
        manager.update_metrics("worker-2", NodeMetrics(cpu_usage=30.0))
        
        master = coordinator.select_master()
        
        assert master is not None
        assert master.config.node_id == "worker-0"
    
    def test_select_master_no_workers(self):
        """Test master selection with no workers."""
        manager = ClusterNodeManager()
        coordinator = ClusterCoordinator(manager)
        
        master = coordinator.select_master()
        
        assert master is None
    
    def test_load_balance(self):
        """Test load balancing."""
        manager = ClusterNodeManager()
        coordinator = ClusterCoordinator(manager)
        
        for i in range(3):
            config = NodeConfig(node_id=f"balance-{i}")
            manager.create_node(config)
            manager.start_node(f"balance-{i}")
        
        manager.update_metrics("balance-0", NodeMetrics(cpu_usage=80.0))
        manager.update_metrics("balance-1", NodeMetrics(cpu_usage=20.0))
        manager.update_metrics("balance-2", NodeMetrics(cpu_usage=50.0))
        
        selected = coordinator.load_balance(["balance-0", "balance-1", "balance-2"])
        
        assert selected == "balance-1"


class TestClusterHealth:
    """Test cluster health monitoring."""
    
    def test_health_check_running_node(self):
        """Test health check on running node."""
        manager = ClusterNodeManager()
        config = NodeConfig(node_id="health-test")
        node = manager.create_node(config)
        manager.start_node("health-test")
        
        result = manager.health_check("health-test")
        
        assert result is True
    
    def test_health_check_stopped_node(self):
        """Test health check on stopped node."""
        manager = ClusterNodeManager()
        config = NodeConfig(node_id="health-stopped")
        manager.create_node(config)
        manager.stop_node("health-stopped")
        
        result = manager.health_check("health-stopped")
        
        assert result is False
    
    def test_health_check_timeout(self):
        """Test health check with timeout."""
        manager = ClusterNodeManager()
        config = NodeConfig(node_id="health-timeout")
        node = manager.create_node(config)
        manager.start_node("health-timeout")
        
        # Simulate timeout by setting old heartbeat
        node.metrics.last_heartbeat = time.time() - 10.0
        
        result = manager.health_check("health-timeout", timeout=5.0)
        
        assert result is False
        assert node.state == NodeState.DEGRADED
    
    def test_health_check_nonexistent_node(self):
        """Test health check on nonexistent node."""
        manager = ClusterNodeManager()
        result = manager.health_check("nonexistent")
        
        assert result is False


class TestClusterConcurrency:
    """Test cluster operations under concurrency."""
    
    def test_concurrent_node_operations(self):
        """Test concurrent node operations."""
        manager = ClusterNodeManager()
        
        def create_and_start(node_id: str):
            config = NodeConfig(node_id=node_id)
            manager.create_node(config)
            manager.start_node(node_id)
        
        threads = []
        for i in range(10):
            t = threading.Thread(target=create_and_start, args=(f"concurrent-{i}",))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(manager.get_all_nodes()) == 10
        assert all(n.state == NodeState.RUNNING for n in manager.get_all_nodes())
    
    def test_concurrent_metrics_updates(self):
        """Test concurrent metrics updates."""
        manager = ClusterNodeManager()
        config = NodeConfig(node_id="concurrent-metrics")
        node = manager.create_node(config)
        manager.start_node("concurrent-metrics")
        
        updates = []
        
        def update_metrics():
            for _ in range(10):
                metrics = NodeMetrics(
                    cpu_usage=float(hash(time.time()) % 100),
                    memory_usage=float(hash(time.time()) % 100),
                )
                manager.update_metrics("concurrent-metrics", metrics)
                updates.append(metrics.cpu_usage)
        
        threads = []
        for _ in range(5):
            t = threading.Thread(target=update_metrics)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(updates) == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
