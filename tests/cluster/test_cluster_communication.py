"""
Cluster Communication Test Suite - Tests for inter-node communication

Tests cover:
- Message passing between nodes
- RPC calls
- Event broadcasting
- Message queue operations
- Connection management
"""

import pytest
import time
import threading
import json
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque


class MessageType(Enum):
    """Types of messages in cluster."""
    HEARTBEAT = "heartbeat"
    TASK_ASSIGNMENT = "task_assignment"
    TASK_RESULT = "task_result"
    ERROR_REPORT = "error_report"
    CONFIG_UPDATE = "config_update"
    NODE_JOIN = "node_join"
    NODE_LEAVE = "node_leave"


@dataclass
class Message:
    """Represents a cluster message."""
    message_type: MessageType
    source_node: str
    target_node: Optional[str] = None
    payload: Dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    correlation_id: str = field(default_factory=lambda: str(hash(time.time())))
    sequence_number: int = 0


class MessageQueue:
    """Thread-safe message queue for inter-node communication."""
    
    def __init__(self, max_size: int = 10000):
        self.queue: deque = deque()
        self._max_size = max_size
        self._lock = threading.RLock()
        self._condition = threading.Condition(self._lock)
        self._closed = False
    
    @property
    def max_size(self) -> int:
        return self._max_size
    
    def put(self, message: Message, timeout: float = 0.1) -> bool:
        """Put message into queue."""
        with self._condition:
            if self._closed:
                return False
            
            start_time = time.time()
            while len(self.queue) >= self._max_size:
                remaining = timeout - (time.time() - start_time)
                if remaining <= 0:
                    return False
                if not self._condition.wait(timeout=min(remaining, 0.05)):
                    if time.time() - start_time >= timeout:
                        return False
            
            if self._closed:
                return False
            self.queue.append(message)
            self._condition.notify_all()
            return True
    
    def get(self, timeout: float = 0.1) -> Optional[Message]:
        """Get message from queue."""
        with self._condition:
            if self._closed:
                return None
            
            start_time = time.time()
            while not self.queue and not self._closed:
                remaining = timeout - (time.time() - start_time)
                if remaining <= 0:
                    return None
                if not self._condition.wait(timeout=min(remaining, 0.05)):
                    if time.time() - start_time >= timeout:
                        return None
            
            if self._closed:
                return None
            
            if self.queue:
                msg = self.queue.popleft()
                self._condition.notify_all()
                return msg
            return None
    
    def peek(self) -> Optional[Message]:
        """Peek at next message without removing it."""
        with self._lock:
            if self.queue:
                return self.queue[0]
            return None
    
    def size(self) -> int:
        """Get queue size."""
        with self._lock:
            return len(self.queue)
    
    def clear(self):
        """Clear all messages."""
        with self._condition:
            self.queue.clear()
            self._condition.notify_all()
    
    def close(self):
        """Close the queue."""
        with self._condition:
            self._closed = True
            self._condition.notify_all()


class ConnectionManager:
    """Manages connections between nodes."""
    
    def __init__(self):
        self.connections: Dict[str, Dict[str, bool]] = {}
        self._lock = threading.RLock()
    
    def connect(self, source: str, target: str) -> bool:
        """Establish connection between nodes."""
        with self._lock:
            if source not in self.connections:
                self.connections[source] = {}
            if target not in self.connections:
                self.connections[target] = {}
            
            self.connections[source][target] = True
            self.connections[target][source] = True
            return True
    
    def disconnect(self, source: str, target: str) -> bool:
        """Disconnect between nodes."""
        with self._lock:
            found = False
            if source in self.connections and target in self.connections[source]:
                del self.connections[source][target]
                found = True
            if target in self.connections and source in self.connections[target]:
                del self.connections[target][source]
                found = True
            return found
    
    def is_connected(self, source: str, target: str) -> bool:
        """Check if nodes are connected."""
        with self._lock:
            return source in self.connections and target in self.connections[source]
    
    def get_connection_count(self, node: str) -> int:
        """Get number of connections for a node."""
        with self._lock:
            return len(self.connections.get(node, {}))
    
    def get_all_connections(self, node: str) -> List[str]:
        """Get all connected nodes."""
        with self._lock:
            return list(self.connections.get(node, {}).keys())
    
    def broadcast(self, message: Message, exclude: Optional[str] = None) -> int:
        """Broadcast message to all connected nodes."""
        with self._lock:
            count = 0
            for target in self.connections.get(message.source_node, {}):
                if target != exclude:
                    count += 1
            return count


class MessageRouter:
    """Routes messages to appropriate handlers."""
    
    def __init__(self):
        self._handlers: Dict[MessageType, List[Callable]] = {}
        self._lock = threading.RLock()
    
    def register_handler(self, message_type: MessageType, handler: Callable) -> None:
        """Register handler for message type."""
        with self._lock:
            if message_type not in self._handlers:
                self._handlers[message_type] = []
            self._handlers[message_type].append(handler)
    
    def unregister_handler(self, message_type: MessageType, handler: Callable) -> None:
        """Unregister handler for message type."""
        with self._lock:
            if message_type in self._handlers:
                self._handlers[message_type].remove(handler)
    
    def get_handlers(self, message_type: MessageType) -> List[Callable]:
        """Get all handlers for message type."""
        with self._lock:
            return list(self._handlers.get(message_type, []))
    
    def route(self, message: Message) -> int:
        """Route message to handlers."""
        handlers = self.get_handlers(message.message_type)
        executed = 0
        
        for handler in handlers:
            try:
                handler(message)
                executed += 1
            except Exception:
                pass
        
        return executed


class TestMessageQueue:
    """Test message queue operations."""
    
    def test_queue_put_get(self):
        """Test basic put and get operations."""
        queue = MessageQueue()
        
        message = Message(
            message_type=MessageType.HEARTBEAT,
            source_node="node-1",
            payload={"data": "test"}
        )
        
        result = queue.put(message)
        assert result is True
        
        retrieved = queue.get()
        assert retrieved is not None
        assert retrieved.message_type == MessageType.HEARTBEAT
        assert retrieved.payload["data"] == "test"
    
    def test_queue_fifo_order(self):
        """Test FIFO ordering."""
        queue = MessageQueue()
        
        for i in range(5):
            message = Message(
                message_type=MessageType.HEARTBEAT,
                source_node=f"node-{i}",
                payload={"index": i}
            )
            queue.put(message)
        
        for i in range(5):
            retrieved = queue.get()
            assert retrieved.payload["index"] == i
    
    def test_queue_max_size(self):
        """Test queue max size limit."""
        queue = MessageQueue(max_size=3)
        
        for i in range(5):
            message = Message(
                message_type=MessageType.HEARTBEAT,
                source_node=f"node-{i}",
                payload={"index": i}
            )
            result = queue.put(message)
            
            if i < 3:
                assert result is True
            else:
                assert result is False
    
    def test_queue_peek(self):
        """Test peek operation."""
        queue = MessageQueue()
        
        message1 = Message(
            message_type=MessageType.HEARTBEAT,
            source_node="node-1",
            payload={"data": "first"}
        )
        message2 = Message(
            message_type=MessageType.HEARTBEAT,
            source_node="node-2",
            payload={"data": "second"}
        )
        
        queue.put(message1)
        queue.put(message2)
        
        peeked = queue.peek()
        assert peeked is not None
        assert peeked.payload["data"] == "first"
        
        # Queue should still have both messages
        assert queue.size() == 2
    
    def test_queue_clear(self):
        """Test clear operation."""
        queue = MessageQueue()
        
        for i in range(5):
            message = Message(
                message_type=MessageType.HEARTBEAT,
                source_node=f"node-{i}",
                payload={"index": i}
            )
            queue.put(message)
        
        queue.clear()
        assert queue.size() == 0
        assert queue.get() is None
    
    def test_queue_close(self):
        """Test close operation."""
        queue = MessageQueue()
        
        message = Message(
            message_type=MessageType.HEARTBEAT,
            source_node="node-1",
            payload={"data": "test"}
        )
        
        queue.put(message)
        queue.close()
        
        assert queue.get() is None


class TestConnectionManager:
    """Test connection management operations."""
    
    def test_connect_disconnect(self):
        """Test connect and disconnect operations."""
        manager = ConnectionManager()
        
        result = manager.connect("node-1", "node-2")
        assert result is True
        assert manager.is_connected("node-1", "node-2")
        
        result = manager.disconnect("node-1", "node-2")
        assert result is True
        assert not manager.is_connected("node-1", "node-2")
    
    def test_multiple_connections(self):
        """Test multiple connections from one node."""
        manager = ConnectionManager()
        
        manager.connect("node-1", "node-2")
        manager.connect("node-1", "node-3")
        manager.connect("node-1", "node-4")
        
        assert manager.get_connection_count("node-1") == 3
        assert "node-2" in manager.get_all_connections("node-1")
        assert "node-3" in manager.get_all_connections("node-1")
        assert "node-4" in manager.get_all_connections("node-1")
    
    def test_connection_count(self):
        """Test connection count accuracy."""
        manager = ConnectionManager()
        
        manager.connect("node-1", "node-2")
        manager.connect("node-2", "node-3")
        manager.connect("node-3", "node-4")
        
        assert manager.get_connection_count("node-1") == 1
        assert manager.get_connection_count("node-2") == 2
        assert manager.get_connection_count("node-3") == 2
        assert manager.get_connection_count("node-4") == 1
    
    def test_broadcast(self):
        """Test message broadcasting."""
        manager = ConnectionManager()
        
        manager.connect("node-1", "node-2")
        manager.connect("node-1", "node-3")
        manager.connect("node-2", "node-4")
        
        message = Message(
            message_type=MessageType.HEARTBEAT,
            source_node="node-1",
            payload={"data": "broadcast"}
        )
        
        count = manager.broadcast(message)
        assert count == 2  # node-2 and node-3


class TestMessageRouter:
    """Test message routing operations."""
    
    def test_handler_registration(self):
        """Test handler registration."""
        router = MessageRouter()
        
        def handler1(message: Message):
            pass
        
        def handler2(message: Message):
            pass
        
        router.register_handler(MessageType.HEARTBEAT, handler1)
        router.register_handler(MessageType.HEARTBEAT, handler2)
        
        handlers = router.get_handlers(MessageType.HEARTBEAT)
        assert len(handlers) == 2
    
    def test_message_routing(self):
        """Test message routing to handlers."""
        router = MessageRouter()
        
        executed = []
        
        def handler1(message: Message):
            executed.append(("handler1", message.payload))
        
        def handler2(message: Message):
            executed.append(("handler2", message.payload))
        
        router.register_handler(MessageType.HEARTBEAT, handler1)
        router.register_handler(MessageType.HEARTBEAT, handler2)
        
        message = Message(
            message_type=MessageType.HEARTBEAT,
            source_node="node-1",
            payload={"data": "test"}
        )
        
        count = router.route(message)
        
        assert count == 2
        assert len(executed) == 2
        assert ("handler1", {"data": "test"}) in executed
        assert ("handler2", {"data": "test"}) in executed
    
    def test_different_message_types(self):
        """Test routing different message types separately."""
        router = MessageRouter()
        
        executed = []
        
        def heartbeat_handler(message: Message):
            executed.append(("heartbeat",))
        
        def error_handler(message: Message):
            executed.append(("error",))
        
        router.register_handler(MessageType.HEARTBEAT, heartbeat_handler)
        router.register_handler(MessageType.ERROR_REPORT, error_handler)
        
        heartbeat = Message(
            message_type=MessageType.HEARTBEAT,
            source_node="node-1",
            payload={}
        )
        
        error = Message(
            message_type=MessageType.ERROR_REPORT,
            source_node="node-1",
            payload={"error": "test"}
        )
        
        router.route(heartbeat)
        router.route(error)
        
        assert ("heartbeat",) in executed
        assert ("error",) in executed
    
    def test_handler_unregistration(self):
        """Test handler unregistration."""
        router = MessageRouter()
        
        def handler1(message: Message):
            pass
        
        def handler2(message: Message):
            pass
        
        router.register_handler(MessageType.HEARTBEAT, handler1)
        router.register_handler(MessageType.HEARTBEAT, handler2)
        
        router.unregister_handler(MessageType.HEARTBEAT, handler1)
        
        handlers = router.get_handlers(MessageType.HEARTBEAT)
        assert len(handlers) == 1


class TestMessageSerialization:
    """Test message serialization and deserialization."""
    
    def test_message_json_serialization(self):
        """Test message can be serialized to JSON."""
        message = Message(
            message_type=MessageType.HEARTBEAT,
            source_node="node-1",
            target_node="node-2",
            payload={"key": "value"},
            timestamp=1234567890.0,
            correlation_id="corr-123",
            sequence_number=42
        )
        
        serialized = json.dumps({
            "message_type": message.message_type.value,
            "source_node": message.source_node,
            "target_node": message.target_node,
            "payload": message.payload,
            "timestamp": message.timestamp,
            "correlation_id": message.correlation_id,
            "sequence_number": message.sequence_number
        })
        
        assert serialized is not None
        assert "heartbeat" in serialized
        assert "node-1" in serialized
    
    def test_message_json_deserialization(self):
        """Test message can be deserialized from JSON."""
        json_data = json.dumps({
            "message_type": "heartbeat",
            "source_node": "node-1",
            "target_node": "node-2",
            "payload": {"key": "value"},
            "timestamp": 1234567890.0,
            "correlation_id": "corr-123",
            "sequence_number": 42
        })
        
        data = json.loads(json_data)
        
        assert data["message_type"] == "heartbeat"
        assert data["source_node"] == "node-1"
        assert data["payload"]["key"] == "value"
    
    def test_message_payload_types(self):
        """Test message with various payload types."""
        message = Message(
            message_type=MessageType.TASK_RESULT,
            source_node="node-1",
            payload={
                "result": 42,
                "status": "success",
                "data": [1, 2, 3],
                "nested": {"key": "value"}
            }
        )
        
        assert message.payload["result"] == 42
        assert message.payload["status"] == "success"
        assert message.payload["data"] == [1, 2, 3]


class TestClusterCommunicationIntegration:
    """Test integration of communication components."""
    
    def test_full_message_flow(self):
        """Test complete message flow through system."""
        queue = MessageQueue()
        router = MessageRouter()
        manager = ConnectionManager()
        
        executed_messages = []
        
        def handler(message: Message):
            executed_messages.append(message)
        
        router.register_handler(MessageType.HEARTBEAT, handler)
        
        # Create connection
        manager.connect("sender", "receiver")
        
        # Create and send message
        message = Message(
            message_type=MessageType.HEARTBEAT,
            source_node="sender",
            target_node="receiver",
            payload={"data": "test"}
        )
        
        # Put in queue
        queue.put(message)
        
        # Get from queue and route
        retrieved = queue.get()
        router.route(retrieved)
        
        assert len(executed_messages) == 1
        assert executed_messages[0].payload["data"] == "test"
    
    def test_concurrent_message_processing(self):
        """Test concurrent message processing."""
        queue = MessageQueue()
        router = MessageRouter()
        
        processed = []
        lock = threading.Lock()
        
        def handler(message: Message):
            with lock:
                processed.append(message.correlation_id)
        
        router.register_handler(MessageType.HEARTBEAT, handler)
        
        def producer():
            for i in range(10):
                message = Message(
                    message_type=MessageType.HEARTBEAT,
                    source_node=f"producer-{i % 3}",
                    payload={"index": i}
                )
                queue.put(message)
        
        def consumer():
            for _ in range(10):
                message = queue.get(timeout=1.0)
                if message:
                    router.route(message)
        
        # Start producer and consumer threads
        producer_thread = threading.Thread(target=producer)
        consumer_thread = threading.Thread(target=consumer)
        
        producer_thread.start()
        consumer_thread.start()
        
        producer_thread.join()
        consumer_thread.join()
        
        assert len(processed) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
