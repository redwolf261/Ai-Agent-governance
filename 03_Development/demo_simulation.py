"""
AI Agent Governance System - Demonstration Script
Simulates system functionality with sample agents, tasks, and governance scenarios

Author: Rivan Shetty
Group: CS-K GRP 3
Roll No: 13
PRN: 12411956

This script demonstrates:
1. Agent registration and management
2. Task creation with automatic governance evaluation
3. ML-based anomaly detection
4. Audit logging and compliance reporting
5. Dashboard data generation
"""
import sys
import os
import time
import random
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import init_db, get_session
from models.agent import Agent, AgentType, AgentStatus
from models.task import Task, TaskStatus, TaskType
from services.governance_engine import GovernanceEngine
from services.anomaly_detector import AnomalyDetector
from services.audit_service import AuditService
from services.agent_service import AgentService
from services.task_service import TaskService


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_subheader(text):
    """Print formatted subheader"""
    print(f"\n--- {text} ---")


def print_result(label, value, status="info"):
    """Print formatted result"""
    icons = {"success": "✓", "warning": "⚠", "error": "✗", "info": "→"}
    icon = icons.get(status, "→")
    print(f"  {icon} {label}: {value}")


class GovernanceDemo:
    """
    Demonstration class for AI Agent Governance System.
    
    Showcases the complete functionality of the governance
    platform through simulated scenarios.
    """
    
    def __init__(self):
        """Initialize demo components"""
        print_header("AI AGENT GOVERNANCE SYSTEM - DEMO")
        print("Initializing system components...")
        
        # Initialize database
        init_db()
        self.session = get_session()
        
        # Initialize services
        self.governance = GovernanceEngine(self.session)
        self.anomaly_detector = AnomalyDetector()
        self.audit_service = AuditService(self.session)
        self.agent_service = AgentService(self.session)
        self.task_service = TaskService(self.session)
        
        # Storage for demo entities
        self.agents = []
        self.tasks = []
        
        print_result("Database", "Initialized", "success")
        print_result("Services", "Ready", "success")
    
    def setup_governance_rules(self):
        """Create default governance rules"""
        print_subheader("Setting Up Governance Rules")
        
        rules = self.governance.create_default_rules()
        print_result("Rules Created", len(rules), "success")
        
        for rule in rules[:5]:  # Show first 5 rules
            print(f"    • {rule.name} ({rule.rule_type.value}) - {rule.action.value}")
    
    def train_anomaly_detector(self):
        """Train ML models for anomaly detection"""
        print_subheader("Training Anomaly Detection Models")
        
        print("  Training Isolation Forest...")
        print("  Training One-Class SVM...")
        
        # Generate synthetic training data
        training_data = self.anomaly_detector.generate_synthetic_training_data(n_samples=500)
        self.anomaly_detector.train_models(training_data)
        
        print_result("Models", "Trained", "success")
    
    def register_demo_agents(self):
        """Register sample AI agents"""
        print_subheader("Registering AI Agents")
        
        agent_configs = [
            {
                "name": "CodeGen-Alpha",
                "agent_type": "code_generator",
                "description": "Primary code generation agent for Python and JavaScript",
                "is_trusted": True,
                "capabilities": ["python", "javascript", "typescript", "testing"]
            },
            {
                "name": "Reviewer-Beta",
                "agent_type": "code_reviewer",
                "description": "Code review and quality analysis agent",
                "is_trusted": True,
                "capabilities": ["static_analysis", "security_scan", "code_quality"]
            },
            {
                "name": "TestRunner-Gamma",
                "agent_type": "test_runner",
                "description": "Automated test execution and reporting",
                "is_trusted": False,
                "capabilities": ["unit_tests", "integration_tests", "coverage"]
            },
            {
                "name": "DocWriter-Delta",
                "agent_type": "documentation",
                "description": "Documentation generation and maintenance",
                "is_trusted": False,
                "capabilities": ["markdown", "api_docs", "readme"]
            },
            {
                "name": "Deployer-Epsilon",
                "agent_type": "deployment",
                "description": "Deployment automation agent (restricted)",
                "is_trusted": False,
                "capabilities": ["docker", "kubernetes", "ci_cd"]
            }
        ]
        
        for config in agent_configs:
            agent = self.agent_service.register_agent(**config)
            self.agents.append(agent)
            status = "success" if agent.is_trusted else "info"
            trust = "Trusted" if agent.is_trusted else "Standard"
            print_result(config["name"], f"{config['agent_type']} ({trust})", status)
    
    def simulate_normal_tasks(self):
        """Simulate normal task execution"""
        print_subheader("Simulating Normal Task Operations")
        
        normal_tasks = [
            {
                "agent": self.agents[0],  # CodeGen
                "task_type": "code_generation",
                "title": "Generate User Authentication Module",
                "description": "Create login/logout functionality with JWT tokens",
                "duration": 300
            },
            {
                "agent": self.agents[1],  # Reviewer
                "task_type": "code_review",
                "title": "Review Pull Request #142",
                "description": "Review changes in user management module",
                "duration": 180
            },
            {
                "agent": self.agents[2],  # TestRunner
                "task_type": "testing",
                "title": "Run Unit Test Suite",
                "description": "Execute all unit tests for API module",
                "duration": 120
            },
            {
                "agent": self.agents[3],  # DocWriter
                "task_type": "documentation",
                "title": "Update API Documentation",
                "description": "Document new authentication endpoints",
                "duration": 240
            }
        ]
        
        for config in normal_tasks:
            task, evaluation = self.task_service.create_task(
                agent_id=config["agent"].id,
                task_type=config["task_type"],
                title=config["title"],
                description=config["description"],
                estimated_duration=config["duration"]
            )
            
            self.tasks.append(task)
            
            risk = evaluation["risk_assessment"]["score"]
            governance_status = evaluation["governance"]["status"]
            
            status = "success" if governance_status == "approved" else "warning"
            print_result(
                config["title"][:40],
                f"Risk: {risk:.2f} | Status: {governance_status}",
                status
            )
            
            # Simulate task execution for approved tasks
            if governance_status == "approved" and task.status == TaskStatus.PENDING:
                task.start_execution()
                self.session.commit()
                time.sleep(0.1)  # Brief pause
                task.complete_execution(str({"status": "success", "lines_generated": random.randint(50, 200)}))
                self.session.commit()
    
    def simulate_risky_tasks(self):
        """Simulate high-risk task scenarios"""
        print_subheader("Simulating High-Risk Task Scenarios")
        
        risky_tasks = [
            {
                "agent": self.agents[4],  # Deployer
                "task_type": "system_modification",
                "title": "Deploy to Production Server",
                "description": "Deploy latest build to production environment",
                "duration": 600,
                "input_data": {"environment": "production", "rollback": False}
            },
            {
                "agent": self.agents[0],  # CodeGen
                "task_type": "code_generation",
                "title": "Generate Database Migration Script",
                "description": "Create script to modify production database schema",
                "duration": 450,
                "input_data": {"operation": "alter_table", "database": "production"}
            },
            {
                "agent": self.agents[4],  # Deployer
                "task_type": "external_api_call",
                "title": "Access External Payment API",
                "description": "Connect to third-party payment processing system",
                "duration": 180,
                "input_data": {"api": "payment_gateway", "scope": "full_access"}
            }
        ]
        
        for config in risky_tasks:
            task, evaluation = self.task_service.create_task(
                agent_id=config["agent"].id,
                task_type=config["task_type"],
                title=config["title"],
                description=config["description"],
                estimated_duration=config["duration"],
                input_data=config.get("input_data", {})
            )
            
            self.tasks.append(task)
            
            risk = evaluation["risk_assessment"]["score"]
            governance_status = evaluation["governance"]["status"]
            triggered_rules = evaluation["governance"]["triggered_rules"]
            
            if governance_status == "blocked":
                status = "error"
            elif governance_status == "flagged":
                status = "warning"
            else:
                status = "success"
            
            print_result(
                config["title"][:40],
                f"Risk: {risk:.2f} | Status: {governance_status.upper()} | Rules: {len(triggered_rules)}",
                status
            )
            
            # Show triggered rules if any
            for rule in triggered_rules[:2]:
                print(f"      ⚡ {rule}")
    
    def simulate_anomalous_behavior(self):
        """Simulate anomalous agent behavior"""
        print_subheader("Simulating Anomalous Behavior Detection")
        
        anomalous_tasks = [
            {
                "agent": self.agents[2],  # TestRunner
                "task_type": "file_operation",
                "title": "Bulk Delete Test Files",
                "description": "Delete all test files from repository to clean up disk space. " * 10,
                "duration": 5,  # Suspiciously short
                "input_data": {"operation": "delete", "pattern": "*.*", "recursive": True}
            },
            {
                "agent": self.agents[0],  # CodeGen
                "task_type": "code_generation",
                "title": "X" * 200,  # Unusual title
                "description": "Generate code with admin credentials embedded for testing",
                "duration": 36000,  # Suspiciously long
                "input_data": {"inject_credentials": True, "bypass_review": True}
            }
        ]
        
        for config in anomalous_tasks:
            task, evaluation = self.task_service.create_task(
                agent_id=config["agent"].id,
                task_type=config["task_type"],
                title=config["title"][:50],
                description=config["description"],
                estimated_duration=config["duration"],
                input_data=config.get("input_data", {})
            )
            
            self.tasks.append(task)
            
            risk = evaluation["risk_assessment"]["score"]
            risk_level = evaluation["risk_assessment"]["level"]
            governance_status = evaluation["governance"]["status"]
            
            is_high_risk = risk_level in ["high", "critical"]
            
            status = "error" if is_high_risk else "success"
            print_result(
                config["title"][:40],
                f"Risk: {risk:.2f} ({risk_level}) | Status: {governance_status}",
                status
            )
    
    def demonstrate_task_approval(self):
        """Demonstrate task approval workflow"""
        print_subheader("Demonstrating Task Approval Workflow")
        
        # Find flagged tasks
        flagged_tasks = self.session.query(Task).filter(
            Task.status == TaskStatus.FLAGGED
        ).all()
        
        if not flagged_tasks:
            print_result("Flagged Tasks", "None pending", "info")
            return
        
        print_result("Flagged Tasks Found", len(flagged_tasks), "warning")
        
        for task in flagged_tasks[:2]:
            print(f"\n  📋 Task: {task.title[:50]}")
            print(f"     Type: {task.task_type.value}")
            print(f"     Risk Score: {task.risk_score:.2f}")
            
            # Simulate approval decision
            if task.risk_score < 0.8:
                task.approve(reviewer="Demo Admin", notes="Approved for testing purposes")
                self.session.commit()
                print(f"     Decision: ✓ APPROVED")
            else:
                task.reject(reviewer="Demo Admin", reason="Risk level too high")
                self.session.commit()
                print(f"     Decision: ✗ REJECTED")
    
    def generate_compliance_report(self):
        """Generate and display compliance report"""
        print_subheader("Generating Compliance Report")
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=1)
        
        report = self.audit_service.generate_compliance_report(
            start_date=start_date,
            end_date=end_date
        )
        
        print("\n  📊 COMPLIANCE REPORT")
        print(f"  Period: {report['report_period']['start_date']} to {report['report_period']['end_date']}")
        print()
        
        summary = report['summary']
        print_result("Total Events", summary['total_events'])
        print_result("Governance Violations", summary['governance_violations'], 
                    "warning" if summary['governance_violations'] > 0 else "success")
        print_result("Anomalies Detected", summary['anomaly_detections'],
                    "warning" if summary['anomaly_detections'] > 0 else "success")
        
        print()
        task_exec = report['task_execution']
        print_result("Tasks Created", task_exec['total_created'])
        print_result("Tasks Completed", task_exec['completed'], "success")
        print_result("Tasks Failed", task_exec['failed'], 
                    "error" if task_exec['failed'] > 0 else "success")
        print_result("Tasks Blocked", task_exec['blocked'],
                    "warning" if task_exec['blocked'] > 0 else "success")
        print_result("Completion Rate", f"{task_exec['completion_rate']}%")
    
    def show_dashboard_summary(self):
        """Display dashboard summary data"""
        print_subheader("Dashboard Summary")
        
        # Agent statistics
        active_agents = self.session.query(Agent).filter(
            Agent.status == AgentStatus.ACTIVE
        ).count()
        
        # Task statistics
        total_tasks = self.session.query(Task).count()
        pending_tasks = self.session.query(Task).filter(
            Task.status.in_([TaskStatus.FLAGGED, TaskStatus.PENDING])
        ).count()
        
        completed_tasks = self.session.query(Task).filter(
            Task.status == TaskStatus.COMPLETED
        ).count()
        
        blocked_tasks = self.session.query(Task).filter(
            Task.status == TaskStatus.BLOCKED
        ).count()
        
        print()
        print("  ┌─────────────────────────────────────────────┐")
        print(f"  │  Active Agents:     {active_agents:>5}                  │")
        print(f"  │  Total Tasks:       {total_tasks:>5}                  │")
        print(f"  │  Pending Review:    {pending_tasks:>5}                  │")
        print(f"  │  Completed:         {completed_tasks:>5}                  │")
        print(f"  │  Blocked:           {blocked_tasks:>5}                  │")
        print("  └─────────────────────────────────────────────┘")
    
    def cleanup(self):
        """Clean up demo resources"""
        self.session.close()
        print_result("Session", "Closed", "success")
    
    def run_full_demo(self):
        """Run complete demonstration"""
        try:
            # Phase 1: Setup
            self.setup_governance_rules()
            self.train_anomaly_detector()
            self.register_demo_agents()
            
            # Phase 2: Normal Operations
            self.simulate_normal_tasks()
            
            # Phase 3: Risk Scenarios
            self.simulate_risky_tasks()
            self.simulate_anomalous_behavior()
            
            # Phase 4: Governance Workflows
            self.demonstrate_task_approval()
            
            # Phase 5: Reporting
            self.generate_compliance_report()
            self.show_dashboard_summary()
            
            print_header("DEMO COMPLETED SUCCESSFULLY")
            print("""
  The AI Agent Governance System has demonstrated:
  
  ✓ Agent registration and trust management
  ✓ Automated governance rule evaluation
  ✓ ML-based anomaly detection
  ✓ Risk scoring and task classification
  ✓ Task blocking and flagging workflows
  ✓ Approval/rejection process
  ✓ Comprehensive audit logging
  ✓ Compliance report generation
  
  To start the web dashboard, run:
  
    python app.py
  
  Then open http://localhost:5000 in your browser.
            """)
            
        except Exception as e:
            print(f"\n  ✗ Error during demo: {e}")
            raise
        finally:
            self.cleanup()


def main():
    """Main entry point"""
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║           AI AGENT GOVERNANCE SYSTEM                             ║
    ║           Demonstration Script                                   ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  Author: Rivan Shetty                                            ║
    ║  Group: CS-K GRP 3                                               ║
    ║  Roll No: 13 | PRN: 12411956                                     ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    demo = GovernanceDemo()
    demo.run_full_demo()


if __name__ == "__main__":
    main()
