"""
Audit Log Model
Comprehensive logging of all system activities for compliance
"""
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from models.database import Base


class AuditAction(enum.Enum):
    """Types of auditable actions"""
    # Task Actions
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_FLAGGED = "task_flagged"
    TASK_BLOCKED = "task_blocked"
    TASK_APPROVED = "task_approved"
    TASK_REJECTED = "task_rejected"
    
    # Agent Actions
    AGENT_REGISTERED = "agent_registered"
    AGENT_ACTIVATED = "agent_activated"
    AGENT_SUSPENDED = "agent_suspended"
    AGENT_UPDATED = "agent_updated"
    
    # Governance Actions
    RULE_CREATED = "rule_created"
    RULE_UPDATED = "rule_updated"
    RULE_DELETED = "rule_deleted"
    RULE_TRIGGERED = "rule_triggered"
    
    # User Actions
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    
    # System Actions
    ANOMALY_DETECTED = "anomaly_detected"
    RISK_ASSESSED = "risk_assessed"
    ESCALATION_TRIGGERED = "escalation_triggered"
    SYSTEM_ERROR = "system_error"


class AuditLog(Base):
    """
    Audit Log entity for tracking all system activities.
    
    Provides comprehensive audit trail for compliance, security,
    and operational monitoring purposes.
    
    Attributes:
        id: Unique log entry identifier
        timestamp: When the action occurred
        action: Type of action performed
        entity_type: Type of entity affected (task, agent, user, etc.)
        entity_id: ID of the affected entity
        task_id: Reference to associated task (if applicable)
        user_id: User who performed the action (if applicable)
        agent_id: Agent involved (if applicable)
        details: JSON with action details
        ip_address: Source IP address
        user_agent: Client user agent string
        severity: Log severity level
    """
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    action = Column(SQLEnum(AuditAction), nullable=False)
    
    # Entity References
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(36), nullable=True)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=True)
    user_id = Column(String(36), nullable=True)
    agent_id = Column(String(36), nullable=True)
    
    # Details
    details = Column(Text, nullable=True)  # JSON string
    old_value = Column(Text, nullable=True)  # Previous state
    new_value = Column(Text, nullable=True)  # New state
    
    # Context
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(500), nullable=True)
    session_id = Column(String(100), nullable=True)
    
    # Classification
    severity = Column(String(20), default="info")  # info, warning, error, critical
    category = Column(String(50), nullable=True)
    
    # Relationships
    task = relationship("Task", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action.value}, timestamp={self.timestamp})>"
    
    def to_dict(self):
        """Convert audit log to dictionary"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "action": self.action.value,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "task_id": self.task_id,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "details": self.details,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "session_id": self.session_id,
            "severity": self.severity,
            "category": self.category
        }


def create_audit_log(
    action: AuditAction,
    entity_type: str,
    entity_id: str = None,
    task_id: str = None,
    user_id: str = None,
    agent_id: str = None,
    details: str = None,
    old_value: str = None,
    new_value: str = None,
    ip_address: str = None,
    severity: str = "info",
    category: str = None
) -> AuditLog:
    """
    Factory function to create an audit log entry.
    
    Args:
        action: The action being logged
        entity_type: Type of entity (task, agent, user, etc.)
        entity_id: ID of the entity
        task_id: Related task ID
        user_id: User performing the action
        agent_id: Agent involved
        details: JSON string with additional details
        old_value: Previous state (for updates)
        new_value: New state (for updates)
        ip_address: Client IP address
        severity: Log severity level
        category: Log category
    
    Returns:
        AuditLog instance (not yet committed to database)
    """
    return AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        task_id=task_id,
        user_id=user_id,
        agent_id=agent_id,
        details=details,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address,
        severity=severity,
        category=category
    )
