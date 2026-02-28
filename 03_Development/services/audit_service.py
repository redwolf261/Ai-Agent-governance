"""
Audit Service
Comprehensive logging and audit trail management
"""
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from models.audit_log import AuditLog, AuditAction, create_audit_log
from models.task import Task
from models.agent import Agent


class AuditService:
    """
    Service for managing audit logs and generating compliance reports.
    
    Provides comprehensive logging of all system activities for
    regulatory compliance and operational monitoring.
    """
    
    def __init__(self, db: Session):
        """
        Initialize audit service with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def log_action(
        self,
        action: AuditAction,
        entity_type: str,
        entity_id: str = None,
        task_id: str = None,
        user_id: str = None,
        agent_id: str = None,
        details: Dict = None,
        old_value: Any = None,
        new_value: Any = None,
        ip_address: str = None,
        severity: str = "info",
        category: str = None
    ) -> AuditLog:
        """
        Log an auditable action.
        
        Args:
            action: The action type to log
            entity_type: Type of entity affected
            entity_id: ID of the entity
            task_id: Related task ID
            user_id: User performing the action
            agent_id: Agent involved
            details: Additional details as dictionary
            old_value: Previous state (for updates)
            new_value: New state (for updates)
            ip_address: Client IP address
            severity: Log severity level
            category: Log category
        
        Returns:
            Created AuditLog instance
        """
        audit_log = create_audit_log(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            task_id=task_id,
            user_id=user_id,
            agent_id=agent_id,
            details=json.dumps(details) if details else None,
            old_value=json.dumps(old_value) if old_value else None,
            new_value=json.dumps(new_value) if new_value else None,
            ip_address=ip_address,
            severity=severity,
            category=category
        )
        
        self.db.add(audit_log)
        self.db.commit()
        
        return audit_log
    
    def log_task_action(
        self,
        task: Task,
        action: AuditAction,
        user_id: str = None,
        details: Dict = None,
        ip_address: str = None
    ) -> AuditLog:
        """
        Log a task-related action.
        
        Args:
            task: The task being logged
            action: The action type
            user_id: User performing action
            details: Additional details
            ip_address: Client IP
        
        Returns:
            Created AuditLog instance
        """
        severity = "info"
        if action in [AuditAction.TASK_BLOCKED, AuditAction.TASK_FAILED]:
            severity = "warning"
        elif action == AuditAction.TASK_FLAGGED:
            severity = "warning"
        
        return self.log_action(
            action=action,
            entity_type="task",
            entity_id=task.id,
            task_id=task.id,
            agent_id=task.agent_id,
            user_id=user_id,
            details=details or {
                "task_type": task.task_type.value,
                "title": task.title,
                "status": task.status.value,
                "risk_level": task.risk_level.value
            },
            ip_address=ip_address,
            severity=severity,
            category="task_execution"
        )
    
    def log_agent_action(
        self,
        agent: Agent,
        action: AuditAction,
        user_id: str = None,
        details: Dict = None,
        old_value: Any = None,
        new_value: Any = None,
        ip_address: str = None
    ) -> AuditLog:
        """
        Log an agent-related action.
        """
        return self.log_action(
            action=action,
            entity_type="agent",
            entity_id=agent.id,
            agent_id=agent.id,
            user_id=user_id,
            details=details or {
                "agent_name": agent.name,
                "agent_type": agent.agent_type.value,
                "status": agent.status.value
            },
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            severity="info",
            category="agent_management"
        )
    
    def get_audit_logs(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        action: AuditAction = None,
        entity_type: str = None,
        entity_id: str = None,
        agent_id: str = None,
        user_id: str = None,
        severity: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """
        Query audit logs with filters.
        
        Args:
            start_date: Filter logs after this date
            end_date: Filter logs before this date
            action: Filter by action type
            entity_type: Filter by entity type
            entity_id: Filter by entity ID
            agent_id: Filter by agent ID
            user_id: Filter by user ID
            severity: Filter by severity level
            limit: Maximum number of results
            offset: Pagination offset
        
        Returns:
            List of matching AuditLog instances
        """
        query = self.db.query(AuditLog)
        
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        if action:
            query = query.filter(AuditLog.action == action)
        
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        
        if entity_id:
            query = query.filter(AuditLog.entity_id == entity_id)
        
        if agent_id:
            query = query.filter(AuditLog.agent_id == agent_id)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        if severity:
            query = query.filter(AuditLog.severity == severity)
        
        return query.order_by(desc(AuditLog.timestamp)).offset(offset).limit(limit).all()
    
    def get_task_audit_trail(self, task_id: str) -> List[AuditLog]:
        """
        Get complete audit trail for a specific task.
        
        Args:
            task_id: The task ID to get audit trail for
        
        Returns:
            List of AuditLog entries for the task
        """
        return self.db.query(AuditLog).filter(
            AuditLog.task_id == task_id
        ).order_by(AuditLog.timestamp).all()
    
    def get_agent_audit_trail(self, agent_id: str) -> List[AuditLog]:
        """
        Get complete audit trail for a specific agent.
        
        Args:
            agent_id: The agent ID to get audit trail for
        
        Returns:
            List of AuditLog entries for the agent
        """
        return self.db.query(AuditLog).filter(
            AuditLog.agent_id == agent_id
        ).order_by(desc(AuditLog.timestamp)).all()
    
    def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Generate a compliance report for the specified period.
        
        Args:
            start_date: Report start date
            end_date: Report end date
        
        Returns:
            Dictionary containing compliance metrics and summaries
        """
        # Get all logs in period
        logs = self.get_audit_logs(
            start_date=start_date,
            end_date=end_date,
            limit=10000
        )
        
        # Calculate metrics
        total_events = len(logs)
        
        # Group by action
        action_counts = {}
        for log in logs:
            action_name = log.action.value
            action_counts[action_name] = action_counts.get(action_name, 0) + 1
        
        # Group by severity
        severity_counts = {}
        for log in logs:
            severity_counts[log.severity] = severity_counts.get(log.severity, 0) + 1
        
        # Task execution summary
        task_logs = [l for l in logs if l.entity_type == "task"]
        task_created = sum(1 for l in task_logs if l.action == AuditAction.TASK_CREATED)
        task_completed = sum(1 for l in task_logs if l.action == AuditAction.TASK_COMPLETED)
        task_failed = sum(1 for l in task_logs if l.action == AuditAction.TASK_FAILED)
        task_blocked = sum(1 for l in task_logs if l.action == AuditAction.TASK_BLOCKED)
        task_flagged = sum(1 for l in task_logs if l.action == AuditAction.TASK_FLAGGED)
        
        # Governance violations
        governance_violations = sum(
            1 for l in logs 
            if l.action in [AuditAction.TASK_BLOCKED, AuditAction.RULE_TRIGGERED]
        )
        
        # Anomaly detections
        anomaly_detections = sum(
            1 for l in logs 
            if l.action == AuditAction.ANOMALY_DETECTED
        )
        
        # User activity summary
        user_logins = sum(1 for l in logs if l.action == AuditAction.USER_LOGIN)
        
        return {
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_events": total_events,
                "governance_violations": governance_violations,
                "anomaly_detections": anomaly_detections
            },
            "task_execution": {
                "total_created": task_created,
                "completed": task_completed,
                "failed": task_failed,
                "blocked": task_blocked,
                "flagged": task_flagged,
                "completion_rate": round(task_completed / max(task_created, 1) * 100, 2)
            },
            "action_breakdown": action_counts,
            "severity_breakdown": severity_counts,
            "user_activity": {
                "total_logins": user_logins
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def get_risk_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Get a summary of risk-related events.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with risk summary metrics
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get high-severity events
        high_severity_logs = self.db.query(AuditLog).filter(
            and_(
                AuditLog.timestamp >= start_date,
                AuditLog.severity.in_(["warning", "error", "critical"])
            )
        ).all()
        
        # Group by day
        daily_risks = {}
        for log in high_severity_logs:
            day_key = log.timestamp.strftime("%Y-%m-%d")
            if day_key not in daily_risks:
                daily_risks[day_key] = {"warning": 0, "error": 0, "critical": 0}
            daily_risks[day_key][log.severity] += 1
        
        return {
            "period_days": days,
            "total_risk_events": len(high_severity_logs),
            "daily_breakdown": daily_risks,
            "most_common_actions": self._get_top_actions(high_severity_logs, 5)
        }
    
    def _get_top_actions(self, logs: List[AuditLog], n: int) -> List[Dict]:
        """Get top N most common actions from logs"""
        action_counts = {}
        for log in logs:
            action_name = log.action.value
            action_counts[action_name] = action_counts.get(action_name, 0) + 1
        
        sorted_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"action": a, "count": c} for a, c in sorted_actions[:n]]
    
    def export_audit_logs(
        self,
        start_date: datetime,
        end_date: datetime,
        format: str = "json"
    ) -> str:
        """
        Export audit logs for the specified period.
        
        Args:
            start_date: Export start date
            end_date: Export end date
            format: Export format (json or csv)
        
        Returns:
            Exported data as string
        """
        logs = self.get_audit_logs(
            start_date=start_date,
            end_date=end_date,
            limit=100000
        )
        
        if format == "json":
            return json.dumps([log.to_dict() for log in logs], indent=2)
        elif format == "csv":
            if not logs:
                return "No logs found"
            
            headers = list(logs[0].to_dict().keys())
            lines = [",".join(headers)]
            
            for log in logs:
                values = [str(v).replace(",", ";") for v in log.to_dict().values()]
                lines.append(",".join(values))
            
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported format: {format}")
