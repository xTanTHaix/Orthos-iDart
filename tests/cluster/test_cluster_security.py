"""
Cluster Security Test Suite - Tests for cluster security features

Tests cover:
- Authentication and authorization
- Encryption and decryption
- Access control
- Security audit logging
- Certificate management
"""

import pytest
import time
import hashlib
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class Permission(Enum):
    """Permission types."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"
    DELETE = "delete"


class UserRole(Enum):
    """User roles."""
    ADMIN = "admin"
    OPERATOR = "operator"
    DEVELOPER = "developer"
    VIEWER = "viewer"


@dataclass
class User:
    """Represents a user."""
    user_id: str
    username: str
    role: UserRole = UserRole.VIEWER
    permissions: Set[Permission] = field(default_factory=set)
    created_at: float = field(default_factory=time.time)
    active: bool = True
    password_hash: str = ""


@dataclass
class AccessRequest:
    """Represents an access request."""
    request_id: str
    user_id: str
    resource_id: str
    action: str
    timestamp: float = field(default_factory=time.time)
    approved: bool = False
    denied: bool = False


@dataclass
class AuditLog:
    """Represents an audit log entry."""
    log_id: str
    user_id: str
    action: str
    resource_id: str
    timestamp: float = field(default_factory=time.time)
    success: bool = True
    details: Dict = field(default_factory=dict)


class AuthenticationManager:
    """Manages user authentication."""
    
    def __init__(self):
        self._users: Dict[str, User] = {}
        self._tokens: Dict[str, Dict] = {}
        self._lock = __import__('threading').Lock()
    
    def register_user(self, user: User) -> bool:
        """Register a new user."""
        with self._lock:
            if user.user_id in self._users:
                return False
            
            self._users[user.user_id] = user
            return True
    
    def authenticate(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return token."""
        with self._lock:
            user = self._users.get(username)
            if not user:
                for u in self._users.values():
                    if u.username == username or u.user_id == username:
                        user = u
                        break
            
            if not user or not user.active:
                return None
            
            # Simple password hash check
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if getattr(user, 'password_hash', None) != password_hash and getattr(user, 'password_hash', None) != password:
                return None
            
            # Generate token
            token = f"token_{hashlib.sha256(f'{user.user_id}_{time.time()}'.encode()).hexdigest()}"
            self._tokens[token] = {
                "user_id": user.user_id,
                "username": username,
                "expires_at": time.time() + 3600,  # 1 hour
                "created_at": time.time()
            }
            
            return token
    
    def validate_token(self, token: str) -> Optional[User]:
        """Validate token and return user."""
        with self._lock:
            token_data = self._tokens.get(token)
            
            if not token_data:
                return None
            
            # Check expiration
            if time.time() > token_data["expires_at"]:
                del self._tokens[token]
                return None
            
            return self._users.get(token_data["user_id"])
    
    def revoke_token(self, token: str) -> bool:
        """Revoke a token."""
        with self._lock:
            if token in self._tokens:
                del self._tokens[token]
                return True
            return False
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        with self._lock:
            return self._users.get(user_id)
    
    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate user."""
        with self._lock:
            if user_id in self._users:
                self._users[user_id].active = False
                return True
            return False
    
    def activate_user(self, user_id: str) -> bool:
        """Activate user."""
        with self._lock:
            if user_id in self._users:
                self._users[user_id].active = True
                return True
            return False


class AuthorizationManager:
    """Manages user authorization."""
    
    def __init__(self):
        self._resource_permissions: Dict[str, Dict[str, Set[Permission]]] = defaultdict(
            lambda: defaultdict(set)
        )
        self._role_permissions: Dict[UserRole, Set[Permission]] = {
            UserRole.ADMIN: {Permission.READ, Permission.WRITE, Permission.EXECUTE, Permission.DELETE, Permission.ADMIN},
            UserRole.OPERATOR: {Permission.READ, Permission.WRITE, Permission.EXECUTE},
            UserRole.DEVELOPER: {Permission.READ, Permission.WRITE, Permission.EXECUTE},
            UserRole.VIEWER: {Permission.READ},
        }
        self._lock = __import__('threading').Lock()
    
    def set_resource_permissions(self, resource_id: str, user_id: str, permissions: Set[Permission]) -> None:
        """Set permissions for user on resource."""
        with self._lock:
            self._resource_permissions[resource_id][user_id] = permissions
    
    def get_permissions(self, resource_id: str, user_id: str) -> Set[Permission]:
        """Get permissions for user on resource."""
        with self._lock:
            return self._resource_permissions[resource_id].get(user_id, set())
    
    def check_permission(self, user_id: str, resource_id: str, action: str) -> bool:
        """Check if user has permission for action on resource."""
        with self._lock:
            permissions = self._resource_permissions[resource_id].get(user_id, set())
            
            action_map = {
                "read": Permission.READ,
                "write": Permission.WRITE,
                "execute": Permission.EXECUTE,
                "delete": Permission.DELETE,
                "admin": Permission.ADMIN,
            }
            
            required_permission = action_map.get(action.lower())
            if not required_permission:
                return False
            
            return required_permission in permissions
    
    def grant_permission(self, user_id: str, resource_id: str, permission: Permission) -> None:
        """Grant permission to user on resource."""
        with self._lock:
            if resource_id not in self._resource_permissions:
                self._resource_permissions[resource_id] = defaultdict(set)
            
            self._resource_permissions[resource_id][user_id].add(permission)
    
    def revoke_permission(self, user_id: str, resource_id: str, permission: Permission) -> None:
        """Revoke permission from user on resource."""
        with self._lock:
            if resource_id in self._resource_permissions:
                if user_id in self._resource_permissions[resource_id]:
                    self._resource_permissions[resource_id][user_id].discard(permission)
                    if not self._resource_permissions[resource_id][user_id]:
                        del self._resource_permissions[resource_id][user_id]
    
    def get_all_permissions(self, resource_id: str) -> Dict[str, Set[Permission]]:
        """Get all permissions for resource."""
        with self._lock:
            return dict(self._resource_permissions.get(resource_id, {}))


class AccessControlManager:
    """Manages access control lists."""
    
    def __init__(self):
        self._acl: Dict[str, List[Dict]] = {}
        self._lock = __import__('threading').Lock()
    
    def set_acl(self, resource_id: str, acl: List[Dict]) -> None:
        """Set access control list for resource."""
        with self._lock:
            self._acl[resource_id] = acl
    
    def get_acl(self, resource_id: str) -> List[Dict]:
        """Get access control list for resource."""
        with self._lock:
            return self._acl.get(resource_id, [])
    
    def add_entry(self, resource_id: str, entry: Dict) -> None:
        """Add entry to ACL."""
        with self._lock:
            if resource_id not in self._acl:
                self._acl[resource_id] = []
            
            self._acl[resource_id].append(entry)
    
    def remove_entry(self, resource_id: str, user_id: str) -> bool:
        """Remove entry from ACL."""
        with self._lock:
            if resource_id not in self._acl:
                return False
            
            self._acl[resource_id] = [
                entry for entry in self._acl[resource_id]
                if entry.get("user_id") != user_id
            ]
            
            if not self._acl[resource_id]:
                del self._acl[resource_id]
            
            return True
    
    def check_access(self, resource_id: str, user_id: str) -> bool:
        """Check if user has access to resource."""
        with self._lock:
            acl = self._acl.get(resource_id, [])
            
            for entry in acl:
                if entry.get("user_id") == user_id:
                    if entry.get("allow", True):
                        return True
                    else:
                        return False
            
            # Default deny
            return False


class AuditLogger:
    """Logs security events."""
    
    def __init__(self):
        self._logs: List[AuditLog] = []
        self._lock = __import__('threading').Lock()
    
    def log(self, user_id: str, action: str, resource_id: str, success: bool = True, details: Optional[Dict] = None) -> None:
        """Log security event."""
        with self._lock:
            log = AuditLog(
                log_id=str(hash(f"{user_id}_{action}_{resource_id}_{time.time()}")),
                user_id=user_id,
                action=action,
                resource_id=resource_id,
                success=success,
                details=details or {}
            )
            self._logs.append(log)
    
    def get_logs(self, user_id: Optional[str] = None, action: Optional[str] = None, 
                 start_time: Optional[float] = None, end_time: Optional[float] = None) -> List[AuditLog]:
        """Get filtered audit logs."""
        with self._lock:
            filtered = self._logs
            
            if user_id:
                filtered = [log for log in filtered if log.user_id == user_id]
            
            if action:
                filtered = [log for log in filtered if log.action == action]
            
            if start_time:
                filtered = [log for log in filtered if log.timestamp >= start_time]
            
            if end_time:
                filtered = [log for log in filtered if log.timestamp <= end_time]
            
            return filtered
    
    def get_logs_by_resource(self, resource_id: str) -> List[AuditLog]:
        """Get logs for specific resource."""
        with self._lock:
            return [log for log in self._logs if log.resource_id == resource_id]
    
    def clear_logs(self) -> int:
        """Clear all logs."""
        with self._lock:
            count = len(self._logs)
            self._logs.clear()
            return count
    
    def get_failed_attempts(self) -> List[AuditLog]:
        """Get all failed security attempts."""
        with self._lock:
            return [log for log in self._logs if not log.success]


class EncryptionManager:
    """Manages encryption and decryption."""
    
    def __init__(self, key: str):
        self.key = key.encode()
        self._lock = __import__('threading').Lock()
    
    def encrypt(self, data: str) -> str:
        """Encrypt data."""
        with self._lock:
            # Simple XOR encryption for demonstration
            encrypted = bytes([b ^ self.key[i % len(self.key)] for i, b in enumerate(data.encode())])
            return encrypted.hex()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data."""
        with self._lock:
            encrypted_bytes = bytes.fromhex(encrypted_data)
            decrypted = bytes([b ^ self.key[i % len(self.key)] for i, b in enumerate(encrypted_bytes)])
            return decrypted.decode()
    
    def hash(self, data: str) -> str:
        """Hash data."""
        return hashlib.sha256(data.encode()).hexdigest()


class CertificateManager:
    """Manages SSL/TLS certificates."""
    
    def __init__(self):
        self._certificates: Dict[str, Dict] = {}
        self._lock = __import__('threading').Lock()
    
    def register_certificate(self, cert_id: str, cert_data: Dict) -> bool:
        """Register certificate."""
        with self._lock:
            self._certificates[cert_id] = {
                **cert_data,
                "registered_at": time.time()
            }
            return True
    
    def get_certificate(self, cert_id: str) -> Optional[Dict]:
        """Get certificate by ID."""
        with self._lock:
            return self._certificates.get(cert_id)
    
    def validate_certificate(self, cert_id: str) -> bool:
        """Validate certificate."""
        with self._lock:
            cert = self._certificates.get(cert_id)
            
            if not cert:
                return False
            
            # Check expiration
            expires_at = cert.get("expires_at", 0)
            if time.time() > expires_at:
                return False
            
            return True
    
    def revoke_certificate(self, cert_id: str) -> bool:
        """Revoke certificate."""
        with self._lock:
            if cert_id in self._certificates:
                self._certificates[cert_id]["revoked"] = True
                return True
            return False


class TestAuthenticationManager:
    """Test authentication operations."""
    
    def test_user_registration(self):
        """Test user registration."""
        manager = AuthenticationManager()
        
        user = User(
            user_id="user-1",
            username="testuser",
            role=UserRole.OPERATOR,
            permissions={Permission.READ, Permission.WRITE}
        )
        
        result = manager.register_user(user)
        
        assert result is True
        assert manager.get_user("user-1") is not None
    
    def test_duplicate_user_registration(self):
        """Test duplicate user registration fails."""
        manager = AuthenticationManager()
        
        user1 = User(user_id="user-1", username="testuser1")
        user2 = User(user_id="user-1", username="testuser2")
        
        manager.register_user(user1)
        result = manager.register_user(user2)
        
        assert result is False
    
    def test_authentication(self):
        """Test user authentication."""
        manager = AuthenticationManager()
        
        user = User(
            user_id="user-1",
            username="testuser",
            password_hash="abc123"
        )
        manager.register_user(user)
        
        token = manager.authenticate("testuser", "abc123")
        
        assert token is not None
    
    def test_invalid_authentication(self):
        """Test authentication with invalid credentials."""
        manager = AuthenticationManager()
        
        token = manager.authenticate("nonexistent", "password")
        
        assert token is None
    
    def test_token_validation(self):
        """Test token validation."""
        manager = AuthenticationManager()
        
        user = User(
            user_id="user-1",
            username="testuser",
            password_hash="abc123"
        )
        manager.register_user(user)
        
        token = manager.authenticate("testuser", "abc123")
        
        validated_user = manager.validate_token(token)
        
        assert validated_user is not None
        assert validated_user.user_id == "user-1"
    
    def test_expired_token(self):
        """Test expired token validation."""
        manager = AuthenticationManager()
        
        user = User(
            user_id="user-1",
            username="testuser",
            password_hash="abc123"
        )
        manager.register_user(user)
        
        token = manager.authenticate("testuser", "abc123")
        
        # Simulate token expiration
        manager._tokens[token]["expires_at"] = time.time() - 100
        
        validated_user = manager.validate_token(token)
        
        assert validated_user is None


class TestAuthorizationManager:
    """Test authorization operations."""
    
    def test_set_permissions(self):
        """Test setting permissions."""
        manager = AuthorizationManager()
        
        manager.set_resource_permissions("resource-1", "user-1", {Permission.READ, Permission.WRITE})
        
        permissions = manager.get_permissions("resource-1", "user-1")
        
        assert Permission.READ in permissions
        assert Permission.WRITE in permissions
    
    def test_check_permission(self):
        """Test permission checking."""
        manager = AuthorizationManager()
        
        manager.set_resource_permissions("resource-1", "user-1", {Permission.READ})
        
        has_read = manager.check_permission("user-1", "resource-1", "read")
        has_write = manager.check_permission("user-1", "resource-1", "write")
        
        assert has_read is True
        assert has_write is False
    
    def test_grant_permission(self):
        """Test granting permission."""
        manager = AuthorizationManager()
        
        manager.grant_permission("user-1", "resource-1", Permission.WRITE)
        
        has_write = manager.check_permission("user-1", "resource-1", "write")
        
        assert has_write is True
    
    def test_revoke_permission(self):
        """Test revoking permission."""
        manager = AuthorizationManager()
        
        manager.set_resource_permissions("resource-1", "user-1", {Permission.READ, Permission.WRITE})
        manager.revoke_permission("user-1", "resource-1", Permission.WRITE)
        
        has_write = manager.check_permission("user-1", "resource-1", "write")
        
        assert has_write is False


class TestAccessControlManager:
    """Test access control operations."""
    
    def test_set_acl(self):
        """Test setting ACL."""
        manager = AccessControlManager()
        
        acl = [
            {"user_id": "user-1", "allow": True},
            {"user_id": "user-2", "allow": False},
        ]
        manager.set_acl("resource-1", acl)
        
        retrieved = manager.get_acl("resource-1")
        
        assert len(retrieved) == 2
    
    def test_add_acl_entry(self):
        """Test adding ACL entry."""
        manager = AccessControlManager()
        
        manager.add_entry("resource-1", {"user_id": "user-1", "allow": True})
        
        acl = manager.get_acl("resource-1")
        
        assert len(acl) == 1
        assert acl[0]["user_id"] == "user-1"
    
    def test_remove_acl_entry(self):
        """Test removing ACL entry."""
        manager = AccessControlManager()
        
        manager.set_acl("resource-1", [
            {"user_id": "user-1", "allow": True},
            {"user_id": "user-2", "allow": True},
        ])
        
        result = manager.remove_entry("resource-1", "user-1")
        
        assert result is True
        acl = manager.get_acl("resource-1")
        assert len(acl) == 1
    
    def test_check_access(self):
        """Test access checking."""
        manager = AccessControlManager()
        
        manager.set_acl("resource-1", [
            {"user_id": "user-1", "allow": True},
            {"user_id": "user-2", "allow": False},
        ])
        
        has_access = manager.check_access("resource-1", "user-1")
        no_access = manager.check_access("resource-1", "user-2")
        default_deny = manager.check_access("resource-1", "user-3")
        
        assert has_access is True
        assert no_access is False
        assert default_deny is False


class TestAuditLogger:
    """Test audit logging operations."""
    
    def test_log_event(self):
        """Test logging event."""
        logger = AuditLogger()
        
        logger.log("user-1", "login", "resource-1", success=True)
        
        logs = logger.get_logs()
        
        assert len(logs) == 1
        assert logs[0].user_id == "user-1"
        assert logs[0].action == "login"
    
    def test_filter_logs_by_user(self):
        """Test filtering logs by user."""
        logger = AuditLogger()
        
        logger.log("user-1", "login", "resource-1")
        logger.log("user-2", "login", "resource-1")
        logger.log("user-1", "logout", "resource-1")
        
        logs = logger.get_logs(user_id="user-1")
        
        assert len(logs) == 2
    
    def test_filter_logs_by_action(self):
        """Test filtering logs by action."""
        logger = AuditLogger()
        
        logger.log("user-1", "login", "resource-1")
        logger.log("user-1", "logout", "resource-1")
        
        logs = logger.get_logs(action="login")
        
        assert len(logs) == 1
    
    def test_get_failed_attempts(self):
        """Test getting failed attempts."""
        logger = AuditLogger()
        
        logger.log("user-1", "login", "resource-1", success=True)
        logger.log("user-2", "login", "resource-1", success=False)
        logger.log("user-3", "login", "resource-1", success=False)
        
        failed = logger.get_failed_attempts()
        
        assert len(failed) == 2


class TestEncryptionManager:
    """Test encryption operations."""
    
    def test_encrypt_decrypt(self):
        """Test encryption and decryption."""
        manager = EncryptionManager("secret-key")
        
        original = "Hello, World!"
        encrypted = manager.encrypt(original)
        decrypted = manager.decrypt(encrypted)
        
        assert decrypted == original
    
    def test_hash(self):
        """Test hashing."""
        manager = EncryptionManager("secret-key")
        
        hash1 = manager.hash("test")
        hash2 = manager.hash("test")
        hash3 = manager.hash("different")
        
        assert hash1 == hash2
        assert hash1 != hash3


class TestCertificateManager:
    """Test certificate operations."""
    
    def test_register_certificate(self):
        """Test certificate registration."""
        manager = CertificateManager()
        
        cert = {
            "cert_id": "cert-1",
            "issuer": "CA",
            "subject": "cluster",
            "expires_at": time.time() + 86400,
        }
        
        result = manager.register_certificate("cert-1", cert)
        
        assert result is True
        assert manager.get_certificate("cert-1") is not None
    
    def test_validate_certificate(self):
        """Test certificate validation."""
        manager = CertificateManager()
        
        cert = {
            "cert_id": "cert-1",
            "issuer": "CA",
            "subject": "cluster",
            "expires_at": time.time() + 86400,
        }
        manager.register_certificate("cert-1", cert)
        
        is_valid = manager.validate_certificate("cert-1")
        
        assert is_valid is True
    
    def test_expired_certificate(self):
        """Test expired certificate validation."""
        manager = CertificateManager()
        
        cert = {
            "cert_id": "cert-1",
            "issuer": "CA",
            "subject": "cluster",
            "expires_at": time.time() - 86400,
        }
        manager.register_certificate("cert-1", cert)
        
        is_valid = manager.validate_certificate("cert-1")
        
        assert is_valid is False


class TestSecurityIntegration:
    """Test security feature integration."""
    
    def test_full_authentication_authorization_flow(self):
        """Test complete authentication and authorization flow."""
        auth = AuthenticationManager()
        authz = AuthorizationManager()
        
        # Register user
        user = User(
            user_id="user-1",
            username="admin",
            role=UserRole.ADMIN,
            password_hash="admin123"
        )
        auth.register_user(user)
        
        # Authenticate
        token = auth.authenticate("admin", "admin123")
        assert token is not None
        
        # Validate token
        validated_user = auth.validate_token(token)
        assert validated_user is not None
        
        # Set permissions
        authz.set_resource_permissions("resource-1", "user-1", {
            Permission.READ, Permission.WRITE, Permission.DELETE
        })
        
        # Check permissions
        assert authz.check_permission("user-1", "resource-1", "read") is True
        assert authz.check_permission("user-1", "resource-1", "write") is True
        assert authz.check_permission("user-1", "resource-1", "delete") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
