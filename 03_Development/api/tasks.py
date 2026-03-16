"""
Task API Endpoints
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from models.database import SessionLocal
from services.task_service import TaskService

tasks_bp = Blueprint('tasks', __name__)


@tasks_bp.route('', methods=['GET'])
def list_tasks():
    """
    List tasks with optional filters.
    
    Query params:
        agent_id: Filter by agent
        status: Filter by status
        risk_level: Filter by risk level
        task_type: Filter by task type
        start_date: Filter by start date (ISO format)
        end_date: Filter by end date (ISO format)
        limit: Max results
        offset: Pagination offset
    """
    db = SessionLocal()
    try:
        service = TaskService(db)
        
        agent_id = request.args.get('agent_id')
        status = request.args.get('status')
        risk_level = request.args.get('risk_level')
        task_type = request.args.get('task_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Parse dates if provided
        if start_date:
            start_date = datetime.fromisoformat(start_date)
        if end_date:
            end_date = datetime.fromisoformat(end_date)
        
        tasks = service.get_tasks(
            agent_id=agent_id,
            status=status,
            risk_level=risk_level,
            task_type=task_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        return jsonify({
            "success": True,
            "data": [task.to_dict() for task in tasks],
            "count": len(tasks)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@tasks_bp.route('/<task_id>', methods=['GET'])
def get_task(task_id):
    """Get a specific task by ID"""
    db = SessionLocal()
    try:
        service = TaskService(db)
        task = service.get_task(task_id)
        
        if not task:
            return jsonify({"success": False, "error": "Task not found"}), 404
        
        return jsonify({
            "success": True,
            "data": task.to_dict()
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@tasks_bp.route('/<task_id>/decision-trace', methods=['GET'])
def get_task_decision_trace(task_id):
    """Get decision lineage and audit timeline for a task"""
    db = SessionLocal()
    try:
        service = TaskService(db)
        trace = service.get_task_decision_trace(task_id)

        return jsonify({
            "success": True,
            "data": trace
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@tasks_bp.route('', methods=['POST'])
def create_task():
    """
    Create a new task.
    
    Request body:
        agent_id: Agent executing the task (required)
        task_type: Type of task (required)
        title: Task title (required)
        description: Task description
        input_data: Input parameters (object)
    """
    db = SessionLocal()
    try:
        service = TaskService(db)
        data = request.get_json()
        
        # Validate required fields
        required = ['agent_id', 'task_type', 'title']
        for field in required:
            if not data.get(field):
                return jsonify({"success": False, "error": f"{field} is required"}), 400
        
        task, evaluation = service.create_task(
            agent_id=data['agent_id'],
            task_type=data['task_type'],
            title=data['title'],
            description=data.get('description'),
            input_data=data.get('input_data'),
            ip_address=request.remote_addr
        )
        
        return jsonify({
            "success": True,
            "data": task.to_dict(),
            "evaluation": evaluation,
            "message": "Task created successfully"
        }), 201
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@tasks_bp.route('/<task_id>/start', methods=['POST'])
def start_task(task_id):
    """Start a pending task"""
    db = SessionLocal()
    try:
        service = TaskService(db)
        task = service.start_task(task_id)
        
        return jsonify({
            "success": True,
            "data": task.to_dict(),
            "message": "Task started"
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@tasks_bp.route('/<task_id>/complete', methods=['POST'])
def complete_task(task_id):
    """Mark a task as completed"""
    db = SessionLocal()
    try:
        service = TaskService(db)
        data = request.get_json() or {}
        
        task = service.complete_task(
            task_id=task_id,
            output_data=data.get('output_data')
        )
        
        return jsonify({
            "success": True,
            "data": task.to_dict(),
            "message": "Task completed"
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@tasks_bp.route('/<task_id>/fail', methods=['POST'])
def fail_task(task_id):
    """Mark a task as failed"""
    db = SessionLocal()
    try:
        service = TaskService(db)
        data = request.get_json() or {}
        
        task = service.fail_task(
            task_id=task_id,
            error_message=data.get('error_message', 'Unknown error')
        )
        
        return jsonify({
            "success": True,
            "data": task.to_dict(),
            "message": "Task marked as failed"
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@tasks_bp.route('/<task_id>/approve', methods=['POST'])
def approve_task(task_id):
    """Approve a flagged task"""
    db = SessionLocal()
    try:
        service = TaskService(db)
        data = request.get_json() or {}
        
        if not data.get('reviewer'):
            return jsonify({"success": False, "error": "Reviewer is required"}), 400
        
        task = service.approve_task(
            task_id=task_id,
            reviewer=data['reviewer'],
            notes=data.get('notes')
        )
        
        return jsonify({
            "success": True,
            "data": task.to_dict(),
            "message": "Task approved"
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@tasks_bp.route('/<task_id>/reject', methods=['POST'])
def reject_task(task_id):
    """Reject a flagged task"""
    db = SessionLocal()
    try:
        service = TaskService(db)
        data = request.get_json() or {}
        
        if not data.get('reviewer') or not data.get('reason'):
            return jsonify({"success": False, "error": "Reviewer and reason are required"}), 400
        
        task = service.reject_task(
            task_id=task_id,
            reviewer=data['reviewer'],
            reason=data['reason']
        )
        
        return jsonify({
            "success": True,
            "data": task.to_dict(),
            "message": "Task rejected"
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@tasks_bp.route('/flagged', methods=['GET'])
def get_flagged_tasks():
    """Get tasks requiring review"""
    db = SessionLocal()
    try:
        service = TaskService(db)
        limit = int(request.args.get('limit', 50))
        
        tasks = service.get_flagged_tasks(limit)
        
        return jsonify({
            "success": True,
            "data": [task.to_dict() for task in tasks],
            "count": len(tasks)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@tasks_bp.route('/statistics', methods=['GET'])
def get_task_statistics():
    """Get task statistics"""
    db = SessionLocal()
    try:
        service = TaskService(db)
        days = int(request.args.get('days', 7))
        
        stats = service.get_task_statistics(days)
        
        return jsonify({
            "success": True,
            "data": stats
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()
