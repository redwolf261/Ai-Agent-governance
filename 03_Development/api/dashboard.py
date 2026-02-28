"""
Dashboard API Endpoints
Aggregated data for dashboard visualization
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from models.database import SessionLocal
from models.task import Task, TaskStatus, RiskLevel
from models.agent import Agent, AgentStatus
from models.audit_log import AuditLog, AuditAction
from models.governance_rule import GovernanceRule
from services.task_service import TaskService
from services.agent_service import AgentService
from services.audit_service import AuditService

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/summary', methods=['GET'])
def get_dashboard_summary():
    """
    Get dashboard summary with key metrics.
    
    Returns overview data for the main dashboard view.
    """
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)
        
        # Agent counts
        total_agents = db.query(Agent).count()
        active_agents = db.query(Agent).filter(Agent.status == AgentStatus.ACTIVE).count()
        
        # Task counts
        total_tasks = db.query(Task).count()
        tasks_today = db.query(Task).filter(Task.created_at >= today).count()
        tasks_week = db.query(Task).filter(Task.created_at >= week_ago).count()
        
        # Task status breakdown (last 7 days)
        task_status_counts = db.query(
            Task.status, func.count(Task.id)
        ).filter(
            Task.created_at >= week_ago
        ).group_by(Task.status).all()
        
        status_breakdown = {status.value: count for status, count in task_status_counts}
        
        # Risk level breakdown (last 7 days)
        risk_counts = db.query(
            Task.risk_level, func.count(Task.id)
        ).filter(
            Task.created_at >= week_ago
        ).group_by(Task.risk_level).all()
        
        risk_breakdown = {level.value: count for level, count in risk_counts}
        
        # Pending reviews
        flagged_count = db.query(Task).filter(Task.status == TaskStatus.FLAGGED).count()
        
        # Active governance rules
        active_rules = db.query(GovernanceRule).filter(GovernanceRule.is_active == True).count()
        
        # Recent violations (blocked + flagged tasks)
        violations_week = db.query(Task).filter(
            Task.created_at >= week_ago,
            Task.status.in_([TaskStatus.BLOCKED, TaskStatus.FLAGGED])
        ).count()
        
        # High risk alerts (critical + high risk tasks today)
        high_risk_today = db.query(Task).filter(
            Task.created_at >= today,
            Task.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL])
        ).count()
        
        return jsonify({
            "success": True,
            "data": {
                "agents": {
                    "total": total_agents,
                    "active": active_agents
                },
                "tasks": {
                    "total": total_tasks,
                    "today": tasks_today,
                    "this_week": tasks_week,
                    "status_breakdown": status_breakdown,
                    "risk_breakdown": risk_breakdown
                },
                "alerts": {
                    "pending_reviews": flagged_count,
                    "violations_this_week": violations_week,
                    "high_risk_today": high_risk_today
                },
                "governance": {
                    "active_rules": active_rules
                },
                "generated_at": now.isoformat()
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@dashboard_bp.route('/activity-timeline', methods=['GET'])
def get_activity_timeline():
    """
    Get activity timeline for charts.
    
    Query params:
        days: Number of days to include (default 7)
        granularity: hour or day (default day)
    """
    db = SessionLocal()
    try:
        days = int(request.args.get('days', 7))
        granularity = request.args.get('granularity', 'day')
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get tasks grouped by date
        tasks = db.query(Task).filter(Task.created_at >= start_date).all()
        
        # Aggregate by granularity
        timeline = {}
        for task in tasks:
            if granularity == 'hour':
                key = task.created_at.strftime('%Y-%m-%d %H:00')
            else:
                key = task.created_at.strftime('%Y-%m-%d')
            
            if key not in timeline:
                timeline[key] = {
                    "total": 0,
                    "completed": 0,
                    "failed": 0,
                    "blocked": 0,
                    "flagged": 0,
                    "low_risk": 0,
                    "medium_risk": 0,
                    "high_risk": 0,
                    "critical_risk": 0
                }
            
            timeline[key]["total"] += 1
            timeline[key][task.status.value] = timeline[key].get(task.status.value, 0) + 1
            timeline[key][f"{task.risk_level.value}_risk"] += 1
        
        # Sort by date
        sorted_timeline = [
            {"date": k, **v}
            for k, v in sorted(timeline.items())
        ]
        
        return jsonify({
            "success": True,
            "data": sorted_timeline
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@dashboard_bp.route('/agent-performance', methods=['GET'])
def get_agent_performance():
    """Get performance metrics for all agents"""
    db = SessionLocal()
    try:
        days = int(request.args.get('days', 7))
        service = AgentService(db)
        
        stats = service.get_all_agent_statistics(days)
        
        # Sort by total tasks
        stats.sort(key=lambda x: x['total_tasks'], reverse=True)
        
        return jsonify({
            "success": True,
            "data": stats
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@dashboard_bp.route('/risk-overview', methods=['GET'])
def get_risk_overview():
    """Get risk overview for dashboard"""
    db = SessionLocal()
    try:
        days = int(request.args.get('days', 7))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get tasks in period
        tasks = db.query(Task).filter(Task.created_at >= start_date).all()
        
        # Calculate average risk score
        if tasks:
            avg_risk_score = sum(t.risk_score for t in tasks) / len(tasks)
        else:
            avg_risk_score = 0
        
        # Risk distribution
        risk_distribution = {level.value: 0 for level in RiskLevel}
        for task in tasks:
            risk_distribution[task.risk_level.value] += 1
        
        # Top risk agents
        agent_risks = {}
        for task in tasks:
            if task.agent_id not in agent_risks:
                agent_risks[task.agent_id] = {"total": 0, "score_sum": 0}
            agent_risks[task.agent_id]["total"] += 1
            agent_risks[task.agent_id]["score_sum"] += task.risk_score
        
        top_risk_agents = []
        for agent_id, data in agent_risks.items():
            avg = data["score_sum"] / data["total"]
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            top_risk_agents.append({
                "agent_id": agent_id,
                "agent_name": agent.name if agent else "Unknown",
                "average_risk_score": round(avg, 3),
                "task_count": data["total"]
            })
        
        top_risk_agents.sort(key=lambda x: x["average_risk_score"], reverse=True)
        
        return jsonify({
            "success": True,
            "data": {
                "average_risk_score": round(avg_risk_score, 3),
                "risk_distribution": risk_distribution,
                "top_risk_agents": top_risk_agents[:10],
                "total_tasks_analyzed": len(tasks)
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@dashboard_bp.route('/recent-activity', methods=['GET'])
def get_recent_activity():
    """Get recent activity feed"""
    db = SessionLocal()
    try:
        limit = int(request.args.get('limit', 20))
        
        # Get recent audit logs
        logs = db.query(AuditLog).order_by(
            desc(AuditLog.timestamp)
        ).limit(limit).all()
        
        activities = []
        for log in logs:
            activity = {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "action": log.action.value,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "severity": log.severity
            }
            
            # Add context based on entity type
            if log.entity_type == "task" and log.task_id:
                task = db.query(Task).filter(Task.id == log.task_id).first()
                if task:
                    activity["context"] = {
                        "task_title": task.title,
                        "task_type": task.task_type.value
                    }
            elif log.entity_type == "agent" and log.agent_id:
                agent = db.query(Agent).filter(Agent.id == log.agent_id).first()
                if agent:
                    activity["context"] = {
                        "agent_name": agent.name
                    }
            
            activities.append(activity)
        
        return jsonify({
            "success": True,
            "data": activities
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@dashboard_bp.route('/governance-stats', methods=['GET'])
def get_governance_stats():
    """Get governance rule statistics"""
    db = SessionLocal()
    try:
        days = int(request.args.get('days', 7))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all rules
        rules = db.query(GovernanceRule).all()
        
        # Get rule trigger events
        triggers = db.query(AuditLog).filter(
            AuditLog.action == AuditAction.RULE_TRIGGERED,
            AuditLog.timestamp >= start_date
        ).all()
        
        # Count triggers per rule
        trigger_counts = {}
        for trigger in triggers:
            rule_id = trigger.entity_id
            trigger_counts[rule_id] = trigger_counts.get(rule_id, 0) + 1
        
        rule_stats = []
        for rule in rules:
            rule_stats.append({
                "id": rule.id,
                "name": rule.name,
                "type": rule.rule_type.value,
                "action": rule.action.value,
                "is_active": rule.is_active,
                "priority": rule.priority,
                "trigger_count": trigger_counts.get(rule.id, 0)
            })
        
        # Sort by trigger count
        rule_stats.sort(key=lambda x: x["trigger_count"], reverse=True)
        
        return jsonify({
            "success": True,
            "data": {
                "total_rules": len(rules),
                "active_rules": sum(1 for r in rules if r.is_active),
                "total_triggers": len(triggers),
                "rules": rule_stats
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()
