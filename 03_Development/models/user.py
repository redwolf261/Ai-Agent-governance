"""
User Model
System users who interact with the governance platform
"""
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy import Enum as SQLEnum
from datetime import datetime
import uuid
import enum
import bcrypt

from models.database import Base


class UserRole(enum.Enum):
    """User roles in the system"""
    ADMIN = "admin"
    AUDITOR = "auditor"
    ENGINEER = "engineer"
    MANAGER = "manager"
    VIEWER = "viewer"


class User(Base):
    """
    User entity for system access control.
    
    Attributes:
        id: Unique user identifier
        username: Login username
        email: User email address
        password_hash: Hashed password
        full_name: User's full name
        role: User role for access control
        is_active: Whether account is active
        last_login: Last login timestamp
    """
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Security
    failed_login_attempts = Column(String(10), default="0")
    locked_until = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role.value})>"
    
    def to_dict(self):
        """Convert user to dictionary (excluding password)"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role.value,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }
    
    def set_password(self, password: str):
        """Hash and set the password"""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        """Verify password against stored hash"""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
    
    def has_permission(self, required_role: UserRole) -> bool:
        """Check if user has required role or higher"""
        role_hierarchy = {
            UserRole.VIEWER: 0,
            UserRole.ENGINEER: 1,
            UserRole.MANAGER: 2,
            UserRole.AUDITOR: 3,
            UserRole.ADMIN: 4
        }
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(required_role, 0)
