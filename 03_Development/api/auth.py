"""
Authentication API Endpoints
"""
from flask import Blueprint, request, jsonify
from datetime import timedelta
import jwt
from functools import wraps
from models.database import SessionLocal
from models.user import User, UserRole
from models.audit_log import AuditAction
from services.audit_service import AuditService
from config import config
from utils.time_utils import utc_now

auth_bp = Blueprint('auth', __name__)

SECRET_KEY = config.api.secret_key
JWT_EXPIRATION_HOURS = config.api.jwt_expiration_hours


def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({"success": False, "error": "Token is missing"}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({"success": False, "error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"success": False, "error": "Invalid token"}), 401
        
        return f(current_user_id, *args, **kwargs)
    
    return decorated


def role_required(min_role: UserRole):
    """Decorator to require minimum role level"""
    def decorator(f):
        @wraps(f)
        def decorated(current_user_id, *args, **kwargs):
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.id == current_user_id).first()
                if not user:
                    return jsonify({"success": False, "error": "User not found"}), 404
                
                if not user.has_permission(min_role):
                    return jsonify({
                        "success": False, 
                        "error": f"Insufficient permissions. Required: {min_role.value}"
                    }), 403
                
                return f(current_user_id, *args, **kwargs)
            finally:
                db.close()
        return decorated
    return decorator


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user.
    
    Request body:
        username: Username (required)
        email: Email address (required)
        password: Password (required)
        full_name: Full name
    """
    db = SessionLocal()
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['username', 'email', 'password']
        for field in required:
            if not data.get(field):
                return jsonify({"success": False, "error": f"{field} is required"}), 400
        
        # Check if username/email already exists
        existing = db.query(User).filter(
            (User.username == data['username']) | (User.email == data['email'])
        ).first()
        
        if existing:
            return jsonify({
                "success": False, 
                "error": "Username or email already exists"
            }), 400
        
        # Create user
        user = User(
            username=data['username'],
            email=data['email'],
            full_name=data.get('full_name'),
            role=UserRole.VIEWER  # Default role
        )
        user.set_password(data['password'])
        
        db.add(user)
        
        # Log registration
        audit_service = AuditService(db)
        audit_service.log_action(
            action=AuditAction.USER_CREATED,
            entity_type="user",
            entity_id=user.id,
            user_id=user.id,
            details={"username": user.username},
            ip_address=request.remote_addr
        )
        
        db.commit()
        
        return jsonify({
            "success": True,
            "data": user.to_dict(),
            "message": "User registered successfully"
        }), 201
    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate user and return JWT token.
    
    Request body:
        username: Username
        password: Password
    """
    db = SessionLocal()
    try:
        data = request.get_json()
        
        if not data.get('username') or not data.get('password'):
            return jsonify({
                "success": False, 
                "error": "Username and password are required"
            }), 400
        
        user = db.query(User).filter(User.username == data['username']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({
                "success": False, 
                "error": "Invalid username or password"
            }), 401
        
        if not user.is_active:
            return jsonify({
                "success": False, 
                "error": "Account is deactivated"
            }), 401
        
        # Generate token
        token = jwt.encode({
            'user_id': user.id,
            'username': user.username,
            'role': user.role.value,
            'exp': utc_now() + timedelta(hours=JWT_EXPIRATION_HOURS)
        }, SECRET_KEY, algorithm="HS256")
        
        # Update last login
        user.update_last_login()
        
        # Log login
        audit_service = AuditService(db)
        audit_service.log_action(
            action=AuditAction.USER_LOGIN,
            entity_type="user",
            entity_id=user.id,
            user_id=user.id,
            ip_address=request.remote_addr
        )
        
        db.commit()
        
        return jsonify({
            "success": True,
            "data": {
                "token": token,
                "user": user.to_dict(),
                "expires_in": JWT_EXPIRATION_HOURS * 3600
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user_id):
    """Get current user profile"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == current_user_id).first()
        
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404
        
        return jsonify({
            "success": True,
            "data": user.to_dict()
        })
    finally:
        db.close()


@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user_id):
    """Log out current user"""
    db = SessionLocal()
    try:
        # Log logout
        audit_service = AuditService(db)
        audit_service.log_action(
            action=AuditAction.USER_LOGOUT,
            entity_type="user",
            entity_id=current_user_id,
            user_id=current_user_id,
            ip_address=request.remote_addr
        )
        db.commit()
        
        return jsonify({
            "success": True,
            "message": "Logged out successfully"
        })
    finally:
        db.close()


@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password(current_user_id):
    """Change user password"""
    db = SessionLocal()
    try:
        data = request.get_json()
        
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({
                "success": False,
                "error": "Current and new passwords are required"
            }), 400
        
        user = db.query(User).filter(User.id == current_user_id).first()
        
        if not user.check_password(data['current_password']):
            return jsonify({
                "success": False,
                "error": "Current password is incorrect"
            }), 401
        
        user.set_password(data['new_password'])
        db.commit()
        
        return jsonify({
            "success": True,
            "message": "Password changed successfully"
        })
    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()


@auth_bp.route('/users', methods=['GET'])
@token_required
@role_required(UserRole.ADMIN)
def list_users(current_user_id):
    """List all users (admin only)"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        
        return jsonify({
            "success": True,
            "data": [user.to_dict() for user in users]
        })
    finally:
        db.close()


@auth_bp.route('/users/<user_id>/role', methods=['PUT'])
@token_required
@role_required(UserRole.ADMIN)
def update_user_role(current_user_id, user_id):
    """Update user role (admin only)"""
    db = SessionLocal()
    try:
        data = request.get_json()
        
        if not data.get('role'):
            return jsonify({"success": False, "error": "Role is required"}), 400
        
        try:
            new_role = UserRole(data['role'])
        except ValueError:
            valid_roles = [r.value for r in UserRole]
            return jsonify({
                "success": False,
                "error": f"Invalid role. Valid options: {valid_roles}"
            }), 400
        
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404
        
        old_role = user.role.value
        user.role = new_role
        
        # Log role change
        audit_service = AuditService(db)
        audit_service.log_action(
            action=AuditAction.USER_UPDATED,
            entity_type="user",
            entity_id=user_id,
            user_id=current_user_id,
            details={"field": "role", "old": old_role, "new": new_role.value},
            ip_address=request.remote_addr
        )
        
        db.commit()
        
        return jsonify({
            "success": True,
            "data": user.to_dict(),
            "message": f"User role updated to {new_role.value}"
        })
    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()
