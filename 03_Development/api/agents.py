"""
Agent API Endpoints
"""
from flask import Blueprint, request, jsonify
from models.database import SessionLocal
from services.agent_service import AgentService

agents_bp = Blueprint('agents', __name__)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Session will be closed after request


@agents_bp.route('', methods=['GET'])
def list_agents():
    """
    List all agents with optional filters.
    
    Query params:
        status: Filter by status (active, inactive, suspended)
        type: Filter by agent type
        trusted: Filter by trust level (true/false)
        limit: Max results (default 100)
        offset: Pagination offset
    """
    db = SessionLocal()
    try:
        service = AgentService(db)
        
        status = request.args.get('status')
        agent_type = request.args.get('type')
        is_trusted = request.args.get('trusted')
        if is_trusted:
            is_trusted = is_trusted.lower() == 'true'
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        agents = service.get_agents(
            status=status,
            agent_type=agent_type,
            is_trusted=is_trusted,
            limit=limit,
            offset=offset
        )
        
        return jsonify({
            "success": True,
            "data": [agent.to_dict() for agent in agents],
            "count": len(agents)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@agents_bp.route('/<agent_id>', methods=['GET'])
def get_agent(agent_id):
    """Get a specific agent by ID"""
    db = SessionLocal()
    try:
        service = AgentService(db)
        agent = service.get_agent(agent_id)
        
        if not agent:
            return jsonify({"success": False, "error": "Agent not found"}), 404
        
        return jsonify({
            "success": True,
            "data": agent.to_dict()
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@agents_bp.route('', methods=['POST'])
def register_agent():
    """
    Register a new agent.
    
    Request body:
        name: Agent name (required)
        agent_type: Type of agent
        description: Agent description
        capabilities: List of capabilities
        owner: Owner identifier
        is_trusted: Trust level (default false)
    """
    db = SessionLocal()
    try:
        service = AgentService(db)
        data = request.get_json()
        
        if not data.get('name'):
            return jsonify({"success": False, "error": "Name is required"}), 400
        
        agent = service.register_agent(
            name=data['name'],
            agent_type=data.get('agent_type', 'general'),
            description=data.get('description'),
            capabilities=data.get('capabilities'),
            owner=data.get('owner'),
            is_trusted=data.get('is_trusted', False),
            ip_address=request.remote_addr
        )
        
        return jsonify({
            "success": True,
            "data": agent.to_dict(),
            "message": "Agent registered successfully"
        }), 201
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@agents_bp.route('/<agent_id>', methods=['PUT'])
def update_agent(agent_id):
    """Update an agent's properties"""
    db = SessionLocal()
    try:
        service = AgentService(db)
        data = request.get_json()
        
        agent = service.update_agent(
            agent_id=agent_id,
            updates=data,
            ip_address=request.remote_addr
        )
        
        return jsonify({
            "success": True,
            "data": agent.to_dict(),
            "message": "Agent updated successfully"
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@agents_bp.route('/<agent_id>/suspend', methods=['POST'])
def suspend_agent(agent_id):
    """Suspend an agent"""
    db = SessionLocal()
    try:
        service = AgentService(db)
        data = request.get_json() or {}
        
        agent = service.suspend_agent(
            agent_id=agent_id,
            reason=data.get('reason'),
            ip_address=request.remote_addr
        )
        
        return jsonify({
            "success": True,
            "data": agent.to_dict(),
            "message": "Agent suspended"
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@agents_bp.route('/<agent_id>/activate', methods=['POST'])
def activate_agent(agent_id):
    """Activate a suspended agent"""
    db = SessionLocal()
    try:
        service = AgentService(db)
        
        agent = service.activate_agent(
            agent_id=agent_id,
            ip_address=request.remote_addr
        )
        
        return jsonify({
            "success": True,
            "data": agent.to_dict(),
            "message": "Agent activated"
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@agents_bp.route('/<agent_id>/trust', methods=['POST'])
def set_agent_trust(agent_id):
    """Set agent trust level"""
    db = SessionLocal()
    try:
        service = AgentService(db)
        data = request.get_json()
        
        if 'is_trusted' not in data:
            return jsonify({"success": False, "error": "is_trusted field required"}), 400
        
        agent = service.set_trust_level(
            agent_id=agent_id,
            is_trusted=data['is_trusted'],
            ip_address=request.remote_addr
        )
        
        return jsonify({
            "success": True,
            "data": agent.to_dict(),
            "message": f"Agent trust level set to {data['is_trusted']}"
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@agents_bp.route('/<agent_id>/statistics', methods=['GET'])
def get_agent_stats(agent_id):
    """Get agent performance statistics"""
    db = SessionLocal()
    try:
        service = AgentService(db)
        days = int(request.args.get('days', 7))
        
        stats = service.get_agent_statistics(agent_id, days)
        
        return jsonify({
            "success": True,
            "data": stats
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()
