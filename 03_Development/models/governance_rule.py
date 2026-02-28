"""
Governance Rule Model
Defines rules for AI agent behavior governance
"""
from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer
from sqlalchemy import Enum as SQLEnum
from datetime import datetime
import uuid
import enum

from models.database import Base


class RuleType(enum.Enum):
    """Types of governance rules"""
    TASK_TYPE_RESTRICTION = "task_type_restriction"
    EXECUTION_TIME_LIMIT = "execution_time_limit"
    RESOURCE_ACCESS = "resource_access"
    DATA_SENSITIVITY = "data_sensitivity"
    OPERATION_RESTRICTION = "operation_restriction"
    RISK_THRESHOLD = "risk_threshold"
    AGENT_TRUST_LEVEL = "agent_trust_level"
    TIME_BASED = "time_based"
    RATE_LIMIT = "rate_limit"
    COMPLIANCE = "compliance"


class RuleAction(enum.Enum):
    """Actions to take when rule is triggered"""
    ALLOW = "allow"
    BLOCK = "block"
    FLAG = "flag"
    ESCALATE = "escalate"
    LOG_ONLY = "log_only"
    REQUIRE_APPROVAL = "require_approval"


class RuleSeverity(enum.Enum):
    """Severity level of the rule"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GovernanceRule(Base):
    """
    Governance Rule entity defining policies for AI agent behavior.
    
    Rules are evaluated against tasks to determine if they should
    be allowed, blocked, flagged, or escalated.
    
    Attributes:
        id: Unique rule identifier
        name: Human-readable rule name
        description: Detailed rule description
        rule_type: Category of the rule
        condition: JSON expression defining when rule triggers
        action: What to do when rule is triggered
        severity: Importance level of the rule
        is_active: Whether rule is currently enforced
        priority: Order of rule evaluation (lower = higher priority)
        created_by: User who created the rule
        applies_to_agents: Comma-separated agent IDs (null = all)
        applies_to_task_types: Comma-separated task types (null = all)
    """
    __tablename__ = "governance_rules"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Rule Definition
    rule_type = Column(SQLEnum(RuleType), nullable=False)
    condition = Column(Text, nullable=False)  # JSON condition expression
    action = Column(SQLEnum(RuleAction), default=RuleAction.FLAG)
    severity = Column(SQLEnum(RuleSeverity), default=RuleSeverity.MEDIUM)
    
    # Configuration
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=100)  # Lower number = higher priority
    
    # Scope
    applies_to_agents = Column(Text, nullable=True)  # Comma-separated agent IDs
    applies_to_task_types = Column(Text, nullable=True)  # Comma-separated types
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    
    # Versioning
    version = Column(Integer, default=1)
    effective_from = Column(DateTime, default=datetime.utcnow)
    effective_until = Column(DateTime, nullable=True)
    
    # Action Configuration
    action_config = Column(Text, nullable=True)  # JSON for action parameters
    notification_config = Column(Text, nullable=True)  # JSON for notifications
    
    def __repr__(self):
        return f"<GovernanceRule(id={self.id}, name={self.name}, type={self.rule_type.value})>"
    
    def to_dict(self):
        """Convert rule to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "rule_type": self.rule_type.value,
            "condition": self.condition,
            "action": self.action.value,
            "severity": self.severity.value,
            "is_active": self.is_active,
            "priority": self.priority,
            "applies_to_agents": self.applies_to_agents,
            "applies_to_task_types": self.applies_to_task_types,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "version": self.version,
            "effective_from": self.effective_from.isoformat() if self.effective_from else None,
            "effective_until": self.effective_until.isoformat() if self.effective_until else None,
            "action_config": self.action_config,
            "notification_config": self.notification_config
        }
    
    def is_applicable_to_agent(self, agent_id: str) -> bool:
        """Check if rule applies to a specific agent"""
        if not self.applies_to_agents:
            return True
        agent_ids = [aid.strip() for aid in self.applies_to_agents.split(",")]
        return agent_id in agent_ids
    
    def is_applicable_to_task_type(self, task_type: str) -> bool:
        """Check if rule applies to a specific task type"""
        if not self.applies_to_task_types:
            return True
        task_types = [tt.strip() for tt in self.applies_to_task_types.split(",")]
        return task_type in task_types
    
    def is_currently_effective(self) -> bool:
        """Check if rule is currently in effect"""
        now = datetime.utcnow()
        if self.effective_from and now < self.effective_from:
            return False
        if self.effective_until and now > self.effective_until:
            return False
        return self.is_active
