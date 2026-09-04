"""
Cluster Monitoring Test Suite - Tests for cluster monitoring and metrics

Tests cover:
- Metrics collection
- Performance monitoring
- Resource utilization tracking
- Alert generation
- Dashboard data aggregation
"""

import pytest
import time
import threading
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class MetricType(Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Metric:
    """Represents a metric."""
    name: str
    metric_type: MetricType
    value: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    unit: str = ""


@dataclass
class Alert:
    """Represents an alert."""
    alert_id: str
    alert_type: str
    severity: str
    message: str
    triggered_at: float = field(default_factory=time.time)
    acknowledged: bool = False
    resolved: bool = False


class MetricsCollector:
    """Collects metrics from nodes."""
    
    def __init__(self):
        self._metrics: Dict[str, Metric] = {}
        self._counters: Dict[str, int] = defaultdict(int)
        self._lock = threading.RLock()
    
    def record_counter(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """Record counter metric."""
        with self._lock:
            key = f"{name}:{labels}" if labels else name
            
            if key in self._counters:
                self._counters[key] += value
            else:
                self._counters[key] = value
    
    def record_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record gauge metric."""
        with self._lock:
            key = f"{name}:{labels}" if labels else name
            
            if key not in self._metrics:
                self._metrics[key] = Metric(
                    name=name,
                    metric_type=MetricType.GAUGE,
                    value=value,
                    labels=labels or {},
                    timestamp=time.time()
                )
            else:
                self._metrics[key].value = value
                self._metrics[key].timestamp = time.time()
    
    def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record histogram metric."""
        with self._lock:
            key = f"{name}:{labels}" if labels else name
            
            if key not in self._metrics:
                self._metrics[key] = Metric(
                    name=name,
                    metric_type=MetricType.HISTOGRAM,
                    value=value,
                    labels=labels or {},
                    timestamp=time.time()
                )
            else:
                self._metrics[key].value = value
                self._metrics[key].timestamp = time.time()
    
    def get_metric(self, name: str, labels: Optional[Dict[str, str]] = None) -> Optional[Metric]:
        """Get metric by name and labels."""
        with self._lock:
            key = f"{name}:{labels}" if labels else name
            return self._metrics.get(key)
    
    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> int:
        """Get counter value."""
        with self._lock:
            key = f"{name}:{labels}" if labels else name
            return self._counters.get(key, 0)
    
    def get_all_metrics(self) -> List[Metric]:
        """Get all metrics."""
        with self._lock:
            return list(self._metrics.values())
    
    def get_all_counters(self) -> Dict[str, int]:
        """Get all counters."""
        with self._lock:
            return dict(self._counters)
    
    def clear(self) -> None:
        """Clear all metrics."""
        with self._lock:
            self._metrics.clear()
            self._counters.clear()


class PerformanceMonitor:
    """Monitors performance metrics."""
    
    def __init__(self, window_size: float = 60.0):
        self.window_size = window_size
        self._response_times: Dict[str, List[Tuple[float, float]]] = defaultdict(list)
        self._throughput: Dict[str, int] = defaultdict(int)
        self._lock = threading.RLock()

    def _get_current_times(self, endpoint: str) -> List[float]:
        now = time.time()
        cutoff = now - self.window_size
        valid = [rt for rt, ts in self._response_times.get(endpoint, []) if ts >= cutoff]
        self._response_times[endpoint] = [(rt, ts) for rt, ts in self._response_times.get(endpoint, []) if ts >= cutoff]
        return valid
    
    def record_response_time(self, endpoint: str, response_time: float) -> None:
        """Record response time."""
        with self._lock:
            now = time.time()
            self._response_times[endpoint].append((response_time, now))
            
            # Remove old entries outside window
            cutoff = now - self.window_size
            self._response_times[endpoint] = [
                entry for entry in self._response_times[endpoint]
                if entry[1] >= cutoff
            ]
    
    def record_request(self, endpoint: str) -> None:
        """Record request for throughput."""
        with self._lock:
            self._throughput[endpoint] += 1
    
    def get_avg_response_time(self, endpoint: str) -> float:
        """Get average response time for endpoint."""
        with self._lock:
            times = self._get_current_times(endpoint)
            if not times:
                return 0.0
            return sum(times) / len(times)
    
    def get_min_response_time(self, endpoint: str) -> float:
        """Get minimum response time for endpoint."""
        with self._lock:
            times = self._get_current_times(endpoint)
            if not times:
                return 0.0
            return min(times)
    
    def get_max_response_time(self, endpoint: str) -> float:
        """Get maximum response time for endpoint."""
        with self._lock:
            times = self._get_current_times(endpoint)
            if not times:
                return 0.0
            return max(times)
    
    def get_throughput(self, endpoint: str) -> int:
        """Get throughput for endpoint."""
        with self._lock:
            return self._throughput.get(endpoint, 0)
    
    def get_p95_response_time(self, endpoint: str) -> float:
        """Get 95th percentile response time."""
        with self._lock:
            times = sorted(self._get_current_times(endpoint))
            if not times:
                return 0.0
            
            index = int(len(times) * 0.95)
            return times[min(index, len(times) - 1)]
    
    def get_p99_response_time(self, endpoint: str) -> float:
        """Get 99th percentile response time."""
        with self._lock:
            times = sorted(self._get_current_times(endpoint))
            if not times:
                return 0.0
            
            index = int(len(times) * 0.99)
            return times[min(index, len(times) - 1)]


class ResourceMonitor:
    """Monitors resource utilization."""
    
    def __init__(self):
        self._cpu_usage: Dict[str, float] = {}
        self._memory_usage: Dict[str, float] = {}
        self._disk_usage: Dict[str, float] = {}
        self._network_in: Dict[str, float] = {}
        self._network_out: Dict[str, float] = {}
        self._lock = threading.RLock()
    
    def update_cpu_usage(self, node_id: str, usage: float) -> None:
        """Update CPU usage for node."""
        with self._lock:
            self._cpu_usage[node_id] = usage
    
    def update_memory_usage(self, node_id: str, usage: float) -> None:
        """Update memory usage for node."""
        with self._lock:
            self._memory_usage[node_id] = usage
    
    def update_disk_usage(self, node_id: str, usage: float) -> None:
        """Update disk usage for node."""
        with self._lock:
            self._disk_usage[node_id] = usage
    
    def update_network_usage(self, node_id: str, inbound: float, outbound: float) -> None:
        """Update network usage for node."""
        with self._lock:
            self._network_in[node_id] = inbound
            self._network_out[node_id] = outbound
    
    def get_cpu_usage(self, node_id: str) -> float:
        """Get CPU usage for node."""
        with self._lock:
            return self._cpu_usage.get(node_id, 0.0)
    
    def get_memory_usage(self, node_id: str) -> float:
        """Get memory usage for node."""
        with self._lock:
            return self._memory_usage.get(node_id, 0.0)
    
    def get_disk_usage(self, node_id: str) -> float:
        """Get disk usage for node."""
        with self._lock:
            return self._disk_usage.get(node_id, 0.0)
    
    def get_network_usage(self, node_id: str) -> tuple:
        """Get network usage for node."""
        with self._lock:
            return (
                self._network_in.get(node_id, 0.0),
                self._network_out.get(node_id, 0.0)
            )
    
    def get_all_resources(self, node_id: str) -> Dict[str, float]:
        """Get all resource usage for node."""
        with self._lock:
            return {
                "cpu": self._cpu_usage.get(node_id, 0.0),
                "memory": self._memory_usage.get(node_id, 0.0),
                "disk": self._disk_usage.get(node_id, 0.0),
                "network_in": self._network_in.get(node_id, 0.0),
                "network_out": self._network_out.get(node_id, 0.0),
            }


class AlertManager:
    """Manages alerts and notifications."""
    
    def __init__(self):
        self._alerts: Dict[str, Alert] = {}
        self._alert_rules: Dict[str, Dict] = {}
        self._lock = threading.RLock()
    
    def add_alert_rule(self, alert_type: str, severity: str, threshold: float) -> None:
        """Add alert rule."""
        with self._lock:
            self._alert_rules[alert_type] = {
                "severity": severity,
                "threshold": threshold
            }
    
    def check_alerts(self, metrics: Dict[str, float]) -> List[Alert]:
        """Check metrics against alert rules."""
        with self._lock:
            triggered = []
            
            for alert_type, rule in self._alert_rules.items():
                if alert_type in metrics:
                    value = metrics[alert_type]
                    if value > rule["threshold"]:
                        alert = Alert(
                            alert_id=str(hash(alert_type)),
                            alert_type=alert_type,
                            severity=rule["severity"],
                            message=f"{alert_type} exceeded threshold: {value} > {rule['threshold']}"
                        )
                        triggered.append(alert)
                        self._alerts[alert.alert_id] = alert
            
            return triggered
    
    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get alert by ID."""
        with self._lock:
            return self._alerts.get(alert_id)
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge alert."""
        with self._lock:
            if alert_id in self._alerts:
                self._alerts[alert_id].acknowledged = True
                return True
            return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve alert."""
        with self._lock:
            if alert_id in self._alerts:
                self._alerts[alert_id].resolved = True
                return True
            return False
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts."""
        with self._lock:
            return [
                alert for alert in self._alerts.values()
                if not alert.resolved
            ]
    
    def get_alerts_by_severity(self, severity: str) -> List[Alert]:
        """Get alerts by severity."""
        with self._lock:
            return [
                alert for alert in self._alerts.values()
                if alert.severity == severity and not alert.resolved
            ]
    
    def clear_resolved_alerts(self) -> int:
        """Clear resolved alerts."""
        with self._lock:
            count = 0
            to_remove = [
                alert_id for alert_id, alert in self._alerts.items()
                if alert.resolved
            ]
            
            for alert_id in to_remove:
                del self._alerts[alert_id]
                count += 1
            
            return count


class DashboardAggregator:
    """Aggregates data for dashboard display."""
    
    def __init__(self):
        self._node_data: Dict[str, Dict] = {}
        self._lock = threading.RLock()
    
    def update_node_data(self, node_id: str, data: Dict) -> None:
        """Update data for node."""
        with self._lock:
            self._node_data[node_id] = data
    
    def get_node_data(self, node_id: str) -> Optional[Dict]:
        """Get data for node."""
        with self._lock:
            return self._node_data.get(node_id)
    
    def get_all_node_data(self) -> Dict[str, Dict]:
        """Get all node data."""
        with self._lock:
            return dict(self._node_data)
    
    def get_cluster_summary(self) -> Dict:
        """Get cluster summary."""
        with self._lock:
            if not self._node_data:
                return {}
            
            nodes = list(self._node_data.values())
            
            return {
                "total_nodes": len(nodes),
                "avg_cpu": sum(n.get("cpu", 0) for n in nodes) / len(nodes),
                "avg_memory": sum(n.get("memory", 0) for n in nodes) / len(nodes),
                "max_cpu": max(n.get("cpu", 0) for n in nodes),
                "max_memory": max(n.get("memory", 0) for n in nodes),
            }


class TestMetricsCollector:
    """Test metrics collection operations."""
    
    def test_counter_recording(self):
        """Test counter metric recording."""
        collector = MetricsCollector()
        
        collector.record_counter("requests", 1, labels={"endpoint": "/api"})
        collector.record_counter("requests", 1, labels={"endpoint": "/api"})
        collector.record_counter("requests", 1, labels={"endpoint": "/api"})
        
        count = collector.get_counter("requests", labels={"endpoint": "/api"})
        
        assert count == 3
    
    def test_gauge_recording(self):
        """Test gauge metric recording."""
        collector = MetricsCollector()
        
        collector.record_gauge("cpu_usage", 50.0, labels={"node": "node-1"})
        collector.record_gauge("cpu_usage", 60.0, labels={"node": "node-1"})
        
        metric = collector.get_metric("cpu_usage", labels={"node": "node-1"})
        
        assert metric is not None
        assert metric.value == 60.0
    
    def test_histogram_recording(self):
        """Test histogram metric recording."""
        collector = MetricsCollector()
        
        collector.record_histogram("response_time", 100.0)
        collector.record_histogram("response_time", 150.0)
        
        metric = collector.get_metric("response_time")
        
        assert metric is not None
        assert metric.value == 150.0
    
    def test_get_all_metrics(self):
        """Test getting all metrics."""
        collector = MetricsCollector()
        
        collector.record_gauge("cpu", 50.0)
        collector.record_gauge("memory", 60.0)
        
        metrics = collector.get_all_metrics()
        
        assert len(metrics) == 2


class TestPerformanceMonitor:
    """Test performance monitoring operations."""
    
    def test_response_time_recording(self):
        """Test response time recording."""
        monitor = PerformanceMonitor(window_size=60.0)
        
        monitor.record_response_time("/api", 100.0)
        monitor.record_response_time("/api", 150.0)
        monitor.record_response_time("/api", 200.0)
        
        avg = monitor.get_avg_response_time("/api")
        
        assert avg == 150.0
    
    def test_response_time_percentiles(self):
        """Test response time percentile calculation."""
        monitor = PerformanceMonitor(window_size=60.0)
        
        for i in range(100):
            monitor.record_response_time("/api", float(i * 10))
        
        p95 = monitor.get_p95_response_time("/api")
        p99 = monitor.get_p99_response_time("/api")
        
        assert p95 >= 940.0  # 95th percentile of 0-990
        assert p99 >= 980.0  # 99th percentile of 0-990
    
    def test_throughput_tracking(self):
        """Test throughput tracking."""
        monitor = PerformanceMonitor(window_size=60.0)
        
        for _ in range(100):
            monitor.record_request("/api")
        
        throughput = monitor.get_throughput("/api")
        
        assert throughput == 100
    
    def test_response_time_window(self):
        """Test response time window expiration."""
        monitor = PerformanceMonitor(window_size=0.1)  # 100ms window
        
        monitor.record_response_time("/api", 100.0)
        time.sleep(0.15)
        monitor.record_response_time("/api", 200.0)
        
        avg = monitor.get_avg_response_time("/api")
        
        # Should only include the 200ms response
        assert avg == 200.0


class TestResourceMonitor:
    """Test resource monitoring operations."""
    
    def test_cpu_usage_update(self):
        """Test CPU usage update."""
        monitor = ResourceMonitor()
        
        monitor.update_cpu_usage("node-1", 50.0)
        
        usage = monitor.get_cpu_usage("node-1")
        
        assert usage == 50.0
    
    def test_memory_usage_update(self):
        """Test memory usage update."""
        monitor = ResourceMonitor()
        
        monitor.update_memory_usage("node-1", 75.0)
        
        usage = monitor.get_memory_usage("node-1")
        
        assert usage == 75.0
    
    def test_network_usage_update(self):
        """Test network usage update."""
        monitor = ResourceMonitor()
        
        monitor.update_network_usage("node-1", 1000.0, 500.0)
        
        inbound, outbound = monitor.get_network_usage("node-1")
        
        assert inbound == 1000.0
        assert outbound == 500.0
    
    def test_all_resources(self):
        """Test getting all resources for node."""
        monitor = ResourceMonitor()
        
        monitor.update_cpu_usage("node-1", 50.0)
        monitor.update_memory_usage("node-1", 75.0)
        monitor.update_disk_usage("node-1", 60.0)
        monitor.update_network_usage("node-1", 1000.0, 500.0)
        
        resources = monitor.get_all_resources("node-1")
        
        assert resources["cpu"] == 50.0
        assert resources["memory"] == 75.0
        assert resources["disk"] == 60.0
        assert resources["network_in"] == 1000.0
        assert resources["network_out"] == 500.0


class TestAlertManager:
    """Test alert management operations."""
    
    def test_alert_rule_addition(self):
        """Test alert rule addition."""
        manager = AlertManager()
        
        manager.add_alert_rule("cpu_usage", "critical", 90.0)
        
        assert "cpu_usage" in manager._alert_rules
    
    def test_alert_triggering(self):
        """Test alert triggering when threshold exceeded."""
        manager = AlertManager()
        
        manager.add_alert_rule("cpu_usage", "critical", 50.0)
        
        metrics = {"cpu_usage": 60.0}
        alerts = manager.check_alerts(metrics)
        
        assert len(alerts) == 1
        assert alerts[0].alert_type == "cpu_usage"
        assert alerts[0].severity == "critical"
    
    def test_alert_acknowledgment(self):
        """Test alert acknowledgment."""
        manager = AlertManager()
        
        manager.add_alert_rule("cpu_usage", "critical", 50.0)
        metrics = {"cpu_usage": 60.0}
        manager.check_alerts(metrics)
        
        alert_id = list(manager._alerts.keys())[0]
        result = manager.acknowledge_alert(alert_id)
        
        assert result is True
        assert manager.get_alert(alert_id).acknowledged is True
    
    def test_alert_resolution(self):
        """Test alert resolution."""
        manager = AlertManager()
        
        manager.add_alert_rule("cpu_usage", "critical", 50.0)
        metrics = {"cpu_usage": 60.0}
        manager.check_alerts(metrics)
        
        alert_id = list(manager._alerts.keys())[0]
        result = manager.resolve_alert(alert_id)
        
        assert result is True
        assert manager.get_alert(alert_id).resolved is True
    
    def test_get_active_alerts(self):
        """Test getting active alerts."""
        manager = AlertManager()
        
        manager.add_alert_rule("cpu_usage", "critical", 50.0)
        manager.add_alert_rule("memory_usage", "warning", 80.0)
        
        metrics = {"cpu_usage": 60.0, "memory_usage": 90.0}
        manager.check_alerts(metrics)
        
        active = manager.get_active_alerts()
        
        assert len(active) == 2
    
    def test_clear_resolved_alerts(self):
        """Test clearing resolved alerts."""
        manager = AlertManager()
        
        manager.add_alert_rule("cpu_usage", "critical", 50.0)
        metrics = {"cpu_usage": 60.0}
        manager.check_alerts(metrics)
        
        alert_id = list(manager._alerts.keys())[0]
        manager.resolve_alert(alert_id)
        
        count = manager.clear_resolved_alerts()
        
        assert count == 1
        assert len(manager._alerts) == 0


class TestDashboardAggregator:
    """Test dashboard aggregation operations."""
    
    def test_node_data_update(self):
        """Test node data update."""
        aggregator = DashboardAggregator()
        
        data = {"cpu": 50.0, "memory": 60.0}
        aggregator.update_node_data("node-1", data)
        
        retrieved = aggregator.get_node_data("node-1")
        
        assert retrieved is not None
        assert retrieved["cpu"] == 50.0
    
    def test_cluster_summary(self):
        """Test cluster summary generation."""
        aggregator = DashboardAggregator()
        
        aggregator.update_node_data("node-1", {"cpu": 50.0, "memory": 60.0})
        aggregator.update_node_data("node-2", {"cpu": 70.0, "memory": 80.0})
        aggregator.update_node_data("node-3", {"cpu": 90.0, "memory": 100.0})
        
        summary = aggregator.get_cluster_summary()
        
        assert summary["total_nodes"] == 3
        assert summary["avg_cpu"] == 70.0
        assert summary["avg_memory"] == 80.0
        assert summary["max_cpu"] == 90.0
        assert summary["max_memory"] == 100.0
    
    def test_empty_cluster_summary(self):
        """Test cluster summary with no nodes."""
        aggregator = DashboardAggregator()
        
        summary = aggregator.get_cluster_summary()
        
        assert summary == {}


class TestMonitoringIntegration:
    """Test integration of monitoring components."""
    
    def test_full_monitoring_pipeline(self):
        """Test complete monitoring pipeline."""
        collector = MetricsCollector()
        monitor = PerformanceMonitor()
        resource = ResourceMonitor()
        alerts = AlertManager()
        dashboard = DashboardAggregator()
        
        # Simulate node data
        collector.record_counter("requests", 100, labels={"node": "node-1"})
        collector.record_gauge("cpu_usage", 50.0, labels={"node": "node-1"})
        collector.record_gauge("memory_usage", 75.0, labels={"node": "node-1"})
        
        resource.update_cpu_usage("node-1", 50.0)
        resource.update_memory_usage("node-1", 75.0)
        
        monitor.record_response_time("/api", 100.0)
        monitor.record_request("/api")
        
        # Update dashboard
        data = {
            "cpu": resource.get_cpu_usage("node-1"),
            "memory": resource.get_memory_usage("node-1"),
            "requests": collector.get_counter("requests", labels={"node": "node-1"}),
        }
        dashboard.update_node_data("node-1", data)
        
        # Check alerts
        metrics = {
            "cpu_usage": resource.get_cpu_usage("node-1"),
            "memory_usage": resource.get_memory_usage("node-1"),
        }
        alerts.add_alert_rule("cpu_usage", "critical", 90.0)
        alerts.add_alert_rule("memory_usage", "critical", 95.0)
        alerts.check_alerts(metrics)
        
        # Verify
        assert dashboard.get_node_data("node-1") is not None
        assert len(alerts.get_active_alerts()) == 0  # No alerts triggered


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
