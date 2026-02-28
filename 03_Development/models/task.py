"""
Task Model
Represents tasks executed by AI agents
"""
from sqlalchemy import Column, String, DateTime, Text, Float, ForeignKey, Integer
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from models.database import Base


class TaskStatus(enum.Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    FLAGGED = "flagged"
    APPROVED = "approved"
    REJECTED = "rejected"


class RiskLevel(enum.Enum):
    """Risk level classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskType(enum.Enum):
    """Types of tasks AI agents can perform"""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    MONITORING = "monitoring"
    DEPLOYMENT = "deployment"
    DATA_ANALYSIS = "data_analysis"
    FILE_OPERATION = "file_operation"
    API_CALL = "api_call"
    DATABASE_QUERY = "database_query"
    SYSTEM_COMMAND = "system_command"
    OTHER = "other"


class Task(Base):
    """
    Task entity representing actions performed by AI agents.
    
    Attributes:
        id: Unique task identifier
        agent_id: Reference to the executing agent
        task_type: Category of the task
        title: Brief title of the task
        description: Detailed description
        input_data: Input parameters (JSON)
        output_data: Task output/result (JSON)
        status: Current execution status
        risk_level: Assessed risk level
        risk_score: Numerical risk score (0.0 - 1.0)
        started_at: Execution start time
        completed_at: Execution end time
        execution_time_ms: Duration in milliseconds
        decision_rationale: Explanation of agent's decision
        governance_status: Governance rule evaluation result
    """
    __tablename__ = "tasks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=False)
    task_type = Column(SQLEnum(TaskType), default=TaskType.OTHER)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Input/Output
    input_data = Column(Text, nullable=True)  # JSON string
    output_data = Column(Text, nullable=True)  # JSON string
    
    # Status & Risk
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING)
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.LOW)
    risk_score = Column(Float, default=0.0)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    estimated_duration = Column(Integer, nullable=True)  # Estimated duration in seconds
    
    # Decision Tracking
    decision_rationale = Column(Text, nullable=True)
    governance_status = Column(String(50), default="pending")  # approved, blocked, flagged
    governance_notes = Column(Text, nullable=True)
    
    # Review
    reviewed_by = Column(String(255), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)
    
    # Relationships
    agent = relationship("Agent", back_populates="tasks")
    audit_logs = relationship("AuditLog", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Task(id={self.id}, type={self.task_type.value}, status={self.status.value})>"
    
    def to_dict(self):
        """Convert task to dictionary"""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "task_type": self.task_type.value,
            "title": self.title,
            "description": self.description,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "status": self.status.value,
            "risk_level": self.risk_level.value,
            "risk_score": self.risk_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "execution_time_ms": self.execution_time_ms,
            "decision_rationale": self.decision_rationale,
            "governance_status": self.governance_status,
            "governance_notes": self.governance_notes,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "review_notes": self.review_notes
        }
    
    def start_execution(self):
        """Mark task as started"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()
    
    def complete_execution(self, output_data: str = None):
        """Mark task as completed"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        if output_data:
            self.output_data = output_data
        if self.started_at:
            delta = self.completed_at - self.started_at
            self.execution_time_ms = int(delta.total_seconds() * 1000)
    
    def fail_execution(self, error_message: str = None):
        """Mark task as failed"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        if error_message:
            self.output_data = f'{{"error": "{error_message}"}}'
    
    def flag_for_review(self, reason: str = None):
        """Flag task for human review"""
        self.status = TaskStatus.FLAGGED
        self.governance_status = "flagged"
        if reason:
            self.governance_notes = reason
    
    def block_execution(self, reason: str = None):
        """Block task execution"""
        self.status = TaskStatus.BLOCKED
        self.governance_status = "blocked"
        if reason:
            self.governance_notes = reason
    
    def approve(self, reviewer: str, notes: str = None):
        """Approve task after review"""
        self.status = TaskStatus.APPROVED
        self.governance_status = "approved"
        self.reviewed_by = reviewer
        self.reviewed_at = datetime.utcnow()
        if notes:
            self.review_notes = notes
