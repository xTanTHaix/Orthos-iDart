"""
Cluster Configuration Test Suite - Tests for cluster configuration management

Tests cover:
- Configuration loading and validation
- Configuration updates
- Configuration persistence
- Configuration schema validation
- Multi-environment configurations
"""

import pytest
import json
import os
import tempfile
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Environment(Enum):
    """Environment types."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class NodeRole(Enum):
    """Node roles."""
    MASTER = "master"
    WORKER = "worker"
    STANDBY = "standby"
    GATEWAY = "gateway"


@dataclass
class NodeConfig:
    """Configuration for a single node."""
    node_id: str
    role: NodeRole = NodeRole.WORKER
    host: str = "localhost"
    port: int = 8000
    heartbeat_interval: float = 1.0
    timeout: float = 5.0
    max_retries: int = 3
    cpu_cores: int = 1
    memory_gb: float = 1.0
    storage_gb: float = 100.0
    enabled: bool = True


@dataclass
class ClusterConfig:
    """Configuration for the entire cluster."""
    cluster_id: str = ""
    environment: Environment = Environment.DEVELOPMENT
    node_count: int = 1
    master_nodes: List[str] = field(default_factory=list)
    worker_nodes: List[str] = field(default_factory=list)
    standby_nodes: List[str] = field(default_factory=list)
    gateway_nodes: List[str] = field(default_factory=list)
    replication_factor: int = 1
    consensus_timeout: float = 5.0
    leader_lease_timeout: float = 10.0
    max_message_size: int = 10485760  # 10MB
    enable_compression: bool = True
    enable_encryption: bool = False
    encryption_key: Optional[str] = None
    logging_level: str = "INFO"
    metrics_interval: float = 60.0
    health_check_interval: float = 30.0
    auto_scaling: bool = False
    max_nodes: int = 10
    min_nodes: int = 1
    heartbeat_interval: float = 1.0


@dataclass
class StorageConfig:
    """Configuration for storage."""
    type: str = "local"  # local, s3, gcs, azure
    path: str = "./data"
    max_size_gb: float = 100.0
    cleanup_threshold: float = 0.8
    compression: bool = True
    encryption: bool = False
    backup_enabled: bool = True
    backup_interval_hours: int = 24


@dataclass
class NetworkConfig:
    """Configuration for network."""
    bind_address: str = "0.0.0.0"
    port: int = 8000
    tls_enabled: bool = False
    tls_cert_path: Optional[str] = None
    tls_key_path: Optional[str] = None
    max_connections: int = 1000
    connection_timeout: float = 30.0
    read_timeout: float = 60.0
    write_timeout: float = 60.0


class ErrorList(list):
    """List of error strings supporting substring 'in' checks."""
    def __contains__(self, item: Any) -> bool:
        if super().__contains__(item):
            return True
        if isinstance(item, str):
            return any(item in err for err in self)
        return False


class ConfigValidator:
    """Validates cluster configuration."""
    
    def __init__(self):
        self._errors: ErrorList = ErrorList()
    
    def validate_cluster_config(self, config: ClusterConfig) -> bool:
        """Validate cluster configuration."""
        self._errors.clear()
        
        # Check required fields
        if not config.cluster_id:
            self._errors.append("cluster_id is required")
        
        if not config.environment:
            self._errors.append("environment is required")
        
        # Check node counts
        if config.node_count <= 0:
            self._errors.append("node_count must be positive")
        
        if config.node_count > config.max_nodes:
            self._errors.append(f"node_count ({config.node_count}) exceeds max_nodes ({config.max_nodes})")
        
        # Check master nodes
        if config.master_nodes:
            if len(config.master_nodes) < 1:
                self._errors.append("At least one master node is required")
            if len(config.master_nodes) > 1:
                self._errors.append("Only one master node is allowed")
        
        # Check timeouts
        if config.consensus_timeout <= 0:
            self._errors.append("consensus_timeout must be positive")
        
        if config.leader_lease_timeout <= 0:
            self._errors.append("leader_lease_timeout must be positive")
        
        # Check message size
        if config.max_message_size <= 0:
            self._errors.append("max_message_size must be positive")
        
        # Check intervals
        if config.metrics_interval <= 0:
            self._errors.append("metrics_interval must be positive")
        
        if config.health_check_interval <= 0:
            self._errors.append("health_check_interval must be positive")
        
        return len(self._errors) == 0
    
    def get_errors(self) -> ErrorList:
        """Get validation errors."""
        return ErrorList(self._errors)
    
    def clear_errors(self) -> None:
        """Clear validation errors."""
        self._errors.clear()


class ConfigLoader:
    """Loads configuration from various sources."""
    
    def __init__(self):
        self._config: Optional[ClusterConfig] = None
        self._storage: Optional[StorageConfig] = None
        self._network: Optional[NetworkConfig] = None
    
    def load_from_dict(self, data: Dict) -> bool:
        """Load configuration from dictionary."""
        try:
            self._config = ClusterConfig(**data)
            return True
        except Exception as e:
            return False
    
    def load_from_json(self, filepath: str) -> bool:
        """Load configuration from JSON file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            return self.load_from_dict(data)
        except Exception:
            return False
    
    def load_from_env(self, env_prefix: str = "CLUSTER_") -> bool:
        """Load configuration from environment variables."""
        try:
            config_data = {}
            
            # Load cluster config
            config_data['cluster_id'] = os.getenv(f"{env_prefix}CLUSTER_ID", "")
            env_str = os.getenv(f"{env_prefix}ENVIRONMENT", "development")
            try:
                config_data['environment'] = Environment(env_str)
            except Exception:
                config_data['environment'] = Environment.DEVELOPMENT
            
            # Load node config
            config_data['node_count'] = int(
                os.getenv(f"{env_prefix}NODE_COUNT", "1")
            )
            self._config = ClusterConfig(**config_data)
            
            # Load storage config
            storage_data = {
                'type': os.getenv(f"{env_prefix}STORAGE_TYPE", "local"),
                'path': os.getenv(f"{env_prefix}STORAGE_PATH", "./data"),
                'max_size_gb': float(
                    os.getenv(f"{env_prefix}STORAGE_MAX_SIZE_GB", "100.0")
                ),
            }
            self._storage = StorageConfig(**storage_data)
            
            # Load network config
            network_data = {
                'bind_address': os.getenv(f"{env_prefix}BIND_ADDRESS", "0.0.0.0"),
                'port': int(os.getenv(f"{env_prefix}PORT", "8000")),
                'tls_enabled': os.getenv(f"{env_prefix}TLS_ENABLED", "false").lower() == "true",
            }
            self._network = NetworkConfig(**network_data)
            
            return True
        except Exception:
            return False
    
    def get_config(self) -> Optional[ClusterConfig]:
        """Get loaded configuration."""
        return self._config
    
    def get_storage_config(self) -> Optional[StorageConfig]:
        """Get storage configuration."""
        return self._storage
    
    def get_network_config(self) -> Optional[NetworkConfig]:
        """Get network configuration."""
        return self._network


class ConfigPersister:
    """Persists configuration to storage."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self._lock = __import__('threading').RLock()  # RLock allows re-entrant acquisition by same thread
    
    def save_config(self, config: ClusterConfig) -> bool:
        """Save configuration to file."""
        try:
            with self._lock:
                data = {
                    'cluster_id': config.cluster_id,
                    'environment': config.environment.value if hasattr(config.environment, 'value') else str(config.environment),
                    'node_count': config.node_count,
                    'master_nodes': config.master_nodes,
                    'worker_nodes': config.worker_nodes,
                    'standby_nodes': config.standby_nodes,
                    'gateway_nodes': config.gateway_nodes,
                    'replication_factor': config.replication_factor,
                    'consensus_timeout': config.consensus_timeout,
                    'leader_lease_timeout': config.leader_lease_timeout,
                    'max_message_size': config.max_message_size,
                    'enable_compression': config.enable_compression,
                    'enable_encryption': config.enable_encryption,
                    'logging_level': config.logging_level,
                    'metrics_interval': config.metrics_interval,
                    'health_check_interval': config.health_check_interval,
                    'auto_scaling': config.auto_scaling,
                    'max_nodes': config.max_nodes,
                    'min_nodes': config.min_nodes,
                }
                
                with open(self.filepath, 'w') as f:
                    json.dump(data, f, indent=2)
                
                return True
        except Exception:
            return False
    
    def load_config(self) -> Optional[ClusterConfig]:
        """Load configuration from file."""
        try:
            with self._lock:
                if not os.path.exists(self.filepath):
                    return None
                
                with open(self.filepath, 'r') as f:
                    data = json.load(f)
                if 'environment' in data and isinstance(data['environment'], str):
                    try:
                        data['environment'] = Environment(data['environment'])
                    except Exception:
                        pass
                return ClusterConfig(**data)
        except Exception:
            return None
    
    def update_config(self, updates: Dict) -> bool:
        """Update configuration with partial data."""
        try:
            with self._lock:
                current = self.load_config()
                if not current:
                    return False
                
                # Merge updates
                for key, value in updates.items():
                    if hasattr(current, key):
                        setattr(current, key, value)
                
                return self.save_config(current)
        except Exception:
            return False


class TestConfigValidator:
    """Test configuration validation."""
    
    def test_valid_config(self):
        """Test valid configuration passes validation."""
        validator = ConfigValidator()
        
        config = ClusterConfig(
            cluster_id="test-cluster",
            environment=Environment.DEVELOPMENT,
            node_count=3,
            master_nodes=["node-1"],
            worker_nodes=["node-2", "node-3"],
            consensus_timeout=5.0,
            leader_lease_timeout=10.0,
            max_message_size=10485760,
            metrics_interval=60.0,
            health_check_interval=30.0,
            max_nodes=10,
            min_nodes=1
        )
        
        result = validator.validate_cluster_config(config)
        
        assert result is True
        assert len(validator.get_errors()) == 0
    
    def test_missing_cluster_id(self):
        """Test validation fails without cluster_id."""
        validator = ConfigValidator()
        
        config = ClusterConfig(
            environment=Environment.DEVELOPMENT,
            node_count=3
        )
        
        result = validator.validate_cluster_config(config)
        
        assert result is False
        assert "cluster_id is required" in validator.get_errors()
    
    def test_invalid_node_count(self):
        """Test validation fails with invalid node count."""
        validator = ConfigValidator()
        
        config = ClusterConfig(
            cluster_id="test-cluster",
            environment=Environment.DEVELOPMENT,
            node_count=0
        )
        
        result = validator.validate_cluster_config(config)
        
        assert result is False
        assert "node_count must be positive" in validator.get_errors()
    
    def test_exceeds_max_nodes(self):
        """Test validation fails when exceeding max nodes."""
        validator = ConfigValidator()
        
        config = ClusterConfig(
            cluster_id="test-cluster",
            environment=Environment.DEVELOPMENT,
            node_count=15,
            max_nodes=10
        )
        
        result = validator.validate_cluster_config(config)
        
        assert result is False
        assert "exceeds max_nodes" in validator.get_errors()
    
    def test_multiple_master_nodes(self):
        """Test validation fails with multiple master nodes."""
        validator = ConfigValidator()
        
        config = ClusterConfig(
            cluster_id="test-cluster",
            environment=Environment.DEVELOPMENT,
            node_count=3,
            master_nodes=["node-1", "node-2"],
            max_nodes=10
        )
        
        result = validator.validate_cluster_config(config)
        
        assert result is False
        assert "Only one master node" in validator.get_errors()
    
    def test_negative_timeout(self):
        """Test validation fails with negative timeout."""
        validator = ConfigValidator()
        
        config = ClusterConfig(
            cluster_id="test-cluster",
            environment=Environment.DEVELOPMENT,
            node_count=3,
            consensus_timeout=-1.0,
            max_nodes=10
        )
        
        result = validator.validate_cluster_config(config)
        
        assert result is False
        assert "consensus_timeout must be positive" in validator.get_errors()


class TestConfigLoader:
    """Test configuration loading."""
    
    def test_load_from_dict(self):
        """Test loading from dictionary."""
        loader = ConfigLoader()
        
        data = {
            'cluster_id': "test-cluster",
            'environment': 'development',
            'node_count': 3,
            'master_nodes': ['node-1'],
            'worker_nodes': ['node-2', 'node-3'],
            'consensus_timeout': 5.0,
            'leader_lease_timeout': 10.0,
            'max_message_size': 10485760,
            'metrics_interval': 60.0,
            'health_check_interval': 30.0,
            'max_nodes': 10,
            'min_nodes': 1
        }
        
        result = loader.load_from_dict(data)
        
        assert result is True
        assert loader.get_config() is not None
        assert loader.get_config().cluster_id == "test-cluster"
    
    def test_load_invalid_dict(self):
        """Test loading invalid dictionary fails."""
        loader = ConfigLoader()
        
        data = {
            'cluster_id': "test-cluster",
            'invalid_field': "value"
        }
        
        result = loader.load_from_dict(data)
        
        assert result is False
        assert loader.get_config() is None
    
    def test_load_from_json(self, tmp_path):
        """Test loading from JSON file."""
        loader = ConfigLoader()
        
        config_path = tmp_path / "config.json"
        data = {
            'cluster_id': "json-cluster",
            'environment': 'testing',
            'node_count': 5,
            'master_nodes': ['node-1'],
            'worker_nodes': ['node-2', 'node-3', 'node-4', 'node-5'],
            'consensus_timeout': 3.0,
            'leader_lease_timeout': 5.0,
            'max_message_size': 5242880,
            'metrics_interval': 30.0,
            'health_check_interval': 15.0,
            'max_nodes': 10,
            'min_nodes': 2
        }
        
        with open(config_path, 'w') as f:
            json.dump(data, f)
        
        result = loader.load_from_json(str(config_path))
        
        assert result is True
        assert loader.get_config().cluster_id == "json-cluster"
    
    def test_load_from_env(self):
        """Test loading from environment variables."""
        loader = ConfigLoader()
        
        # Set environment variables
        os.environ['CLUSTER_CLUSTER_ID'] = 'env-cluster'
        os.environ['CLUSTER_ENVIRONMENT'] = 'staging'
        os.environ['CLUSTER_NODE_COUNT'] = '4'
        os.environ['CLUSTER_PORT'] = '9000'
        
        result = loader.load_from_env()
        
        assert result is True
        assert loader.get_config() is not None
        assert loader.get_config().cluster_id == 'env-cluster'
        assert loader.get_network_config().port == 9000
    
    def test_load_nonexistent_file(self):
        """Test loading nonexistent file fails."""
        loader = ConfigLoader()
        
        result = loader.load_from_json("/nonexistent/path/config.json")
        
        assert result is False


class TestConfigPersister:
    """Test configuration persistence."""
    
    def test_save_config(self, tmp_path):
        """Test saving configuration to file."""
        persister = ConfigPersister(str(tmp_path / "config.json"))
        
        config = ClusterConfig(
            cluster_id="persist-cluster",
            environment=Environment.PRODUCTION,
            node_count=5,
            master_nodes=["node-1"],
            worker_nodes=["node-2", "node-3", "node-4", "node-5"],
            consensus_timeout=5.0,
            leader_lease_timeout=10.0,
            max_message_size=10485760,
            metrics_interval=60.0,
            health_check_interval=30.0,
            max_nodes=10,
            min_nodes=2
        )
        
        result = persister.save_config(config)
        
        assert result is True
        assert os.path.exists(str(tmp_path / "config.json"))
    
    def test_load_config(self, tmp_path):
        """Test loading configuration from file."""
        persister = ConfigPersister(str(tmp_path / "config.json"))
        
        config = ClusterConfig(
            cluster_id="load-cluster",
            environment=Environment.STAGING,
            node_count=3,
            master_nodes=["node-1"],
            worker_nodes=["node-2", "node-3"],
            consensus_timeout=5.0,
            leader_lease_timeout=10.0,
            max_message_size=10485760,
            metrics_interval=60.0,
            health_check_interval=30.0,
            max_nodes=10,
            min_nodes=1
        )
        
        persister.save_config(config)
        loaded = persister.load_config()
        
        assert loaded is not None
        assert loaded.cluster_id == "load-cluster"
        assert loaded.environment == Environment.STAGING
    
    def test_load_nonexistent_file(self):
        """Test loading nonexistent file returns None."""
        persister = ConfigPersister("/nonexistent/path/config.json")
        
        result = persister.load_config()
        
        assert result is None
    
    def test_update_config(self, tmp_path):
        """Test updating configuration."""
        persister = ConfigPersister(str(tmp_path / "config.json"))
        
        # Save initial config
        persister.save_config(ClusterConfig(
            cluster_id="update-cluster",
            environment=Environment.DEVELOPMENT,
            node_count=3,
            master_nodes=["node-1"],
            worker_nodes=["node-2", "node-3"],
            consensus_timeout=5.0,
            leader_lease_timeout=10.0,
            max_message_size=10485760,
            metrics_interval=60.0,
            health_check_interval=30.0,
            max_nodes=10,
            min_nodes=1
        ))
        
        # Update node count
        result = persister.update_config({'node_count': 5})
        
        assert result is True
        
        # Load and verify
        loaded = persister.load_config()
        assert loaded.node_count == 5
    
    def test_update_nonexistent_config(self, tmp_path):
        """Test updating nonexistent configuration fails."""
        persister = ConfigPersister(str(tmp_path / "config.json"))
        
        result = persister.update_config({'node_count': 5})
        
        assert result is False


class TestMultiEnvironmentConfig:
    """Test multi-environment configuration management."""
    
    def test_different_environments(self):
        """Test configuration for different environments."""
        environments = [
            (Environment.DEVELOPMENT, 1, 10, 0.1, 1.0),
            (Environment.TESTING, 5, 50, 0.5, 2.0),
            (Environment.STAGING, 10, 100, 1.0, 4.0),
            (Environment.PRODUCTION, 20, 200, 5.0, 10.0),
        ]
        
        for env, min_nodes, max_nodes, timeout, heartbeat in environments:
            config = ClusterConfig(
                cluster_id=f"cluster-{env.value}",
                environment=env,
                node_count=10,
                min_nodes=min_nodes,
                max_nodes=max_nodes,
                consensus_timeout=timeout,
                heartbeat_interval=heartbeat,
            )
            
            validator = ConfigValidator()
            result = validator.validate_cluster_config(config)
            
            assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
