"""
Agent Service
Business logic for AI agent management
"""
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.agent import Agent, AgentType, AgentStatus
from models.task import Task, TaskStatus
from models.audit_log import AuditAction
from services.audit_service import AuditService


class AgentService:
    """
    Service for managing AI agents in the governance system.
    """
    
    def __init__(self, db: Session):
        """
        Initialize agent service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.audit_service = AuditService(db)
    
    def register_agent(
        self,
        name: str,
        agent_type: str,
        description: str = None,
        capabilities: List[str] = None,
        owner: str = None,
        is_trusted: bool = False,
        user_id: str = None,
        ip_address: str = None
    ) -> Agent:
        """
        Register a new AI agent in the system.
        
        Args:
            name: Agent name (must be unique)
            agent_type: Type of agent
            description: Agent description
            capabilities: List of agent capabilities
            owner: Owner/creator of the agent
            is_trusted: Whether agent should be trusted
            user_id: User registering the agent
            ip_address: Client IP
        
        Returns:
            Created Agent instance
        """
        # Check if name already exists
        existing = self.db.query(Agent).filter(Agent.name == name).first()
        if existing:
            raise ValueError(f"Agent with name '{name}' already exists")
        
        # Create agent
        agent = Agent(
            name=name,
            agent_type=AgentType(agent_type) if agent_type in [t.value for t in AgentType] else AgentType.GENERAL,
            description=description,
            capabilities=json.dumps(capabilities) if capabilities else None,
            owner=owner,
            is_trusted=is_trusted,
            status=AgentStatus.ACTIVE
        )
        
        self.db.add(agent)
        self.db.flush()
        
        # Log registration
        self.audit_service.log_agent_action(
            agent=agent,
            action=AuditAction.AGENT_REGISTERED,
            user_id=user_id,
            details={
                "agent_type": agent.agent_type.value,
                "is_trusted": is_trusted,
                "owner": owner
            },
            ip_address=ip_address
        )
        
        self.db.commit()
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID"""
        return self.db.query(Agent).filter(Agent.id == agent_id).first()
    
    def get_agent_by_name(self, name: str) -> Optional[Agent]:
        """Get agent by name"""
        return self.db.query(Agent).filter(Agent.name == name).first()
    
    def get_agents(
        self,
        status: str = None,
        agent_type: str = None,
        is_trusted: bool = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Agent]:
        """
        Query agents with filters.
        
        Args:
            status: Filter by status
            agent_type: Filter by type
            is_trusted: Filter by trust level
            limit: Maximum results
            offset: Pagination offset
        
        Returns:
            List of matching agents
        """
        query = self.db.query(Agent)
        
        if status:
            query = query.filter(Agent.status == AgentStatus(status))
        
        if agent_type:
            query = query.filter(Agent.agent_type == AgentType(agent_type))
        
        if is_trusted is not None:
            query = query.filter(Agent.is_trusted == is_trusted)
        
        return query.order_by(desc(Agent.created_at)).offset(offset).limit(limit).all()
    
    def update_agent(
        self,
        agent_id: str,
        updates: Dict[str, Any],
        user_id: str = None,
        ip_address: str = None
    ) -> Agent:
        """
        Update agent properties.
        
        Args:
            agent_id: Agent ID
            updates: Dictionary of fields to update
            user_id: User making the update
            ip_address: Client IP
        
        Returns:
            Updated agent
        """
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
        
        old_values = agent.to_dict()
        
        # Apply updates
        allowed_fields = ["name", "description", "capabilities", "owner", "is_trusted"]
        for field, value in updates.items():
            if field in allowed_fields:
                if field == "capabilities" and isinstance(value, list):
                    value = json.dumps(value)
                setattr(agent, field, value)
        
        # Log update
        self.audit_service.log_agent_action(
            agent=agent,
            action=AuditAction.AGENT_UPDATED,
            user_id=user_id,
            old_value=old_values,
            new_value=agent.to_dict(),
            ip_address=ip_address
        )
        
        self.db.commit()
        return agent
    
    def suspend_agent(
        self,
        agent_id: str,
        reason: str = None,
        user_id: str = None,
        ip_address: str = None
    ) -> Agent:
        """
        Suspend an agent from executing tasks.
        
        Args:
            agent_id: Agent ID
            reason: Suspension reason
            user_id: User suspending the agent
            ip_address: Client IP
        
        Returns:
            Updated agent
        """
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
        
        old_status = agent.status.value
        agent.suspend()
        
        self.audit_service.log_agent_action(
            agent=agent,
            action=AuditAction.AGENT_SUSPENDED,
            user_id=user_id,
            details={"reason": reason, "previous_status": old_status},
            ip_address=ip_address
        )
        
        self.db.commit()
        return agent
    
    def activate_agent(
        self,
        agent_id: str,
        user_id: str = None,
        ip_address: str = None
    ) -> Agent:
        """
        Activate a suspended agent.
        
        Args:
            agent_id: Agent ID
            user_id: User activating the agent
            ip_address: Client IP
        
        Returns:
            Updated agent
        """
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
        
        old_status = agent.status.value
        agent.activate()
        
        self.audit_service.log_agent_action(
            agent=agent,
            action=AuditAction.AGENT_ACTIVATED,
            user_id=user_id,
            details={"previous_status": old_status},
            ip_address=ip_address
        )
        
        self.db.commit()
        return agent
    
    def set_trust_level(
        self,
        agent_id: str,
        is_trusted: bool,
        user_id: str = None,
        ip_address: str = None
    ) -> Agent:
        """
        Set agent trust level.
        
        Args:
            agent_id: Agent ID
            is_trusted: New trust level
            user_id: User making the change
            ip_address: Client IP
        
        Returns:
            Updated agent
        """
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
        
        old_trust = agent.is_trusted
        agent.is_trusted = is_trusted
        
        self.audit_service.log_agent_action(
            agent=agent,
            action=AuditAction.AGENT_UPDATED,
            user_id=user_id,
            details={
                "field": "is_trusted",
                "old_value": old_trust,
                "new_value": is_trusted
            },
            ip_address=ip_address
        )
        
        self.db.commit()
        return agent
    
    def get_agent_statistics(self, agent_id: str, days: int = 7) -> Dict[str, Any]:
        """
        Get performance statistics for an agent.
        
        Args:
            agent_id: Agent ID
            days: Number of days to analyze
        
        Returns:
            Dictionary with agent statistics
        """
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        tasks = self.db.query(Task).filter(
            Task.agent_id == agent_id,
            Task.created_at >= start_date
        ).all()
        
        # Calculate metrics
        total_tasks = len(tasks)
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in tasks if t.status == TaskStatus.FAILED)
        blocked = sum(1 for t in tasks if t.status == TaskStatus.BLOCKED)
        flagged = sum(1 for t in tasks if t.status == TaskStatus.FLAGGED)
        
        # Average execution time
        completed_tasks = [t for t in tasks if t.execution_time_ms is not None]
        avg_execution_time = (
            sum(t.execution_time_ms for t in completed_tasks) / len(completed_tasks)
            if completed_tasks else 0
        )
        
        # Average risk score
        avg_risk_score = (
            sum(t.risk_score for t in tasks) / len(tasks)
            if tasks else 0
        )
        
        # Task type distribution
        type_counts = {}
        for task in tasks:
            task_type = task.task_type.value
            type_counts[task_type] = type_counts.get(task_type, 0) + 1
        
        return {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "period_days": days,
            "total_tasks": total_tasks,
            "completed": completed,
            "failed": failed,
            "blocked": blocked,
            "flagged": flagged,
            "success_rate": round(completed / max(total_tasks, 1) * 100, 2),
            "failure_rate": round(failed / max(total_tasks, 1) * 100, 2),
            "average_execution_time_ms": round(avg_execution_time, 2),
            "average_risk_score": round(avg_risk_score, 3),
            "task_type_distribution": type_counts
        }
    
    def get_all_agent_statistics(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get statistics for all active agents.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            List of agent statistics
        """
        agents = self.get_agents(status="active")
        return [self.get_agent_statistics(agent.id, days) for agent in agents]
