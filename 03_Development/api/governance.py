"""
Governance API Endpoints
"""
import json
from flask import Blueprint, request, jsonify
from models.database import SessionLocal
from models.governance_rule import GovernanceRule, RuleType, RuleAction
from services.governance_engine import GovernanceEngine
from services.audit_service import AuditService
from models.audit_log import AuditAction

governance_bp = Blueprint('governance', __name__)


@governance_bp.route('/rules', methods=['GET'])
def list_rules():
    """List all governance rules"""
    db = SessionLocal()
    try:
        rules = db.query(GovernanceRule).order_by(GovernanceRule.priority).all()
        
        return jsonify({
            "success": True,
            "data": [rule.to_dict() for rule in rules],
            "count": len(rules)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@governance_bp.route('/rules/<rule_id>', methods=['GET'])
def get_rule(rule_id):
    """Get a specific rule by ID"""
    db = SessionLocal()
    try:
        rule = db.query(GovernanceRule).filter(GovernanceRule.id == rule_id).first()
        
        if not rule:
            return jsonify({"success": False, "error": "Rule not found"}), 404
        
        return jsonify({
            "success": True,
            "data": rule.to_dict()
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@governance_bp.route('/rules', methods=['POST'])
def create_rule():
    """
    Create a new governance rule.
    
    Request body:
        name: Rule name (required)
        description: Rule description
        rule_type: Type of rule (required)
        condition: JSON condition expression (required)
        action: Action to take when triggered
        severity: Rule severity
        priority: Rule priority (lower = higher priority)
        applies_to_agents: Comma-separated agent IDs
        applies_to_task_types: Comma-separated task types
    """
    db = SessionLocal()
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name') or not data.get('rule_type') or not data.get('condition'):
            return jsonify({
                "success": False, 
                "error": "name, rule_type, and condition are required"
            }), 400
        
        # Validate rule type
        try:
            rule_type = RuleType(data['rule_type'])
        except ValueError:
            valid_types = [t.value for t in RuleType]
            return jsonify({
                "success": False,
                "error": f"Invalid rule_type. Valid options: {valid_types}"
            }), 400
        
        # Validate action
        action = RuleAction.FLAG
        if data.get('action'):
            try:
                action = RuleAction(data['action'])
            except ValueError:
                valid_actions = [a.value for a in RuleAction]
                return jsonify({
                    "success": False,
                    "error": f"Invalid action. Valid options: {valid_actions}"
                }), 400
        
        # Validate condition is valid JSON
        condition = data['condition']
        if isinstance(condition, dict):
            condition = json.dumps(condition)
        else:
            try:
                json.loads(condition)
            except json.JSONDecodeError:
                return jsonify({
                    "success": False,
                    "error": "condition must be valid JSON"
                }), 400
        
        rule = GovernanceRule(
            name=data['name'],
            description=data.get('description'),
            rule_type=rule_type,
            condition=condition,
            action=action,
            priority=data.get('priority', 100),
            applies_to_agents=data.get('applies_to_agents'),
            applies_to_task_types=data.get('applies_to_task_types'),
            created_by=data.get('created_by', 'api')
        )
        
        db.add(rule)
        
        # Log rule creation
        audit_service = AuditService(db)
        audit_service.log_action(
            action=AuditAction.RULE_CREATED,
            entity_type="governance_rule",
            entity_id=rule.id,
            details={
                "rule_name": rule.name,
                "rule_type": rule.rule_type.value
            },
            ip_address=request.remote_addr
        )
        
        db.commit()
        
        return jsonify({
            "success": True,
            "data": rule.to_dict(),
            "message": "Rule created successfully"
        }), 201
    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@governance_bp.route('/rules/<rule_id>', methods=['PUT'])
def update_rule(rule_id):
    """Update a governance rule"""
    db = SessionLocal()
    try:
        rule = db.query(GovernanceRule).filter(GovernanceRule.id == rule_id).first()
        
        if not rule:
            return jsonify({"success": False, "error": "Rule not found"}), 404
        
        data = request.get_json()
        old_values = rule.to_dict()
        
        # Update allowed fields
        if 'name' in data:
            rule.name = data['name']
        if 'description' in data:
            rule.description = data['description']
        if 'condition' in data:
            condition = data['condition']
            if isinstance(condition, dict):
                condition = json.dumps(condition)
            rule.condition = condition
        if 'action' in data:
            rule.action = RuleAction(data['action'])
        if 'priority' in data:
            rule.priority = data['priority']
        if 'is_active' in data:
            rule.is_active = data['is_active']
        if 'applies_to_agents' in data:
            rule.applies_to_agents = data['applies_to_agents']
        if 'applies_to_task_types' in data:
            rule.applies_to_task_types = data['applies_to_task_types']
        
        rule.version += 1
        rule.updated_by = data.get('updated_by', 'api')
        
        # Log update
        audit_service = AuditService(db)
        audit_service.log_action(
            action=AuditAction.RULE_UPDATED,
            entity_type="governance_rule",
            entity_id=rule.id,
            old_value=old_values,
            new_value=rule.to_dict(),
            ip_address=request.remote_addr
        )
        
        db.commit()
        
        return jsonify({
            "success": True,
            "data": rule.to_dict(),
            "message": "Rule updated successfully"
        })
    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@governance_bp.route('/rules/<rule_id>', methods=['DELETE'])
def delete_rule(rule_id):
    """Delete a governance rule"""
    db = SessionLocal()
    try:
        rule = db.query(GovernanceRule).filter(GovernanceRule.id == rule_id).first()
        
        if not rule:
            return jsonify({"success": False, "error": "Rule not found"}), 404
        
        rule_data = rule.to_dict()
        
        # Log deletion
        audit_service = AuditService(db)
        audit_service.log_action(
            action=AuditAction.RULE_DELETED,
            entity_type="governance_rule",
            entity_id=rule_id,
            old_value=rule_data,
            ip_address=request.remote_addr
        )
        
        db.delete(rule)
        db.commit()
        
        return jsonify({
            "success": True,
            "message": "Rule deleted successfully"
        })
    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@governance_bp.route('/rules/<rule_id>/toggle', methods=['POST'])
def toggle_rule(rule_id):
    """Toggle a rule's active status"""
    db = SessionLocal()
    try:
        rule = db.query(GovernanceRule).filter(GovernanceRule.id == rule_id).first()
        
        if not rule:
            return jsonify({"success": False, "error": "Rule not found"}), 404
        
        rule.is_active = not rule.is_active
        
        db.commit()
        
        return jsonify({
            "success": True,
            "data": rule.to_dict(),
            "message": f"Rule {'activated' if rule.is_active else 'deactivated'}"
        })
    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@governance_bp.route('/init-defaults', methods=['POST'])
def initialize_defaults():
    """Initialize default governance rules"""
    db = SessionLocal()
    try:
        engine = GovernanceEngine(db)
        engine.create_default_rules()
        
        return jsonify({
            "success": True,
            "message": "Default governance rules created"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@governance_bp.route('/rule-types', methods=['GET'])
def get_rule_types():
    """Get available rule types and actions"""
    return jsonify({
        "success": True,
        "data": {
            "rule_types": [t.value for t in RuleType],
            "actions": [a.value for a in RuleAction]
        }
    })
