"""
Task Service
Business logic for task management
"""
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from models.task import Task, TaskStatus, TaskType, RiskLevel
from models.agent import Agent
from models.audit_log import AuditAction
from services.governance_engine import GovernanceEngine
from services.anomaly_detector import AnomalyDetector
from services.audit_service import AuditService


class TaskService:
    """
    Service for managing AI agent tasks with integrated
    governance and anomaly detection.
    """
    
    def __init__(self, db: Session):
        """
        Initialize task service with dependencies.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.governance_engine = GovernanceEngine(db)
        self.anomaly_detector = AnomalyDetector()
        self.audit_service = AuditService(db)
    
    def create_task(
        self,
        agent_id: str,
        task_type: str,
        title: str,
        description: str = None,
        input_data: Dict = None,
        estimated_duration: int = None,
        user_id: str = None,
        ip_address: str = None
    ) -> Tuple[Task, Dict]:
        """
        Create a new task with governance evaluation and risk assessment.
        
        Args:
            agent_id: ID of the executing agent
            task_type: Type of task
            title: Task title
            description: Task description
            input_data: Input parameters as dictionary
            estimated_duration: Estimated task duration in seconds
            user_id: User creating the task
            ip_address: Client IP address
        
        Returns:
            Tuple of (created task, evaluation results)
        """
        # Validate agent exists and is active
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
        
        if agent.status.value != "active":
            raise ValueError(f"Agent is not active: {agent.status.value}")
        
        # Include estimated_duration in input_data for evaluation
        if input_data is None:
            input_data = {}
        if estimated_duration:
            input_data["estimated_execution_time"] = estimated_duration
        
        # Create task
        task = Task(
            agent_id=agent_id,
            task_type=TaskType(task_type) if task_type in [t.value for t in TaskType] else TaskType.OTHER,
            title=title,
            description=description,
            input_data=json.dumps(input_data) if input_data else None,
            status=TaskStatus.PENDING,
            estimated_duration=estimated_duration
        )
        
        self.db.add(task)
        self.db.flush()  # Get task ID
        
        # Get historical data for the agent
        historical_data = self._get_agent_historical_data(agent_id)
        
        # Perform risk assessment
        risk_score, risk_level, risk_analysis = self.anomaly_detector.calculate_risk_score(
            task, agent, historical_data
        )
        
        task.risk_score = risk_score
        task.risk_level = risk_level
        
        # Log anomaly if detected
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            self.audit_service.log_action(
                action=AuditAction.ANOMALY_DETECTED,
                entity_type="task",
                entity_id=task.id,
                task_id=task.id,
                agent_id=agent_id,
                user_id=user_id,
                details={
                    "risk_score": risk_score,
                    "risk_level": risk_level.value,
                    "analysis": risk_analysis
                },
                ip_address=ip_address,
                severity="warning" if risk_level == RiskLevel.HIGH else "critical"
            )
        
        # Evaluate governance rules
        governance_status, triggered_rules = self.governance_engine.evaluate_task(task, agent)
        
        # Apply governance decision
        self.governance_engine.apply_governance_decision(task, governance_status, triggered_rules)
        
        # Log task creation
        self.audit_service.log_task_action(
            task=task,
            action=AuditAction.TASK_CREATED,
            user_id=user_id,
            details={
                "task_type": task.task_type.value,
                "risk_score": risk_score,
                "risk_level": risk_level.value,
                "governance_status": governance_status
            },
            ip_address=ip_address
        )
        
        # Update agent activity
        agent.update_last_active()
        
        self.db.commit()
        
        evaluation_results = {
            "risk_assessment": {
                "score": risk_score,
                "level": risk_level.value,
                "analysis": risk_analysis
            },
            "governance": {
                "status": governance_status,
                "triggered_rules": triggered_rules
            }
        }
        
        return task, evaluation_results
    
    def start_task(self, task_id: str, user_id: str = None) -> Task:
        """
        Start task execution.
        
        Args:
            task_id: ID of the task to start
            user_id: User initiating the start
        
        Returns:
            Updated task
        """
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        if task.status != TaskStatus.PENDING and task.status != TaskStatus.APPROVED:
            raise ValueError(f"Cannot start task in status: {task.status.value}")
        
        task.start_execution()
        
        self.audit_service.log_task_action(
            task=task,
            action=AuditAction.TASK_STARTED,
            user_id=user_id
        )
        
        self.db.commit()
        return task
    
    def complete_task(
        self,
        task_id: str,
        output_data: Dict = None,
        user_id: str = None
    ) -> Task:
        """
        Mark task as completed.
        
        Args:
            task_id: ID of the task
            output_data: Task output
            user_id: User completing the task
        
        Returns:
            Updated task
        """
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        task.complete_execution(json.dumps(output_data) if output_data else None)
        
        self.audit_service.log_task_action(
            task=task,
            action=AuditAction.TASK_COMPLETED,
            user_id=user_id,
            details={
                "execution_time_ms": task.execution_time_ms
            }
        )
        
        self.db.commit()
        return task
    
    def fail_task(
        self,
        task_id: str,
        error_message: str,
        user_id: str = None
    ) -> Task:
        """
        Mark task as failed.
        
        Args:
            task_id: ID of the task
            error_message: Error description
            user_id: User marking the failure
        
        Returns:
            Updated task
        """
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        task.fail_execution(error_message)
        
        self.audit_service.log_task_action(
            task=task,
            action=AuditAction.TASK_FAILED,
            user_id=user_id,
            details={"error": error_message}
        )
        
        self.db.commit()
        return task
    
    def approve_task(
        self,
        task_id: str,
        reviewer: str,
        notes: str = None
    ) -> Task:
        """
        Approve a flagged task for execution.
        
        Args:
            task_id: ID of the task
            reviewer: Reviewer username/ID
            notes: Review notes
        
        Returns:
            Updated task
        """
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        if task.status != TaskStatus.FLAGGED:
            raise ValueError(f"Task is not flagged for review: {task.status.value}")
        
        task.approve(reviewer, notes)
        
        self.audit_service.log_task_action(
            task=task,
            action=AuditAction.TASK_APPROVED,
            user_id=reviewer,
            details={"review_notes": notes}
        )
        
        self.db.commit()
        return task
    
    def reject_task(
        self,
        task_id: str,
        reviewer: str,
        reason: str
    ) -> Task:
        """
        Reject a flagged task.
        
        Args:
            task_id: ID of the task
            reviewer: Reviewer username/ID
            reason: Rejection reason
        
        Returns:
            Updated task
        """
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        task.status = TaskStatus.REJECTED
        task.reviewed_by = reviewer
        task.reviewed_at = datetime.utcnow()
        task.review_notes = reason
        
        self.audit_service.log_task_action(
            task=task,
            action=AuditAction.TASK_REJECTED,
            user_id=reviewer,
            details={"rejection_reason": reason}
        )
        
        self.db.commit()
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        return self.db.query(Task).filter(Task.id == task_id).first()
    
    def get_tasks(
        self,
        agent_id: str = None,
        status: str = None,
        risk_level: str = None,
        task_type: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Task]:
        """
        Query tasks with filters.
        
        Args:
            agent_id: Filter by agent ID
            status: Filter by status
            risk_level: Filter by risk level
            task_type: Filter by task type
            start_date: Filter by creation date (after)
            end_date: Filter by creation date (before)
            limit: Maximum results
            offset: Pagination offset
        
        Returns:
            List of matching tasks
        """
        query = self.db.query(Task)
        
        if agent_id:
            query = query.filter(Task.agent_id == agent_id)
        
        if status:
            query = query.filter(Task.status == TaskStatus(status))
        
        if risk_level:
            query = query.filter(Task.risk_level == RiskLevel(risk_level))
        
        if task_type:
            query = query.filter(Task.task_type == TaskType(task_type))
        
        if start_date:
            query = query.filter(Task.created_at >= start_date)
        
        if end_date:
            query = query.filter(Task.created_at <= end_date)
        
        return query.order_by(desc(Task.created_at)).offset(offset).limit(limit).all()
    
    def get_flagged_tasks(self, limit: int = 50) -> List[Task]:
        """Get tasks awaiting review"""
        return self.db.query(Task).filter(
            Task.status == TaskStatus.FLAGGED
        ).order_by(desc(Task.created_at)).limit(limit).all()
    
    def get_task_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get task statistics for the specified period.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with task statistics
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        tasks = self.db.query(Task).filter(Task.created_at >= start_date).all()
        
        # Status breakdown
        status_counts = {}
        for task in tasks:
            status = task.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Risk level breakdown
        risk_counts = {}
        for task in tasks:
            risk = task.risk_level.value
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
        
        # Average execution time (for completed tasks)
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
        
        return {
            "period_days": days,
            "total_tasks": len(tasks),
            "status_breakdown": status_counts,
            "risk_breakdown": risk_counts,
            "average_execution_time_ms": round(avg_execution_time, 2),
            "average_risk_score": round(avg_risk_score, 3),
            "blocked_count": status_counts.get("blocked", 0),
            "flagged_count": status_counts.get("flagged", 0),
            "completion_rate": round(
                status_counts.get("completed", 0) / max(len(tasks), 1) * 100, 2
            )
        }
    
    def _get_agent_historical_data(self, agent_id: str) -> Dict[str, Any]:
        """
        Get historical data for an agent for risk assessment.
        
        Args:
            agent_id: Agent ID
        
        Returns:
            Dictionary with historical metrics
        """
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        
        # Tasks in last hour
        recent_tasks = self.db.query(Task).filter(
            Task.agent_id == agent_id,
            Task.created_at >= one_hour_ago
        ).all()
        
        # Tasks in last day
        daily_tasks = self.db.query(Task).filter(
            Task.agent_id == agent_id,
            Task.created_at >= one_day_ago
        ).all()
        
        # Calculate metrics
        tasks_per_hour = len(recent_tasks)
        
        failed_count = sum(1 for t in daily_tasks if t.status == TaskStatus.FAILED)
        recent_failure_rate = failed_count / max(len(daily_tasks), 1)
        
        # Calculate pattern deviation (simplified)
        if daily_tasks:
            avg_risk = sum(t.risk_score for t in daily_tasks) / len(daily_tasks)
            recent_avg_risk = (
                sum(t.risk_score for t in recent_tasks) / len(recent_tasks)
                if recent_tasks else avg_risk
            )
            pattern_deviation = abs(recent_avg_risk - avg_risk)
        else:
            pattern_deviation = 0.0
        
        return {
            "tasks_per_hour": tasks_per_hour,
            "recent_failure_rate": recent_failure_rate,
            "pattern_deviation": pattern_deviation
        }
