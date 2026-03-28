"""
API Routes Registration
"""
from flask import Flask
from api.agents import agents_bp
from api.tasks import tasks_bp
from api.governance import governance_bp
from api.audit import audit_bp
from api.dashboard import dashboard_bp
from api.auth import auth_bp
from api.llama import llama_bp


def register_routes(app: Flask):
    """
    Register all API blueprints with the Flask application.
    
    Args:
        app: Flask application instance
    """
    # Register blueprints with URL prefixes
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(agents_bp, url_prefix='/api/agents')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
    app.register_blueprint(governance_bp, url_prefix='/api/governance')
    app.register_blueprint(audit_bp, url_prefix='/api/audit')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(llama_bp, url_prefix='/api/llama')
    
    print("✅ API routes registered")
