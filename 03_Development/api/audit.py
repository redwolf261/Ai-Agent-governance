"""
Audit API Endpoints
"""
from flask import Blueprint, request, jsonify, Response
from datetime import datetime, timedelta
from models.database import SessionLocal
from services.audit_service import AuditService
from models.audit_log import AuditAction

audit_bp = Blueprint('audit', __name__)


@audit_bp.route('/logs', methods=['GET'])
def list_audit_logs():
    """
    Query audit logs with filters.
    
    Query params:
        start_date: ISO format date
        end_date: ISO format date
        action: Action type filter
        entity_type: Entity type filter
        entity_id: Entity ID filter
        agent_id: Agent ID filter
        user_id: User ID filter
        severity: Severity level filter
        limit: Max results
        offset: Pagination offset
    """
    db = SessionLocal()
    try:
        service = AuditService(db)
        
        # Parse query params
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        action_str = request.args.get('action')
        entity_type = request.args.get('entity_type')
        entity_id = request.args.get('entity_id')
        agent_id = request.args.get('agent_id')
        user_id = request.args.get('user_id')
        severity = request.args.get('severity')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Parse dates
        if start_date:
            start_date = datetime.fromisoformat(start_date)
        if end_date:
            end_date = datetime.fromisoformat(end_date)
        
        # Parse action
        action = None
        if action_str:
            try:
                action = AuditAction(action_str)
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": f"Invalid action: {action_str}"
                }), 400
        
        logs = service.get_audit_logs(
            start_date=start_date,
            end_date=end_date,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            agent_id=agent_id,
            user_id=user_id,
            severity=severity,
            limit=limit,
            offset=offset
        )
        
        return jsonify({
            "success": True,
            "data": [log.to_dict() for log in logs],
            "count": len(logs)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@audit_bp.route('/task/<task_id>/trail', methods=['GET'])
def get_task_audit_trail(task_id):
    """Get complete audit trail for a task"""
    db = SessionLocal()
    try:
        service = AuditService(db)
        logs = service.get_task_audit_trail(task_id)
        
        return jsonify({
            "success": True,
            "data": [log.to_dict() for log in logs],
            "count": len(logs)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@audit_bp.route('/agent/<agent_id>/trail', methods=['GET'])
def get_agent_audit_trail(agent_id):
    """Get audit trail for an agent"""
    db = SessionLocal()
    try:
        service = AuditService(db)
        logs = service.get_agent_audit_trail(agent_id)
        
        return jsonify({
            "success": True,
            "data": [log.to_dict() for log in logs],
            "count": len(logs)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@audit_bp.route('/compliance-report', methods=['GET'])
def generate_compliance_report():
    """
    Generate a compliance report for a date range.
    
    Query params:
        start_date: Report start date (ISO format)
        end_date: Report end date (ISO format)
    """
    db = SessionLocal()
    try:
        service = AuditService(db)
        
        # Default to last 30 days if not specified
        end_date = request.args.get('end_date')
        start_date = request.args.get('start_date')
        
        if end_date:
            end_date = datetime.fromisoformat(end_date)
        else:
            end_date = datetime.utcnow()
        
        if start_date:
            start_date = datetime.fromisoformat(start_date)
        else:
            start_date = end_date - timedelta(days=30)
        
        report = service.generate_compliance_report(start_date, end_date)
        
        return jsonify({
            "success": True,
            "data": report
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@audit_bp.route('/risk-summary', methods=['GET'])
def get_risk_summary():
    """Get risk summary for recent period"""
    db = SessionLocal()
    try:
        service = AuditService(db)
        days = int(request.args.get('days', 7))
        
        summary = service.get_risk_summary(days)
        
        return jsonify({
            "success": True,
            "data": summary
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@audit_bp.route('/export', methods=['GET'])
def export_audit_logs():
    """
    Export audit logs.
    
    Query params:
        start_date: Export start date
        end_date: Export end date
        format: Export format (json or csv)
    """
    db = SessionLocal()
    try:
        service = AuditService(db)
        
        # Parse parameters
        end_date = request.args.get('end_date')
        start_date = request.args.get('start_date')
        export_format = request.args.get('format', 'json')
        
        if end_date:
            end_date = datetime.fromisoformat(end_date)
        else:
            end_date = datetime.utcnow()
        
        if start_date:
            start_date = datetime.fromisoformat(start_date)
        else:
            start_date = end_date - timedelta(days=7)
        
        data = service.export_audit_logs(start_date, end_date, export_format)
        
        if export_format == 'csv':
            return Response(
                data,
                mimetype='text/csv',
                headers={"Content-Disposition": "attachment;filename=audit_logs.csv"}
            )
        else:
            return Response(
                data,
                mimetype='application/json',
                headers={"Content-Disposition": "attachment;filename=audit_logs.json"}
            )
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@audit_bp.route('/actions', methods=['GET'])
def get_available_actions():
    """Get list of available audit actions"""
    return jsonify({
        "success": True,
        "data": [action.value for action in AuditAction]
    })
