"""
AI Agent Governance System - Main Application Entry Point
Ethical AI Governance and Agent Task Auditing System

Author: Rivan Shetty
Group: CS-K GRP 3
Roll No: 13
PRN: 12411956
"""
import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

from config import config
from models.database import init_db, Base, engine
from api.routes import register_routes


def create_app():
    """
    Application factory function.
    
    Creates and configures the Flask application with all
    necessary extensions and routes.
    
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__, static_folder='static')
    
    # Configuration
    app.config['SECRET_KEY'] = config.api.secret_key
    app.config['DEBUG'] = config.api.debug
    
    # Enable CORS for API access
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Initialize database
    init_db()
    
    # Register API routes
    register_routes(app)
    
    # Root route - serve dashboard
    @app.route('/')
    def index():
        return send_from_directory('static', 'index.html')
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return jsonify({
            "status": "healthy",
            "service": "AI Agent Governance System",
            "version": "1.0.0"
        })
    
    # API documentation endpoint
    @app.route('/api')
    def api_docs():
        return jsonify({
            "name": "AI Agent Governance API",
            "version": "1.0.0",
            "endpoints": {
                "auth": {
                    "POST /api/auth/register": "Register new user",
                    "POST /api/auth/login": "Authenticate user",
                    "GET /api/auth/me": "Get current user",
                    "POST /api/auth/logout": "Logout user"
                },
                "agents": {
                    "GET /api/agents": "List all agents",
                    "POST /api/agents": "Register new agent",
                    "GET /api/agents/<id>": "Get agent details",
                    "PUT /api/agents/<id>": "Update agent",
                    "POST /api/agents/<id>/suspend": "Suspend agent",
                    "POST /api/agents/<id>/activate": "Activate agent",
                    "GET /api/agents/<id>/statistics": "Get agent stats"
                },
                "tasks": {
                    "GET /api/tasks": "List tasks",
                    "POST /api/tasks": "Create task",
                    "GET /api/tasks/<id>": "Get task details",
                    "POST /api/tasks/<id>/start": "Start task",
                    "POST /api/tasks/<id>/complete": "Complete task",
                    "POST /api/tasks/<id>/fail": "Fail task",
                    "POST /api/tasks/<id>/approve": "Approve flagged task",
                    "POST /api/tasks/<id>/reject": "Reject flagged task",
                    "GET /api/tasks/<id>/decision-trace": "Get decision lineage for a task",
                    "GET /api/tasks/flagged": "Get flagged tasks",
                    "GET /api/tasks/statistics": "Get task statistics"
                },
                "governance": {
                    "GET /api/governance/rules": "List governance rules",
                    "POST /api/governance/rules": "Create rule",
                    "GET /api/governance/rules/<id>": "Get rule",
                    "PUT /api/governance/rules/<id>": "Update rule",
                    "DELETE /api/governance/rules/<id>": "Delete rule",
                    "POST /api/governance/rules/<id>/toggle": "Toggle rule active status",
                    "POST /api/governance/init-defaults": "Initialize default rules"
                },
                "audit": {
                    "GET /api/audit/logs": "Query audit logs",
                    "GET /api/audit/task/<id>/trail": "Get task audit trail",
                    "GET /api/audit/agent/<id>/trail": "Get agent audit trail",
                    "GET /api/audit/compliance-report": "Generate compliance report",
                    "GET /api/audit/risk-summary": "Get risk summary",
                    "GET /api/audit/export": "Export audit logs"
                },
                "dashboard": {
                    "GET /api/dashboard/summary": "Get dashboard summary",
                    "GET /api/dashboard/activity-timeline": "Get activity timeline",
                    "GET /api/dashboard/agent-performance": "Get agent performance",
                    "GET /api/dashboard/risk-overview": "Get risk overview",
                    "GET /api/dashboard/recent-activity": "Get recent activity",
                    "GET /api/dashboard/governance-stats": "Get governance stats",
                    "GET /api/dashboard/live-alerts": "Get high-severity live alerts"
                }
            }
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "error": "Resource not found"}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"success": False, "error": "Internal server error"}), 500
    
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║           AI AGENT GOVERNANCE SYSTEM                             ║
    ║           Ethical AI Governance and Task Auditing                ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  Author: Rivan Shetty                                            ║
    ║  Group: CS-K GRP 3                                               ║
    ║  Roll No: 13 | PRN: 12411956                                     ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    return app


def run_server():
    """Run the development server"""
    app = create_app()
    
    print(f"""
    🚀 Server starting...
    📍 URL: http://{config.api.host}:{config.api.port}
    📊 Dashboard: http://localhost:{config.api.port}
    📚 API Docs: http://localhost:{config.api.port}/api
    🔧 Debug Mode: {config.api.debug}
    """)
    
    app.run(
        host=config.api.host,
        port=config.api.port,
        debug=config.api.debug
    )


if __name__ == "__main__":
    run_server()
