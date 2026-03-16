"""
AI Agent Model
Represents AI agents that perform tasks in the system
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
import uuid
import enum

from models.database import Base
from utils.time_utils import utc_now


class AgentType(enum.Enum):
    """Types of AI agents"""
    CODE_GENERATOR = "code_generator"
    CODE_REVIEWER = "code_reviewer"
    TEST_RUNNER = "test_runner"
    DOCUMENTATION = "documentation"
    MONITORING = "monitoring"
    DEPLOYMENT = "deployment"
    DATA_ANALYST = "data_analyst"
    GENERAL = "general"


class AgentStatus(enum.Enum):
    """Agent operational status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    UNDER_REVIEW = "under_review"


class Agent(Base):
    """
    AI Agent entity representing autonomous agents in the system.
    
    Attributes:
        id: Unique identifier for the agent
        name: Human-readable name of the agent
        agent_type: Category/type of the agent
        description: Detailed description of agent's purpose
        status: Current operational status
        capabilities: JSON list of agent capabilities
        created_at: Timestamp of agent registration
        last_active_at: Last activity timestamp
        is_trusted: Whether agent has elevated trust level
        owner: Owner/creator of the agent
    """
    __tablename__ = "agents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True)
    agent_type = Column(SQLEnum(AgentType), default=AgentType.GENERAL)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(AgentStatus), default=AgentStatus.ACTIVE)
    capabilities = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    last_active_at = Column(DateTime, nullable=True)
    is_trusted = Column(Boolean, default=False)
    owner = Column(String(255), nullable=True)
    version = Column(String(50), default="1.0.0")
    
    # Relationships
    tasks = relationship("Task", back_populates="agent", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Agent(id={self.id}, name={self.name}, type={self.agent_type.value})>"
    
    def to_dict(self):
        """Convert agent to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "agent_type": self.agent_type.value,
            "description": self.description,
            "status": self.status.value,
            "capabilities": self.capabilities,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_active_at": self.last_active_at.isoformat() if self.last_active_at else None,
            "is_trusted": self.is_trusted,
            "owner": self.owner,
            "version": self.version
        }
    
    def update_last_active(self):
        """Update last active timestamp"""
        self.last_active_at = utc_now()
    
    def suspend(self):
        """Suspend the agent"""
        self.status = AgentStatus.SUSPENDED
    
    def activate(self):
        """Activate the agent"""
        self.status = AgentStatus.ACTIVE
